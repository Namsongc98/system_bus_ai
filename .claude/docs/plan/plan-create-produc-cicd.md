# Kế hoạch setup Production + CI/CD — Ticket Bus

> Ngày lập: 2026-10-06. Dựa trên trạng thái repo thật: `ticket-system/.github/workflows/ci-cd.yml`, `Infrastructure/*`, `DEPLOYMENT.md`, bài `07-production-va-cicd.md`.
> Task trong plan chính: `screen-feature-plan.md` Phase 6 — phase 1 → 6.1, phase 3 → 6.2 (chỉ FE), phase 2 → 6.2b (sau 6.4), phase 4 → 6.3, phase 5 → 6.4, phase 6 → 6.5, phase 7 → 6.6. Câu hỏi mở (domain, RAM, MinIO) ở mục 3 plan chính.
> Giả định: giữ mô hình hiện tại — VM1 Oracle Always Free (Ampere A1, ARM64, ~6GB RAM) chạy toàn bộ BE + hạ tầng bằng Docker Compose, FE trên Cloudflare Pages, image trên GHCR.
> 2026-10-28: đổi FE từ Vercel sang Cloudflare Pages — domain + DNS đã ở Cloudflare, gom về 1 dashboard (dash.cloudflare.com).

## 0. Hiện trạng — lỗi phải sửa trước khi deploy thật

| # | Vấn đề | Hậu quả |
|---|---|---|
| H1 | `docker-compose.prod.override.yml` ghép với nhiều `-f` | Ghép theo nhóm → lỗi "no image"; ghép tất cả → project dir = `mysql/`: Kong mất `kong.yml`, Redis mất data, Kafka volume mới |
| H2 | Chỉ tag `:latest` | Không rollback được |
| H3 | CI build trên `ubuntu-latest` (amd64), VM là Ampere **ARM64** | Image không chạy trên VM (`exec format error`) |
| H4 | CI không chạy trên PR, `mvn test` (không `verify`), không cache Maven | Lỗi chỉ lộ sau merge; build chậm |
| H5 | Deploy `up -d` không `--wait`, không smoke test, không `concurrency` | Deploy hỏng vẫn xanh; 2 deploy chồng nhau |
| H6 | App không có `healthcheck`, không log rotation, không `stop_grace_period` | `--wait` vô dụng; đĩa đầy; request bị cắt khi deploy |
| H7 | MinIO được code đọc nhưng không có compose | App có thể không khởi động/không upload được |
| H8 | Không có backup MySQL | Mất VM = mất dữ liệu vé |
| H9 | FE repo không có CI | Build lỗi chỉ thấy trên Cloudflare Pages |

## 1. Quyết định (chốt 2026-10-06)

1. **Domain — đề xuất:** mua 1 domain qua Cloudflare Registrar (giá gốc, .com ~10.5 USD/năm), DNS để ở Cloudflare.
   - `api.<domain>` → A record IP VM1, chế độ **DNS only** (mây xám) để NGINX + Let's Encrypt HTTP-01 hiện có chạy nguyên.
   - `<domain>` / `www` → Cloudflare Pages (FE; gắn custom domain trong project Pages, DNS cùng tài khoản nên Cloudflare tự tạo record). Khác origin với `api.` → cần plugin `cors` trên Kong, cho origin `https://<domain>`.
   - Phương án miễn phí: `.id.vn` (VNNIC cấp miễn phí cho công dân đủ điều kiện — kiểm điều kiện hiện hành tại nhà đăng ký).
   - Không dùng DuckDNS/nip.io: dùng chung hạn mức Let's Encrypt, kém ổn định.
   - Sửa `Infrastructure/tls/nginx.conf`: `your-domain.com` → `api.<domain>` (3 chỗ).
