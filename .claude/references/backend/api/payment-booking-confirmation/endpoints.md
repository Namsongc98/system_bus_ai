# API — Thanh toán + Xác nhận đặt vé

> Màn hình: [`.claude/docs/design/payment-booking-confirmation.md`](../../../../docs/design/payment-booking-confirmation.md) · Figma `2:1385`
> Quy ước chung: [`../_conventions.md`](../_conventions.md)
> Controller: `TicketController`, `TicketWebController` (`manage-revenue-ticket`, port `8082`)
> **Đây là màn có nhiều gap/nghịch lý code nhất trong 17 màn — đọc kỹ mục 3 trước khi giao việc cho FE.**

## Endpoint dùng ở màn này

| Button/Hành động UI | Method | Path | Trạng thái | Auth |
|---|---|---|---|---|
| Link "Accept" trong email xác nhận | GET | `/ticket/confirm-page?ticketId=&status=accept` | ⚠️ Đã có (server-render, lệch tham số) | Public |
| Link "Cancel" trong email xác nhận | GET | `/ticket/confirm-page?ticketId=&status=cancel` | ⚠️ Đã có (server-render, lệch tham số) | Public |
| (JS trong `confirm_landing.html` gọi ngầm — chưa xác nhận có gọi hay không) | GET | `/api/ticket/email?ticketId=&status=` | ⚠️ Đã có nhưng là stub | Public |
| (tương tự, phương án khác) | POST | `/api/ticket/confirm` | ⚠️ Đã có nhưng là stub | Public |
| Xem lại vé/QR sau khi có `ticketId` | GET | `/api/ticket/{id}` | ❌ Cần tạo mới | — |

## 1. Trang xác nhận qua email (server-render)

- **Gọi khi:** khách click nút Accept/Cancel trong email do `EmailConfirmTicketConsumer` gửi.
- **Method & Path:** `GET /ticket/confirm-page`
- **Controller:** `TicketWebController.java:12` (method `showConfirmPage`)
- **Auth:** Public (`@PublicApi`, có trong `permitAll`).
- **Trả về:** HTML template `emailConfirmTicket/confirm_landing` (server-side render, không phải JSON) — không phải REST API JSON, cần lưu ý khi FE là SPA (Vue) muốn nhúng/redirect vào flow này.

### Request (query params)

| Param | Type | Required | Ghi chú |
|---|---|---|---|
| `ticketId` | string | có | **Controller chỉ đọc `ticketId`** |
| `status` | string | có | `accept` / `cancel` |

### ⚠️ Lệch tham số — bug thật, không phải suy đoán

`EmailConfirmTicketConsumer` (bên sinh link trong email) build URL với các param:
```
tripId, status, sellerId, customerId, customerEmail, seatNumber, price, issuedAt
```
nhưng `TicketWebController.showConfirmPage` **chỉ khai báo `@RequestParam String ticketId` và
`@RequestParam String status`** — không có `ticketId` nào được gửi từ consumer (consumer gửi
`tripId`, không phải `ticketId`), và các tham số còn lại consumer gửi lên sẽ bị Spring bỏ qua vì
controller không khai báo nhận. **Kết quả thực tế: click link trong email hiện tại rất có thể lỗi
400 (thiếu required param `ticketId`)** — cần vá 1 trong 2 phía cho khớp tên tham số trước khi màn
hình này có thể hoạt động.

## 2. `GET /api/ticket/email` — stub, chưa có logic thật

- **Controller:** `TicketController.java` (`@GetMapping("/email")`)
- **Auth:** Public (`@PublicApi`).
- **Request:** `ticketId` (string), `status` (string).
- **Response (200):**
```json
{ "message": "Cập nhật trạng thái ticket thành công!" }
```
- **Không đi qua `BaseResponseDto`** (khác chuẩn envelope chung, response chỉ là `Map<String,String>` thô).
- **Nội dung xử lý thật:** không có — code chỉ `System.out.println(...)` rồi trả message tĩnh
  (comment gốc: `// 1. Logic xử lý database tại đây`). **Không cập nhật `Ticket` trong DB.**

## 3. `POST /api/ticket/confirm` — stub, chưa có logic thật

- **Controller:** `TicketController.java` (`@PostMapping("/confirm")`)
- **Auth:** Public (`@PublicApi`).
- **Request (query params, không phải JSON body):**

| Param | Type |
|---|---|
| `tripId` | string |
| `status` | string |
| `sellerId` | string |
| `customerId` | string |
| `customerEmail` | string |
| `seatNumber` | string |
| `price` | string |
| `issuedAt` | string |

- **Response (200):** `{ "message": "Cập nhật thành công" }` — cũng không đi qua `BaseResponseDto`.
- **Nội dung xử lý thật:** không có (comment gốc: `// --- BẮT ĐẦU LOGIC NGHIỆP VỤ ---`, biến
  `isSuccess = true` hard-code). **Không cập nhật `Ticket` trong DB, không kiểm tra double-submit.**

## 4. (Đề xuất) Lấy chi tiết 1 vé theo id

- **Method & Path đề xuất:** `GET /api/ticket/{id}`
- **Auth đề xuất:** cần JWT, chỉ chủ vé hoặc ADMIN mới xem được.
- **Mục đích:** render lại `Summary Card` + QR khi khách quay lại xem vé sau khi đặt — hiện hoàn toàn
  không có cách nào lấy 1 `Ticket` cụ thể qua REST API.

## Việc cần làm trước khi FE code màn này (tóm tắt ưu tiên)

- [ ] (Blocking) Chốt kiến trúc: thanh toán đồng bộ thật (cần thêm cổng thanh toán + API trả kết quả
      ngay) **hoặc** giữ mô hình đặt-trước-xác-nhận-qua-email hiện tại nhưng phải vá lại toàn bộ luồng
      (mục 5-7 dưới).
- [ ] (Blocking) Sửa `EmailConfirmTicketConsumer` và `TicketWebController` dùng chung 1 bộ tên tham số.
- [ ] (Blocking) Viết logic thật cho `/api/ticket/email` và `/api/ticket/confirm` (hiện là code giả),
      bao gồm: tìm ticket, chặn xử lý 2 lần, cập nhật `TicketStatus`.
- [ ] (Blocking) Đổi 2 endpoint trên sang dùng `BaseResponseDto` cho nhất quán với toàn hệ thống.
- [ ] (Blocking) Tạo `GET /api/ticket/{id}` để render lại Summary Card/QR.
- [ ] Cân nhắc đổi `POST /api/ticket/confirm` từ query param sang JSON body — hiện đang nhận 8 param
      rời rạc qua URL, dễ vượt giới hạn độ dài URL và lộ dữ liệu (`customerEmail`, `price`) trong access log.
