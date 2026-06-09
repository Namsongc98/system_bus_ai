---
name: backend-implement-api
description: Use when adding or changing a Spring Boot REST API endpoint.
---

# Skill: Backend Implement API

Use this skill when adding or changing a backend REST endpoint.

## Workflow

1. Read `.codex/references/backend/rules/api.md`, `.codex/references/backend/rules/security.md`, and `.codex/references/backend/project-context.md`.
2. Locate the target module and existing controller/service/repository patterns.
3. Define or update request and response DTOs.
4. Add validation annotations and `@Valid`.
5. Implement controller method as a thin adapter.
6. Put business logic in a service method.
7. Use repository methods for persistence.
8. Add domain-specific exceptions for expected failures.
9. Add or update tests for status codes, validation, authorization, and service behavior.
10. Run the narrowest useful Maven test command.

## Done Criteria

- Endpoint path, method, request, response, and status codes are clear.
- Authentication and role checks are correct.
- No entity is exposed as the default response unless the module already intentionally does so.
- Validation failures produce consistent errors.
- Tests cover success and important failure paths.
