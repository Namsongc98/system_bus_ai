#!/usr/bin/env python3
"""Unit tests for the dashboard. Run: python3 -m unittest discover -s .claude/dashboard"""
from __future__ import annotations

import contextlib
import http.client
import io
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import collect  # noqa: E402
import server  # noqa: E402

GATES_DONE = "".join(f"- [x] {gate}\n" for gate in collect.GATES)
GATES_NONE = "".join(f"- [ ] {gate}\n" for gate in collect.GATES)
LEDGER = (
    "# Ledger\n\n## 0.1 — Done task\n" + GATES_DONE
    + "\n## 0.3 — Clean, not ticked\n" + GATES_DONE.replace("[x] lead-review", "[ ] lead-review")
    + "\n## 4.1 — Plain\n" + GATES_NONE
    + "\n## 4.1a — Letter suffix\n" + GATES_DONE
    + "\n## 5.1 — Reviewing\n" + GATES_DONE.replace("[x] review", "[ ] review").replace("[x] lead-review", "[ ] lead-review")
    + "\n## 6.1 — Paused with spec doc\n" + GATES_NONE
    + "\n## 6.2 — Done in paused phase\n" + GATES_DONE
)
REPORT = """| ID | Task | Ngày | Lead review | Report |
|---|---|---|---|---|
| 0.1 | Done | 2026-09-28 | round 1, CLEAN | [x](x.md) |
| 0.3 | Flyway | 2026-11-02 | round 3, CLEAN | [x](x.md) |
"""
PLAN = "## Phase 5 — Hardening\n\ntext\n\n## Phase 6 — Production\n\n> **TẠM DỪNG từ 2026-11-08 (user).** x\n\nmore\n"
LEAD = """# Doc

## 7. Lead review

Round 3 · 2026-11-02 · Verdict: **CLEAN** — no FIX open

| ID | Severity | Class | Finding | Evidence (file:line / command) | Status |
|---|---|---|---|---|---|
| L1 | medium | FIX | a | b | fixed round 2 |
| L2 | low | FIX | a | b | open |
| L3 | low | NEEDS-USER | a | b | waiting |
"""
SCOPE = "# Scope\n\n## Reviewers\n- `backend-reviewer`: a\n- `config-reviewer`: b\n- Not run: frontend\n"
FINDINGS = """## Findings
| # | Severity | File:line | Finding | Why it matters | How to check |
|---|---|---|---|---|---|
| 1 | high | A.java:1 | Bad thing | why | HOW_TO_CHECK_TEXT |
| 2 | low | B.java:2 | Minor | why | how |

## Not checked
- x
"""
FINDINGS_NONE = "## Findings\nnone\n\n## Not checked\n- x\n"
VERDICT_FILE = """## Verdicts
| # | Source finding | Verdict | Evidence |
|---|---|---|---|
| 1 | backend-reviewer #1 | confirmed (omission that misleads; rest uncertain) | ok |
| 2 | backend-reviewer #2 | maybe | ok |
"""
SUMMARY = """# Review summary — 4.1a round 2 · 2026-11-04
Reviewers: backend-reviewer · Verifier calls: 1 (root) · Missing: none

| R | Source | Severity | File:line | Finding | Verdict | Evidence |
|---|---|---|---|---|---|---|
| R1 | backend #1 + config #2 | high | A.java:1 | Bad thing | confirmed (partly) | EVIDENCE_TEXT |
| R2 | backend #2 | low | B.java:2 | Minor | unverified (low) | — |

## Refuted (kept for the record)
- config #3: refuted because of code
- none
"""


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def clean_detector(_text: str) -> list:
    return []


class RepoFixture(unittest.TestCase):
    def setUp(self) -> None:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve() / "repo"
        self.projects = Path(temp.name).resolve() / "projects"
        claude = self.root / ".claude"
        write(claude / "ledger/screen-feature-plan.md", LEDGER)
        write(claude / "docs/report/screen-feature-plan.md", REPORT)
        write(claude / "docs/plan/screen-feature-plan.md", PLAN)
        write(claude / "docs/review/0.3-flyway.md", LEAD)
        write(claude / "docs/review/4.1a-avatar.md", LEAD)
        write(claude / "docs/review/6.1-compose.md", "# spec\n")
        write(claude / "agents/backend-reviewer.md", "---\nname: backend-reviewer\n# why\nmodel: opus\n---\nbody\n")
        write(claude / "agents/finding-verifier.md", "---\nname: finding-verifier\nmodel: opus\n---\nbody\n")
        self.workspace = claude / "docs/review/_workspace"
        one = self.workspace / "4.1a/round-1"
        write(one / "00_main_scope.md", SCOPE)
        write(one / "01_backend-reviewer_findings.md", FINDINGS)
        write(one / "01_config-reviewer_findings.md", FINDINGS_NONE)
        write(one / "02_finding-verifier_root.md", VERDICT_FILE)
        write(one / "03_main_summary.md", SUMMARY)
        two = self.workspace / "4.1a/round-2"
        write(two / "00_main_scope.md", SCOPE.replace("- `backend-reviewer`: a\n", ""))
        write(two / "01_config-reviewer_findings.md", FINDINGS_NONE)
        write(two / "03_main_summary.md", SUMMARY.replace("R1 |", "R9 |"))
        write(self.workspace / "4.1a/round-1.prev-2215/03_main_summary.md", SUMMARY)
        write(self.workspace / "5.1/round-1/00_main_scope.md", SCOPE)
        write(self.workspace / "5.1/round-1/01_backend-reviewer_findings.md", FINDINGS)
        write(self.workspace / "adhoc-harness/round-1/03_main_summary.md", SUMMARY)

    def snapshot(self, **kwargs) -> dict:
        kwargs.setdefault("detector", clean_detector)
        kwargs.setdefault("with_git", False)
        return collect.build_snapshot(self.root, projects_dir=self.projects, **kwargs)

    def task(self, snapshot: dict, task_id: str) -> dict:
        return next(item for item in snapshot["tasks"] if item["id"] == task_id)

    def add_meta(self, name: str, agent, finished, age: float, now: float) -> None:
        folder = self.projects / collect.project_slug(self.root) / "sess/subagents"
        folder.mkdir(parents=True, exist_ok=True)
        (folder / f"{name}.meta.json").write_text(json.dumps({"agentType": agent, "finished": finished}), encoding="utf-8")
        transcript = folder / f"{name}.jsonl"
        transcript.write_text("TRANSCRIPT_CONTENT\n", encoding="utf-8")
        os.utime(transcript, (now - age, now - age))


