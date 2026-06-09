# Architecture Rules

## Module Responsibilities

`common-library` contains shared backend infrastructure:
- Security configuration.
- JWT filter and token utilities.
- Global exception handling.
- Redis and session configuration.
- Kafka configuration.
- Shared DTOs, enums, annotations, and utility code.

`booking_ticket` handles booking-facing workflows:
- Accept booking requests.
- Validate booking request shape and authentication.
- Publish booking/order events to Kafka.
- Call revenue service through Feign only where the existing design requires it.

`manage-revenue-ticket` owns operational data:
- Authentication and password changes.
- Users, profiles, routes, buses, trips, tickets, revenue, loyalty, salary, and audit logs.
- Booking event consumption.
- Revenue calculation and reports.
- Email confirmation and file handling where already implemented.

## Layering

Use this flow for request/response code:

```text
Controller -> Service -> Repository -> Database
```

Use this flow for async booking:

```text
booking_ticket Controller -> Producer -> Kafka topic -> manage-revenue-ticket Consumer -> Service -> Database
```

Controllers must not contain persistence rules, role calculations, or multi-step business flows.

## Transaction Boundaries

- Put `@Transactional` on service methods that write more than one entity or require atomic state transitions.
- Keep read-only methods as `@Transactional(readOnly = true)` when they depend on lazy relations or consistent snapshots.
- For concurrent booking, trip assignment, or bus status changes, use optimistic locking, pessimistic locking, or database constraints as appropriate.

## Cross-Service Contracts

- Keep Kafka event payloads stable and explicit.
- Version or extend DTOs carefully when consumers may depend on existing fields.
- Avoid synchronous service calls inside transactions unless necessary.
- External side effects such as email should not break the main transaction unless the business requires it.

