# Workflow: Implement Endpoint

Use this workflow for new or changed REST APIs.

## Steps

1. Read `.claude/references/backend/rules/api.md` and `.claude/references/backend/rules/security.md`.
2. Locate the target module and existing controller conventions.
3. Define request/response DTOs.
4. Add validation.
5. Implement controller, service, repository changes.
6. Add exception mapping for expected failures.
7. Add authorization checks.
8. Add tests for success, validation, not found/conflict, and authorization.
9. Run the target module tests.
10. Document the endpoint behavior in the change summary if the user requested documentation.

## Checklist

- Path and HTTP method are correct.
- Response wrapper is consistent.
- Input validation is present.
- Business rules are in service layer.
- Database writes are transactional.
- Security behavior is explicit.
