# TLS — NGINX + Let's Encrypt (chỉ production)

Index: [README.md](README.md) · Runbook: `ticket-system/Infrastructure/tls/README.md`

## Vai trò

Chỉ **TLS termination** trước Kong: nhận HTTPS :443, chuyển HTTP nguyên request sang `http://kong:8000`.
Không route, không rate-limit (Kong làm). Máy dev không cần — FE gọi thẳng Kong `:8000`.

```text
Internet :443 → tls-proxy (nginx) → http://kong:8000 → BE
Internet :80  → 301 HTTPS (trừ /.well-known/acme-challenge/ cho certbot)
```

## File nguồn

| File | Nội dung |
|---|---|
| `docker-compose.yml` | `nginx` (`nginx:1.27-alpine`, container `tls-proxy`, 80/443) + `certbot` (entrypoint `true`, chỉ dùng qua `docker compose run`) |
| `nginx.conf` | 2 server block; `your-domain.com` là placeholder (3 chỗ) |
| `certbot/conf`, `certbot/www` | chứng chỉ + file thử thách ACME — không commit |

Mạng `ticket-system-network` (external). NGINX gọi Kong bằng **tên service** `kong` (alias DNS của
service trong `kong/docker-compose.yml`), không phải container name `kong-gateway`.

## Header & timeout

| Directive | Giá trị | Ghi chú |
|---|---|---|
| `proxy_set_header Host` | `$host` | giữ tên miền gốc |
| `proxy_set_header X-Forwarded-For` | `$proxy_add_x_forwarded_for` | Kong **chưa** tin header này (B29f) |
| `proxy_read_timeout` / `proxy_send_timeout` | 60s | khớp Kong read/write 60000ms |
| `X-Forwarded-Proto` | **không đặt** | BE không biết request gốc là HTTPS (ảnh hưởng redirect/cookie `Secure` nếu có dùng) |

## Lần đầu xin chứng chỉ (gà-trứng: nginx cần cert cho 443, certbot cần nginx phục vụ 80)

1. Comment khối `server { listen 443 … }`.
2. `docker compose up -d nginx`
3. `docker compose run --rm certbot certonly --webroot -w /var/www/certbot -d <domain> --email <email> --agree-tos`
4. Bỏ comment, `docker compose restart nginx`.

Gia hạn (90 ngày): `docker compose run --rm certbot renew && docker compose exec nginx nginx -s reload` — nên cron hằng ngày
(chưa có cron nào trong repo).

## Kiểm tra

```bash
docker compose exec nginx nginx -t
curl -I http://<domain>                   # 301 → https
curl -I https://<domain>/api/auth/me      # 401 từ BE = thông tới Kong và BE
```

## Rules khi sửa

- Thứ tự chạy: Kong trước NGINX (khác compose nên không `depends_on`).
- Đổi timeout → đổi Kong. Không thêm routing/rate-limit vào NGINX.
- Không commit chứng chỉ.

## Tồn đọng

- B29f: cần `KONG_TRUSTED_IPS` (subnet `ticket-system-network`) + `KONG_REAL_IP_HEADER: X-Forwarded-For` ở Kong prod.
- Chưa có HSTS, chưa cấu hình `ssl_protocols`/ciphers (dùng mặc định nginx 1.27).
