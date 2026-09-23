# Frontend API — Quản lý Xe & Tuyến đường

> Màn hình: [`.claude/docs/design/admin-buses-routes.md`](../../../../docs/design/admin-buses-routes.md)
>
> **Cập nhật task 0.2 (2026-09-21):** `API_ENDPOINTS` đã đổi `/buses`→`/bus`, `/routes`→`/route`, `/trips`→`/trip` (`BASE`, `BY_ID`), `/tickets`→`/ticket` (`BASE`). Các bảng "FE hiện tại" bên dưới ghi path **trước** 0.2; lỗi lệch số ít/nhiều đã hết, lỗi thiếu endpoint BE vẫn còn (giờ trả 405 thay vì 404). Xem `.claude/docs/review/0.2-api-endpoints.md`.
>
> Backend thật: [`references/backend/api/admin-buses-routes/endpoints.md`](../../../backend/api/admin-buses-routes/endpoints.md)
> Quy ước chung: [`../_conventions.md`](../_conventions.md)
> File thật: `src/pages/admin/BusesRoutes.vue`, `src/services/busRouteService.js` (`busService`, `routeService`)
> Modal liên quan: [`admin-create-bus-modal`](../admin-create-bus-modal/endpoints.md),
> [`admin-create-route-modal`](../admin-create-route-modal/endpoints.md),
> [`admin-delete-confirmation`](../admin-delete-confirmation/endpoints.md)

## Nút nào gọi API nào

| Nút/UI trên `BusesRoutes.vue` | Handler | API gọi | Trạng thái |
|---|---|---|---|
| Vào trang (`onMounted`) | `fetchFleetNetwork()` → `Promise.allSettled([busService.getAll(), routeService.getAll()])` | `GET /buses`, `GET /routes` | ⚠️ Có gọi nhưng lệch path (số ít/nhiều) |
| Nút **"Add New Bus"** | `openCreateBusModal()` → mở `ModalCreateBus` | xem [`admin-create-bus-modal`](../admin-create-bus-modal/endpoints.md) | — |
| Nút **"Add Route"** | `openCreateRouteModal()` → mở `ModalCreateRoute` | xem [`admin-create-route-modal`](../admin-create-route-modal/endpoints.md) | — |
| Click 1 `RouteNetworkCard` | `selectRoute(route)` → toggle `selectedRouteId` local | không gọi API | — |
| Icon xoá trên `RouteNetworkCard` (`@delete`) | `openDeleteRouteModal(route)` → mở `ModalDeleteRoute` | xem [`admin-delete-confirmation`](../admin-delete-confirmation/endpoints.md) | — |
| Card "+" cuối grid Bus (`is-add-card`) | không có `@click` riêng thấy trong code đọc được — cùng nhóm với "Add New Bus" | không gọi API | — |
| Không có nút xoá/sửa nào trên `FleetBusCard` | — | — | ❌ UI list Bus chỉ đọc, không có edit/delete card-level dù backend đã có `PUT /api/bus/{id}` |

## 1. List Bus / List Route — lệch path số ít/nhiều

```js
busService.getAll()   // GET '/buses'   — busRouteService.js
routeService.getAll() // GET '/routes'
```

| Domain | FE path | Backend thật |
|---|---|---|
| Bus | `/buses` | `/api/bus?page=&size=` |
| Route | `/routes` | ❌ **không tồn tại ở backend** — chỉ có `POST`/`PUT` route, chưa có `GET` list (xem backend doc mục 7) |

**Route đặc biệt nghiêm trọng hơn Bus:** kể cả sau khi sửa path đúng số ít, `GET /api/route` vẫn
**không tồn tại** ở backend — không chỉ là vấn đề đặt tên, mà là API chưa được viết. Cột "Routes
Network" (`RouteNetworkCard` list) sẽ luôn rơi vào `useFallback()` (dữ liệu mẫu
`BUSES_ROUTES_FALLBACK_ROUTES`) cho tới khi backend bổ sung endpoint này.

### Cách trang xử lý khi 1 trong 2 API fail

```js
const [busResult, routeResult] = await Promise.allSettled([...])
if (nextBuses.length || nextRoutes.length) {
  // giữ phần thật, fallback phần rỗng, hiển thị banner vàng "Some fleet data is unavailable"
} else {
  useFallback('Fleet APIs returned no records. Showing sample fleet network data.')
}
```
Xử lý per-domain khá tốt (Bus có thể hiển thị thật trong khi Route vẫn fallback) — không phải gap ở
tầng FE, chỉ cần backend bổ sung `GET /api/route`.

## 2. Xoá Bus — không có UI, dù đã có kế hoạch xoá Route

`FleetBusCard` không emit sự kiện xoá nào (khác `RouteNetworkCard` đã có `@delete`) — chưa có
`ModalDeleteBus` tương đương `ModalDeleteRoute`. Backend cũng **chưa có `DELETE /api/bus/{id}`** (xem
backend doc mục 4) — 2 phía đang đồng bộ ở trạng thái "chưa làm", không có gap lệch nhau riêng ở đây.

## Requirements

- [x] Sửa `API_ENDPOINTS.BUSES.BASE`/`ROUTES.BASE` từ `/buses`/`/routes` sang `/bus`/`/route` (số ít)
      để khớp backend — xem [`../_conventions.md`](../_conventions.md#5-đường-dẫn-path--lệch-số-ítsố-nhiều-gần-như-toàn-bộ-hệ-thống).
- [ ] (Blocking, phía backend) Cần `GET /api/route` (list) trước khi cột Route hoạt động thật — xem
      backend doc mục 7 (dùng chung phát hiện với `admin-create-trip-modal`, `trip-search-results`).
- [ ] Thêm UI xoá Bus (card-level) nếu giữ trong scope — hiện chưa có ở cả FE lẫn backend.
- [ ] Set đúng `VITE_KONG_API_URL` (`http://localhost:8000/api`, qua Kong).
