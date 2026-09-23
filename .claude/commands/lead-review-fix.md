---
description: Fix the open FIX findings /lead-review recorded for one screen-feature-plan task, re-verify and re-review, then hand back to /lead-review.
argument-hint: "<task ID from .claude/docs/plan/screen-feature-plan.md, e.g. 0.5, 1.1>"
allowed-tools: Read, Grep, Glob, Bash, Write, Edit
---

# Prompt: Lead Review Fix (the fix step of the lead-review loop)

Use `.claude/skills/lead-review-fix/SKILL.md`.

Flow: `/lead-review <ID>` (verdict `OPEN`) → `/plan-task <ID>` (routes here
automatically) or `/lead-review-fix <ID>` → `/lead-review <ID>` again. At most
3 rounds; then stop and ask the user.

## Request Template

Lead review fix for:
- Task ID:

## Claude Instructions

- Follow the skill's Claude Instructions exactly (gate → re-verify → fix only
  `FIX` rows → defer / needs-user → verify and review → update status → report).
- Input is the `## 7. Lead review` section of `.claude/docs/review/<ID>-<slug>.md`; missing → stop and point
  to `/lead-review <ID>`.
- Do not tick `spec` or `lead-review`.
- One task ID per run.
