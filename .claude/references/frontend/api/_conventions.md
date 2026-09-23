# Quy ước dùng chung — Frontend API Reference (đọc trước khi vào từng màn)

> Áp dụng cho mọi file trong `references/frontend/api/<màn>/endpoints.md`. Không lặp lại nội dung này
> ở từng file con — chỉ trỏ về đây. Đối chiếu song song với
> [`references/backend/api/_conventions.md`](../../backend/api/_conventions.md) (quy ước backend thật)
> — 2 file KHÔNG giống nhau, vì FE code hiện tại có nhiều điểm lệch so với backend thật.

## 1. Axios client thật (`src/services/axios.js`, đã đọc trực tiếp code)

Chỉ có **1 client duy nhất**, tạo qua factory `createClient(baseURL)`:

| Client | Export | Base URL | Dùng cho |
|---|---|---|---|
| `apiClient` | default export của `axios.js` | `API_BASE_URL_SYSTEM` = `import.meta.env.VITE_KONG_API_URL` (không có giá trị mặc định) | Toàn bộ API, kể cả Booking (`bookingService.createBooking` → `POST /booking`) |

Không còn `bookingClient` và `API_BASE_URL_BOOKING`. FE **luôn gọi qua Kong**
(`http://localhost:8000/api`), không gọi thẳng service `8081`/`8082`. Kong tự định tuyến theo path
(xem `ticket-system/Infrastructure/kong/kong.yml`):

| Path FE gọi | Kong route | Service đích |
|---|---|---|
| `/api/booking` | `booking-route` (priority 10) | Booking Service (`booking-container:8081`) |
| `/api/*` còn lại | `revenue-route` (priority 5) | Manage Revenue Service (`manage-revenue-ticket:8082`) |

**⚠️ Bắt buộc set `VITE_KONG_API_URL`** (ví dụ `http://localhost:8000/api`) trong file biến môi
trường của FE. `API_BASE_URL_SYSTEM` không có giá trị dự phòng: nếu thiếu, `baseURL` là `undefined`,
axios gọi tương đối về dev server `:5173` và **toàn bộ request FE sẽ lỗi 404**, không liên quan gì đến
việc path đúng hay sai. Cổng `8001` là **Kong Admin API**, không phải Booking Service — tuyệt đối không
trỏ FE vào đó. Xác nhận biến này trước khi debug bất kỳ lỗi API nào ở FE.

## 2. Interceptor — request/response (đã đọc trực tiếp code, không suy đoán)

```js
// Request: tự gắn JWT nếu có trong localStorage (LOCAL_STORAGE_KEYS.ACCESS_TOKEN)
config.headers.Authorization = `Bearer ${token}`

// Response — THÀNH CÔNG: trả nguyên response Axios, KHÔNG tự bóc res.data
(response) => response

// Response — LỖI: bóc 1 lớp, ném error.response.data (nếu có)
(error) => Promise.reject(error.response?.data ?? error)
```

**Hệ quả quan trọng, áp dụng cho mọi service/store:**

- **Khi thành công:** service nhận về nguyên `AxiosResponse`. Muốn lấy payload backend thật (field
  `data` trong `BaseResponseDto`) phải bóc **2 lớp**: `response.data` (Axios) → `.data` (backend
  envelope). Phần lớn store/page trong code thật đang tự viết:
  ```js
  response?.data?.data ?? response?.data ?? response
  ```
  để phòng trường hợp service đã tự bóc 1 lớp trước đó (không đồng nhất giữa các service — xem mục 3).
- **Khi lỗi:** caller (store/page) nhận thẳng **object lỗi backend thật** (`{status, message, data,
  timestamp}` nếu backend trả đúng envelope) hoặc Axios error gốc nếu không có `error.response` (lỗi
  mạng/timeout/connection refused — trường hợp cổng sai ở mục 1 rơi vào đây). Đọc `err?.message` là an
  toàn ở cả 2 trường hợp; `err?.code` **không tồn tại** trong response thật của backend (xem mục 4).
- **401 không thuộc `/auth/**`:** tự xoá token + `user` khỏi localStorage, redirect `ROUTE_NAMES.LOGIN`.
  Request tới chính `/auth/login`/`/auth/register` bị lỗi 401 sẽ **không** bị redirect (loại trừ theo
  `error.config?.url?.includes('/auth/')`).

## 3. Service layer hiện tại KHÔNG đồng nhất cách bóc response

