# Frontend API — Admin Dashboard

> Màn hình: [`.claude/docs/design/admin-dashboard.md`](../../../../docs/design/admin-dashboard.md)
> Backend thật: [`references/backend/api/admin-dashboard/endpoints.md`](../../../backend/api/admin-dashboard/endpoints.md)
> Quy ước chung: [`../_conventions.md`](../_conventions.md)
> File thật: `src/pages/admin/DashboardView.vue`, `src/stores/admin.js` (`useAdminStore`), `src/services/adminService.js`
> **Đây là màn nối API đúng nhất trong toàn bộ 17 màn** — path khớp, bóc response đúng lớp. Chỉ còn
> lệch port (giống mọi màn khác).

## Nút nào gọi API nào

| Nút/UI trên `DashboardView.vue` | Handler | API gọi | Trạng thái |
|---|---|---|---|
| Vào trang (`onMounted`) | `Promise.allSettled([adminStore.fetchDashboard(), adminStore.fetchRevenue({period})])` | `GET /admin/dashboard` + `GET /admin/revenue?period=monthly` | ✅ Đã nối đúng (chỉ lệch port) |
| Nút **"New Booking"** | `goToNewBooking()` → `router.push({ name: ROUTE_NAMES.ADMIN_TICKETS })` | không gọi API, điều hướng sang **trang stub rỗng** (xem cảnh báo bên dưới) | ⚠️ Điều hướng vào dead-end |
| Đổi tab period trong `BaseTrendChart` (Revenue Trend) | `handleRevenuePeriodChange(period)` → `adminStore.fetchRevenue({ period })` | `GET /admin/revenue?period=<value>` | ✅ Đã nối đúng |

## ⚠️ Nút "New Booking" dẫn tới trang rỗng

`ROUTE_NAMES.ADMIN_TICKETS` map tới `pages/admin/TicketsAdmin.vue` — component này chỉ có
`<!-- UI provided by Figma design -->` (14 dòng, chưa implement gì, xem
[`admin-toast-notifications`](../admin-toast-notifications/endpoints.md) không liên quan — đúng ra
nên xem đây là gap riêng: không có UI tạo booking thủ công cho Admin). Bấm nút này hiện tại chỉ dẫn
tới trang trắng.

## 1. Dashboard tổng hợp

- **Service:** `adminService.getDashboard()` — **tự bóc 1 lớp** (`return response.data`, nhóm 2 trong
  [`../_conventions.md`](../_conventions.md#3-service-layer-hiện-tại-không-đồng-nhất-cách-bóc-response)
  mục 3) → trả về nguyên envelope backend `{status, message, data, timestamp}`.
- **Store:** `fetchDashboard()` → `dashboard.value = response?.data ?? null` — bóc đúng **thêm 1 lớp**
  để lấy `data` thật → **kết quả `dashboard.value` = đúng payload `AdminDashboardResponse` thật**, không
  bị lệch lớp như nhiều store khác trong hệ thống.

| | FE (`API_ENDPOINTS.ADMIN.DASHBOARD`) | Backend thật |
|---|---|---|
| Path | `/admin/dashboard` | `/api/admin/dashboard` |

Path khớp hoàn toàn (chỉ khác baseURL/port, xem `../_conventions.md` mục 1).

## 2. Revenue Trend (chart)

- **Service:** `adminService.getRevenue(params)` — cũng tự bóc 1 lớp, trả nguyên envelope.
- **Store:** `fetchRevenue()` → `revenueTrend.value = Array.isArray(response?.data) ? response.data : []`
  — đúng, vì `data` của `GET /api/admin/revenue` là `List<RevenueTrendResponse>` (xem backend doc).

| | FE (`API_ENDPOINTS.ADMIN.REVENUE`) | Backend thật |
|---|---|---|
| Path | `/admin/revenue?period=` | `/api/admin/revenue?period=` |

Path khớp hoàn toàn.

### Field mapping UI ← response (đã đối chiếu `AdminDashboardResponse` thật)

| UI | Field trong `dashboard.value` |
|---|---|
| 4 KPI card | `kpis.totalRevenue/.revenueTrendPercent`, `.tripsCompleted/.tripsTrendPercent`, `.ticketsSold/.ticketsTrendPercent`, `.activeCustomers/.customersTrendPercent` — map qua `DASHBOARD_KPIS` config (`src/constants/admin/dashboard.js`) |
| "Top Routes" | `topRoutes[]` — dùng thẳng, không normalize thêm |
| "Loyal Voyagers" table | `loyalCustomers[]` — map thêm `id = customerId`, format `totalSpent` qua `formatCurrency` |
| "Recent Bookings" | `recentBookings[]` — map thành `{ title, description, time }`, `time` qua `formatRelativeTime` (tính local, không phải field trả sẵn) |

## Requirements

- [ ] Set đúng `VITE_KONG_API_URL` (`http://localhost:8000/api`, qua Kong) — đây là điều kiện duy nhất còn thiếu để màn
      này hoạt động thật, không cần sửa code path/field nào khác.
- [ ] Backend cần xác nhận danh sách giá trị hợp lệ cho `period` (xem backend doc) — FE hiện chỉ dùng
      `'monthly'` làm mặc định và các key trong `DASHBOARD_REVENUE_PERIOD_TABS`, chưa xác nhận khớp.
- [ ] Quyết định: xây `TicketsAdmin.vue` (trang tạo booking Admin) thật, hoặc đổi nút "New Booking"
      trỏ sang route khác — hiện đang dẫn vào trang trắng.