2. **MinIO: tự host bằng compose** — đã tạo `Infrastructure/minio/` (docker-compose.yml + README). Chỉ nội bộ (bind 127.0.0.1:9010/9011, mạng `ticket-system-network`), user app riêng tạo bằng profile `init`, `mem_limit: 384m`.
   - ⚠ MinIO CE ngừng phát hành image từ 10/2025, repo đã archive → image không có bản vá: pin digest, không public, BE viết theo API S3 chuẩn để đổi sang Garage/SeaweedFS khi cần.
   - ⚠ **2026-10-07:** `minio/minio`, `minio/mc` không còn tải được (Docker Hub + quay.io) → **đã chốt dùng `pgsty/minio` + `pgsty/mc`** (bản build lại của Pigsty, có `linux/arm64`); pin digest ở prod; chạy local OK (task 6.1).
   - Code Java hiện chưa dùng MinIO (chỉ có property) → chưa chốt cách trả file cho browser (stream qua BE khuyến nghị).
   - RAM: tổng `mem_limit` lên ~5.3GB/6GB → rất sát; ứng viên cắt: Redis 6 → 3 node, hoặc heap Kafka.
3. **Deploy cần duyệt**: GitHub Environment `production` + required reviewer (repo BE public → dùng được trên gói Free).

## 2. Lộ trình theo phase

### Phase 1 — Compose production chạy đúng trên 1 máy (sửa H1, H6)

- Tạo `Infrastructure/docker-compose.prod.yml` gốc dùng `include:` (Compose ≥ 2.20, mỗi file include giữ project dir riêng) **hoặc** mỗi nhóm 1 file `*/docker-compose.prod.yml` chạy trong thư mục của nó. Khuyến nghị `include:` → 1 lệnh duy nhất, đường dẫn tương đối đúng.
- Xoá `docker-compose.prod.override.yml` sau khi file mới chạy được (giữ `mem_limit`/heap từ bảng Bài 07).
- App service:
  - `image: ghcr.io/<owner-lowercase>/ticket-system-<module>:${IMAGE_TAG:-latest}`
  - `healthcheck`: `curl -f localhost:808x/actuator/health/readiness` (image cần có `curl`/`wget`, hoặc dùng Spring Boot `jar` + wget từ busybox)
  - `stop_grace_period: 40s` + `server.shutdown=graceful` trong `application-prod.properties`
  - `depends_on` với `condition: service_healthy` cho mysql/kafka (có thể khi dùng `include:` cùng project)
- Mọi service: `logging: { driver: json-file, options: { max-size: 10m, max-file: "3" } }`, `restart: unless-stopped`.
- Mọi port không public bind `127.0.0.1:` (MySQL 3306, Kafka 9092-9094, Redis 7001-7006, Kong Admin 8001). Chỉ NGINX publish 80/443.
- **DoD:** `docker compose -f docker-compose.prod.yml config` sạch lỗi; trên máy local `up -d --wait` → mọi container `healthy`; `curl localhost:8000/api/...` qua Kong OK.

### Phase 2 — CI backend (sửa H4)

> **2026-11-03 (user):** dời sang task **6.2b**, làm sau khi có VM (6.4). Scope đã kiểm: `.claude/docs/review/6.2-ci-cd-frontend.md` mục 4.

- Trigger: `pull_request` (không lọc `paths` — nếu lọc, PR không chạm path thì required check chờ mãi) + push `main`, `develop` (nhánh tích hợp thật) với `paths` thêm `Infrastructure/**` và `.github/workflows/**`.
- `actions/setup-java@v4` với `cache: maven`; chạy `mvn -B -ntp verify` (Testcontainers chạy được trên `ubuntu-latest` vì có Docker sẵn; đã kiểm 2026-11-03 không cần hạ tầng local).
- Upload test report (`surefire-reports`) làm artifact khi fail.
- `build-push`/`deploy-vm1` chỉ chạy khi push `main`; `packages: write` chỉ ở job `build-push`.
- Branch protection trên `develop` và `main`: bắt buộc check `build-test` xanh trước khi merge PR, không cho admin bypass.
- **DoD:** mở 1 PR vào `develop` cố tình fail test → PR bị chặn merge.

