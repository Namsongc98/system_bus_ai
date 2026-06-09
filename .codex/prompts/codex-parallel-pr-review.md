---
name: prompt-codex-parallel-pr-review
description: Run a parallel read-only review using backend, frontend, security, and test-gap subagents.
argument-hint: "<branch, diff, PR, or changed files>"
---

# Prompt: Parallel PR Review

Use this prompt for broad reviews where parallel read-only subagents reduce
context noise.

## Request Template

Review this change with parallel subagents.

Target:
- Branch, PR, diff, or changed files:
- Required behavior:
- Areas of concern:

Agents:
- `backend-reviewer`
- `frontend-reviewer`
- `security-reviewer`
- `test-gap-reviewer`

## Codex Instructions

- Spawn only the agents relevant to the changed files.
- Keep all subagents read-only.
- Wait for all requested agents.
- Summarize findings by category: backend, frontend, security, tests.
- Include file/line references where available.
- Do not include raw logs unless they are necessary evidence.
