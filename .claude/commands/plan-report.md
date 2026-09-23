---
description: Write the report section for one CLEAN screen-feature-plan task into .claude/docs/report/<plan-file-name>.md, then run plan-commit.
argument-hint: "<task ID from .claude/docs/plan/screen-feature-plan.md, e.g. 0.4, 1.1>"
allowed-tools: Read, Grep, Glob, Bash, Write, Edit, Skill
---

# Prompt: Plan Report

Use `.claude/skills/plan-report/SKILL.md`.

Flow: `/lead-review <ID>` (CLEAN) → `/plan-report <ID>` (runs automatically) →
`plan-commit` → `plan-push` → user ticks `lead-review`.

## Request Template

Plan report for:
- Task ID:

## Claude Instructions

- Follow the skill exactly: gate on a CLEAN lead review → collect facts →
  per-repo changed-file list with mixed marks → write the task section → run
  `plan-commit`.
- Writes only the report file. Do not tick any ledger line.
- One task ID per run.
