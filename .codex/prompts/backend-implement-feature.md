---
name: prompt-backend-implement-feature
description: Guide Codex to implement a backend feature in this Java Spring Boot project.
argument-hint: "<module> <feature description>"
---

# Prompt: Implement Feature

Use this prompt to guide Codex when implementing a backend feature.

## Request Template

Implement the backend feature in this repository.

Feature:
- Describe the business behavior.

Scope:
- Target module:
- Target API or service:
- Data model changes:
- Security requirements:
- Redis/Kafka/Docker impact:

Expected behavior:
- Success cases:
- Failure cases:
- Response contract:

Verification:
- Unit tests:
- Integration tests:
- Manual command:

## Codex Instructions

- Read `ticket-system/AGENTS.md` first.
- Keep changes backend-only.
- Follow existing Spring Boot and Maven patterns.
- Add focused tests for changed behavior.
- Summarize files changed and verification performed.
