---
name: backend-refactor-service
description: Use when refactoring Spring service-layer code while preserving existing backend behavior.
---

# Skill: Backend Refactor Service

Use this skill when improving service-layer code without changing intended behavior.

## Workflow

1. Read the target service and nearby tests.
2. Identify current responsibilities and transaction boundaries.
3. Extract repeated validation into private methods or dedicated validators.
4. Replace field injection with constructor injection if touching that class.
5. Replace generic expected exceptions with domain exceptions.
6. Keep public method signatures stable unless the API task requires changes.
7. Preserve behavior and response contracts.
8. Add regression tests around the behavior being refactored.
9. Run module tests.

## Guardrails

- Do not combine unrelated refactors.
- Do not change persistence semantics accidentally.
- Do not move side effects such as Kafka publishing or email sending across transaction boundaries without a clear reason.
- Keep refactors small enough to review.
