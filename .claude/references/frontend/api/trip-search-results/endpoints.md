# Frontend API — Trang chủ tìm chuyến + Kết quả

> Màn hình: [`.claude/docs/design/trip-search-results.md`](../../../../docs/design/trip-search-results.md)
> Backend thật: [`references/backend/api/trip-search-results/endpoints.md`](../../../backend/api/trip-search-results/endpoints.md)
> Quy ước chung: [`../_conventions.md`](../_conventions.md)
> File thật: `src/pages/user/TripView.vue`, `src/services/tripService.js` (có hàm `search` nhưng
> **không được gọi ở đâu cả** — xem mục 1)
> **Màn này hiện KHÔNG gọi bất kỳ API nào — toàn bộ dữ liệu hiển thị là hardcode.**

## Nút nào gọi API nào

| Nút/UI trên `TripView.vue` | Handler | API gọi | Trạng thái |
|---|---|---|---|
| Nút "Search" trong `BaseSearchForm` | `@search="() => {}"` — **no-op rỗng, literally không làm gì** | không gọi API | ❌ Chưa nối |
| Nút "Reset" trong `BaseSearchForm` | `@reset="() => {}"` — no-op rỗng | không gọi API | ❌ Chưa nối |
| `BaseSortFilter` "Sort by" | `sortBy` ref local, `@update:model-value` chỉ set ref, không re-sort/re-fetch | không gọi API | ❌ Chưa nối |
| Click 1 `BaseTripCard` | `handleSelectTrip(trip)` → `router.push({ name: SEAT_VIEW, params: { tripId: trip.id } })` | không gọi API, chỉ điều hướng | — |
| Danh sách chuyến hiển thị | `trips = ref(TRIP_VIEW_FALLBACK_TRIPS)` — hardcode từ `src/constants/user/tripView.js`, không đổi theo search | không gọi API | ❌ Luôn là dữ liệu mẫu |

## 1. Tìm chuyến — chưa nối, dù service đã viết sẵn

`tripService.js` đã có sẵn hàm:
```js
search(params) {
  return apiClient.get(API_ENDPOINTS.TRIPS.SEARCH, { params })  // GET '/trips/search'
}
```
nhưng **`TripView.vue` không import `tripService` ở đâu cả** — hàm `search()` tồn tại trong code
nhưng chết (dead code), không được gọi từ bất kỳ page nào trong 17 màn đã review. `@search` handler
của `BaseSearchForm` là `() => {}` — khi implement thật, cần gọi `tripService.search({from, to, date})`
từ đây.

### Nếu nối vào — so với backend thật

Backend **hoàn toàn chưa có** `GET /api/trip/search` (chỉ là đề xuất, xem
[backend doc](../../../backend/api/trip-search-results/endpoints.md)) — nên dù FE có nối
`tripService.search()` vào `@search` handler ngay bây giờ, request vẫn sẽ 404 cho tới khi backend
viết endpoint này. Đây là màn hình **bị chặn ở cả 2 phía**: FE chưa nối handler, backend chưa có API.

| | FE path (`API_ENDPOINTS.TRIPS.SEARCH`) | Backend đề xuất |
|---|---|---|
| Path | `/trips/search` | `/api/trip/search` (đề xuất, chưa tồn tại) |

Cũng lệch số ít/số nhiều như toàn bộ domain Trip (xem `../_conventions.md` mục 5).

## 2. Autocomplete "Điểm đi"/"Điểm đến" — chưa có ở FE lẫn backend

Không có component autocomplete nào được nối trong `TripView.vue` hiện tại — ô "Điểm đi"/"Điểm đến"
nằm trong `BaseSearchForm` (chưa đọc chi tiết component này, nhưng `TripView.vue` không truyền prop
danh sách route nào vào). Backend cũng chưa có `GET /api/route` (list) — xem
[backend doc](../../../backend/api/trip-search-results/endpoints.md) mục 2 và
[`admin-buses-routes`](../admin-buses-routes/endpoints.md).

## Requirements

- [ ] (Blocking) Nối `tripService.search()` vào `@search` handler của `BaseSearchForm` — hiện là
      no-op hoàn toàn, không phải chỉ sai path.
- [ ] (Blocking, phía backend) Cần `GET /api/trip/search` và `GET /api/route` tồn tại trước khi màn
      này có thể hoạt động thật — xem yêu cầu chi tiết ở backend doc.
- [ ] Sau khi nối, đổi `from`/`to` hiển thị ở header kết quả (`AVAILABLE JOURNEYS`) từ hardcode
      `'Hà Nội'`/`'Hải Phòng'` sang giá trị thật từ kết quả search (đã có `TODO` comment sẵn trong code).