### Phase 3 — CI frontend (sửa H9)

- Workflow trong `booking_ticket_vue`: `npm ci` → `npm run test:unit -- --run` → `npm run build` (repo không có script `lint`). Làm ở task 6.2 (chỉ FE); runbook Pages + branch protection: `.claude/references/infrastructure/production-cicd.md`.
- Cloudflare Pages giữ vai trò CD cho FE (dash.cloudflare.com → Workers & Pages → Create → Pages → Connect to Git): preview deploy mỗi PR/branch, production khi merge `main`. Build command `npm run build`, output `dist`; biến môi trường `NODE_VERSION=22`, `VITE_KONG_API_URL=https://api.<domain>/api` (đặt cho cả Production và Preview).
- SPA history mode: không cần file cấu hình — Pages tự trả `index.html` cho route không khớp khi `dist/` không có `404.html`. Không thêm `_redirects` `/* /index.html 200` (Pages coi là vòng lặp và bỏ qua).
- Kong: plugin `cors` cho origin `https://<domain>` (+ `https://*.<project>.pages.dev` nếu cần gọi API từ preview).

### Phase 4 — Build & push image (sửa H2, H3)

- `docker/setup-qemu-action` + `docker/setup-buildx-action`, `platforms: linux/arm64` — **hoặc** chạy job trên runner `ubuntu-24.04-arm` (native ARM, nhanh hơn QEMU nhiều lần cho Maven build). Khuyến nghị runner ARM native.
- Tag: `${{ github.sha }}` + `latest`. Cache layer: `cache-from/to: type=gha`.
- Chỉ chạy khi `push` main (PR không push image).
- **DoD:** `docker manifest inspect ghcr.io/<owner>/ticket-system-booking_ticket:<sha>` có `arm64`.

### Phase 5 — Chuẩn bị VM1 (1 lần)

| Việc | Ghi chú |
|---|---|
| User `deploy` riêng, SSH key-only, tắt password + root login | Key deploy riêng cho CI (ed25519), không dùng key cá nhân |
| Docker Engine + Compose plugin ≥ 2.20 | Cần cho `include:` |
| Firewall | Oracle **Security List** chỉ mở 22/80/443. Image Ubuntu của Oracle có sẵn rule iptables REJECT → phải mở 80/443 trong iptables nữa |
| Swap 2GB | Đệm khi JVM vượt nhẹ, tránh OOM toàn VM |
| `ticket-system/.env` quyền `600`, owner `deploy` | Tạo tay trên VM, không qua CI |
| `docker login ghcr.io` bằng PAT `read:packages` | Hoặc để package public |
| TLS | certbot cấp cert → mount vào `tls/`; cron renew + reload NGINX |
| Redis cluster init 1 lần | `setup-cluster.sh` |
| Backup | cron `mysqldump --single-transaction` hằng ngày → gzip → Oracle Object Storage (rclone/oci cli), giữ 7–14 bản; **test restore** 1 lần |

### Phase 6 — CD: deploy có kiểm chứng + rollback (sửa H5)

- Logic deploy nằm trong `Infrastructure/deploy.sh <sha>` trên repo (test được bằng tay), workflow chỉ SSH gọi script:
  1. `git pull` thư mục Infrastructure (cấu hình compose) — hoặc copy bằng `scp-action` để VM không cần quyền đọc repo
  2. Lưu SHA đang chạy vào `.previous_sha`
  3. `IMAGE_TAG=<sha> docker compose pull <app services>`
  4. `IMAGE_TAG=<sha> docker compose up -d --wait --wait-timeout 180 <app services>`
  5. Smoke test qua Kong: `curl -fsS https://<domain>/api/booking/actuator/health` + 1 API GET public
  6. Fail ở 4/5 → `IMAGE_TAG=$(cat .previous_sha) docker compose up -d --wait` + exit 1 (job đỏ)
  7. Thành công → ghi SHA vào `.current_sha`, `docker image prune -f --filter until=168h`
