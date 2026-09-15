---
name: backend-kafka-event
description: Use when adding, changing, reviewing, or debugging Spring Kafka producers, consumers, event DTOs, retries, dead-letter topics, idempotency, or event-driven transaction behavior.
---

# Backend Kafka Event

1. Read the Kafka, architecture, database, security, and testing backend rules.
2. Trace the producer, topic, serializer, consumer group, listener, service, and database write.
3. Define the event contract, stable key, event id, compatibility impact, and sensitive-data boundary.
4. Make producer delivery handling explicit and keep critical publication aligned with transaction commit.
5. Make consumers transactional and idempotent.
6. Classify failures as retryable or non-retryable; use bounded backoff and a dead-letter topic.
7. Add focused unit tests plus Kafka integration tests when wiring, serialization, retry, or DLT behavior changes.
8. Verify both producing and consuming modules when the shared contract changes.

## Done Criteria

- Duplicate delivery cannot repeat the business effect.
- Breaking contract changes are versioned or coordinated.
- Failed messages are observable and recoverable.
- Logs identify events without exposing sensitive payloads.
- Success, duplicate, retry, DLT, and rollback behavior is covered where applicable.
