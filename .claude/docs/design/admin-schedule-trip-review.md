# Màn hình: Modal tạo chuyến — Bước 4 (Final Review)

> Figma: node-id `2:4033` (tên frame: "Create Trip Flow") — file "Ticket-Buses" (`fileKey=QgeicQW2IuhLakGxpsQnr1`)
> Nhóm: Admin Terminal (modal)
> Slug: `admin-schedule-trip-review`
> **Liên quan:** đây là bước 4/4 của cùng 1 wizard với
> [`admin-create-trip-modal.md`](./admin-create-trip-modal.md) (`node-id 2:3625`, bước 1-3). Dữ liệu
> form giống hệt nhau — chỉ khác: file này mới thực sự **gọi API submit**.

## 1. Tổng quan

Bước cuối của wizard "Schedule New Trip" — tổng hợp lại toàn bộ lựa chọn (Route, Vehicle, Captain,
Timing) kèm mini-map minh hoạ tuyến, có badge trạng thái "SCHEDULED", trước khi bấm nút submit cuối
cùng.

## 2. Basic Design

- `Progress Steps` (4 bước: Route → Resources → Schedule → Review) — bước 4 đang active.
- `Final Review`:
  - Badge trạng thái ("SCHEDULED").
  - Route Visual Section: Departure/Destination + khoảng cách.
  - Details Grid 3 cột: `Resource 1: Bus` (mã xe, capacity, tag "ELITE" nếu có), `Resource 2: Driver`
    (ảnh, tên, chức danh/kinh nghiệm), `Schedule Info` (Departure/Arrival datetime + duration).
  - `Map/Route Visual Preview`: bản đồ minh hoạ tuyến (tên đường cao tốc mẫu).
- `Modal Footer`: nút Back to Schedule, Cancel, nút submit chính "Schedule Trip".

## 3. Detail Design

| Field | Nguồn (từ bước 1-3, không gọi API mới ở đây) |
|---|---|
| Departure/Destination + khoảng cách | `Route.startPoint`/`endPoint`, khoảng cách hiển thị dạng "420 mi" — đơn vị dặm trong Figma, cần đổi sang km cho khớp `Route.distanceKm` |
| Fleet Resource (mã xe, capacity, badge "ELITE") | `Buses.plateNumber`(map với "FV-2024-X1"?), `.capacity` — **badge "ELITE" không có field tương ứng ở entity `Buses`**, cần xác nhận đây là hạng xe (loại ghế/tiện ích) chưa được model hoá |
| Captain (driver) | tên, chức danh, số năm kinh nghiệm — **entity `User` không có các field này** (chỉ có `email`, `role`, `driverStatus`) |
| Timing | `TripRequestDto.departureTime`/`arrivalTime`, duration tính toán ở FE |
| Badge "SCHEDULED" | mặc định `TripRequestDto.status = SCHEDULED` |

**States:** review (mặc định), đang submit (loading trên nút "Schedule Trip"), lỗi submit (giữ modal
ở bước 4, hiện lỗi), thành công (đóng modal, hiện toast — xem `admin-toast-notifications.md`).

## 4. Business Logic

1. Hiển thị lại toàn bộ dữ liệu đã nhập ở bước 1-3 (không gọi API, chỉ đọc state FE).
2. Bấm "Schedule Trip" → gọi `POST /api/trip` với `TripRequestDto` đã build từ toàn bộ wizard.
3. Thành công → đóng modal, refresh danh sách ở `admin-trips-management.md`, hiện toast success.
4. Thất bại (vd trùng lịch Bus/Driver — nếu backend có validate) → giữ modal ở bước 4, hiện lỗi, cho
   phép "Back to Schedule" để sửa mà không mất dữ liệu.
5. "Back to Schedule" quay lại bước 1-3 (`admin-create-trip-modal.md`) mà không mất dữ liệu đã nhập.

## 5. API

| Method | Path | Trạng thái | Request | Response | Nguồn |
|---|---|---|---|---|---|
| POST | `/api/trip` | Đã có | `TripRequestDto` (`routeId`, `busId`, `driverId`, `departureTime`, `arrivalTime`, `revenue`, `status`) | `BaseResponseDto<Trip>` | `TripController.java:24` |

**Gap:** backend `tripService.createTrip` hiện chưa rõ có validate trùng lịch Bus/Driver hay không
(cần đọc `TripService` để xác nhận — không nằm trong phạm vi review Controller lần này). Nếu chưa có,
cần bổ sung trước khi cho phép tạo chuyến hàng loạt.

## 6. Requirements

- [ ] Chỉ gọi `POST /api/trip` ở bước này (bước 4), không gọi ở bước 1-3.
- [ ] Đổi đơn vị khoảng cách hiển thị sang km cho khớp `distanceKm` (Figma đang mock "mi").
- [ ] (Blocking, nếu cần đúng như Figma) Bổ sung field "hạng xe/ELITE" và thông tin tài xế (chức
      danh, số năm kinh nghiệm) vào entity nếu bắt buộc phải hiển thị — hoặc bỏ các field này khỏi
      UI nếu không phải ưu tiên MVP.
- [ ] Xử lý lỗi submit không làm mất dữ liệu đã nhập ở 3 bước trước.
- [ ] (TODO/needs confirmation) Xác nhận `TripService.createTrip` có check trùng lịch Bus/Driver
      chưa — nếu chưa, bổ sung trước khi nhiều Admin cùng tạo chuyến song song.
