# Report — Kế hoạch xây dựng tính năng theo màn hình (FE ↔ BE)

Plan: `.claude/docs/plan/screen-feature-plan.md` · Ledger: `.claude/ledger/screen-feature-plan.md`.
Mỗi task CLEAN ở `/lead-review` có 1 file report riêng (viết bởi skill `plan-report`);
file này chỉ là mục lục.

| ID | Task | Ngày | Lead review | Report |
|---|---|---|---|---|
| 0.1 | Dùng 1 base URL `VITE_KONG_API_URL` → Kong `:8000/api`; bỏ `bookingClient` | 2026-09-28 | round 1, CLEAN | [0.1-kong-base-url.md](0.1-kong-base-url.md) |
| 0.2 | Đồng bộ `API_ENDPOINTS` với path BE đã có (B2) | 2026-09-28 | round 1, CLEAN | [0.2-api-endpoints.md](0.2-api-endpoints.md) |
| 0.4 | Khoá endpoint public (B8) | 2026-09-22 | round 2, CLEAN | [0.4-lock-public-endpoints.md](0.4-lock-public-endpoints.md) |
| 0.5 | Chặn tự đăng ký ADMIN (B11) + gắn `@RoleRequired` (B12) | 2026-09-23 | round 2, CLEAN | [0.5-register-role-required.md](0.5-register-role-required.md) |
| 0.6 | `GET /api/auth/me` | 2026-09-23 | round 5, CLEAN | [0.6-auth-me.md](0.6-auth-me.md) |
| 0.7 | Quy ước response list: `PageResponse<T>` trong `common-library` | 2026-09-24 | round 1, CLEAN | [0.7-page-response.md](0.7-page-response.md) |
| 0.8 | Sửa check sức chứa (B4) + unique ghế theo chuyến + stub báo ADMIN khi ghế huỷ được đặt lại | 2026-09-24 | round 1, CLEAN | [0.8-capacity-unique-seat.md](0.8-capacity-unique-seat.md) |
| 1.1 | BusesRoutes: CRUD xe + tuyến, trạng thái xe `AVAILABLE/IN_USE/MAINTENANCE` (B15) | 2026-09-29 | round 1, CLEAN | [1.1-buses-routes.md](1.1-buses-routes.md) |
| 1.2 | UserManagement: quản lý user + khoá tài khoản (B6) | 2026-09-29 | round 1, CLEAN | [1.2-user-management.md](1.2-user-management.md) |
| 1.3 | TripsManagement: quản lý chuyến, state machine, check trùng giờ (B30, B31) + khắc phục rủi ro (B18, B20, B26, B33, B35, B36, B37) | 2026-10-06 | round 5, CLEAN | [1.3-trips-management.md](1.3-trips-management.md) |
