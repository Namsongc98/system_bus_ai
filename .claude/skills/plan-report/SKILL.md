---
name: plan-report
description: Write the report entry for one screen-feature-plan task after /lead-review returned CLEAN — one report file per plan in .claude/docs/report/, one section per task — then hand over to plan-commit. Use when a lead review is CLEAN, when the user asks for a task report, or invokes /plan-report.
argument-hint: "<task ID from .claude/docs/plan/screen-feature-plan.md, e.g. 0.4, 1.1>"
allowed-tools: Read, Grep, Glob, Bash, Write, Edit, Skill
---

# Skill: Plan Report (record a finished task, then commit it)

Also callable as `/plan-report` (`.claude/commands/plan-report.md`). `/lead-review`
runs it automatically when its verdict is `CLEAN`.

```
/lead-review <ID> --CLEAN--> plan-report --> plan-commit --> plan-push --> user ticks `lead-review`
```

One report file per plan, named after the plan file:
`.claude/docs/plan/screen-feature-plan.md` → `.claude/docs/report/screen-feature-plan.md`.
Each task is one `## <ID> — <task name>` section in that file.

## Request Template

Plan report for:
- Task ID:

## Claude Instructions

### 1. Gate
- The task's review doc `.claude/docs/review/<ID>-<slug>.md` must have a
  `## 7. Lead review` section whose current verdict is `CLEAN`. Otherwise stop:
  point to `/lead-review <ID>` (or `/plan-task <ID>` if it is `OPEN`).

### 2. Collect facts — never invent
Read, do not guess:
- Plan `.claude/docs/plan/screen-feature-plan.md`: plan title (first `#` heading),
  the task row (name, owner area, size, DoD).
- Review doc sections 1–7: fix scope `S<n>`, endpoints, lead-review round,
  verdict, findings and their statuses, commands run.
- Ledger `.claude/ledger/screen-feature-plan.md`: the task's checklist.
- Git, per repo (`ticket-system`, `booking_ticket_vue`, and the root repo for
  `.claude/…`): `git -C <repo> status --porcelain` and `git -C <repo> diff -- <file>`.

### 3. Build the changed-file list (used by `plan-commit` to stage)
- Start from every file the review doc names as changed or added for this task
  (fix scope, lead-review evidence, tests), plus the task's own docs in the root
  repo: this report file, the review doc, the ledger, the plan (if the task
  edited it).
- Keep only paths that are actually uncommitted in `git status`. List them per
  repo with repo-relative paths. Never list `.env*`, secrets, `target/`,
  `node_modules/`, `dist/`, or runtime data.
- For each file, read its diff. If it also holds changes that are not this
  task's (another task's scope, older unrelated work), mark it
  `mixed — also contains <what>`. Mixed files are still committed whole; the
  mark goes into the commit message.
- An untracked directory counts only for the files of this task inside it —
  list files, not the directory.

### 4. Write the section
Create `.claude/docs/report/<plan-file-name>.md` if missing, with
`# Report — <plan title>` and one line pointing at the plan. Then insert this
task's section in task-ID order, replacing an existing section for the same ID:

```
## <ID> — <task name from the plan>

Date: <YYYY-MM-DD> · Lead review: round <N>, CLEAN · Review doc: `.claude/docs/review/<ID>-<slug>.md`

### Kết quả
- DoD (plan): <DoD cell> → <how it was met, with the test that proves it>
- S1 … Sn: <one line each, done / not done>

### Endpoint thay đổi
| Method | Path | Auth | Change |

### File thay đổi
**ticket-system** (branch at report time: <branch>)
- `path` — <what> [mixed — also contains …]
**booking_ticket_vue** / **root repo** — same format; omit a repo with no files.

### Test
- `<command>` → <pass/fail counts>

### Review
- <rounds, who reviewed, key fixes> (short; details stay in the review doc)

### Còn lại
- DEFER: L<n> → B<n> / task <id> …
- NEEDS-USER: L<n> … (or "none")

### Commit
(pending — filled by plan-commit)
```

### 5. Hand over
Invoke the `plan-commit` skill for the same task ID. Report the report path and
the per-repo file list (with mixed marks) in the chat.

## Boundaries
- No code edits. Writes only the report file.
- Do not tick any ledger line.
- One task ID per run.