- Workflow: `concurrency: { group: deploy-prod, cancel-in-progress: false }`, `environment: production` (secrets VM + reviewer).
- Thêm `workflow_dispatch` với input `sha` → rollback/redeploy bằng tay từ GitHub UI.
- Lưu ý Flyway: rollback image **không** rollback schema → migration phải theo expand/contract (V5+ chỉ thêm cột/bảng, xoá ở release sau).

### Phase 7 — Observability tối thiểu

- Actuator + Micrometer `/actuator/prometheus`, chỉ expose nội bộ (không route qua Kong public).
- Uptime check ngoài VM (UptimeRobot/Better Stack free) gọi `https://<domain>/api/booking/actuator/health` mỗi 1–5 phút → mail/Telegram khi down.
- Cảnh báo đĩa: cron `df` > 80% → gửi Telegram webhook.
- Correlation-id Kong → MDC log BE (đã có plugin correlation-id, kiểm lại BE có đưa vào log pattern chưa).
- Giai đoạn sau (nếu còn RAM): Prometheus + Grafana trên VM2, scrape VM1 qua private network.

## 3. Thứ tự làm & ước lượng

| Thứ tự | Phase | Phụ thuộc | Ước lượng |
|---|---|---|---|
| 1 | Chốt quyết định mục 1 | — | 0.5 ngày |
| 2 | Phase 1 compose prod | — | 1–2 ngày |
| 3 | Phase 2 CI BE + Phase 3 CI FE | — (song song với 2) | 1 ngày |
| 4 | Phase 4 build ARM + SHA | 2 | 0.5 ngày |
| 5 | Phase 5 VM1 | domain | 1 ngày |
| 6 | Phase 6 deploy + rollback | 2, 4, 5 | 1 ngày |
| 7 | Phase 7 observability | 6 | 0.5–1 ngày |

## 4. Trade-off

- **1 VM + Compose thay vì K8s/managed service:** chi phí 0, dễ hiểu từng lớp; đổi lại SPOF — VM chết là toàn hệ thống chết. Backup ngoài VM là thứ bù tối thiểu bắt buộc.
- **Recreate deploy (có downtime ~20–60s):** không tốn thêm RAM. Rolling cần 2 instance/service (+~500MB mỗi service) — chưa đáng ở giai đoạn này.
- **Deploy script trong repo thay vì inline YAML:** chạy tay được khi GitHub Actions lỗi; review được như code.
- **Runner ARM native thay vì QEMU:** build Maven trong QEMU chậm 5–10 lần.

## 5. Edge case & cách debug trên production

| Tình huống | Dấu hiệu | Debug |
|---|---|---|
| OOM (vượt `mem_limit`) | Exit 137, `OOMKilled: true` | `docker inspect <c> --format '{{.State.OOMKilled}}'`, `docker stats` |
| Flyway migration lỗi | App restart liên tục, log `failed migration` | `docker logs --since 10m manage-revenue-ticket`; sửa tay + `flyway repair` |
| Redis cluster mất slot sau reboot | Lỗi `CLUSTERDOWN` | `redis-cli -p 7001 cluster info` |
| Kafka broker không lên lại | Consumer lag tăng, producer timeout | `kafka-ui --profile debug` tạm thời, log broker |
| Kong trả 502/503 sau deploy | Target UNHEALTHY | `curl 127.0.0.1:8001/upstreams/<name>/health` |
| Cert hết hạn | Browser báo lỗi TLS | `certbot certificates`, log cron renew |
| GHCR pull 401 | Deploy fail bước pull | `docker login` lại trên VM, kiểm hạn PAT |

Metric cần nhìn: error rate 5xx tại Kong, p95 latency, JVM heap/GC pause, HikariCP active/pending, Kafka consumer lag `order-events`, disk usage.