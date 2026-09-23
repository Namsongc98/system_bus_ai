# Kafka Rules

## Event Contracts

- Keep event payloads explicit DTOs; do not publish JPA entities.
- Treat topic names, keys, field names, enum values, and timestamp formats as cross-service contracts.
- Prefer additive, backward-compatible changes. Version the event or topic when a breaking change is unavoidable.
- Include a stable event identifier and the business aggregate identifier needed for deduplication and tracing.
- Never place passwords, tokens, or unnecessary personal data in events.

## Producer Behavior

- Use a stable message key when ordering per booking, ticket, trip, or user matters.
- Configure acknowledgements and idempotent producer behavior intentionally.
- Handle asynchronous send failures; do not treat `send()` invocation as confirmed delivery.
- Do not publish an event before a database transaction commits when consumers require committed state. Use an after-commit or outbox pattern for critical flows.

## Consumer Behavior

- Consumers must tolerate duplicate delivery. Enforce idempotency with an event-id record, unique constraint, or safe state transition.
- Validate payloads before changing state.
- Keep database writes transactional and acknowledge only after successful processing.
- Distinguish retryable infrastructure failures from non-retryable validation or business failures.
- Configure bounded retries with backoff and a dead-letter topic for messages that cannot be processed.
- Log topic, partition, offset, event id, and aggregate id, but not sensitive payload fields.

## Testing

- Unit test producer payload mapping and consumer business decisions.
- Integration test serialization, topic wiring, duplicate delivery, retry, dead-letter routing, and transaction rollback when those behaviors change.
- Use the project test profile or Testcontainers instead of depending on a developer's local Kafka cluster.
