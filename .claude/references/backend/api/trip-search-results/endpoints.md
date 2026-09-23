# API — Trang chủ tìm chuyến + Kết quả

> Màn hình: [`.claude/docs/design/trip-search-results.md`](../../../../docs/design/trip-search-results.md) · Figma `2:961`
> Quy ước chung: [`../_conventions.md`](../_conventions.md)
> Controller: **không có** — toàn bộ endpoint dưới đây đều cần tạo mới.

## Endpoint dùng ở màn này

| Button/Hành động UI | Method | Path (đề xuất) | Trạng thái |
|---|---|---|---|
| Nút "Search" (điểm đi/đến/ngày) | GET | `/api/trip/search?from=&to=&date=&page=&size=` | ❌ Cần tạo mới |
| Autocomplete ô "Điểm đi"/"Điểm đến" | GET | `/api/route` (hoặc `/api/route/options`) | ❌ Cần tạo mới |

`TripController` hiện có (`manage-revenue-ticket`, `8082`) nhưng **không có** endpoint tìm kiếm công
khai — toàn bộ method hiện tại (`POST /api/trip`, `GET /api/trip/scheduled`, `PUT /api/trip/{id}`,
`GET /api/trip/{id}/revenue`) đều thiết kế cho Admin Terminal, không phù hợp cho trang public search
(không filter theo route+ngày, và `/scheduled` đang yêu cầu auth — xem `_conventions.md`).

## 1. (Đề xuất) Tìm chuyến theo tuyến + ngày

- **Gọi khi:** user bấm "Search" sau khi nhập Điểm đi/Điểm đến/Ngày ở Hero Section.
- **Method & Path đề xuất:** `GET /api/trip/search`
- **Auth đề xuất:** Public (khách chưa đăng nhập vẫn tìm được chuyến).

### Request (query params, đề xuất)

| Param | Type | Required | Ghi chú |
|---|---|---|---|
| `from` | string hoặc `routeId` | có | nên dùng `routeId` nếu có autocomplete chọn từ danh sách route có sẵn, tránh so khớp chuỗi tự do |
| `to` | string hoặc `routeId` | có | — |
| `date` | date (`yyyy-MM-dd`) | có | — |
| `page`, `size` | int | không | phân trang kết quả |

### Response (đề xuất — cần thống nhất với backend trước khi FE code cứng theo mẫu này)

```json
{
  "status": 200,
  "message": "Search success",
  "data": {
    "content": [
      {
        "tripId": 12,
        "routeId": 3,
        "routeName": "Hà Nội - Hải Phòng",
        "startPoint": "Hà Nội",
        "endPoint": "Hải Phòng",
        "departureTime": "2026-04-10T08:00:00",
        "arrivalTime": "2026-04-10T10:30:00",
        "busPlateNumber": "29A-12345",
        "capacity": 45,
        "seatsAvailable": 12,
        "priceFrom": 150000
      }
    ],
    "totalElements": 3,
    "totalPages": 1
  },
  "timestamp": 1733728800000
}
```

**Chưa xác định được ở backend hiện tại (cần chốt trước khi implement):**
- Nguồn `priceFrom`: `Trip` entity không có field giá niêm yết, giá hiện chỉ tồn tại ở từng
  `Ticket.price` (giá theo vé đã bán) — cần model lại (giá theo Route? theo hạng ghế? cấu hình theo Trip?).
- Nguồn `seatsAvailable`: cần tính `capacity - COUNT(ticket theo tripId với status != CANCELLED)`,
  chưa có query/service nào làm việc này.

## 2. (Đề xuất) List Route để autocomplete

- **Gọi khi:** user gõ vào ô "Điểm đi"/"Điểm đến".
- **Method & Path đề xuất:** `GET /api/route?q=&page=&size=`
- **Auth đề xuất:** Public.
- **Response field tối thiểu:** `id`, `routeName`, `startPoint`, `endPoint` (map từ entity `Route`,
  xem `RouteRequestDto`/`Route.java` — field đã tồn tại ở entity, chỉ thiếu endpoint `GET`).

## Requirements liên quan tới backend

- [ ] (Blocking) Tạo `GET /api/trip/search` — không có cách nào implement trang chủ nếu thiếu API này.
- [ ] (Blocking) Tạo `GET /api/route` (list, public, có thể không cần phân trang nếu số route ít).
- [ ] Chốt mô hình giá vé (đâu là "giá niêm yết" hiển thị ở kết quả tìm kiếm) trước khi thiết kế response.
- [ ] Chốt cách tính `seatsAvailable` — tính lúc query hay lưu counter riêng (ảnh hưởng hiệu năng khi nhiều người tìm cùng lúc).
