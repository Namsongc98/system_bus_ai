---
name: plan-task
description: Use when executing one task (by ID such as 0.5, 1.1, 2.2) from .claude/docs/plan/screen-feature-plan.md — gated by dependencies and open decisions, BE contract then tests then FE wiring, verify, review, ledger update. Re-running it after /lead-review reported open FIX findings switches to fix mode (skill lead-review-fix).
argument-hint: "<task ID from .claude/docs/plan/screen-feature-plan.md, e.g. 0.3, 1.1, 2.2>"
allowed-tools: Read, Grep, Glob, Bash, Write, Edit
---

# Skill: Plan Task (execute one task of the screen feature plan)

Source of truth: `.claude/docs/plan/screen-feature-plan.md`.
Progress: `.claude/ledger/screen-feature-plan.md`.
Approved scope per task: `.claude/docs/review/<task-id>-<slug>.md` (written by
`/spec-review <ID>`, approved when the user ticks `spec`).

One run = one task ID. Never chain into the next task in the same run.

## Request Template

Plan task:
- Task ID:
- Scope limit (optional, e.g. "BE only", "FE only"):

## Task Registry

| ID | Scope | Design doc | Depends on | Skills | Open decision that blocks it |
|---|---|---|---|---|---|
| 0.1 | FE single base URL (`VITE_KONG_API_URL`) → Kong `:8000/api` | — | — | `frontend-integrate-api` | — |
| 0.2 | FE `API_ENDPOINTS` aligned to existing BE paths | — | 0.1 | `frontend-integrate-api` | — |
| 0.3 | Flyway + V1 baseline (`manage-revenue-ticket`) | — | — | `backend-database-change` | — |
| 0.4 | Lock public endpoints (B8) | — | — | `backend-implement-api` | — |
| 0.5 | Register always CUSTOMER (B11) + `@RoleRequired` (B12) | — | — | `backend-implement-api` | — |
| 0.6 | `GET /api/auth/me` | — | — | `backend-implement-api` | — |
| 0.7 | `PageResponse<T>` in `common-library` | — | — | `backend-implement-api` | — |
| 0.8 | Capacity check fix + unique `(trip_id, seat_number)` (B4) | — | 0.3 | `backend-database-change` | — |
| 1.1 | BusesRoutes | `admin-buses-routes.md`, `admin-create-bus-modal.md`, `admin-create-route-modal.md`, `admin-delete-confirmation.md` | 0.1, 0.2, 0.5, 0.7 | `backend-implement-api`, `frontend-api-pinia-store`, `frontend-wire-api-to-event` | — |
| 1.2 | UserManagement | `admin-user-management.md` | 0.1, 0.2, 0.5, 0.7 | `backend-implement-api`, `frontend-api-pinia-store` | bulk action (hide it, do not build) |
| 1.3 | TripsManagement | `admin-trips-management.md`, `admin-create-trip-modal.md`, `admin-schedule-trip-review.md` | 1.1, 1.2 | `backend-implement-api`, `frontend-api-pinia-store`, `frontend-wire-api-to-event` | — |
| 2.1 | TripView | `trip-search-results.md` | 1.3 | `backend-implement-api`, `frontend-api-pinia-store` | — |
| 2.2 | SeatView + booking flow (B3, B7) | `seat-selection-checkout.md` | 0.3, 0.6, 0.8, 2.1 | `backend-kafka-event`, `backend-database-change`, `backend-implement-api`, `frontend-api-pinia-store` | B5 (BOOKED rule) |
| 2.3 | QRConfirmPopup | `payment-booking-confirmation.md` | 2.2 | `backend-implement-api`, `backend-kafka-event` | payment method |
| 2.4 | MyTickets | `my-tickets.md` | 2.2 | `backend-implement-api`, `frontend-api-pinia-store` | cancellation window / refund |
| 3.1 | DashboardView | `admin-dashboard.md` | 0.1, 2.2 | `frontend-api-pinia-store` | — |
| 3.2 | RevenueReports | `admin-revenue-reports.md` | 0.4, 0.5 | `backend-refactor-service`, `frontend-integrate-download-api` | — |
| 4.1 | ProfileView | **none** → run `/clear-spec` first | 0.6 | — | — |
| 4.2 | TicketsAdmin | **none** → run `/clear-spec` first | 2.2 | — | — |
| 4.3 | Loyalty | — | 2.2 | `backend-implement-api` | loyalty rule |
| 4.4 | Salary | — | — | — | deferred: no screen exists |
| 4.5 | RegisterPage fields | `customer-register.md` | 0.5 | `backend-implement-api`, `backend-database-change` | — |
| 4.6 | ADMIN notification: cancelled seat re-booked (Firebase) | **none** → run `/clear-spec` first | 0.8, 2.2 | `backend-implement-api`, `backend-database-change`, `frontend-api-pinia-store` | Firebase project/credentials |

## Claude Instructions

Slash commands referenced below (`/spec-review`, `/clear-spec`, `/parallel-review`) live in
`.claude/commands/`. If a command is not available in the current surface
(e.g. Cowork loads skills but not commands), read that command file and follow
its instructions directly instead of stopping. `spec-review` also exists as a
skill (`.claude/skills/spec-review/SKILL.md`) for exactly that case.

### 1. Gate (stop early, before editing anything)
1. Look up the task ID in the registry. Unknown ID → list valid IDs and stop.
2. Read the ledger. If any **Depends on** task is not `implement` + `test` ticked,
   stop and name the missing dependency.
3. If the task has an **open decision**, and the work needs it, ask the user one
   question that covers every open point, then stop. Never invent the business
   rule. Partial work that does not depend on the decision may continue only if
   the user says so.
