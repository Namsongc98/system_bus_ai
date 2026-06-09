---
name: prompt-codex-review-hooks-roadmap
description: Review the project Codex hook design, policy risk, trust model, and verification plan.
argument-hint: "<hook area, risk concern, or proposed hook change>"
---

# Prompt: Review Codex Hooks Roadmap

Use this prompt to review hooks before adopting or tightening enforcement.

## Request Template

Review the Codex hook design for this repository.

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

## Codex Instructions

- Read `AGENTS.md`.
- Read `.codex/hooks.json` and the scripts under `.codex/hooks/`.
- Verify that hooks are fast, scoped, and do not edit files.
- Treat destructive command blocking as the only hard-fail behavior in v1.
- Lead with findings and file/line references.
- Include dry-run commands that prove the hook behavior.
