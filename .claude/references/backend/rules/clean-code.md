# Clean Code Rules

## Services

- Services should express business actions clearly and orchestrate repositories, validators, events, and external clients.
- Extract repeated validation into private methods or dedicated validators when it is reused across service methods.
- Avoid mixing unrelated responsibilities such as ticket creation, loyalty calculation, email sending, and revenue aggregation in a single large method.
- Prefer clear method names over comments that restate code.

## Dependency Injection

- Use constructor injection, preferably with Lombok `@RequiredArgsConstructor` if that is already used in the module.
- Dependencies should be `private final`.
- Do not use field injection for new code.
- Shared beans such as `PasswordEncoder`, `ObjectMapper`, `RestTemplate`-like clients, Kafka templates, and Redis templates should be configured as Spring beans.

## Exceptions

- Do not throw generic `RuntimeException` for expected business errors.
- Create meaningful exceptions such as `UserNotFoundException`, `InvalidPasswordException`, `TripOngoingException`, `BusAlreadyInUseException`, or reuse existing project exceptions.
- Preserve the original exception as the cause when wrapping unexpected infrastructure failures.
- Map exceptions to consistent HTTP responses in a global handler.

## Logging

- Use `@Slf4j` or an existing logger pattern.
- Log business milestones at `info` only when useful.
- Log technical details and identifiers at `debug`.
- Log recoverable external failures at `warn`.
- Log unexpected failures at `error` with the exception object.
- Never log passwords, JWT tokens, refresh tokens, SMTP credentials, or full secret values.

## Data Access

- Repositories should contain data access, not business decisions.
- Prefer Spring Data method names or JPQL when possible.
- Native SQL is acceptable for reporting or performance-sensitive queries, but it must be parameterized.
- Avoid loading all rows for pageable or report endpoints. Use `Pageable`, projections, aggregation queries, or streaming patterns where appropriate.
