#!/usr/bin/env python3
"""Project-local Claude Code hook policy for System_bus.

This script is intentionally conservative:
- destructive commands are blocked;
- dotenv reads (also via globs) and secret-environment disclosure are blocked;
- Bash may not change the guard itself or secret files (.claude/hooks/**,
  .claude/settings*.json, .env*) — edit those with the Edit tool, which prompts;
- read-only subagents (reviewers, finding-verifier, Explore, Plan; detected by
  the payload's agent_type) get an allowlist: read-only git, grep/find/cat/
  sed -n, `mvn ... test`, `npm run test:unit`; anything else is blocked;
- ambiguous cases produce warnings without editing files;
- dry-run flags make the policy testable outside Claude Code runtime.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any


SECRET_PATTERNS = [
    ("openai_api_key", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
    (
        "generic_api_key",
        re.compile(
            r"(?i)\b(?:api[_-]?key|token|secret|password)\s*[:=]\s*['\"]?"
            r"(?P<value>[^'\"\s]{8,})"
        ),
    ),
    ("jwt", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b")),
    ("private_key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    (
        "backend_config_credential",
        re.compile(
            r"(?im)^\s*(?:jwt\.secret|spring\.datasource\.password|spring\.mail\.password|"
            r"minio\.(?:access-key|secret-key)|aws_(?:access_key_id|secret_access_key))"
            r"\s*[:=]\s*(?P<value>.+?)\s*$"
        ),
    ),
]

DESTRUCTIVE_PATTERNS = [
    ("rm_recursive_force", re.compile(r"(^|[\s;&|])rm\s+[^;&|]*-(?:[^\s;&|]*r[^\s;&|]*f|[^\s;&|]*f[^\s;&|]*r)\b")),
    ("git_reset_hard", re.compile(r"(^|[\s;&|])git\s+reset\s+--hard\b")),
    ("git_clean_force", re.compile(r"(^|[\s;&|])git\s+clean\s+-(?:[^\s;&|]*f|[^\s;&|]*x|[^\s;&|]*d){1,}\b")),
    ("force_push", re.compile(r"(^|[\s;&|])git\s+push\b[^;&|]*(--force|-f)\b")),
    ("chmod_world_writable", re.compile(r"(^|[\s;&|])chmod\s+(?:-R\s+)?777\b")),
    (
        "worktree_force_remove",
        re.compile(r"(^|[\s;&|])git\s+(?:-C\s+\S+\s+)?worktree\s+remove\b[^;&|]*(?:--force|-f)\b"),
    ),
    (
        "direct_branch_delete",
        re.compile(r"(^|[\s;&|])git\s+(?:-C\s+\S+\s+)?branch\b[^;&|]*(?:-d|-D|--delete)\b"),
    ),
    (
        "direct_ref_delete",
        re.compile(r"(^|[\s;&|])git\s+(?:-C\s+\S+\s+)?update-ref\s+-d\s+refs/heads/"),
    ),
]

DOTENV_PATH_RE = re.compile(
    r"(?i)(?:^|[\s'\"=:/])\.env(?:\.[A-Za-z0-9_.-]+)?(?:$|[\s'\";&|)])"
)
ENV_DUMP_RE = re.compile(
    r"(^|[\s;&|])(?:"
    r"(?:command\s+)?(?:/usr/bin/|/bin/)?(?:env|printenv)(?:\s|$|[;&|])|"
    r"export\s+-p(?:\s|$|[;&|])|"
    r"declare\s+-x(?:\s|$|[;&|])"
    r")"
)
SENSITIVE_ENV_REFERENCE_RE = re.compile(
    r"(?i)(?:"
    r"\$(?:\{)?(?:JWT_|DB_|MAIL_|MINIO_)[A-Z0-9_]*(?:\})?|"
    r"\b(?:JWT_|DB_|MAIL_|MINIO_)[A-Z0-9_]*\s*="
    r")"
)

# Globs such as `.env*`, `.e*` or `.en?` would expand to dotenv files at run time.
DOTENV_GLOB_RE = re.compile(r"(?:^|[\s'\"=:/])\.e(?:n|nv)?[*?\[]")
# Environment readers the plain `env`/`printenv` rule does not see.
ENV_READ_RE = re.compile(
    r"(?:/proc/[^\s/]+/environ|"
    r"(?:^|[;&|(]\s*)set\s*(?:$|[;&|)])|"
    r"\b(?:python3?|node|ruby|perl)\b[^\n]*\s-(?:c|e)\b[^\n]*"
    r"(?:os\.environ|getenv|process\.env|ENV\[|%ENV))"
)
# Files that hold the guard itself or secrets: Bash may read the guard, never change it.
PROTECTED_PATH_RE = re.compile(
    r"(?:^|/)\.claude/hooks(?:/|$)|(?:^|/)\.claude/settings(?:\.local)?\.json$|(?:^|/)\.env(?:\.[^/]*)?$"
)
WRITE_COMMANDS = {
    "tee", "cp", "mv", "rm", "truncate", "ln", "install", "rsync", "dd",
    "chmod", "chown", "touch", "unlink", "rmdir", "mkdir",
}
IN_PLACE_EDITORS = {"sed", "gsed", "perl"}
GIT_OVERWRITE_SUBCOMMANDS = {"checkout", "restore", "rm", "mv", "apply", "stash", "reset"}
REDIRECT_OPERATORS = {">", ">>", ">|", "&>", "&>>", ">&", "&>|"}
SEPARATORS = {";", "&&", "||", "|", "&", "|&", ";;"}
INTERPRETERS = {"python", "python3", "node", "ruby", "perl"}
PROTECTED_CODE_RE = re.compile(r"\.claude/hooks|\.claude/settings|\.env\b")
INTERPRETER_WRITE_RE = re.compile(r"open\(|write|unlink|rename|replace|rmtree|remove\(|writeFile|appendFile|rmSync")
HEREDOC_RE = re.compile(r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1")

# Subagents that must not change anything. Plugin copies use the `system-bus-dev:` prefix.
READ_ONLY_AGENT_TYPES = {
    "backend-reviewer", "frontend-reviewer", "security-reviewer", "test-gap-reviewer",
    "config-reviewer", "finding-verifier", "Explore", "Plan",
}
READ_ONLY_COMMANDS = {
    "cd", "pwd", "ls", "cat", "head", "tail", "wc", "grep", "egrep", "fgrep", "rg",
    "sort", "uniq", "cut", "tr", "diff", "cmp", "file", "stat", "echo", "printf",
    "true", "basename", "dirname", "realpath", "which", "tree", "jq", "nl", "comm", "column",
}
READ_ONLY_GIT_SUBCOMMANDS = {
    "status", "diff", "log", "show", "rev-parse", "ls-files", "grep", "blame",
    "merge-base", "cat-file", "describe", "shortlog",
}
FIND_WRITE_FLAGS = {"-exec", "-execdir", "-ok", "-okdir", "-delete", "-fprint", "-fprint0", "-fprintf", "-fls"}
MVN_FORBIDDEN_GOAL_RE = re.compile(r"^(?:clean|install|deploy|package|verify|site|release:.*|spring-boot:.*|exec:.*|flyway:.*|dependency:.*)$")
READ_ONLY_PYTHON_SCRIPTS = {
    ".claude/hooks/claude_hook.py",
    ".claude/hooks/test_claude_hook.py",
    ".claude/skills/review-pipeline/scripts/scan_workspace.py",
}

REDIS_RUNTIME_RE = re.compile(r"Infrastructure/redis-cluster/data")
REDIRECT_RE = re.compile(r"(?:^|\s)(?:>|>>)\s*(?P<path>/[^\s;&|]+)")
DIFF_SCAN_EXCLUDES = {
    ".git",
    "node_modules",
    "target",
    "dist",
    "coverage",
    "Infrastructure/redis-cluster/data",
}
MAX_UNTRACKED_SECRET_SCAN_BYTES = 1_000_000
CODE_CHANGE_SUFFIXES = {".java", ".vue", ".js", ".ts", ".py", ".sql", ".yml", ".yaml", ".properties"}
CODE_CHANGE_NAMES = {"pom.xml", "package.json"}


def resolve_project_root() -> Path:
    """Find the System_bus root without relying on git root."""
    current = Path.cwd().resolve()
    candidates = [current, *current.parents]
    for candidate in candidates:
        if candidate.name == "System_bus" and (candidate / ".claude").exists():
            return candidate
    for candidate in candidates:
        if (candidate / ".claude").exists() and (candidate / "ticket-system").exists() and (candidate / "booking_ticket_vue").exists():
            return candidate
    for candidate in candidates:
        if (
            (candidate / ".claude/hooks/claude_hook.py").exists()
        ):
            return candidate
    return current


def read_payload() -> dict[str, Any]:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {"raw": raw}
    return data if isinstance(data, dict) else {"payload": data}


def walk_values(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        values: list[str] = []
        for item in value.values():
            values.extend(walk_values(item))
        return values
    if isinstance(value, list):
        values = []
        for item in value:
            values.extend(walk_values(item))
        return values
    return []


def first_field(payload: dict[str, Any], names: set[str]) -> str:
    stack: list[Any] = [payload]
    while stack:
        item = stack.pop()
        if isinstance(item, dict):
            for key, value in item.items():
                if key in names and isinstance(value, str):
                    return value
                stack.append(value)
        elif isinstance(item, list):
            stack.extend(item)
    return ""


def extract_command(payload: dict[str, Any], override: str | None) -> str:
    if override:
        return override
    return first_field(payload, {"command", "cmd", "shell_command", "bash_command"})


def extract_prompt(payload: dict[str, Any], override: str | None) -> str:
    if override:
        return override
    return first_field(payload, {"prompt", "user_prompt", "message", "text", "input"})


def extract_reason(payload: dict[str, Any], override: str | None) -> str:
    if override:
        return override
    return first_field(payload, {"justification", "reason", "approval_reason"})


def extract_status(payload: dict[str, Any], override: str | None) -> int | None:
    if override is not None:
        try:
            return int(override)
        except ValueError:
            return None
    for name in ("exit_code", "status", "returncode", "code"):
        value = payload.get(name)
        if isinstance(value, int):
            return value
        if isinstance(value, str) and value.isdigit():
            return int(value)
    return None


def blocked_command_reasons(command: str, root: Path) -> list[str]:
    reasons = [name for name, pattern in DESTRUCTIVE_PATTERNS if pattern.search(command)]
    raw_path = worktree_remove_path(command)
    if raw_path:
        target = Path(raw_path)
        if not target.is_absolute():
            target = (Path.cwd() / target).resolve()
        else:
            target = target.resolve()
        allowed = managed_worktree_root(root)
        if allowed != target and allowed not in target.parents:
            reasons.append(f"worktree_cleanup_outside_managed_root:{target}")
    if REDIS_RUNTIME_RE.search(command):
        for token in shlex.split(command, posix=True) if command else []:
            if token.startswith((">", ">>")) or token in {"rm", "mv", "cp", "rsync", "tee"}:
                reasons.append("redis_runtime_data_write")
                break
        if re.search(r"(^|[\s;&|])(rm|mv|cp|rsync|tee|truncate)\b", command):
            reasons.append("redis_runtime_data_write")
    for match in REDIRECT_RE.finditer(command):
        target = Path(match.group("path")).resolve()
        if not is_allowed_write_path(target, root):
            reasons.append(f"redirect_outside_workspace:{target}")
    if DOTENV_PATH_RE.search(command) or DOTENV_GLOB_RE.search(command):
        reasons.append("dotenv_file_access")
    if ENV_DUMP_RE.search(command) or ENV_READ_RE.search(command):
        reasons.append("environment_dump")
    if SENSITIVE_ENV_REFERENCE_RE.search(command):
        reasons.append("sensitive_environment_reference")
    reasons.extend(protected_path_write_reasons(command, root))
    return sorted(set(reasons))


def strip_heredoc_bodies(command: str) -> str:
    """Drop heredoc bodies: they are data written by the command, not commands."""
    lines = command.split("\n")
    kept: list[str] = []
    delimiter: str | None = None
    for line in lines:
        if delimiter is not None:
            if line.strip() == delimiter:
                delimiter = None
            continue
        kept.append(line)
        match = HEREDOC_RE.search(line)
        if match:
            delimiter = match.group(2)
    return "\n".join(kept)


def command_segments(command: str) -> list[list[str]] | None:
    """Split a shell command into simple commands; None when it cannot be parsed."""
    text = strip_heredoc_bodies(command).replace("\\\n", " ")
    segments: list[list[str]] = []
    for line in text.split("\n"):
        lexer = shlex.shlex(line, posix=True, punctuation_chars=True)
        lexer.whitespace_split = True
        lexer.commenters = ""
        try:
            tokens = list(lexer)
        except ValueError:
            return None
        current: list[str] = []
        for token in tokens:
            if token in SEPARATORS:
                if current:
                    segments.append(current)
                current = []
            else:
                current.append(token)
        if current:
            segments.append(current)
    return segments


def redirect_targets(tokens: list[str]) -> list[str]:
    targets = []
    for index, token in enumerate(tokens):
        if token in REDIRECT_OPERATORS and index + 1 < len(tokens):
            target = tokens[index + 1]
            if token == ">&" and target.isdigit():
                continue
            targets.append(target)
    return targets


def is_protected_path(token: str, root: Path) -> bool:
    value = token.split("=", 1)[1] if token.startswith("--") and "=" in token else token
    if PROTECTED_PATH_RE.search(value):
        return True
    if not value or value.startswith("-"):
        return False
    try:
        resolved = (Path.cwd() / value).resolve()
        relative = resolved.relative_to(root.resolve())
    except (OSError, ValueError):
        return False
    return bool(PROTECTED_PATH_RE.search(relative.as_posix()))


def command_word(tokens: list[str]) -> tuple[str, list[str]]:
    """First word after `VAR=value` prefixes, and the arguments after it."""
    index = 0
    while index < len(tokens) and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", tokens[index]):
        index += 1
    if index >= len(tokens):
        return "", []
    return tokens[index].rsplit("/", 1)[-1], tokens[index + 1 :]


def protected_path_write_reasons(command: str, root: Path) -> list[str]:
    segments = command_segments(command)
    if segments is None:
        has_protected = any(is_protected_path(word, root) for word in re.split(r"[\s'\"]+", command))
        has_write = re.search(r">|\btee\b|-i\b|--in-place|\b(?:cp|mv|rm|truncate|ln)\b|--output", command)
        return ["protected_path_write"] if has_protected and has_write else []
    for tokens in segments:
        if any(is_protected_path(target, root) for target in redirect_targets(tokens)):
            return ["protected_path_write"]
        word, args = command_word(tokens)
        operands = [arg for arg in args if arg not in REDIRECT_OPERATORS]
        if word in WRITE_COMMANDS and any(is_protected_path(arg, root) for arg in operands):
            return ["protected_path_write"]
        if word in IN_PLACE_EDITORS and any(arg.startswith(("-i", "--in-place")) for arg in args):
            if any(is_protected_path(arg, root) for arg in operands):
                return ["protected_path_write"]
        if word == "git":
            if any(arg.startswith("--output") and is_protected_path(arg, root) for arg in args):
                return ["protected_path_write"]
            subcommand = git_subcommand(args)
            if subcommand in GIT_OVERWRITE_SUBCOMMANDS and any(is_protected_path(arg, root) for arg in args):
                return ["protected_path_write"]
        if word in INTERPRETERS and {"-c", "-e"}.intersection(args):
            code = " ".join(args)
            if PROTECTED_CODE_RE.search(code) and INTERPRETER_WRITE_RE.search(code):
                return ["protected_path_write"]
    return []


def git_subcommand(args: list[str]) -> str:
    index = 0
    while index < len(args):
        arg = args[index]
        if arg in {"-C", "-c", "--git-dir", "--work-tree"}:
            index += 2
            continue
        if arg.startswith("-"):
            index += 1
            continue
        return arg
    return ""


def read_only_git_form(subcommand: str, rest: list[str]) -> bool:
    """Listing forms of git subcommands that can also write (stash, branch, remote, worktree)."""
    if subcommand == "stash":
        return bool(rest) and rest[0] in {"list", "show"}
    if subcommand == "branch":
        return all(arg in {"--show-current", "--list", "-a", "-r", "-v", "-vv", "--all", "--remotes"} for arg in rest)
    if subcommand == "remote":
        return rest in ([], ["-v"]) or (bool(rest) and rest[0] == "get-url")
    if subcommand == "worktree":
        return rest[:1] == ["list"]
    return False


def agent_type_of(payload: dict[str, Any], override: str | None) -> str:
    """Subagent type from the hook payload ('' for the main session)."""
    value = override if override is not None else payload.get("agent_type") or payload.get("subagent_type") or ""
    return str(value).rsplit(":", 1)[-1]


def read_only_agent_reasons(command: str, root: Path) -> list[str]:
    """Allowlist for read-only subagents: anything not clearly read-only is blocked."""
    if "$(" in command or "`" in command or "<(" in command or ">(" in command:
        return ["read_only_agent_command_substitution"]
    if HEREDOC_RE.search(command):
        return ["read_only_agent_heredoc"]
    segments = command_segments(command)
    if segments is None:
        return ["read_only_agent_unparseable_command"]
    reasons: list[str] = []
    for tokens in segments:
        if any(token in {"(", ")"} for token in tokens):
            reasons.append("read_only_agent_subshell")
            continue
        for target in redirect_targets(tokens):
            if target != "/dev/null":
                reasons.append(f"read_only_agent_write:{target}")
        word, args = command_word(tokens)
        if len(tokens) and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", tokens[0]):
            reasons.append("read_only_agent_env_assignment")
        reason = read_only_command_reason(word, args, root)
        if reason:
            reasons.append(reason)
    return reasons


def read_only_command_reason(word: str, args: list[str], root: Path) -> str:
    if word in READ_ONLY_COMMANDS:
        return ""
    if word in {"sed", "gsed"}:
        if any(arg.startswith(("-i", "--in-place")) for arg in args):
            return "read_only_agent_in_place_edit"
        return ""
    if word == "find":
        flags = FIND_WRITE_FLAGS.intersection(args)
        return f"read_only_agent_find_action:{sorted(flags)[0]}" if flags else ""
    if word == "git":
        subcommand = git_subcommand(args)
        rest = args[args.index(subcommand) + 1 :] if subcommand in args else []
        if subcommand not in READ_ONLY_GIT_SUBCOMMANDS and not read_only_git_form(subcommand, rest):
            return f"read_only_agent_git_write:{subcommand or 'none'}"
        if any(arg.startswith("--output") for arg in args):
            return "read_only_agent_git_output_file"
        return ""
    if word == "mvn":
        goals = [arg for arg in args if not arg.startswith("-") and not arg.endswith(".xml") and "/" not in arg and "," not in arg]
        if "test" not in goals or any(MVN_FORBIDDEN_GOAL_RE.match(goal) for goal in goals):
            return "read_only_agent_mvn_goal"
        return ""
    if word == "npm":
        if "run" in args and "test:unit" in args and not {"install", "ci", "exec", "publish"}.intersection(args):
            return ""
        return "read_only_agent_npm_command"
    if word in {"python", "python3"}:
        script = next((arg for arg in args if not arg.startswith("-")), "")
        if script in READ_ONLY_PYTHON_SCRIPTS or args[:2] == ["-m", "unittest"]:
            return ""
        return "read_only_agent_python"
    return f"read_only_agent_command_not_allowed:{word or 'empty'}"


def worktree_remove_path(command: str) -> str:
    try:
        tokens = shlex.split(command, posix=True)
    except ValueError:
        return ""
    for index, token in enumerate(tokens):
        if token != "git":
            continue
        cursor = index + 1
        if cursor < len(tokens) and tokens[cursor] == "-C":
            cursor += 2
        if tokens[cursor : cursor + 2] != ["worktree", "remove"]:
            continue
        cursor += 2
        while cursor < len(tokens):
            candidate = tokens[cursor]
            if candidate in {"--force", "-f"}:
                cursor += 1
                continue
            if candidate.startswith("-"):
                cursor += 1
                continue
            return candidate
    return ""


def managed_worktree_root(root: Path) -> Path:
    if root.parent.name == "System_bus-worktrees":
        return root.parent.resolve()
    return (root.parent / "System_bus-worktrees").resolve()


def is_allowed_write_path(path: Path, root: Path) -> bool:
    allowed_roots = [
        root,
        Path("/tmp"),
        Path("/private/tmp"),
        Path(os.environ.get("TMPDIR", "/tmp")).resolve(),
    ]
    return any(path == allowed or allowed in path.parents for allowed in allowed_roots)


def secret_findings(text: str) -> list[str]:
    findings = []
    for name, pattern in SECRET_PATTERNS:
        for match in pattern.finditer(text):
            value = match.groupdict().get("value", match.group(0)).strip()
            normalized = value.strip("'\"")
            if (
                not normalized
                or "${" in normalized
                or normalized.lower().startswith("replace-with-")
                or normalized.lower() in {"redacted", "<redacted>", "changeme", "example", "placeholder"}
            ):
                continue
            findings.append(name)
            break
    return findings


def discover_git_repositories(root: Path) -> list[Path]:
    repositories = []
    candidates = [root]
    try:
        candidates.extend(path for path in root.iterdir() if path.is_dir())
    except OSError:
        return repositories
    for candidate in candidates:
        if (candidate / ".git").exists():
            repositories.append(candidate)
    return repositories


def run_git(repository: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repository), *args],
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )
    return result.stdout if result.returncode == 0 else ""


def added_lines_by_path(diff: str) -> dict[str, str]:
    current_path = ""
    additions: dict[str, list[str]] = {}
    for line in diff.splitlines():
        if line.startswith("+++ b/"):
            current_path = line[6:]
            continue
        if line.startswith("+") and not line.startswith("+++"):
            additions.setdefault(current_path or "<unknown>", []).append(line[1:])
    return {path: "\n".join(lines) for path, lines in additions.items()}


def should_skip_diff_path(path: str) -> bool:
    normalized = path.replace("\\", "/").lstrip("./")
    return any(
        normalized == excluded or normalized.startswith(f"{excluded}/")
        for excluded in DIFF_SCAN_EXCLUDES
    )


def scan_git_diff(root: Path, diff_override: str | None = None) -> list[dict[str, Any]]:
    if diff_override is not None:
        sources = [("<dry-run>", diff_override)]
        repositories: list[Path] = []
    else:
        repositories = discover_git_repositories(root)
        sources = []
        for repository in repositories:
            staged = run_git(repository, "diff", "--cached", "--no-ext-diff", "--no-color", "--unified=0")
            unstaged = run_git(repository, "diff", "--no-ext-diff", "--no-color", "--unified=0")
            sources.append((repository.name, f"{staged}\n{unstaged}"))

    findings: list[dict[str, Any]] = []
    for repository_name, diff in sources:
        for path, added_text in added_lines_by_path(diff).items():
            if should_skip_diff_path(path):
                continue
            types = secret_findings(added_text)
            if types:
                findings.append({"repository": repository_name, "path": path, "types": types})

    for repository in repositories:
        untracked = run_git(repository, "ls-files", "--others", "--exclude-standard").splitlines()
        for relative_path in untracked:
            if should_skip_diff_path(relative_path):
                continue
            path = repository / relative_path
            try:
                if not path.is_file() or path.stat().st_size > MAX_UNTRACKED_SECRET_SCAN_BYTES:
                    continue
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            types = secret_findings(text)
            if types:
                findings.append({"repository": repository.name, "path": relative_path, "types": types})
    return findings


def emit(level: str, message: str, details: dict[str, Any] | None = None) -> None:
    """Print a hook result.

    Claude Code only feeds stderr back to Claude when a hook exits with code 2,
    so blocking results go to stderr; everything else stays on stdout.
    """
    payload = {"level": level, "message": message}
    if details:
        payload["details"] = details
    stream = sys.stderr if level == "block" else sys.stdout
    print(json.dumps(payload, ensure_ascii=True), file=stream)


def handle_pre_tool_use(args: argparse.Namespace, payload: dict[str, Any], root: Path) -> int:
    command = extract_command(payload, args.dry_run_command)
    if not command:
        emit("warn", "No Bash command found in hook payload; policy could not inspect it.")
        return 0
    reasons = blocked_command_reasons(command, root)
    if agent_type_of(payload, args.dry_run_agent_type) in READ_ONLY_AGENT_TYPES:
        reasons = sorted(set(reasons + read_only_agent_reasons(command, root)))
    if reasons:
        emit("block", "Blocked dangerous or out-of-scope Bash command.", {"reasons": reasons})
        return 2
    emit("ok", "Bash command passed project hook policy.")
    return 0


def handle_permission_request(args: argparse.Namespace, payload: dict[str, Any]) -> int:
    reason = extract_reason(payload, args.dry_run_reason)
    if len(reason.strip()) < 12:
        emit("warn", "Escalation request should include a concrete justification.")
        return 0
    if re.search(r"(?i)\b(anything|everything|full access|all commands|bypass)\b", reason):
        emit("warn", "Escalation request looks broad; scope it to the exact command or capability.")
        return 0
    emit("ok", "Escalation request justification is present.")
    return 0


def handle_user_prompt_submit(args: argparse.Namespace, payload: dict[str, Any]) -> int:
    prompt = extract_prompt(payload, args.dry_run_prompt)
    findings = secret_findings(prompt)
    if findings:
        emit("warn", "Prompt may contain secret material. Remove or redact it before continuing.", {"types": findings})
        return 0
    # UserPromptSubmit stdout is added to Claude's context; stay silent when clean.
    return 0


def handle_post_tool_use(args: argparse.Namespace, payload: dict[str, Any]) -> int:
    status = extract_status(payload, args.dry_run_status)
    command = extract_command(payload, args.dry_run_command)
    if status is not None and status != 0:
        hint = "Inspect the failing output and rerun with a narrower diagnostic command."
        if command and re.search(r"\bmvn\b", command):
            hint = "For Maven startup failures, rerun with -e and inspect the Spring Boot stack trace above MojoExecutionException."
        elif command and re.search(r"\bnpm\b", command):
            hint = "For npm failures, inspect the first error above the final lifecycle summary."
        emit("warn", "Command failed; verification is not complete.", {"exit_code": status, "hint": hint})
        return 0
    emit("ok", "Command completed without hook-detected failure.")
    return 0


def scan_open_ledger_items(root: Path) -> list[dict[str, Any]]:
    ledger_dir = root / ".claude" / "ledger"
    findings: list[dict[str, Any]] = []
    if not ledger_dir.is_dir():
        return findings
    for path in sorted(ledger_dir.glob("*.md")):
        if path.stem.upper() in {"README", "TEMPLATE"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        open_count = text.count("[ ]")
        if open_count:
            findings.append({"ledger": str(path.relative_to(root)), "open_items": open_count})
    return findings


def is_code_change_path(path: str) -> bool:
    normalized = path.replace("\\", "/")
    if should_skip_diff_path(normalized):
        return False
    name = normalized.rsplit("/", 1)[-1]
    return name in CODE_CHANGE_NAMES or Path(name).suffix in CODE_CHANGE_SUFFIXES


def changed_code_files(root: Path, override: str | None = None) -> list[str]:
    """Uncommitted code/config files (staged, unstaged, untracked) across the repos."""
    if override is not None:
        return [path for path in override.split(",") if path and is_code_change_path(path)]
    changed: list[str] = []
    for repository in discover_git_repositories(root):
        output = run_git(repository, "status", "--porcelain", "--untracked-files=all")
        for line in output.splitlines():
            path = line[3:].split(" -> ")[-1].strip('"')
            if is_code_change_path(path):
                changed.append(f"{repository.name}/{path}")
    return changed


def handle_stop(args: argparse.Namespace, payload: dict[str, Any], root: Path) -> int:
    # Claude is already continuing because of an earlier Stop block: never loop.
    if payload.get("stop_hook_active") is True:
        return 0
    findings = scan_git_diff(root, args.dry_run_diff)
    if findings:
        emit(
            "block",
            "Git diff may contain secret material. Remove it and tell the user to rotate any exposed credential before committing.",
            {"findings": findings},
        )
        return 2
    changed = changed_code_files(root, args.dry_run_changed)
    if changed:
        emit(
            "block",
            "Uncommitted code changes exist. Before finishing, run the matching verification "
            "(mvn test for ticket-system, npm run test:unit / npm run build for booking_ticket_vue, "
            "python3 -m unittest for .claude/hooks) unless already run after the last edit, then report "
            "changed files, verification commands with results, skipped checks, and remaining risks.",
            {"changed_files": changed[:20], "total": len(changed)},
        )
        return 2
    ledger_findings = scan_open_ledger_items(root)
    if ledger_findings:
        emit(
            "warn",
            "Open ledger items remain for tracked work-units. Confirm status before reporting done; leave the lead-review line for the user to tick.",
            {"ledgers": ledger_findings},
        )
        return 0
    emit("info", "Before final response, report changed files, verification commands, skipped checks, and remaining risks.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--event", required=True)
    parser.add_argument("--dry-run-command")
    parser.add_argument("--dry-run-agent-type", help="Simulate a PreToolUse call from this subagent type.")
    parser.add_argument("--dry-run-prompt")
    parser.add_argument("--dry-run-reason")
    parser.add_argument("--dry-run-status")
    parser.add_argument("--dry-run-diff")
    parser.add_argument("--dry-run-changed", help="Comma-separated changed paths for the Stop hook.")
    args = parser.parse_args()

    root = resolve_project_root()
    payload = read_payload()

    handlers = {
        "PreToolUse": lambda: handle_pre_tool_use(args, payload, root),
        "PermissionRequest": lambda: handle_permission_request(args, payload),
        "UserPromptSubmit": lambda: handle_user_prompt_submit(args, payload),
        "PostToolUse": lambda: handle_post_tool_use(args, payload),
        "Stop": lambda: handle_stop(args, payload, root),
    }
    handler = handlers.get(args.event)
    if handler is None:
        emit("warn", f"Unsupported hook event: {args.event}")
        return 0
    return handler()


if __name__ == "__main__":
    raise SystemExit(main())
