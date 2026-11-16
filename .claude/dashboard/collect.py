#!/usr/bin/env python3
"""Build a read-only snapshot of the System_bus harness.

Sources: ledger, report index, review docs, review-pipeline workspace, subagent
metadata and git. Nothing here writes a file. Subagent transcripts are never
opened: only `*.meta.json` is read and the `.jsonl` files are stat-ed.

Check against the real repo:  python3 .claude/dashboard/collect.py --check
"""
from __future__ import annotations

import argparse
import json
import os
import re
import runpy
import stat
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

GATES = ("spec", "implement", "test", "review", "lead-review")
REVIEWERS = ("backend-reviewer", "frontend-reviewer", "security-reviewer", "test-gap-reviewer", "config-reviewer")
VERIFIER = "finding-verifier"
ROLES = {
    "backend-reviewer": ("Review backend", "BE"),
    "frontend-reviewer": ("Review frontend", "FE"),
    "security-reviewer": ("Review bảo mật", "BM"),
    "test-gap-reviewer": ("Soát thiếu test", "TG"),
    "config-reviewer": ("Soát cấu hình", "CF"),
    VERIFIER: ("Kiểm chứng finding", "KC"),
}
SEVERITIES = ("high", "medium", "low")
VERDICTS = ("confirmed", "refuted", "uncertain", "unverified")
RUNNING_WINDOW = 120
RECENT_WINDOW = 1800
GIT_TTL = 30
MAX_FILE_BYTES = 2_000_000

TASK_ID = r"\d+\.\d+[a-z]?"
LEDGER_HEADING_RE = re.compile(rf"^##\s+({TASK_ID})\s+[—–-]\s+(.*)$")
LEDGER_GATE_RE = re.compile(r"^- \[([ xX])\]\s+(\S+)")
REPORT_ROW_RE = re.compile(rf"^{TASK_ID}$")
REPORT_ROUND_RE = re.compile(r"round\s+(\d+),\s*([A-Z-]+)")
PHASE_RE = re.compile(r"^##\s+Phase\s+(\d+)\b")
PAUSED_RE = re.compile(r"^>\s*\*\*TẠM DỪNG")
REVIEW_DOC_RE = re.compile(rf"^({TASK_ID})-.*\.md$")
ROUND_DIR_RE = re.compile(r"^round-(\d+)$")
LEAD_RE = re.compile(r"Round\s+(\d+)\s*·\s*([0-9-]+)\s*·\s*Verdict:\s*\**([A-Z-]+)")
CELL_SPLIT_RE = re.compile(r"(?<!\\)\|")
SECRET_KEYWORDS = (r"api[_-]?key|access[_-]?key|(?:private|encryption|signing|master)[_-]?key|token|secret(?:[_-]?key)?"
                   r"|passw(?:or)?d|pwd|credentials?")
