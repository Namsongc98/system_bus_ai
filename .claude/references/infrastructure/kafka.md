# Kafka

Index: [README.md](README.md) · Runbook: `ticket-system/Infrastructure/kafka/README.md` ·
Workflow chi tiết: `.claude/references/backend/workflows/docker-kafka-setup.md` · Rules: `.claude/references/backend/rules/kafka.md`

## Vai trò

Event bus giữa 2 service. `booking_ticket` produce `BookingEvent` vào topic `order-events`
(key = `customerEmail`); `manage-revenue-ticket` consume bằng 3 consumer group độc lập (mỗi group nhận đủ mọi message).

| Consumer group | Listener class |
|---|---|
| `booking-group` | `manage-revenue-ticket/.../service/RevenueConsumer.java` |
| `revenue-group` | `manage-revenue-ticket/.../service/RevenueService.java` |
| `email-service-group` | `manage-revenue-ticket/.../service/EmailConfirmTicketConsumer.java` |

Producer: `booking_ticket/.../service/BookingProducer.java`.

## File nguồn

`Infrastructure/kafka/docker-compose.yml` — project `kafka`, 3 broker + `kafka-ui`, tạo mạng `kafka-net`
(tên thật `kafka_kafka-net`), 3 volume có tên `broker1-data…`.

## Cấu hình chính

| Mục | Giá trị |
|---|---|
| Image | `confluentinc/cp-kafka:7.5.0` (Kafka 3.5), 3 broker cùng bản |
| Chế độ | KRaft combined (`KAFKA_PROCESS_ROLES=broker,controller`), không Zookeeper |
| Quorum | `1@broker1:29093,2@broker2:29093,3@broker3:29093` |
| `CLUSTER_ID` | giống nhau ở 3 broker; đổi → phải xoá volume |
| Replication topic nội bộ | offsets RF=3, transaction log RF=3, `min ISR=2` → chịu được 1 broker chết |
| Kafka UI | `provectuslabs/kafka-ui:latest`, `http://localhost:9000` |

## Listener — nguyên nhân số 1 của lỗi kết nối

| Listener | Địa chỉ | Dùng cho |
|---|---|---|
| `PLAINTEXT` | `brokerN:29092` | container ↔ container (broker khác, app, kafka-ui) |
| `CONTROLLER` | `brokerN:29093` | chỉ bầu controller giữa broker |
| `PLAINTEXT_HOST` | host `localhost:9092/9093/9094` | BE chạy IntelliJ |

Client vào listener nào nhận `ADVERTISED_LISTENERS` của listener đó → container không bao giờ nhận
`localhost`, IntelliJ không bao giờ nhận `broker1`.

| BE chạy ở | `spring.kafka.bootstrap-servers` | Đặt ở |
|---|---|---|
| IntelliJ | `localhost:9092,localhost:9093,localhost:9094` | `application.properties` 2 service |
| Container | `broker1:29092,broker2:29092,broker3:29092` | `SPRING_KAFKA_BOOTSTRAP_SERVERS` trong `app/docker-compose.yml` |

## Cấu hình client (application.properties)

- Producer (booking): `acks=all`, `enable-idempotence=true`, `retries=3`, `JsonSerializer`.
- Consumer (revenue): `auto-offset-reset=earliest`, `JsonDeserializer`, `trusted.packages=*`, `listener.concurrency=3`.
- `spring.kafka.admin.auto-create=false` (booking). Không có bean `NewTopic`/`TopicBuilder` trong code.

## Kiểm tra

```bash
docker exec broker1 kafka-topics --bootstrap-server broker1:29092 --list
docker exec broker1 kafka-topics --bootstrap-server broker1:29092 --describe --topic order-events
docker exec broker1 kafka-consumer-groups --bootstrap-server broker1:29092 --describe --group booking-group
```

## Lỗi thường gặp

| Hiện tượng | Nguyên nhân |
|---|---|
| BE container `UnknownHostException: broker1` | container không join `kafka_kafka-net` |
| BE IntelliJ `Connection to node … broker1:29092` | BE dùng `broker1:29092` thay vì `localhost:9092` |
| Broker khởi động rồi thoát, log `cluster ID` | volume cũ của cluster khác — `docker compose down -v` (mất dữ liệu topic) |
| Message chia lung tung giữa 2 BE | IntelliJ và container BE chạy cùng lúc, cùng consumer group |

## Rules khi sửa

- Đổi hostname/cổng listener → cập nhật cả `app/docker-compose.yml` lẫn `application.properties`.
- Đổi tên project (thư mục `kafka/`) hoặc tên mạng → tên `kafka_kafka-net` trong `app/docker-compose.yml` hỏng.
- Không đổi `CLUSTER_ID` trên môi trường có dữ liệu.
- Thay đổi event DTO / consumer / retry / DLT → skill `backend-kafka-event`.

## Cần kiểm chứng (phát hiện khi viết context, chưa chạy live)

- `order-events` không được tạo tường minh (không `NewTopic`, admin auto-create tắt) → nhiều khả năng do
  broker tự tạo khi produce lần đầu với mặc định broker (Apache Kafka: `num.partitions=1`,
  `default.replication.factor=1`). Nếu đúng: topic chỉ 1 partition, RF=1 → `concurrency=3` vô ích và mất
  1 broker là mất topic. Kiểm bằng `--describe --topic order-events` ở trên.
- `auto.create.topics.enable=false` trong `manage-revenue-ticket/application.properties` là **config của broker**,
  đặt trong Spring không có tác dụng.
- `RevenueService` log in `groupId: booking-group` nhưng annotation là `revenue-group` — log gây nhầm.

## Production

`docker-compose.prod.override.yml`: mỗi broker `mem_limit: 700m`, `KAFKA_HEAP_OPTS=-Xmx400m -Xms400m`;
`kafka-ui` tắt (bật bằng `--profile debug`). Không có TLS/SASL — mọi listener PLAINTEXT, chỉ an toàn khi
9092-9094 không mở ra Internet.
