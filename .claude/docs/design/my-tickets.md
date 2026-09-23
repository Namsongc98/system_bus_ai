# Màn hình: Vé của tôi

> Figma: node-id `2:1565` (tên frame gốc trong Figma: **"Tickets Admin"** — tên gây nhầm lẫn, nội
> dung thực tế là trang khách hàng xem vé đã đặt, không phải trang quản trị) — file "Ticket-Buses"
> (`fileKey=QgeicQW2IuhLakGxpsQnr1`)
> Nhóm: Passenger/Public UI
> Slug: `my-tickets`

## 1. Tổng quan

Danh sách vé của khách hàng, dạng card, có 3 biến thể trạng thái quan sát được trong Figma: vé
sắp tới (Active/Upcoming, có QR), vé đã dùng/khác trạng thái, và vé đã huỷ có hoàn tiền
("REFUND: PROCESSED"). Có filter tabs phía trên và section gợi ý ("Upgrade to First Class", "Save
15% on Groups") không thuộc nghiệp vụ vé.

## 2. Basic Design

- `Editorial Header Section`: heading + `Filter Tabs` (3 nút — khả năng: Upcoming / Completed /
  Cancelled).
- `Tickets Grid`: 3 `Ticket Card` mẫu, mỗi card có `QR Side` riêng (digital ticket QR).
- Section gợi ý khuyến mãi (marketing, không cần API nghiệp vụ vé).
- `Footer` dùng chung.

## 3. Detail Design

| Ticket Card | Trạng thái | Field hiển thị (Figma) |
|---|---|---|
| Card 1 | Active/Upcoming | Date "Oct 24, 2024", Seat "12A (Window)", Price "$45.00", QR code, nút hành động |
| Card 2 | biến thể khác (chưa rõ tên trạng thái cụ thể) | Date "Oct 19, 2024", Seat "04C (Aisle)", Price "$32.00" |
| Card 3 | Cancelled | Date "Nov 02, 2024", Seat "--", "REFUND: PROCESSED", nút "VIEW REASON" |

**Ghi chú:** giá hiển thị dạng `$` (USD) trong Figma nhưng domain thực tế dùng VNĐ (`₫` xuất hiện ở
`admin-dashboard`) — cần thống nhất đơn vị tiền tệ trước khi code.

**States:** loading danh sách, empty-state (chưa có trong Figma, cần bổ sung khi khách chưa có vé
nào), theo từng filter tab.

## 4. Business Logic

1. Khách đăng nhập → FE gọi API lấy danh sách vé theo `customerId` (kèm filter trạng thái).
2. Card "Cancelled" hiển thị lý do hoàn tiền qua nút "VIEW REASON" — cần API/field lưu lý do huỷ.
3. Trạng thái vé nên map theo enum `TicketStatus` đã có ở backend: `NOT_BOOKED`, `PENDING`,
   `CANCELLED`, `SUCCESS` — tab "Active/Upcoming" tương ứng `SUCCESS` (đã xác nhận) hoặc `PENDING`
   (đang chờ xác nhận qua email, xem `payment-booking-confirmation.md`).

## 5. API

| Method | Path | Trạng thái | Ghi chú |
|---|---|---|---|
| — | `GET /api/ticket/me` hoặc `GET /api/ticket?customerId=` (đề xuất) | **Cần tạo mới** | `TicketController` hiện không có API list vé theo khách hàng — chỉ có `POST` (tạo), `PUT /{tripId}` (sửa — lưu ý path dùng `tripId` không phải `ticketId`, khả năng bug đặt tên), `GET /summary`/`/summary/excel` (tổng doanh thu, dành cho Admin) |
| — | `GET /api/ticket/{id}/refund-reason` (đề xuất, nếu cần) | **Cần tạo mới** | Không có field/endpoint lưu lý do huỷ+hoàn tiền trong `Ticket` entity hiện tại |

## 6. Requirements

- [ ] (Blocking) Tạo API list vé theo khách hàng đang đăng nhập, có filter theo `TicketStatus`.
- [ ] Thống nhất đơn vị tiền tệ hiển thị (VNĐ, khớp phần Admin) thay vì `$` như trong Figma.
- [ ] Thiết kế empty-state khi khách chưa có vé nào.
- [ ] (TODO/needs confirmation) Cơ chế lưu & hiển thị lý do huỷ/hoàn tiền.
- [ ] (TODO/needs confirmation) `PUT /api/ticket/{tripId}` dùng `tripId` làm path variable nhưng sửa
      1 `Ticket` cụ thể — xác nhận đây có phải lỗi đặt tên (nên là `ticketId`) không, tránh nhầm giữa
      nhiều vé cùng trip.