# `pass` and `auth` are ordinary words ("tests pass: green", "oauth: enabled", "bypass=true"), so they count only as a
# name part after `_`/`-` (DB_PASS, X-AUTH) with `:` or `=`, or as a whole word assigned with `=` (AUTH=...).
# All lookarounds are fixed width, so the patterns stay linear.
WEAK_KEYWORDS = r"(?:pass|auth)(?![a-z0-9])"
# Short dev passwords such as `root` must be caught; 4 keeps prose like `token: x` readable.
MIN_SECRET_CHARS = 4
# Unquoted value: backticks may appear inside it; surrounding ones are stripped before the length check.
PLAIN_VALUE = rf"\s*[\"'`]*(?P<value>[^\s\"'|,;]{{{MIN_SECRET_CHARS},}})"
# Added on top of the hook's patterns: review text is markdown and names secrets with prefixes.
EXTRA_SECRET_PATTERNS = [
    # No `[a-z0-9_.-]*` prefix: the keyword already matches inside DB_PASSWORD, and the prefix backtracks quadratically.
    re.compile(rf"(?i)(?:{SECRET_KEYWORDS})[\"'`]*\s*[:=]{PLAIN_VALUE}"),
    re.compile(rf"(?i)(?<=[_-]){WEAK_KEYWORDS}[\"'`]*\s*[:=]{PLAIN_VALUE}"),
    re.compile(rf"(?i)(?<![a-z0-9_-]){WEAK_KEYWORDS}[\"'`]*\s*={PLAIN_VALUE}"),
    # Quoted value with spaces: only the opening quote ends it, so other quote characters may appear inside.
    re.compile(rf"(?i)(?:{SECRET_KEYWORDS}|(?<=[_-]){WEAK_KEYWORDS})[\"'`]*\s*[:=]\s*(?P<quote>[\"'`])"
               rf"(?P<value>(?:(?!(?P=quote))[^\n]){{{MIN_SECRET_CHARS},}})(?P=quote)"),
    re.compile(r"(?i)\bauthorization\s*:\s*basic\s+(?P<value>[A-Za-z0-9+/]{8,}={0,2})"),
    # Scheme length is bounded: an unbounded `[a-z0-9+.-]*` is quadratic on long dotted or hyphenated text.
    re.compile(r"(?i)\b[a-z][a-z0-9+.-]{0,31}://[^\s/:@]+:(?P<value>[^\s/@]+)@"),
    re.compile(r"(?i)\bbearer\s+(?P<value>[a-z0-9._~+/-]{12,}=*)"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})\b"),
    re.compile(r"\bxox[abeoprs]-[A-Za-z0-9-]{10,}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY"),
]
SAFE_SECRET_VALUES = {"redacted", "changeme", "example", "placeholder", "true", "false", "none", "null"}
# Every status value the snapshot can carry; app.js must have a label for each (test_collect checks it).
AGENT_STATUSES = ("running", "done", "idle", "unknown")
TASK_STATUSES = ("done", "paused", "waiting_user", "reviewing", "in_progress", "not_started")
STAGES = ("empty", "scoped", "reviewing", "verifying", "summarized")

Detector = Callable[[str], list]


class DetectorUnavailable(RuntimeError):
    """The secret scanner could not be loaded, so nothing may be served."""


def iso(ts: float | None) -> str | None:
    if ts is None:
        return None
    return datetime.fromtimestamp(ts, timezone.utc).isoformat(timespec="seconds")


def table_cells(line: str) -> list[str] | None:
    stripped = line.strip()
    if not (stripped.startswith("|") and stripped.endswith("|")):
        return None
    return [cell.strip().replace("\\|", "|") for cell in CELL_SPLIT_RE.split(stripped[1:-1])]


def section(text: str, heading: str) -> list[str] | None:
    """Lines under the first `## ` heading matching `heading`, up to the next one."""
    pattern = re.compile(heading)
    found: list[str] | None = None
    for line in text.splitlines():
        if line.startswith("## "):
            if found is not None:
                return found
            if pattern.search(line):
                found = []
            continue
        if found is not None:
            found.append(line)
    return found


def clean(value: str) -> str:
    return value.strip(" *`")


def normalize_severity(value: str) -> str:
    """`low (verifier)` -> `low`."""
    words = clean(value).lower().split()
    return words[0] if words else ""


def normalize_verdict(value: str) -> str | None:
    lowered = clean(value).lower()
    for verdict in VERDICTS:
        if lowered.startswith(verdict):
            return verdict
    return None


def source_agents(source: str) -> list[str]:
    """`test-gap #2 + backend #2 (a, b)` -> the two reviewer agent names."""
    agents = []
    for part in source.split("+"):
        match = re.match(r"\s*([a-z][a-z-]*)", part)
        if not match:
            continue
        name = match.group(1).removesuffix("-reviewer") + "-reviewer"
        if name in REVIEWERS and name not in agents:
            agents.append(name)
    return agents


def parse_ledger(text: str) -> tuple[list[dict], list[str]]:
    tasks: list[dict] = []
    warnings: list[str] = []
    for line in text.splitlines():
        heading = LEDGER_HEADING_RE.match(line)
        if heading:
            tasks.append({"id": heading.group(1), "title": heading.group(2).strip(), "gates": {}})
            continue
        gate = LEDGER_GATE_RE.match(line)
        if gate and tasks:
            if gate.group(2) in GATES:
                tasks[-1]["gates"][gate.group(2)] = gate.group(1).lower() == "x"
            else:
                warnings.append(f"Ledger {tasks[-1]['id']}: cổng lạ '{gate.group(2)}'")
    for task in tasks:
        missing = [gate for gate in GATES if gate not in task["gates"]]
        if missing:
            warnings.append(f"Ledger {task['id']}: thiếu cổng {', '.join(missing)}")
            for gate in missing:
                task["gates"][gate] = False
    return tasks, warnings


