# Testing Rules

## Test Priority

Prioritize tests for:
- Authentication and authorization.
- JWT role extraction and `ROLE_` authority mapping.
- Booking and ticket status transitions.
- Transaction rollback for multi-entity writes.
- Concurrent bus, trip, and seat assignment behavior.
- Kafka producer and consumer behavior.
- Repository queries used by reports.
- Redis cache/session behavior when code changes touch it.

## Test Types

- Unit tests for services, validators, mappers, and utility classes.
- Slice tests for controllers when API behavior changes.
- Repository tests for custom queries.
- Integration tests for transaction behavior and cross-layer flows.
- Security tests for public versus protected endpoints and role restrictions.
- Testcontainers integration tests for behavior that depends on real MySQL, Kafka, or Redis semantics.

## Required Regression Coverage

- API changes: success, validation, authentication, authorization, not found, conflict, and response contract.
- Security changes: public/protected behavior, role mapping, invalid/expired token behavior, and principal ownership checks.
- Transaction changes: commit, rollback, duplicate/concurrent update behavior, and external side-effect boundaries.
- Kafka changes: serialization, producer failure, consumer success, duplicate delivery, retries, dead-letter routing, and rollback.

## Testcontainers

- Reuse container definitions across tests when doing so does not leak state.
- Pin compatible image versions and use dynamic properties rather than hardcoded host ports.
- Reset business data between tests; do not depend on execution order.
- Use MySQL rather than H2 for native SQL, locking, enum, index, or transaction behavior.
- Use Kafka and Redis containers only for tests that require their real protocol or lifecycle behavior; mock narrow collaborators in unit tests.

## Maven Commands

Run all tests:

```bash
mvn test
```

Run tests for one module:

```bash
mvn -f manage-revenue-ticket/pom.xml test
mvn -f booking_ticket/pom.xml test
```

Run one test class:

```bash
mvn -f manage-revenue-ticket/pom.xml -Dtest=ClassNameTest test
```

## Test Quality

- Tests should assert behavior, not implementation details.
- Use meaningful names that describe the business case.
- Cover both success and failure paths.
- When a test requires infrastructure, state that clearly or use a containerized/test profile if available.
- Do not weaken assertions just to make tests pass.
