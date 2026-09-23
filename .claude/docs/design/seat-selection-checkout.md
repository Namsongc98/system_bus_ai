# Màn hình: Chọn ghế + Nhập thông tin hành khách

> Figma: node-id `2:1179` (tên frame: "Seat Selection") — file "Ticket-Buses" (`fileKey=QgeicQW2IuhLakGxpsQnr1`)
> Nhóm: Passenger/Public UI
> Slug: `seat-selection-checkout`

## 1. Tổng quan

Màn hình chọn ghế trên sơ đồ xe (bus map) kết hợp form nhập thông tin hành khách (Full Name, Phone,
Email) và tóm tắt giá bên panel phải. Đây là bước ngay trước khi tạo booking.

## 2. Basic Design

- Sticky header: nút back + tiêu đề chuyến.
- `Main` chia 2 cột:
  - `Left Side: Bus Visualization` — sơ đồ ghế (Driver section, Legend, Seat Grid nhiều hàng, ghế
    có trạng thái `ACTIVE SEAT` khi được chọn).
  - `Right Side: Side Panel` — `Selection Card` (tóm tắt ghế đã chọn) + `Checkout Form` (Full Name,
    Phone, Email) + nút submit + `Promo Banner`.
- `Footer` dùng chung toàn site.

## 3. Detail Design

| Field/Control | Loại | Placeholder (Figma) | Validate (đề xuất) |
|---|---|---|---|
| Sơ đồ ghế | interactive grid | — | mỗi ghế có state: trống / đã chọn / đã bán (disable) |
| Full Name | text | "John Doe" | required |
| Phone Number | text | "+84 000 000 000" | required, format số điện thoại VN |
| Email | text | "john@example.com" | required, format email — map trực tiếp `TicketRequestDto.customerEmail` |
| Nút submit (Checkout) | button | trong `Checkout Form` | disable nếu chưa chọn ghế hoặc form invalid |

**States:** chưa chọn ghế (nút submit disable), đã chọn 1+ ghế (Selection Card cập nhật giá), ghế đã
bán (không click được), loading khi submit, lỗi khi ghế vừa bị người khác đặt trước (race condition
— xem mục Business Logic).

## 4. Business Logic

1. User chọn 1 (hoặc nhiều) ghế trống trên sơ đồ → `Selection Card` cập nhật tổng tiền.
2. User nhập Full Name / Phone / Email.
3. Submit → build `TicketRequestDto` (`tripId`, `seatNumber`, `customerEmail`, `price`, …) → gọi
   `POST /api/booking`.
4. `BookingController.addTicket` **không lưu DB ngay** — chỉ đẩy message vào Kafka topic
   `order-events` qua `BookingProducer` (fire-and-forget, response 200 ngay cả khi consumer chưa xử
   lý xong).
5. Có 2 consumer lắng nghe `order-events`:
   - `RevenueConsumer` (group `booking-group`): hiện **chỉ log ra console**, chưa thực sự tạo bản ghi
     `Ticket` trong DB (`ticketService.createTicket` KHÔNG được gọi ở đây) — **gap nghiệp vụ quan
     trọng**.
   - `EmailConfirmTicketConsumer` (group `email-service-group`): gửi email xác nhận cho khách với 2
     link Accept/Cancel trỏ tới `GET /ticket/confirm-page`.
6. **Race condition ghế trống chưa được xử lý ở tầng nào** trong code hiện tại (không thấy lock ghế
   theo `tripId + seatNumber` trước khi 2 khách cùng chọn 1 ghế) — cần bổ sung trước khi go-live.

## 5. API

| Method | Path | Trạng thái | Request | Response | Nguồn |
|---|---|---|---|---|---|
| POST | `/api/booking` | Đã có (nhưng chưa hoàn chỉnh) | `TicketRequestDto` (`tripId`, `sellerId`, `customerId`, `customerEmail`, `status`, `seatNumber`, `price`, `issuedAt`) | `void` (200 OK, không trả dữ liệu) | `BookingController.java:16` |

**Gap:** response rỗng nên FE không có `ticketId`/trạng thái để hiển thị ngay — nếu muốn có màn
"Payment Booking Confirmation" tức thời (không phải chờ email), cần API trả về đồng bộ hơn hoặc
WebSocket/polling theo `tripId + seatNumber` để biết trạng thái booking.

## 6. Requirements

- [ ] (Blocking) Xử lý khoá ghế tạm thời (seat lock) khi 1 khách đang checkout, tránh bán trùng ghế.
- [ ] (Blocking) `RevenueConsumer` phải thực sự tạo `Ticket` (status `PENDING`) trong DB khi nhận
      message từ `order-events`, hiện chỉ log.
- [ ] Validate `seatNumber` được chọn thực sự còn trống tại thời điểm submit (double-check server-side,
      không tin tưởng hoàn toàn state client).
- [ ] Hiển thị lỗi rõ khi ghế vừa bị người khác đặt mất trong lúc mình đang điền form.
- [ ] (TODO/needs confirmation) `sellerId`/`customerId` trong `TicketRequestDto` lấy từ đâu khi khách
      tự đặt online (không qua nhân viên bán vé)?
