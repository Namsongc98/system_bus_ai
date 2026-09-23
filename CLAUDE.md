# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

**System Bus** is a Vietnamese bus ticket management system built as a microservices monorepo with:
- **Frontend:** `booking_ticket_vue/` — Vue 3 SPA
- **Backend:** `ticket-system/` — Java Spring Boot microservices
- **Infrastructure:** `ticket-system/Infrastructure/` — Docker-managed MySQL, Kafka, Redis

---

## Frontend Commands (`booking_ticket_vue/`)

```bash
npm install          # Install dependencies (Node ^20.19.0 or >=22.12.0)
npm run dev          # Dev server at http://localhost:5173
npm run build        # Production build
npm run preview      # Serve build at http://localhost:4173

npm run test:unit    # Vitest unit tests
npm run test:e2e     # Playwright E2E tests (requires running dev server)
npm run format       # Prettier formatter (src/ only)
```

---

## Backend Commands (`ticket-system/`)

```bash
# Build all modules
mvn clean install

# Skip tests (when infra is unavailable)
mvn clean install -DskipTests

# Run individual services
mvn -f booking_ticket/pom.xml spring-boot:run          # Port 8081
mvn -f manage-revenue-ticket/pom.xml spring-boot:run   # Port 8082

# Run tests for a specific module
mvn -f manage-revenue-ticket/pom.xml test

# Run a specific test class
mvn -f manage-revenue-ticket/pom.xml -Dtest=ClassName test
```

---

## Infrastructure Setup (Docker — first-time only)

```bash
# Create networks
docker network create ticket-system-network
docker network create redis-cluster-net --subnet=173.20.0.0/16

# Start in order
cd ticket-system/Infrastructure/mysql && docker-compose up -d && cd ../../..
cd ticket-system/Infrastructure/kafka && docker-compose up -d && cd ../../..
cd ticket-system/Infrastructure/redis-cluster && docker-compose up -d

# Initialize Redis cluster (one-time)
docker exec -it redis-1 redis-cli --cluster create \
  173.20.0.11:7001 173.20.0.12:7002 173.20.0.13:7003 \
  173.20.0.14:7004 173.20.0.15:7005 173.20.0.16:7006 \
  --cluster-replicas 1

# Verify services
curl http://localhost:8081/actuator/health
curl http://localhost:8082/actuator/health
```

---

## Architecture

### Service Topology

```
Vue SPA (5173)
  └── apiClient (VITE_KONG_API_URL = http://localhost:8000/api)
        ↓
      Kong gateway (8000)
        ├── /api/booking → Booking Service (8081)          → Kafka producer
        └── /api/*       → Manage Revenue Service (8082)  ← Kafka consumer
                                                              ↓
                                                      Kafka (order-events)
                                                              ↓
                                                      Manage Revenue Service
                                                              ↓
                                                      MySQL / Redis Cluster
```

### Module Responsibilities

| Module | Port | Role |
|--------|------|------|
| `common-library` | — | Shared: JWT, Spring Security, Redis/Kafka config, global exception handler, shared DTOs/enums |
| `booking_ticket` | 8081 | Accepts booking requests, publishes `BookingEvent` to Kafka `order-events` topic |
| `manage-revenue-ticket` | 8082 | Source of truth: auth, users, routes, buses, trips, tickets, revenue, salary, loyalty; consumes Kafka events |
| `booking_ticket_vue` | 5173 | SPA with role-based pages (`/pages/auth`, `/pages/user`, `/pages/admin`) |

### Frontend Architecture

- **Stores (`src/stores/`):** Pinia — `auth`, `booking`, `admin`, `trip`, `user`, `seat`
- **Services (`src/services/`):** Axios wrappers per domain; `axios.js` defines the single `apiClient` (base URL `VITE_KONG_API_URL`, through Kong) with JWT interceptors
- **Pages (`src/pages/`):** Role-grouped: `auth/`, `user/`, `admin/`
- **Components (`src/components/`):** `elements/` (primitives), `common/` (widgets), `layout/` (shell)

### Backend Layer Pattern

```
Controller (thin: validate + delegate)
  → Service (@Transactional, business logic)
    → Repository (Spring Data JPA + custom queries)
      → MySQL
```

- Request DTOs use `@Valid`; response DTOs are separate from entities
- `common-library` provides `@RestControllerAdvice` global exception handler — use domain-specific exceptions, not raw `RuntimeException`
- Controllers in `booking_ticket` call Revenue Service synchronously via OpenFeign when needed in addition to Kafka events

### User Roles

`ADMIN`, `DRIVER`, `COLLECTOR`, `CUSTOMER`

### Key Statuses

- **Trip:** `SCHEDULED → ONGOING → COMPLETED | CANCELLED`
- **Ticket:** `NOT_BOOKED → BOOKED → PAID | CANCELLED`
- **Bus:** `AVAILABLE`, `IN_USE`, `MAINTENANCE`

---

## Configuration

Secrets go in `.env` (git-ignored), never hardcoded. Services read:
- `JWT_SECRET`, `DB_PASSWORD`, `MAIL_PASSWORD`, `MINIO_*` from environment variables

Local defaults:
- MySQL: `localhost:3306`, DB `quan-ly-ban-hang`
- Kafka brokers: `localhost:9092,9093,9094`, topic `order-events`
- Redis cluster: `localhost:7001–7006`
- JWT expiry: 86400000 ms (1 day), session timeout: 30 min

---

## Key Guidelines from `.claude/references/`

**Backend:**
- Use constructor injection with `final` fields
- Use SLF4J for logging, never `System.out`
- Paginate large list/report endpoints
- Use `@Transactional` for multi-entity writes
- Do not use `ddl-auto=update` in production — use Flyway/Liquibase for migrations
- Consider optimistic/pessimistic locking for concurrent ticket/seat booking

**Frontend:**
- Use Vue 3 Composition API (`<script setup>`) — no Options API, no Vuex
- API calls go through `src/services/`; stores call services, not axios directly
- All API endpoints defined in `src/constants/`

---

## Working Rules

Moved here from the former root `AGENTS.md`. Subproject rules live in
`ticket-system/CLAUDE.md` (backend) and `booking_ticket_vue/CLAUDE.md` (frontend);
read the matching one before changing code in that subproject.

- Preserve user changes already present in the workspace.
- Keep changes scoped to the requested frontend, backend, or `.claude/` area.
- Do not commit secrets, tokens, credentials, local environment files, or runtime data.
- Never read `.env` or `.env.*` files, print the process environment, expand secret
  environment variables in commands, or ask the user to paste secret values.
  Use `.claude/references/backend/environment-variable-names.md` (names only) when
  checking required configuration; developers start secret-dependent services from
  a separate terminal.
- Prefer existing project patterns over new abstractions.
- Do not delete, move, or rewrite documentation outside the requested scope.
- Report verification commands run and any checks that could not be run.
- Git worktrees: only through the `git-worktree` skill (preview → explicit approval
  of the token → create/cleanup). No raw `git worktree add/remove`, no force removal,
  no direct branch deletion.
- `.claude/` layout and the end-to-end workflow: `.claude/VIBE_CODE_INSTRUCTIONS.md`.

---

## Documentation

Detailed docs live in `ticket-system/.github/`:
- `PROJECT_INSTRUCTIONS.md` — Full architecture, DB schema, configuration reference
- `API_DOCUMENTATION.md` — REST API reference
- `QUICK_START.md` — Minimal setup guide
