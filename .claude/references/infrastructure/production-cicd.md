# Production & CI/CD

Index: [README.md](README.md) · Nguồn: `DEPLOYMENT.md` (root), `Infrastructure/docker-compose.prod.override.yml`,
`ticket-system/.github/workflows/ci-cd.yml`, `booking_ticket_vue/.github/workflows/ci.yml`

## Mô hình triển khai

| Thành phần | Nơi chạy |
|---|---|
| Backend + toàn bộ hạ tầng | VM1 Oracle Always Free (Ampere A1, ~6GB RAM), tất cả bằng Docker, chế độ container + `tls/` |
| K8s sandbox | VM2 k3s riêng — xem [k8s-sandbox.md](k8s-sandbox.md) |
| Frontend | Cloudflare Pages Git integration (đổi từ Vercel 2026-10-28) — runbook ở mục "CD frontend" bên dưới |
| Image | GHCR `ghcr.io/<owner>/ticket-system-<module>:latest` |
| MySQL | container trên VM1 (không managed DB) |
| MinIO | **chưa có** compose — cần xác nhận trước khi deploy |

## Ngân sách RAM (`docker-compose.prod.override.yml`)

| Service (tên service compose) | `mem_limit` | Heap |
|---|---|---|
| `broker1..3` | 700m ×3 | `KAFKA_HEAP_OPTS=-Xmx400m -Xms400m` |
| `mysql` | 700m | mặc định |
| `kong` | 256m | — |
| `redis-node-1..6` | 150m ×6 | — |
| `booking-service`, `manage-revenue-ticket` | 500m ×2 | `JAVA_TOOL_OPTIONS=-Xmx350m` |
| `kafka-ui` | tắt (`profiles: ["debug"]`) | — |
| **Tổng trần** | ~4950m | còn ~1GB cho OS + nginx — sát, theo dõi `docker stats` |

Override gộp theo **tên service** (không phải `container_name`). Vượt `mem_limit` → container bị OOM-kill;
heap đặt thấp hơn để chừa metaspace/thread stack/page cache.

## CI/CD (`ticket-system/.github/workflows/ci-cd.yml`)

Trigger: push `main` khi đổi `booking_ticket/**`, `manage-revenue-ticket/**`, `common-library/**`, `pom.xml`.

```mermaid
graph LR
    BuildTest[build-test: mvn clean test, JDK 21] --> BuildPush[build-push matrix 2 module: docker build-push, context ticket-system]
    BuildPush --> DeployVm1[deploy-vm1: SSH appleboy, compose pull + up -d]
```

Secret GitHub: `VM1_HOST`, `VM1_USER`, `VM1_SSH_KEY` (+ `GITHUB_TOKEN` cho GHCR).
Không trigger `pull_request`, không kiểm compose/Kong, không buildx cache (B27b, B27c). Đổi `Infrastructure/**`
không kích hoạt CI. Sửa ở task **6.2b** (sau khi có VM) — scope đã kiểm trong
`.claude/docs/review/6.2-ci-cd-frontend.md` mục 4. Trong lúc chờ: merge `develop` → `main` vẫn chạy `build-push` +
`deploy-vm1`, job deploy đỏ (thiếu secret `VM1_*`, lỗi override bên dưới).

## CI frontend (`booking_ticket_vue/.github/workflows/ci.yml`, task 6.2)

- Trigger: mọi `pull_request` + push `main`, `develop`. `concurrency` theo ref, huỷ lần chạy cũ.
- Job `build-test` (`timeout-minutes: 15`): Node 22 + cache npm → `npm ci` → `npm run test:unit -- --run` →
  `npm run build` với `VITE_KONG_API_URL=https://api.example.com/api` (chỉ để bundle hợp lệ; URL thật nằm ở Pages).
- Không có bước lint (repo không có script `lint`). Workflow không deploy và không cần secret.
- `build-test` là required status check cho `develop` và `main` (branch protection, bước 6 runbook dưới).
- Kiểm tĩnh: `docker run --rm -v "$PWD:/repo" -w /repo rhysd/actionlint:1.7.12 -no-color .github/workflows/ci.yml`.

## CD frontend: Cloudflare Pages — runbook (user làm trên dashboard)

Claude không làm được các bước này (cần tài khoản Cloudflare/GitHub của user) và không đặt secret nào.

1. dash.cloudflare.com → **Workers & Pages** → **Create** → tab **Pages** → **Connect to Git** → chọn GitHub,
   cấp quyền cho riêng repo `booking_ticket_vue` (không cấp all repositories). Nếu app đã cài từ trước, dashboard
   dùng lại mà không hỏi → kiểm GitHub → Settings → Applications → **Cloudflare Workers and Pages** → Configure →
   *Only select repositories* = `booking_ticket_vue`.
2. **Production branch:** `main`. **Preview:** bật cho mọi branch (mỗi PR có URL `https://<hash>.<project>.pages.dev`).
3. **Build settings:** framework preset `Vue` (hoặc None), build command `npm run build`, output directory `dist`,
   root directory để trống.
4. **Environment variables** (đặt cho cả *Production* và *Preview*):
   - `NODE_VERSION` = `22`
   - `VITE_KONG_API_URL` = `https://api.example.com/api` — **giá trị giữ chỗ** (6.2, D1): trang deploy được nhưng mọi
     lệnh gọi API lỗi tới khi task 6.4 đổi thành `https://api.<domain>/api` và bấm **Retry deployment**.
   Biến `VITE_*` được nhúng vào bundle lúc build → đổi giá trị phải build lại, và không bao giờ đặt secret vào đây.
