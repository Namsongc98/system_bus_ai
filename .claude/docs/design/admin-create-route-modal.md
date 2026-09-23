# Màn hình: Modal tạo tuyến đường

> Figma: node-id `2:3833` (tên frame: "Create Route Modal") — file "Ticket-Buses" (`fileKey=QgeicQW2IuhLakGxpsQnr1`)
> Nhóm: Admin Terminal (modal)
> Slug: `admin-create-route-modal`

## 1. Tổng quan

Modal tạo/sửa tuyến đường — form khớp gần như 1:1 với `RouteRequestDto` ở backend, đây là 1 trong số
ít màn hình **không có gap block nào**, có thể implement ngay.

## 2. Basic Design

- `Header`: tiêu đề + nút đóng.
- `Scrollable Content` → `Form`:
  - `Route Name Input`.
  - `Location Details`: Origin Terminal, Destination Terminal.
  - `Distance Input`.
  - `Status Toggle`.
  - `Preview Card`: xem trước tuyến trên nền bản đồ trừu tượng.
- `Footer`: 2 nút (Cancel / Save).

## 3. Detail Design

| Field | Loại | Placeholder (Figma) | Map (`RouteRequestDto`) | Validate |
|---|---|---|---|---|
| Route Name | text | "e.g. Coastal Express Alpha" | `routeName` | required |
| Origin Terminal | text | — | `startPoint` | required |
| Destination Terminal | text | — | `endPoint` | required, khác Origin |
| Distance | number | — | `distanceKm` | required, > 0 |
| Route Status | toggle | — | `status` (`RouteStatus`: ACTIVE/INACTIVE) | mặc định `ACTIVE` theo backend |
| Preview Card | read-only | tổng hợp từ các field trên | — | — |

**States:** default (tạo mới, mặc định Status = Active), edit (điền sẵn dữ liệu route hiện có), lỗi
validate từng field, đang lưu.

## 4. Business Logic

1. Điền form → validate client-side (bắt buộc, khác Origin/Destination, distance > 0).
2. Tạo mới → `POST /api/route`. Sửa → `PUT /api/route/{routeId}`.
3. Sau khi lưu thành công → đóng modal, refresh danh sách ở `admin-buses-routes.md`, hiện toast
   thành công (xem `admin-toast-notifications.md`).
4. Lưu thất bại → giữ modal mở, hiện lỗi, không đóng modal (tránh mất dữ liệu đã nhập).

## 5. API

| Method | Path | Trạng thái | Request | Response | Nguồn |
|---|---|---|---|---|---|
| POST | `/api/route` | Đã có | `RouteRequestDto` | `BaseResponseDto<Route>` | `RouteController.java:18` |
| PUT | `/api/route/{routeId}` | Đã có | `RouteRequestDto` | `BaseResponseDto<Route>` (response body hiện trả `null`, không trả lại Route đã update — cần xác nhận có cần sửa không) | `RouteController.java:25` |

## 6. Requirements

- [ ] Validate Origin ≠ Destination trước khi submit.
- [ ] Sau khi tạo/sửa thành công, đồng bộ lại danh sách route ở `admin-buses-routes.md` (không có
      `GET /api/route` list — xem gap ở file đó, ảnh hưởng cả modal này khi cần refresh).
- [ ] Giữ dữ liệu form khi submit lỗi, không tự đóng modal.
- [ ] (TODO/needs confirmation) `PUT /api/route/{routeId}` hiện trả `null` ở body — xác nhận FE có
      cần response trả lại `Route` đã cập nhật để tránh phải gọi lại API list ngay sau đó không.
