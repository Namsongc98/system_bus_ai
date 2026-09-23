#!/usr/bin/env python3
"""Review-first Git worktree management for the System_bus workspace."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Optional


TOKEN_VERSION = 1
TOKEN_CONTEXT = b"system-bus-worktree-v1\0"
TASK_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SHA_RE = re.compile(r"^[0-9a-f]{40,64}$")
REPOSITORIES = {
    "backend": "ticket-system",
    "frontend": "booking_ticket_vue",
}


class FlowError(RuntimeError):
    pass


@dataclass(frozen=True)
class RemoteState:
    default_branch: str
    base_ref: str
    base_sha: str
    remote_ref: str


@dataclass(frozen=True)
class WorktreePlan:
    version: int
    action: str
    repo: str
    task: str
    source: str
    default_branch: str
    base_ref: str
    base_sha: str
    remote_ref: str
    branch: str
    wrapper: str
    project_path: str
    branch_sha: str = ""


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
        root = Path(override).expanduser().resolve()
        if not (root / ".claude").exists() or not (root / "CLAUDE.md").exists():
            raise FlowError(f"Invalid System_bus root: {root}")
        return root

    candidates = [Path.cwd().resolve(), *Path.cwd().resolve().parents]
    script_path = Path(__file__).resolve()
    candidates.extend([script_path.parent, *script_path.parents])
    for candidate in candidates:
        if (
            (candidate / ".claude").exists()
            and (candidate / "CLAUDE.md").exists()
            and any((candidate / name).exists() for name in REPOSITORIES.values())
        ):
            return candidate
    raise FlowError("Could not locate the System_bus root.")


def validate_task(task: str) -> str:
    if len(task) > 48 or not TASK_RE.fullmatch(task):
        raise FlowError(
            "Task must be 1-48 lowercase letters/digits separated by single hyphens."
        )
    return task


def repository_path(root: Path, repo: str) -> Path:
    try:
        name = REPOSITORIES[repo]
    except KeyError as exc:
        raise FlowError("Repository must be 'backend' or 'frontend'.") from exc
    return root / name


def workspace_base(root: Path) -> Path:
    return root.parent / f"{root.name}-worktrees"


def worktree_paths(root: Path, repo: str, task: str) -> tuple[Path, Path]:
    wrapper = workspace_base(root) / f"{repo}-{task}"
    project = wrapper / REPOSITORIES[repo]
    return wrapper, project


def ensure_under(path: Path, parent: Path) -> None:
    resolved_path = path.resolve(strict=False)
    resolved_parent = parent.resolve(strict=False)
    if resolved_path != resolved_parent and resolved_parent not in resolved_path.parents:
        raise FlowError(f"Path escapes worktree base: {path}")


def require_git_repository(repository: Path) -> None:
    if not repository.exists():
        raise FlowError(f"Source repository does not exist: {repository}")
    inside = git(repository, "rev-parse", "--is-inside-work-tree", check=False)
    if inside != "true":
        raise FlowError(f"Source is not a Git worktree: {repository}")


def remote_state(repository: Path) -> RemoteState:
    require_git_repository(repository)
    if not git(repository, "remote", "get-url", "origin", check=False):
        raise FlowError(f"Remote 'origin' is not configured for {repository}")

    output = git(repository, "ls-remote", "--symref", "origin", "HEAD")
    default_ref = ""
    head_sha = ""
    for line in output.splitlines():
        if line.startswith("ref: ") and line.endswith("\tHEAD"):
            default_ref = line.split()[1]
        elif line.endswith("\tHEAD"):
            head_sha = line.split()[0]
    prefix = "refs/heads/"
    if not default_ref.startswith(prefix):
        raise FlowError("origin/HEAD does not identify a remote default branch.")
    if not SHA_RE.fullmatch(head_sha):
        raise FlowError("origin/HEAD did not return a valid commit SHA.")
    default_branch = default_ref[len(prefix) :]
    return RemoteState(
        default_branch=default_branch,
        base_ref=default_ref,
        base_sha=head_sha,
        remote_ref=f"refs/remotes/origin/{default_branch}",
    )


def status_warning(repository: Path) -> str:
    status = git(repository, "status", "--porcelain=v1")
    if not status:
        return ""
    count = len(status.splitlines())
    return (
        f"Source repository has {count} changed/untracked path(s). "
        "They will not be copied into the new worktree."
    )


def local_branch_exists(repository: Path, branch: str) -> bool:
    result = run(
        ["git", "-C", str(repository), "show-ref", "--verify", "--quiet", f"refs/heads/{branch}"],
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


def registered_worktree(repository: Path, project_path: Path) -> Optional[dict[str, str]]:
    expected = str(project_path.resolve(strict=False))
    for item in parse_worktrees(repository):
        actual = item.get("worktree", "")
        if actual and str(Path(actual).resolve(strict=False)) == expected:
            return item
    return None


def build_create_plan(root: Path, repo: str, task: str) -> tuple[WorktreePlan, list[str]]:
    task = validate_task(task)
    source = repository_path(root, repo)
    state = remote_state(source)
    wrapper, project = worktree_paths(root, repo, task)
    ensure_under(wrapper, workspace_base(root))
    branch = f"claude/{task}"

    if local_branch_exists(source, branch):
        raise FlowError(f"Local branch already exists: {branch}")
    if wrapper.exists() or project.exists():
        raise FlowError(f"Worktree destination already exists: {wrapper}")
    if registered_worktree(source, project):
        raise FlowError(f"Git already registers worktree path: {project}")

    warnings = [warning for warning in [status_warning(source)] if warning]
    return (
        WorktreePlan(
            version=TOKEN_VERSION,
            action="create",
            repo=repo,
            task=task,
            source=str(source.resolve()),
            default_branch=state.default_branch,
            base_ref=state.base_ref,
            base_sha=state.base_sha,
            remote_ref=state.remote_ref,
            branch=branch,
            wrapper=str(wrapper.resolve(strict=False)),
            project_path=str(project.resolve(strict=False)),
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
        plan = WorktreePlan(**data)
    except (ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        raise FlowError("Invalid approval token.") from exc
    if plan.version != TOKEN_VERSION:
        raise FlowError("Unsupported approval token version.")
    return plan


def command_plan(plan: WorktreePlan, root: Path) -> list[str]:
    source = Path(plan.source)
    wrapper = Path(plan.wrapper)
    project = Path(plan.project_path)
    if plan.action == "create":
        return [
            command_text(
                [
                    "git",
                    "-C",
                    str(source),
                    "fetch",
                    "--no-tags",
                    "origin",
                    f"+{plan.base_ref}:{plan.remote_ref}",
                ]
            ),
            command_text(
                ["git", "-C", str(source), "worktree", "add", "-b", plan.branch, str(project), plan.base_sha]
            ),
            f"symlink {wrapper / 'CLAUDE.md'} -> {root / 'CLAUDE.md'}",
            f"symlink {wrapper / '.claude'} -> {root / '.claude'}",
        ]
    return [
        command_text(
            [
                "git",
                "-C",
                str(source),
                "fetch",
                "--no-tags",
                "origin",
                f"+{plan.base_ref}:{plan.remote_ref}",
            ]
        ),
        command_text(["git", "-C", str(source), "worktree", "remove", str(project)]),
        command_text(
            ["git", "-C", str(source), "branch", "--set-upstream-to", f"origin/{plan.default_branch}", plan.branch]
        ),
        command_text(["git", "-C", str(source), "branch", "-d", plan.branch]),
        f"unlink shared context and remove empty wrapper {wrapper}",
    ]


def compare_plan(approved: WorktreePlan, current: WorktreePlan) -> None:
    if asdict(approved) != asdict(current):
        raise FlowError(
            "Worktree state changed after preview. Run preview again and approve the new token."
        )


def fetch_approved_base(plan: WorktreePlan) -> None:
    source = Path(plan.source)
    git(source, "fetch", "--no-tags", "origin", f"+{plan.base_ref}:{plan.remote_ref}")
    fetched = git(source, "rev-parse", plan.remote_ref)
    if fetched != plan.base_sha:
        raise FlowError(
            "Remote default branch changed after approval. Run preview again."
        )


def create_worktree(root: Path, approved: WorktreePlan) -> dict[str, Any]:
    if approved.action != "create":
        raise FlowError("Approval token is not for create.")
    current, warnings = build_create_plan(root, approved.repo, approved.task)
    compare_plan(approved, current)
    fetch_approved_base(approved)

    wrapper = Path(approved.wrapper)
    project = Path(approved.project_path)
    created_wrapper = False
    try:
        wrapper.mkdir(parents=True, exist_ok=False)
        created_wrapper = True
        (wrapper / "CLAUDE.md").symlink_to(root / "CLAUDE.md")
        (wrapper / ".claude").symlink_to(root / ".claude", target_is_directory=True)
        git(
            Path(approved.source),
            "worktree",
            "add",
            "-b",
            approved.branch,
            str(project),
            approved.base_sha,
        )
    except Exception:
        if not project.exists() and created_wrapper:
            for link in (wrapper / ".claude", wrapper / "CLAUDE.md"):
                if link.is_symlink():
                    link.unlink()
            try:
                wrapper.rmdir()
            except OSError:
                pass
        raise
    return {
        "status": "created",
        "workspace": str(wrapper),
        "project": str(project),
        "branch": approved.branch,
        "warnings": warnings,
    }


def ensure_remote_commit_available(repository: Path, sha: str) -> None:
    result = run(
        ["git", "-C", str(repository), "cat-file", "-e", f"{sha}^{{commit}}"],
        check=False,
    )
    if result.returncode != 0:
        raise FlowError(
            "Remote default commit is not available locally. Fetch origin, then rerun cleanup-preview."
        )


def build_cleanup_plan(root: Path, repo: str, task: str) -> tuple[WorktreePlan, list[str]]:
    task = validate_task(task)
    source = repository_path(root, repo)
    state = remote_state(source)
    wrapper, project = worktree_paths(root, repo, task)
    ensure_under(wrapper, workspace_base(root))
    branch = f"claude/{task}"

    item = registered_worktree(source, project)
    if not item:
        raise FlowError(f"Worktree is not registered: {project}")
    registered_branch = item.get("branch", "")
    if registered_branch != f"refs/heads/{branch}":
        raise FlowError(
            f"Worktree branch mismatch: expected refs/heads/{branch}, got {registered_branch or '<detached>'}"
        )
    if git(project, "status", "--porcelain=v1"):
        raise FlowError("Worktree has uncommitted changes; cleanup is not allowed.")

    branch_sha = git(source, "rev-parse", f"refs/heads/{branch}")
    ensure_remote_commit_available(source, state.base_sha)
    merged = run(
        ["git", "-C", str(source), "merge-base", "--is-ancestor", branch_sha, state.base_sha],
        check=False,
    )
    if merged.returncode != 0:
        raise FlowError(
            f"Branch {branch} is not merged into origin/{state.default_branch}."
        )

    warnings: list[str] = []
    expected_claude_md = root / "CLAUDE.md"
    expected_claude = root / ".claude"
    if not (wrapper / "CLAUDE.md").is_symlink() or (wrapper / "CLAUDE.md").resolve() != expected_claude_md.resolve():
        warnings.append("Wrapper CLAUDE.md symlink is missing or unexpected.")
    if not (wrapper / ".claude").is_symlink() or (wrapper / ".claude").resolve() != expected_claude.resolve():
        warnings.append("Wrapper .claude symlink is missing or unexpected.")

    return (
        WorktreePlan(
            version=TOKEN_VERSION,
            action="cleanup",
            repo=repo,
            task=task,
            source=str(source.resolve()),
            default_branch=state.default_branch,
            base_ref=state.base_ref,
            base_sha=state.base_sha,
            remote_ref=state.remote_ref,
            branch=branch,
            wrapper=str(wrapper.resolve(strict=False)),
            project_path=str(project.resolve(strict=False)),
            branch_sha=branch_sha,
        ),
        warnings,
    )


def remove_wrapper(wrapper: Path) -> list[str]:
    warnings: list[str] = []
    for name in (".claude", "CLAUDE.md"):
        path = wrapper / name
        if path.is_symlink():
            path.unlink()
        elif path.exists():
            warnings.append(f"Did not remove unexpected wrapper entry: {path}")
    try:
        wrapper.rmdir()
    except OSError:
        warnings.append(f"Wrapper retained because it is not empty: {wrapper}")
    parent = wrapper.parent
    try:
        parent.rmdir()
    except OSError:
        pass
    return warnings


def cleanup_worktree(root: Path, approved: WorktreePlan) -> dict[str, Any]:
    if approved.action != "cleanup":
        raise FlowError("Approval token is not for cleanup.")
    current, warnings = build_cleanup_plan(root, approved.repo, approved.task)
    compare_plan(approved, current)
    fetch_approved_base(approved)

    source = Path(approved.source)
    project = Path(approved.project_path)
    merged = run(
        ["git", "-C", str(source), "merge-base", "--is-ancestor", approved.branch_sha, approved.base_sha],
        check=False,
    )
    if merged.returncode != 0:
        raise FlowError("Branch is no longer verified as merged; cleanup stopped.")

    git(source, "worktree", "remove", str(project))
    git(
        source,
        "branch",
        "--set-upstream-to",
        f"origin/{approved.default_branch}",
        approved.branch,
    )
    git(source, "branch", "-d", approved.branch)
    warnings.extend(remove_wrapper(Path(approved.wrapper)))
    return {
        "status": "cleaned",
        "workspace": approved.wrapper,
        "branch": approved.branch,
        "warnings": warnings,
    }


def list_worktrees(root: Path) -> dict[str, Any]:
    result: dict[str, Any] = {"worktree_base": str(workspace_base(root)), "repositories": {}}
    for repo, name in REPOSITORIES.items():
        source = root / name
        if git(source, "rev-parse", "--is-inside-work-tree", check=False) != "true":
            result["repositories"][repo] = {
                "source": str(source),
                "error": "not a Git worktree",
                "worktrees": [],
            }
            continue
        entries = []
        for item in parse_worktrees(source):
            path = Path(item.get("worktree", ""))
            wrapper = path.parent
            entries.append(
                {
                    **item,
                    "claude_wrapper": str(wrapper)
                    if workspace_base(root).resolve(strict=False) in path.resolve(strict=False).parents
                    else "",
                    "shared_claude_md": (wrapper / "CLAUDE.md").is_symlink(),
                    "shared_claude": (wrapper / ".claude").is_symlink(),
                }
            )
        result["repositories"][repo] = {
            "source": str(source),
            "worktrees": entries,
        }
    return result


def preview_payload(plan: WorktreePlan, warnings: list[str], root: Path) -> dict[str, Any]:
    return {
        "status": "approval_required",
        "action": plan.action,
        "repo": plan.repo,
        "source": plan.source,
        "remote_default": f"origin/{plan.default_branch}",
        "base_sha": plan.base_sha,
        "branch": plan.branch,
        "workspace": plan.wrapper,
        "project": plan.project_path,
        "warnings": warnings,
        "commands": command_plan(plan, root),
        "approval_token": encode_token(plan),
    }


def print_output(data: dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(data, indent=2, sort_keys=True))
        return
    for key, value in data.items():
        if isinstance(value, list):
            print(f"{key}:")
            if value:
                for item in value:
                    print(f"  - {item}")
            else:
                print("  - none")
        elif isinstance(value, dict):
            print(f"{key}:")
            print(json.dumps(value, indent=2, sort_keys=True))
        else:
            print(f"{key}: {value}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", help="Override the System_bus root (used by tests).")
    parser.add_argument("--json", action="store_true", help="Emit JSON.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    for command in ("preview", "cleanup-preview"):
        sub = subparsers.add_parser(command)
        sub.add_argument("--repo", choices=sorted(REPOSITORIES), required=True)
        sub.add_argument("--task", required=True)

    create = subparsers.add_parser("create")
    create.add_argument("--approve", required=True)

    cleanup = subparsers.add_parser("cleanup")
    cleanup.add_argument("--approve", required=True)

    subparsers.add_parser("list")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        root = resolve_root(args.root)
        if args.command == "preview":
            plan, warnings = build_create_plan(root, args.repo, args.task)
            output = preview_payload(plan, warnings, root)
        elif args.command == "create":
            output = create_worktree(root, decode_token(args.approve))
        elif args.command == "cleanup-preview":
            plan, warnings = build_cleanup_plan(root, args.repo, args.task)
            output = preview_payload(plan, warnings, root)
        elif args.command == "cleanup":
            output = cleanup_worktree(root, decode_token(args.approve))
        else:
            output = list_worktrees(root)
        print_output(output, args.json)
        return 0
    except FlowError as exc:
        error = {"status": "error", "message": str(exc)}
        print_output(error, args.json)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
