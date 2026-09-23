# API — Báo cáo doanh thu

> Màn hình: [`.claude/docs/design/admin-revenue-reports.md`](../../../../docs/design/admin-revenue-reports.md) · Figma `2:2115`
> Quy ước chung: [`../_conventions.md`](../_conventions.md)
> Controller: `RevenueController`, `TicketController` (`manage-revenue-ticket`, port `8082`)
> **⚠️ `RevenueController` KHÔNG có `@RoleRequired(ADMIN)`** — bất kỳ user có JWT hợp lệ (kể cả
> CUSTOMER) đang gọi thẳng được toàn bộ endpoint dưới đây. Xem `../_conventions.md` mục 3.

## Endpoint dùng ở màn này

| Button/Hành động UI | Method | Path | Trạng thái | Auth (thực tế trong code) |
|---|---|---|---|---|
| Load 3 Summary Card | GET | `/api/revenue/report?period=` | ✅ Đã có | JWT (không check role) |
| Chart "Revenue by Route" | GET | `/api/revenue/by-route?period=` | ✅ Đã có | JWT (không check role) |
| Bảng "Revenue by Bus Table" | GET | `/api/revenue/bus/all?date=` | ✅ Đã có (khác dạng filter) | JWT (không check role) |
| Nút export ở bảng Bus | GET | `/api/ticket/summary/excel?busId=&fromDate=&toDate=` | ✅ Đã có | **Public — không cần JWT** (permitAll) |
| Heat Map Calendar | GET | `/api/revenue/by-date?period=` | ✅ Đã có | JWT (không check role) |
| "Employee Performance" | GET | `/api/revenue/top-customers?period=` | ✅ Đã có (đặt tên gây nhầm) | JWT (không check role) |

## 1. Revenue Report (3 summary card)

- **Method & Path:** `GET /api/revenue/report?period=`
- **Controller:** `RevenueController.java:76`
- **Response:** `Map<String,Object>` — **không có DTO cụ thể**, field trả về do `RevenueService.getRevenueReport` quyết định (chưa đọc service, cần xác nhận field name thật trước khi FE bind, ví dụ không chắc là `totalRevenue`/`avgRevenuePerTrip`/`avgRevenuePerBus` hay tên khác).

```json
{
  "status": 200,
  "message": "Revenue report fetched",
  "data": { "...": "field cụ thể cần xác nhận với backend" },
  "timestamp": 1733728800000
}
```

## 2. Revenue by Route (chart)

- **Method & Path:** `GET /api/revenue/by-route?period=`
- **Controller:** `RevenueController.java:82`
- **Response:**
```json
{
  "status": 200,
  "message": "Revenue by route fetched",
  "data": { "routes": [ { "...": "field cụ thể cần xác nhận" } ] },
  "timestamp": 1733728800000
}
```
Response bọc thêm 1 lớp `{ "routes": [...] }` thay vì trả thẳng mảng — khác pattern so với
`/api/revenue/bus/all` (trả thẳng `List`). **Không nhất quán giữa các endpoint cùng controller.**

## 3. Revenue by Bus (bảng)

- **Method & Path:** `GET /api/revenue/bus/all?date=`
- **Controller:** `RevenueController.java:68`
- **Request:** `date` (LocalDate, bắt buộc) — **lọc theo 1 ngày cụ thể, KHÔNG theo `period` dạng chuỗi
  như các endpoint khác cùng màn** — FE cần map lại UI filter cho khớp (nếu UI chỉ có control chọn
  period dạng "This month" thì phải tự tính ra ngày cụ thể, hoặc xin backend đổi param).
- **Response:** `List<Map<String,Object>>`.

## 4. Export Excel

- **Method & Path:** `GET /api/ticket/summary/excel?busId=&fromDate=&toDate=`
- **Controller:** `TicketController.java` (`exportTicketSummaryToExcel`)
- **Auth:** **Public** (`/api/ticket/summary/excel` nằm trong `permitAll` ở `SecurityConfig`) — bất kỳ
  ai có URL cũng tải được, không cần đăng nhập. **Gap bảo mật cần soát lại trước production.**
- **Request:**

| Param | Type | Required | Format |
|---|---|---|---|
| `busId` | Long | không | — |
| `fromDate` | LocalDateTime | có | `yyyy-MM-dd:HH:mm:ss` (lưu ý dấu `:` giữa ngày và giờ, khác ISO chuẩn) |
| `toDate` | LocalDateTime | có | `yyyy-MM-dd:HH:mm:ss` |

- **Response:** file nhị phân `application/octet-stream`, header
  `Content-Disposition: attachment; filename=ticket_summary.xlsx`.

## 5. Revenue by Date (heatmap)

- **Method & Path:** `GET /api/revenue/by-date?period=`
- **Controller:** `RevenueController.java:88`
- **Response:** `{ "heatmap": [...] }` — cùng vấn đề field chưa xác định như mục 2.

## 6. "Employee Performance" — thực chất gọi `/top-customers`

- **Method & Path:** `GET /api/revenue/top-customers?period=`
- **Controller:** `RevenueController.java:94`
- **Response:** `{ "staff": [...] }` — **service method tên `getTopCustomers` nhưng key trả về là
  `"staff"`, và UI hiển thị "Employee Performance"** — 3 cái tên (route, method, key JSON, UI) đang
  lệch nhau, nghi vấn copy-paste nhầm bên backend. Cần hỏi lại: đây có đúng là dữ liệu "nhân viên bán
  vé nhiều nhất" hay thực ra phải là "khách hàng chi tiêu nhiều nhất" (2 khái niệm khác hẳn nghiệp vụ)?

## Requirements liên quan tới backend

- [ ] (Blocking) Xác nhận field JSON thật của `/report`, `/by-route`, `/by-date`, `/top-customers` —
      cả 4 đều trả `Map`/generic, không có DTO, rủi ro đổi field ngầm không báo trước cho FE.
- [ ] (Blocking) Làm rõ nghịch lý tên ở mục 6 (`top-customers` route/method vs `staff` key vs
      "Employee Performance" trên UI) trước khi FE code.
- [ ] Thống nhất kiểu filter thời gian: `period` (chuỗi) vs `date`/`fromDate`+`toDate` (ngày cụ thể) —
      hiện 3 kiểu khác nhau trong cùng 1 controller.
- [ ] (Bảo mật, Blocking) Thêm `@RoleRequired(ADMIN)` cho toàn bộ `RevenueController`, và xem lại việc
      để `/api/ticket/summary/excel` public.
