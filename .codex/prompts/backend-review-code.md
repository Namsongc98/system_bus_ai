---
name: prompt-backend-review-code
description: Guide Codex to review backend changes for correctness, security, data safety, and tests.
argument-hint: "<branch, commit, PR, diff, or file path>"
---

# Prompt: Review Code

Use this prompt for backend code review.

## Request Template

Review this backend change.

Scope:
- Branch, PR, commit, file, or diff:
- Areas of concern:
- Required behavior:

Review focus:
- Security:
- Transactions:
- API contract:
- Database queries:
- Redis/Kafka behavior:
- Tests:

## Codex Instructions

- Use `.codex/skills/backend-code-review/SKILL.md`.
- Lead with findings, ordered by severity.
- Include precise file and line references.
- Do not spend space on praise.
- If no issues are found, say so and list residual test gaps or risks.
