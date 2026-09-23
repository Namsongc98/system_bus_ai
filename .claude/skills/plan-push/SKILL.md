---
name: plan-push
description: Push the task/<ID>-<slug> branches that plan-commit created for one screen-feature-plan task to origin — booking_ticket_vue, then ticket-system, then the root System_bus repo — with an explicit refspec, never force. Does not open pull requests. Use right after plan-commit, or when the user invokes /plan-push.
argument-hint: "<task ID from .claude/docs/plan/screen-feature-plan.md, e.g. 0.4, 1.1>"
allowed-tools: Read, Grep, Glob, Bash
---

# Skill: Plan Push (push one task's branches)

Also callable as `/plan-push` (`.claude/commands/plan-push.md`). Normally
started by `plan-commit` after its last commit succeeded.

```
/lead-review <ID> --CLEAN--> plan-report --> plan-commit --> plan-push --> user ticks `lead-review`
```

Remotes (`origin` in each repo): `booking_ticket_vue` → `system_bus_fe`,
`ticket-system` → `system_bus_be`, `.` → `system_bus_ai`. Pushing publishes
to GitHub and cannot be taken back by Claude — the user approves each push
command when Claude Code asks (no allow rule for push on purpose).

## Request Template

Plan push for:
- Task ID:

## Claude Instructions

### 1. Gate
- The report `.claude/docs/report/<plan-file-name>.md` has a `## <ID> — …`
  section whose `### Commit` lists the commits `plan-commit` made. No commits
  recorded (blocked, test failure, pending) → stop: point to `/plan-commit <ID>`.
- Repos to push = the repos with a commit for this task, in order
  `booking_ticket_vue` → `ticket-system` → `.`. A repo recorded as "no files" is
  skipped.
- For each: `git -C <repo> rev-parse --verify task/<ID>-<slug>` must succeed,
  and `git -C <repo> log -1 --format=%h task/<ID>-<slug>` must match the
  recorded hash (root repo: its commit message starts with `<ID> `). Mismatch →
  stop and show both; never push something the report does not describe.

### 2. Before pushing
- `git -C <repo> ls-remote --heads origin task/<ID>-<slug>`: if the branch
  already exists on origin and its hash is not an ancestor of the local branch
  (`git -C <repo> merge-base --is-ancestor <remote-hash> task/<ID>-<slug>`
  fails, or the hash is unknown locally), stop: the remote has diverged. Never
  force.
- If the report marks the task **Not self-contained**, say so in the chat
  before pushing: CI on that branch may fail until the dependent work is
  committed. This is a warning, not a stop.

### 3. Push, one repo at a time
```bash
git -C <repo> push -u origin task/<ID>-<slug>
```
Always the explicit branch name — never a bare `git push`, `HEAD`, `--all`,
`--tags`, `--mirror`, `--force`, `--force-with-lease`, or a `:branch` delete.
A failure (auth, network, rejected) → stop, report the git message, and leave
the rest unpushed. Do not retry with other credentials, do not ask the user
for tokens, do not change remotes.

### 4. Report (chat only — the report file is already committed)
- Per repo: branch, pushed hash, remote URL (`git -C <repo> remote get-url
  origin`), or "skipped — no commit" / the failure.
- Compare link to open a PR if the user wants one:
  `<remote URL without .git>/compare/<base>...task/<ID>-<slug>` with base
  `main` for `booking_ticket_vue` / `ticket-system`, `develop` for the root repo.
  Do not create the PR.
- Reminder: `lead-review` in the ledger is still for the user to tick.

## Boundaries
- Push only `task/<ID>-<slug>` branches of this task. Never push `main`,
  `develop`, or any other branch.
- Never force, never delete remote branches, never create pull requests,
  never edit remotes or git config.
- No file edits, no commits, no ledger ticks. One task ID per run.