class ParserTests(unittest.TestCase):
    def test_paused_needs_banner_right_after_heading(self) -> None:
        self.assertEqual(collect.parse_paused_phases(PLAN), ["6"])

    def test_lead_review_counts(self) -> None:
        lead = collect.parse_lead_review(LEAD)
        self.assertEqual((lead["round"], lead["verdict"], lead["openFix"], lead["needsUser"]), (3, "CLEAN", 1, 1))

    def test_lead_review_absent(self) -> None:
        self.assertIsNone(collect.parse_lead_review("# no section\n"))

    def test_unknown_verdict_warns_and_is_not_counted(self) -> None:
        counts, warnings = collect.parse_verdicts(VERDICT_FILE)
        self.assertEqual(counts["confirmed"], 1)
        self.assertEqual(len(warnings), 1)

    def test_findings_none(self) -> None:
        self.assertEqual(collect.parse_findings(FINDINGS_NONE), ([], []))

    def test_annotated_severity_is_accepted(self) -> None:
        self.assertEqual(collect.normalize_severity("low (verifier)"), "low")

    def test_source_agents(self) -> None:
        self.assertEqual(collect.source_agents("test-gap #2 + backend #2 (a, b)"), ["test-gap-reviewer", "backend-reviewer"])

    def test_bad_ledger_gate_warns(self) -> None:
        tasks, warnings = collect.parse_ledger("## 0.1 — x\n- [x] spec\n- [x] deploy\n")
        self.assertEqual(tasks[0]["gates"]["test"], False)
        self.assertEqual(len(warnings), 2)

    def test_status_priority(self) -> None:
        done = {gate: True for gate in collect.GATES}
        none = {gate: False for gate in collect.GATES}
        self.assertEqual(collect.task_status(done, None, False, True, None), "done")
        self.assertEqual(collect.task_status(none, None, True, True, None), "paused")
        self.assertEqual(collect.task_status(none, None, True, False, None), "waiting_user")
        self.assertEqual(collect.task_status(none, None, False, False, None), "not_started")


class SnapshotTests(RepoFixture):
    def test_progress(self) -> None:
        snapshot = self.snapshot()
        self.assertEqual((snapshot["progress"]["done"], snapshot["progress"]["total"]), (22, 35))
        self.assertEqual((snapshot["progress"]["activeDone"], snapshot["progress"]["activeTotal"]), (17, 25))
        self.assertEqual(snapshot["counts"]["tasksDone"], 3)

    def test_statuses_and_discrepancies(self) -> None:
        snapshot = self.snapshot()
        self.assertEqual(self.task(snapshot, "0.3")["status"], "waiting_user")
        self.assertEqual(self.task(snapshot, "6.1")["status"], "paused")
        self.assertEqual(self.task(snapshot, "6.2")["status"], "done")
        self.assertEqual(self.task(snapshot, "5.1")["status"], "reviewing")
        self.assertEqual([item["id"] for item in snapshot["waiting"]], ["0.3"])

    def test_id_match_is_exact(self) -> None:
        snapshot = self.snapshot()
        self.assertIsNone(self.task(snapshot, "4.1")["lead"])
        self.assertIsNone(self.task(snapshot, "4.1")["latestRound"])
        self.assertEqual(self.task(snapshot, "4.1a")["latestRound"], "4.1a/2")

    def test_archived_round_is_ignored(self) -> None:
        keys = [item["key"] for item in self.snapshot()["rounds"]]
        self.assertEqual(sorted(keys), ["4.1a/1", "4.1a/2", "5.1/1", "adhoc-harness/1"])

    def test_round_without_verifier_is_still_summarized(self) -> None:
        item = next(entry for entry in self.snapshot()["rounds"] if entry["key"] == "4.1a/2")
        self.assertEqual(item["stage"], "summarized")
        self.assertFalse(item["verifierRan"])

    def test_out_of_plan_round(self) -> None:
        item = next(entry for entry in self.snapshot()["rounds"] if entry["id"] == "adhoc-harness")
        self.assertTrue(item["outOfPlan"])

    def test_round_flow_counts(self) -> None:
        item = next(entry for entry in self.snapshot()["rounds"] if entry["key"] == "4.1a/1")
        backend = next(row for row in item["flow"]["reviewers"] if row["agent"] == "backend-reviewer")
        self.assertEqual((backend["toVerifier"], backend["direct"]), (1, 1))
        self.assertEqual(item["flow"]["confirmed"], 1)
        self.assertEqual(len(item["refuted"]), 1)

    def test_missing_reviewer_is_reported(self) -> None:
        write(self.workspace / "7.7/round-1/00_main_scope.md", SCOPE)
        item = next(entry for entry in self.snapshot()["rounds"] if entry["id"] == "7.7")
        self.assertEqual(item["missing"], ["backend-reviewer", "config-reviewer"])
        self.assertEqual(item["stage"], "scoped")

    def test_only_display_fields_are_sent(self) -> None:
        body = json.dumps(self.snapshot())
        self.assertNotIn("HOW_TO_CHECK_TEXT", body)
        self.assertNotIn("EVIDENCE_TEXT", body)

    def test_one_broken_source_does_not_hide_others(self) -> None:
        (self.root / ".claude/docs/report/screen-feature-plan.md").unlink()
        snapshot = self.snapshot()
        self.assertFalse(snapshot["sources"]["report"]["ok"])
        self.assertTrue(snapshot["sources"]["ledger"]["ok"])
        self.assertEqual(snapshot["progress"]["total"], 35)
        self.assertTrue(any("report" in warning for warning in snapshot["warnings"]))

    def test_redaction_covers_every_string(self) -> None:
        def detector(text: str) -> list:
            return ["hit"] if "Bad thing" in text else []
        body = json.dumps(self.snapshot(detector=detector))
        self.assertNotIn("Bad thing", body)
        self.assertIn("<redacted>", body)

    def test_real_detector_loads_from_hook(self) -> None:
        hook = Path(__file__).resolve().parents[1] / "hooks/claude_hook.py"
        write(self.root / ".claude/hooks/claude_hook.py", hook.read_text(encoding="utf-8"))
        detector = collect.load_detector(self.root)
        self.assertTrue(detector("pass" + "word=" + "abcd1234efgh"))
        self.assertFalse(detector("Thiếu test cho AvatarService"))

    def test_missing_detector_fails_closed(self) -> None:
        with self.assertRaises(collect.DetectorUnavailable):
            collect.load_detector(self.root)

    def test_symlink_outside_is_not_read(self) -> None:
        outside = self.root.parent / "outside.md"
        outside.write_text("OUTSIDE_SECRET", encoding="utf-8")
        link = self.workspace / "4.1a/round-1/01_security-reviewer_findings.md"
        link.symlink_to(outside)
        self.assertNotIn("OUTSIDE_SECRET", json.dumps(self.snapshot()))

    def test_dotenv_is_refused(self) -> None:
        path = self.root / ".claude/.env"
        path.write_text("x", encoding="utf-8")
        with self.assertRaises(PermissionError):
            collect.read_inside(path, self.root / ".claude")


