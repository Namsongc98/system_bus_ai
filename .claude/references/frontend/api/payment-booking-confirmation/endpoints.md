# Frontend API — Thanh toán + Xác nhận đặt vé

> Màn hình: [`.claude/docs/design/payment-booking-confirmation.md`](../../../../docs/design/payment-booking-confirmation.md)
> Backend thật: [`references/backend/api/payment-booking-confirmation/endpoints.md`](../../../backend/api/payment-booking-confirmation/endpoints.md)
> Quy ước chung: [`../_conventions.md`](../_conventions.md)
> File thật: `src/pages/user/QRConfirmPopup.vue` (mở từ `SeatView.vue`, xem
> [`seat-selection-checkout`](../seat-selection-checkout/endpoints.md)), `src/services/paymentService.js`
> **Popup này 100% hiển thị dữ liệu tĩnh — không gọi bất kỳ API nào khi mở.**

## Nút nào gọi API nào

| Nút/UI trên `QRConfirmPopup.vue` | Handler | API gọi | Trạng thái |
|---|---|---|---|
| Mở popup (khi `SeatView.vue` set `isQrModalOpen = true`) | không có hook `onMounted`/`watch` nào gọi API | không gọi API | ❌ Toàn bộ nội dung hardcode |
| Nút **"View My Tickets"** | `viewTickets()` → đóng popup, `router.push({ name: ROUTE_NAMES.PROFILE })` | không gọi API, chỉ điều hướng | — |
| Nút **"Download Receipt"** | `downloadReceipt()` → `emit('download-receipt')` | không gọi API, và **`SeatView.vue` không lắng nghe `@download-receipt`** trên `<QRConfirmPopup>` | ❌ Emit vào khoảng không, không có gì xảy ra khi bấm |
| Icon X / click ngoài modal | `close()` → `emit('update:modelValue', false)` | không gọi API | — |

## 1. Dữ liệu hiển thị trong popup — hoàn toàn hardcode từ `SeatView.vue`

```html
<!-- SeatView.vue -->
<QRConfirmPopup v-model="isQrModalOpen" ticket-id="FV-2024-X92L" />
```

- `ticket-id` truyền cứng chuỗi `"FV-2024-X92L"` — không phải ticket vừa tạo (vì thực tế **chưa có
  ticket nào được tạo**, xem [`seat-selection-checkout`](../seat-selection-checkout/endpoints.md) mục 2).
- `qrCodeUrl` **không được truyền** (prop có default `''`) → `QRConfirmPopup.vue` render `<div
  v-else>` (khối xám placeholder) thay vì ảnh QR thật.
- Không có gọi `paymentService.getQRCode(ticketId)` ở đâu trong luồng này dù hàm đã viết sẵn trong
  `services/paymentService.js`:
  ```js
  getQRCode(ticketId) {
    return apiClient.get(API_ENDPOINTS.PAYMENTS.QR(ticketId))  // GET '/payments/{ticketId}/qr'
  }
  ```

### Nếu nối lại — backend không có domain "Payment" riêng

Backend **không có `PaymentController`/entity `Payment`** — QR code, xác nhận thanh toán hiện tại đi
qua luồng khác hẳn ở backend thật: server-render HTML (`GET /ticket/confirm-page`) từ link trong
email do `EmailConfirmTicketConsumer` gửi, **không phải REST JSON API cho SPA gọi** (xem chi tiết đầy
đủ ở [backend doc](../../../backend/api/payment-booking-confirmation/endpoints.md) — đây là màn có
nhiều gap/nghịch lý nhất ở phía backend: 2 endpoint `/api/ticket/email` và `/api/ticket/confirm` đều
là code giả, chưa cập nhật DB thật).

| Domain FE gọi | Path FE | Có tương đương ở backend? |
|---|---|---|
| `paymentService.getQRCode` | `/payments/{ticketId}/qr` | ❌ Không có |
| `paymentService.confirmPayment` | `POST /payments/{id}/confirm` | ❌ Không có (gần nhất là `POST /api/ticket/confirm`, nhưng nhận query param khác hẳn và là code giả) |
| `paymentService.getById` | `/payments/{id}` | ❌ Không có |

**Kết luận:** đây là domain lệch mô hình dữ liệu (không chỉ lệch path) — trước khi nối API thật cho
popup này, cần chốt kiến trúc thanh toán với backend (đồng bộ thật qua cổng thanh toán, hay giữ mô
hình đặt-trước-xác-nhận-qua-email hiện tại) như đã nêu ở backend doc mục "Việc cần làm trước khi FE
code màn này".

## 2. Nút "Download Receipt" — emit rơi vào khoảng không

`downloadReceipt()` chỉ `emit('download-receipt')` lên component cha — nhưng `SeatView.vue` (nơi
render `<QRConfirmPopup>`) không có `@download-receipt="..."` trên thẻ này. Không có lỗi runtime
(emit không ai lắng nghe thì không làm gì), nhưng về mặt UX nút này **hoàn toàn không phản hồi** khi
bấm.

## Requirements

- [ ] (Blocking, phía backend trước) Chốt kiến trúc thanh toán/xác nhận — xem backend doc — trước khi
      thiết kế lại luồng gọi API cho popup này.
- [ ] Nối `@download-receipt` ở `SeatView.vue`, hoặc bỏ nút nếu chưa có tính năng xuất receipt.
- [ ] Truyền `qrCodeUrl` thật (từ response tạo booking/ticket) thay vì để trống — hiện luôn hiển thị
      khối xám placeholder.
- [ ] `ticket-id="FV-2024-X92L"` cần thay bằng ID thật trả về sau khi `createBooking`/`createTicket`
      thành công — phụ thuộc vào việc nối API ở [`seat-selection-checkout`](../seat-selection-checkout/endpoints.md)
      trước.