`rules/api-service-rules.md`/`services/api-json-service.md` (tài liệu quy ước) nói **"Return `res.data`
for JSON endpoints"**, nhưng code thật rẽ làm 2 nhóm:

| Nhóm | Ví dụ | Hành vi thật |
|---|---|---|
| Trả nguyên `AxiosResponse`, không bóc gì | `authService`, `userService`, `tripService`, `seatService`, `ticketService`, `paymentService`, `busRouteService` (object-style service, method trả thẳng `apiClient.get(...)`) | Store/page phải tự bóc `response?.data?.data ?? response?.data` |
| Tự bóc 1 lớp `res.data` bên trong service (`async () => { const res = await apiClient...; return res.data }`) | `adminService`, `getRevenueReport`/`getRevenueByRoute`/`getRevenueByDate`/`getTopCustomers` (`revenueService.js`), `getMyPoints`/`earnPoints`/`redeemPoints` (`loyaltyService.js`), `getSalaries`/`calculateSalary`/`getBaseSalaries` (`salaryService.js`), `createBooking` (`bookingService.js`) | Caller chỉ cần bóc **thêm 1 lớp** (`response?.data`) để lấy payload thật, bóc 2 lớp như nhóm trên sẽ SAI (lấy nhầm field con của payload) |

**Không có quy tắc rõ ràng để phân biệt 2 nhóm nếu không đọc trực tiếp code từng service** — mỗi file
`endpoints.md` bên dưới ghi rõ nhóm nào cho từng API để tránh nhầm khi code mới dựa theo.

## 4. Response envelope backend — FE đang tài liệu SAI, cần đọc theo bản backend thật

- **Tài liệu FE cũ** (`api/_legacy/api-document.md`, `services/api-error-handling.md`,
  `services/pinia-store.md`) đều ghi field là **`code`**: `{ "code": 200, "message": ..., "data": ... }`.
