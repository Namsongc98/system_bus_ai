# Workflow: Docker Kafka Setup

Use this workflow when starting, verifying, or troubleshooting the local Kafka stack defined in `Infrastructure/kafka/docker-compose.yml`.

## Stack Summary

The Kafka stack runs three Confluent Kafka 7.5.0 brokers in KRaft mode and one Kafka management console.

Services:
- `broker1`: Kafka broker/controller, host port `9092`
- `broker2`: Kafka broker/controller, host port `9093`
- `broker3`: Kafka broker/controller, host port `9094`
- `kafka-ui`: Kafka management console, host port `9000`

Docker resources:
- Network: `kafka-net`
- Volumes: `broker1-data`, `broker2-data`, `broker3-data`
- Cluster id: `q1Sh-9_ISia_zwGINzRvyQ`

## Listener Model

Each broker exposes two Kafka listener paths:

- Internal container listener:
  - Broker address pattern: `brokerN:29092`
  - Used by brokers and `kafka-ui` inside `kafka-net`
- Host listener:
  - `broker1`: `localhost:9092`
  - `broker2`: `localhost:9093`
  - `broker3`: `localhost:9094`
  - Used by Spring Boot services running directly on the host

Controller quorum:

```text
1@broker1:29093,2@broker2:29093,3@broker3:29093
```

Spring Boot local bootstrap servers should be:

```text
localhost:9092,localhost:9093,localhost:9094
```

Kafka management console uses internal bootstrap servers:

```text
broker1:29092,broker2:29092,broker3:29092
```

## Start Kafka

From the repository root:

```bash
docker compose -f Infrastructure/kafka/docker-compose.yml up -d
```

Start only Kafka without the management console when needed:

```bash
docker compose -f Infrastructure/kafka/docker-compose.yml up -d broker1 broker2 broker3
```

## Verify Containers

```bash
docker ps
```

Expected containers:
- `broker1`
- `broker2`
- `broker3`
- `kafka-ui`

Expected host ports:
- `9092`
- `9093`
- `9094`
- `9000`

Open the management console at:

```text
http://localhost:9000
```

## Application Flow

Main project flow:

```text
booking_ticket -> Kafka topic order-events -> manage-revenue-ticket
```

Use this checklist when testing the flow:
1. Kafka brokers are running.
2. Booking service has bootstrap servers `localhost:9092,localhost:9093,localhost:9094`.
3. Manage revenue service has the same bootstrap servers.
4. Producer topic name matches consumer topic name, especially `order-events`.
5. Consumer group configuration is stable for the local test.
6. Producer logs show successful send metadata.
7. Consumer logs show received event handling.

## Troubleshooting

If Spring Boot cannot connect to Kafka:
- Confirm brokers are running with `docker ps`.
- Check broker logs:

```bash
docker logs broker1
docker logs broker2
docker logs broker3
```

- Confirm the app is running on the host. If it runs inside Docker, `localhost:9092` points to the app container, not the Kafka broker.
- For host-based apps, use `localhost:9092,localhost:9093,localhost:9094`.
- For containers on `kafka-net`, use `broker1:29092,broker2:29092,broker3:29092`.
- Verify no other process already uses ports `9092`, `9093`, `9094`, or `9000`.

If the management console cannot connect:
- Confirm `kafka-ui` is on `kafka-net`.
- Confirm `KAFKA_CLUSTERS_0_BOOTSTRAPSERVERS` uses `broker1:29092,broker2:29092,broker3:29092`.
- Check logs:

```bash
docker logs kafka-ui
```

If messages are produced but not consumed:
- Confirm topic name and consumer group.
- Confirm the consumer service is running.
- Check whether the consumer is failing during deserialization.
- Check whether the event payload class or JSON shape changed.
- Check consumer logs before changing Kafka configuration.

## Stop Kafka

Stop containers while preserving volumes:

```bash
docker compose -f Infrastructure/kafka/docker-compose.yml down
```

Remove Kafka volumes only when intentionally resetting all local Kafka state:

```bash
docker compose -f Infrastructure/kafka/docker-compose.yml down -v
```

