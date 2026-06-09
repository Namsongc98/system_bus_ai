# Workflow: Database Change

Use this workflow for entity, repository, query, schema, or data consistency changes.

## Steps

1. Read `.codex/references/backend/rules/database.md`.
2. Identify affected entities, repositories, DTOs, services, and APIs.
3. Check relationships and cascade behavior before editing.
4. Choose Flyway or Liquibase according to the existing project setup; do not introduce both.
5. Add an immutable migration for schema, constraints, indexes, and required data backfills.
6. Add or update repository methods with parameterized queries.
7. Add transaction boundaries and locking in services where consistency requires them.
8. Add repository or Testcontainers integration tests for migrations, custom queries, and write behavior.
9. Run migrations against an empty database and an upgrade fixture when feasible.
10. Verify the target module with Hibernate schema validation.

## Risk Checks

- Lazy loading outside transaction.
- N+1 query behavior.
- Unbounded `findAll()`.
- Missing rollback for multi-entity writes.
- Duplicate event processing.
- Concurrent update conflicts.
