# Kong API Gateway

Index: [README.md](README.md) · Runbook: `ticket-system/Infrastructure/kong/README.md` ·
Đánh giá thiết kế: doc project `claude/kong-gateway-danh-gia.md`

## Vai trò

Điểm vào **duy nhất** của FE (`VITE_KONG_API_URL=http://localhost:8000/api`, đọc ở
`booking_ticket_vue/src/constants/api_endpoint.js` — thiếu biến thì app throw lúc khởi động).
Kong 3.9 OSS chạy **DB-less**: toàn bộ route/upstream/plugin nằm trong 1 file YAML, đọc lúc khởi động.

## File nguồn

| File | Vai trò |
|---|---|
| `docker-compose.yml` | container `kong-gateway`, cổng, mạng, mount `kong.yml` → `/etc/kong/kong.yml` |
| `kong.yml` | declarative config khi BE chạy **container** (target = tên container) |
| `docker-compose.dev.yml` | override: mount `kong.dev.yml` vào **cùng đường dẫn đích**, thêm `host.docker.internal:host-gateway` |
| `kong.dev.yml` | như `kong.yml`, chỉ khác target = `host.docker.internal:8081/8082` (BE chạy **IntelliJ**) |

`kong.yml` và `kong.dev.yml` phải giống hệt nhau trừ 2 dòng `target`.

## Container

| Mục | Giá trị |
|---|---|
| Image | `kong:3.9` |
| `KONG_DATABASE` | `off` |
| `KONG_DECLARATIVE_CONFIG` | `/etc/kong/kong.yml` |
| Cổng | `8000:8000` proxy; `127.0.0.1:8001:8001` Admin API (không auth → chỉ loopback) |
| `KONG_DNS_VALID_TTL` | `10` — recreate BE đổi IP container, Kong phải phân giải lại (B25-9) |
| Log | proxy/admin access → stdout, error → stderr (`docker logs kong-gateway`) |
| Healthcheck container | `kong health` (health của Kong, khác health upstream) |
| Mạng | `ticket-system-network` |

## Định tuyến

| Service | Route path | Upstream | Target `kong.yml` | Target `kong.dev.yml` | Rate limit (IP, local) |
|---|---|---|---|---|---|
| `booking-service` | `/api/booking` | `booking-upstream` | `booking-container:8081` | `host.docker.internal:8081` | 60/phút, 1000/giờ |
| `revenue-service` | `/api` | `revenue-upstream` | `manage-revenue-ticket:8082` | `host.docker.internal:8082` | 120/phút, 2000/giờ |

- `strip_path: false` → BE nhận nguyên `/api/...`. Path dài hơn thắng (không cần `priority`).
- Timeout service: connect 5s, read/write 60s (khớp NGINX `tls/`).
- Plugin per-service: `rate-limiting`, `correlation-id` (`X-Request-ID`, `uuid#counter`, echo về client).
- Plugin global: `request-size-limiting` 8MB.
- **Không có plugin CORS** — CORS do BE trả (`common-library/.../security/SecurityConfig.java`).
- Không có plugin auth — JWT do BE xác thực.

## Active health check (Kong kiểm BE)

| Tham số | Giá trị | Lý do |
|---|---|---|
| `http_path` | `/actuator/health/readiness` | = `readinessState,db,redis`; không gồm mail |
| `timeout` | 5s | mặc định 1s quá ngắn (health đầy đủ ~2s) |
| healthy | mỗi 10s, 2 lần OK → khoẻ | |
| unhealthy | mỗi 5s; 3 lỗi HTTP / 2 lỗi TCP / 3 timeout → loại | mặc định `tcp_failures=0` = tắt |

Phía BE cần: `management.endpoint.health.probes.enabled=true`, group readiness, và `permitAll`
cho `/actuator/health/**` (chi tiết chỉ ADMIN). Test: `GatewaySecurityChainTest`, `ActuatorExposureTest`.

## Chạy

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --force-recreate   # BE trong IntelliJ
docker compose up -d --force-recreate                                                  # BE container
```

Sửa YAML → bắt buộc `--force-recreate`. Kiểm cú pháp trước:

```bash
docker run --rm -v "$PWD/kong.yml:/tmp/kong.yml:ro" -e KONG_DATABASE=off kong:3.9 kong config parse /tmp/kong.yml
```

## Debug

```bash
curl -s http://127.0.0.1:8001/upstreams/revenue-upstream/health    # HEALTHY/UNHEALTHY + IP
curl -s http://127.0.0.1:8001/upstreams/booking-upstream/health
docker logs kong-gateway --since 2m 2>&1 | grep -i healthcheck
curl -i -X OPTIONS http://localhost:8000/api/auth/login \
  -H 'Origin: http://localhost:5173' -H 'Access-Control-Request-Method: POST'   # 200 + Access-Control-Allow-Origin
```

| Hiện tượng | Nguyên nhân |
|---|---|
| Trình duyệt báo CORS; curl ra `503 failure to get a peer from the ring-balancer` | không upstream khoẻ — Kong lỗi thì không có header CORS |
| BE IntelliJ nhưng UNHEALTHY | Kong đang dùng `kong.yml` → chạy lại kèm `-f docker-compose.dev.yml` |
| BE container nhưng UNHEALTHY | Kong đang dùng `kong.dev.yml`; hoặc BE không cùng `ticket-system-network` |
| `failed to receive status line` | probe timeout — readiness chậm/treo |
| `unhealthy TCP increment` | không tới cổng BE (BE tắt, sai IP) |
| Vừa recreate BE vẫn UNHEALTHY | đợi 10-20s (DNS TTL) hoặc recreate Kong |
| Readiness 404 | BE thiếu `probes.enabled=true` |

Request trace: header `X-Request-ID` trả về client; BE nên log kèm giá trị này để nối log Kong ↔ BE.

## Rules khi sửa

- Sửa `kong.yml` ⇒ sửa `kong.dev.yml` tương ứng, rồi `kong config parse` cả hai.
- Đổi `target` ⇒ khớp `container_name` trong `app/docker-compose.yml`.
- Đổi timeout ⇒ đổi `tls/nginx.conf`.
- Thêm route mới: path cụ thể hơn `/api` sẽ tự ưu tiên; nhớ `strip_path: false` nếu BE mapping có tiền tố `/api`.
- Không mở Admin API ra ngoài loopback.

## Tồn đọng

- B29f: sau NGINX, Kong chưa có `KONG_TRUSTED_IPS` + `KONG_REAL_IP_HEADER` → rate-limit theo IP của NGINX (mọi user chung 1 hạn mức).
- B27b: CI không chạy `kong config parse`.
- `policy: local` → mỗi instance Kong đếm riêng; scale >1 Kong cần policy `redis`.
