---
name: plan-commit
description: Commit one finished screen-feature-plan task after plan-report, as three separate commits — booking_ticket_vue (FE unit tests first), then ticket-system (BE unit tests first), then the root System_bus docs repo (no tests) — each on a task/<ID>-<slug> branch, staging exactly the files the report lists, with the message taken from the plan. Does not push itself; hands over to plan-push. Use after plan-report, or when the user invokes /plan-commit.
argument-hint: "<task ID from .claude/docs/plan/screen-feature-plan.md, e.g. 0.4, 1.1>"
allowed-tools: Read, Grep, Glob, Bash, Edit
---

# Skill: Plan Commit (three commits: FE → BE → root docs)

Also callable as `/plan-commit` (`.claude/commands/plan-commit.md`). Normally
started by `plan-report` right after it writes the task's report section.

`booking_ticket_vue/` and `ticket-system/` are separate git repos (the root
repo ignores both). The root repo `.` (System_bus) only holds `.claude/…` docs
for the AI workflow. One task therefore becomes up to three commits, in this
order:

| # | Repo | Test before commit | No files for this task in the report |
|---|---|---|---|
| 1 | `booking_ticket_vue` | `npm --prefix booking_ticket_vue run test:unit -- --run` | skip test and commit, record "no files" |
| 2 | `ticket-system` | `mvn -f ticket-system/pom.xml -pl manage-revenue-ticket,booking_ticket -am test` | skip test and commit, record "no files" |
| 3 | `.` (System_bus) | **none** — docs only, commit directly | always has files (report, review doc, ledger…) |

## Request Template

Plan commit for:
- Task ID:

## Claude Instructions

### 1. Gate
- `.claude/docs/report/<plan-file-name>.md` has a `## <ID> — …` section, and the
  task's review doc `## 7. Lead review` verdict is `CLEAN`. Otherwise stop.
- For every repo that has files in the report's `### File thay đổi` list:
  `git -C <repo> diff --cached --quiet` must succeed (nothing already staged).
  Something staged → stop and show it; never commit someone else's staged work.
- Retry after an earlier failed run: a repo whose branch `task/<ID>-<slug>`
  already exists and has none of the report's files left uncommitted is already
  done — skip it and continue with the next repo.

### 2. Commit procedure (used by commits 1–3)
For repo `<repo>`:

1. Branch: `git -C <repo> switch -c task/<ID>-<slug>` (slug from the review doc
   file name). If it already exists: `git -C <repo> switch task/<ID>-<slug>`.
   The branch starts from the current HEAD, so branches of later tasks stack
   on top of earlier ones — say so in the report the first time it happens.
2. Stage exactly the report's files for that repo:
   `git -C <repo> add -- <file> <file> …`. Never `git add -A`, `.`, a directory,
   or a glob.
3. Check `git -C <repo> diff --cached --name-only` equals that list. Anything
   extra, or any `.env*`, key, credential, `target/`, `node_modules/`, `dist/`
   path → unstage it (`git -C <repo> restore --staged -- <path>`) and stop.
4. Commit with a message built from the plan (no invented text):
   ```
   <ID> <task name from the plan table>

   DoD: <DoD cell from the plan table>
   Scope: <S1..Sn done> — see .claude/docs/review/<ID>-<slug>.md
   Mixed files: <file> — also contains <…>        (only if the report marks any)

   Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
   ```
   Pass it with a heredoc (`git -C <repo> commit -F - <<'EOF' … EOF`). If a
   commit hook fails, fix the cause and make a new commit — never `--no-verify`,
   never `--amend`.
5. Record `git -C <repo> rev-parse --short HEAD`.

### 3. Commit 1 — `booking_ticket_vue` (FE)
Run the FE unit tests. Any failure or error → **stop: no commit here and none
of the later commits**. Write the pass/fail counts and failing test names
under `### Commit` in the report and tell the user to fix it via
`/plan-task <ID>` (then `/lead-review <ID>` again). Green → run the commit
procedure. Do not skip, disable, or mark tests to get green.

### 4. Commit 2 — `ticket-system` (BE)
Same as commit 1 with the BE unit tests. If commit 1 is already made and the BE
tests fail, commit 1 stays on its branch (no rollback, no `reset`); record that
in the report — the retry skips `booking_ticket_vue` (see Gate).

### 5. Commit 3 — root repo `.` (System_bus docs)
No unit tests. First fill the report's `### Commit` with, per code repo:
branch, short hash, file count, mixed files (or "no files" / test result).
Then run the commit procedure for the root repo; its listed files include the
updated report. The root commit's own hash is reported in chat only.

### 6. Report
- Test results: FE, BE (counts, or "skipped — no files").
- Per repo: branch, hash, files committed, mixed files.
- Then invoke the `plan-push` skill for the same task ID (only when every
  commit this run needed succeeded; a stop above means no push).

## Boundaries
- Never `git push` here (pushing belongs to `plan-push`), never force anything, never delete branches, never
  `reset`/`clean`/`checkout .`, never `--no-verify` or `--amend`.
- Commit only files listed in the report for this task.
- Do not tick any ledger line.
- One task ID per run.
