# Observability Rules

## Health And Actuator

- Expose only the Actuator endpoints required by operations.
- Keep detailed health information protected outside local development.
- Add health indicators for MySQL, Kafka, Redis, and required external services when their availability affects readiness.
- Separate liveness from readiness so dependency outages do not cause unnecessary process restarts.

## Logging

- Use SLF4J with structured, searchable fields.
- Carry a correlation id from HTTP requests into service logs and outbound calls.
- Include event id, topic, partition, and offset for Kafka processing.
- Log identifiers and state transitions, not full request bodies or sensitive data.
- Never log passwords, JWTs, session ids, authorization headers, mail credentials, or secret configuration.

## Metrics

- Use Micrometer metrics for request latency, error rates, Kafka processing, retry/DLT counts, and business-critical operations.
- Keep metric names and tags stable.
- Avoid unbounded tags such as email, user id, ticket id, raw URL, or exception message.
- Add alerts only for actionable symptoms with a documented owner or response.

## Error Reporting

- Preserve exceptions in error logs while returning safe client messages.
- Record enough context to trace a failure across HTTP, Kafka, Redis, and database boundaries.
- Do not use `System.out`, `printStackTrace`, or ad hoc logging formats.
