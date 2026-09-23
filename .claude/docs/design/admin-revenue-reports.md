# Màn hình: Báo cáo doanh thu

> Figma: node-id `2:2115` (tên frame: "Revenue Reports") — file "Ticket-Buses" (`fileKey=QgeicQW2IuhLakGxpsQnr1`)
> Nhóm: Admin Terminal
> Slug: `admin-revenue-reports`

## 1. Tổng quan

Trang báo cáo doanh thu chi tiết hơn Dashboard: 3 summary card, biểu đồ mixed chart (Revenue by
Route), bảng Revenue by Bus, heatmap calendar, và bảng Employee Performance.

## 2. Basic Design

- `Title & Sticky Filter Bar`: heading + nhóm nút filter (khoảng thời gian) + nút export.
- `Summary Cards Bento Grid`: Total Revenue, Avg/Trip, Avg/Bus.
- `Main Analytics Section`:
  - `Revenue by Route Chart Section` (mixed bar+line chart, 5 bar mẫu).
  - `Revenue by Bus Table` (table có nút export riêng).
  - `Right Column`: `Heat Map Calendar` + `Employee Performance` (3 nhân viên mẫu, có avatar).

## 3. Detail Design

| Khối UI | Field | Nguồn dữ liệu (đề xuất map) |
|---|---|---|
| Total Revenue | "$482,950.00" | `GET /api/revenue/report` |
| Avg Revenue / Trip | "$1,240.50" | `GET /api/revenue/report` |
| Avg Revenue / Bus | "$14,200.00" | `GET /api/revenue/report` |
| Revenue by Route chart | 5 route, doanh thu theo route | `GET /api/revenue/by-route?period=` → `routes[]` |
| Revenue by Bus table | danh sách xe + doanh thu | `GET /api/revenue/bus/all?date=` hoặc `GET /api/revenue/bus?busId=&date=` |
| Heat Map Calendar | doanh thu theo ngày trong tháng | `GET /api/revenue/by-date?period=` → `heatmap[]` |
| Employee Performance | tên, doanh thu bán được | `GET /api/revenue/top-customers?period=` → `staff[]` (tên field response là "staff" dù path là "top-customers" — cần xác nhận đặt tên lại) |

**States:** loading riêng từng block (không phụ thuộc lẫn nhau), lỗi từng API riêng biệt, filter theo
`period` áp dụng chung cho toàn trang hay từng block — **cần xác nhận UX**.

## 4. Business Logic

1. Trang load với `period` mặc định → gọi 4 API độc lập: `/report`, `/by-route`, `/by-date`,
   `/top-customers` (đều nhận `period` optional).
2. Nút export ở `Revenue by Bus Table` — có khả năng dùng `GET /api/ticket/summary/excel` (export
   Excel theo `busId` + khoảng `fromDate`/`toDate`) chứ không phải API `revenue` — cần xác nhận vì
   2 API export khác nhau đang tồn tại (`/api/ticket/summary/excel` theo bus+range ngày cụ thể, và
   trang này lọc theo `period` dạng chuỗi như "monthly").
3. Đổi filter thời gian → gọi lại toàn bộ 4 API với `period` mới.

## 5. API

| Method | Path | Trạng thái | Response | Nguồn |
|---|---|---|---|---|
| GET | `/api/revenue/report?period=` | Đã có | `Map<String,Object>` (generic, chưa có DTO cụ thể) | `RevenueController.java:76` |
| GET | `/api/revenue/by-route?period=` | Đã có | `{ "routes": [...] }` | `RevenueController.java:82` |
| GET | `/api/revenue/by-date?period=` | Đã có | `{ "heatmap": [...] }` | `RevenueController.java:88` |
| GET | `/api/revenue/top-customers?period=` | Đã có | `{ "staff": [...] }` | `RevenueController.java:94` |
| GET | `/api/revenue/bus/all?date=` | Đã có (khác nhóm — theo ngày cụ thể không theo `period`) | `List<Map<String,Object>>` | `RevenueController.java:68` |
| GET | `/api/ticket/summary/excel?busId=&fromDate=&toDate=` | Đã có | file `.xlsx` | `TicketController.java` |

**Gap:** endpoint `/report`, `/by-route`, `/by-date`, `/top-customers` đều trả `Map<String,Object>`
hoặc field generic (`routes`, `heatmap`, `staff`) thay vì DTO có kiểu rõ ràng như
`AdminDashboardResponse` — FE cần thống nhất field name với backend trước khi bind UI (rủi ro đổi
field ngầm không báo trước).

## 6. Requirements

- [ ] Xác nhận nút export ở "Revenue by Bus Table" gọi API nào (`/api/ticket/summary/excel` hay cần
      API export mới theo `period`).
- [ ] Chuẩn hoá response của 4 endpoint `/report`, `/by-route`, `/by-date`, `/top-customers` sang DTO
      có kiểu rõ ràng (đề xuất, không bắt buộc phải làm trước khi FE code, nhưng nên báo trước khi đổi).
- [ ] Xác nhận field `staff` trong response `/top-customers` — tên gây nhầm giữa "khách hàng" và
      "nhân viên", route tên là top-customers nhưng UI hiển thị Employee Performance.
- [ ] (TODO/needs confirmation) Danh sách giá trị hợp lệ cho `period` trên toàn bộ 4 API.
