---
description: Commit and push one CLEAN task — booking_ticket_vue (after FE unit tests), ticket-system (after BE unit tests), root System_bus docs (no tests) — staging exactly the files listed in the task report .claude/docs/report/<ID>-<slug>.md on a task/<ID>-<slug> branch, message taken from the plan, then push those branches to origin. Never force, no pull request.
argument-hint: "<task ID from .claude/docs/plan/screen-feature-plan.md, e.g. 0.4, 1.1>"
allowed-tools: Read, Grep, Glob, Bash, Edit
---

# Prompt: Git Commit

Use `.claude/skills/git-commit/SKILL.md`.

Run by the user after `/lead-review <ID>` is CLEAN and `plan-report` has listed
the changed files. Re-run it to continue after a failed test, network or auth
error — commits and pushes already done are skipped. Never started automatically.

## Request Template

Git commit for:
- Task ID:

## Claude Instructions

- Follow the skill exactly: gate → **commit** `booking_ticket_vue` (FE unit
  tests first) → `ticket-system` (BE unit tests first) → fill `## Commit` in the
  task report → root repo (no tests) → **push** the same order with
  `git -C <repo> push -u origin task/<ID>-<slug>` after checking the remote has
  not diverged → report hashes and compare links in chat.
- A test failure stops that commit, every later one, and the whole push part.
- Each commit: branch `task/<ID>-<slug>`, stage only the task report's files
  (root also stages the index), verify, commit with the plan-derived message.
- Never force, never `--no-verify`, never `--amend`, never `git add -A`, never
  push another branch, never open a PR.
- Do not tick any ledger line. One task ID per run.
