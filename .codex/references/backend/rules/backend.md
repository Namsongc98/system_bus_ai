# Backend Rules

## Core Stack

Use Java 21, Spring Boot 3.3.6, Maven, Spring Web, Spring Security, Spring Data JPA, Spring Data Redis, Spring Session, Spring Kafka, OpenFeign, MySQL, Docker, and Redis Cluster according to the existing module setup.

## Backend Boundaries

Allowed task areas:
- REST APIs, controllers, DTOs, validation, and response contracts.
- Service-layer business rules.
- JPA entities, repositories, queries, transactions, and schema-related changes.
- Authentication, authorization, JWT, sessions, and security filters.
- Redis cache/session behavior.
- Kafka producer/consumer behavior.
- Docker Compose infrastructure for local backend services.
- Logging, exception handling, testing, and troubleshooting.

## Coding Defaults

- Use constructor injection and `final` dependencies.
- Keep controllers thin; place business rules in services.
- Use DTOs for request and response bodies. Do not expose entities as a default API contract.
- Validate inputs with Jakarta Validation and `@Valid`.
- Use domain-specific exceptions for expected business failures.
- Centralize exception mapping in `@RestControllerAdvice`.
- Use SLF4J logging. Do not use `System.out.println` or `printStackTrace`.
- Use `@Transactional` at service methods that perform multi-step writes.
- Keep secrets in environment variables or externalized configuration for production-quality changes.

## Maven Rules

- Treat root `pom.xml` as an aggregator.
- Run application services through their module POMs.
- For shared library changes, verify both service modules when feasible.
- Avoid introducing dependencies unless they solve a real backend problem and fit the current stack.
