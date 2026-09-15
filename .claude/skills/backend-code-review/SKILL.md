---
name: backend-code-review
description: Use when reviewing backend changes for bugs, regressions, security, data consistency, and missing tests.
---

# Skill: Backend Code Review

Use this skill for backend review, refactor planning, or quality fixes.

## Review Priorities

1. Security vulnerabilities.
2. Data consistency and transaction safety.
3. Authorization and role handling.
4. API contract regressions.
5. Query performance and unbounded reads.
6. Exception handling and logging.
7. Test coverage for changed behavior.
8. Maintainability and duplication.

## Specific Checks

- No hardcoded ADMIN authority.
- No hardcoded secrets in production-quality configuration.
- `PasswordEncoder` is injected as a bean.
- Multi-step writes use `@Transactional`.
- Concurrent state changes use locking or constraints where needed.
- Expected business failures use custom exceptions.
- Controllers remain thin.
- DTO validation is present.
- Logs are structured and do not expose secrets.
- Repository queries are parameterized.
- List endpoints are paginated.

## Output Format

Lead with findings ordered by severity. Include file and line references when available. Then list open questions, test gaps, and a short summary.
