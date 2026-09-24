---
name: git-commit
description: Commit and push one finished screen-feature-plan task — three commits (booking_ticket_vue after FE unit tests, ticket-system after BE unit tests, root System_bus docs without tests), each on a task/<ID>-<slug> branch staging exactly the files the task report (.claude/docs/report/<ID>-<slug>.md) lists with the message taken from the plan, then push those branches to origin with an explicit refspec, never force, no pull request. Run only when the user invokes /git-commit (or explicitly asks to commit a task) — never automatically after lead-review or plan-report.
argument-hint: "<task ID from .claude/docs/plan/screen-feature-plan.md, e.g. 0.4, 1.1>"
allowed-tools: Read, Grep, Glob, Bash, Edit
---

# Skill: Git Commit (commit FE → BE → root, then push)

Also callable as `/git-commit` (`.claude/commands/git-commit.md`). Started only
by the user, after `/lead-review <ID>` is `CLEAN`, `plan-report` has written the
task report, and the user has inspected the changed files. `/lead-review` and
`plan-report` never start it.

```
/lead-review <ID> --CLEAN--> plan-report --> STOP (user inspects changed files)
/git-commit <ID> (user runs it): A. commit FE → BE → root   B. push FE → BE → root
                              --> user ticks `lead-review`
```

"The report" below always means the task report file
`.claude/docs/report/<ID>-<slug>.md` (same `<ID>-<slug>` as the review doc), not
the plan's index `.claude/docs/report/<plan-file-name>.md`.

`booking_ticket_vue/` and `ticket-system/` are separate git repos (the root
repo ignores both). The root repo `.` (System_bus) only holds `.claude/…` docs
for the AI workflow. One task therefore becomes up to three commits, in this
order:

| # | Repo | Test before commit | No files for this task in the report |
|---|---|---|---|
| 1 | `booking_ticket_vue` | `npm --prefix booking_ticket_vue run test:unit -- --run` | skip test, commit and push; record "no files" |
| 2 | `ticket-system` | `mvn -f ticket-system/pom.xml -pl manage-revenue-ticket,booking_ticket -am test` | skip test, commit and push; record "no files" |
| 3 | `.` (System_bus) | **none** — docs only, commit directly | always has files (task report, index, review doc, ledger…) |

Remotes (`origin` in each repo): `booking_ticket_vue` → `system_bus_fe`,
`ticket-system` → `system_bus_be`, `.` → `system_bus_ai`. Pushing publishes
to GitHub and cannot be taken back by Claude — the user approves each push
command when Claude Code asks (no allow rule for push on purpose).

## Request Template

Git commit for:
- Task ID:

## Claude Instructions

### 1. Gate
- `.claude/docs/report/<ID>-<slug>.md` exists, the index
  `.claude/docs/report/<plan-file-name>.md` has a row for `<ID>`, and the task's
  review doc `## 7. Lead review` verdict is `CLEAN`. Otherwise stop: point to
  `/plan-report <ID>` (or `/lead-review <ID>`).
- For every repo that has files in the report's `## File thay đổi` list:
  `git -C <repo> diff --cached --quiet` must succeed (nothing already staged).
  Something staged → stop and show it; never commit someone else's staged work.
- **Retry after an earlier stopped run** (test failure, network, auth):
  - Commit part: a repo whose branch `task/<ID>-<slug>` already exists and has
    none of the report's files left uncommitted is already committed — skip its
    commit and continue with the next repo.
  - Push part: a repo whose `origin/task/<ID>-<slug>` already points at the
    local branch hash is already pushed — skip its push.

### Part A — Commit

#### 2. Commit procedure (used by commits 1–3)
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

   <Co-Authored-By trailer given by the session's attribution instructions>
   ```
   Pass it with a heredoc (`git -C <repo> commit -F - <<'EOF' … EOF`). If a
   commit hook fails, fix the cause and make a new commit — never `--no-verify`,
   never `--amend`.
5. Record `git -C <repo> rev-parse --short HEAD`.

#### 3. Commit 1 — `booking_ticket_vue` (FE)
Run the FE unit tests. Any failure or error → **stop: no commit here, none of
the later commits, and no push at all**. Write the pass/fail counts and failing
test names under `## Commit` in the report and tell the user to fix it via
`/plan-task <ID>` (then `/lead-review <ID>` again). Green → run the commit
procedure. Do not skip, disable, or mark tests to get green.

#### 4. Commit 2 — `ticket-system` (BE)
Same as commit 1 with the BE unit tests. If commit 1 is already made and the BE
tests fail, commit 1 stays on its branch (no rollback, no `reset`) and nothing
is pushed; record that in the report — the retry skips the FE commit (see Gate).

#### 5. Commit 3 — root repo `.` (System_bus docs)
No unit tests. First fill the report's `## Commit` with, per code repo:
branch, short hash, file count, mixed files (or "no files" / test result).
Then run the commit procedure for the root repo; its listed files include the
updated task report and the index. The root commit's own hash is reported in
chat only.

### Part B — Push
Start only when every commit Part A needed has succeeded.

#### 6. Before pushing
- Repos to push = the repos with a commit for this task, in order
  `booking_ticket_vue` → `ticket-system` → `.`. A repo recorded as "no files" is
  skipped.
- For each: `git -C <repo> rev-parse --verify task/<ID>-<slug>` must succeed,
  and `git -C <repo> log -1 --format=%h task/<ID>-<slug>` must match the hash
  recorded in `## Commit` (root repo: its commit message starts with `<ID> `).
  Mismatch → stop and show both; never push something the report does not
  describe.
- `git -C <repo> ls-remote --heads origin task/<ID>-<slug>`: if the branch
  already exists on origin and its hash is not an ancestor of the local branch
  (`git -C <repo> merge-base --is-ancestor <remote-hash> task/<ID>-<slug>`
  fails, or the hash is unknown locally), stop: the remote has diverged. Never
  force.
- If the report marks the task **Not self-contained**, say so in the chat
  before pushing: CI on that branch may fail until the dependent work is
  committed. This is a warning, not a stop.

#### 7. Push, one repo at a time
```bash
git -C <repo> push -u origin task/<ID>-<slug>
```
Always the explicit branch name — never a bare `git push`, `HEAD`, `--all`,
`--tags`, `--mirror`, `--force`, `--force-with-lease`, or a `:branch` delete.
A failure (auth, network, rejected) → stop, report the git message, and leave
the rest unpushed; the user re-runs `/git-commit <ID>` to continue. Do not retry
with other credentials, do not ask the user for tokens, do not change remotes.

### 8. Report (chat only — the report file is already committed)
- Test results: FE, BE (counts, or "skipped — no files").
- Per repo: branch, hash, files committed, mixed files, push result, remote URL
  (`git -C <repo> remote get-url origin`), or "skipped — no files" / the failure.
- Compare link to open a PR if the user wants one:
  `<remote URL without .git>/compare/<base>...task/<ID>-<slug>` with base
  `main` for `booking_ticket_vue` / `ticket-system`, `develop` for the root repo.
  Do not create the PR.
- Reminder: `lead-review` in the ledger is still for the user to tick.

## Boundaries
- Commit only files listed in the task report for this task.
- Push only `task/<ID>-<slug>` branches of this task. Never push `main`,
  `develop`, or any other branch.
- Never force anything, never delete local or remote branches, never
  `reset`/`clean`/`checkout .`, never `--no-verify` or `--amend`.
- Never create pull requests, never edit remotes or git config.
- Do not tick any ledger line. One task ID per run.
