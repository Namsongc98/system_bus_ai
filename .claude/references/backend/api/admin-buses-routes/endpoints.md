# API — Quản lý Xe & Tuyến đường

> Màn hình: [`.claude/docs/design/admin-buses-routes.md`](../../../../docs/design/admin-buses-routes.md) · Figma `2:2475`
> Quy ước chung: [`../_conventions.md`](../_conventions.md)
> Controller: `BusController`, `RouteController` (`manage-revenue-ticket`, port `8082`)
> **⚠️ Không controller nào ở đây có `@RoleRequired(ADMIN)`** — chỉ cần JWT hợp lệ là gọi được.

## Endpoint dùng ở màn này

| Button/Hành động UI | Method | Path | Trạng thái | Auth (thực tế) |
|---|---|---|---|---|
| Load `Bus Fleet Grid` | GET | `/api/bus?page=&size=` | ✅ Đã có | JWT (không check role) |
| Nút "Add" (cột Bus) | POST | `/api/bus` | ✅ Đã có | JWT (không check role) |
| Sửa 1 Bus Card | PUT | `/api/bus/{busId}` | ✅ Đã có | JWT (không check role) |
| Xoá 1 Bus Card | DELETE | `/api/bus/{busId}` | ❌ Cần tạo mới | — |
| Load `Route Card` list | GET | `/api/route?page=&size=` | ❌ Cần tạo mới | — |
| Nút "Add" (cột Route) | POST | `/api/route` | ✅ Đã có | JWT (không check role) |
| Sửa 1 Route Card | PUT | `/api/route/{routeId}` | ✅ Đã có | JWT (không check role) |
| Xoá 1 Route Card | DELETE | `/api/route/{routeId}` | ❌ Cần tạo mới | — |

## 1. List Bus

- **Method & Path:** `GET /api/bus?page=&size=`
- **Controller:** `BusController.java:24`
- **Response (200):**
```json
{
  "status": 200,
  "message": "Get Successfully",
  "data": {
    "content": [
      { "id": 1, "plateNumber": "29A-12345", "capacity": 45, "status": "ACTIVE" }
    ],
    "currentPage": 0,
    "totalItems": 12,
    "totalPages": 2
  },
  "timestamp": 1733728800000
}
```
**Lưu ý:** code build sẵn 1 `Map` (`content`, `currentPage`, `totalItems`, `totalPages`) rồi **không
dùng biến đó** — response thực tế trả thẳng `BaseResponseDto.success(200, ..., listBus)` với
`listBus` là `Page<Buses>` gốc của Spring Data (field chuẩn Spring: `content`, `totalElements`,
`totalPages`, `number`, `size`...). **Response mẫu ở trên theo cấu trúc Spring `Page` thật, không phải
theo biến `Map` bị bỏ quên trong code** — cần FE test thật với Postman để xác nhận field chính xác
trước khi code cứng.

## 2. Tạo Bus

- **Method & Path:** `POST /api/bus`
- **Controller:** `BusController.java:38`
- **Request (`BusRequest`):**
```json
{ "plateNumber": "29A-12345", "capacity": 45, "status": "ACTIVE" }
```
| Field | Type | Required | Ghi chú |
|---|---|---|---|
| `plateNumber` | string | có (đề xuất — DTO không có annotation validate) | không check unique ở backend hiện tại |
| `capacity` | Integer | có | không check `> 0` ở backend hiện tại |
| `status` | **String tự do** | có | phải đúng 1 trong `ACTIVE`/`INACTIVE`/`PENDING` (enum `BusStatus`) nhưng DTO không ép kiểu enum — FE phải tự giới hạn giá trị |

- **Response (200):** `BaseResponseDto<Buses>` — **`data` trả `null`**, không trả lại object vừa tạo.

## 3. Sửa Bus

- **Method & Path:** `PUT /api/bus/{busId}`
- **Controller:** `BusController.java:44`
- **Request:** giống `BusRequest` ở trên.
- **Response (200):** `data` cũng trả `null`.

## 4. Xoá Bus — chưa tồn tại

- **Method & Path đề xuất:** `DELETE /api/bus/{busId}`
- **Việc cần làm:** thêm method vào `BusController`, kiểm tra Bus không đang gắn Trip `SCHEDULED`/`ONGOING` trước khi cho xoá.

## 5. Tạo Route

- **Method & Path:** `POST /api/route`
- **Controller:** `RouteController.java:18`
- **Request (`RouteRequestDto`):**
```json
{ "routeName": "Hà Nội - Hải Phòng", "startPoint": "Hà Nội", "endPoint": "Hải Phòng", "distanceKm": 120.5, "status": "ACTIVE" }
```
- **Response (200):** `BaseResponseDto<Route>` — **có trả lại object đã tạo** (khác Bus/Route-update, method này thực sự trả `response` từ service).

## 6. Sửa Route

- **Method & Path:** `PUT /api/route/{routeId}`
- **Controller:** `RouteController.java:25`
- **Request:** giống `RouteRequestDto`.
- **Response (200):** `data` trả `null` (không trả lại Route đã sửa — không nhất quán với API tạo mới ở mục 5).

## 7. List Route — chưa tồn tại

- **Method & Path đề xuất:** `GET /api/route?page=&size=`
- **Lý do cần:** không có cách nào hiển thị cột "Routes Network" nếu thiếu endpoint này. Field trả về
  nên giống hệt field trong `RouteRequestDto`/entity `Route` (`id`, `routeName`, `startPoint`,
  `endPoint`, `distanceKm`, `status`) — không cần thiết kế thêm, chỉ cần viết method `GET`.

## 8. Xoá Route — chưa tồn tại

- **Method & Path đề xuất:** `DELETE /api/route/{routeId}`
- **Việc cần làm:** thêm method vào `RouteController`, kiểm tra Route không đang gắn Trip `SCHEDULED`/`ONGOING` trước khi cho xoá (dùng chung logic với xoá Bus nếu có thể).

## Requirements liên quan tới backend

- [ ] (Blocking) Tạo `GET /api/route` (list) — chặn toàn bộ cột phải màn hình này và cả autocomplete route ở `trip-search-results`, `admin-create-trip-modal`.
- [ ] (Blocking) Tạo `DELETE /api/bus/{busId}` và `DELETE /api/route/{routeId}`.
- [ ] Xác nhận response thật của `GET /api/bus` bằng Postman (đoạn code build `Map` rồi không dùng là dấu hiệu bug/code chết).
- [ ] Đồng nhất hành vi trả `data` sau `PUT`/`POST` — hiện Route-create trả object, Bus-create/Bus-update/Route-update đều trả `null`.
- [ ] Ép `BusRequest.status` về đúng enum `BusStatus` thay vì `String` tự do.
- [ ] (Bảo mật) Thêm `@RoleRequired(ADMIN)` cho `BusController` và `RouteController`.
