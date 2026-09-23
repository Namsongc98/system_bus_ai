# Frontend API Reference — theo màn hình

> Đọc [`_conventions.md`](./_conventions.md) trước (2 axios client thật, cách bóc response, port mặc
> định lệch backend, bảng đối chiếu path toàn hệ thống) — không lặp lại ở từng file con. Mỗi màn hình
> có 1 folder riêng, file `endpoints.md` bên trong liệt kê: **nút/hành động UI nào gọi API nào** (đối
> chiếu trực tiếp code thật — service/store/page/component), field request gửi lên có khớp DTO backend
> thật hay không, và trạng thái sẵn sàng.
>
> Slug khớp 1:1 với [`.claude/docs/design/<slug>.md`](../../../docs/design/) (thiết kế UI) và
> [`references/backend/api/<slug>/endpoints.md`](../../backend/api/) (API backend thật) để tra cứu chéo.
> Thay thế cho tài liệu cũ [`api-document.md`](../_legacy/api-document.md) (giữ lại tham khảo, không
> còn là nguồn thật).

## Mục lục

### Nhóm A — Passenger / Public
| Màn hình | Folder | File thật (Vue) |
|---|---|---|
| Đăng nhập (Admin Terminal) | [`admin-login/`](./admin-login/endpoints.md) | `pages/auth/LoginPage.vue` |
| Đăng ký khách hàng | [`customer-register/`](./customer-register/endpoints.md) | `pages/auth/RegisterPage.vue` |
| Tìm chuyến + kết quả | [`trip-search-results/`](./trip-search-results/endpoints.md) | `pages/user/TripView.vue` *(chưa gọi API nào)* |
| Chọn ghế + checkout | [`seat-selection-checkout/`](./seat-selection-checkout/endpoints.md) | `pages/user/SeatView.vue` *(submit không tạo booking thật)* |
| Thanh toán + xác nhận | [`payment-booking-confirmation/`](./payment-booking-confirmation/endpoints.md) | `pages/user/QRConfirmPopup.vue` *(toàn bộ hardcode)* |
| Vé của tôi | [`my-tickets/`](./my-tickets/endpoints.md) | `pages/user/MyTickets.vue` |

### Nhóm B — Admin Terminal
| Màn hình | Folder | File thật (Vue) |
|---|---|---|
| Dashboard | [`admin-dashboard/`](./admin-dashboard/endpoints.md) | `pages/admin/DashboardView.vue` *(nối đúng nhất)* |
| Báo cáo doanh thu | [`admin-revenue-reports/`](./admin-revenue-reports/endpoints.md) | `pages/admin/RevenueReports.vue` |
| Quản lý Xe & Tuyến | [`admin-buses-routes/`](./admin-buses-routes/endpoints.md) | `pages/admin/BusesRoutes.vue` |
| Quản lý chuyến đi | [`admin-trips-management/`](./admin-trips-management/endpoints.md) | `pages/admin/TripsManagement.vue` |
| Quản lý người dùng | [`admin-user-management/`](./admin-user-management/endpoints.md) | `pages/admin/UserManagement.vue` *(chặn 100%, `UserController` rỗng)* |
| Modal tạo chuyến — bước 1-3 | [`admin-create-trip-modal/`](./admin-create-trip-modal/endpoints.md) | `components/common/Modal/ModalCreateTrip.vue` *(chung file với cột bên phải)* |
| Modal tạo chuyến — bước 4 (submit) | [`admin-schedule-trip-review/`](./admin-schedule-trip-review/endpoints.md) | `components/common/Modal/ModalCreateTrip.vue` |
| Modal tạo tuyến | [`admin-create-route-modal/`](./admin-create-route-modal/endpoints.md) | `components/common/Modal/ModalCreateRoute.vue` *(payload khớp backend 100%)* |
| Modal tạo xe | [`admin-create-bus-modal/`](./admin-create-bus-modal/endpoints.md) | `components/common/Modal/ModalCreateBus.vue` *(3 lỗi field cùng lúc)* |
| Pattern: Toast | [`admin-toast-notifications/`](./admin-toast-notifications/endpoints.md) | `composables/useToast.js` |
| Pattern: Xác nhận xoá | [`admin-delete-confirmation/`](./admin-delete-confirmation/endpoints.md) | `components/common/Modal/ModalDeleteRoute.vue` *(chỉ 1 modal được build, gọi API không tồn tại)* |

## Phát hiện xuyên suốt (đọc 1 lần, áp dụng cho nhiều màn)

