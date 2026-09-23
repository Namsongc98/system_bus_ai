# Docker Rules

## Local Infrastructure

Infrastructure is under `Infrastructure/`:
- `Infrastructure/mysql/docker-compose.yml`
- `Infrastructure/kafka/docker-compose.yml`
- `Infrastructure/redis-cluster/docker-compose.yml`

Infrastructure responsibilities:
- MySQL stores the main relational business data.
- Kafka carries booking/order events between services.
- Redis Cluster stores sessions and cache data.
- Docker Compose provides local development dependencies; it is not the Spring Boot runtime entrypoint.

Create the shared network before starting services:

```bash
docker network create ticket-system-network
```

Start services:

```bash
docker compose -f Infrastructure/mysql/docker-compose.yml up -d
docker compose -f Infrastructure/kafka/docker-compose.yml up -d
docker compose -f Infrastructure/redis-cluster/docker-compose.yml up -d
```

## Editing Rules

- Do not edit runtime data under `Infrastructure/redis-cluster/data`.
- Keep Dockerfile and compose changes scoped to backend services and infrastructure.
- Prefer environment variables for credentials and service endpoints.
- Preserve exposed local ports unless the task explicitly changes them.
- Treat container names, advertised listeners, cluster announce IPs, and mounted volumes as runtime contract. Change them only when the corresponding application configuration and workflow documentation are updated together.
- For local-only credentials in compose files, do not copy those values into production guidance.

## Expected Local Ports

- MySQL: `3306`
- Kafka brokers: `9092`, `9093`, `9094`
- Kafka management console: `9000` if enabled by compose
- Redis Cluster: `7001` to `7006`
- Redis cluster bus ports: `17001` to `17006`
- Booking service: `8081`
- Manage revenue service: `8082`

## Network Model

Current compose networks:
- MySQL uses external `ticket-system-network`.
- Kafka uses `kafka-net`.
- Redis Cluster uses `redis-cluster-net` with fixed node IP addresses.

Spring Boot services commonly run on the host during development and connect through localhost ports. If services are containerized, make sure their containers join the correct networks or use reachable hostnames.

## MySQL Notes

- Container name: `mysql-ticket-system`.
- Image: `mysql:8.0`.
- Database: `quan-ly-ban-hang`.
- Main consumers: both Spring Boot services through JPA repositories.
- Common startup failure: database container is not running, database is missing, or credentials do not match application properties.

## Kafka Notes

- Containers: `broker1`, `broker2`, `broker3`.
- Image: `confluentinc/cp-kafka:7.5.0`.
- Local bootstrap servers: `localhost:9092,localhost:9093,localhost:9094`.
- Main topic area: booking/order events, especially `order-events`.
- Common startup failure: advertised listeners do not match where the Spring Boot process is running.

## Redis Cluster Notes

- Containers: `redis-1` through `redis-6`.
- Image: `redis:7-alpine`.
- Data directories: `Infrastructure/redis-cluster/data/node-*`.
- Main consumers: Spring Session and cache configuration.
- Common startup failure: nodes are running but the cluster was not initialized or the app uses single-node Redis settings.

## Troubleshooting

- Use `docker ps` to check container state.
- Use `docker logs <container>` for infrastructure startup errors.
- If a service cannot connect, verify the compose stack, local port binding, and application properties.
- If Redis Cluster does not respond, verify all six nodes are up and cluster setup completed.
- If Kafka consumers do not receive events, verify the producer bootstrap servers, topic name, consumer group, and broker logs.
- If MySQL starts but the app fails schema operations, inspect the Spring Boot stack trace and JPA/database configuration.