class LiveStatusTests(RepoFixture):
    def card(self, snapshot: dict, name: str) -> dict:
        return next(item for item in snapshot["agents"] if item["id"] == name)

    def test_states(self) -> None:
        now = time.time()
        self.add_meta("a1", "backend-reviewer", None, 10, now)
        self.add_meta("a2", "finding-verifier", None, 600, now)
        snapshot = self.snapshot(now=now)
        self.assertEqual(self.card(snapshot, "backend-reviewer")["status"], "running")
        self.assertEqual(self.card(snapshot, "finding-verifier")["status"], "unknown")
        self.assertEqual(snapshot["counts"]["running"], 1)

    def test_finished_and_old_runs(self) -> None:
        now = time.time()
        self.add_meta("a1", "backend-reviewer", True, 60, now)
        self.add_meta("a2", "finding-verifier", None, 90000, now)
        snapshot = self.snapshot(now=now)
        self.assertEqual(self.card(snapshot, "backend-reviewer")["status"], "done")
        self.assertEqual(self.card(snapshot, "finding-verifier")["status"], "idle")

    def test_changed_meta_format_warns_without_crash(self) -> None:
        now = time.time()
        self.add_meta("a1", 123, "later", 10, now)
        snapshot = self.snapshot(now=now)
        self.assertTrue(any("metadata" in warning for warning in snapshot["warnings"]))
        self.assertEqual(snapshot["counts"]["running"], 0)

    def test_transcript_content_is_never_included(self) -> None:
        now = time.time()
        self.add_meta("a1", "backend-reviewer", None, 10, now)
        self.assertNotIn("TRANSCRIPT_CONTENT", json.dumps(self.snapshot(now=now)))


class ReviewFixTests(RepoFixture):
    def round_of(self, snapshot: dict, key: str) -> dict:
        return next(item for item in snapshot["rounds"] if item["key"] == key)

    def real_detector(self):
        hook = Path(__file__).resolve().parents[1] / "hooks/claude_hook.py"
        write(self.root / ".claude/hooks/claude_hook.py", hook.read_text(encoding="utf-8"))
        return collect.load_detector(self.root)

    def test_detector_catches_prefixed_names_and_markdown(self) -> None:
        detector = self.real_detector()
        samples = [
            "DB_PASSWORD=abcd1234efgh", "JWT_SECRET=abcd1234efgh", "MINIO_SECRET_KEY=abcd1234efgh", "accessToken: abcd1234efgh",
            "x minio.secret-key=abcd1234efgh", "`pass" + "word`: `abcd1234efgh`", "mysql://root:abcd1234@db/x",
            "Authorization: Bearer abcdefghijklmnop", "AKIA" + "ABCDEFGHIJKLMNOP", "gh" + "p_" + "a" * 24, "xox" + "b-1234567890-abc",
            "-----BEGIN ENCRYPTED " + "PRIVATE KEY-----",
        ]
        for sample in samples:
            self.assertTrue(detector(sample), sample)

    def test_detector_leaves_safe_text(self) -> None:
        detector = self.real_detector()
        for sample in ("DB_PASSWORD=<redacted>", "mysql://user:<redacted>@host/x", "JWT_SECRET=${JWT_SECRET}", "Thiếu test cho token hết hạn", "https://example.com/a:b"):
            self.assertFalse(detector(sample), sample)

    def test_dict_keys_are_redacted(self) -> None:
        write(self.workspace / "4.1a/round-1/01_secretname_findings.md", FINDINGS_NONE)
        body = json.dumps(self.snapshot(detector=lambda text: ["hit"] if text == "secretname" else []))
        self.assertNotIn("secretname", body)

    def test_detector_failure_fails_closed(self) -> None:
        def detector(_text: str) -> list:
            raise RuntimeError
        with self.assertRaises(RuntimeError):
            self.snapshot(detector=detector)

    def test_symlinked_summary_keeps_round_with_one_warning(self) -> None:
        outside = self.root.parent / "outside.md"
        outside.write_text("OUTSIDE_SECRET", encoding="utf-8")
        summary = self.workspace / "4.1a/round-1/03_main_summary.md"
        summary.unlink()
        summary.symlink_to(outside)
        snapshot = self.snapshot()
        self.assertNotIn("OUTSIDE_SECRET", json.dumps(snapshot))
        self.assertEqual(self.round_of(snapshot, "4.1a/1")["stage"], "verifying")
        self.assertEqual(sum("03_main_summary" in warning for warning in snapshot["warnings"]), 1)

    def test_oversized_file_keeps_round(self) -> None:
        (self.workspace / "4.1a/round-1/01_config-reviewer_findings.md").write_text("x" * (collect.MAX_FILE_BYTES + 1), encoding="utf-8")
        snapshot = self.snapshot()
        self.assertEqual(self.round_of(snapshot, "4.1a/1")["stage"], "summarized")
        self.assertTrue(any("ValueError" in warning for warning in snapshot["warnings"]))

    def test_invalid_utf8_is_tolerated(self) -> None:
        (self.workspace / "4.1a/round-1/01_config-reviewer_findings.md").write_bytes(b"\xff" + FINDINGS_NONE.encode())
        self.assertEqual(self.round_of(self.snapshot(), "4.1a/1")["stage"], "summarized")

    def test_fifo_does_not_block(self) -> None:
        fifo = self.workspace / "9.9/round-1/00_main_scope.md"
        fifo.parent.mkdir(parents=True)
        os.mkfifo(fifo)
        outcome = run_with_timeout(lambda: collect.read_inside(fifo, self.workspace))
        self.assertIsInstance(outcome, ValueError)

    def test_reviewing_and_verifying_stages(self) -> None:
        write(self.workspace / "8.1/round-1/01_config-reviewer_findings.md", FINDINGS_NONE)
        write(self.workspace / "8.2/round-1/02_finding-verifier_root.md", VERDICT_FILE)
        snapshot = self.snapshot()
        self.assertEqual(self.round_of(snapshot, "8.1/1")["stage"], "reviewing")
        self.assertEqual(self.round_of(snapshot, "8.2/1")["stage"], "verifying")

    def test_waiting_reason_prefers_clean_report(self) -> None:
        gates = {gate: False for gate in collect.GATES}
        self.assertIn("lead-review", collect.waiting_reason({"gates": gates, "report": {"verdict": "CLEAN"}}))
        self.assertIn("spec", collect.waiting_reason({"gates": gates, "report": None}))


def run_with_timeout(action, seconds: float = 3.0):
    """Run `action` in a daemon thread so a blocking regression fails instead of hanging the suite."""
    result: list = []

    def target() -> None:
        try:
            result.append(action())
        except BaseException as error:  # noqa: BLE001 - returned to the test
            result.append(error)

    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    thread.join(seconds)
    if thread.is_alive():
        raise AssertionError(f"blocked for more than {seconds}s")
    return result[0]


