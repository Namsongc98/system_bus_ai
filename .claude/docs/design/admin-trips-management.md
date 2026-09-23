# Màn hình: Quản lý chuyến đi

> Figma: node-id `2:2822` (tên frame: "Trips Management") — file "Ticket-Buses" (`fileKey=QgeicQW2IuhLakGxpsQnr1`)
> Nhóm: Admin Terminal
> Slug: `admin-trips-management`

## 1. Tổng quan

Quản lý chuyến đi dạng lịch (calendar) kết hợp danh sách chi tiết. Có filter sidebar, calendar grid
theo tháng, danh sách "Trips List Details" dạng card, và 1 bảng dạng "Full List Table View" (có vẻ là
view thay thế, ẩn mặc định).

## 2. Basic Design

- `Header Section`: heading + nhóm nút filter theo trạng thái (3 nút) + nút "Create Trip" (mở modal,
  xem `admin-create-trip-modal.md`).
- `Filters Sidebar/Bar`: 3 option filter (dạng card có ảnh minh hoạ — khả năng filter theo status:
  Scheduled/Ongoing/Completed/Cancelled).
- `Calendar View`: `Calendar Grid` theo tuần/tháng, ô có buổi có chuyến sẽ highlight.
- `Trips List Details`: card từng chuyến — vd "NYC ➔ DC, 08:00 AM - 12:30 PM, 84%" (84% khả năng là
  % lấp đầy ghế/occupancy).
- `Full List Table View`: bảng đầy đủ, có nút hành động trên từng dòng.

## 3. Detail Design

| Field | Nguồn dữ liệu | Ghi chú |
|---|---|---|
| Route (vd "NYC ➔ DC") | `Trip.route.routeName` hoặc `startPoint`/`endPoint` | — |
| Khung giờ | `Trip.departureTime` – `Trip.arrivalTime` | — |
| % lấp đầy | **không có field sẵn** | cần tính = số ghế đã bán (đếm `Ticket` theo `tripId`) / `Buses.capacity` |
| Trạng thái chuyến | `Trip.status` (`TripStatus`: SCHEDULED/ONGOING/COMPLETED/CANCELLED) | dùng cho filter tabs + màu badge |
| Doanh thu chuyến | `Trip.revenue` hoặc `GET /api/trip/{id}/revenue` | 2 nguồn khác nhau — cần chọn 1 |

**States:** loading calendar + list riêng biệt, filter theo status, chuyển view Calendar ↔ Table
(nếu đúng là 2 view thay thế nhau chứ không phải hiển thị đồng thời — cần xác nhận lại ảnh gốc).

## 4. Business Logic

1. Load trang → gọi `GET /api/trip/scheduled?page=&size=` lấy danh sách chuyến (hiện trả
   `Page<Map<String,Object>>` — kiểu generic, không có DTO rõ field).
2. Filter theo status/ngày → **API hiện không nhận tham số filter** (`GET /api/trip/scheduled` chỉ
   nhận `page`, `size`) — cần bổ sung `status`, `fromDate`, `toDate`.
3. Click "Create Trip" → mở modal (xem `admin-create-trip-modal.md` + `admin-schedule-trip-review.md`).
4. Sửa chuyến → `PUT /api/trip/{tripId}`.
5. Xoá chuyến → **chưa có API**.

## 5. API

| Method | Path | Trạng thái | Response | Nguồn |
|---|---|---|---|---|
| GET | `/api/trip/scheduled?page=&size=` | Đã có (thiếu filter) | `Page<Map<String,Object>>` | `TripController.java:30` |
| POST | `/api/trip` | Đã có | `TripRequestDto` → `Trip` | `TripController.java:24` |
| PUT | `/api/trip/{tripId}` | Đã có | `TripRequestDto` → `Trip` | `TripController.java:41` |
| GET | `/api/trip/{tripId}/revenue` | Đã có | `RevenueResponse` (`tripId`, `totalRevenue`, `averageRevenue`) | `TripController.java:53` |
| DELETE | `/api/trip/{tripId}` | **Cần tạo mới** | — | — |
| — | filter theo `status`/khoảng ngày trên `/scheduled` | **Cần bổ sung param** | — | — |

## 6. Requirements

- [ ] (Blocking) Bổ sung filter `status`/`fromDate`/`toDate` cho `GET /api/trip/scheduled` trước khi
      code filter sidebar + calendar.
- [ ] (Blocking) Tạo `DELETE /api/trip/{tripId}` (kèm ràng buộc: không cho xoá chuyến đã có vé bán,
      chỉ cho huỷ = đổi status `CANCELLED`).
- [ ] Đổi kiểu response `/scheduled` từ `Map<String,Object>` sang DTO rõ field để FE bind an toàn.
- [ ] Làm rõ cách tính "% lấp đầy" hiển thị trên card — tính ở FE hay backend trả sẵn.
- [ ] (TODO/needs confirmation) Calendar View và Full List Table View là 2 view thay thế nhau hay
      hiển thị song song — ảnh hưởng cấu trúc component.
