# Màn hình: Admin Dashboard

> Figma: node-id `2:1799` (tên frame: "Admin Dashboard") — file "Ticket-Buses" (`fileKey=QgeicQW2IuhLakGxpsQnr1`)
> Nhóm: Admin Terminal
> Slug: `admin-dashboard`
> Yêu cầu quyền: `ADMIN` (backend đã enforce bằng `@RoleRequired(UserRole.ADMIN)`)

## 1. Tổng quan

Trang tổng quan cho Admin: 4 KPI card, biểu đồ doanh thu theo thời gian, bảng Top Routes, bảng Top
Customers ("Loyal Voyagers"), danh sách Recent Bookings. Đây là màn hình **được backend hỗ trợ tốt
nhất** trong toàn bộ 17 màn — DTO response khớp gần như 1:1 với thiết kế Figma.

## 2. Basic Design

- `Header - TopNavBar`: search box + actions.
- `Aside - SideNavBar`: menu điều hướng (Dashboard, Routes, Buses, Trips, Users, Revenue, Settings).
- `KPI Cards Row` (4 card): Total Revenue, Trips Completed, Tickets Sold, Active Customers.
- `Charts Section`: `Revenue Trend` (60% width, area chart) + `Top Routes` (40% width).
- `Bottom Section: Tables`: `Top Customers` (table), `Recent Bookings` (list card).

## 3. Detail Design

| Khối UI | Field | Nguồn dữ liệu (response field) |
|---|---|---|
| KPI: Total Revenue | số tiền + % so với kỳ trước | `kpis.totalRevenue`, `kpis.revenueTrendPercent` |
| KPI: Trips Completed | số chuyến + % | `kpis.tripsCompleted`, `kpis.tripsTrendPercent` |
| KPI: Tickets Sold | số vé + % | `kpis.ticketsSold`, `kpis.ticketsTrendPercent` |
| KPI: Active Customers | số khách + % | `kpis.activeCustomers`, `kpis.customersTrendPercent` |
| Revenue Trend chart | series theo `label`/khoảng ngày | gọi riêng `GET /api/admin/revenue?period=` |
| Top Routes | tên tuyến, số vé bán, % thị phần | `topRoutes[].name`, `.ticketsSold`, `.sharePercent` |
| Top Customers ("Loyal Voyagers") | tên khách, số chuyến, tổng chi tiêu, hạng | `loyalCustomers[].customer`, `.trips`, `.totalSpent`, `.rank` |
| Recent Bookings | khách, tuyến, ghế, số tiền, thời gian | `recentBookings[].customer`, `.routeName`, `.seatNumber`, `.amount`, `.occurredAt` |
| Khoảng thời gian đang xem | date range hiển thị trên header | `period.startDate`, `period.endDate` |

**States:** loading (skeleton cho 4 KPI card + 2 chart), lỗi tải dữ liệu (retry), rỗng cho từng bảng
con nếu chưa có data trong kỳ.

## 4. Business Logic

1. Trang load → gọi song song `GET /api/admin/dashboard` (KPI + top routes + loyal customers +
   recent bookings) và `GET /api/admin/revenue?period=monthly` (dữ liệu vẽ chart xu hướng doanh thu).
2. Đổi bộ lọc thời gian (nếu có control chọn range — chưa thấy rõ trong Figma, `Button`/`Button`
   cạnh heading "Revenue Trend" gợi ý có toggle daily/weekly/monthly) → gọi lại `GET
   /api/admin/revenue?period=<daily|weekly|monthly>`.
3. Toàn bộ API dưới `/api/admin/**` bắt buộc role `ADMIN` — FE cần chặn truy cập route này ở phía
   client cho user không phải Admin, không chỉ dựa vào lỗi 403 từ server.

## 5. API

| Method | Path | Trạng thái | Response | Nguồn |
|---|---|---|---|---|
| GET | `/api/admin/dashboard` | Đã có | `AdminDashboardResponse` (period, kpis, topRoutes, loyalCustomers, recentBookings) | `AdminDashboardController.java:27` |
| GET | `/api/admin/revenue?period=monthly` | Đã có | `List<RevenueTrendResponse>` (`label`, `startDate`, `endDate`, `amount`) | `AdminDashboardController.java:37` |

## 6. Requirements

- [ ] Gọi song song 2 API (dashboard + revenue trend), không chờ tuần tự để giảm thời gian tải.
- [ ] Hiển thị đúng chiều mũi tên tăng/giảm theo dấu của các field `*TrendPercent` (âm = giảm).
- [ ] Chặn route Dashboard ở FE cho user không phải `ADMIN` (redirect, không chỉ ẩn menu).
- [ ] Xử lý rỗng riêng cho từng bảng con (Top Routes/Top Customers/Recent Bookings có thể rỗng độc lập).
- [ ] (TODO/needs confirmation) Giá trị `period` hợp lệ cho `/api/admin/revenue` — code default là
      `"monthly"`, cần hỏi backend danh sách đầy đủ (`daily`? `weekly`? `yearly`?).
