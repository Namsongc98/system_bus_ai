---
description: Commit one task as three commits — booking_ticket_vue (after FE unit tests), ticket-system (after BE unit tests), root System_bus docs (no tests) — staging exactly the files listed in the task report .claude/docs/report/<ID>-<slug>.md on a task/<ID>-<slug> branch, message taken from the plan, then hands over to plan-push.
argument-hint: "<task ID from .claude/docs/plan/screen-feature-plan.md, e.g. 0.4, 1.1>"
allowed-tools: Read, Grep, Glob, Bash, Edit
---

# Prompt: Plan Commit

Use `.claude/skills/plan-commit/SKILL.md`.

Normally started by `plan-report`; call it directly to retry a commit after a
failed test run has been fixed.

## Request Template

Plan commit for:
- Task ID:

## Claude Instructions

- Follow the skill exactly: gate → commit 1 `booking_ticket_vue` (FE unit tests
  first) → commit 2 `ticket-system` (BE unit tests first) → fill `## Commit`
  in the task report `.claude/docs/report/<ID>-<slug>.md` → commit 3 root repo (no tests). A test failure stops that
  commit and every later one. Each commit: branch `task/<ID>-<slug>`, stage only
  the task report's files (root also stages the index), verify, commit with the plan-derived message.
- Then run `plan-push` for the same ID. This command itself never pushes,
  never `--no-verify`, never `--amend`, never `git add -A`.
- Do not tick any ledger line. One task ID per run.
