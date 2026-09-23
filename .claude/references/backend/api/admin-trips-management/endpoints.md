# API — Quản lý chuyến đi

> Màn hình: [`.claude/docs/design/admin-trips-management.md`](../../../../docs/design/admin-trips-management.md) · Figma `2:2822`
> Quy ước chung: [`../_conventions.md`](../_conventions.md)
> Controller: `TripController` (`manage-revenue-ticket`, port `8082`)
> **⚠️ Không có `@RoleRequired(ADMIN)`.**

## Endpoint dùng ở màn này

| Button/Hành động UI | Method | Path | Trạng thái | Auth (thực tế) |
|---|---|---|---|---|
| Load Calendar/List (mặc định) | GET | `/api/trip/scheduled?page=&size=` | ⚠️ Đã có (thiếu filter) | JWT (không check role) |
| Đổi filter status/ngày | — | *(API hiện không nhận filter)* | ❌ Cần bổ sung param | — |
| Nút "Create Trip" | — | mở modal, xem `admin-create-trip-modal` + `admin-schedule-trip-review` | — | — |
| Sửa 1 chuyến (từ Table row) | PUT | `/api/trip/{tripId}` | ✅ Đã có | JWT (không check role) |
| Xoá/Huỷ 1 chuyến | DELETE | `/api/trip/{tripId}` | ❌ Cần tạo mới | — |
| Xem doanh thu 1 chuyến (nếu có nút riêng) | GET | `/api/trip/{tripId}/revenue` | ✅ Đã có | JWT (không check role) |

## 1. List chuyến đã lên lịch

- **Method & Path:** `GET /api/trip/scheduled?page=&size=`
- **Controller:** `TripController.java:30`
- **Request:** chỉ nhận `page` (default `0`), `size` (default `10`) — **không nhận `status`,
  `routeId`, `busId`, `driverId`, khoảng ngày** dù UI có Filters Sidebar theo trạng thái.
- **Response (200):**
```json
{
  "status": 200,
  "message": "create success",
  "data": {
    "content": [ { "...": "Map<String,Object>, field cụ thể do TripService.getTripScheduled trả — chưa có DTO" } ],
    "totalElements": 20,
    "totalPages": 2
  },
  "timestamp": 1733728800000
}
```
**Lưu ý:** `message` trả về là `"create success"` dù đây là API đọc (`GET`) — copy-paste nhầm message
từ endpoint tạo mới, không ảnh hưởng logic nhưng nên sửa cho đúng ngữ nghĩa. Response kiểu
`Page<Map<String,Object>>` — field cụ thể (route/bus/driver/status/revenue có được include hay
không) phụ thuộc hoàn toàn vào `TripService.getTripScheduled`, cần đọc service hoặc test Postman
trước khi FE code cứng theo field nào.

## 2. Tạo chuyến

- **Method & Path:** `POST /api/trip`
- **Controller:** `TripController.java:24`
- Xem chi tiết request/response đầy đủ ở [`admin-schedule-trip-review/endpoints.md`](../admin-schedule-trip-review/endpoints.md) (đây là API dùng ở bước 4 của modal tạo chuyến, không gọi trực tiếp từ màn danh sách).

## 3. Sửa chuyến

- **Method & Path:** `PUT /api/trip/{tripId}`
- **Controller:** `TripController.java:41`
- **Request (`TripRequestDto`):**
```json
{
  "routeId": 3,
  "busId": 1,
  "driverId": 5,
  "departureTime": "2026-04-10T08:00:00",
  "arrivalTime": "2026-04-10T10:30:00",
  "revenue": 0,
  "status": "SCHEDULED"
}
```
- **Response (200):** `BaseResponseDto<Trip>`, `message` cũng bị copy nhầm thành `"create success"`.

## 4. Doanh thu 1 chuyến

- **Method & Path:** `GET /api/trip/{tripId}/revenue`
- **Controller:** `TripController.java:53`
- **Response (200) — trả thẳng `RevenueResponse`, KHÔNG bọc qua `BaseResponseDto`:**
```json
{ "tripId": 12, "totalRevenue": 4500000, "averageRevenue": 150000 }
```
**Lưu ý:** đây là endpoint DUY NHẤT trong `TripController` không dùng `BaseResponseDto` — FE cần xử lý
riêng, không mong đợi field `status`/`data` như các API khác.

## 5. Xoá/Huỷ chuyến — chưa tồn tại

- **Method & Path đề xuất:** `DELETE /api/trip/{tripId}`
- **Khuyến nghị nghiệp vụ:** nếu chuyến chưa bán vé (`status=SCHEDULED`, chưa có `Ticket` nào) → cho
  xoá cứng. Nếu đã bán vé → chỉ cho đổi `status=CANCELLED`, giữ lại lịch sử phục vụ báo cáo doanh thu.

## Requirements liên quan tới backend

- [ ] (Blocking) Bổ sung param filter (`status`, `routeId`, `busId`, `driverId`, khoảng ngày) cho `GET /api/trip/scheduled`.
- [ ] (Blocking) Tạo `DELETE /api/trip/{tripId}` (hoặc endpoint huỷ riêng, xem khuyến nghị ở mục 5).
- [ ] Đổi response `/scheduled` từ `Map<String,Object>` sang DTO rõ field (`TripSummaryResponse` chẳng hạn).
- [ ] Sửa `message` bị copy nhầm ("create success") ở `/scheduled` (GET) và `PUT /{tripId}`.
- [ ] Đồng bộ `GET /{tripId}/revenue` vào `BaseResponseDto` cho nhất quán, hoặc ghi rõ đây là ngoại lệ nếu chủ đích giữ nguyên.
- [ ] (Bảo mật) Thêm `@RoleRequired(ADMIN)` cho `TripController`.
