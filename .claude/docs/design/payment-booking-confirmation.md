# Màn hình: Thanh toán + Xác nhận đặt vé

> Figma: node-id `2:1385` (tên frame: "Payment Booking Confirmation") — file "Ticket-Buses" (`fileKey=QgeicQW2IuhLakGxpsQnr1`)
> Nhóm: Passenger/Public UI
> Slug: `payment-booking-confirmation`

## 1. Tổng quan

Bước cuối luồng đặt vé: hiển thị `Progress Indicator` (3 bước), `Summary Card` (thông tin chuyến +
hành khách + price breakdown), và một `Success Modal Overlay` có QR code placeholder khi đặt vé
thành công.

## 2. Basic Design

- `Progress Indicator`: 3 mốc (khả năng: Seat → Payment → Confirmation).
- `Summary Card`:
  - `Ticket Header` (gradient) — tiêu đề vé.
  - `Details Body` gồm 3 khối: `Journey Info` (ngày giờ khởi hành), `Passenger Info` (tên hành
    khách, ghế), `Price Breakdown`.
- `Footer` dùng chung.
- `Success Modal Overlay`: hiện sau khi thanh toán/xác nhận thành công — có `Checkmark Animation`,
  heading, `QR Code Placeholder`, 2 nút hành động (khả năng: Tải vé / Về trang chủ).

## 3. Detail Design

| Field | Nội dung mẫu (Figma) |
|---|---|
| Departure Date | "April 10, 2024" |
| Departure Time | "08:00 AM" |
| Passenger | "Nguyễn Văn A" |
| Seat Assignment | (text, giá trị cụ thể chưa đọc được) |
| QR Code | placeholder — cần sinh mã QR thật chứa `ticketId` để soát vé |

**States:** đang chờ xác nhận thanh toán (loading), thành công (mở Success Modal), thất bại (chưa có
thiết kế riêng trong Figma — cần bổ sung).

## 4. Business Logic

Đây là điểm cần làm rõ nhất trong toàn bộ luồng đặt vé, vì code backend hiện tại cho thấy **2 luồng
xác nhận khác nhau, chưa thống nhất**:

1. **Luồng "hiển thị ngay" (theo Figma):** sau khi submit ở `seat-selection-checkout`, FE có thể kỳ
   vọng thấy `Success Modal` ngay lập tức — nhưng `POST /api/booking` trả `void`, không có dữ liệu
   để confirm ngay, và `RevenueConsumer` (xử lý Kafka) hiện chưa lưu Ticket vào DB.
2. **Luồng "xác nhận qua email" (theo code):** `EmailConfirmTicketConsumer` gửi email cho khách với
   2 link Accept/Cancel trỏ `GET /ticket/confirm-page?ticketId=&status=` (server-render HTML,
   `TicketWebController`), sau đó trang đó gọi `POST /api/ticket/confirm` hoặc `GET /api/ticket/email`
   để cập nhật trạng thái — nhưng cả 2 endpoint này hiện là code giả lập (`// Giả lập xử lý thành
   công`, không có logic DB thật), và tên tham số không khớp: consumer build URL với `tripId`,
   `sellerId`, `customerId`... nhưng `TicketWebController.showConfirmPage` chỉ đọc `ticketId` và
   `status` — 2 bên đang lệch tham số.

**Kết luận:** cần chốt với team 1 trong 2 mô hình trước khi code FE cho màn hình này:
- (A) Thanh toán online tức thời (cần tích hợp cổng thanh toán thật + API đồng bộ trả về kết quả),
  hoặc
- (B) Đặt chỗ trước, xác nhận qua email trong X phút (giữ luồng Kafka + email hiện tại, nhưng phải
  vá lại consumer để lưu Ticket, và sửa `TicketWebController`/`/api/ticket/confirm` cho khớp tham số).

## 5. API

| Method | Path | Trạng thái | Ghi chú |
|---|---|---|---|
| POST | `/api/booking` | Đã có (chưa hoàn chỉnh) | Xem `seat-selection-checkout.md` — không trả dữ liệu để hiển thị confirmation ngay |
| GET | `/ticket/confirm-page` | Đã có (server-render, chưa hoàn chỉnh) | `TicketWebController` — chỉ nhận `ticketId`, `status`; lệch với tham số do `EmailConfirmTicketConsumer` build |
| GET | `/api/ticket/email` | Đã có nhưng là stub | Chỉ log + trả message tĩnh, chưa cập nhật DB (`TicketController.java` dòng `@GetMapping("/email")`) |
| POST | `/api/ticket/confirm` | Đã có nhưng là stub | Tương tự — comment code ghi rõ "BẮT ĐẦU LOGIC NGHIỆP VỤ" nhưng chưa implement |
| — | API lấy chi tiết 1 ticket theo `id` (để render Summary Card sau khi có `ticketId`) | **Cần tạo mới** | Chưa thấy `GET /api/ticket/{id}` trong `TicketController` |

## 6. Requirements

- [ ] (Blocking) Chốt mô hình xác nhận: đồng bộ ngay vs. qua email — ảnh hưởng trực tiếp UI/UX của
      Success Modal (hiện ngay hay "kiểm tra email của bạn").
- [ ] (Blocking) Vá `RevenueConsumer` để thực sự tạo `Ticket` khi nhận message.
- [ ] (Blocking) Thống nhất tên tham số giữa `EmailConfirmTicketConsumer` và `TicketWebController`/
      `/api/ticket/confirm`.
- [ ] Bổ sung `GET /api/ticket/{id}` để render lại Summary Card/QR khi khách quay lại xem vé.
- [ ] Thiết kế trạng thái lỗi thanh toán/hết hạn giữ chỗ (chưa có trong Figma).
- [ ] (TODO/needs confirmation) QR code chứa dữ liệu gì để soát vé (ticketId ký số? JWT ngắn hạn?).
