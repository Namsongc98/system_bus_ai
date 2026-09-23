---
description: Spec gate for one screen-feature-plan task — re-check the coded screen against design doc + real BE, write the agreed fix scope, then ask the user to tick `spec`.
argument-hint: "<task ID from .claude/docs/plan/screen-feature-plan.md, e.g. 1.1, 2.2>"
allowed-tools: Read, Grep, Glob, Bash, Write
---

# Prompt: Spec Review (the step before the user ticks `spec`)

Use `.claude/skills/spec-review/SKILL.md`.

Flow: `/spec-review <ID>` → user reads the doc → user ticks `spec` in
`.claude/ledger/screen-feature-plan.md` → `/plan-task <ID>`.

## Request Template

Spec review for:
- Task ID:
- Known broken behaviour (optional, e.g. "list shows mock data", "save returns 404"):

## Claude Instructions

- Follow the skill's Claude Instructions exactly (locate task → review →
  feature check → diff against plan → write `.claude/docs/review/<task-id>-<slug>.md`
  → stop and hand over).
- Read-only for code: the only file written is the review doc.
- Do not tick `spec` (or any ledger line) — the user does.
- One task ID per run.
