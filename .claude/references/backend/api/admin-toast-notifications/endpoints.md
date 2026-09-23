# API — Pattern: Toast Notification

> Màn hình: [`.claude/docs/design/admin-toast-notifications.md`](../../../../docs/design/admin-toast-notifications.md) · Figma `2:4193`
> Quy ước chung: [`../_conventions.md`](../_conventions.md)
> Controller: **không có** — Toast không phải 1 trang, không có API riêng.

## Endpoint dùng ở màn này

| Loại Toast | Nguồn dữ liệu | Trạng thái |
|---|---|---|
| Success (vd "Route #402 đã cập nhật") | `message` trong `BaseResponseDto` của API vừa gọi thành công | ✅ Có sẵn (tái dùng response envelope, không cần API riêng) |
| Error (vd "Failed to synchronize ticket sales") | `message` trong `BaseResponseDto.error(...)` khi API trả lỗi, hoặc message tự dựng khi lỗi mạng/timeout | ✅ Có sẵn (tái dùng) |
| Info (vd "System maintenance scheduled...") | **Không có nguồn dữ liệu nào ở backend hiện tại** | ❌ Cần tạo mới (nếu muốn dùng thật) |

## 1. Success / Error Toast — không cần API riêng

Mọi Toast Success/Error nên đọc trực tiếp field có sẵn trong `BaseResponseDto` (xem
[`../_conventions.md`](../_conventions.md#2-response-envelope--đã-xác-minh-trong-code)):

```json
{ "status": 200, "message": "Create Successfully", "data": { }, "timestamp": 1733728800000 }
```

- Thành công → `type=success`, `message = response.data.message`.
- Thất bại (4xx/5xx từ backend) → `type=error`, `message = response.data.message` nếu backend trả
  đúng envelope lỗi; nếu lỗi mạng/parse (không có response body hợp lệ) → dùng message chung do FE tự
  định nghĩa (không hard-code tiếng Việt lẫn tiếng Anh lộn xộn như hiện tại — 1 số message backend
  đang tiếng Việt (`RevenueController`: "xe không có doanh thu"), 1 số tiếng Anh (`RouteController`:
  "Create Successfully") — **không nhất quán ngôn ngữ giữa các controller**, FE nên có lớp dịch/chuẩn
  hoá message trước khi hiển thị Toast thay vì hiển thị thẳng `message` từ mọi API).

## 2. Info Toast (hệ thống) — chưa có nguồn dữ liệu

- **Không có** WebSocket/SSE/endpoint polling nào phát thông báo dạng "system maintenance" ở backend hiện tại.
- **Đề xuất nếu cần làm thật:** `GET /api/system/notices` (polling định kỳ) hoặc kênh WebSocket
  `/ws/notifications` — **cần xác nhận với backend có nằm trong phạm vi MVP không**, có thể bỏ qua nếu chỉ là ý tưởng minh hoạ của designer.

## Requirements liên quan tới backend

- [ ] Chuẩn hoá ngôn ngữ `message` trả về giữa các controller (hiện lẫn lộn Việt/Anh) — không bắt buộc nhưng nên làm trước khi FE build lớp hiển thị Toast dùng chung.
- [ ] (Không blocking) Quyết định có cần channel Info Toast hệ thống thật hay bỏ khỏi phạm vi MVP.