1. **Base URL duy nhất qua Kong** — FE chỉ còn `apiClient`, base URL lấy từ `VITE_KONG_API_URL`
   (ví dụ `http://localhost:8000/api`, không có giá trị mặc định; `bookingClient` đã bị xoá). Kong tự
   định tuyến `/api/booking` → Booking Service và `/api/*` → Manage Revenue Service. Nếu thiếu biến
   này, **mọi API ở mọi màn đều lỗi**, bất kể path đúng hay sai. Xem [`_conventions.md`](./_conventions.md#1-axios-client-thật-srcservicesaxiosjs-đã-đọc-trực-tiếp-code) mục 1.
2. **Lệch số ít/số nhiều gần như toàn hệ thống** — `API_ENDPOINTS` dùng số nhiều
   (`/users`, `/trips`, `/buses`, `/routes`, `/tickets`), backend dùng số ít
   (`/api/user`, `/api/trip`, `/api/bus`, `/api/route`, `/api/ticket`). Chỉ Auth, Admin, Revenue,
   Booking khớp path thật. Xem [`_conventions.md`](./_conventions.md#5-đường-dẫn-path--lệch-số-ítsố-nhiều-gần-như-toàn-bộ-hệ-thống) mục 5.
3. **Response interceptor KHÔNG tự bóc `res.data`** khi thành công (chỉ bóc khi lỗi) — trái với những
   gì `services/api-service-rules.md`/`services/api-json-service.md` mô tả. Service layer thật chia
   làm 2 nhóm bóc response khác nhau, không đồng nhất — dễ gây lỗi khi viết store/page mới theo đúng
   1 nhóm mà không kiểm tra service đang gọi thuộc nhóm nào. Xem `_conventions.md` mục 2-3.
4. **`UserController` rỗng hoàn toàn ở backend** — chặn [`admin-user-management`](./admin-user-management/endpoints.md)
   100%, và chặn dropdown "Assigned Driver" ở [`admin-create-trip-modal`](./admin-create-trip-modal/endpoints.md).
5. **Không có API `GET` list cho Route** — chặn cột phải [`admin-buses-routes`](./admin-buses-routes/endpoints.md),
   dropdown Route ở [`admin-create-trip-modal`](./admin-create-trip-modal/endpoints.md), và toàn bộ
   [`trip-search-results`](./trip-search-results/endpoints.md).
6. **Không có API `DELETE` cho bất kỳ entity nào** — nút xoá ở
   [`admin-delete-confirmation`](./admin-delete-confirmation/endpoints.md) (chỉ Route có UI, gọi API
   không tồn tại) chắc chắn fail; Bus/Trip/User chưa có cả UI lẫn API.
7. **Luồng đặt vé khách hàng (`seat-selection-checkout` → `payment-booking-confirmation`) không tạo
   dữ liệu thật** — nút submit checkout chỉ mở popup "Booking Confirmed!" giả, không gọi bất kỳ API
   nào; `bookingService.createBooking()` đã viết đúng và path khớp backend, nhưng không được gọi.
   Đây là gap nghiêm trọng nhất trong toàn bộ 17 màn vì ảnh hưởng trực tiếp luồng nghiệp vụ chính.
8. **Field/enum lệch DTO backend ở modal tạo Bus** — `licensePlate` (FE) vs `plateNumber` (backend,
   tên khác hẳn, không bind được), field thừa `busNumber`, enum status hoàn toàn khác
   (`AVAILABLE`/`IN_USE`/`MAINTENANCE` vs `ACTIVE`/`INACTIVE`/`PENDING`). Xem
   [`admin-create-bus-modal`](./admin-create-bus-modal/endpoints.md).
9. **Lỗi API bị nuốt âm thầm ở `useBookingStore.fetchMyTickets`** — `catch` cố tình set
   `error.value = null` thay vì message lỗi thật, khác hành vi mọi store khác trong hệ thống — người
   dùng thấy vé mẫu (`MOCK_TICKETS`) mà không có cảnh báo API đang fail. Xem
   [`my-tickets`](./my-tickets/endpoints.md) mục 2.
10. **`api-document.md` (file cũ) mô tả sai gần như toàn bộ**: envelope field `code` (thật là
    `status`), path số nhiều cho hầu hết domain (thật là số ít), enum Bus status sai. Các file
    `endpoints.md` trong đây lấy path/field/response **trực tiếp từ code** (cả 2 phía FE và backend),
    ưu tiên dùng làm nguồn thật thay cho `api-document.md`. File cũ được giữ lại ở
    [`_legacy/`](./_legacy/) để tham khảo lịch sử.

## Xếp hạng mức độ "sẵn sàng nối API thật" (từ tốt nhất đến kém nhất)

| Hạng | Màn hình | Lý do |
|---|---|---|
| Tốt nhất | `admin-dashboard`, `admin-create-route-modal`, `admin-schedule-trip-review` | Field/path gần như khớp 100%, chỉ cần sửa port hoặc 1 path segment |
| Trung bình | `admin-login`, `customer-register` (mất field), `admin-buses-routes`, `admin-revenue-reports` (field response chưa xác định), `admin-create-trip-modal` (bị chặn bởi domain khác), `admin-trips-management` | Có gọi API thật, cần sửa path/field, hoặc bị chặn bởi 1 domain khác chưa sẵn sàng |
| Kém nhất | `seat-selection-checkout`, `payment-booking-confirmation`, `trip-search-results` (chưa nối handler nào) | Chưa gọi API thật dù service đã viết sẵn |
| Chặn cứng | `admin-user-management`, `admin-delete-confirmation` | Backend chưa có endpoint nào tồn tại, sửa gì ở FE cũng không giúp được |