def parse_report_index(text: str) -> tuple[dict[str, dict], list[str]]:
    reports: dict[str, dict] = {}
    warnings: list[str] = []
    for line in text.splitlines():
        cells = table_cells(line)
        if not cells or not REPORT_ROW_RE.match(cells[0]):
            continue
        if len(cells) < 5:
            warnings.append(f"Report {cells[0]}: dòng thiếu cột")
            continue
        match = REPORT_ROUND_RE.search(cells[3])
        if not match:
            warnings.append(f"Report {cells[0]}: không đọc được '{cells[3]}'")
            continue
        reports[cells[0]] = {"date": cells[2], "round": int(match.group(1)), "verdict": match.group(2)}
    return reports, warnings


def parse_paused_phases(text: str) -> list[str]:
    paused: list[str] = []
    current: str | None = None
    for line in text.splitlines():
        phase = PHASE_RE.match(line)
        if phase:
            current = phase.group(1)
            continue
        if current is None or not line.strip():
            continue
        if PAUSED_RE.match(line):
            paused.append(current)
        current = None
    return paused


def parse_lead_review(text: str) -> dict | None:
    lines = section(text, r"^##\s+7\.\s+Lead review")
    if lines is None:
        return None
    match = LEAD_RE.search("\n".join(lines))
    seen: dict[str, tuple[str, str]] = {}
    for line in lines:
        cells = table_cells(line)
        if cells and len(cells) >= 6 and re.fullmatch(r"L\d+", cells[0]) and cells[0] not in seen:
            seen[cells[0]] = (clean(cells[2]).upper(), clean(cells[-1]).lower())
    open_fix = sum(
        1 for klass, status in seen.values()
        if klass == "FIX" and not status.startswith(("fixed", "done", "resolved"))
    )
    return {
        "round": int(match.group(1)) if match else None,
        "date": match.group(2) if match else None,
        "verdict": match.group(3) if match else None,
        "openFix": open_fix,
        "needsUser": sum(1 for klass, _ in seen.values() if klass == "NEEDS-USER"),
        "items": len(seen),
    }


def parse_findings(text: str) -> tuple[list[dict], list[str]]:
    lines = section(text, r"^##\s+Findings")
    if lines is None:
        return [], ["không có mục Findings"]
    rows: list[dict] = []
    warnings: list[str] = []
    for line in lines:
        cells = table_cells(line)
        if not cells or not cells[0].isdigit():
            continue
        severity = normalize_severity(cells[1]) if len(cells) > 1 else ""
        if len(cells) < 4 or severity not in SEVERITIES:
            warnings.append(f"finding #{cells[0]}: không đọc được dòng")
            continue
        rows.append({"severity": severity, "file": cells[2], "finding": cells[3]})
    return rows, warnings


def parse_verdicts(text: str) -> tuple[dict[str, int], list[str]]:
    counts = {verdict: 0 for verdict in VERDICTS}
    warnings: list[str] = []
    for line in section(text, r"^##\s+Verdicts") or []:
        cells = table_cells(line)
        if not cells or not cells[0].isdigit():
            continue
        verdict = normalize_verdict(cells[2]) if len(cells) > 2 else None
        if verdict is None:
            warnings.append(f"verdict #{cells[0]}: không nhận ra")
            continue
        counts[verdict] += 1
    return counts, warnings


def parse_scope(text: str) -> list[str]:
    names: list[str] = []
    for line in section(text, r"^##\s+Reviewers") or []:
        match = re.match(r"^-\s+`([a-z-]+)`", line)
        if match and match.group(1) in REVIEWERS:
            names.append(match.group(1))
    return names


def parse_summary(text: str) -> tuple[dict, list[str]]:
    lines = text.splitlines()
    calls = re.search(r"Verifier calls:\s*(\d+)", text)
    missing = re.search(r"Missing:\s*(.+)", text)
    rows: list[dict] = []
    warnings: list[str] = []
    for line in lines:
        cells = table_cells(line)
        if not cells or not re.fullmatch(r"R\d+", cells[0]):
            continue
        verdict = normalize_verdict(cells[5]) if len(cells) >= 7 else None
        severity = normalize_severity(cells[2]) if len(cells) >= 7 else ""
        if verdict is None or severity not in SEVERITIES:
            warnings.append(f"summary {cells[0]}: không đọc được dòng")
            continue
        rows.append({
            "id": cells[0],
            "source": cells[1],
            "agents": source_agents(cells[1]),
            "severity": severity,
            "file": cells[3],
            "finding": cells[4],
            "verdict": verdict,
        })
    refuted = []
    for line in section(text, r"^##\s+Refuted") or []:
        match = re.match(r"^-\s+(.*)$", line)
        if match and clean(match.group(1)).lower() != "none":
            refuted.append({"text": match.group(1), "agents": source_agents(match.group(1).split(":")[0])})
    return {
        "title": lines[0].lstrip("# ").strip() if lines else "",
        "verifierCalls": int(calls.group(1)) if calls else None,
        "missing": missing.group(1).strip() if missing else None,
        "rows": rows,
        "refuted": refuted,
    }, warnings


