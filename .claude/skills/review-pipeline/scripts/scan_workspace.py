#!/usr/bin/env python3
"""Scan review-pipeline workspace files for secrets with the hook's own patterns.

The workspace is git-ignored, so the Stop hook never scans it. Run this after
writing the files of a round; it prints only file names and pattern names,
never the matched values.

Usage (from repo root):
  python3 .claude/skills/review-pipeline/scripts/scan_workspace.py .claude/docs/review/_workspace/<ID>/round-<N>
Exit code: 0 = clean, 1 = possible secret found, 2 = bad path.
"""
from __future__ import annotations

import runpy
import sys
from pathlib import Path

HOOK = Path(__file__).resolve().parents[3] / "hooks" / "claude_hook.py"


def main() -> int:
    if len(sys.argv) != 2 or not Path(sys.argv[1]).is_dir():
        print(__doc__.strip().splitlines()[-2])
        return 2
    secret_findings = runpy.run_path(str(HOOK))["secret_findings"]
    hits = 0
    for path in sorted(Path(sys.argv[1]).rglob("*.md")):
        names = secret_findings(path.read_text(encoding="utf-8", errors="replace"))
        if names:
            hits += 1
            print(f"{path}: {', '.join(names)}")
    print("clean" if hits == 0 else f"{hits} file(s) with possible secrets — replace the values with <redacted>")
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
