# Màn hình: Trang chủ tìm chuyến + Kết quả tìm kiếm

> Figma: node-id `2:961` (tên frame: "Trip Selection") — file "Ticket-Buses" (`fileKey=QgeicQW2IuhLakGxpsQnr1`)
> Nhóm: Passenger/Public UI
> Slug: `trip-search-results`

## 1. Tổng quan

Trang chủ khách hàng: hero section có form tìm chuyến (Điểm đi / Điểm đến / Ngày đi) theo kiểu
glassmorphism, bên dưới là danh sách kết quả (3 trip card mẫu, card thứ 3 có nhãn "Premium Option").
Có Header (TopNavBar) và Footer dùng chung toàn site.

## 2. Basic Design

- `Header - TopNavBar`: logo, nav links, nút login/register.
- `Hero Section with Glassmorphism Search`: heading "Where to next?" + form search nổi trên ảnh nền.
- `Main - Trip Results Content`: heading kết quả + danh sách `Trip Card` (lặp lại theo số chuyến tìm
  được — Figma mock 3 card, card 3 có style riêng "Premium Option").
- `Footer`: quick links (Destinations, Schedules, Help Center), newsletter input.

## 3. Detail Design

| Field/Control | Loại | Placeholder/Ví dụ (Figma) | Ghi chú |
|---|---|---|---|
| Điểm đi | text/autocomplete | "Hà Nội" | Nên là dropdown/autocomplete từ danh sách bến/route có sẵn |
| Điểm đến | text/autocomplete | "Hải Phòng" | tương tự |
| Ngày đi | date picker | "Oct 24, 2024" | không cho chọn ngày quá khứ |
| Nút Search | button | — | disable khi thiếu điểm đi/đến |
| Trip Card | card | Giờ đi/đến, giá, số ghế trống (chưa đọc được số cụ thể từ text extraction, cần xem lại ảnh) | mỗi card có nút CTA riêng ("Button") để sang Seat Selection |
| Newsletter input (footer) | text | "Enter email" | không liên quan nghiệp vụ đặt vé |

**States:** trang trống trước khi search (chỉ có hero), loading khi đang tìm, empty-state khi không
có chuyến phù hợp (chưa thấy trong Figma — cần bổ sung thiết kế), danh sách kết quả.

## 4. Business Logic

1. User nhập điểm đi/đến/ngày → bấm Search.
2. FE cần gọi API tìm chuyến theo route (điểm đi/đến) + ngày → **API này hiện KHÔNG tồn tại trong
   backend** (xem mục 5). Đây là gap chặn được cả tính năng.
3. Chọn 1 trip card → điều hướng sang `seat-selection-checkout` kèm `tripId`.

## 5. API

| Method | Path | Trạng thái | Ghi chú |
|---|---|---|---|
| — | `GET /api/trip/search?from=&to=&date=` (đề xuất) | **Cần tạo mới** | Không có endpoint tìm chuyến theo route+ngày cho khách hàng. `TripController` hiện chỉ có: tạo trip (`POST /api/trip`, admin), `GET /api/trip/scheduled` (phân trang, không filter theo route/ngày, dùng cho Admin), `PUT /api/trip/{tripId}`, `GET /api/trip/{tripId}/revenue`. |
| — | `GET /api/route` (đề xuất, để autocomplete điểm đi/đến) | **Cần tạo mới** | `RouteController` hiện chỉ có `POST` và `PUT`, không có `GET` list. |

**Đề xuất response cho `GET /api/trip/search`:** danh sách trip kèm `routeName`, `startPoint`,
`endPoint`, `departureTime`, `arrivalTime`, giá vé thấp nhất, số ghế trống — hiện chưa có field "giá
vé" ở entity `Trip` (giá nằm ở `Ticket.price`, được set theo từng vé bán ra, không phải giá niêm yết
theo trip) → cần làm rõ mô hình giá vé (giá cố định theo trip/route, hay linh hoạt theo ghế).

## 6. Requirements

- [ ] (Blocking) Tạo API tìm chuyến theo điểm đi/điểm đến/ngày trước khi implement FE.
- [ ] (Blocking) Tạo API list routes để autocomplete điểm đi/đến.
- [ ] Làm rõ nguồn giá vé hiển thị trên trip card (giá niêm yết theo route/trip hay tính động).
- [ ] Thiết kế empty-state khi không có chuyến phù hợp.
- [ ] (TODO/needs confirmation) Số ghế trống hiển thị trên card lấy từ đâu (capacity bus trừ số vé
      đã bán theo trip?).