def read_inside(path: Path, base: Path) -> str:
    """Read a file only if it really lives under `base` and is a normal size."""
    if path.is_symlink() or not path.resolve().is_relative_to(base.resolve()):
        raise PermissionError("path outside allowed base")
    if path.name.startswith(".env"):
        raise PermissionError("dotenv files are never read")
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, "rb") as handle:
        info = os.fstat(handle.fileno())
        if not stat.S_ISREG(info.st_mode):
            raise ValueError("not a regular file")
        if info.st_size > MAX_FILE_BYTES:
            raise ValueError("file too large")
        return handle.read().decode("utf-8", errors="replace")


def scan_round(directory: Path, task_id: str, number: int, base: Path) -> tuple[dict, list[str]]:
    prefix = f"{task_id} vòng {number}"
    warnings: list[str] = []
    files = []
    for path in sorted(directory.glob("*.md")):
        if path.is_symlink():
            warnings.append(f"{prefix} {path.name}: symlink bị bỏ qua")
        else:
            files.append(path)
    latest = {step: None for step in ("00", "01", "02", "03")}
    for path in files:
        step = path.name[:2]
        if step in latest:
            latest[step] = max(latest[step] or 0, path.stat().st_mtime)
    stage = "summarized" if latest["03"] else "verifying" if latest["02"] else "reviewing" if latest["01"] else "scoped" if latest["00"] else "empty"

    def read(path: Path) -> str | None:
        """One bad file costs a warning, not the whole round."""
        try:
            return read_inside(path, base)
        except (OSError, ValueError) as error:
            warnings.append(f"{prefix} {path.name}: {type(error).__name__}")
            return None

    expected: list[str] = []
    scope = directory / "00_main_scope.md"
    scope_text = read(scope) if scope in files else None
    if scope_text is not None:
        expected = parse_scope(scope_text)

    per_reviewer: dict[str, dict] = {}
    finding_rows: list[dict] = []
    for path in files:
        match = re.fullmatch(r"01_([a-z-]+)_findings\.md", path.name)
        if not match:
            continue
        agent = match.group(1)
        findings_text = read(path)
        if findings_text is None:
            continue
        rows, problems = parse_findings(findings_text)
        warnings += [f"{prefix} {agent}: {problem}" for problem in problems]
        per_reviewer[agent] = {severity: sum(1 for row in rows if row["severity"] == severity) for severity in SEVERITIES}
        finding_rows += [{"id": None, "source": agent, "agents": [agent], "verdict": None, **row} for row in rows]

    verdicts = {verdict: 0 for verdict in VERDICTS}
    verifier_files = [path for path in files if path.name.startswith("02_")]
    for path in verifier_files:
        verdict_text = read(path)
        if verdict_text is None:
            continue
        counts, problems = parse_verdicts(verdict_text)
        warnings += [f"{prefix} verifier: {problem}" for problem in problems]
        for verdict, count in counts.items():
            verdicts[verdict] += count

    summary = None
    summary_path = directory / "03_main_summary.md"
    summary_text = read(summary_path) if summary_path in files else None
    if summary_text is not None:
        summary, problems = parse_summary(summary_text)
        warnings += [f"{prefix}: {problem}" for problem in problems]

    agents = sorted({*expected, *per_reviewer})
    round_data = {
        "key": f"{task_id}/{number}",
        "id": task_id,
        "round": number,
        "stage": stage,
        "updatedAt": iso(max((value for value in latest.values() if value), default=None)),
        "steps": {step: iso(value) for step, value in latest.items()},
        "expected": expected,
        "missing": [agent for agent in expected if agent not in per_reviewer],
        "rows": summary["rows"] if summary else finding_rows,
        "refuted": summary["refuted"] if summary else [],
        "title": summary["title"] if summary else prefix,
        "verifierRan": bool(verifier_files),
        "verdicts": verdicts,
        "flow": {
            "reviewers": [
                {
                    "agent": agent,
                    "toVerifier": per_reviewer.get(agent, {}).get("high", 0) + per_reviewer.get(agent, {}).get("medium", 0),
                    "direct": per_reviewer.get(agent, {}).get("low", 0),
                    "done": agent in per_reviewer,
                }
                for agent in agents
            ],
            "confirmed": verdicts["confirmed"],
            "refuted": verdicts["refuted"],
            "uncertain": verdicts["uncertain"],
            "summaryRows": len(summary["rows"]) if summary else None,
        },
        "perReviewer": per_reviewer,
    }
    return round_data, warnings


