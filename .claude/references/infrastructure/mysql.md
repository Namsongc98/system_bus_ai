# MySQL

Index: [README.md](README.md) · Runbook: `ticket-system/Infrastructure/mysql/README.md`

## Vai trò

DB quan hệ chính `quan-ly-ban-hang`, dùng chung cho `booking_ticket` và `manage-revenue-ticket`.
Schema do **Flyway** trong `manage-revenue-ticket` sở hữu; Hibernate ở cả 2 service chỉ `validate`.

## File nguồn

| File | Nội dung |
|---|---|
| `Infrastructure/mysql/docker-compose.yml` | 1 service `mysql`, image `mysql:8.0`, container `mysql-ticket-system` |
| `manage-revenue-ticket/src/main/resources/db/migration/V1__baseline.sql`, `V2__tickets_unique_active_seat.sql` | migration Flyway |
| `<module>/src/main/resources/application.properties` | `spring.datasource.url=${DB_URL…}`, `spring.jpa.hibernate.ddl-auto=${JPA_DDL_AUTO:validate}` |
| `application-prod.properties` (revenue) | `spring.flyway.baseline-on-migrate=true`, `baseline-version=1` |

## Cấu hình chính

| Mục | Giá trị |
|---|---|
| Image | `mysql:8.0` (cùng bản với Testcontainers `MySQLContainer("mysql:8.0")`) |
| Container / hostname | `mysql-ticket-system` |
| Cổng | `3306:3306` |
| Mạng | `ticket-system-network` (external) |
| DB tạo sẵn | `MYSQL_DATABASE=quan-ly-ban-hang` |
| User | `root`; mật khẩu hardcode trong compose (dev-only, B29a) — BE đọc `DB_PASSWORD`, hai giá trị phải trùng |
| Volume | **không có volume có tên** → volume ẩn danh cho `/var/lib/mysql` |

## Ai kết nối, bằng địa chỉ nào

| Client | JDBC URL |
|---|---|
| BE IntelliJ, DBeaver | `jdbc:mysql://localhost:3306/quan-ly-ban-hang` (biến `DB_URL`) |
| BE container (`Infrastructure/app`) | `jdbc:mysql://mysql-ticket-system:3306/quan-ly-ban-hang` (compose đặt `SPRING_DATASOURCE_URL`) |
| Test (`ManageRevenueTicketApplicationTests`, `ActuatorExposureTest`…) | Testcontainers dựng `mysql:8.0` riêng — không đụng DB này |

## Vòng đời dữ liệu

- `up -d` / recreate: giữ dữ liệu (Compose gắn lại volume ẩn danh cũ).
- `down` rồi `up`: container + volume ẩn danh **mới** → DB trống; phải khởi động `manage-revenue-ticket`
  để Flyway tạo lại schema. Volume cũ vẫn nằm trong `docker volume ls` nhưng không được gắn.

## Kiểm tra

```bash
docker exec -it mysql-ticket-system mysql -uroot -p -e "SHOW DATABASES;"
docker exec -it mysql-ticket-system mysql -uroot -p quan-ly-ban-hang \
  -e "SELECT version, description, success FROM flyway_schema_history;"
```

## Lỗi thường gặp

| Hiện tượng | Nguyên nhân |
|---|---|
| `Access denied for user 'root'` | `DB_PASSWORD` ≠ `MYSQL_ROOT_PASSWORD` |
| `Communications link failure` | container chưa chạy, hoặc BE container không cùng `ticket-system-network` |
| Flyway checksum mismatch | đã sửa file `V<n>` đã chạy — tạo `V<n+1>` mới, không sửa file cũ |
| Cổng 3306 bị chiếm | MySQL cài sẵn trên máy — tắt nó hoặc đổi `"3307:3306"` (và `DB_URL`) |
| Readiness BE `DOWN`, Kong UNHEALTHY | readiness gồm `db` — DB không tới được thì Kong ngừng định tuyến |

## Rules khi sửa

- Không đổi `container_name` / tên DB mà không cập nhật `SPRING_DATASOURCE_URL` trong `app/docker-compose.yml`,
  `DB_URL`, và `application.properties`.
- Thay đổi schema → migration Flyway mới trong `manage-revenue-ticket` (skill `backend-database-change`,
  `.claude/references/backend/rules/database.md`). Không dùng `ddl-auto=update`.
- Không chép mật khẩu dev vào tài liệu prod hay context.

## Tồn đọng

- B29a: mật khẩu root hardcode; chưa có volume có tên. Đề xuất: `MYSQL_ROOT_PASSWORD: ${DB_PASSWORD}` + volume `mysql-data`.
- Prod đang chạy MySQL container trên cùng VM (quyết định trong `DEPLOYMENT.md`), không dùng managed DB.
