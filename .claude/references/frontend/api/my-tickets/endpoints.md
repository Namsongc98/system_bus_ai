# Frontend API — Vé của tôi

> Màn hình: [`.claude/docs/design/my-tickets.md`](../../../../docs/design/my-tickets.md)
> Backend thật: [`references/backend/api/my-tickets/endpoints.md`](../../../backend/api/my-tickets/endpoints.md)
> Quy ước chung: [`../_conventions.md`](../_conventions.md)
> File thật: `src/pages/user/MyTickets.vue`, `src/stores/booking.js` (`useBookingStore.fetchMyTickets`), `src/services/ticketService.js`
> **Đây là màn hình được implement đầy đủ nhất ở FE trong nhóm Passenger — nhưng lỗi API bị "nuốt"
> âm thầm, xem mục 2.**

## Nút nào gọi API nào

| Nút/UI trên `MyTickets.vue` | Handler | API gọi | Trạng thái |
|---|---|---|---|
| Vào trang (`onMounted`) | `refreshTickets()` → `bookingStore.fetchMyTickets()` | `GET {API_BASE_URL_SYSTEM}/tickets/my` | ⚠️ Có gọi API nhưng lệch path — xem mục 1 |
| Đổi tab `BaseTabs` (Upcoming/Past/Cancelled) | `selectedTicketTab` ref, lọc **local** trên `myTickets.value` đã fetch sẵn — không gọi lại API | không gọi API | — (đúng thiết kế, không phải gap) |
| Click 1 `BaseTicketCard` ("view-pass"/"expand") | `handleViewPass(ticket)` → `bookingStore.currentTicket = ticket` | không gọi API, chỉ set state local | — |
| Nút "Find trips" (khi rỗng dữ liệu) | `goToTrips()` → điều hướng `ROUTE_NAMES.TRIP_VIEW` | không gọi API | — |

## 1. List vé — `GET /tickets/my`, backend chưa có endpoint tương đương

- **Service:** `ticketService.getMyTickets(params)` → `apiClient.get(API_ENDPOINTS.TICKETS.MINE, {
  params })` = `GET '/tickets/my'`.
- **Store:** `bookingStore.fetchMyTickets()` bóc `response?.data?.data ?? response?.data ?? response`,
  kỳ vọng `Array` hoặc `{ content: [...] }`.

| | FE path | Backend thật |
|---|---|---|
| Path | `/tickets/my` | *(không tồn tại — đề xuất `GET /api/ticket/me`, xem backend doc)* |

Path khác cả về số ít/nhiều (`tickets` vs `ticket`) lẫn hậu tố (`my` vs `me` được đề xuất) — **không
phải chỉ sửa số nhiều→số ít là xong**, cần backend viết endpoint mới hoàn toàn.

## 2. ⚠️ Lỗi API bị nuốt — `error.value` không được set khi fetch fail

```js
// stores/booking.js — fetchMyTickets
} catch (err) {
  error.value = null          // ← luôn reset về null, kể cả khi có lỗi thật
  myTickets.value = [...MOCK_TICKETS]
  return myTickets.value
}
```

So sánh với các store khác trong cùng codebase (`stores/admin.js`, `stores/user.js`,
`stores/trip.js`) — tất cả đều làm `error.value = err?.message || '...'` trong nhánh catch. Riêng
`fetchMyTickets` **cố tình set `error.value = null`** thay vì message lỗi thật. Hệ quả: khi API
`/tickets/my` 404 (như hiện tại, do path chưa tồn tại ở backend) hoặc khi mất kết nối, `MyTickets.vue`
render bình thường với `MOCK_TICKETS` (3 vé mẫu hardcode trong `stores/booking.js`) và **không hiển
thị banner lỗi nào** (`v-if="error"` không bao giờ true trong trường hợp này) — người dùng nhìn thấy
vé giả mà tưởng là vé thật của mình, không có tín hiệu nào cho biết API đang fail.

Đây là hành vi khác biệt so với các trang admin khác (`admin-buses-routes`, `admin-trips-management`,
`admin-revenue-reports`) — các trang đó đều hiển thị `BaseEmptyState` màu vàng cảnh báo "Showing
sample data" khi fallback. `my-tickets` không có cảnh báo tương tự dù cùng cơ chế fallback.

## 3. Sửa 1 vé — endpoint đã tồn tại nhưng không dùng ở màn này

`ticketService.js` có sẵn:
```js
cancel(id) {
  return apiClient.patch(`${API_ENDPOINTS.TICKETS.BY_ID(id)}/cancel`)  // PATCH '/tickets/{id}/cancel'
}
```
nhưng **không được gọi ở đâu trong `MyTickets.vue`** — không có nút "Cancel"/"VIEW REASON" nào được
nối trong code thật hiện tại (dù `.claude/docs/design/my-tickets.md` có mô tả nút "VIEW REASON" cho vé
Cancelled). Method HTTP cũng khác backend: FE dùng `PATCH`, backend thật dùng `PUT
/api/ticket/{tripId}` (xem [backend doc](../../../backend/api/my-tickets/endpoints.md) — path-variable
đặt tên gây nhầm, thực chất sửa theo `tripId` không phải `ticketId`).

## Requirements

- [ ] (Blocking, phía backend trước) Cần `GET /api/ticket/me` (hoặc endpoint tương đương) tồn tại —
      xem backend doc.
- [ ] (Ưu tiên cao) Sửa `catch` trong `fetchMyTickets` để set `error.value` đúng message thật thay vì
      `null` — hiện đang che giấu lỗi API, khiến QA/người dùng tưởng tính năng hoạt động bình thường.
- [ ] Nối nút "Cancel"/"VIEW REASON" (nếu giữ trong scope) vào `ticketService.cancel()`, đối chiếu lại
      method HTTP đúng với backend (`PUT`, không phải `PATCH`) sau khi backend đổi path rõ ràng hơn.