def scan_rounds(workspace: Path) -> tuple[list[dict], list[str]]:
    rounds: list[dict] = []
    warnings: list[str] = []
    if not workspace.is_dir():
        return rounds, warnings
    for task_dir in sorted(workspace.iterdir()):
        if task_dir.is_symlink():
            warnings.append(f"{task_dir.name}: thư mục symlink bị bỏ qua")
            continue
        if not task_dir.is_dir():
            continue
        for directory in sorted(task_dir.iterdir()):
            match = ROUND_DIR_RE.match(directory.name)
            if match and directory.is_symlink():
                warnings.append(f"{task_dir.name}/{directory.name}: thư mục symlink bị bỏ qua")
                continue
            if not match or not directory.is_dir():
                continue  # e.g. round-1.prev-2215 is an archived copy
            try:
                data, problems = scan_round(directory, task_dir.name, int(match.group(1)), workspace)
            except (OSError, ValueError) as error:
                warnings.append(f"{task_dir.name}/{directory.name}: {type(error).__name__}")
                continue
            rounds.append(data)
            warnings += problems
    rounds.sort(key=lambda item: item["updatedAt"] or "", reverse=True)
    return rounds, warnings


def project_slug(root: Path) -> str:
    return re.sub(r"[^A-Za-z0-9]", "-", str(root))


def scan_subagents(project_dir: Path, now: float) -> tuple[dict, list[str]]:
    live = {
        "agents": {},
        "sessionActiveAt": None,
        "latestAt": None,
    }
    warnings: list[str] = []
    if not project_dir.is_dir():
        return live, warnings
    symlinks = 0
    sessions = []
    for path in project_dir.glob("*.jsonl"):
        if path.is_symlink():
            symlinks += 1
        else:
            sessions.append(path.stat().st_mtime)
    live["sessionActiveAt"] = max(sessions, default=None)
    invalid = 0
    for meta in project_dir.glob("*/subagents/*.meta.json"):
        if meta.is_symlink():
            symlinks += 1
            continue
        try:
            data = json.loads(read_inside(meta, project_dir))
            agent = data["agentType"]
            finished = data.get("finished")
            if not isinstance(agent, str) or finished not in (True, None):
                raise ValueError
        except (OSError, ValueError, KeyError, TypeError):
            invalid += 1
            continue
        transcript = meta.with_name(meta.name.removesuffix(".meta.json") + ".jsonl")
        symlinks += transcript.is_symlink()
        mtime = transcript.stat().st_mtime if transcript.exists() and not transcript.is_symlink() else meta.stat().st_mtime
        age = now - mtime
        entry = live["agents"].setdefault(agent, {"runs": 0, "running": 0, "unknown": 0, "recentDone": 0, "lastAt": None})
        entry["runs"] += 1
        entry["lastAt"] = max(entry["lastAt"] or 0, mtime)
        live["latestAt"] = max(live["latestAt"] or 0, mtime)
        if finished is True:
            entry["recentDone"] += 1 if age <= RECENT_WINDOW else 0
        elif age <= RUNNING_WINDOW:
            entry["running"] += 1
        elif age <= RECENT_WINDOW:
            entry["unknown"] += 1
    if symlinks:
        warnings.append(f"{symlinks} file symlink trong thư mục subagent bị bỏ qua")
    if invalid:
        live["invalid"] = invalid
        warnings.append(f"{invalid} file metadata subagent không đúng định dạng mong đợi")
    return live, warnings


_git_cache: dict[str, tuple[float, dict]] = {}