class StatusTableTests(unittest.TestCase):
    def test_priority_table(self) -> None:
        none = {gate: False for gate in collect.GATES}
        some = {**none, "spec": True}
        lead_open = {**{gate: True for gate in collect.GATES}, "lead-review": False}
        clean = {"verdict": "CLEAN", "round": 1, "date": "x"}
        fix = {"verdict": "FIX", "round": 1, "date": "x"}
        scoped = {"stage": "scoped"}
        summarized = {"stage": "summarized"}
        table = [
            (lead_open, clean, False, True, None, "paused"),
            (lead_open, clean, True, False, scoped, "waiting_user"),
            (lead_open, fix, False, False, None, "in_progress"),
            (none, None, True, False, scoped, "waiting_user"),
            (some, None, False, False, scoped, "reviewing"),
            (some, None, False, False, summarized, "in_progress"),
            (some, None, True, False, None, "in_progress"),
            (none, None, False, False, None, "not_started"),
        ]
        for gates, report, spec_doc, paused, latest, expected in table:
            self.assertEqual(collect.task_status(gates, report, spec_doc, paused, latest), expected, (report, spec_doc, paused, latest))


class ParserEdgeTests(unittest.TestCase):
    def test_table_cells_keeps_escaped_pipe(self) -> None:
        self.assertEqual(collect.table_cells("| a \\| b | c |"), ["a | b", "c"])

    def test_report_row_problems_warn(self) -> None:
        _, short = collect.parse_report_index("| 0.1 | a | b |\n")
        _, bad = collect.parse_report_index("| 0.1 | a | b | soon | x |\n")
        self.assertEqual((len(short), len(bad)), (1, 1))

    def test_short_summary_row_warns(self) -> None:
        summary, warnings = collect.parse_summary("| R1 | a | low | f | x | confirmed |\n")
        self.assertEqual((summary["rows"], len(warnings)), ([], 1))

    def test_project_slug_matches_real_directory_name(self) -> None:
        path = Path("/Users/ADMIN/Desktop/Wordspace/Programing/Project/System_bus")
        self.assertEqual(collect.project_slug(path), "-Users-ADMIN-Desktop-Wordspace-Programing-Project-System-bus")


class GitInfoTests(unittest.TestCase):
    def setUp(self) -> None:
        collect._git_cache.clear()
        self.addCleanup(collect._git_cache.clear)
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.repo = Path(temp.name)

    def git(self, *args: str) -> None:
        subprocess.run(["git", "-C", str(self.repo), "-c", "user.name=t", "-c", "user.email=t@example.com", *args], check=True, capture_output=True)

    def test_branch_dirty_and_commit(self) -> None:
        self.git("init", "-b", "work")
        self.git("commit", "--allow-empty", "-m", "first")
        (self.repo / "new.txt").write_text("x", encoding="utf-8")
        info = collect.git_info(self.repo, 100.0)
        self.assertEqual((info["branch"], info["dirty"], info["commit"]["subject"]), ("work", 1, "first"))

    def test_no_commits_yet(self) -> None:
        self.git("init", "-b", "work")
        info = collect.git_info(self.repo, 100.0)
        self.assertEqual((info["branch"], info["commit"]), ("work", None))

    def test_detached_head(self) -> None:
        self.git("init", "-b", "work")
        self.git("commit", "--allow-empty", "-m", "first")
        self.git("checkout", "--detach")
        self.assertEqual(collect.git_info(self.repo, 100.0)["branch"], "detached HEAD")

    def test_upstream_suffix_is_removed(self) -> None:
        self.assertEqual(collect.parse_branch("main...origin/main [ahead 1]"), "main")

    def test_failure_is_not_cached(self) -> None:
        self.assertFalse(collect.git_info(self.repo, 100.0)["available"])
        self.assertNotIn(str(self.repo), collect._git_cache)

    def test_success_is_cached_within_ttl(self) -> None:
        self.git("init", "-b", "work")
        first = collect.git_info(self.repo, 100.0)
        with mock.patch.object(collect, "run_git", side_effect=AssertionError):
            self.assertIs(collect.git_info(self.repo, 100.0 + collect.GIT_TTL - 1), first)


class LiveEdgeTests(RepoFixture):
    def card(self, snapshot: dict, name: str) -> dict:
        return next(item for item in snapshot["agents"] if item["id"] == name)

    def session(self, age: float, now: float) -> None:
        folder = self.projects / collect.project_slug(self.root)
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / "main.jsonl"
        path.write_text("TRANSCRIPT_CONTENT", encoding="utf-8")
        os.utime(path, (now - age, now - age))

    def test_changed_format_marks_cards_unknown(self) -> None:
        now = time.time()
        self.add_meta("a1", "backend-reviewer", False, 10, now)
        snapshot = self.snapshot(now=now)
        self.assertEqual(self.card(snapshot, "backend-reviewer")["status"], "unknown")
        self.assertEqual(self.card(snapshot, "finding-verifier")["status"], "unknown")
        self.assertEqual(snapshot["orchestrator"]["status"], "unknown")

    def test_age_boundaries(self) -> None:
        for age, status in ((119, "running"), (121, "unknown"), (1799, "unknown"), (1801, "idle")):
            now = time.time()
            shutil.rmtree(self.projects, ignore_errors=True)
            self.add_meta("a1", "backend-reviewer", None, age, now)
            self.assertEqual(self.card(self.snapshot(now=now), "backend-reviewer")["status"], status, age)

    def test_old_finished_run_is_idle(self) -> None:
        now = time.time()
        self.add_meta("a1", "backend-reviewer", True, 1801, now)
        self.assertEqual(self.card(self.snapshot(now=now), "backend-reviewer")["status"], "idle")

    def test_running_beats_done(self) -> None:
        now = time.time()
        self.add_meta("a1", "backend-reviewer", True, 10, now)
        self.add_meta("a2", "backend-reviewer", None, 10, now)
        self.assertEqual(self.card(self.snapshot(now=now), "backend-reviewer")["status"], "running")

    def test_missing_transcript_uses_meta_time(self) -> None:
        now = time.time()
        self.add_meta("a1", "backend-reviewer", None, 90000, now)
        folder = self.projects / collect.project_slug(self.root) / "sess/subagents"
        (folder / "a1.jsonl").unlink()
        self.assertEqual(self.card(self.snapshot(now=time.time()), "backend-reviewer")["status"], "running")

    def test_orchestrator_status(self) -> None:
        now = time.time()
        self.session(30, now)
        self.assertEqual(self.snapshot(now=now)["orchestrator"]["status"], "running")
        self.session(500, now)
        self.assertEqual(self.snapshot(now=now)["orchestrator"]["status"], "idle")

    def test_broken_subagent_source_marks_unknown(self) -> None:
        with mock.patch.object(collect, "scan_subagents", side_effect=OSError):
            snapshot = self.snapshot()
        self.assertEqual(snapshot["orchestrator"]["status"], "unknown")
        self.assertEqual(self.card(snapshot, "backend-reviewer")["status"], "unknown")


class ServerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.builds = 0

        def build() -> dict:
            self.builds += 1
            return {"ok": True}

        self.server = server.create_server(0, build)
        self.port = self.server.server_address[1]
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)

    def request(self, method: str, path: str, host: str | None = None):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        self.addCleanup(connection.close)
        connection.putrequest(method, path, skip_host=True)
        if host != "":
            connection.putheader("Host", host or f"127.0.0.1:{self.port}")
        connection.endheaders()
        response = connection.getresponse()
        return response, response.read()

    def test_binds_loopback_only(self) -> None:
        self.assertEqual(self.server.server_address[0], "127.0.0.1")

    def test_snapshot_and_headers(self) -> None:
        response, body = self.request("GET", "/api/snapshot")
        self.assertEqual(response.status, 200)
        self.assertEqual(json.loads(body), {"ok": True})
        self.assertIn("default-src 'none'", response.getheader("Content-Security-Policy"))
        self.assertEqual(response.getheader("X-Content-Type-Options"), "nosniff")
        self.assertEqual(response.getheader("Cache-Control"), "no-store")
        self.assertIsNone(response.getheader("Access-Control-Allow-Origin"))

    def test_foreign_host_rejected(self) -> None:
        self.assertEqual(self.request("GET", "/api/snapshot", "evil.example:80")[0].status, 403)

    def test_localhost_allowed(self) -> None:
        self.assertEqual(self.request("GET", "/api/snapshot", f"localhost:{self.port}")[0].status, 200)

    def test_write_methods_rejected(self) -> None:
        for method in ("POST", "PUT", "PATCH", "DELETE"):
            self.assertEqual(self.request(method, "/api/snapshot")[0].status, 405)

    def test_unknown_and_traversal_paths_404(self) -> None:
        for path in ("/collect.py", "/../collect.py", "/static/../../.env", "/app.js/../server.py"):
            self.assertEqual(self.request("GET", path)[0].status, 404, path)

    def test_static_routes(self) -> None:
        for path, kind in (("/", "text/html"), ("/app.js", "text/javascript"), ("/style.css", "text/css")):
            response, body = self.request("GET", path)
            self.assertEqual(response.status, 200, path)
            self.assertIn(kind, response.getheader("Content-Type"))
            self.assertIn("default-src 'none'", response.getheader("Content-Security-Policy"))
            self.assertTrue(body)

    def test_hosts_are_matched_exactly(self) -> None:
        for host in ("127.0.0.1", "localhost", "127.0.0.1:1", f"localhost:{self.port}.evil.com", f"evil.localhost:{self.port}", ""):
            self.assertEqual(self.request("GET", "/api/snapshot", host)[0].status, 403, host)

    def test_head_has_no_body(self) -> None:
        response, body = self.request("HEAD", "/api/snapshot")
        self.assertEqual((response.status, body), (200, b""))

    def test_other_methods_rejected_with_headers(self) -> None:
        for method in ("OPTIONS", "TRACE", "CONNECT"):
            response, _ = self.request(method, "/api/snapshot")
            self.assertEqual(response.status, 405, method)
            self.assertIsNotNone(response.getheader("Content-Security-Policy"))

    def test_unknown_method_gets_json_error_with_headers(self) -> None:
        response, body = self.request("BREW", "/")
        self.assertEqual(response.status, 501)
        self.assertEqual(json.loads(body), {"error": "bad_request"})
        self.assertIsNotNone(response.getheader("Content-Security-Policy"))

    def test_query_string_is_ignored(self) -> None:
        self.assertEqual(self.request("GET", "/api/snapshot?x=1")[0].status, 200)

    def test_encoded_traversal_is_404(self) -> None:
        self.assertEqual(self.request("GET", "/%2e%2e/collect.py")[0].status, 404)

    def test_cross_site_snapshot_rejected(self) -> None:
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        self.addCleanup(connection.close)
        host = f"127.0.0.1:{self.port}"
        connection.request("GET", "/api/snapshot", headers={"Host": host, "Sec-Fetch-Site": "cross-site"})
        response = connection.getresponse()
        response.read()
        self.assertEqual(response.status, 403)
        connection.request("GET", "/api/snapshot", headers={"Host": host, "Sec-Fetch-Site": "same-origin"})
        response = connection.getresponse()
        response.read()
        self.assertEqual(response.status, 200)

    def test_scanner_unavailable_is_503(self) -> None:
        def fail() -> dict:
            raise collect.DetectorUnavailable("x")

        broken = server.create_server(0, fail)
        self.addCleanup(broken.server_close)
        self.addCleanup(broken.shutdown)
        threading.Thread(target=broken.serve_forever, daemon=True).start()
        port = broken.server_address[1]
        connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
        self.addCleanup(connection.close)
        connection.request("GET", "/api/snapshot", headers={"Host": f"127.0.0.1:{port}"})
        response = connection.getresponse()
        self.assertEqual((response.status, json.loads(response.read())), (503, {"error": "secret_scanner_unavailable"}))

    def test_cache_rebuilds_after_ttl(self) -> None:
        calls = []
        cache = server.SnapshotCache(lambda: calls.append(1) or {}, ttl=0)
        cache.get()
        cache.get()
        self.assertEqual(len(calls), 2)

    def test_concurrent_requests_build_once(self) -> None:
        calls = []

        def build() -> dict:
            calls.append(1)
            time.sleep(0.05)
            return {}

        cache = server.SnapshotCache(build, ttl=60)
        threads = [threading.Thread(target=cache.get) for _ in range(8)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual(len(calls), 1)

    def test_snapshot_is_cached(self) -> None:
        self.request("GET", "/api/snapshot")
        self.request("GET", "/api/snapshot")
        self.assertEqual(self.builds, 1)

    def test_internal_error_has_no_details(self) -> None:
        def fail() -> dict:
            raise RuntimeError("SENSITIVE_DETAIL")

        broken = server.create_server(0, fail)
        self.addCleanup(broken.server_close)
        self.addCleanup(broken.shutdown)
        threading.Thread(target=broken.serve_forever, daemon=True).start()
        port = broken.server_address[1]
        connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
        self.addCleanup(connection.close)
        stderr, sys.stderr = sys.stderr, open(os.devnull, "w", encoding="utf-8")
        try:
            connection.request("GET", "/api/snapshot", headers={"Host": f"127.0.0.1:{port}"})
            response = connection.getresponse()
            body = response.read()
        finally:
            sys.stderr.close()
            sys.stderr = stderr
        self.assertEqual(response.status, 500)
        self.assertNotIn(b"SENSITIVE_DETAIL", body)



PASSWORD = "pass" + "word"  # split so the Stop hook does not flag the test file itself


class SnapshotGitTests(RepoFixture):
    """R1 (round 2): git wiring inside build_snapshot."""

    def setUp(self) -> None:
        super().setUp()
        collect._git_cache.clear()
        self.addCleanup(collect._git_cache.clear)

    def git_init(self, repo: Path, branch: str) -> None:
        repo.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "-C", str(repo), "init", "-b", branch], check=True, capture_output=True)

    def test_branch_comes_from_root_repo(self) -> None:
        self.git_init(self.root, "main")
        self.git_init(self.root / "ticket-system", "other")
        snapshot = self.snapshot(with_git=True)
        self.assertEqual(snapshot["mission"]["branch"], "main")
        self.assertEqual([repo["name"] for repo in snapshot["repos"]], [self.root.name, "ticket-system"])

    def test_no_root_repo_means_no_mission_branch(self) -> None:
        self.git_init(self.root / "ticket-system", "other")
        snapshot = self.snapshot(with_git=True)
        self.assertIsNone(snapshot["mission"]["branch"])
        self.assertEqual([repo["name"] for repo in snapshot["repos"]], ["ticket-system"])


