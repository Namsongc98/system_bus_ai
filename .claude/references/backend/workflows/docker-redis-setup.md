# Workflow: Docker Infrastructure Setup

Use this workflow when starting or troubleshooting local backend infrastructure: MySQL, Kafka, and Redis Cluster.

## Components

- MySQL stores users, routes, buses, trips, tickets, revenue, loyalty, salary, and audit data.
- Kafka moves booking/order events from `booking_ticket` to `manage-revenue-ticket`.
- Redis Cluster supports Spring Session and cache behavior.

## Start Infrastructure

```bash
docker network create ticket-system-network
docker compose -f Infrastructure/mysql/docker-compose.yml up -d
docker compose -f Infrastructure/kafka/docker-compose.yml up -d
docker compose -f Infrastructure/redis-cluster/docker-compose.yml up -d
```

## Verify

```bash
docker ps
```

Expected services:
- `mysql-ticket-system` on port `3306`.
- `broker1`, `broker2`, and `broker3` on ports `9092`, `9093`, `9094`.
- `redis-1` through `redis-6` on ports `7001` to `7006`.

## Application Connectivity

For Spring Boot services running on the host:
- MySQL URL should target `localhost:3306`.
- Kafka bootstrap servers should target `localhost:9092,localhost:9093,localhost:9094`.
- Redis Cluster nodes should target `localhost:7001` through `localhost:7006`.

For Spring Boot services running inside Docker:
- Review Docker networks first.
- MySQL, Kafka, and Redis are currently on separate compose networks.
- Use container hostnames only when the application container can reach the same network.

## Startup Checks

1. Confirm `ticket-system-network` exists before starting MySQL.
2. Confirm MySQL is healthy before running JPA-dependent flows.
3. Confirm all Kafka brokers are up before testing booking events.
4. Confirm all six Redis containers are up before testing login/session or cache behavior.
5. Start Spring Boot services from module POMs, not from the root aggregator.

## Troubleshooting

- Check logs for the failing container.
- Confirm the Docker network exists.
- Confirm ports are not occupied by another process.
- For Redis Cluster, confirm all six nodes are running and cluster initialization completed.
- For Kafka, confirm advertised listener settings match host-based app execution.
- For MySQL, confirm database name and credentials match application properties.
- Do not edit files under `Infrastructure/redis-cluster/data`.
