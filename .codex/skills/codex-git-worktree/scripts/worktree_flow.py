#!/usr/bin/env python3
"""Review-first dual-repository worktrees for the System_bus workspace."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
import shlex
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Optional


TOKEN_VERSION = 2
TOKEN_CONTEXT = b"system-bus-dual-worktree-v2\0"
TASK_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SHA_RE = re.compile(r"^[0-9a-f]{40,64}$")
PROJECTS = {
    "backend": "ticket-system",
    "frontend": "booking_ticket_vue",
}
ROOT_ALLOWED_FILES = {".gitignore", "AGENTS.md"}
ROOT_ALLOWED_PREFIXES = (".codex/",)


class FlowError(RuntimeError):
    pass


@dataclass(frozen=True)
class RepoPlan:
    source: str
    default_branch: str
    base_ref: str
    base_sha: str
    remote_ref: str
    branch: str
    worktree_path: str


@dataclass(frozen=True)
class WorktreePlan:
    version: int
    action: str
    repo: str
    task: str
    workspace: str
    common: RepoPlan
    project: RepoPlan
    common_branch_sha: str = ""
    project_branch_sha: str = ""


def command_text(parts: list[str]) -> str:
    return shlex.join(parts)


def run(
    parts: list[str],
    *,
    cwd: Optional[Path] = None,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        parts,
        cwd=str(cwd) if cwd else None,
        check=False,
        capture_output=True,
        text=True,
    )
    if check and result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "command failed"
        raise FlowError(f"{command_text(parts)}: {detail}")
    return result


def git(repository: Path, *args: str, check: bool = True) -> str:
    return run(["git", "-C", str(repository), *args], check=check).stdout.strip()


def resolve_root(override: Optional[str] = None) -> Path:
    if override:
        candidates = [Path(override).expanduser().resolve()]
    else:
        current = Path.cwd().resolve()
        script = Path(__file__).resolve()
        candidates = [current, *current.parents, script.parent, *script.parents]
    for candidate in candidates:
        if (candidate / ".codex").exists() and (candidate / "AGENTS.md").exists():
            if git(candidate, "rev-parse", "--show-toplevel", check=False) == str(candidate):
                return candidate
    raise FlowError("Could not locate the System_bus Git root.")


def validate_task(task: str) -> str:
    if len(task) > 48 or not TASK_RE.fullmatch(task):
        raise FlowError(
            "Task must be 1-48 lowercase letters/digits separated by single hyphens."
        )
    return task


def project_source(root: Path, repo: str) -> Path:
    try:
        name = PROJECTS[repo]
    except KeyError as exc:
        raise FlowError("Repository must be 'backend' or 'frontend'.") from exc
    return root / name


def workspace_base(root: Path) -> Path:
    return root.parent / f"{root.name}-worktrees"


def workspace_path(root: Path, repo: str, task: str) -> Path:
    return workspace_base(root) / f"{repo}-{task}"


def ensure_under(path: Path, parent: Path) -> None:
    resolved_path = path.resolve(strict=False)
    resolved_parent = parent.resolve(strict=False)
    if resolved_path != resolved_parent and resolved_parent not in resolved_path.parents:
        raise FlowError(f"Path escapes worktree base: {path}")


def require_git_root(repository: Path) -> None:
    if not repository.exists():
        raise FlowError(f"Repository does not exist: {repository}")
    top = git(repository, "rev-parse", "--show-toplevel", check=False)
    if not top or Path(top).resolve() != repository.resolve():
        raise FlowError(f"Path is not an independent Git root: {repository}")


def cached_default_branch(repository: Path) -> str:
    symbolic = git(
        repository,
        "symbolic-ref",
        "--quiet",
        "--short",
        "refs/remotes/origin/HEAD",
        check=False,
    )
    if symbolic.startswith("origin/"):
        return symbolic[len("origin/") :]

    upstream = git(
        repository,
        "rev-parse",
        "--abbrev-ref",
        "--symbolic-full-name",
        "@{upstream}",
        check=False,
    )
    if upstream.startswith("origin/"):
        return upstream[len("origin/") :]

    refs = git(
        repository,
        "for-each-ref",
        "--format=%(refname:strip=3)",
        "refs/remotes/origin",
        check=False,
    )
    branches = sorted(
        branch for branch in refs.splitlines() if branch and branch != "HEAD"
    )
    if len(branches) == 1:
        return branches[0]
    raise FlowError(
        "Could not determine origin default branch from origin/HEAD, current "
        "upstream, or a single cached remote branch."
    )


def remote_state(repository: Path) -> tuple[dict[str, str], list[str]]:
    require_git_root(repository)
    if not git(repository, "remote", "get-url", "origin", check=False):
        raise FlowError(f"Remote 'origin' is not configured for {repository}")

    warnings: list[str] = []
    remote = run(
        ["git", "-C", str(repository), "ls-remote", "--symref", "origin", "HEAD"],
        check=False,
    )
    default_ref = ""
    base_sha = ""
    if remote.returncode == 0:
        for line in remote.stdout.splitlines():
            if line.startswith("ref: ") and line.endswith("\tHEAD"):
                default_ref = line.split()[1]
            elif line.endswith("\tHEAD"):
                base_sha = line.split()[0]

    prefix = "refs/heads/"
    if not default_ref.startswith(prefix) or not SHA_RE.fullmatch(base_sha):
        default_branch = cached_default_branch(repository)
        default_ref = f"refs/heads/{default_branch}"
        remote_ref = f"refs/remotes/origin/{default_branch}"
        base_sha = git(repository, "rev-parse", "--verify", remote_ref, check=False)
        if not SHA_RE.fullmatch(base_sha):
            detail = remote.stderr.strip() or "remote HEAD was unavailable"
            raise FlowError(
                f"Could not query origin or resolve cached {remote_ref}: {detail}"
            )
        warnings.append(
            f"{repository.name}: origin was unavailable; preview uses cached "
            f"{remote_ref} at {base_sha}."
        )
    else:
        default_branch = default_ref[len(prefix) :]
        remote_ref = f"refs/remotes/origin/{default_branch}"

    return (
        {
            "default_branch": default_branch,
            "base_ref": default_ref,
            "base_sha": base_sha,
            "remote_ref": remote_ref,
        },
        warnings,
    )


def root_scope_violations(root: Path) -> list[str]:
    violations = []
    for path in git(root, "ls-files").splitlines():
        root_document = "/" not in path and path.endswith(".md")
        if (
            path in ROOT_ALLOWED_FILES
            or path.startswith(ROOT_ALLOWED_PREFIXES)
            or root_document
        ):
            continue
        violations.append(path)
    return violations


def status_warning(repository: Path) -> str:
    status = git(repository, "status", "--porcelain=v1")
    if not status:
        return ""
    return (
        f"{repository.name}: source has {len(status.splitlines())} changed or "
        "untracked path(s); they are not copied into worktrees."
    )


def local_branch_exists(repository: Path, branch: str) -> bool:
    result = run(
        [
            "git",
            "-C",
            str(repository),
            "show-ref",
            "--verify",
            "--quiet",
            f"refs/heads/{branch}",
        ],
        check=False,
    )
    return result.returncode == 0


def parse_worktrees(repository: Path) -> list[dict[str, str]]:
    output = git(repository, "worktree", "list", "--porcelain")
    worktrees: list[dict[str, str]] = []
    current: dict[str, str] = {}
    for line in output.splitlines():
        if not line:
            if current:
                worktrees.append(current)
                current = {}
            continue
        key, _, value = line.partition(" ")
        current[key] = value
    if current:
        worktrees.append(current)
    return worktrees


def registered_worktree(
    repository: Path, worktree_path: Path
) -> Optional[dict[str, str]]:
    expected = worktree_path.resolve(strict=False)
    for item in parse_worktrees(repository):
        actual = item.get("worktree")
        if actual and Path(actual).resolve(strict=False) == expected:
            return item
    return None


def repo_plan(
    source: Path,
    state: dict[str, str],
    branch: str,
    worktree: Path,
) -> RepoPlan:
    return RepoPlan(
        source=str(source.resolve()),
        default_branch=state["default_branch"],
        base_ref=state["base_ref"],
        base_sha=state["base_sha"],
        remote_ref=state["remote_ref"],
        branch=branch,
        worktree_path=str(worktree.resolve(strict=False)),
    )


def build_create_plan(
    root: Path, repo: str, task: str
) -> tuple[WorktreePlan, list[str]]:
    task = validate_task(task)
    project = project_source(root, repo)
    require_git_root(root)
    require_git_root(project)

    violations = root_scope_violations(root)
    if violations:
        preview = ", ".join(violations[:5])
        suffix = "..." if len(violations) > 5 else ""
        raise FlowError(
            "Common repository tracks paths outside .codex, AGENTS.md, and "
            f".gitignore: {preview}{suffix}"
        )

    common_state, common_warnings = remote_state(root)
    project_state, project_warnings = remote_state(project)
    branch = f"codex/{task}"
    workspace = workspace_path(root, repo, task)
    project_worktree = workspace / PROJECTS[repo]
    ensure_under(workspace, workspace_base(root))

    for source, label in ((root, "common"), (project, repo)):
        if local_branch_exists(source, branch):
            raise FlowError(f"{label} local branch already exists: {branch}")
    if workspace.exists():
        raise FlowError(f"Workspace destination already exists: {workspace}")
    if registered_worktree(root, workspace):
        raise FlowError(f"Common repo already registers worktree: {workspace}")
    if registered_worktree(project, project_worktree):
        raise FlowError(f"Project repo already registers worktree: {project_worktree}")

    warnings = common_warnings + project_warnings
    warnings.extend(
        warning
        for warning in (status_warning(root), status_warning(project))
        if warning
    )
    return (
        WorktreePlan(
            version=TOKEN_VERSION,
            action="create",
            repo=repo,
            task=task,
            workspace=str(workspace.resolve(strict=False)),
            common=repo_plan(root, common_state, branch, workspace),
            project=repo_plan(project, project_state, branch, project_worktree),
        ),
        warnings,
    )


def encode_token(plan: WorktreePlan) -> str:
    raw = json.dumps(asdict(plan), sort_keys=True, separators=(",", ":")).encode()
    payload = base64.urlsafe_b64encode(raw).decode().rstrip("=")
    digest = hashlib.sha256(TOKEN_CONTEXT + raw).hexdigest()[:24]
    return f"{payload}.{digest}"


def decode_token(token: str) -> WorktreePlan:
    try:
        payload, digest = token.rsplit(".", 1)
        raw = base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4))
        expected = hashlib.sha256(TOKEN_CONTEXT + raw).hexdigest()[:24]
        if digest != expected:
            raise FlowError("Approval token checksum does not match.")
        data = json.loads(raw)
        common = RepoPlan(**data.pop("common"))
        project = RepoPlan(**data.pop("project"))
        plan = WorktreePlan(common=common, project=project, **data)
    except (ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        raise FlowError("Invalid approval token.") from exc
    if plan.version != TOKEN_VERSION:
        raise FlowError(
            f"Approval token version {plan.version} is obsolete; run preview again."
        )
    return plan


def fetch_command(plan: RepoPlan) -> list[str]:
    return [
        "git",
        "-C",
        plan.source,
        "fetch",
        "--no-tags",
        "origin",
        f"+{plan.base_ref}:{plan.remote_ref}",
    ]


def command_plan(plan: WorktreePlan) -> list[str]:
    if plan.action == "create":
        return [
            command_text(fetch_command(plan.common)),
            command_text(fetch_command(plan.project)),
            command_text(
                [
                    "git",
                    "-C",
                    plan.common.source,
                    "worktree",
                    "add",
                    "-b",
                    plan.common.branch,
                    plan.common.worktree_path,
                    plan.common.base_sha,
                ]
            ),
            command_text(
                [
                    "git",
                    "-C",
                    plan.project.source,
                    "worktree",
                    "add",
                    "-b",
                    plan.project.branch,
                    plan.project.worktree_path,
                    plan.project.base_sha,
                ]
            ),
        ]
    return [
        command_text(fetch_command(plan.common)),
        command_text(fetch_command(plan.project)),
        command_text(
            [
                "git",
                "-C",
                plan.project.source,
                "worktree",
                "remove",
                plan.project.worktree_path,
            ]
        ),
        command_text(
            [
                "git",
                "-C",
                plan.common.source,
                "worktree",
                "remove",
                plan.common.worktree_path,
            ]
        ),
        command_text(
            [
                "git",
                "-C",
                plan.project.source,
                "branch",
                "--set-upstream-to",
                f"origin/{plan.project.default_branch}",
                plan.project.branch,
            ]
        ),
        command_text(
            [
                "git",
                "-C",
                plan.common.source,
                "branch",
                "--set-upstream-to",
                f"origin/{plan.common.default_branch}",
                plan.common.branch,
            ]
        ),
        command_text(
            ["git", "-C", plan.project.source, "branch", "-d", plan.project.branch]
        ),
        command_text(
            ["git", "-C", plan.common.source, "branch", "-d", plan.common.branch]
        ),
    ]


def compare_plan(approved: WorktreePlan, current: WorktreePlan) -> None:
    if asdict(approved) != asdict(current):
        raise FlowError(
            "Repository or remote state changed after preview. Run preview again."
        )


def fetch_and_verify(repo: RepoPlan) -> None:
    run(fetch_command(repo))
    fetched = git(Path(repo.source), "rev-parse", repo.remote_ref)
    if fetched != repo.base_sha:
        raise FlowError(
            f"{Path(repo.source).name}: remote default changed after approval."
        )


def delete_branch_if_exists(
    repository: Path, branch: str, default_branch: str
) -> None:
    if local_branch_exists(repository, branch):
        git(
            repository,
            "branch",
            "--set-upstream-to",
            f"origin/{default_branch}",
            branch,
            check=False,
        )
        git(repository, "branch", "-d", branch)


def create_worktrees(root: Path, approved: WorktreePlan) -> dict[str, Any]:
    if approved.action != "create":
        raise FlowError("Approval token is not for create.")
    current, warnings = build_create_plan(root, approved.repo, approved.task)
    compare_plan(approved, current)
    fetch_and_verify(approved.common)
    fetch_and_verify(approved.project)

    common_source = Path(approved.common.source)
    project_source_path = Path(approved.project.source)
    workspace = Path(approved.workspace)
    common_created = False
    project_created = False
    try:
        git(
            common_source,
            "worktree",
            "add",
            "-b",
            approved.common.branch,
            approved.common.worktree_path,
            approved.common.base_sha,
        )
        common_created = True
        git(
            project_source_path,
            "worktree",
            "add",
            "-b",
            approved.project.branch,
            approved.project.worktree_path,
            approved.project.base_sha,
        )
        project_created = True
    except Exception:
        if project_created:
            git(
                project_source_path,
                "worktree",
                "remove",
                approved.project.worktree_path,
                check=False,
            )
        delete_branch_if_exists(
            project_source_path,
            approved.project.branch,
            approved.project.default_branch,
        )
        if common_created:
            git(
                common_source,
                "worktree",
                "remove",
                approved.common.worktree_path,
                check=False,
            )
        delete_branch_if_exists(
            common_source,
            approved.common.branch,
            approved.common.default_branch,
        )
        raise

    return {
        "status": "created",
        "workspace": str(workspace),
        "common_branch": approved.common.branch,
        "project_branch": approved.project.branch,
        "project": approved.project.worktree_path,
        "warnings": warnings,
    }


def ensure_commit_available(repository: Path, sha: str) -> None:
    result = run(
        ["git", "-C", str(repository), "cat-file", "-e", f"{sha}^{{commit}}"],
        check=False,
    )
    if result.returncode != 0:
        raise FlowError(
            f"{repository.name}: cached remote commit is unavailable; fetch and retry."
        )


def verify_cleanup_repo(
    repo: RepoPlan,
    expected_branch: str,
    base_sha: str,
) -> str:
    source = Path(repo.source)
    worktree = Path(repo.worktree_path)
    item = registered_worktree(source, worktree)
    if not item:
        raise FlowError(f"Worktree is not registered: {worktree}")
    if item.get("branch") != f"refs/heads/{expected_branch}":
        raise FlowError(f"Worktree branch mismatch: {worktree}")
    if git(worktree, "status", "--porcelain=v1"):
        raise FlowError(f"Worktree has uncommitted changes: {worktree}")
    branch_sha = git(source, "rev-parse", f"refs/heads/{expected_branch}")
    ensure_commit_available(source, base_sha)
    merged = run(
        ["git", "-C", str(source), "merge-base", "--is-ancestor", branch_sha, base_sha],
        check=False,
    )
    if merged.returncode != 0:
        raise FlowError(
            f"Branch {expected_branch} is not merged into origin/{repo.default_branch} "
            f"for {source.name}."
        )
    return branch_sha


def build_cleanup_plan(
    root: Path, repo: str, task: str
) -> tuple[WorktreePlan, list[str]]:
    task = validate_task(task)
    project = project_source(root, repo)
    common_state, common_warnings = remote_state(root)
    project_state, project_warnings = remote_state(project)
    branch = f"codex/{task}"
    workspace = workspace_path(root, repo, task)
    project_worktree = workspace / PROJECTS[repo]

    common = repo_plan(root, common_state, branch, workspace)
    project_plan = repo_plan(project, project_state, branch, project_worktree)
    common_sha = verify_cleanup_repo(common, branch, common.base_sha)
    project_sha = verify_cleanup_repo(project_plan, branch, project_plan.base_sha)

    return (
        WorktreePlan(
            version=TOKEN_VERSION,
            action="cleanup",
            repo=repo,
            task=task,
            workspace=str(workspace.resolve(strict=False)),
            common=common,
            project=project_plan,
            common_branch_sha=common_sha,
            project_branch_sha=project_sha,
        ),
        common_warnings + project_warnings,
    )


def cleanup_worktrees(root: Path, approved: WorktreePlan) -> dict[str, Any]:
    if approved.action != "cleanup":
        raise FlowError("Approval token is not for cleanup.")
    current, warnings = build_cleanup_plan(root, approved.repo, approved.task)
    compare_plan(approved, current)
    fetch_and_verify(approved.common)
    fetch_and_verify(approved.project)

    verify_cleanup_repo(
        approved.common, approved.common.branch, approved.common.base_sha
    )
    verify_cleanup_repo(
        approved.project, approved.project.branch, approved.project.base_sha
    )
    common_source = Path(approved.common.source)
    project_source_path = Path(approved.project.source)
    git(
        project_source_path,
        "worktree",
        "remove",
        approved.project.worktree_path,
    )
    git(common_source, "worktree", "remove", approved.common.worktree_path)
    git(
        project_source_path,
        "branch",
        "--set-upstream-to",
        f"origin/{approved.project.default_branch}",
        approved.project.branch,
    )
    git(
        common_source,
        "branch",
        "--set-upstream-to",
        f"origin/{approved.common.default_branch}",
        approved.common.branch,
    )
    git(project_source_path, "branch", "-d", approved.project.branch)
    git(common_source, "branch", "-d", approved.common.branch)
    try:
        workspace_base(root).rmdir()
    except OSError:
        pass
    return {
        "status": "cleaned",
        "workspace": approved.workspace,
        "common_branch": approved.common.branch,
        "project_branch": approved.project.branch,
        "warnings": warnings,
    }


def managed_entries(repository: Path, base: Path) -> dict[str, dict[str, str]]:
    entries: dict[str, dict[str, str]] = {}
    for item in parse_worktrees(repository):
        raw = item.get("worktree")
        if not raw:
            continue
        path = Path(raw).resolve(strict=False)
        if base.resolve(strict=False) not in path.parents:
            continue
        entries[str(path)] = item
    return entries


def list_worktrees(root: Path) -> dict[str, Any]:
    base = workspace_base(root)
    common_entries = managed_entries(root, base)
    project_entries = {
        repo: managed_entries(project_source(root, repo), base)
        for repo in PROJECTS
    }
    groups: list[dict[str, Any]] = []
    seen_projects: set[str] = set()

    for common_path, common in sorted(common_entries.items()):
        workspace = Path(common_path)
        match = re.fullmatch(r"(backend|frontend)-(.+)", workspace.name)
        if not match:
            groups.append(
                {
                    "workspace": common_path,
                    "status": "unrecognized-common-worktree",
                    "common": common,
                }
            )
            continue
        repo, task = match.groups()
        project_path = str((workspace / PROJECTS[repo]).resolve(strict=False))
        project = project_entries[repo].get(project_path)
        if project:
            seen_projects.add(project_path)
        expected_branch = f"refs/heads/codex/{task}"
        synchronized = bool(
            project
            and common.get("branch") == expected_branch
            and project.get("branch") == expected_branch
        )
        groups.append(
            {
                "repo": repo,
                "task": task,
                "workspace": common_path,
                "status": "ready" if synchronized else "incomplete-or-mismatched",
                "common": common,
                "project": project or {},
            }
        )

    for repo, entries in project_entries.items():
        for path, item in entries.items():
            if path not in seen_projects:
                groups.append(
                    {
                        "repo": repo,
                        "workspace": str(Path(path).parent),
                        "status": "orphan-project-worktree",
                        "project": item,
                    }
                )
    return {
        "worktree_base": str(base),
        "groups": groups,
    }


def preview_payload(plan: WorktreePlan, warnings: list[str]) -> dict[str, Any]:
    return {
        "status": "approval_required",
        "action": plan.action,
        "repo": plan.repo,
        "workspace": plan.workspace,
        "branch": plan.common.branch,
        "common": asdict(plan.common),
        "project": asdict(plan.project),
        "warnings": warnings,
        "commands": command_plan(plan),
        "approval_token": encode_token(plan),
    }


def print_output(data: dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(data, indent=2, sort_keys=True))
        return
    for key, value in data.items():
        if isinstance(value, (list, dict)):
            print(f"{key}:")
            print(json.dumps(value, indent=2, sort_keys=True))
        else:
            print(f"{key}: {value}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", help="Override the System_bus root for tests.")
    parser.add_argument("--json", action="store_true", help="Emit JSON.")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("preview", "cleanup-preview"):
        sub = commands.add_parser(name)
        sub.add_argument("--repo", choices=sorted(PROJECTS), required=True)
        sub.add_argument("--task", required=True)
    create = commands.add_parser("create")
    create.add_argument("--approve", required=True)
    cleanup = commands.add_parser("cleanup")
    cleanup.add_argument("--approve", required=True)
    commands.add_parser("list")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        root = resolve_root(args.root)
        if args.command == "preview":
            plan, warnings = build_create_plan(root, args.repo, args.task)
            output = preview_payload(plan, warnings)
        elif args.command == "create":
            output = create_worktrees(root, decode_token(args.approve))
        elif args.command == "cleanup-preview":
            plan, warnings = build_cleanup_plan(root, args.repo, args.task)
            output = preview_payload(plan, warnings)
        elif args.command == "cleanup":
            output = cleanup_worktrees(root, decode_token(args.approve))
        else:
            output = list_worktrees(root)
        print_output(output, args.json)
        return 0
    except FlowError as exc:
        print_output({"status": "error", "message": str(exc)}, args.json)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