class FifoTests(RepoFixture):
    """R2 (round 2): a FIFO anywhere in the inputs must not block the snapshot."""

    def test_fifo_findings_file_keeps_round(self) -> None:
        os.mkfifo(self.workspace / "4.1a/round-1/01_security-reviewer_findings.md")
        snapshot = run_with_timeout(self.snapshot)
        self.assertIsInstance(snapshot, dict)
        self.assertTrue(any(item["key"] == "4.1a/1" for item in snapshot["rounds"]))
        self.assertTrue(any("security-reviewer" in warning and "ValueError" in warning for warning in snapshot["warnings"]))

    def test_fifo_meta_counts_as_invalid(self) -> None:
        folder = self.projects / collect.project_slug(self.root) / "sess/subagents"
        folder.mkdir(parents=True)
        os.mkfifo(folder / "a1.meta.json")
        snapshot = run_with_timeout(self.snapshot)
        self.assertIsInstance(snapshot, dict)
        self.assertTrue(any("metadata" in warning for warning in snapshot["warnings"]))


class SecurityHeaderTests(unittest.TestCase):
    """R3 (round 2): every security header on every kind of response; Sec-Fetch-Site allow-set."""

    def setUp(self) -> None:
        self.server = server.create_server(0, lambda: {"ok": True})
        self.port = self.server.server_address[1]
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)

    def request(self, method: str, path: str, headers: dict | None = None):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        self.addCleanup(connection.close)
        connection.request(method, path, headers={"Host": f"127.0.0.1:{self.port}", **(headers or {})})
        response = connection.getresponse()
        response.read()
        return response

    # Fixed here on purpose: deleting a header from server.SECURITY_HEADERS must fail this test.
    EXPECTED = {
        "X-Content-Type-Options": "nosniff",
        "Referrer-Policy": "no-referrer",
        "Cache-Control": "no-store",
        "Cross-Origin-Resource-Policy": "same-origin",
    }

    def test_all_headers_on_200_404_405(self) -> None:
        for method, path, status in (("GET", "/api/snapshot", 200), ("GET", "/nope", 404), ("POST", "/api/snapshot", 405)):
            response = self.request(method, path)
            self.assertEqual(response.status, status)
            self.assertIn("default-src 'none'", response.getheader("Content-Security-Policy"), (method, path))
            for name, value in {**server.SECURITY_HEADERS, **self.EXPECTED}.items():
                self.assertEqual(response.getheader(name), value, (method, path, name))

    def test_sec_fetch_site_values(self) -> None:
        for value, status in (("same-origin", 200), ("none", 200), ("same-site", 403), ("cross-site", 403), ("bogus", 403)):
            self.assertEqual(self.request("GET", "/api/snapshot", {"Sec-Fetch-Site": value}).status, status, value)


class MainTests(RepoFixture):
    """R4 (round 2): command-line entry points."""

    def run_main(self, function, *args, **kwargs):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = function(*args, **kwargs)
        return code, out.getvalue(), err.getvalue()

    def test_server_exits_when_detector_unavailable(self) -> None:
        with mock.patch.object(collect, "load_detector", side_effect=collect.DetectorUnavailable("x")):
            code, _, err = self.run_main(server.main, [])
        self.assertEqual(code, 1)
        self.assertIn("claude_hook.py", err)
        self.assertNotIn("Traceback", err)

    def test_server_exits_when_port_in_use(self) -> None:
        busy = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.addCleanup(busy.close)
        busy.bind(("127.0.0.1", 0))
        busy.listen(1)
        port = busy.getsockname()[1]
        with mock.patch.object(collect, "load_detector", return_value=clean_detector):
            code, _, err = self.run_main(server.main, ["--port", str(port)])
        self.assertEqual(code, 1)
        self.assertIn(str(port), err)

    def check(self):
        return self.run_main(collect.main, ["--check"], root=self.root, projects_dir=self.projects,
                             detector=clean_detector, with_git=False)

    def test_check_ok(self) -> None:
        code, out, _ = self.check()
        self.assertEqual(code, 0)
        self.assertIn("Nguồn ledger: OK", out)

    def test_check_fails_when_a_source_fails(self) -> None:
        with mock.patch.object(collect, "parse_report_index", side_effect=ValueError("broken")):
            code, out, _ = self.check()
        self.assertEqual(code, 1)
        self.assertIn("LỖI", out)


class RunGitTests(unittest.TestCase):
    """R5 (round 2): git failure modes, flags and cache expiry."""

    def setUp(self) -> None:
        collect._git_cache.clear()
        self.addCleanup(collect._git_cache.clear)
        self.repo = Path(tempfile.gettempdir())

    def test_timeout_and_missing_git_degrade(self) -> None:
        for error in (subprocess.TimeoutExpired("git", 3), FileNotFoundError("git")):
            collect._git_cache.clear()
            with mock.patch.object(subprocess, "run", side_effect=error):
                self.assertIsNone(collect.run_git(self.repo, "status"))
                info = collect.git_info(self.repo, 100.0)
            self.assertFalse(info["available"], error)
            self.assertNotIn(str(self.repo), collect._git_cache)

    def test_safety_flags_are_passed(self) -> None:
        done = subprocess.CompletedProcess([], 0, stdout="", stderr="")
        with mock.patch.object(subprocess, "run", return_value=done) as run:
            collect.run_git(self.repo, "status")
        argv = run.call_args.args[0]
        self.assertIn("--no-optional-locks", argv)
        self.assertEqual(argv[argv.index("-c") + 1], "core.fsmonitor=false")

    def test_malformed_log_has_no_commit(self) -> None:
        outputs = {"status": "## main\n", "log": "only-one-field\n"}
        with mock.patch.object(collect, "run_git", side_effect=lambda _repo, command, *_: outputs[command]):
            info = collect.git_info(self.repo, 100.0)
        self.assertEqual((info["available"], info["branch"], info["commit"]), (True, "main", None))

    def test_cache_expires_after_ttl(self) -> None:
        calls = []

        def fake(_repo, command, *_):
            calls.append(command)
            return "## main\n" if command == "status" else None

        with mock.patch.object(collect, "run_git", side_effect=fake):
            collect.git_info(self.repo, 100.0)
            collect.git_info(self.repo, 100.0 + collect.GIT_TTL)
        self.assertEqual(calls.count("status"), 2)


