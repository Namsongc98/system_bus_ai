#!/usr/bin/env python3
"""Build the `system-bus-dev` plugin from the repo's .claude/ directory.

Source of truth stays in .claude/{skills,commands,agents}. This script copies
them into dist/system-bus-dev/, injects a short repo-context preamble so the
paths inside each file resolve in both Claude Code (repo root = cwd) and the
Claude App / Cowork (repo = connected folder), then zips dist/system-bus-dev.plugin.

Usage (from repo root):  python3 .claude/plugin/build_plugin.py [--version X.Y.Z]
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

PLUGIN_NAME = "system-bus-dev"
ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / ".claude"
DIST = ROOT / "dist"
OUT_DIR = DIST / PLUGIN_NAME
EXCLUDE_NAMES = {".DS_Store", "__pycache__"}

PREAMBLE = """> **Repo context ({plugin} plugin).** Paths such as `.claude/…`, `ticket-system/…`,
> `booking_ticket_vue/…` are relative to the **System_bus repo root**: the working
> directory in Claude Code, or the connected folder `System_bus`
> (`$HOME/mnt/System_bus` in the device shell) in the Claude App. If the repo is not
> reachable, stop and ask the user to connect the `System_bus` folder.
"""

FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.S)


def git_version() -> str:
    try:
        count = subprocess.check_output(
            ["git", "-C", str(ROOT), "rev-list", "--count", "HEAD"], text=True
        ).strip()
        return f"0.1.{int(count)}"
    except (subprocess.CalledProcessError, FileNotFoundError, ValueError):
        return "0.1.0"


def inject_preamble(text: str) -> str:
    match = FRONTMATTER.match(text)
    preamble = PREAMBLE.format(plugin=PLUGIN_NAME)
    if not match:
        return preamble + "\n" + text
    head, body = text[: match.end()], text[match.end():]
    return f"{head}\n{preamble}\n{body.lstrip()}"


def copy_tree(src: Path, dst: Path) -> None:
    for path in src.rglob("*"):
        if any(part in EXCLUDE_NAMES for part in path.parts):
            continue
        target = dst / path.relative_to(src)
        if path.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        if path.name == "SKILL.md":
            target.write_text(inject_preamble(path.read_text(encoding="utf-8")), encoding="utf-8")
        else:
            shutil.copy(path, target)  # fresh mtime: marks the file as part of this build


BUILD_STARTED = 0.0


def build(version: str) -> Path:
    global BUILD_STARTED
    import time
    BUILD_STARTED = time.time() - 1
    # Overwrite in place instead of rmtree: the Cowork device shell cannot delete
    # files without an extra permission. Only files written by this run are zipped,
    # so stale files left in OUT_DIR never reach the .plugin archive.
    (OUT_DIR / ".claude-plugin").mkdir(parents=True, exist_ok=True)

    skills = sorted(p for p in (SRC / "skills").iterdir() if (p / "SKILL.md").is_file())
    for skill in skills:
        copy_tree(skill, OUT_DIR / "skills" / skill.name)

    skill_names = {s.name for s in skills}
    commands, skipped = [], []
    (OUT_DIR / "commands").mkdir(exist_ok=True)
    for cmd in sorted((SRC / "commands").glob("*.md")):
        if cmd.stem in skill_names:
            skipped.append(cmd.stem)  # same slash name as a skill -> skill wins
            continue
        (OUT_DIR / "commands" / cmd.name).write_text(
            inject_preamble(cmd.read_text(encoding="utf-8")), encoding="utf-8"
        )
        commands.append(cmd.stem)

    agents = []
    (OUT_DIR / "agents").mkdir(exist_ok=True)
    for agent in sorted((SRC / "agents").glob("*.md")):
        (OUT_DIR / "agents" / agent.name).write_text(
            inject_preamble(agent.read_text(encoding="utf-8")), encoding="utf-8"
        )
        agents.append(agent.stem)

    manifest = {
        "name": PLUGIN_NAME,
        "version": version,
        "description": "System_bus (Ticket Bus) dev toolkit: Spring Boot + Vue skills, "
        "review agents, and the screen-feature plan runner (plan-task).",
        "author": {"name": "Sơn Lucky"},
        "keywords": ["spring-boot", "vue", "kafka", "code-review", "system-bus"],
    }
    (OUT_DIR / ".claude-plugin" / "plugin.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    readme = [
        f"# {PLUGIN_NAME} v{version}",
        "",
        "**Generated file — do not edit.** Source: `.claude/{skills,commands,agents}` "
        "in the System_bus repo. Rebuild with `python3 .claude/plugin/build_plugin.py`.",
        "",
        "Requires the `System_bus` repo: open Claude Code at the repo root, or connect "
        "the `System_bus` folder in the Claude App.",
        "",
        f"## Skills ({len(skills)})",
        *[f"- `{s.name}`" for s in skills],
        "",
        f"## Commands ({len(commands)})",
        *[f"- `/{c}`" for c in commands],
        "",
        f"## Agents ({len(agents)})",
        *[f"- `{a}`" for a in agents],
        "",
        "Not packaged: hooks (`.claude/settings.json` + `claude_hook.py` stay repo-only), "
        "references/docs/ledger (read from the repo at runtime).",
    ]
    if skipped:
        readme += ["", "Commands skipped (a skill has the same name): "
                   + ", ".join(f"`{s}`" for s in skipped)]
    (OUT_DIR / "README.md").write_text("\n".join(readme) + "\n", encoding="utf-8")

    started = BUILD_STARTED
    archive = DIST / f"{PLUGIN_NAME}.plugin"
    stale = []
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:  # "w" truncates
        for path in sorted(OUT_DIR.rglob("*")):
            if not path.is_file():
                continue
            if path.stat().st_mtime < started:
                stale.append(path)
                try:
                    path.unlink()
                except PermissionError:
                    pass
                continue
            zf.write(path, path.relative_to(OUT_DIR))
    if stale:
        print(f"  excluded {len(stale)} stale file(s) from a previous build")

    print(f"built {archive.relative_to(ROOT)}  v{version}")
    print(f"  skills={len(skills)} commands={len(commands)} agents={len(agents)}")
    if skipped:
        print(f"  skipped commands (name clash with skill): {', '.join(skipped)}")
    return archive


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default=None)
    args = parser.parse_args()
    build(args.version or git_version())
    return 0


if __name__ == "__main__":
    sys.exit(main())
