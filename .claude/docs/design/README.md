# Design Docs — Ticket-Buses (Figma) → System_bus

Nguồn: Figma file "Ticket-Buses" (`fileKey=QgeicQW2IuhLakGxpsQnr1`), page "Page 1", 17 top-level frame.
Mỗi frame có 1 file riêng trong thư mục này. Mỗi file độc lập, có đủ API/nghiệp vụ/basic-detail
design/yêu cầu riêng để AI hoặc người đọc tra cứu nhanh mà không cần đọc các file khác — trừ 2 file
thuộc cùng 1 luồng (`admin-create-trip-modal.md` bước 1-3 và `admin-schedule-trip-review.md` bước 4)
thì có trỏ chéo sang nhau.

## Mục lục

### Nhóm A — Passenger / Public (Fluid Voyager customer site)
| # | File | Figma node-id | Màn hình |
|---|---|---|---|
| 1 | [admin-login.md](./admin-login.md) | `13:2` | Đăng nhập (Admin Terminal) |
| 2 | [customer-register.md](./customer-register.md) | `2:3525` | Đăng ký tài khoản khách hàng |
| 3 | [trip-search-results.md](./trip-search-results.md) | `2:961` | Trang chủ tìm chuyến + kết quả |
| 4 | [seat-selection-checkout.md](./seat-selection-checkout.md) | `2:1179` | Chọn ghế + nhập thông tin hành khách |
| 5 | [payment-booking-confirmation.md](./payment-booking-confirmation.md) | `2:1385` | Thanh toán + xác nhận đặt vé |
| 6 | [my-tickets.md](./my-tickets.md) | `2:1565` | Vé của tôi (đặt tên lại từ "Tickets Admin") |

### Nhóm B — Admin Terminal (quản trị)
| # | File | Figma node-id | Màn hình |
|---|---|---|---|
| 7 | [admin-dashboard.md](./admin-dashboard.md) | `2:1799` | Dashboard tổng quan |
| 8 | [admin-revenue-reports.md](./admin-revenue-reports.md) | `2:2115` | Báo cáo doanh thu |
| 9 | [admin-buses-routes.md](./admin-buses-routes.md) | `2:2475` | Quản lý Xe & Tuyến đường |
| 10 | [admin-trips-management.md](./admin-trips-management.md) | `2:2822` | Quản lý chuyến đi |
| 11 | [admin-user-management.md](./admin-user-management.md) | `2:3159` | Quản lý người dùng |
| 12 | [admin-create-trip-modal.md](./admin-create-trip-modal.md) | `2:3625` | Modal tạo chuyến — bước 1-3 |
| 13 | [admin-create-route-modal.md](./admin-create-route-modal.md) | `2:3833` | Modal tạo tuyến đường |
| 14 | [admin-create-bus-modal.md](./admin-create-bus-modal.md) | `2:3949` | Modal tạo xe |
| 15 | [admin-schedule-trip-review.md](./admin-schedule-trip-review.md) | `2:4033` | Modal tạo chuyến — bước 4 (Final Review) |
| 16 | [admin-toast-notifications.md](./admin-toast-notifications.md) | `2:4193` | Pattern: Toast notification |
| 17 | [admin-delete-confirmation.md](./admin-delete-confirmation.md) | `2:4370` | Pattern: Xác nhận xoá |

## Quy ước dùng chung cho cả 17 file

- **Basic Design**: bố cục tổng thể, các khối chính, không đi vào field-level.
- **Detail Design**: từng field/control, kiểu dữ liệu, placeholder, validate, state (empty/loading/error).
- **Business Logic**: luồng xử lý, điều kiện, quy tắc nghiệp vụ.
- **API**: đối chiếu trực tiếp với controller thật trong `ticket-system/` (module `manage-revenue-ticket`
  hoặc `booking_ticket`). Method/path lấy từ code, không suy đoán. Ô "Trạng thái" ghi rõ *đã có* / *cần bổ
  sung* / *cần tạo mới*.
- **Requirements**: checklist acceptance criteria, có thể copy thẳng sang `/make-testcase`.
- Field trong Figma không map được field nào ở backend hiện tại → ghi rõ trong bảng, không tự bịa field mới.

## Gap tổng hợp (phát hiện khi đối chiếu Figma ↔ backend)

Xem chi tiết trong từng file, tóm tắt nhanh:

| Gap | Ảnh hưởng màn hình |
|---|---|
| `UserController` rỗng — chưa có bất kỳ API list/create/update/xoá/đổi role user nào | `admin-user-management.md` |
| `RouteController`/`BusController`/`TripController` không có API xoá (`DELETE`) | `admin-delete-confirmation.md`, `admin-buses-routes.md`, `admin-trips-management.md` |
| `RouteController` không có API `GET` để list routes | `admin-buses-routes.md` |
| `UserRequestDto` (register) chỉ có `email`/`password`/`role` — không có `fullName`/`phone`/`dateOfBirth` như UI | `customer-register.md` |
| Không có frame Login riêng cho khách hàng (chỉ có Login cho Admin Terminal) — khách hàng có thể đang dùng chung `/api/auth/login` nhưng chưa có UI | `admin-login.md` |
| `TicketController /email` và `/confirm` mới là code giả lập (`// Giả lập xử lý thành công`), chưa có logic DB thật | `my-tickets.md`, `payment-booking-confirmation.md` |
