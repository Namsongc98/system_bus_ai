# API — Quản lý người dùng

> Màn hình: [`.claude/docs/design/admin-user-management.md`](../../../../docs/design/admin-user-management.md) · Figma `2:3159`
> Quy ước chung: [`../_conventions.md`](../_conventions.md)
> Controller: `UserController` (`manage-revenue-ticket`, port `8082`) — **file tồn tại nhưng là class rỗng:**
> ```java
> package com.ticket_system.manage_revenue_ticket.controller;
> public class UserController {
> }
> ```
> Toàn bộ bảng dưới đây là **đề xuất**, chưa có gì chạy được.

## Endpoint dùng ở màn này — tất cả ❌ Cần tạo mới

| Button/Hành động UI | Method | Path (đề xuất) | Trạng thái |
|---|---|---|---|
| Load bảng theo Filter Tab (role) | GET | `/api/user?role=&page=&size=` | ❌ Cần tạo mới |
| Click 1 row → xem chi tiết | GET | `/api/user/{id}` | ❌ Cần tạo mới |
| Sửa role/thông tin user | PUT | `/api/user/{id}` | ❌ Cần tạo mới |
| Khoá/mở khoá (toggle trong bulk hoặc từng row) | PUT | `/api/user/{id}/status` | ❌ Cần tạo mới |
| Xoá user | DELETE | `/api/user/{id}` | ❌ Cần tạo mới |
| Bulk action (chọn nhiều row) | POST | `/api/user/bulk-action` | ❌ Cần tạo mới |
| Nút "Create" (FAB) | POST | `/api/auth/register` | ✅ Đã có (tái dùng, không cần API riêng) |

## 1. (Đề xuất) List user

- **Method & Path:** `GET /api/user?role=&page=&size=`
- **Auth đề xuất:** JWT + role `ADMIN` (dùng `@RoleRequired(UserRole.ADMIN)` giống `AdminDashboardController` — đây là controller nên copy pattern security đúng ngay từ đầu, không lặp lại lỗi thiếu role-check như các controller khác).
- **Response field tối thiểu** (map thẳng từ entity `User`, đã xác minh trong code):

```json
{
  "status": 200,
  "message": "Get Successfully",
  "data": {
    "content": [
      {
        "id": 1,
        "email": "driver1@fluidvoyager.com",
        "role": "DRIVER",
        "isActive": true,
        "driverStatus": "ACTIVE",
        "userStatus": null,
        "createdAt": "2026-01-10T08:00:00",
        "updatedAt": "2026-04-01T10:00:00"
      }
    ],
    "totalElements": 40,
    "totalPages": 4
  },
  "timestamp": 1733728800000
}
```

**⚠️ Field UI hiển thị nhưng KHÔNG có trong entity `User`** — nếu muốn API trả đúng như Figma cần bổ
sung field trước (không tự bịa ra field mới ở đây):
- Tên hiển thị / avatar (entity chỉ có `email`).
- "2 mins ago / IP: 192.168.1.1" (Admin) — không có field lastActiveAt/lastLoginIp.
- "Shift: Night Route 402" (Driver) — không có field ca trực.
- "Station: Central Terminal" (Collector) — không có field trạm.
- "Mobile App (iOS)" (Customer) — không có field thiết bị đăng nhập.

`Password` **không** nằm trong response ở bất kỳ trường hợp nào — không đưa `password` vào DTO trả về.

## 2. (Đề xuất) Chi tiết 1 user

- **Method & Path:** `GET /api/user/{id}`
- **Response:** giống 1 phần tử ở mục 1.

## 3. (Đề xuất) Sửa user (role/thông tin)

- **Method & Path:** `PUT /api/user/{id}`
- **Request đề xuất:**
```json
{ "role": "COLLECTOR", "isActive": true }
```
- **Không nhận `password`, `email`** qua endpoint này (đổi email/password nên đi qua flow riêng có xác thực bổ sung, tương tự `PUT /api/auth/update-password` đã có sẵn cho password).

## 4. (Đề xuất) Khoá/mở khoá

- **Method & Path:** `PUT /api/user/{id}/status`
- **Request:** `{ "isActive": false }`
- Map trực tiếp field `User.isActive` đã có sẵn ở entity.

## 5. (Đề xuất) Xoá user

- **Method & Path:** `DELETE /api/user/{id}`
- **Khuyến nghị:** soft-delete (`isActive=false` + có thể thêm field `deletedAt`), **không xoá cứng**
  vì `User` có quan hệ với `Ticket.customer`, `Ticket.seller`, `Trip.driver` — xoá cứng sẽ vỡ dữ liệu
  lịch sử vé/chuyến.

## 6. (Đề xuất) Bulk action

- **Method & Path:** `POST /api/user/bulk-action`
- **Chưa xác định được nội dung 3 nút trong "Bulk Actions Floating Bar"** trên Figma — cần xác nhận
  nghiệp vụ cụ thể (đổi role hàng loạt? khoá hàng loạt? xoá hàng loạt?) trước khi thiết kế request body.

## 7. Tạo user mới — tái dùng API đã có

- **Method & Path:** `POST /api/auth/register` (xem chi tiết ở [`customer-register/endpoints.md`](../customer-register/endpoints.md))
- Dùng lại thay vì viết API tạo user riêng — chỉ cần truyền đúng `role` mong muốn (`DRIVER`, `COLLECTOR`, `ADMIN`, `EMPLOYEE`...).

## Requirements liên quan tới backend

- [ ] (Blocking, ưu tiên cao nhất trong toàn bộ 17 màn) Implement toàn bộ `UserController`.
- [ ] Dùng `@RoleRequired(UserRole.ADMIN)` ngay từ đầu cho controller này (đừng lặp lại lỗi thiếu role-check của Trip/Route/Bus/Revenue Controller).
- [ ] Quyết định: mở rộng entity `User` để khớp field Figma, hay rút gọn UI cho khớp field đã có (`role`, `isActive`, `driverStatus`, `userStatus`).
- [ ] Làm rõ nội dung 3 nút Bulk Action trước khi thiết kế `POST /api/user/bulk-action`.
- [ ] Xoá user dùng soft-delete, không xoá cứng (ràng buộc dữ liệu với `Ticket`/`Trip`).
