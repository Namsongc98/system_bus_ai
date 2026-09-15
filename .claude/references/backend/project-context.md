# Project Context

## Overview

Ticket System is a backend bus ticket management project using Spring Boot microservice-style modules.

Core capabilities:
- Bus ticket booking.
- User, profile, route, bus, trip, ticket, revenue, loyalty, salary, and audit management.
- JWT authentication and role-based authorization.
- Redis Cluster for sessions and caching.
- Kafka for booking/order events.
- MySQL as the primary relational database.

## Maven Structure

```text
ticket-system
├── common-library
├── booking_ticket
├── manage-revenue-ticket
└── Infrastructure
```

The root Maven project is an aggregator. Run services through module POMs.

## Modules

### common-library

Shared backend code:
- Spring Security configuration.
- JWT auth filter and token utilities.
- Global exception handling.
- Custom auth entry point and access denied handler.
- Redis, session, Kafka producer, and Kafka consumer configuration.
- Shared annotations such as public API and role requirements.
- Shared enums such as user role and status values.

### booking_ticket

Booking service:
- Port: `8081`.
- Main responsibility: accept booking requests and publish booking/order events.
- Main API area: `/api/booking`.
- Uses Kafka topic `order-events`.
- May use Feign clients to communicate with management/revenue service where existing code does so.

### manage-revenue-ticket

Management and revenue service:
- Port: `8082`.
- Owns authentication, user management, routes, buses, trips, tickets, revenue reports, loyalty, salaries, audit logs, email, and file handling.
- Consumes booking/order events.
- Stores and updates the main operational data.

## Important Domain Concepts

Roles:
- `ADMIN`
- `DRIVER`
- `COLLECTOR`
- `CUSTOMER`

Common statuses:
- Customer: `ACTIVE`, `INACTIVE`, `BLOCKED`
- Bus: `AVAILABLE`, `IN_USE`, `MAINTENANCE`
- Route: `ACTIVE`, `INACTIVE`
- Trip: `SCHEDULED`, `ONGOING`, `COMPLETED`, `CANCELLED`
- Ticket: `NOT_BOOKED`, `BOOKED`, `PAID`, `CANCELLED`
- Loyalty transaction: `EARN`, `REDEEM`, `EXPIRE`

Important relationships:
- User has many tickets as customer.
- User has many tickets as seller.
- User has many trips as driver.
- Route has many trips.
- Bus has many trips.
- Trip has many tickets and revenue records.
- User has many loyalty points and salary records.

## Local Infrastructure

Local defaults:
- MySQL: `localhost:3306`
- Database: `quan-ly-ban-hang`
- MySQL user: `root`
- Kafka brokers: `localhost:9092`, `localhost:9093`, `localhost:9094`
- Redis Cluster: `localhost:7001` to `localhost:7006`
- Booking service: `localhost:8081`
- Manage revenue service: `localhost:8082`

Use environment variables for production-quality secrets.

### Infrastructure Layout

Infrastructure files live under `Infrastructure/`:

```text
Infrastructure
├── mysql
│   └── docker-compose.yml
├── kafka
│   └── docker-compose.yml
└── redis-cluster
    ├── Dockerfile
    ├── docker-compose.yml
    ├── redis-cluster.tmpl
    └── setup-cluster.sh
```

### MySQL

The MySQL compose stack runs `mysql:8.0` as container `mysql-ticket-system`.

Local configuration:
- Host port: `3306`
- Database: `quan-ly-ban-hang`
- Root password in local compose: `123456789`
- Docker network: external `ticket-system-network`

Both Spring Boot services use MySQL as their main persistence layer through Spring Data JPA. Authentication, users, routes, buses, trips, tickets, revenue, loyalty, salary, and audit data are stored in this relational database.

### Kafka

The Kafka compose stack runs three Confluent Kafka 7.5.0 brokers:
- `broker1`: host port `9092`
- `broker2`: host port `9093`
- `broker3`: host port `9094`

Kafka runs in KRaft mode with controller quorum across the three brokers. Internal broker traffic uses container hostnames on the `kafka-net` bridge network. Spring Boot apps running on the host should use the advertised `localhost:9092,localhost:9093,localhost:9094` bootstrap servers.

Primary application flow:

```text
booking_ticket -> Kafka topic order-events -> manage-revenue-ticket
```

The booking service publishes booking/order events. The management and revenue service consumes those events to update operational data, revenue-related state, and downstream side effects such as confirmation email where implemented.

### Redis Cluster

The Redis compose stack runs six `redis:7-alpine` nodes:
- `redis-1`: `7001`, cluster bus `17001`
- `redis-2`: `7002`, cluster bus `17002`
- `redis-3`: `7003`, cluster bus `17003`
- `redis-4`: `7004`, cluster bus `17004`
- `redis-5`: `7005`, cluster bus `17005`
- `redis-6`: `7006`, cluster bus `17006`

The containers use fixed addresses on `redis-cluster-net` in subnet `172.30.0.0/16`. Data is mounted under `Infrastructure/redis-cluster/data/node-*`. These files are runtime state and must not be edited manually.

Redis is used for:
- Spring Session after authentication.
- Cache entries for frequently read backend data where configured.
- Shared runtime state that should survive a single app process restart.

### Network Notes

The infrastructure compose files do not all use the same Docker network:
- MySQL expects external `ticket-system-network`.
- Kafka creates and uses `kafka-net`.
- Redis creates and uses `redis-cluster-net`.

This is fine when Spring Boot services run directly on the host and connect through `localhost` ports. If the application services are moved into Docker containers, network membership and service hostnames must be reviewed so containers can reach MySQL, Kafka, and Redis correctly.

### Startup Order

Start infrastructure before running Spring Boot services:
1. Create `ticket-system-network` if it does not exist.
2. Start MySQL.
3. Start Kafka.
4. Start Redis Cluster.
5. Run `manage-revenue-ticket` and `booking_ticket` from their module POMs.

## Known High-Risk Areas

- Hardcoded secrets in local configuration.
- JWT authority mapping must not grant ADMIN to all users.
- Password encoding should use an injected bean.
- Ticket, trip, and bus status changes need transaction and concurrency protection.
- Multi-entity writes need rollback behavior.
- Large list/report endpoints need pagination or projections.
- Kafka producers and consumers need clear error handling.
- Redis cache entries need TTLs and invalidation after writes.
