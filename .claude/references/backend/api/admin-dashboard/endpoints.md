# API — Admin Dashboard

> Màn hình: [`.claude/docs/design/admin-dashboard.md`](../../../../docs/design/admin-dashboard.md) · Figma `2:1799`
> Quy ước chung: [`../_conventions.md`](../_conventions.md)
> Controller: `AdminDashboardController` (`manage-revenue-ticket`, port `8082`)
> **Màn hình duy nhất có `@RoleRequired(ADMIN)` thật sự — dùng làm mẫu chuẩn cho các màn admin khác.**

## Endpoint dùng ở màn này

| Button/Hành động UI | Method | Path | Trạng thái | Auth |
|---|---|---|---|---|
| Load trang (KPI + Top Routes + Loyal Voyagers + Recent Bookings) | GET | `/api/admin/dashboard` | ✅ Đã có | JWT + role `ADMIN` |
| Toggle khoảng thời gian ở "Revenue Trend" chart | GET | `/api/admin/revenue?period=` | ✅ Đã có | JWT + role `ADMIN` |

## 1. Dashboard tổng hợp

- **Gọi khi:** vào trang Admin Dashboard (load 1 lần).
- **Method & Path:** `GET /api/admin/dashboard`
- **Controller:** `AdminDashboardController.java:27`
- **Auth:** `@RoleRequired(UserRole.ADMIN)` ở cả class và method → JWT hợp lệ + role phải là `ADMIN`, sai role → 403 (`UnauthorizedRoleException`).

### Request

Không có param.

### Response (200) — theo `AdminDashboardResponse` (Java `record`, đã đọc trực tiếp source)

```json
{
  "status": 200,
  "message": "Dashboard fetched",
  "data": {
    "period": { "startDate": "2026-04-01", "endDate": "2026-04-09" },
    "kpis": {
      "totalRevenue": 125500000,
      "revenueTrendPercent": 12.4,
      "tripsCompleted": 342,
      "tripsTrendPercent": 3.1,
      "ticketsSold": 8450,
      "ticketsTrendPercent": 5.0,
      "activeCustomers": 1245,
      "customersTrendPercent": 2.2
    },
    "topRoutes": [
      { "routeId": 3, "name": "Hà Nội - Hải Phòng", "ticketsSold": 620, "sharePercent": 18.5 }
    ],
    "loyalCustomers": [
      { "customerId": 7, "customer": "Nguyễn Văn A", "trips": 24, "totalSpent": 3600000, "rank": 1 }
    ],
    "recentBookings": [
      { "ticketId": 101, "customer": "Nguyễn Văn A", "routeName": "Hà Nội - Hải Phòng", "seatNumber": 15, "amount": 150000, "occurredAt": "2026-04-09T14:30:00" }
    ]
  },
  "timestamp": 1733728800000
}
```

| Field | Type | Map UI |
|---|---|---|
| `kpis.totalRevenue` / `.revenueTrendPercent` | BigDecimal | KPI card "Total Revenue" |
| `kpis.tripsCompleted` / `.tripsTrendPercent` | long / BigDecimal | KPI card "Trips Completed" |
| `kpis.ticketsSold` / `.ticketsTrendPercent` | long / BigDecimal | KPI card "Tickets Sold" |
| `kpis.activeCustomers` / `.customersTrendPercent` | long / BigDecimal | KPI card "Active Customers" |
| `topRoutes[]` | list | block "Top Routes" |
| `loyalCustomers[]` | list | block "Loyal Voyagers" |
| `recentBookings[]` | list | block "Recent Bookings" |

## 2. Xu hướng doanh thu (chart)

- **Gọi khi:** load trang, và lại mỗi khi đổi toggle khoảng thời gian trên "Revenue Trend".
- **Method & Path:** `GET /api/admin/revenue?period=monthly`
- **Controller:** `AdminDashboardController.java:37`
- **Auth:** `@RoleRequired(UserRole.ADMIN)`.

### Request

| Param | Type | Required | Default | Ghi chú |
|---|---|---|---|---|
| `period` | string | không | `"monthly"` | **danh sách giá trị hợp lệ chưa xác nhận được từ Controller** — cần hỏi backend (`daily`/`weekly`/`monthly`/`yearly`?) |

### Response (200)

```json
{
  "status": 200,
  "message": "Revenue trend fetched",
  "data": [
    { "label": "Apr 2026", "startDate": "2026-04-01", "endDate": "2026-04-30", "amount": 125500000 }
  ],
  "timestamp": 1733728800000
}
```

`data` là `List<RevenueTrendResponse>` — mỗi phần tử là 1 điểm trên chart.

## Requirements liên quan tới backend

- [ ] Xác nhận danh sách giá trị hợp lệ cho `period` — hiện chỉ biết default `"monthly"` từ code.
- [ ] Không có gì để bổ sung phía API — đây là màn hình sẵn sàng nhất, có thể code FE ngay.