def run_git(repo: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "--no-optional-locks", "-c", "core.fsmonitor=false", "-C", str(repo), *args],
            capture_output=True, text=True, errors="replace", timeout=3, check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return result.stdout if result.returncode == 0 else None


def parse_branch(head: str) -> str | None:
    """The text after `## ` on the first line of `git status --branch`."""
    if head.startswith("HEAD (no branch)"):
        return "detached HEAD"
    for prefix in ("No commits yet on ", "Initial commit on "):
        if head.startswith(prefix):
            return head.removeprefix(prefix) or None
    return head.split("...")[0] or None


def git_info(repo: Path, now: float) -> dict:
    cached = _git_cache.get(str(repo))
    if cached and now - cached[0] < GIT_TTL:
        return cached[1]
    info: dict[str, Any] = {"name": repo.name, "available": False, "branch": None, "dirty": 0, "commit": None}
    status = run_git(repo, "status", "--porcelain=v1", "--branch")
    if status is not None:
        lines = status.splitlines()
        head = lines[0][3:] if lines and lines[0].startswith("## ") else ""
        info.update(available=True, branch=parse_branch(head), dirty=max(len(lines) - 1, 0))
        log = run_git(repo, "log", "-1", "--format=%h%x1f%s%x1f%cI")
        if log and log.count("\x1f") == 2:
            short, subject, date = log.strip().split("\x1f")
            info["commit"] = {"hash": short, "subject": subject, "date": date}
    if info["available"]:
        _git_cache[str(repo)] = (now, info)
    return info


def read_agents(directory: Path) -> list[dict]:
    agents = []
    for path in sorted(directory.glob("*.md")):
        match = re.match(r"^---\n(.*?)\n---", read_inside(path, directory), re.DOTALL)
        fields = {}
        for line in (match.group(1) if match else "").splitlines():
            key, separator, value = line.partition(":")
            if separator and not key.startswith((" ", "#")):
                fields[key.strip()] = value.strip().strip('"')
        if fields.get("name"):
            agents.append({"id": fields["name"], "model": fields.get("model")})
    return agents


def task_status(gates: dict, report: dict | None, spec_doc: bool, paused: bool, latest_round: dict | None) -> str:
    """The single place that decides a task's status."""
    if all(gates.values()):
        return "done"
    if paused:
        return "paused"
    if report and report["verdict"] == "CLEAN" and not gates["lead-review"]:
        return "waiting_user"
    if spec_doc and not gates["spec"]:
        return "waiting_user"
    if latest_round and latest_round["stage"] != "summarized":
        return "reviewing"
    return "in_progress" if any(gates.values()) else "not_started"


def waiting_reason(task: dict) -> str:
    report = task["report"]
    if report and report["verdict"] == "CLEAN" and not task["gates"]["lead-review"]:
        return "Đã CLEAN, chờ bạn tick lead-review"
    return "Có spec review, chờ bạn tick spec"


def agent_cards(agent_list: list[dict], rounds: list[dict], live: dict, sources_ok: bool) -> list[dict]:
    cards = []
    for agent in agent_list:
        name = agent["id"]
        role, initials = ROLES.get(name, (name, name[:2].upper()))
        state = live["agents"].get(name, {})
        involved = [
            item for item in rounds
            if (name == VERIFIER and item["verifierRan"]) or name in item["perReviewer"]
        ]
        severity = {key: sum(item["perReviewer"].get(name, {}).get(key, 0) for item in rounds) for key in SEVERITIES}
        verified = {verdict: 0 for verdict in ("confirmed", "refuted", "uncertain")}
        if name == VERIFIER:
            for item in rounds:
                for verdict in verified:
                    verified[verdict] += item["verdicts"][verdict]
        else:
            for item in rounds:
                for row in item["rows"]:
                    if name in row["agents"] and row["verdict"] in verified:
                        verified[row["verdict"]] += 1
                verified["refuted"] += sum(1 for row in item["refuted"] if name in row["agents"])
        if not sources_ok:
            status = "unknown"
        elif state.get("running"):
            status = "running"
        elif state.get("unknown"):
            status = "unknown"
        elif state.get("recentDone"):
            status = "done"
        else:
            status = "idle"
        note = "Chưa có vòng review nào trong _workspace"
        if involved:
            last = involved[0]
            if name == VERIFIER:
                note = f"{last['id']} vòng {last['round']}: {last['verdicts']['confirmed']} confirmed, {last['verdicts']['refuted']} refuted"
            else:
                counts = last["perReviewer"][name]
                note = f"{last['id']} vòng {last['round']}: {counts['high']} high, {counts['medium']} medium, {counts['low']} low"
        cards.append({
            "id": name, "role": role, "initials": initials, "model": agent.get("model"),
            "status": status, "note": note, "rounds": len(involved), "severity": severity, "verified": verified,
            "liveRuns": state.get("runs", 0), "lastAt": iso(state.get("lastAt")),
        })
    return cards


