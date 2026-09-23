# Frontend API — Báo cáo doanh thu

> Màn hình: [`.claude/docs/design/admin-revenue-reports.md`](../../../../docs/design/admin-revenue-reports.md)
> Backend thật: [`references/backend/api/admin-revenue-reports/endpoints.md`](../../../backend/api/admin-revenue-reports/endpoints.md)
> Quy ước chung: [`../_conventions.md`](../_conventions.md)
> File thật: `src/pages/admin/RevenueReports.vue`, `src/services/revenueService.js` (gọi thẳng, **không
> qua store**)

## Nút nào gọi API nào

| Nút/UI trên `RevenueReports.vue` | Handler | API gọi | Trạng thái |
|---|---|---|---|
| Vào trang / đổi tab period (Daily/Weekly/...) | `fetchRevenueReports()` → `Promise.allSettled([getRevenueReport, getRevenueByRoute, getRevenueByDate, getTopCustomers])` | 4 request song song, path khớp backend (chỉ lệch port) | ⚠️ Gọi đúng nhưng field không xác định |
| Nút **"Oct 01 - Oct 31"** (date range) | không có `@click` handler nối logic — chỉ có `aria-label` tĩnh | không gọi API | ❌ Trang trí thuần, chưa có date picker |
| Nút **"Export PDF"** | không có `@click` handler nào | không gọi API | ❌ Chưa nối — và backend chỉ có export Excel, không có PDF (xem mục 4) |

## 1-4. Bốn API gọi song song — path khớp, nhưng field response chưa xác định ở CẢ 2 PHÍA

```js
getRevenueReport(params)    // GET '/revenue/report'      params: { period }
getRevenueByRoute(params)   // GET '/revenue/by-route'     params: { period }
getRevenueByDate(params)    // GET '/revenue/by-date'      params: { period }
getTopCustomers(params)     // GET '/revenue/top-customers' params: { period }
```

| | FE path | Backend thật |
|---|---|---|
| Cả 4 | `/revenue/report`, `/revenue/by-route`, `/revenue/by-date`, `/revenue/top-customers` | `/api/revenue/report`, `/api/revenue/by-route`, `/api/revenue/by-date`, `/api/revenue/top-customers` |

**Path khớp hoàn toàn** (1 trong số ít domain khớp, xem `../_conventions.md` mục 5) — chỉ lệch port.
Nhưng cả 4 endpoint ở backend **trả `Map<String,Object>`/generic, không có DTO cố định** (xem
[backend doc](../../../backend/api/admin-revenue-reports/endpoints.md)) — field JSON thật chưa được
xác nhận ở cả 2 phía. `RevenueReports.vue` xử lý gap này bằng cách thử **rất nhiều tên field khả dĩ**
qua helper `firstDefined(...)` (ví dụ `totalRevenue`/`revenue`/`amount` cho tổng doanh thu), và fallback
về hằng số `REVENUE_REPORT_FALLBACK_*` khi không khớp field nào — nếu response thật của backend có
field khác hoàn toàn những gì FE đang đoán, trang sẽ hiển thị **toàn bộ dữ liệu mẫu** kèm banner vàng
"Some revenue data is unavailable" mà không báo rõ nguyên nhân là field JSON sai tên.

### Điểm cần lưu ý riêng: nguồn dữ liệu bảng "Revenue by Bus" bị trộn nhầm endpoint

```js
const busItems = getCollection(reportPayload, ['buses', 'busRevenue', 'units'])
```

`RevenueBusTable` lấy dữ liệu từ `reportPayload` (kết quả của `getRevenueReport` = `GET
/revenue/report`), **không gọi** endpoint riêng cho bus. Nhưng theo backend thật, dữ liệu theo bus
nằm ở **`GET /api/revenue/bus/all?date=`** — một endpoint hoàn toàn khác, dùng filter theo `date` cụ
thể chứ không phải `period` (xem backend doc mục 3) — và **FE hiện không gọi endpoint này ở đâu cả**.
Kết quả: bảng "Revenue by Bus" gần như chắc chắn sẽ luôn rơi vào fallback (`REVENUE_REPORT_FALLBACK_BUS_ROWS`)
vì đang cố tìm field `buses`/`busRevenue`/`units` trong response của 1 API hoàn toàn không liên quan.

## 5. "Employee Performance" panel — tên gọi nhầm lẫn cả 2 phía

```js
const staffItems = getCollection(customerPayload, ['staff', 'employees', 'performance'])
```
`customerPayload` đến từ `getTopCustomers()` (`GET /revenue/top-customers`) — FE đặt tên biến
`customerPayload`/`staffItems` lẫn lộn, và backend cũng có cùng vấn đề: route/method tên
"top-customers" nhưng key JSON trả về là `"staff"`, trong khi UI hiển thị "Employee Performance"
(xem [backend doc](../../../backend/api/admin-revenue-reports/endpoints.md) mục 6) — **cả 3 tầng
(route, response key, UI label) đang dùng 3 khái niệm nghiệp vụ khác nhau** (khách hàng chi tiêu
nhiều nhất vs nhân viên bán vé nhiều nhất). Đây là điểm cần chốt lại nghiệp vụ trước khi tiếp tục
sửa field mapping ở FE, không chỉ là lỗi đặt tên.

## 6. Nút "Export PDF" — chưa nối, và backend chỉ hỗ trợ Excel

Không có handler nào gọi bất kỳ API export nào khi bấm nút này. Backend thật **chỉ có 1 endpoint
export**, `GET /api/ticket/summary/excel` (trả file `.xlsx`, **public — không cần JWT**, xem gap bảo
mật ở backend doc), không có endpoint PDF nào. Nếu giữ nút "Export PDF" như thiết kế, cần 1 trong 2
hướng: đổi UI thành "Export Excel" cho khớp backend, hoặc yêu cầu backend viết thêm endpoint PDF.

## Requirements

- [ ] (Blocking, phía backend trước) Xác nhận field JSON thật của cả 4 endpoint — không thể sửa FE
      cho khớp khi chưa biết response thật trả gì (xem backend doc).
- [ ] (Blocking) Gọi đúng `GET /api/revenue/bus/all?date=` cho bảng "Revenue by Bus" thay vì cố đoán
      field từ response của `/revenue/report`.
- [ ] Làm rõ nghịch lý "top-customers" vs "staff" vs "Employee Performance" trước khi code tiếp phần
      normalize dữ liệu này.
- [ ] Nối nút "Export PDF" (đổi thành Excel để khớp backend) và nút chọn khoảng ngày — cả 2 hiện là
      UI tĩnh.
