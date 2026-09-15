---
name: backend-debug
description: Use when diagnosing backend build, startup, API, database, Redis, Kafka, or Docker issues.
---

# Skill: Backend Debug

Use this skill when diagnosing build, startup, API, database, Redis, Kafka, or Docker issues.

## Workflow

1. Reproduce the issue with the narrowest command.
2. If Maven startup fails, rerun with `-e`.
3. Read the Spring Boot stack trace above Maven's final plugin failure.
4. Check whether the root aggregator was run by mistake.
5. Verify required infrastructure: MySQL, Kafka, Redis Cluster, ports, and environment variables.
6. Inspect relevant application properties and active profiles.
7. Trace the failing path through controller, service, repository, config, or listener code.
8. Fix the root cause and avoid broad rewrites.
9. Verify with the same command that reproduced the issue.

## Common Commands

```bash
mvn -f booking_ticket/pom.xml spring-boot:run -e
mvn -f manage-revenue-ticket/pom.xml spring-boot:run -e
docker ps
docker logs <container>
```

## Common Causes

- Running `spring-boot:run` from the root aggregator.
- MySQL database missing or unavailable.
- Redis Cluster not initialized.
- Kafka brokers unavailable.
- Port `8081` or `8082` already in use.
- Hardcoded local credentials missing in the runtime environment.
- Bean creation failure due to missing configuration or circular dependency.
