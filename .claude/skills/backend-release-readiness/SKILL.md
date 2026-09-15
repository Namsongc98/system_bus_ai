---
name: backend-release-readiness
description: Use when preparing or auditing a backend release for build health, regression tests, exposed secrets, production configuration, database migrations, Kafka compatibility, observability, and deployment risks.
---

# Backend Release Readiness

Run this as a read-first audit. Do not rotate credentials, apply production migrations, or deploy without explicit authorization.

1. Read the backend rules for security, testing, database, Kafka, Docker, and observability.
2. Review the release diff for secrets, unsafe defaults, API/event breaking changes, and missing migrations.
3. Run the narrow module tests, then `mvn clean install` when feasible.
4. Confirm production config externalizes secrets and disables schema mutation through Hibernate.
5. Validate migrations on an empty database and an upgrade fixture when available.
6. Check Kafka compatibility, consumer idempotency, retry/DLT behavior, and cross-module verification.
7. Check Actuator exposure, readiness dependencies, logging redaction, metrics, and correlation ids.
8. Report blockers first, then passed checks, skipped checks, commands run, and residual risk.

## Release Blockers

- A credential remains exposed or has not been rotated after exposure.
- Required tests fail or critical changed behavior lacks regression coverage.
- Production depends on `ddl-auto=update`.
- A breaking API or event change is unversioned or uncoordinated.
- A required migration cannot run safely.
