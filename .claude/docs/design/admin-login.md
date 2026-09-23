# Màn hình: Đăng nhập (Admin Terminal)

> Figma: node-id `13:2` (tên frame gốc: "Frame 1") — file "Ticket-Buses" (`fileKey=QgeicQW2IuhLakGxpsQnr1`)
> Nhóm: Passenger/Public UI, dùng cho tài khoản nội bộ (Admin)
> Slug: `admin-login`

## 1. Tổng quan

Form đăng nhập cho tài khoản quản trị (`Fluid Voyager Admin`). Placeholder email trong Figma là
`admin@fluidvoyager.com` — xác nhận đây là cổng đăng nhập dành cho Admin Terminal, không phải app
khách hàng. Có thêm 2 nút "Social Login" (Google, Google — trùng lặp trong Figma, khả năng là
placeholder chưa hoàn thiện) và link sang trang Đăng ký.

**Lưu ý (gap):** trong 17 frame lấy được, không có frame "Login" riêng cho khách hàng (customer).
Chỉ có `customer-register.md`. Cần xác nhận với người thiết kế: khách hàng có dùng chung form này
(chỉ khác branding) hay chưa được thiết kế.

## 2. Basic Design

- Layout 1 cột, căn giữa màn hình, nền có overlay/blur (glassmorphism), logo + heading phía trên.
- Khối chính: `Glass Card` chứa toàn bộ form.
- Thứ tự từ trên xuống: Heading "Fluid Voyager Admin" → Form (Email, Password) → Actions (Remember
  me / Forgot password) → nút Login → Divider "or" → Social logins → Footer link sang Register.

## 3. Detail Design

| Field/Control | Loại | Placeholder/Label | Validate (đề xuất) |
|---|---|---|---|
| Email | text input | `EMAIL ADDRESS` — vd `admin@fluidvoyager.com` | required, đúng định dạng email |
| Password | password input | `Password` — hiển thị `••••••••` | required, tối thiểu 6 ký tự (khớp `UserRequestDto`) |
| Remember me / Forgot password | link/checkbox | — | không bắt buộc, chưa có API tương ứng |
| Nút Login | button (CTA) | "Login" | disable khi form invalid hoặc đang gọi API |
| Social login (Google ×2) | button | "Google" | Figma có 2 nút trùng tên — nghi vấn placeholder, cần hỏi lại designer |
| Signup Link | link | điều hướng sang `customer-register` | — |

**States cần có:** default, đang submit (loading trên nút Login), lỗi (email/password sai — hiển
thị message chung, không tiết lộ email tồn tại hay không), lỗi network.

## 4. Business Logic

1. User nhập email + password → validate client-side trước.
2. Gọi `POST /api/auth/login`.
3. Backend trả về `TokenResponse` (accessToken + refreshToken) nếu đúng; đồng thời server lưu
   session vào Redis với key `session:<userId>`, TTL 1 ngày (xem `AuthController.login`).
4. Client lưu access/refresh token (khuyến nghị: refresh token ở httpOnly cookie, access token ở
   memory) → điều hướng theo `role` trả về trong token/response (`ADMIN` → Admin Dashboard).
5. Không giới hạn số lần thử sai trong code hiện tại (không có rate-limit/lockout) — **rủi ro bảo
   mật cần bổ sung** nếu đưa lên production.

## 5. API

| Method | Path | Trạng thái | Request | Response | Nguồn |
|---|---|---|---|---|---|
| POST | `/api/auth/login` | Đã có | `UserRequestDto` (`email`, `password`, `role` optional) | `BaseResponseDto<TokenResponse>` (`accessToken`, `refreshToken`) | `AuthController.java:65` |

- Endpoint đánh dấu `@PublicApi` (không cần JWT để gọi).
- Không có endpoint riêng cho "logout" hay "refresh token" trong `AuthController` hiện tại — **cần
  bổ sung** nếu FE cần xoay vòng access token.

## 6. Requirements

- [ ] Validate email/password ở client trước khi gọi API, tránh call rỗng.
- [ ] Hiển thị lỗi generic khi sai email/mật khẩu (không lộ email có tồn tại hay không).
- [ ] Điều hướng theo `role` sau khi login thành công (không hard-code sang Admin Dashboard).
- [ ] Xử lý lỗi mạng/504 riêng biệt với lỗi sai thông tin đăng nhập.
- [ ] (TODO/needs confirmation) Xác nhận 2 nút Google login có thực sự cần 2 provider khác nhau không.
- [ ] (TODO/needs confirmation) Xác nhận có cần màn Login riêng cho khách hàng hay dùng chung form này.
