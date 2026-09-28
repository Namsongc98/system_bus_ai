---
name: plan-report
description: Write the report for one screen-feature-plan task after /lead-review returned CLEAN — one report file per task (.claude/docs/report/<ID>-<slug>.md) plus a row in the plan's index file (.claude/docs/report/<plan-file-name>.md) — then show the changed-file list and stop; the user runs /git-commit. Use when a lead review is CLEAN, when the user asks for a task report, or invokes /plan-report.
argument-hint: "<task ID from .claude/docs/plan/screen-feature-plan.md, e.g. 0.4, 1.1>"
allowed-tools: Read, Grep, Glob, Bash, Write, Edit, Skill
---

# Skill: Plan Report (record a finished task, show its changed files)

Also callable as `/plan-report` (`.claude/commands/plan-report.md`). `/lead-review`
runs it automatically when its verdict is `CLEAN`.

```
/lead-review <ID> --CLEAN--> plan-report
                               1. write .claude/docs/report/<ID>-<slug>.md   (task report)
                               2. update .claude/docs/report/<plan-file-name>.md (index row)
                               3. show the changed-file list, STOP
user inspects the changes --> /git-commit <ID> (commit + push) --> user ticks `lead-review`
```

Two outputs, both in `.claude/docs/report/`:

| File | Content |
|---|---|
| `<ID>-<slug>.md` — same name as the task's review doc `.claude/docs/review/<ID>-<slug>.md` | The full report of one task. `git-commit` reads it. |
| `<plan-file-name>.md` — `.claude/docs/plan/screen-feature-plan.md` → `screen-feature-plan.md` | Index only: one table row per reported task, linking to its task file. |

## Request Template

Plan report for:
- Task ID:

## Claude Instructions

### 1. Gate
- The task's review doc `.claude/docs/review/<ID>-<slug>.md` must have a
  `## 7. Lead review` section whose current verdict is `CLEAN`. Otherwise stop:
  point to `/lead-review <ID>` (or `/plan-task <ID>` if it is `OPEN`).
- `<slug>` is taken from that review doc's file name; the task report file uses
  the same `<ID>-<slug>`.

### 2. Collect facts — never invent
Read, do not guess:
- Plan `.claude/docs/plan/screen-feature-plan.md`: plan title (first `#` heading),
  the task row (name, owner area, size, DoD).
- Review doc sections 1–7: fix scope `S<n>`, endpoints, lead-review round,
  verdict, findings and their statuses, commands run.
- Ledger `.claude/ledger/screen-feature-plan.md`: the task's checklist.
- Git, per repo (`ticket-system`, `booking_ticket_vue`, and the root repo for
  `.claude/…`): `git -C <repo> status --porcelain` and `git -C <repo> diff -- <file>`.

### 3. Build the changed-file list (used by `git-commit` to stage)
- Start from every file the review doc names as changed or added for this task
  (fix scope, lead-review evidence, tests), plus the task's own docs in the root
  repo: the task report file `<ID>-<slug>.md`, the index `<plan-file-name>.md`,
  the review doc, the ledger, the plan (if the task edited it). The two report
  files are always listed for the root repo.
- Keep only paths that are actually uncommitted in `git status`. List them per
  repo with repo-relative paths. Never list `.env*`, secrets, `target/`,
  `node_modules/`, `dist/`, or runtime data.
- For each file, read its diff. If it also holds changes that are not this
  task's (another task's scope, older unrelated work), mark it
  `mixed — also contains <what>`. Mixed files are still committed whole; the
  mark goes into the commit message.
- An untracked directory counts only for the files of this task inside it —
  list files, not the directory.

### 4. Write the task report file
Create or overwrite `.claude/docs/report/<ID>-<slug>.md`:

```
# <ID> — <task name from the plan>

Plan: `.claude/docs/plan/<plan-file-name>.md` · Index: `.claude/docs/report/<plan-file-name>.md`
Date: <YYYY-MM-DD> · Lead review: round <N>, CLEAN · Review doc: `.claude/docs/review/<ID>-<slug>.md`

## Kết quả
- DoD (plan): <DoD cell> → <how it was met, with the test that proves it>
- S1 … Sn: <one line each, done / not done>

## Endpoint thay đổi
| Method | Path | Auth | Change |

## File thay đổi
**ticket-system** (branch at report time: <branch>)
- `path` — <what> [mixed — also contains …]
**booking_ticket_vue** / **root repo** — same format; omit a repo with no files.

## Test
- `<command>` → <pass/fail counts>

## Review
- <rounds, who reviewed, key fixes> (short; details stay in the review doc)

## Còn lại
- DEFER: L<n> → B<n> / task <id> …
- NEEDS-USER: L<n> … (or "none")

## Commit
(pending — filled by git-commit)
```

### 5. Update the index
In `.claude/docs/report/<plan-file-name>.md` — create it if missing:

```
# Report — <plan title>

Plan: `.claude/docs/plan/<plan-file-name>.md` · Ledger: `.claude/ledger/<plan-file-name>.md`.
Mỗi task CLEAN ở `/lead-review` có 1 file report riêng (viết bởi skill `plan-report`);
file này chỉ là mục lục.

| ID | Task | Ngày | Lead review | Report |
|---|---|---|---|---|
```

Insert this task's row in task-ID order, or replace the existing row for the
same ID:
`| <ID> | <task name> | <YYYY-MM-DD> | round <N>, CLEAN | [<ID>-<slug>.md](<ID>-<slug>.md) |`.
No other content goes into the index.

### 6. Hand over to the user
Do **not** invoke `git-commit`. In the chat, report both file paths and the
per-repo changed-file list (with mixed marks and a one-line note of what changed
in each file), plus `git -C <repo> diff --stat` for tracked files, so the user
can inspect the changes. End by telling the user to run `/git-commit <ID>` when
they are ready to commit and push.

## Boundaries
- No code edits. Writes only the task report file and the index row.
- Never commit or push — that starts only when the user runs `/git-commit`.
- Do not tick any ledger line.
- One task ID per run.