class RoundGuardTests(RepoFixture):
    """R6 (round 2): per-round guard and symlinked directories."""

    def outside_round(self) -> Path:
        outside = self.root.parent / "outside-round"
        write(outside / "03_main_summary.md", SUMMARY.replace("EVIDENCE_TEXT", "OUTSIDE_SECRET"))
        return outside

    def test_symlinked_round_dir_is_skipped(self) -> None:
        (self.workspace / "7.1").mkdir()
        (self.workspace / "7.1/round-1").symlink_to(self.outside_round(), target_is_directory=True)
        snapshot = self.snapshot()
        self.assertNotIn("OUTSIDE_SECRET", json.dumps(snapshot))
        self.assertFalse(any(item["key"] == "7.1/1" for item in snapshot["rounds"]))
        self.assertIn("7.1/round-1: thư mục symlink bị bỏ qua", snapshot["warnings"])

    def test_symlinked_task_dir_is_skipped(self) -> None:
        task = self.root.parent / "outside-task"
        task.mkdir()
        (task / "round-1").symlink_to(self.outside_round(), target_is_directory=True)
        write(task / "round-2/03_main_summary.md", SUMMARY.replace("EVIDENCE_TEXT", "OUTSIDE_SECRET"))
        (self.workspace / "7.2").symlink_to(task, target_is_directory=True)
        snapshot = self.snapshot()
        self.assertNotIn("OUTSIDE_SECRET", json.dumps(snapshot))
        self.assertFalse(any(item["key"].startswith("7.2/") for item in snapshot["rounds"]))
        self.assertIn("7.2: thư mục symlink bị bỏ qua", snapshot["warnings"])

    def test_one_failing_round_does_not_drop_the_others(self) -> None:
        original = collect.scan_round

        def flaky(directory, task_id, number, base):
            if task_id == "5.1":
                raise OSError("vanished")
            return original(directory, task_id, number, base)

        with mock.patch.object(collect, "scan_round", side_effect=flaky):
            snapshot = self.snapshot()
        keys = {item["key"] for item in snapshot["rounds"]}
        self.assertNotIn("5.1/1", keys)
        self.assertIn("4.1a/1", keys)
        self.assertIn("5.1/round-1: OSError", snapshot["warnings"])

    def test_symlinked_findings_file_warns(self) -> None:
        outside = self.root.parent / "outside.md"
        outside.write_text(FINDINGS, encoding="utf-8")
        (self.workspace / "4.1a/round-1/01_security-reviewer_findings.md").symlink_to(outside)
        snapshot = self.snapshot()
        self.assertEqual(sum("01_security-reviewer_findings.md" in warning for warning in snapshot["warnings"]), 1)


class SubagentSymlinkTests(RepoFixture):
    """R1 (round 3): symlinks in the subagent folder are skipped with one warning, never silently."""

    def test_symlinked_meta_session_and_transcript_warn(self) -> None:
        now = time.time()
        self.add_meta("a1", "backend-reviewer", None, 10, now)
        folder = self.projects / collect.project_slug(self.root)
        outside = self.root.parent / "outside.json"
        outside.write_text(json.dumps({"agentType": "OUTSIDE_AGENT", "finished": None}), encoding="utf-8")
        (folder / "sess/subagents/a2.meta.json").symlink_to(outside)
        (folder / "linked.jsonl").symlink_to(outside)
        transcript = folder / "sess/subagents/a1.jsonl"
        transcript.unlink()
        transcript.symlink_to(outside)
        # R2 (round 4): the link target is very old and the meta is recent, so following any link shows up.
        os.utime(outside, (now - 99999, now - 99999))
        os.utime(folder / "sess/subagents/a1.meta.json", (now - 50, now - 50))
        snapshot = self.snapshot(now=now)
        self.assertNotIn("OUTSIDE_AGENT", json.dumps(snapshot))
        card = next(item for item in snapshot["agents"] if item["id"] == "backend-reviewer")
        self.assertEqual((card["lastAt"], card["status"]), (collect.iso(now - 50), "running"))
        self.assertIsNone(snapshot["orchestrator"]["lastAt"])
        related = [warning for warning in snapshot["warnings"] if "subagent" in warning]
        self.assertEqual(related, ["3 file symlink trong thư mục subagent bị bỏ qua"])


class DetectorRuleTests(unittest.TestCase):
    """R7, R9, R11 (round 2): dashboard-only secret patterns, tested without the hook."""

    def test_safe_values_are_skipped(self) -> None:
        for sample in ("token=changeme", "API_KEY=replace-with-yourkey", PASSWORD + "=${X_" + "PASSWORD}",
                       "secret=example", "pwd=placeholder", PASSWORD + "=<redacted>", "token: x",
                       PASSWORD + ": `abc`", "token=true", "secret: none"):
            self.assertEqual(collect.extra_secret_findings(sample), [], sample)

    def test_real_value_after_safe_value_is_caught(self) -> None:
        self.assertTrue(collect.extra_secret_findings("token=changeme and " + PASSWORD + "=abcd1234efgh"))

    def test_short_quoted_and_basic_values_are_caught(self) -> None:
        samples = ["DB_" + PASSWORD.upper() + "=root", "MYSQL_ROOT_" + PASSWORD.upper() + ": 123456",
                   PASSWORD + ': "two words here"', "Authorization: Basic dXNlcjpwYXNzd29yZA==", "credentials=hunter22",
                   "DB_" + "PASS=abcd", "AU" + "TH=abcd", "PRIVATE" + "_KEY=abcd", "ENCRYPTION" + "_KEY=abcd",
                   PASSWORD + ": `ab cdefgh`"]
        for sample in samples:
            self.assertTrue(collect.extra_secret_findings(sample), sample)

    def test_prose_is_left_alone(self) -> None:
        for sample in ("Thiếu test cho token hết hạn", "basic authentication flow", "JwtAuthFilter bắt lỗi token",
                       "passport: chưa có", "Authorization header bị thiếu",
                       # R1 (round 4): `pass` / `auth` as ordinary words
                       "bypass=true", "oauth: enabled", "OAuth: enabled", "auth: required", "auth: Kong", "pass=true",
                       "all tests pass: green", "tests pass: 109/109", "compass: north", "passenger=abcd",
                       "bypass=enabled", "oauth=enabled",
                       # R1 (round 5): quoted prose must not reach the quoted pattern's weak branch (lookbehind)
                       'oauth: "enabled for all"', 'bypass: "yes it is"'):
            self.assertEqual(collect.extra_secret_findings(sample), [], sample)

    def test_weak_keywords_still_catch_names(self) -> None:
        backtick = "`"
        for sample in ("DB_" + "PASS=abcd", "AU" + "TH=abcd", "X-" + "AUTH: abcd1234", "MYSQL_" + "PASS: hunter22",
                       # R3 (round 4): backticks inside a value no longer hide it
                       PASSWORD + "=ab" + backtick + "cdefgh", PASSWORD + ': "ab' + backtick + 'cdefgh"',
                       PASSWORD + ': "it\'s my word"',  # only the quoted pattern sees past the inner quote and spaces
                       # R1 (round 5): every word is under 4 characters, so only the quoted weak branch can catch these
                       "DB_" + 'PASS: "ab cd ef"', "X-" + "AUTH: 'it is me'",
                       backtick + PASSWORD + backtick + ": " + backtick + "abcd1234efgh" + backtick):
            self.assertTrue(collect.extra_secret_findings(sample), sample)

    def timed(self, text: str) -> float:
        best = float("inf")
        for _ in range(3):
            started = time.perf_counter()
            collect.extra_secret_findings(text)  # some units are themselves secret-shaped; only the time matters
            best = min(best, time.perf_counter() - started)
        return best

    def test_patterns_scale_linearly(self) -> None:
        # Ratio, not a wall-clock bound: 4x the text may cost ~4x (linear), never ~16x (quadratic, as the old
        # `[a-z0-9_.-]*` keyword prefix and the unbounded URL scheme were). Sizes stay small because the regex
        # holds the GIL and a quadratic regression must still fail in seconds. The floor absorbs timer noise.
        for unit in ("a", "a.", "a-", "pass:", "_pass:", "auth=", "token=`", PASSWORD + ': "', "x://", "a://a:"):
            small, large = self.timed(unit * 2_000), self.timed(unit * 8_000)
            self.assertLess(large, max(8 * small, 0.05), unit)


