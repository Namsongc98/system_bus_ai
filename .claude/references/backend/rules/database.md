# Database Rules

## Database Context

The local relational database is MySQL. The primary schema is `quan-ly-ban-hang`.

Important entities include:
- `User`, `Profile`
- `Route`, `Buses`, `Trip`
- `Ticket`, `Revenue`
- `LoyaltyPoint`, `LoyaltyReward`, `BaseLoyaltyPoints`
- `BaseSalary`, `Salary`
- `AuditLog`

## JPA Entity Rules

- Keep entity relationships explicit and aligned with the domain.
- Avoid exposing entities directly from controllers.
- Use enum mappings consistently.
- Be careful with lazy-loading in response serialization; map entities to DTOs inside service or mapper code.
- Ensure `createdAt` and `updatedAt` behavior is consistent with existing audit patterns.

## Repositories

- Use `JpaRepository` for standard CRUD.
- Use `Pageable` for list endpoints.
- Use projections for report queries when full entities are unnecessary.
- Use parameterized JPQL or native SQL only; never concatenate user input into queries.

## Transactions And Consistency

- Multi-entity writes must be inside a service transaction.
- Ticket booking, trip status updates, bus assignment, loyalty point updates, and revenue writes need rollback behavior.
- For concurrent writes to seats, buses, trips, or ticket status, use locking or constraints.
- Prefer idempotent handling for Kafka consumer writes where duplicate events are possible.

## Schema Migrations

- Use Flyway or Liquibase for repeatable schema evolution; follow the migration tool already adopted by the project.
- Do not use `spring.jpa.hibernate.ddl-auto=update` as the production schema-management strategy.
- Production and release verification should use `validate` or an equivalent non-mutating Hibernate mode after migrations run.
- Keep migrations immutable after they have been applied to a shared environment. Add a new migration for corrections.
- `manage-revenue-ticket` uses Flyway: files live in `src/main/resources/db/migration/` and are named `V<n>__<description>.sql` (integer version, two underscores). Never edit an applied file; every schema change is a new file.
- Only `manage-revenue-ticket` runs migrations. `booking_ticket` shares the database and only runs Hibernate `validate`, so start `manage-revenue-ticket` first.
- `manage-revenue-ticket/application.properties` sets `baseline-on-migrate=true`, `baseline-version=1` and `clean-disabled=true` for every environment (0.3, decision 1 = A). A database built by the old `ddl-auto=update` (tables, no `flyway_schema_history`) is marked V1 with its rows kept, then only V2+ run; an empty database gets V1 like a new install. Baseline accepts any non-empty schema, so check that `DB_URL` names `quan-ly-ban-hang` (single-DB project, 0.3 L7 = a). Never drop or recreate a database that holds data to "fix" Flyway; back it up (`mysqldump --single-transaction`) before migrating real data.
- Include constraints, indexes, defaults, and data backfills required by the application change.
- Plan backward-compatible expand/migrate/contract steps when old and new application versions may overlap.

## Performance

- Watch for N+1 queries on report and listing endpoints.
- Use fetch joins, entity graphs, projections, or explicit query methods when needed.
- Add indexes for frequently filtered fields such as email, status, route, trip, bus, customer, seller, and date ranges.
- Do not use `findAll()` for large operational tables unless pagination or filtering is applied.
