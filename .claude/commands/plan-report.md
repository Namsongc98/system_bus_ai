---
description: Write the report file for one CLEAN screen-feature-plan task (.claude/docs/report/<ID>-<slug>.md) and its row in the plan index (.claude/docs/report/<plan-file-name>.md), then run plan-commit.
argument-hint: "<task ID from .claude/docs/plan/screen-feature-plan.md, e.g. 0.4, 1.1>"
allowed-tools: Read, Grep, Glob, Bash, Write, Edit, Skill
---

# Prompt: Plan Report

Use `.claude/skills/plan-report/SKILL.md`.

Flow: `/lead-review <ID>` (CLEAN) → `/plan-report <ID>` (runs automatically:
writes `.claude/docs/report/<ID>-<slug>.md` + index row in
`.claude/docs/report/<plan-file-name>.md`) → `plan-commit` → `plan-push` → user
ticks `lead-review`.

## Request Template

Plan report for:
- Task ID:

## Claude Instructions

- Follow the skill exactly: gate on a CLEAN lead review → collect facts →
  per-repo changed-file list with mixed marks → write the task report file →
  update the index row → run `plan-commit`.
- Writes only the task report file and the index row. Do not tick any ledger line.
- One task ID per run.
