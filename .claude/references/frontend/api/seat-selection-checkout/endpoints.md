# Frontend API — Chọn ghế + Nhập thông tin hành khách

> Màn hình: [`.claude/docs/design/seat-selection-checkout.md`](../../../../docs/design/seat-selection-checkout.md)
> Backend thật: [`references/backend/api/seat-selection-checkout/endpoints.md`](../../../backend/api/seat-selection-checkout/endpoints.md)
> Quy ước chung: [`../_conventions.md`](../_conventions.md)
> File thật: `src/pages/user/SeatView.vue`, `src/stores/seat.js` (toàn bộ placeholder), `src/services/bookingService.js`
> **Màn này hiện KHÔNG tạo booking thật khi bấm submit — xem mục 2, đây là gap nghiêm trọng nhất trong
> luồng đặt vé khách hàng.**

## Nút nào gọi API nào

| Nút/UI trên `SeatView.vue` | Handler | API gọi | Trạng thái |
|---|---|---|---|
| Chọn ghế trên `BaseMapCar` | `@select="(seat) => { /* TODO: seatStore.selectSeat(seat) */ }"` — comment TODO, thân hàm rỗng | không gọi API, **không cả set state local** | ❌ Chưa nối |
| Nút submit trong `BaseSavePaymentForm` (checkout form) | `@submit="isQrModalOpen = true"` | **không gọi bất kỳ API nào** | ❌ Chưa nối — xem mục 2 |

## 1. Sơ đồ ghế — dữ liệu hardcode, `seatStore.fetchByTrip` là placeholder rỗng

```js
// src/stores/seat.js
async function fetchByTrip(tripId) {
  /* placeholder */
}
```
`SeatView.vue` không gọi `fetchByTrip` ở `onMounted` hay bất kỳ đâu — ghế hiển thị lấy thẳng từ
`SEAT_VIEW_FAKE_SEATS` (constant, `src/constants/user/seatView.js`), độc lập với `tripId` thật sự
được điều hướng tới từ `trip-search-results`. `seatService.getByTrip(tripId)` (
`GET /trips/{tripId}/seats`) đã viết sẵn trong `services/seatService.js` nhưng **không được gọi ở
đâu trong toàn bộ codebase đã review**.

Backend **không có khái niệm "Seat" là entity riêng** — ghế chỉ là field `seatNumber` (Integer) trên
`Ticket` (xem `../_conventions.md` mục 5) — nên dù có nối `seatService.getByTrip`, endpoint
`GET /api/trip/{tripId}/seats` **không tồn tại và không có hướng tương đương rõ ràng** ở backend
hiện tại (cần thiết kế lại: có thể là "danh sách ghế đã bán cho 1 Trip" suy ra từ
`COUNT(Ticket WHERE tripId=X AND status != CANCELLED)`, tương tự gap `seatsAvailable` đã nêu ở
[`trip-search-results` (backend doc)](../../../backend/api/trip-search-results/endpoints.md)).

## 2. Submit checkout — KHÔNG tạo booking, chỉ mở popup thành công giả

```js
// SeatView.vue
@submit="isQrModalOpen = true"
```

Đây là toàn bộ logic submit thật của nút checkout: nhận sự kiện `@submit` từ `BaseSavePaymentForm`
(payload `{ fullName, phone, email }`) rồi **chỉ mở modal `QRConfirmPopup`**, không gọi
`bookingService.createBooking()`, không gọi bất kỳ store/service nào khác. `bookingService.js`
đã viết đầy đủ:

```js
// src/services/bookingService.js — tồn tại, hoạt động đúng nếu được gọi, nhưng KHÔNG được gọi ở đây
export const createBooking = async (payload) => {
  const res = await apiClient.post(API_ENDPOINTS.BOOKING.BASE, payload)  // POST '/booking' → Kong → Booking Service
  return res.data
}
```

**Kết quả thực tế:** người dùng điền form, bấm submit, thấy "Booking Confirmed!" (từ
`QRConfirmPopup`, xem [`payment-booking-confirmation`](../payment-booking-confirmation/endpoints.md))
— nhưng **không có request nào được gửi lên backend, không có Ticket/Booking nào được tạo**. Đây
không phải vấn đề path/port như các màn khác — nút "submit" hiện tại không gọi API ở lớp nào cả.

### Nếu nối `createBooking` — so với backend thật

Path thật ra **khớp đúng** (khác với hầu hết domain khác):

| | FE (`API_ENDPOINTS.BOOKING.BASE`) | Backend thật |
|---|---|---|
| Client | `apiClient` — base URL chung `API_BASE_URL_SYSTEM` (Kong) | module `booking_ticket`, Kong route `/api/booking` → port `8081` |
| Path | `/booking` | `/api/booking` |

→ Chỉ cần set `VITE_KONG_API_URL=http://localhost:8000/api` và nối lại `@submit`
handler để gọi `createBooking(payload)`, path đã khớp sẵn.

**Payload cần build lại cho đúng `BookingController` thật** (xem
[backend doc](../../../backend/api/seat-selection-checkout/endpoints.md)): backend cần
`{ tripId, sellerId, customerId, customerEmail, status, seatNumber, price, issuedAt }`, trong khi
`BaseSavePaymentForm` hiện chỉ emit `{ fullName, phone, email }` — thiếu `tripId` (phải lấy từ route
param, xem TODO comment sẵn trong `SeatView.vue`), thiếu `seatNumber` (phải từ `seatStore.selectedSeat`
— hiện cũng chưa nối, xem mục 1), thiếu `price` (chưa có nguồn giá chuẩn ở cả 2 phía — xem gap
`priceFrom` ở [`trip-search-results` backend doc](../../../backend/api/trip-search-results/endpoints.md)),
và `customerId` **không nên do FE gửi** (backend nên tự lấy từ JWT — xem cảnh báo bảo mật ở backend
doc).

## Requirements

- [ ] (Blocking, mức độ cao nhất trong 17 màn) Nối `@submit` handler thật sự gọi
      `bookingService.createBooking(payload)` thay vì chỉ mở modal — hiện tại luồng đặt vé khách hàng
      **không tạo bất kỳ dữ liệu nào ở backend**.
- [ ] Nối `seatStore.selectSeat`/`fetchByTrip` — hiện cả 2 đều là TODO/placeholder rỗng.
- [ ] Set đúng `VITE_KONG_API_URL=http://localhost:8000/api` (Kong).
- [ ] (Blocking, phía backend) `RevenueConsumer` phải thực sự gọi `ticketService.createTicket(...)` —
      xem [backend doc](../../../backend/api/seat-selection-checkout/endpoints.md) — nếu không, dù FE
      nối đúng, `Ticket` vẫn không được lưu vào DB sau khi Kafka nhận message.
