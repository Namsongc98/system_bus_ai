# API — Chọn ghế + Nhập thông tin hành khách

> Màn hình: [`.claude/docs/design/seat-selection-checkout.md`](../../../../docs/design/seat-selection-checkout.md) · Figma `2:1179`
> Quy ước chung: [`../_conventions.md`](../_conventions.md)
> Controller: `BookingController` (`booking_ticket`, port **`8081`** — khác port với phần lớn API khác)

## Endpoint dùng ở màn này

| Button/Hành động UI | Method | Path | Trạng thái | Auth |
|---|---|---|---|---|
| Nút submit trong "Checkout Form" | POST | `/api/booking` | ⚠️ Đã có (chưa hoàn chỉnh) | Cần JWT hợp lệ (không public — không có trong `permitAll`) |
| Chọn/bỏ chọn ghế trên sơ đồ | — | không gọi API | — | chỉ đổi state UI, ghế chỉ thật sự "giữ" khi submit |

## 1. Tạo booking (submit form checkout)

- **Gọi khi:** user đã chọn ghế + điền Full Name/Phone/Email, bấm nút submit.
- **Method & Path:** `POST /api/booking`
- **Controller:** `BookingController.java:16` (method `addTicket`)
- **Auth:** theo `SecurityConfig`, path này **không** nằm trong `permitAll` → cần `Authorization: Bearer <token>` hợp lệ. (Nếu nghiệp vụ cho phép khách "đặt vé không cần tài khoản", đây là gap cần xử lý — hiện bắt buộc phải đăng nhập trước khi đặt vé theo cấu hình security hiện tại.)

### Request

```json
{
  "tripId": 12,
  "sellerId": null,
  "customerId": 7,
  "customerEmail": "john@example.com",
  "status": "PENDING",
  "seatNumber": 15,
  "price": 150000,
  "issuedAt": "2026-04-09T14:30:00"
}
```

| Field | Type | Required (đề xuất) | Map UI |
|---|---|---|---|
| `tripId` | Long | có | truyền ngầm từ bước chọn chuyến trước đó |
| `sellerId` | Long | không (null khi khách tự đặt online) | **chưa rõ nghiệp vụ** — cần xác nhận giá trị khi không qua nhân viên bán vé |
| `customerId` | Long | có nếu đã đăng nhập | lấy từ JWT (`request.getAttribute("id")`), **không nên để FE tự gửi** — cần backend tự lấy từ token thay vì tin request body (đúng theo rule ở `references/backend/rules/security.md`: "Do not trust client-provided ... customer id") |
| `customerEmail` | string | có | field "Email" trên form |
| `status` | string | có | giá trị hợp lệ theo enum `TicketStatus`: `NOT_BOOKED`, `PENDING`, `CANCELLED`, `SUCCESS` — FE nên gửi `PENDING` |
| `seatNumber` | Integer | có | ghế được chọn trên sơ đồ |
| `price` | BigDecimal | có | **chưa có nguồn giá chuẩn ở backend** — xem gap ở `trip-search-results/endpoints.md` |
| `issuedAt` | LocalDateTime | có | thời điểm submit |

### Response (200)

```json
{
  "status": null
}
```

`BookingController.addTicket` là method `void` — **HTTP 200 nhưng body rỗng, không trả `ticketId` hay
bất kỳ dữ liệu nào**. FE không có cách nào biết booking có được tạo/xử lý thành công ở tầng dữ liệu
hay chưa — request chỉ xác nhận "đã đẩy vào Kafka", không xác nhận "đã lưu Ticket".

### Business logic phía sau (không phải API riêng, nhưng ảnh hưởng trực tiếp tới màn hình sau)

1. `BookingProducer.sendBookingEvent` đẩy message vào Kafka topic **`order-events`**.
2. 2 consumer lắng nghe:
   - `RevenueConsumer` (group `booking-group`) — **hiện chỉ log, KHÔNG gọi `ticketService.createTicket`**,
     nghĩa là **`Ticket` chưa thực sự được lưu vào DB** sau bước này. Xem chi tiết + hướng xử lý ở
     [`payment-booking-confirmation/endpoints.md`](../payment-booking-confirmation/endpoints.md).
   - `EmailConfirmTicketConsumer` (group `email-service-group`) — gửi email xác nhận, không đụng DB.

### Lỗi có thể gặp

| Status | Khi nào |
|---|---|
| 401 | thiếu/sai JWT |
| — | **không có 400 validate rõ ràng** — `BookingController` không có `@Valid`, không kiểm tra `seatNumber` có hợp lệ/còn trống hay không trước khi đẩy Kafka |

## Requirements liên quan tới backend

- [ ] (Blocking) `RevenueConsumer` phải thực sự gọi `ticketService.createTicket(...)` khi nhận message.
- [ ] (Blocking) `customerId`/`sellerId` phải lấy từ JWT (`request.getAttribute("id")`), không nhận từ body.
- [ ] (Blocking) Thêm validate `seatNumber` còn trống tại thời điểm submit (khoá ghế tạm thời, tránh bán trùng).
- [ ] Đổi `BookingController.addTicket` trả về ít nhất `{ "accepted": true }` hoặc 1 mã theo dõi tạm
      thời, để FE có gì đó hiển thị trong lúc chờ xác nhận qua email/Kafka.
- [ ] Xác nhận `POST /api/booking` có bắt buộc đăng nhập hay cho phép khách vãng lai (guest checkout).
