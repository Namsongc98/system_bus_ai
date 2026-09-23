# Workflow: Investigate Issue

Use this workflow for backend failures, including startup, API, database, Redis, Kafka, and Docker issues.

## Steps

1. Capture the exact failure: command, endpoint, request body, response, logs, or stack trace.
2. Identify the affected module: `common-library`, `booking_ticket`, `manage-revenue-ticket`, or `Infrastructure`.
3. Reproduce with the narrowest command.
4. For Maven application startup, rerun with `-e`.
5. Verify infrastructure state with Docker if the failure involves MySQL, Kafka, or Redis.
6. Trace from entry point to failing layer.
7. Fix only the root cause.
8. Add a regression test when practical.
9. Re-run the command that reproduced the issue.

## Useful Commands

```bash
mvn -f booking_ticket/pom.xml spring-boot:run -e
mvn -f manage-revenue-ticket/pom.xml spring-boot:run -e
mvn -f manage-revenue-ticket/pom.xml test
docker ps
```