- **Backend thật** (đã xác minh trực tiếp `BaseResponseDto.java`, xem
  [`backend/api/_conventions.md`](../../backend/api/_conventions.md#2-response-envelope--đã-xác-minh-trong-code))
  dùng field **`status`**, không phải `code`: `{ "status": 200, "message": ..., "data": ..., "timestamp": ... }`.
- Code lỗi hiện tại ở nhiều service (`revenueService.js`, `loyaltyService.js`, `salaryService.js`) tự
  build lại object lỗi dạng `{ code: error.response?.data?.code || 500, message: ... }` — field
  `code` này **luôn `undefined`** vì backend không trả field đó, nên luôn fallback về `500` dù backend
  trả đúng status code khác (400/401/403/404). Không phải bug nghiêm trọng (message vẫn đúng), nhưng
  bất kỳ logic nào rẽ nhánh theo `err.code` ở FE hiện tại đều không hoạt động như kỳ vọng.

## 5. Đường dẫn (path) — lệch số ít/số nhiều gần như toàn bộ hệ thống

`src/constants/api_endpoint.js` định nghĩa `API_ENDPOINTS` gần như toàn bộ ở dạng **số nhiều**
(`/users`, `/trips`, `/buses`, `/routes`, `/tickets`, `/payments`), trong khi backend thật dùng
**số ít** (`/api/user`, `/api/trip`, `/api/bus`, `/api/route`, `/api/ticket`) — ngoại lệ **`/auth/**`**
khớp đúng cả 2 phía. Bảng đối chiếu đầy đủ:

| Domain | FE (`API_ENDPOINTS`) | Backend thật | Khớp? |
|---|---|---|---|
| Auth | `/auth/login`, `/auth/register`, `/auth/update-password` | `/api/auth/login`, `/api/auth/register`, `/api/auth/update-password` | ✅ Khớp (chỉ khác baseURL/port) |
| Auth | `/auth/logout`, `/auth/refresh`, `/auth/me` | *(không tồn tại ở backend)* | ❌ FE gọi API không có thật |
| User | `/users`, `/users/{id}`, `/users/profile` | *(`UserController` rỗng — không endpoint nào tồn tại)* | ❌ Toàn bộ domain |
| Trip | `/trips`, `/trips/{id}`, `/trips/search`, `/trips/{id}/complete` | `/api/trip` (POST tạo), `/api/trip/scheduled` (GET list), `/api/trip/{id}` (PUT), `/api/trip/{id}/revenue` (GET) | ❌ Lệch cả path lẫn semantics (list thật nằm ở `/scheduled`, không phải path gốc) |
| Seat | `/trips/{tripId}/seats`, `/seats/{id}` | *(không tồn tại — ghế không phải entity riêng ở backend, chỉ là field `seatNumber` trên `Ticket`)* | ❌ Toàn bộ domain — mô hình dữ liệu 2 bên khác nhau, không chỉ lệch path |
| Ticket | `/tickets`, `/tickets/{id}`, `/tickets/my`, `/tickets/{id}/cancel` | `/api/ticket` (POST), `/api/ticket/{tripId}` (PUT, param đặt tên gây nhầm) | ❌ Không có list/`my`/`cancel` ở backend |
| Payment | `/payments`, `/payments/{id}`, `/payments/{ticketId}/qr`, `/payments/{id}/confirm` | *(không có `PaymentController`/entity `Payment` nào ở backend)* | ❌ Toàn bộ domain — backend không có khái niệm Payment tách riêng khỏi Ticket |
| Bus | `/buses`, `/buses/{id}` | `/api/bus`, `/api/bus/{id}` | ❌ Số nhiều/số ít |
| Route | `/routes`, `/routes/{id}` | `/api/route`, `/api/route/{id}` | ❌ Số nhiều/số ít |
| Admin | `/admin/dashboard`, `/admin/revenue` | `/api/admin/dashboard`, `/api/admin/revenue` | ✅ Khớp (chỉ khác baseURL/port) |
| Revenue | `/revenue/report`, `/revenue/by-route`, `/revenue/by-date`, `/revenue/top-customers` | `/api/revenue/report`, `/api/revenue/by-route`, `/api/revenue/by-date`, `/api/revenue/top-customers` | ✅ Khớp (chỉ khác baseURL/port) |
| Loyalty | `/loyalty-points`, `/loyalty-points/earn`, `/loyalty-points/redeem`, `/loyalty-rewards` | *(không nằm trong 17 màn Figma, chưa đối chiếu — ngoài phạm vi review này)* | — |
| Salary | `/salary`, `/salary/calculate`, `/base-salary` | *(không nằm trong 17 màn Figma, chưa đối chiếu — ngoài phạm vi review này)* | — |
| Booking | `/booking` (qua `apiClient`) | `/api/booking` (module `booking_ticket`, Kong route riêng) | ✅ Khớp path (chỉ lỗi nếu `VITE_KONG_API_URL` thiếu/sai — xem mục 1) |

**Chỉ 3 domain khớp path thật sự (Auth, Admin, Revenue, Booking)** — đây cũng là các domain FE code
hiện có khả năng hoạt động cao nhất nếu sửa đúng port. Domain còn lại (User, Trip, Seat, Ticket,
Payment, Bus, Route) đều cần sửa path trước khi có thể gọi thông.

## 6. Ký hiệu "Trạng thái" dùng trong các bảng endpoint (giống backend, đối tượng khác)

| Ký hiệu | Ý nghĩa (áp dụng cho phía FE) |
|---|---|
| ✅ Đã nối API thật | Nút/hành động UI có gọi service → apiClient, path/field đối chiếu đúng với backend (hoặc chỉ lệch port/prefix có thể sửa nhanh) |
| ⚠️ Có gọi API nhưng lệch | Có gọi service thật, nhưng path/field/enum lệch backend đủ để fail nếu không sửa |
| ❌ Không gọi API (stub/no-op/hardcode) | Nút UI tồn tại nhưng handler rỗng, hoặc dùng thẳng constant `*_FALLBACK_*`/`*_FAKE_*` không qua service nào |

## 7. Liên kết

- Thiết kế UI/UX từng màn: [`.claude/docs/design/<slug>.md`](../../../docs/design/)
- API thật của backend từng màn: [`references/backend/api/<slug>/endpoints.md`](../../backend/api/)
- Quy ước response/auth backend thật: [`references/backend/api/_conventions.md`](../../backend/api/_conventions.md)
- Quy tắc viết service layer (tài liệu quy ước, một số chỗ không khớp code thật — xem mục 3-4):
  [`../services/api-service.md`](../services/api-service.md), [`../rules/api-service-rules.md`](../rules/api-service-rules.md)
- Tài liệu cũ đã được thay thế bởi thư mục này: [`_legacy/api-document.md`](./_legacy/api-document.md),
  [`_legacy/trips-management-api-readiness.md`](./_legacy/trips-management-api-readiness.md)