4. Task with no design doc (4.1, 4.2, 4.6) → stop and tell the user to run
   `/clear-spec` first.
5. **Spec gate.** If this task's `spec` line in the ledger is not ticked, or
   the spec-review doc `.claude/docs/review/<task-id>-<slug>.md` does not exist
   → stop and tell the user
   to run `/spec-review <ID>`, read the doc, and tick `spec`. Never tick `spec`
   yourself and never start without it.
6. **Fix mode.** If the spec-review doc has a `## 7. Lead review` section with
   at least one `FIX` row with status `open`, this run fixes those findings
   instead of the spec-review scope: follow `.claude/skills/lead-review-fix/SKILL.md`
   in place of steps 2–9 below, then stop. The loop is `/lead-review <ID>` →
   `/plan-task <ID>` → `/lead-review <ID>`, at most 3 rounds.
7. **Already done.** If `implement`, `test` and `review` are all ticked and
   there is no open `FIX` finding → stop: nothing to implement. Tell the user
   to run `/lead-review <ID>`.

### 2. Re-verify evidence
Scope = the "Fix scope" section (`S1`, `S2`, …) of the approved spec-review doc.
Do not add items outside it; a new gap found while working goes to step 8.
The plan and the spec-review doc cite files, lines and behaviour captured at a point in time.
- Re-read every file the plan cites for this task. If a cited problem is already
  fixed or the code moved, say so in the report and adjust scope. Do not
  re-implement something that already exists.
- Read `CLAUDE.md` (root, `ticket-system/`, `booking_ticket_vue/`) and the
  relevant `.claude/references/{backend,frontend}/` rules.

### 3. Backend first (contract before UI)
Implement in this order: migration → entity/repository → service → DTO →
controller. Rules for every BE change in this plan:
- Responses are DTOs, never entities. Lists return `PageResponse<T>` (task 0.7).
- Request DTOs carry `@Valid` constraints; violations go through the global
  handler in `common-library` with domain exceptions, not `RuntimeException`.
- Admin mutations and reports: `@RoleRequired(UserRole.ADMIN)`. Public access
  only via `@PublicApi` and only when the plan says so.
- Identity (`customerId`, `sellerId`) and price come from JWT / server data,
  never from the request body.
- Schema changes only via a new Flyway migration (`V<n>__<desc>.sql`), never via
  `ddl-auto=update`.
- Multi-entity writes: `@Transactional` on the service method.
- Kafka publish after commit (`@TransactionalEventListener(phase = AFTER_COMMIT)`
  or outbox) — never inside an open transaction that can still roll back.
- Consumers are idempotent (unique key + catch `DataIntegrityViolationException`).
- SLF4J with `bookingId` / `X-Request-ID` in MDC; remove `System.out.println` in
  every file you touch.
- In files you touch, convert `@Autowired` fields to constructor injection with
  `final`. Do not refactor untouched files.

### 4. Backend tests (same run, not later)
Minimum per task:
- Controller auth: no token → 401, wrong role → 403, correct role → 2xx.
- One test per business rule the task adds (validation, state transition,
  conflict).
- Task 2.2: Testcontainers integration test for MySQL + Kafka covering
  duplicate seat, duplicate message, and hold expired.

### 5. Frontend wiring
Order: `src/constants/api_endpoint.js` → `src/services/*` → `src/stores/*` →
page/component. Rules:
- Only point a constant at an endpoint that now exists in BE. Missing BE →
  keep it and mark `// BE: missing`. Never rename a constant to hide a gap.
- Pages call stores, stores call services. No axios in pages.
- Remove `*_FALLBACK_*` / `MOCK_*` usage for this screen once the real API path
  works. On API error show an error state, never fall back to mock data.
- Composition API `<script setup>` only.

### 6. Verify
Run and paste the result summary (pass/fail counts, not full logs):
```bash
mvn -f ticket-system/pom.xml -pl <module> -am test
cd booking_ticket_vue && npm run test:unit -- --run && npm run build
```
Always use the reactor form (`-pl <module> -am`) for backend modules: it builds
`common-library` from source. `mvn -f ticket-system/<module>/pom.xml test`
resolves `common-library` from the jar installed in `~/.m2`, which can be older
than the working tree and silently hide (or fake) a `common-library` change.
If the task changed `common-library` and the service will be run with
`spring-boot:run`, also run `mvn -f ticket-system/pom.xml install -DskipTests`
so the installed jar matches the source.
If infra (MySQL/Kafka/Redis) is not running, say which checks were skipped.
Do not claim a check passed that was not run.

### 7. Review
- Small task (0.x, 3.1): `backend-code-review` or `frontend-code-review`.
- Screen tasks (1.x, 2.x, 3.2, 4.x): `/parallel-review`.
Fix findings of severity high/medium before reporting.

### 8. Update tracking
- Ledger: tick `implement`, `test`, `review` for this task ID when each is true.
  Never tick `spec` or `lead-review` — user only.
- New gap found while working → append it to the plan (blocker table as
  `B<next>` or section 3 open questions). Do not silently widen the task scope.

### 9. Report (in this order)
1. Fix-scope items done / not done (`S1`, `S2`, …) and files changed (BE, FE, migration).
2. Endpoints added/changed: method, path, auth, request, response.
3. Tests added and verification results.
4. Review findings and how they were handled.
5. Remaining `(TODO/needs confirmation)` and new plan entries.
6. Next step for this task: `/lead-review <ID>`; then the next unblocked task
   ID(s) from the registry.

## Boundaries
- One task ID per run. Stop after the report.
- Do not edit `Infrastructure/` unless the task explicitly requires it.
- Do not read or write `.env` files.
- Do not delete FE fallback constants files — only stop using them.
- Do not tick `spec` or `lead-review`.
