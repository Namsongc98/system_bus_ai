---
description: Review the project Claude hook design, policy risk, trust model, and verification plan.
argument-hint: "<hook area, risk concern, or proposed hook change>"
allowed-tools: Read, Grep, Glob
---

# Prompt: Review Claude Hooks Roadmap

Use this prompt to review hooks before adopting or tightening enforcement.

## Request Template

Review the Claude hook design for this repository.

Scope:
- Hook event:
- Script or policy:
- Desired behavior:
- Risk concern:

Review focus:
- Destructive command blocking:
- Secret scanning:
- Permission request quality:
- Failure reporting:
- Stop/verification reminders:
- Trust and timeout behavior:

## Claude Instructions

- Read `AGENTS.md`.
- Read `.claude/settings.json` and the scripts under `.claude/hooks/`.
- Verify that hooks are fast, scoped, and do not edit files.
- Treat destructive command blocking as the only hard-fail behavior in v1.
- Lead with findings and file/line references.
- Include dry-run commands that prove the hook behavior.
