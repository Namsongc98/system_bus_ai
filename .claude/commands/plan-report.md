---
description: Write the report file for one CLEAN screen-feature-plan task (.claude/docs/report/<ID>-<slug>.md) and its row in the plan index (.claude/docs/report/<plan-file-name>.md), then show the changed files and stop (the user runs /git-commit).
argument-hint: "<task ID from .claude/docs/plan/screen-feature-plan.md, e.g. 0.4, 1.1>"
allowed-tools: Read, Grep, Glob, Bash, Write, Edit, Skill
---

# Prompt: Plan Report

Use `.claude/skills/plan-report/SKILL.md`.

Flow: `/lead-review <ID>` (CLEAN) → `/plan-report <ID>` (runs automatically:
writes `.claude/docs/report/<ID>-<slug>.md` + index row in
`.claude/docs/report/<plan-file-name>.md`, shows the changed files, stops) → user
inspects the changes → `/git-commit <ID>` (user runs it: commit + push) → user
ticks `lead-review`.

## Request Template

Plan report for:
- Task ID:

## Claude Instructions

- Follow the skill exactly: gate on a CLEAN lead review → collect facts →
  per-repo changed-file list with mixed marks → write the task report file →
  update the index row → show the changed-file list → stop.
- Writes only the task report file and the index row. Never commit or push.
  Do not tick any ledger line.
- One task ID per run.
