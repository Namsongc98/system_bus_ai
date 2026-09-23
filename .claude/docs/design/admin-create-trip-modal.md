# Màn hình: Modal tạo chuyến — Bước 1-3 (Route & Vehicle → Schedule → Preview)

> Figma: node-id `2:3625` (tên frame: "Create Trip Modal") — file "Ticket-Buses" (`fileKey=QgeicQW2IuhLakGxpsQnr1`)
> Nhóm: Admin Terminal (modal)
> Slug: `admin-create-trip-modal`
> **Liên quan:** đây là bước 1-3 của 1 wizard 4 bước. Bước 4 (Final Review + submit) nằm ở file
> riêng [`admin-schedule-trip-review.md`](./admin-schedule-trip-review.md) (`node-id 2:4033`). 2 file
> mô tả **cùng 1 form dữ liệu**, chỉ khác bước hiển thị.

## 1. Tổng quan

Modal CRUD "Schedule New Trip" — form nhập tuyến/xe/tài xế + lịch trình, có `Section 3: Preview Glass
Card` xem trước ngay trong modal trước khi qua bước Final Review.

## 2. Basic Design

- `Modal Header`: tiêu đề + nút đóng (X).
- `Modal Body (Scrollable)`:
  - `Section 1: Route & Vehicle` — chọn Route (search), Bus Unit (select), Assigned Driver (select).
  - `Section 2: Schedule` — Departure (date + time), Estimated Arrival (date + time).
  - `Section 3: Preview Glass Card` — xem trước From/To, Vehicle, Capacity theo lựa chọn ở trên.
- `Modal Footer`: nút Cancel + nút Next/Continue (sang bước Final Review).

## 3. Detail Design

| Field | Loại | Placeholder (Figma) | Map request (`TripRequestDto`) |
|---|---|---|---|
| Route | search/select | "Search routes..." | `routeId` |
| Bus Unit | select | "Select available bus" | `busId` |
| Assigned Driver | select | "Select driver" | `driverId` |
| Departure | date + time (6 spinbutton: mm/dd/yyyy + hh/mm/AM-PM) | — | `departureTime` |
| Estimated Arrival | date + time (tương tự) | — | `arrivalTime` |
| Preview: From/To | text (đọc từ Route đã chọn) | vd "London Victoria" | tính toán từ `Route.startPoint`/`endPoint` |
| Preview: Vehicle/Capacity | text (đọc từ Bus đã chọn) | vd "Voyager X-102", "52 Seats" | `Buses.plateNumber` (không khớp — Figma ghi "Voyager X-102" như tên xe, backend chỉ có `plateNumber`; cần xác nhận có field "tên xe" riêng không), `Buses.capacity` |

**Validate đề xuất:**
- `departureTime` < `arrivalTime`.
- `departureTime` phải ở tương lai (không tạo chuyến trong quá khứ) — trừ khi nghiệp vụ cho phép nhập
  liệu chuyến đã chạy.
- Bus/Driver không được trùng lịch với chuyến khác đã `SCHEDULED`/`ONGOING` trong cùng khung giờ
  (**chưa có logic check overlap ở backend hiện tại** — `TripService.createTrip` cần bổ sung).

**States:** loading danh sách Route/Bus/Driver khi mở modal, validate lỗi từng field, đang submit.

## 4. Business Logic

1. Mở modal → load song song danh sách Route (autocomplete), Bus khả dụng, Driver khả dụng.
2. Chọn Route/Bus → `Section 3: Preview` tự cập nhật theo lựa chọn (không gọi API riêng, tính từ data
   đã load).
3. Nhập lịch trình → validate.
4. Bấm Next → chuyển sang bước Final Review (`admin-schedule-trip-review.md`) — dữ liệu giữ ở state
   FE, **submit thật sự chỉ diễn ra ở bước 4**, không gọi API ở bước này.

## 5. API

| Method | Path | Trạng thái | Ghi chú |
|---|---|---|---|
| — | `GET /api/route` (autocomplete) | **Cần tạo mới** | Xem thêm gap ở `admin-buses-routes.md` |
| GET | `/api/bus?page=&size=` | Đã có (dùng tạm để lấy danh sách xe khả dụng, chưa filter theo "khả dụng trong khung giờ") | `BusController.java:24` |
| — | `GET /api/user?role=DRIVER` (list tài xế khả dụng) | **Cần tạo mới** | Phụ thuộc `admin-user-management.md` |
| POST | `/api/trip` | Đã có — dùng ở bước Final Review, không phải bước này | `TripController.java:24` |

## 6. Requirements

- [ ] (Blocking) Cần `GET /api/route` và `GET /api/user?role=DRIVER` trước khi implement Section 1.
- [ ] Validate không cho chọn Bus/Driver đang bận trong khung giờ đã chọn — cần API/logic kiểm tra
      overlap lịch (chưa có ở backend).
- [ ] Preview card (Section 3) chỉ tính từ dữ liệu đã chọn, không gọi thêm API.
- [ ] Giữ state form khi chuyển qua lại giữa bước 1-3 (file này) và bước 4 (`admin-schedule-trip-review.md`).
- [ ] (TODO/needs confirmation) "Voyager X-102" trong preview là tên xe hay chính là `plateNumber` —
      xác nhận vì entity `Buses` hiện chỉ có `plateNumber`, không có field "tên xe" riêng.
