# Backend API Reference — theo màn hình

> Đọc [`_conventions.md`](./_conventions.md) trước (response envelope, auth, status code) — không lặp
> lại ở từng file con. Mỗi màn hình có 1 folder riêng, file `endpoints.md` bên trong liệt kê toàn bộ
> API dùng ở màn đó: method/path thật (đối chiếu trực tiếp code), request/response mẫu, field nào
> button nào trên UI gọi tới, và trạng thái sẵn sàng.
>
> Slug khớp 1:1 với `.claude/docs/design/<slug>.md` (tài liệu thiết kế UI) để tra cứu chéo nhanh.

## Mục lục

### Nhóm A — Passenger / Public
| Màn hình | Folder | Controller chính |
|---|---|---|
| Đăng nhập (Admin Terminal) | [`admin-login/`](./admin-login/endpoints.md) | `AuthController` |
| Đăng ký khách hàng | [`customer-register/`](./customer-register/endpoints.md) | `AuthController` |
| Tìm chuyến + kết quả | [`trip-search-results/`](./trip-search-results/endpoints.md) | *(chưa có controller)* |
| Chọn ghế + checkout | [`seat-selection-checkout/`](./seat-selection-checkout/endpoints.md) | `BookingController` |
| Thanh toán + xác nhận | [`payment-booking-confirmation/`](./payment-booking-confirmation/endpoints.md) | `TicketController`, `TicketWebController` |
| Vé của tôi | [`my-tickets/`](./my-tickets/endpoints.md) | `TicketController` *(thiếu API list)* |

### Nhóm B — Admin Terminal
| Màn hình | Folder | Controller chính |
|---|---|---|
| Dashboard | [`admin-dashboard/`](./admin-dashboard/endpoints.md) | `AdminDashboardController` |
| Báo cáo doanh thu | [`admin-revenue-reports/`](./admin-revenue-reports/endpoints.md) | `RevenueController`, `TicketController` |
| Quản lý Xe & Tuyến | [`admin-buses-routes/`](./admin-buses-routes/endpoints.md) | `BusController`, `RouteController` |
| Quản lý chuyến đi | [`admin-trips-management/`](./admin-trips-management/endpoints.md) | `TripController` |
| Quản lý người dùng | [`admin-user-management/`](./admin-user-management/endpoints.md) | `UserController` *(rỗng)* |
| Modal tạo chuyến — bước 1-3 | [`admin-create-trip-modal/`](./admin-create-trip-modal/endpoints.md) | `TripController`, `RouteController`, `BusController` |
| Modal tạo tuyến | [`admin-create-route-modal/`](./admin-create-route-modal/endpoints.md) | `RouteController` |
| Modal tạo xe | [`admin-create-bus-modal/`](./admin-create-bus-modal/endpoints.md) | `BusController` |
| Modal tạo chuyến — bước 4 | [`admin-schedule-trip-review/`](./admin-schedule-trip-review/endpoints.md) | `TripController` |
| Pattern: Toast | [`admin-toast-notifications/`](./admin-toast-notifications/endpoints.md) | *(không có API riêng)* |
| Pattern: Xác nhận xoá | [`admin-delete-confirmation/`](./admin-delete-confirmation/endpoints.md) | *(chưa có API `DELETE` nào)* |

## Phát hiện xuyên suốt (đọc 1 lần, áp dụng cho nhiều màn)

1. **Bảo mật theo role gần như chưa được enforce** — chỉ `AdminDashboardController` có
   `@RoleRequired(ADMIN)`. Toàn bộ API quản trị khác (Trip/Route/Bus/User/Revenue) chỉ cần JWT hợp
   lệ, không phân biệt role → vi phạm chính rule đã ghi ở `references/backend/rules/security.md`
   ("ADMIN-only operations must enforce ADMIN access"). Xem chi tiết ở [`_conventions.md`](./_conventions.md#3-xác-thực-authentication--2-lớp-đã-xác-minh-trong-code).
2. **`UserController` rỗng hoàn toàn** — chặn toàn bộ màn `admin-user-management` và phần "Assigned
   Driver"/"Captain" ở 2 modal tạo chuyến.
3. **Không có API `GET` list cho Route** — chặn `admin-buses-routes`, `admin-create-trip-modal`,
   `trip-search-results`.
4. **Không có API `DELETE` cho Trip/Route/Bus/User** — chặn toàn bộ `admin-delete-confirmation` và
   nút xoá ở các màn danh sách.
5. **`frontend/api-document.md` (file cũ) mô tả nhiều endpoint theo path/response KHÔNG khớp code
   thật** (`/api/users`, `/api/routes`, `/api/buses`, `/api/trips`, `/api/tickets` số nhiều — thực tế
   backend dùng số ít `/api/user` — hiện còn rỗng, `/api/route`, `/api/bus`, `/api/trip`, `/api/ticket`;
   response envelope field `code` cũng sai, thực tế là `status`). Các file `endpoints.md` trong đây
   lấy path/response **trực tiếp từ code**, ưu tiên dùng làm nguồn thật thay cho `api-document.md` khi
   2 bên khác nhau.
