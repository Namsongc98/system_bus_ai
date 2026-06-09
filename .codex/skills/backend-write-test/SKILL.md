---
name: backend-write-test
description: Use when adding or improving backend tests for Spring Boot services, APIs, security, transactions, persistence, Redis, or Kafka, including Testcontainers integration tests.
---

# Skill: Backend Write Test

Use this skill when adding backend tests or improving coverage for a change.

## Workflow

1. Identify the behavior and risk being tested.
2. Choose the narrowest useful test type.
3. Use existing test libraries and module patterns.
4. Build test data with clear names and minimal fields.
5. Assert business results, status codes, database changes, emitted events, or exceptions.
6. Include negative cases for validation, authorization, and invalid state transitions.
7. Run the specific test class first, then the module test suite when feasible.

## Test Selection

- Use Mockito-based unit tests for isolated service decisions.
- Use controller or security slice tests for HTTP contracts and authorization.
- Use repository tests for JPQL and simple persistence behavior.
- Use Testcontainers with MySQL for native SQL, migrations, locking, and transaction semantics.
- Use Testcontainers with Kafka or Redis when serialization, retries, DLT, sessions, cache invalidation, or real client behavior is under test.

## Regression Minimums

- API: success, invalid input, unauthenticated, forbidden, not found/conflict.
- Security: role mapping, token failure, and authenticated-principal ownership.
- Transactions: rollback and duplicate/concurrent state changes.
- Kafka: payload mapping, duplicate delivery, retry/DLT, and consumer rollback.

## Useful Targets

- Auth login, register, password update.
- JWT parsing and authority mapping.
- Booking event creation.
- Ticket create, cancel, and status changes.
- Trip create/update and bus availability.
- Revenue report queries.
- Redis session/cache behavior.
- Kafka listener error behavior.
