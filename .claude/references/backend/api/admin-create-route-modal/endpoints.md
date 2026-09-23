# API — Modal tạo tuyến đường

> Màn hình: [`.claude/docs/design/admin-create-route-modal.md`](../../../../docs/design/admin-create-route-modal.md) · Figma `2:3833`
> Quy ước chung: [`../_conventions.md`](../_conventions.md)
> Controller: `RouteController` (`manage-revenue-ticket`, port `8082`)
> **Màn không có gap block nào — có thể implement ngay.**

## Endpoint dùng ở màn này

| Button/Hành động UI | Method | Path | Trạng thái | Auth (thực tế) |
|---|---|---|---|---|
| Nút "Save" (tạo mới) | POST | `/api/route` | ✅ Đã có | JWT (không check role) |
| Nút "Save" (chỉnh sửa) | PUT | `/api/route/{routeId}` | ✅ Đã có | JWT (không check role) |

## 1. Tạo Route

- **Method & Path:** `POST /api/route`
- **Controller:** `RouteController.java:18` (method `createRoute`)
- **Request (`RouteRequestDto`):**

```json
{
  "routeName": "Coastal Express Alpha",
  "startPoint": "Origin Terminal",
  "endPoint": "Destination Terminal",
  "distanceKm": 120.5,
  "status": "ACTIVE"
}
```

| Field | Type | Required (đề xuất) | Ghi chú |
|---|---|---|---|
| `routeName` | string | có | không có `@NotBlank` ở DTO — FE nên validate trước khi gửi |
| `startPoint` | string | có | tương ứng "Origin Terminal" |
| `endPoint` | string | có | tương ứng "Destination Terminal" |
| `distanceKm` | BigDecimal | có | không check `> 0` ở backend |
| `status` | string (enum `RouteStatus`: `ACTIVE`/`INACTIVE`) | không | mặc định `ACTIVE` nếu không truyền |

- **Response (200):**
```json
{
  "status": 201,
  "message": "Create Successfully",
  "data": { "id": 9, "routeName": "Coastal Express Alpha", "startPoint": "Origin Terminal", "endPoint": "Destination Terminal", "distanceKm": 120.5, "status": "ACTIVE" },
  "timestamp": 1733728800000
}
```
**Lưu ý:** field `status` trong body là `201` nhưng HTTP status thật là `200` (`ResponseEntity.ok`) — xem quy ước chung mục 4. Đây là endpoint **có trả lại object đã tạo** (`data` không rỗng).

## 2. Sửa Route

- **Method & Path:** `PUT /api/route/{routeId}`
- **Controller:** `RouteController.java:25` (method `updateRoute`)
- **Request:** giống `RouteRequestDto` ở trên.
- **Response (200):**
```json
{ "status": 201, "message": "Update Successfully", "data": null, "timestamp": 1733728800000 }
```
**Lưu ý:** khác API tạo mới, **`data` ở đây luôn là `null`** — FE sau khi sửa thành công cần tự cập
nhật lại state cục bộ (dùng luôn payload vừa gửi) hoặc gọi lại `GET /api/route` (sau khi endpoint đó
được tạo — xem [`admin-buses-routes/endpoints.md`](../admin-buses-routes/endpoints.md)) để lấy dữ liệu mới nhất.

## Lỗi có thể gặp

| Status | Khi nào |
|---|---|
| 400 | thiếu field bắt buộc (nếu FE không tự validate và backend có validate — hiện DTO không có annotation nên khả năng cao lỗi sẽ không rõ ràng, cần FE validate chặt ở client) |
| 404 | `routeId` không tồn tại (khi `PUT`) |

## Requirements liên quan tới backend

- [ ] Cân nhắc thêm `@NotBlank`/`@DecimalMin` vào `RouteRequestDto` để backend tự validate, không phụ thuộc hoàn toàn vào FE.
- [ ] `PUT /api/route/{routeId}` nên trả lại `Route` đã cập nhật (giống hành vi của `POST`) thay vì `null`, để đồng nhất hành vi 2 API.
- [ ] (Bảo mật) Thêm `@RoleRequired(ADMIN)` cho `RouteController`.
