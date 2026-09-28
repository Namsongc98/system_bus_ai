# App Services (container) & Dockerfile

Index: [README.md](README.md) · Runbook: `ticket-system/Infrastructure/app/README.md`

## Vai trò

Chạy `booking_ticket` (8081) và `manage-revenue-ticket` (8082) bằng container, giống prod. Dùng cho
kiểm tích hợp và triển khai; code/debug hằng ngày thì chạy BE trong IntelliJ + Kong chế độ dev.

## File nguồn

| File | Trạng thái |
|---|---|
| `Infrastructure/app/docker-compose.yml` | **dùng** — 2 service `booking-service`, `manage-revenue-ticket` |
| `booking_ticket/Dockerfile`, `manage-revenue-ticket/Dockerfile` | **dùng** — multi-stage, build context = `ticket-system/` |
| `ticket-system/.dockerignore` | loại `.env`, `target/`, `Infrastructure/` khỏi build context |
| `booking_ticket/docker-compose.yml`, `manage-revenue-ticket/docker-compose.yml` | **cũ, hỏng — không dùng** (xem cuối file) |
| `Infrastructure/redis-cluster/Dockerfile` | **cũ, không dùng** (Java 17, B29b) |

## Dockerfile (2 file giống nhau, chỉ khác module/jar/cổng)

```text
Stage build : maven:3.9-eclipse-temurin-21
  COPY pom.xml gốc + pom của MỌI module (reactor đọc mọi <module> kể cả khi -pl)
  COPY common-library/src + <module>/src
  RUN --mount=type=cache,target=/root/.m2 mvn -B -q -pl <module> -am package -DskipTests
Stage run   : eclipse-temurin:21-jre
  user non-root `app` (uid 1001), WORKDIR /app (app sở hữu — revenue ghi uploads/)
  COPY <module>-1.0.0.jar → app.jar ; EXPOSE 808x ; ENTRYPOINT java -jar app.jar
```

- Test không chạy trong image — chạy ở CI job `build-test` và local trước commit.
- Build tay phải đứng ở `ticket-system/`: `docker build -f booking_ticket/Dockerfile .`
- Không có `-XX:MaxRAMPercentage`; heap prod đặt qua `JAVA_TOOL_OPTIONS=-Xmx350m` (override prod).
- Tên jar hardcode `*-1.0.0.jar` → đổi `<version>` trong pom phải sửa Dockerfile.

## Compose `Infrastructure/app/docker-compose.yml`

| Mục | booking-service | manage-revenue-ticket |
|---|---|---|
| `container_name` (= target Kong) | `booking-container` | `manage-revenue-ticket` |
| Image | `ghcr.io/${GITHUB_REPOSITORY_OWNER:-changeme}/ticket-system-booking_ticket:latest` | `…/ticket-system-manage-revenue-ticket:latest` |
| Cổng publish | không (chỉ Kong gọi vào) | không |
| `restart` | `unless-stopped` | `unless-stopped` |
| `env_file` | `ticket-system/.env` (secret, không commit) | như trên |

Biến môi trường ghi đè cho container (cả 2 service):

| Biến | Giá trị | Vì sao |
|---|---|---|
| `SPRING_PROFILES_ACTIVE` | `prod` | nạp `application-prod.properties` |
| `SPRING_DATASOURCE_URL` | `jdbc:mysql://mysql-ticket-system:3306/quan-ly-ban-hang` | tên container MySQL |
| `SPRING_KAFKA_BOOTSTRAP_SERVERS` | `broker1:29092,broker2:29092,broker3:29092` | listener nội bộ |
| `SPRING_REDIS_CLUSTER_NODES` | `redis-1:7001,…,redis-6:7006` | `RedisConfig` đọc `spring.redis.cluster.nodes` |
| `APP_REDIS_MAP_DOCKER_IPS_TO_LOCALHOST` | `false` | dùng thẳng IP 172.30.x |

Mạng: `ticket-system-network` + `redis-cluster-net` + `kafka-net` (external name `kafka_kafka-net`) — thiếu 1 mạng là
thiếu 1 dependency.

Secret đọc từ `.env` — chỉ tên biến: `.claude/references/backend/environment-variable-names.md`
(`JWT_SECRET`, `DB_PASSWORD`, `MAIL_*`, `MINIO_*`, …). Claude không đọc `.env`; người dùng chạy
`docker compose up` từ terminal riêng.

## Profile `prod` khác profile mặc định

| Key | Mặc định | prod |
|---|---|---|
| `spring.jpa.hibernate.ddl-auto` | `${JPA_DDL_AUTO:validate}` | `validate` |
| `spring.jpa.show-sql` | — | `false` |
| `spring.flyway.baseline-on-migrate` (revenue) | — | `true`, `baseline-version=1` |
| Actuator | `health,info,metrics`; `show-details=when_authorized`; `roles=ADMIN`; probes bật | như mặc định (áp mọi profile) |

## Chạy & kiểm tra

```bash
cd ticket-system/Infrastructure/app && docker compose up -d --build
docker logs -f manage-revenue-ticket
docker run --rm --network ticket-system-network curlimages/curl -s \
  http://manage-revenue-ticket:8082/actuator/health/readiness   # {"status":"UP"}
curl -s http://127.0.0.1:8001/upstreams/revenue-upstream/health  # HEALTHY
```

Điều kiện: MySQL, Kafka, Redis cluster đang chạy; Kong **chế độ container**; BE IntelliJ đã tắt.

## Lỗi thường gặp

| Hiện tượng | Nguyên nhân |
|---|---|
| `env file …/.env not found` | chưa tạo `ticket-system/.env` |
| `container name … already in use` | container cũ — `docker ps -a`, kiểm rồi `docker rm` |
| Build `COPY … not found` | sai build context — luôn build từ `ticket-system/` |
| Readiness `DOWN` | log BE: Redis `127.0.0.1:700x` (thiếu biến map), MySQL, … |
| Kong UNHEALTHY sau recreate | IP container đổi — đợi 10-20s |

## Rules khi sửa

- Không đổi `container_name` (contract với `kong.yml`).
- Thêm module mới vào reactor → thêm `COPY <module>/pom.xml` vào **cả 2** Dockerfile.
- Thêm dependency hạ tầng mới (vd. MinIO) → thêm mạng/biến vào compose + tên biến vào `environment-variable-names.md`.
- Thêm service mới → thêm upstream/route trong `kong.yml` + `kong.dev.yml`, mem_limit trong prod override, matrix CI.

## Tồn đọng

- B27a: `booking_ticket` không có thư mục test.
- B27d: không có `depends_on` (các dependency nằm ở compose khác nên `depends_on` cũng không áp dụng được trực tiếp).
- MinIO: code đọc `MINIO_*` nhưng không có compose cho MinIO — chưa rõ chạy ở đâu (`DEPLOYMENT.md` mục "Điều đã sửa lại").

## File compose cũ trong module (không dùng)

`booking_ticket/docker-compose.yml` và `manage-revenue-ticket/docker-compose.yml`: `build: .` (sai context — Dockerfile
cần `ticket-system/`), host DB `mysql` (container thật là `mysql-ticket-system`), mật khẩu hardcode, không join
mạng Kafka/Redis, publish 8081/8082 (đụng BE IntelliJ). Không dùng; ứng viên xoá.