def extra_secret_findings(text: str) -> list:
    for pattern in EXTRA_SECRET_PATTERNS:
        for match in pattern.finditer(text):
            value = match.groupdict().get("value", match.group(0)).strip("'\"`")
            if (len(value) < MIN_SECRET_CHARS or value.lower() in SAFE_SECRET_VALUES
                    or value.startswith(("${", "<", "replace-with-"))):
                continue
            return [pattern.pattern[:20]]
    return []


def load_detector(root: Path) -> Detector:
    try:
        hook_findings = runpy.run_path(str(root / ".claude/hooks/claude_hook.py"))["secret_findings"]
    except Exception as error:
        raise DetectorUnavailable(type(error).__name__) from error

    def detector(text: str) -> list:
        return hook_findings(text) or extra_secret_findings(text)

    return detector


def redact(value: Any, detector: Detector) -> Any:
    if isinstance(value, str):
        return "<redacted>" if detector(value) else value
    if isinstance(value, list):
        return [redact(item, detector) for item in value]
    if isinstance(value, dict):
        return {redact(key, detector): redact(item, detector) for key, item in value.items()}
    return value


def build_snapshot(root: Path, projects_dir: Path | None = None, now: float | None = None,
                   detector: Detector | None = None, with_git: bool = True) -> dict:
    root = root.resolve()
    detector = detector or load_detector(root)
    now = time.time() if now is None else now
    claude = root / ".claude"
    project_dir = (projects_dir or Path.home() / ".claude/projects") / project_slug(root)
    sources: dict[str, dict] = {}
    warnings: list[str] = []
    mtimes: list[float] = []

    def guard(name: str, load: Callable[[], Any], default: Any) -> Any:
        try:
            value = load()
        except Exception as error:  # one broken source must not hide the others
            sources[name] = {"ok": False, "error": type(error).__name__}
            warnings.append(f"Không đọc được nguồn {name}: {type(error).__name__}")
            return default
        sources[name] = {"ok": True, "error": None}
        return value

    def text_of(path: Path) -> str:
        mtimes.append(path.stat().st_mtime)
        return read_inside(path, claude)

    def with_warnings(result: tuple) -> Any:
        warnings.extend(result[1])
        return result[0]

    tasks = guard("ledger", lambda: with_warnings(parse_ledger(text_of(claude / "ledger/screen-feature-plan.md"))), [])
    reports = guard("report", lambda: with_warnings(parse_report_index(text_of(claude / "docs/report/screen-feature-plan.md"))), {})
    paused = guard("plan", lambda: parse_paused_phases(text_of(claude / "docs/plan/screen-feature-plan.md")), [])
    rounds = guard("workspace", lambda: with_warnings(scan_rounds(claude / "docs/review/_workspace")), [])
    agent_list = guard("agents", lambda: read_agents(claude / "agents"), [])
    live = guard("subagents", lambda: with_warnings(scan_subagents(project_dir, now)), {"agents": {}, "sessionActiveAt": None, "latestAt": None})

    def load_docs() -> dict[str, dict | None]:
        docs: dict[str, dict | None] = {}
        for path in sorted((claude / "docs/review").glob("*.md")):
            match = REVIEW_DOC_RE.match(path.name)
            if match:
                docs[match.group(1)] = parse_lead_review(text_of(path))
        return docs

    docs = guard("reviewDocs", load_docs, {})
    latest_by_id: dict[str, dict] = {}
    for item in rounds:
        current = latest_by_id.get(item["id"])
        if current is None or item["round"] > current["round"]:
            latest_by_id[item["id"]] = item
        if item["updatedAt"]:
            mtimes.append(datetime.fromisoformat(item["updatedAt"]).timestamp())
    if live["latestAt"]:
        mtimes.append(live["latestAt"])

    known = {task["id"] for task in tasks}
    for item in rounds:
        item["outOfPlan"] = item["id"] not in known
        item["lead"] = docs.get(item["id"]) if latest_by_id[item["id"]] is item else None

    waiting = []
    for task in tasks:
        task["phase"] = task["id"].split(".")[0]
        task["report"] = reports.get(task["id"])
        task["lead"] = docs.get(task["id"])
        latest = latest_by_id.get(task["id"])
        task["latestRound"] = latest["key"] if latest else None
        task["status"] = task_status(task["gates"], task["report"], task["id"] in docs, task["phase"] in paused, latest)
        if task["status"] == "waiting_user":
            waiting.append({"id": task["id"], "title": task["title"], "reason": waiting_reason(task)})

    done = sum(sum(task["gates"].values()) for task in tasks)
    total = len(tasks) * len(GATES)
    active = [task for task in tasks if task["phase"] not in paused]
    sources_ok = sources["subagents"]["ok"] and not live.get("invalid")
    cards = agent_cards(agent_list, rounds, live, sources_ok)
    session_at = live["sessionActiveAt"]
    summarized = sum(1 for item in rounds if item["stage"] == "summarized")
    repos = []
    if with_git:
        repos = [git_info(repo, now) for repo in (root, root / "ticket-system", root / "booking_ticket_vue") if (repo / ".git").exists()]
    latest_round = rounds[0] if rounds else None

    snapshot = {
        "schema": 1,
        "generatedAt": iso(now),
        "lastChangeAt": iso(max(mtimes, default=None)),
        "mission": {"branch": repos[0]["branch"] if repos and repos[0]["name"] == root.name else None, "latestRound": latest_round["key"] if latest_round else None},
        "progress": {
            "done": done,
            "total": total,
            "percent": round(done * 100 / total) if total else None,
            "activeDone": sum(sum(task["gates"].values()) for task in active),
            "activeTotal": len(active) * len(GATES),
        },
        "counts": {
            "tasksDone": sum(1 for task in tasks if task["status"] == "done"),
            "tasksTotal": len(tasks),
            "waiting": len(waiting),
            "running": sum(entry["running"] for entry in live["agents"].values()),
            "agents": len(cards),
            "latestFindings": len(latest_round["rows"]) if latest_round else None,
        },
        "pausedPhases": paused,
        "orchestrator": {
            "status": "unknown" if not sources_ok else "running" if session_at and now - session_at <= RUNNING_WINDOW else "idle",
            "lastAt": iso(session_at),
            "roundsSummarized": summarized,
            "roundsTotal": len(rounds),
        },
        "waiting": waiting,
        "agents": cards,
        "tasks": tasks,
        "rounds": rounds,
        "latestRound": latest_round["key"] if latest_round else None,
        "repos": repos,
        "sources": sources,
        "warnings": warnings,
    }
    return redact(snapshot, detector)


