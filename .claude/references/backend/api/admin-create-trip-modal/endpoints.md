# API — Modal tạo chuyến (Bước 1-3: Route & Vehicle → Schedule → Preview)

> Màn hình: [`.claude/docs/design/admin-create-trip-modal.md`](../../../../docs/design/admin-create-trip-modal.md) · Figma `2:3625`
> Quy ước chung: [`../_conventions.md`](../_conventions.md)
> **Liên quan:** submit thật sự nằm ở bước 4 — xem [`admin-schedule-trip-review/endpoints.md`](../admin-schedule-trip-review/endpoints.md).
> Controller: `RouteController`, `BusController`, `UserController` (`manage-revenue-ticket`, port `8082`)

## Endpoint dùng ở màn này (chỉ load dữ liệu, không submit)

| Button/Hành động UI | Method | Path | Trạng thái | Auth (thực tế) |
|---|---|---|---|---|
| Mở modal → load autocomplete "Route" | GET | `/api/route?q=` | ❌ Cần tạo mới | — |
| Mở modal → load select "Bus Unit" | GET | `/api/bus?page=&size=` | ✅ Đã có (chưa filter "khả dụng") | JWT (không check role) |
| Mở modal → load select "Assigned Driver" | GET | `/api/user?role=DRIVER` | ❌ Cần tạo mới (phụ thuộc `UserController` rỗng) | — |
| Nút Next (sang bước 4) | — | không gọi API, chỉ chuyển state FE | — | — |

## 1. Autocomplete Route — chưa tồn tại

- Xem chi tiết đề xuất ở [`admin-buses-routes/endpoints.md`](../admin-buses-routes/endpoints.md) mục 7 — dùng chung 1 endpoint `GET /api/route`, chỉ khác cách FE dùng (search-as-you-type ở đây, list đầy đủ ở màn Buses & Routes).

## 2. List Bus khả dụng

- **Method & Path:** `GET /api/bus?page=&size=`
- **Controller:** `BusController.java:24` — xem response mẫu đầy đủ ở [`admin-buses-routes/endpoints.md`](../admin-buses-routes/endpoints.md) mục 1.
- **Gap:** API hiện **không filter theo "khả dụng trong khung giờ đã chọn"** — trả về toàn bộ Bus bất kể `status` hay có đang bận ở Trip khác cùng giờ. FE tạm thời có thể tự lọc `status=ACTIVE` ở client, nhưng **không kiểm tra được trùng lịch** — đây cũng là gốc của gap "không check overlap lịch" nêu ở mục Business Logic của `.claude/docs/design/admin-create-trip-modal.md`.

## 3. List Driver khả dụng — chưa tồn tại

- **Method & Path đề xuất:** `GET /api/user?role=DRIVER&page=&size=`
- **Chặn bởi:** `UserController` hiện rỗng hoàn toàn — xem [`admin-user-management/endpoints.md`](../admin-user-management/endpoints.md).
- **Response tối thiểu cần có:** `id`, hiển thị tên (hiện chỉ có `email` ở entity `User`, xem gap field ở `admin-user-management/endpoints.md`), `driverStatus` (để lọc chỉ hiện driver `ACTIVE`).

## Requirements liên quan tới backend

- [ ] (Blocking) Cần `GET /api/route` và `GET /api/user?role=DRIVER` trước khi modal này load được đầy đủ 3 field chọn lựa ở Section 1.
- [ ] (Blocking, chung với `admin-schedule-trip-review`) Thêm logic check overlap lịch Bus/Driver ở `TripService` — hiện không có ở bất kỳ tầng nào (Controller/Service chưa đọc chi tiết, nhưng Controller không truyền tham số nào cho phép kiểm tra availability).
- [ ] Khi có `GET /api/bus`, bổ sung filter `status=ACTIVE` hoặc `availability=` để không hiện Bus đang `INACTIVE`/`PENDING` trong danh sách chọn.