5. **Save and Deploy.** Không thêm `_redirects` (`/* /index.html 200` bị Pages coi là vòng lặp); SPA history mode
   chạy vì `dist/` không có `404.html` nên Pages tự trả `index.html`.
6. **Branch protection** — GitHub → `booking_ticket_vue` → Settings → **Rules → Rulesets** → New branch ruleset,
   target `develop` và `main`, *Enforcement* = Active:
   - **Bypass list để trống** (kể cả admin/owner — mặc định classic rule cho admin bypass, khi đó check đỏ vẫn
     merge được). Nếu dùng classic Branches → Add rule thì tick *Do not allow bypassing the above settings*.
   - *Restrict deletions* và *Block force pushes*: bật.
   - *Require a pull request before merging*.
   - *Require status checks to pass* → thêm `build-test`, nguồn **GitHub Actions** (check chỉ hiện sau khi
     workflow đã chạy ít nhất 1 lần trên GitHub).
7. Kiểm (DoD 6.2): PR vào `develop` hiện check `build-test` xanh + check preview của Pages; 1 PR nháp cố ý fail
   1 test → check đỏ, nút merge bị chặn **và không có ô "bypass"/"merge without waiting"** → đóng PR, xoá branch
   nháp. Khi có người cộng tác thứ hai: thêm `.github/CODEOWNERS` (`/.github/ @<owner>`) + *Require review from
   Code Owners* để PR không tự sửa `ci.yml` cho qua check.

Để 6.4: custom domain `<domain>` cho project Pages, `VITE_KONG_API_URL` thật, Kong plugin `cors` cho origin
`https://<domain>` (+ `https://*.<project>.pages.dev` nếu preview cần gọi API).

## ⚠ Lỗi đã xác nhận (2026-09-28, `docker compose config` v2.29.7, chưa sửa)

**1. Ghép override theo từng nhóm không chạy được** (cách README `Infrastructure/` hướng dẫn):

```bash
docker compose -f kafka/docker-compose.yml -f docker-compose.prod.override.yml config
# → service "redis-node-5" has neither an image nor a build context specified
docker compose -f app/docker-compose.yml -f docker-compose.prod.override.yml config
# → service "broker2" has neither an image nor a build context specified
```

Override khai báo mọi service; service nào không có trong file gốc thành service mới thiếu image → lỗi.
Bước `pull` trong job `deploy-vm1` dùng đúng tổ hợp `app + override` → **job deploy fail ở bước này**.

**2. Ghép tất cả file trong 1 lệnh (job `deploy-vm1`, `DEPLOYMENT.md` mục 1) chạy được nhưng sai:**

Compose resolve mọi đường dẫn tương đối theo thư mục của file `-f` **đầu tiên** (`mysql/`) và đặt project
name = `mysql`. Kết quả `config`:

| Khai báo | Resolve thành | Hậu quả |
|---|---|---|
| `./kong.yml` (kong) | `Infrastructure/mysql/kong.yml` | file không tồn tại → Docker tạo thư mục rỗng, Kong không có config |
| `./nginx.conf` (tls) | `Infrastructure/mysql/nginx.conf` | như trên, NGINX sai |
| `./data/node-N` (redis) | `Infrastructure/mysql/data/node-N` | thư mục mới rỗng → mất `nodes.conf`, cluster phải tạo lại |
| volume `broker1-data` | `mysql_broker1-data` (thay vì `kafka_broker1-data`) | Kafka lên với volume trống, mất topic/offset |
| mạng `kafka-net`, `redis-cluster-net` | thành `external: true` (gộp với khai báo trong `app/`) | VM mới chưa có 2 mạng này → `up` lỗi |
| `container_name` cố định | trùng container đã tạo bởi project `kafka`/`kong`… | `container name already in use` |

Build context `../../` và `env_file ../../.env` tình cờ vẫn đúng (cùng độ sâu).

**Hướng sửa (chưa làm, cần quyết định):** tách override thành file prod riêng cạnh từng compose
(`kafka/docker-compose.prod.yml`, `app/docker-compose.prod.yml`, …) và chạy từng nhóm trong thư mục của nó;
hoặc 1 file gốc dùng `include:` (Compose ≥ 2.20, mỗi file giữ thư mục riêng). Sau khi sửa, thêm
`docker compose … config --quiet` vào CI (B27b).

## Lệch khác trong `DEPLOYMENT.md`

- Bảo chạy `setup-cluster.sh` để tạo Redis cluster — script chỉ `rm -rf ./redis-data` (B29c); dùng lệnh
  `redis-cli --cluster create` trong [redis-cluster.md](redis-cluster.md).
- Kiểm tra `curl https://<domain>/api/booking/actuator/health` và `/api/actuator/health`: Kong `strip_path: false`
  nên BE nhận nguyên `/api/.../actuator/health`, không phải path actuator (`/actuator/health`) → không kiểm được
  health qua Kong. Kiểm health bằng Admin API `127.0.0.1:8001/upstreams/<name>/health` trên VM.

## Checklist triển khai (sau khi sửa lỗi override)

1. `docker network create ticket-system-network`
2. mysql → kafka → redis-cluster (+ `--cluster create` lần đầu) → kong (mặc định, `kong.yml`) → app → tls (từng thư mục)
3. `ticket-system/.env` có đủ biến, `chmod 600`
4. Kiểm: upstream HEALTHY, `curl -I https://<domain>/api/auth/me` → 401, `docker stats` dưới trần RAM
5. Firewall VM: chỉ mở 80/443 (+22). Không mở 3306, 8001, 9092-9094, 9000, 7001-7006, 17001-17006.
