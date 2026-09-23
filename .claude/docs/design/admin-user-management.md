# Màn hình: Quản lý người dùng

> Figma: node-id `2:3159` (tên frame: "User Management") — file "Ticket-Buses" (`fileKey=QgeicQW2IuhLakGxpsQnr1`)
> Nhóm: Admin Terminal
> Slug: `admin-user-management`
> **⚠️ Gap lớn nhất trong toàn bộ 17 màn: `UserController` backend hiện đang RỖNG — chưa có bất kỳ
> API nào.** Toàn bộ mục 5 dưới đây là đề xuất, chưa có gì tồn tại.

## 1. Tổng quan

Bảng quản lý user với 4 vai trò quan sát được trong Figma: Admin, Driver, Collector, Customer — khớp
đúng với enum `UserRole` ở backend (`DRIVER, COLLECTOR, CUSTOMER, ADMIN, EMPLOYEE` — Figma chưa thấy
`EMPLOYEE` riêng, có thể gộp vào Collector/Admin). Có filter tabs theo role, bảng dữ liệu, bulk
actions bar, và nút tạo user dạng FAB (floating action button).

## 2. Basic Design

- `Header Section`: heading + `Filter Tabs with Badges` (4 nút, mỗi nút có badge số lượng).
- `Main Table Section`: bảng user — mỗi row có avatar, tên/email, vai trò, hoạt động gần nhất
  (vd "2 mins ago / IP: 192.168.1.1" cho Admin, "Shift: Night Route 402" cho Driver, "Station:
  Central Terminal" cho Collector, "Mobile App (iOS)" cho Customer), nút hành động cuối dòng.
- `Table Footer / Pagination`.
- `Bulk Actions Floating Bar`: xuất hiện khi có row được chọn (checkbox) — có 3 nút hành động +
  1 nút phụ.
- `Button - Global "Create" FAB`: nút nổi tạo user mới.

## 3. Detail Design

| Field | Loại | Map entity `User` |
|---|---|---|
| Avatar/Tên/Email | text + ảnh | `User.email` (không có field `name`/avatar ở entity — **thiếu**) |
| Vai trò | badge | `User.role` (`UserRole`) |
| Trạng thái hoạt động | boolean/badge | `User.isActive` |
| Trạng thái riêng theo role | text phụ | `User.driverStatus` (`DriverStatus`: PENDING/ACTIVE/INACTIVE) cho Driver; `User.userStatus` (`CustomerStatus`: BOOKED/NOT_BOOKED) cho Customer — **không khớp hoàn toàn** với nội dung Figma ("Shift: Night Route 402", "Station: Central Terminal", "Mobile App (iOS)", "IP: 192.168.1.1" đều là dữ liệu KHÔNG có field tương ứng trong entity `User` hiện tại) |
| Hoạt động gần nhất (time ago) | text | không có field `lastActiveAt`/audit log gắn trực tiếp `User` — có entity `AuditLog` riêng, cần xác nhận có liên kết được không |
| Bulk actions | nút hành động hàng loạt | chưa xác định rõ 3 hành động là gì (khả năng: đổi role, khoá/mở khoá, xoá) |

**States:** loading bảng, rỗng theo từng filter role, chọn nhiều row (hiện bulk bar), lỗi tải.

## 4. Business Logic

1. Load bảng theo role filter (tab) + phân trang.
2. Click 1 user → xem chi tiết / sửa role / khoá-mở khoá.
3. Chọn nhiều row (checkbox) → `Bulk Actions Floating Bar` hiện, thực hiện hành động hàng loạt.
4. Tạo user mới (FAB) → có thể dùng lại `POST /api/auth/register` (đã có, nhận `role`) thay vì tạo
   API riêng — cần xác nhận.

## 5. API — tất cả đều **cần tạo mới**, vì `UserController.java` hiện chỉ là class rỗng

| Method | Path (đề xuất) | Mục đích |
|---|---|---|
| GET | `/api/user?role=&page=&size=` | List user, filter theo `role`, phân trang |
| GET | `/api/user/{id}` | Chi tiết 1 user |
| PUT | `/api/user/{id}` | Sửa thông tin/role |
| PUT | `/api/user/{id}/status` | Khoá/mở khoá (`isActive`) |
| DELETE | `/api/user/{id}` | Xoá (cân nhắc soft-delete vì user có liên kết `Ticket`, `Trip.driver`) |
| POST | `/api/user/bulk-action` | Hành động hàng loạt (nội dung cụ thể cần xác nhận) |
| POST | `/api/auth/register` | Đã có — có thể tái dùng cho nút "Create" thay vì viết API tạo user riêng |

## 6. Requirements

- [ ] (Blocking) Toàn bộ `UserController` cần được implement trước khi có bất kỳ tiến độ FE nào cho
      màn này — đây là màn hình rủi ro tiến độ cao nhất trong 17 màn.
- [ ] (Blocking) Bổ sung field còn thiếu ở entity `User` nếu muốn hiển thị đúng như Figma: tên hiển
      thị/avatar, IP đăng nhập gần nhất, ca trực (Driver), trạm (Collector), thiết bị đăng nhập
      (Customer) — hoặc rút gọn UI cho khớp field đã có (`role`, `isActive`, `driverStatus`,
      `userStatus`) để tránh phải mở rộng schema.
- [ ] Xác nhận rõ 3 hành động trong Bulk Actions Bar trước khi thiết kế API `bulk-action`.
- [ ] Xác nhận enum `EMPLOYEE` (có ở backend, không thấy tab riêng ở Figma) map vào đâu trên UI.
- [ ] (TODO/needs confirmation) Xoá user là xoá cứng hay đổi `isActive=false` — vì user có ràng buộc
      dữ liệu với `Ticket`/`Trip`, khuyến nghị soft-delete.
