# API — Vé của tôi

> Màn hình: [`.claude/docs/design/my-tickets.md`](../../../../docs/design/my-tickets.md) · Figma `2:1565`
> Quy ước chung: [`../_conventions.md`](../_conventions.md)
> Controller: `TicketController` (`manage-revenue-ticket`, port `8082`) — **thiếu API chính (list theo khách hàng)**

## Endpoint dùng ở màn này

| Button/Hành động UI | Method | Path | Trạng thái | Auth |
|---|---|---|---|---|
| Load danh sách khi vào trang / đổi Filter Tab | GET | `/api/ticket/me?status=` (đề xuất) | ❌ Cần tạo mới | Cần JWT |
| Nút "VIEW REASON" (vé Cancelled) | GET | `/api/ticket/{id}/refund-reason` (đề xuất) | ❌ Cần tạo mới | Cần JWT |
| (dùng nội bộ, không phải nút riêng) — sửa 1 vé | PUT | `/api/ticket/{tripId}` | ⚠️ Đã có (path đặt tên gây nhầm) | Cần JWT |

## 1. (Đề xuất) List vé của khách hàng đang đăng nhập

- **Gọi khi:** vào trang, hoặc đổi `Filter Tabs` (Upcoming/Completed/Cancelled).
- **Method & Path đề xuất:** `GET /api/ticket/me?status=&page=&size=`
- **Auth đề xuất:** cần JWT — `customerId` lấy từ token (`request.getAttribute("id")`), **không nhận
  qua query param** để tránh 1 user xem được vé của người khác.

### Request (query, đề xuất)

| Param | Type | Required |
|---|---|---|
| `status` | string (enum `TicketStatus`: `NOT_BOOKED`/`PENDING`/`CANCELLED`/`SUCCESS`) | không |
| `page`, `size` | int | không |

### Response (đề xuất)

```json
{
  "status": 200,
  "message": "Get Successfully",
  "data": {
    "content": [
      {
        "ticketId": 101,
        "tripId": 12,
        "routeName": "Hà Nội - Hải Phòng",
        "departureTime": "2026-04-10T08:00:00",
        "seatNumber": 15,
        "price": 150000,
        "statusTicket": "SUCCESS",
        "issuedAt": "2026-04-09T14:30:00"
      }
    ],
    "totalElements": 5,
    "totalPages": 1
  },
  "timestamp": 1733728800000
}
```

Field map trực tiếp từ entity `Ticket` (`trip`, `customer`, `seller`, `statusTicket`, `seatNumber`,
`price`, `issuedAt`) — không cần thêm field mới, chỉ thiếu **endpoint**.

## 2. Sửa 1 vé (endpoint đã tồn tại, nhưng không phải "list")

- **Method & Path:** `PUT /api/ticket/{tripId}`
- **Controller:** `TicketController.java` (`updateTicket`)
- **⚠️ Đặt tên path-variable gây nhầm:** path là `/{tripId}` nhưng logic là sửa **1 Ticket cụ thể**
  (không phải sửa theo trip). Nếu 1 trip có nhiều ticket (nhiều ghế), gọi `PUT /api/ticket/5` hiện
  tại đang sửa **theo `tripId=5`**, không rõ sẽ ảnh hưởng ticket nào nếu trip đó có nhiều vé — cần đọc
  `TicketService.updateTicket` để xác nhận logic thật (không nằm trong phạm vi review Controller).
  **Khuyến nghị đổi path thành `/api/ticket/{ticketId}` để rõ ràng.**
- **Request:** `TicketRequestDto` (`tripId`, `sellerId`, `customerId`, `customerEmail`, `status`,
  `seatNumber`, `price`, `issuedAt`).
- **Response (201):** `BaseResponseDto<Ticket>` — body hiện trả `null` (không trả lại Ticket đã sửa).

## 3. (Đề xuất) Lý do huỷ/hoàn tiền

- **Method & Path đề xuất:** `GET /api/ticket/{id}/refund-reason`
- **Lý do cần tạo mới:** entity `Ticket` hiện tại không có field lưu lý do huỷ — cần bổ sung field
  (vd `cancelReason: String`) trước khi có endpoint này, hoặc lưu ở bảng riêng nếu lý do có cấu trúc
  phức tạp hơn (nhiều lần đổi trạng thái).

## Requirements liên quan tới backend

- [ ] (Blocking) Tạo `GET /api/ticket/me` (hoặc tương đương) — không có API này thì màn hình không thể
      implement.
- [ ] Đổi path `PUT /api/ticket/{tripId}` → `/{ticketId}` cho rõ nghĩa, xác nhận với backend trước khi đổi (breaking change).
- [ ] Thêm field `cancelReason` vào entity `Ticket` nếu cần nút "VIEW REASON" hoạt động thật.
- [ ] `PUT /api/ticket/{tripId}` nên trả lại `Ticket` đã cập nhật thay vì `null`, để FE không phải gọi lại API list ngay sau đó.
