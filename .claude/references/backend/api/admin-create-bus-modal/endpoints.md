# API — Modal tạo xe

> Màn hình: [`.claude/docs/design/admin-create-bus-modal.md`](../../../../docs/design/admin-create-bus-modal.md) · Figma `2:3949`
> Quy ước chung: [`../_conventions.md`](../_conventions.md)
> Controller: `BusController` (`manage-revenue-ticket`, port `8082`)

## Endpoint dùng ở màn này

| Button/Hành động UI | Method | Path | Trạng thái | Auth (thực tế) |
|---|---|---|---|---|
| Nút "Save" (tạo mới) | POST | `/api/bus` | ✅ Đã có | JWT (không check role) |
| Nút "Save" (chỉnh sửa) | PUT | `/api/bus/{busId}` | ✅ Đã có | JWT (không check role) |

## 1. Tạo Bus

- **Method & Path:** `POST /api/bus`
- **Controller:** `BusController.java:38` (method `postBus`)
- **Request (`BusRequest`):**

```json
{ "plateNumber": "FV-0000-XX", "capacity": 45, "status": "ACTIVE" }
```

| Field | Type | Required (đề xuất) | Ghi chú |
|---|---|---|---|
| `plateNumber` | string | có | không check unique ở backend — trùng biển số vẫn tạo được, **rủi ro dữ liệu trùng** |
| `capacity` | Integer | có | map trực tiếp Capacity slider/input trên UI, không check `> 0` |
| `status` | **string tự do** | có | UI dùng Segmented Control 3 lựa chọn — FE phải tự giới hạn gửi đúng `ACTIVE`/`INACTIVE`/`PENDING` (khớp enum `BusStatus`), backend **không tự validate enum** vì field DTO khai là `String` |

- **Response (200):**
```json
{ "status": 201, "message": "Post successfully", "data": null, "timestamp": 1733728800000 }
```
`data` trả `null` — sau khi tạo, FE cần tự gọi lại `GET /api/bus` để hiển thị Bus vừa tạo trong danh sách (xem [`admin-buses-routes/endpoints.md`](../admin-buses-routes/endpoints.md)).

## 2. Sửa Bus

- **Method & Path:** `PUT /api/bus/{busId}`
- **Controller:** `BusController.java:44` (method `putBus`)
- **Request:** giống `BusRequest` ở trên.
- **Response (200):** `{ "status": 201, "message": "Put successfully", "data": null, ... }` — cũng không trả lại object.

## Requirements liên quan tới backend

- [ ] Thêm check `plateNumber` unique ở backend (hiện có thể tạo 2 Bus cùng biển số).
- [ ] Đổi `BusRequest.status` từ `String` sang enum `BusStatus` để backend tự validate giá trị hợp lệ.
- [ ] `POST`/`PUT` nên trả lại `Buses` đã tạo/sửa thay vì `null`.
- [ ] (Bảo mật) Thêm `@RoleRequired(ADMIN)` cho `BusController`.