def main(argv: list[str] | None = None, root: Path | None = None, **snapshot_args: Any) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="print a summary instead of JSON")
    args = parser.parse_args(argv)
    snapshot = build_snapshot(root or Path(__file__).resolve().parents[2], **snapshot_args)
    if not args.check:
        json.dump(snapshot, sys.stdout, ensure_ascii=False, indent=1)
        return 0
    progress = snapshot["progress"]
    counts = snapshot["counts"]
    print(f"Cổng: {progress['done']}/{progress['total']} ({progress['percent']}%), không tính phase tạm dừng: {progress['activeDone']}/{progress['activeTotal']}")
    print(f"Task đủ cổng: {counts['tasksDone']}/{counts['tasksTotal']}, chờ duyệt: {[item['id'] for item in snapshot['waiting']]}")
    print(f"Phase tạm dừng: {snapshot['pausedPhases']}, vòng review: {len(snapshot['rounds'])}, mới nhất: {snapshot['latestRound']}")
    print(f"Agent: {counts['agents']}, đang chạy: {counts['running']}")
    for name, source in snapshot["sources"].items():
        print(f"Nguồn {name}: {'OK' if source['ok'] else 'LỖI ' + str(source['error'])}")
    print(f"Cảnh báo ({len(snapshot['warnings'])}):")
    for warning in snapshot["warnings"]:
        print(f"  - {warning}")
    return 0 if all(source["ok"] for source in snapshot["sources"].values()) else 1


if __name__ == "__main__":
    sys.exit(main())
