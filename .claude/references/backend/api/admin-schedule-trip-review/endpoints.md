# API — Modal tạo chuyến (Bước 4: Final Review)

> Màn hình: [`.claude/docs/design/admin-schedule-trip-review.md`](../../../../docs/design/admin-schedule-trip-review.md) · Figma `2:4033`
> Quy ước chung: [`../_conventions.md`](../_conventions.md)
> **Liên quan:** dữ liệu form đến từ bước 1-3, xem [`admin-create-trip-modal/endpoints.md`](../admin-create-trip-modal/endpoints.md). File này là nơi **duy nhất thực sự gọi API submit**.
> Controller: `TripController` (`manage-revenue-ticket`, port `8082`)

## Endpoint dùng ở màn này

| Button/Hành động UI | Method | Path | Trạng thái | Auth (thực tế) |
|---|---|---|---|---|
| Nút "Schedule Trip" | POST | `/api/trip` | ✅ Đã có | JWT (không check role) |
| Nút "Back to Schedule" | — | không gọi API, quay lại bước 1-3 | — | — |
| Nút "Cancel" | — | đóng modal, không gọi API | — | — |

## 1. Tạo chuyến (submit cuối wizard)

- **Method & Path:** `POST /api/trip`
- **Controller:** `TripController.java:24` (method `createTrip`)
- **Request (`TripRequestDto`) — build từ toàn bộ dữ liệu đã nhập ở bước 1-3:**

```json
{
  "routeId": 3,
  "busId": 1,
  "driverId": 5,
  "departureTime": "2026-10-24T08:30:00",
  "arrivalTime": "2026-10-24T15:45:00",
  "revenue": 0,
  "status": "SCHEDULED"
}
```

| Field | Type | Required (đề xuất) | Map UI |
|---|---|---|---|
| `routeId` | Long | có | Route chọn ở Section 1 |
| `busId` | Long | có | Bus Unit chọn ở Section 1 |
| `driverId` | Long | có | Assigned Driver chọn ở Section 1 |
| `departureTime` | LocalDateTime | có | Departure (Section 2) |
| `arrivalTime` | LocalDateTime | có | Estimated Arrival (Section 2) |
| `revenue` | BigDecimal | không | mặc định `0`, backend tự cộng dồn khi có vé bán ra (không set tay từ FE) |
| `status` | string (enum `TripStatus`) | không | mặc định `SCHEDULED`, khớp badge hiển thị ở bước Review |

**Không có annotation validate nào ở `TripRequestDto`** (`@NotNull`, kiểm tra `arrivalTime >
departureTime`...) — toàn bộ validate hiện phải làm ở FE, backend chưa chặn input sai định dạng
nghiệp vụ.

### Response (200)

```json
{
  "status": 201,
  "message": "create success",
  "data": {
    "id": 45,
    "route": { "id": 3, "routeName": "..." },
    "bus": { "id": 1, "plateNumber": "..." },
    "driver": { "id": 5, "email": "..." },
    "departureTime": "2026-10-24T08:30:00",
    "arrivalTime": "2026-10-24T15:45:00",
    "status": "SCHEDULED",
    "revenue": 0
  },
  "timestamp": 1733728800000
}
```

`data` trả về entity `Trip` đầy đủ (có trả lại object, khác các API update ở những màn khác) — FE có
thể dùng ngay `data.id` để đóng modal + điều hướng/refresh danh sách mà không cần gọi thêm API.

### Lỗi có thể gặp

| Status | Khi nào |
|---|---|
| 400 | thiếu field bắt buộc (nếu có validate — hiện DTO không ép, rủi ro lỗi 500 thay vì 400 khi thiếu `routeId`/`busId`/`driverId` không tồn tại) |
| 404 (đề xuất, cần xác nhận) | `routeId`/`busId`/`driverId` không tồn tại — chưa rõ `TripService.createTrip` có check tồn tại trước khi insert hay để lỗi FK ở tầng DB |
| 409 (đề xuất, chưa có) | Bus/Driver đã bận ở chuyến khác cùng khung giờ — **hiện KHÔNG có check này**, xem yêu cầu bên dưới |

## Requirements liên quan tới backend

- [ ] (Blocking) Thêm validate: `arrivalTime > departureTime`, `routeId`/`busId`/`driverId` tồn tại và đúng trạng thái khả dụng.
- [ ] (Blocking) Thêm check overlap lịch: 1 Bus/Driver không được gán 2 Trip `SCHEDULED`/`ONGOING` chồng khung giờ — hiện hoàn toàn chưa có, rủi ro cao khi nhiều Admin tạo chuyến song song.
- [ ] Trả lỗi 400/404/409 rõ ràng thay vì để lỗi rơi xuống 500 khi input sai.
- [ ] (Bảo mật) Thêm `@RoleRequired(ADMIN)` cho `TripController` (bao gồm cả endpoint này).
