# Redis Cluster

Index: [README.md](README.md) · Runbook: `ticket-system/Infrastructure/redis-cluster/README.md` ·
Workflow: `.claude/references/backend/workflows/docker-redis-setup.md` · Rules: `.claude/references/backend/rules/redis.md`

## Vai trò

6 node Redis 7 (3 master + 3 replica) dùng chung cho 2 service: cache (`spring.cache.type=redis`),
HTTP session (`spring.session.store-type=redis`, timeout 30m), giữ ghế (Phase 2).
Client được dựng thủ công trong `common-library/src/main/java/com/ticket_system/common/config/RedisConfig.java`.

## File nguồn

| File | Trạng thái |
|---|---|
| `Infrastructure/redis-cluster/docker-compose.yml` | **dùng** — 6 service `redis-node-1..6`, container `redis-1..6`, tạo mạng `redis-cluster-net` |
| `data/node-1..6/` | dữ liệu runtime (`nodes.conf`, AOF) — không sửa, không commit |
| `Dockerfile` | **không dùng** — Dockerfile Spring cũ nằm nhầm chỗ (B29b) |
| `setup-cluster.sh` | **không hoạt động** — chỉ `rm -rf ./redis-data` (thư mục không tồn tại) (B29c) |
| `redis-cluster.tmpl` | rỗng |

## Cấu hình chính (mỗi node)

| Mục | Giá trị (node N) |
|---|---|
| Image | `redis:7-alpine`, `restart: always` |
| Cổng | client `700N`, bus `1700N` (= client + 10000), đều publish ra host |
| IP cố định | `ipv4_address: 172.30.0.1N` = `--cluster-announce-ip` (phải trùng) |
| Tham số | `--cluster-enabled yes`, `--cluster-node-timeout 5000`, `--appendonly yes`, `--protected-mode no` (không mật khẩu) |
| Mạng | `redis-cluster-net`, subnet `172.30.0.0/16`, tên cố định (không tiền tố project) |

Tạo cluster **1 lần** sau lần `up` đầu (hoặc sau khi xoá `data/`):

```bash
docker exec -it redis-1 redis-cli --cluster create \
  172.30.0.11:7001 172.30.0.12:7002 172.30.0.13:7003 \
  172.30.0.14:7004 172.30.0.15:7005 172.30.0.16:7006 --cluster-replicas 1
```

## Cách BE kết nối — cơ chế announce IP

Client nối vào 1 node, nhận sơ đồ cluster với IP `172.30.0.11-16`, rồi nối thẳng node giữ slot.
Từ máy host (macOS Docker Desktop) IP `172.30.x` không route được → `RedisConfig` có cờ đổi IP.

| BE chạy ở | `spring.redis.cluster.nodes` | Cờ `app.redis.map-docker-ips-to-localhost` | Đường đi |
|---|---|---|---|
| IntelliJ | `172.30.0.11:7001,…` (`application.properties`) | `true` (mặc định) | đổi `172.x` → `127.0.0.1`, qua cổng publish |
| Container | `redis-1:7001,…` (`SPRING_REDIS_CLUSTER_NODES`) | `false` (`APP_REDIS_MAP_DOCKER_IPS_TO_LOCALHOST`) | thẳng IP `172.30.x` trong `redis-cluster-net` |

**Key thật được đọc là `spring.redis.cluster.nodes`**, không phải `spring.data.redis.*`. Các key
`spring.data.redis.*` trong `manage-revenue-ticket/application.properties` là cấu hình chết (B27e).
Test liên quan: `RedisConfigTest`.

## Kiểm tra

```bash
docker exec redis-1 redis-cli -p 7001 cluster info | head -3   # cluster_state:ok
docker exec redis-1 redis-cli -p 7001 cluster nodes            # 3 master + 3 slave, IP 172.30.0.x
curl -s localhost:8082/actuator/health/readiness                # BE IntelliJ: UP (gồm redis)
```

Reset (mất toàn bộ cache/session): `docker compose down` → `rm -rf ./data/node-*` → `up -d` → chạy lại `--cluster create`.

## Lỗi thường gặp

| Hiện tượng | Nguyên nhân |
|---|---|
| BE container `Unable to connect to /127.0.0.1:700x` | thiếu `APP_REDIS_MAP_DOCKER_IPS_TO_LOCALHOST=false` |
| BE IntelliJ không tới Redis, nodes `173.20.0.x` | sai dải mạng (B28 đã sửa cho booking) |
| `cluster_state:fail` / `CLUSTERDOWN` | chưa `--cluster create`, hoặc quá nửa master chết |
| Readiness BE `DOWN`, Kong UNHEALTHY | readiness gồm `redis` |
| Compose báo mạng `redis-cluster-net` thiếu nhãn | mạng tạo tay trước (theo CLAUDE.md cũ) — `docker network rm redis-cluster-net` rồi `up` (B29d) |

## Rules khi sửa

- IP cố định là contract: `ipv4_address` = `--cluster-announce-ip` = `application.properties` = lệnh `--cluster create`.
  Đổi IP node đang có `nodes.conf` → cluster hỏng, phải reset.
- Đổi cấu hình client → sửa `RedisConfig` + key `spring.redis.*`, không thêm `spring.data.redis.*`.
- Không đụng `data/`.

## Production

`mem_limit: 150m` mỗi node (theo tên service `redis-node-N`, không phải `redis-N`). Không mật khẩu,
`--protected-mode no` → chỉ an toàn khi 7001-7006 / 17001-17006 không mở ra Internet (firewall VM).
