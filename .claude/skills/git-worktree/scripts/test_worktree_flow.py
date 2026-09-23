from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("worktree_flow.py")
SPEC = importlib.util.spec_from_file_location("worktree_flow", SCRIPT)
assert SPEC and SPEC.loader
flow = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = flow
SPEC.loader.exec_module(flow)


def run(*parts: str, cwd: Path | None = None) -> str:
    result = subprocess.run(
        list(parts),
        cwd=str(cwd) if cwd else None,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


class WorktreeFlowTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name)
        self.root = base / "System_bus"
        self.root.mkdir()
        (self.root / ".claude").mkdir()
        (self.root / "CLAUDE.md").write_text("# Root\n", encoding="utf-8")

        self.seed = base / "seed"
        self.remote = base / "backend.git"
        self.source = self.root / "ticket-system"
        run("git", "init", "-b", "main", str(self.seed))
        run("git", "-C", str(self.seed), "config", "user.name", "Test User")
        run("git", "-C", str(self.seed), "config", "user.email", "test@example.com")
        (self.seed / "CLAUDE.md").write_text("# Backend\n", encoding="utf-8")
        run("git", "-C", str(self.seed), "add", "CLAUDE.md")
        run("git", "-C", str(self.seed), "commit", "-m", "initial")
        run("git", "clone", "--bare", str(self.seed), str(self.remote))
        run("git", "-C", str(self.remote), "symbolic-ref", "HEAD", "refs/heads/main")
        run("git", "clone", str(self.remote), str(self.source))

    def test_slug_validation_rejects_path_traversal(self) -> None:
        for value in ("../escape", "Upper", "two--hyphens", "ends-"):
            with self.subTest(value=value), self.assertRaises(flow.FlowError):
                flow.validate_task(value)
        self.assertEqual(flow.validate_task("ticket-validation-2"), "ticket-validation-2")

    def test_token_rejects_tampering(self) -> None:
        plan, _ = flow.build_create_plan(self.root, "backend", "token-test")
        token = flow.encode_token(plan)
        with self.assertRaises(flow.FlowError):
            flow.decode_token(token[:-1] + ("0" if token[-1] != "0" else "1"))

    def test_preview_warns_for_dirty_source(self) -> None:
        (self.source / "dirty.txt").write_text("dirty\n", encoding="utf-8")
        _, warnings = flow.build_create_plan(self.root, "backend", "dirty-source")
        self.assertEqual(len(warnings), 1)
        self.assertIn("will not be copied", warnings[0])

    def test_frontend_preview_uses_frontend_repository(self) -> None:
        frontend = self.root / "booking_ticket_vue"
        run("git", "clone", str(self.remote), str(frontend))
        plan, _ = flow.build_create_plan(self.root, "frontend", "ui-review")
        self.assertEqual(Path(plan.source), frontend.resolve())
        self.assertEqual(Path(plan.project_path).name, "booking_ticket_vue")
        self.assertEqual(plan.branch, "claude/ui-review")

    def test_preview_rejects_missing_origin(self) -> None:
        run("git", "-C", str(self.source), "remote", "remove", "origin")
        with self.assertRaisesRegex(flow.FlowError, "Remote 'origin'"):
            flow.build_create_plan(self.root, "backend", "missing-origin")

    def test_preview_rejects_missing_remote_default(self) -> None:
        run(
            "git",
            "-C",
            str(self.remote),
            "symbolic-ref",
            "HEAD",
            "refs/heads/not-present",
        )
        with self.assertRaisesRegex(
            flow.FlowError, "remote default branch|valid commit SHA"
        ):
            flow.build_create_plan(self.root, "backend", "missing-default")

    def test_preview_rejects_existing_branch_and_path(self) -> None:
        run("git", "-C", str(self.source), "branch", "claude/branch-conflict")
        with self.assertRaisesRegex(flow.FlowError, "branch already exists"):
            flow.build_create_plan(self.root, "backend", "branch-conflict")

        wrapper, _ = flow.worktree_paths(self.root, "backend", "path-conflict")
        wrapper.mkdir(parents=True)
        with self.assertRaisesRegex(flow.FlowError, "destination already exists"):
            flow.build_create_plan(self.root, "backend", "path-conflict")

    def test_create_list_and_cleanup(self) -> None:
        plan, _ = flow.build_create_plan(self.root, "backend", "integration")
        created = flow.create_worktree(self.root, flow.decode_token(flow.encode_token(plan)))
        wrapper = Path(created["workspace"])
        project = Path(created["project"])
        self.assertTrue(project.exists())
        self.assertEqual((wrapper / "CLAUDE.md").resolve(), (self.root / "CLAUDE.md").resolve())
        self.assertEqual((wrapper / ".claude").resolve(), (self.root / ".claude").resolve())
        self.assertEqual((project / "CLAUDE.md").read_text(encoding="utf-8"), "# Backend\n")

        listed = flow.list_worktrees(self.root)
        paths = [
            item["worktree"]
            for item in listed["repositories"]["backend"]["worktrees"]
        ]
        self.assertIn(str(project), paths)

        cleanup_plan, _ = flow.build_cleanup_plan(self.root, "backend", "integration")
        cleaned = flow.cleanup_worktree(
            self.root, flow.decode_token(flow.encode_token(cleanup_plan))
        )
        self.assertEqual(cleaned["status"], "cleaned")
        self.assertFalse(wrapper.exists())
        self.assertFalse(flow.local_branch_exists(self.source, "claude/integration"))

    def test_create_rejects_remote_sha_change(self) -> None:
        plan, _ = flow.build_create_plan(self.root, "backend", "stale")
        token = flow.encode_token(plan)
        (self.seed / "later.txt").write_text("later\n", encoding="utf-8")
        run("git", "-C", str(self.seed), "add", "later.txt")
        run("git", "-C", str(self.seed), "commit", "-m", "later")
        run("git", "-C", str(self.seed), "push", str(self.remote), "main")

        with self.assertRaisesRegex(flow.FlowError, "state changed"):
            flow.create_worktree(self.root, flow.decode_token(token))

    def test_cleanup_rejects_dirty_and_unmerged_worktrees(self) -> None:
        dirty_plan, _ = flow.build_create_plan(self.root, "backend", "dirty-cleanup")
        dirty = flow.create_worktree(
            self.root, flow.decode_token(flow.encode_token(dirty_plan))
        )
        dirty_project = Path(dirty["project"])
        (dirty_project / "dirty.txt").write_text("dirty\n", encoding="utf-8")
        with self.assertRaisesRegex(flow.FlowError, "uncommitted changes"):
            flow.build_cleanup_plan(self.root, "backend", "dirty-cleanup")

        run("git", "-C", str(dirty_project), "clean", "-f")
        cleanup_plan, _ = flow.build_cleanup_plan(
            self.root, "backend", "dirty-cleanup"
        )
        flow.cleanup_worktree(
            self.root, flow.decode_token(flow.encode_token(cleanup_plan))
        )

        unmerged_plan, _ = flow.build_create_plan(
            self.root, "backend", "unmerged-cleanup"
        )
        unmerged = flow.create_worktree(
            self.root, flow.decode_token(flow.encode_token(unmerged_plan))
        )
        unmerged_project = Path(unmerged["project"])
        run("git", "-C", str(unmerged_project), "config", "user.name", "Test User")
        run(
            "git",
            "-C",
            str(unmerged_project),
            "config",
            "user.email",
            "test@example.com",
        )
        (unmerged_project / "change.txt").write_text("change\n", encoding="utf-8")
        run("git", "-C", str(unmerged_project), "add", "change.txt")
        run("git", "-C", str(unmerged_project), "commit", "-m", "unmerged")
        with self.assertRaisesRegex(flow.FlowError, "not merged"):
            flow.build_cleanup_plan(self.root, "backend", "unmerged-cleanup")


if __name__ == "__main__":
    unittest.main()
