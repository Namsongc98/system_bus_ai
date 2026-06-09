---
name: prompt-backend-explain-code
description: Guide Codex to explain backend code behavior, responsibilities, and risks.
argument-hint: "<file, class, method, or backend flow>"
---

# Prompt: Explain Code

Use this prompt when explaining backend code.

## Request Template

Explain this backend code.

Target:
- File/class/method:
- What I want to understand:
- Desired depth:

## Codex Instructions

- Explain the code in terms of backend responsibilities and runtime behavior.
- Mention request flow, transaction boundaries, security checks, database access, Redis, or Kafka only when relevant.
- Include file references.
- Call out risks or surprising behavior if found.
- Keep the explanation practical and tied to the repository.
