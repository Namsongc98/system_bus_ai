---
description: Push one task's task/<ID>-<slug> branches (booking_ticket_vue, ticket-system, root repo) to origin after plan-commit. Explicit refspec, never force, no pull request.
argument-hint: "<task ID from .claude/docs/plan/screen-feature-plan.md, e.g. 0.4, 1.1>"
allowed-tools: Read, Grep, Glob, Bash
---

# Prompt: Plan Push

Use `.claude/skills/plan-push/SKILL.md`.

Normally started by `plan-commit`; call it directly to retry a push that
failed (network, auth) or for a task committed before this skill existed.

## Request Template

Plan push for:
- Task ID:

## Claude Instructions

- Follow the skill exactly: gate (commits recorded in the task report
  `.claude/docs/report/<ID>-<slug>.md`, local branch
  matches) → check the remote branch has not diverged → push
  `booking_ticket_vue` → `ticket-system` → root repo with
  `git -C <repo> push -u origin task/<ID>-<slug>` → report hashes and compare
  links in chat.
- Never force, never push another branch, never open a PR.
- Do not tick any ledger line. One task ID per run.
