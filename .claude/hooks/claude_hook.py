#!/usr/bin/env python3
"""Project-local Claude Code hook policy for System_bus.

This script is intentionally conservative:
- destructive commands are blocked;
- dotenv reads and secret-environment disclosure are blocked;
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
    if DOTENV_PATH_RE.search(command):
        reasons.append("dotenv_file_access")
    if ENV_DUMP_RE.search(command):
        reasons.append("environment_dump")
    if SENSITIVE_ENV_REFERENCE_RE.search(command):
        reasons.append("sensitive_environment_reference")
    return sorted(set(reasons))


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
    payload = {"level": level, "message": message}
    if details:
        payload["details"] = details
    print(json.dumps(payload, ensure_ascii=True))


def handle_pre_tool_use(args: argparse.Namespace, payload: dict[str, Any], root: Path) -> int:
    command = extract_command(payload, args.dry_run_command)
    if not command:
        emit("warn", "No Bash command found in hook payload; policy could not inspect it.")
        return 0
    reasons = blocked_command_reasons(command, root)
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
    emit("ok", "Prompt passed basic secret scan.")
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


def handle_stop(args: argparse.Namespace, _: dict[str, Any], root: Path) -> int:
    findings = scan_git_diff(root, args.dry_run_diff)
    if findings:
        emit(
            "warn",
            "Git diff may contain secret material. Remove it and rotate any exposed credential before committing.",
            {"findings": findings},
        )
        return 0
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
    parser.add_argument("--dry-run-prompt")
    parser.add_argument("--dry-run-reason")
    parser.add_argument("--dry-run-status")
    parser.add_argument("--dry-run-diff")
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
