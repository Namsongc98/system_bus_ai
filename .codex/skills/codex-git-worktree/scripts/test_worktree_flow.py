from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).with_name("worktree_flow.py")
SPEC = importlib.util.spec_from_file_location("worktree_flow", SCRIPT)
assert SPEC and SPEC.loader
flow = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = flow
SPEC.loader.exec_module(flow)


def run(*parts: str) -> str:
    result = subprocess.run(
        list(parts), check=True, capture_output=True, text=True
    )
    return result.stdout.strip()


class DualWorktreeFlowTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / "System_bus"
        self.common_remote = self.base / "common.git"
        self.backend_remote = self.base / "backend.git"
        self.frontend_remote = self.base / "frontend.git"

        self._make_remote(
            self.common_remote,
            {
                ".gitignore": "ticket-system/\nbooking_ticket_vue/\n.DS_Store\n",
                "AGENTS.md": "# Root\n",
                ".codex/config.md": "# Codex\n",
            },
        )
        self._make_remote(
            self.backend_remote,
            {"AGENTS.md": "# Backend\n", "pom.xml": "<project/>\n"},
        )
        self._make_remote(
            self.frontend_remote,
            {"AGENTS.md": "# Frontend\n", "package.json": "{}\n"},
        )
        run("git", "clone", str(self.common_remote), str(self.root))
        run(
            "git",
            "clone",
            str(self.backend_remote),
            str(self.root / "ticket-system"),
        )
        run(
            "git",
            "clone",
            str(self.frontend_remote),
            str(self.root / "booking_ticket_vue"),
        )

    def _make_remote(self, remote: Path, files: dict[str, str]) -> None:
        seed = remote.with_suffix(".seed")
        run("git", "init", "-b", "main", str(seed))
        run("git", "-C", str(seed), "config", "user.name", "Test User")
        run("git", "-C", str(seed), "config", "user.email", "test@example.com")
        for relative, content in files.items():
            path = seed / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        run("git", "-C", str(seed), "add", ".")
        run("git", "-C", str(seed), "commit", "-m", "initial")
        run("git", "clone", "--bare", str(seed), str(remote))
        run("git", "-C", str(remote), "symbolic-ref", "HEAD", "refs/heads/main")

    def test_slug_and_v1_token_rejected(self) -> None:
        with self.assertRaises(flow.FlowError):
            flow.validate_task("../escape")
        plan, _ = flow.build_create_plan(self.root, "backend", "token-v2")
        approval_token = flow.encode_token(plan)
        self.assertEqual(flow.decode_token(approval_token).version, 2)
        raw = flow.asdict(plan)
        raw["version"] = 1
        encoded = flow.json.dumps(raw, sort_keys=True, separators=(",", ":")).encode()
        payload = flow.base64.urlsafe_b64encode(encoded).decode().rstrip("=")
        digest = flow.hashlib.sha256(flow.TOKEN_CONTEXT + encoded).hexdigest()[:24]
        with self.assertRaisesRegex(flow.FlowError, "obsolete"):
            flow.decode_token(f"{payload}.{digest}")

    def test_offline_preview_uses_cached_origin_main(self) -> None:
        original = flow.run

        def offline(parts: list[str], **kwargs):
            if "ls-remote" in parts:
                return subprocess.CompletedProcess(parts, 1, "", "offline")
            return original(parts, **kwargs)

        with mock.patch.object(flow, "run", side_effect=offline):
            plan, warnings = flow.build_create_plan(
                self.root, "backend", "offline-preview"
            )
        self.assertEqual(plan.common.default_branch, "main")
        self.assertEqual(plan.project.default_branch, "main")
        self.assertEqual(len(warnings), 2)

    def test_root_scope_violation_is_rejected(self) -> None:
        tracked = self.root / "unexpected.txt"
        tracked.write_text("unexpected\n", encoding="utf-8")
        run("git", "-C", str(self.root), "add", "unexpected.txt")
        with self.assertRaisesRegex(flow.FlowError, "tracks paths outside"):
            flow.build_create_plan(self.root, "backend", "scope-check")

    def test_backend_create_list_cleanup(self) -> None:
        plan, _ = flow.build_create_plan(self.root, "backend", "integration")
        created = flow.create_worktrees(
            self.root, flow.decode_token(flow.encode_token(plan))
        )
        workspace = Path(created["workspace"])
        project = Path(created["project"])
        self.assertTrue((workspace / ".codex").is_dir())
        self.assertFalse((workspace / ".codex").is_symlink())
        self.assertEqual((workspace / "AGENTS.md").read_text(), "# Root\n")
        self.assertEqual((project / "AGENTS.md").read_text(), "# Backend\n")

        listed = flow.list_worktrees(self.root)
        group = next(item for item in listed["groups"] if item.get("task") == "integration")
        self.assertEqual(group["status"], "ready")

        cleanup, _ = flow.build_cleanup_plan(self.root, "backend", "integration")
        flow.cleanup_worktrees(
            self.root, flow.decode_token(flow.encode_token(cleanup))
        )
        self.assertFalse(workspace.exists())
        self.assertFalse(flow.local_branch_exists(self.root, "codex/integration"))
        self.assertFalse(
            flow.local_branch_exists(
                self.root / "ticket-system", "codex/integration"
            )
        )

    def test_frontend_create_has_matching_branches(self) -> None:
        plan, _ = flow.build_create_plan(self.root, "frontend", "ui-task")
        flow.create_worktrees(self.root, flow.decode_token(flow.encode_token(plan)))
        workspace = Path(plan.workspace)
        self.assertEqual(
            flow.git(workspace, "branch", "--show-current"), "codex/ui-task"
        )
        self.assertEqual(
            flow.git(
                workspace / "booking_ticket_vue", "branch", "--show-current"
            ),
            "codex/ui-task",
        )

    def test_stale_project_remote_sha_rejected(self) -> None:
        plan, _ = flow.build_create_plan(self.root, "backend", "stale")
        seed = self.backend_remote.with_suffix(".seed")
        (seed / "later.txt").write_text("later\n", encoding="utf-8")
        run("git", "-C", str(seed), "add", "later.txt")
        run("git", "-C", str(seed), "commit", "-m", "later")
        run("git", "-C", str(seed), "push", str(self.backend_remote), "main")
        with self.assertRaisesRegex(flow.FlowError, "state changed"):
            flow.create_worktrees(self.root, flow.decode_token(flow.encode_token(plan)))

    def test_branch_and_path_conflicts_in_either_repo(self) -> None:
        run("git", "-C", str(self.root), "branch", "codex/common-conflict")
        with self.assertRaisesRegex(flow.FlowError, "common local branch"):
            flow.build_create_plan(self.root, "backend", "common-conflict")

        backend = self.root / "ticket-system"
        run("git", "-C", str(backend), "branch", "codex/project-conflict")
        with self.assertRaisesRegex(flow.FlowError, "backend local branch"):
            flow.build_create_plan(self.root, "backend", "project-conflict")

        flow.workspace_path(self.root, "backend", "path-conflict").mkdir(parents=True)
        with self.assertRaisesRegex(flow.FlowError, "destination already exists"):
            flow.build_create_plan(self.root, "backend", "path-conflict")

    def test_create_rolls_back_common_if_project_add_fails(self) -> None:
        plan, _ = flow.build_create_plan(self.root, "backend", "rollback")
        approved = flow.decode_token(flow.encode_token(plan))
        original_git = flow.git

        def fail_project(repository: Path, *args: str, **kwargs):
            if (
                Path(repository).resolve()
                == (self.root / "ticket-system").resolve()
                and args[:2] == ("worktree", "add")
            ):
                raise flow.FlowError("simulated project failure")
            return original_git(repository, *args, **kwargs)

        with mock.patch.object(flow, "git", side_effect=fail_project):
            with self.assertRaisesRegex(flow.FlowError, "simulated"):
                flow.create_worktrees(self.root, approved)
        self.assertFalse(Path(plan.workspace).exists())
        self.assertFalse(flow.local_branch_exists(self.root, "codex/rollback"))
        self.assertFalse(
            flow.local_branch_exists(
                self.root / "ticket-system", "codex/rollback"
            )
        )

    def test_cleanup_rejects_dirty_or_unmerged_common_and_project(self) -> None:
        dirty_plan, _ = flow.build_create_plan(
            self.root, "backend", "dirty-common"
        )
        flow.create_worktrees(
            self.root, flow.decode_token(flow.encode_token(dirty_plan))
        )
        workspace = Path(dirty_plan.workspace)
        (workspace / "dirty.txt").write_text("dirty\n", encoding="utf-8")
        with self.assertRaisesRegex(flow.FlowError, "uncommitted changes"):
            flow.build_cleanup_plan(self.root, "backend", "dirty-common")
        run("git", "-C", str(workspace), "clean", "-f")
        clean_plan, _ = flow.build_cleanup_plan(
            self.root, "backend", "dirty-common"
        )
        flow.cleanup_worktrees(
            self.root, flow.decode_token(flow.encode_token(clean_plan))
        )

        project_dirty_plan, _ = flow.build_create_plan(
            self.root, "backend", "dirty-project"
        )
        flow.create_worktrees(
            self.root,
            flow.decode_token(flow.encode_token(project_dirty_plan)),
        )
        project_dirty = Path(project_dirty_plan.project.worktree_path)
        (project_dirty / "dirty.txt").write_text("dirty\n", encoding="utf-8")
        with self.assertRaisesRegex(flow.FlowError, "uncommitted changes"):
            flow.build_cleanup_plan(self.root, "backend", "dirty-project")
        run("git", "-C", str(project_dirty), "clean", "-f")
        clean_plan, _ = flow.build_cleanup_plan(
            self.root, "backend", "dirty-project"
        )
        flow.cleanup_worktrees(
            self.root, flow.decode_token(flow.encode_token(clean_plan))
        )

        unmerged_project_plan, _ = flow.build_create_plan(
            self.root, "backend", "unmerged-project"
        )
        flow.create_worktrees(
            self.root,
            flow.decode_token(flow.encode_token(unmerged_project_plan)),
        )
        project = Path(unmerged_project_plan.project.worktree_path)
        run("git", "-C", str(project), "config", "user.name", "Test User")
        run("git", "-C", str(project), "config", "user.email", "test@example.com")
        (project / "change.txt").write_text("change\n", encoding="utf-8")
        run("git", "-C", str(project), "add", "change.txt")
        run("git", "-C", str(project), "commit", "-m", "unmerged")
        with self.assertRaisesRegex(flow.FlowError, "not merged"):
            flow.build_cleanup_plan(
                self.root, "backend", "unmerged-project"
            )

        unmerged_common_plan, _ = flow.build_create_plan(
            self.root, "frontend", "unmerged-common"
        )
        flow.create_worktrees(
            self.root,
            flow.decode_token(flow.encode_token(unmerged_common_plan)),
        )
        common = Path(unmerged_common_plan.common.worktree_path)
        run("git", "-C", str(common), "config", "user.name", "Test User")
        run("git", "-C", str(common), "config", "user.email", "test@example.com")
        (common / "change.md").write_text("change\n", encoding="utf-8")
        run("git", "-C", str(common), "add", "change.md")
        run("git", "-C", str(common), "commit", "-m", "unmerged")
        with self.assertRaisesRegex(flow.FlowError, "not merged"):
            flow.build_cleanup_plan(
                self.root, "frontend", "unmerged-common"
            )


if __name__ == "__main__":
    unittest.main()
