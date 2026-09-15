---
name: backend-database-change
description: Use when changing JPA entities, repositories, native queries, transactions, locking, indexes, relational schema, Flyway or Liquibase migrations, or database-backed consistency behavior.
---

# Backend Database Change

1. Read the database, architecture, testing, and clean-code backend rules.
2. Identify affected entities, relationships, queries, DTOs, services, APIs, and Kafka consumers.
3. Define transaction and concurrency behavior before editing.
4. Add a Flyway or Liquibase migration using the tool already present; never introduce both.
5. Include constraints, indexes, defaults, and safe data backfills required by the code.
6. Keep repository queries parameterized and prevent unbounded reads or N+1 regressions.
7. Add MySQL-backed Testcontainers tests for migrations, native SQL, locking, or transaction semantics.
8. Verify a clean database migration, an upgrade path when fixtures exist, and the target module tests.

## Done Criteria

- Schema and entity mappings agree under Hibernate validation.
- Multi-step writes roll back atomically.
- Concurrent or duplicate operations have a defined database guarantee.
- Migration ordering and rollback/forward-fix strategy are documented.
- Query and migration behavior has focused regression coverage.