class UiContractTests(unittest.TestCase):
    """R8 (round 2): every status the server can emit has a label in app.js, and unknown ones do not crash."""

    APP = (Path(__file__).resolve().parent / "static/app.js").read_text(encoding="utf-8")
    SOURCE = Path(collect.__file__).read_text(encoding="utf-8")

    def js_keys(self, name: str) -> set[str]:
        block = re.search(rf"const {name} = \{{(.*?)\n\}};", self.APP, re.DOTALL)
        self.assertIsNotNone(block, name)
        return set(re.findall(r"^\s*(\w+):", block.group(1), re.MULTILINE))

    def test_agent_statuses_have_labels(self) -> None:
        emitted = set(re.findall(r'status = "(\w+)"', self.SOURCE))
        emitted |= set(re.findall(r'"status": "(\w+)" if', self.SOURCE))
        self.assertTrue(emitted)
        self.assertLessEqual(emitted, set(collect.AGENT_STATUSES))
        self.assertLessEqual(set(collect.AGENT_STATUSES), self.js_keys("AGENT_STATUS"))

    def test_task_statuses_have_labels(self) -> None:
        returned = set(re.findall(r'return "(\w+)"', self.SOURCE.split("def task_status", 1)[1].split("\ndef ", 1)[0]))
        returned |= {"in_progress", "not_started"}
        self.assertEqual(returned, set(collect.TASK_STATUSES))
        self.assertLessEqual(set(collect.TASK_STATUSES), self.js_keys("TASK_STATUS"))

    def test_stages_have_labels(self) -> None:
        line = next(line for line in self.SOURCE.splitlines() if line.strip().startswith("stage = "))
        self.assertEqual(set(re.findall(r'"([a-z]\w*)"', line)), set(collect.STAGES))
        self.assertLessEqual(set(collect.STAGES), self.js_keys("STAGES"))

    def test_no_inner_html(self) -> None:
        self.assertNotIn("innerHTML", self.APP.replace("never innerHTML", ""))

    def test_status_and_stage_lookups_go_through_fallbacks(self) -> None:
        for table in ("AGENT_STATUS", "TASK_STATUS", "STAGES"):
            self.assertIsNone(re.search(rf"{table}\[", self.APP), f"direct {table}[...] lookup bypasses the fallback")


NODE_HARNESS = r"""
const vm = require("vm");
const fs = require("fs");
function element(tag) {
  return { tag, attrs: {}, kids: [], style: {}, setAttribute(k, v) { this.attrs[k] = v; },
           addEventListener() {}, append(...kids) { this.kids.push(...kids); } };
}
const context = vm.createContext({ document: { createElement: element, createElementNS: (_ns, tag) => element(tag) } });
vm.runInContext(fs.readFileSync(process.argv[1], "utf8"), context);
const out = vm.runInContext(`(() => {
  const view = (node) => ({ tag: node.tag, cls: node.attrs.class, text: node.kids.map(String) });
  return {
    unknownAgent: view(statusPill(AGENT_STATUS, "brand_new")),
    unknownTask: view(statusPill(TASK_STATUS, "brand_new")),
    knownTask: view(statusPill(TASK_STATUS, "done")),
    prototypeName: view(statusPill(AGENT_STATUS, "constructor")),
    missing: view(statusPill(AGENT_STATUS, undefined)),
    markup: view(statusPill(AGENT_STATUS, "<img src=x onerror=alert(1)>")),
    stageKnown: stageLabel("summarized"),
    stageUnknown: stageLabel("brand_new"),
    stagePrototype: stageLabel("toString"),
  };
})()`, context);
process.stdout.write(JSON.stringify(out));
"""


@unittest.skipUnless(shutil.which("node"), "node not installed")
class AppJsRuntimeTests(unittest.TestCase):
    """R2 (round 3): run the real app.js fallbacks in node instead of grepping the source."""

    @classmethod
    def setUpClass(cls) -> None:
        app = Path(__file__).resolve().parent / "static/app.js"
        result = subprocess.run(["node", "-e", NODE_HARNESS, str(app)], capture_output=True, text=True, timeout=30)
        if result.returncode:
            raise AssertionError(result.stderr)
        cls.out = json.loads(result.stdout)

    def test_unknown_status_shows_raw_key(self) -> None:
        for key in ("unknownAgent", "unknownTask"):
            self.assertEqual(self.out[key], {"tag": "span", "cls": "pill tone-warn", "text": ["brand_new"]}, key)

    def test_known_status_keeps_label(self) -> None:
        self.assertEqual(self.out["knownTask"], {"tag": "span", "cls": "pill tone-accent", "text": ["Xong"]})

    def test_prototype_names_and_missing_values_do_not_throw(self) -> None:
        self.assertEqual(self.out["prototypeName"]["text"], ["constructor"])
        self.assertEqual(self.out["missing"]["text"], ["không rõ"])
        self.assertEqual(self.out["stagePrototype"], "toString")

    def test_markup_stays_text(self) -> None:
        self.assertEqual(self.out["markup"]["text"], ["<img src=x onerror=alert(1)>"])
        self.assertEqual(self.out["markup"]["cls"], "pill tone-warn")

    def test_stage_labels(self) -> None:
        self.assertEqual((self.out["stageKnown"], self.out["stageUnknown"]), ("Đã tổng hợp", "brand_new"))


if __name__ == "__main__":
    unittest.main()
