# Frontend API — Đăng ký tài khoản khách hàng

> Màn hình: [`.claude/docs/design/customer-register.md`](../../../../docs/design/customer-register.md)
> Backend thật: [`references/backend/api/customer-register/endpoints.md`](../../../backend/api/customer-register/endpoints.md)
> Quy ước chung: [`../_conventions.md`](../_conventions.md)
> File thật: `src/pages/auth/RegisterPage.vue`, `src/stores/auth.js` (`useAuthStore.register`), `src/services/authService.js`

## Nút nào gọi API nào

| Nút/UI trên `RegisterPage.vue` | Handler | API gọi | Trạng thái |
|---|---|---|---|
| Nút **"Create Account"** (submit form, disabled nếu chưa tick Terms) | `handleRegister()` → `authStore.register(form.value)` | `POST {API_BASE_URL_SYSTEM}/auth/register` | ⚠️ Có gọi API, mất dữ liệu |
| Icon mắt ở Password/Confirm | `showPassword`/`showConfirm` toggle | không gọi API | — |
| Password strength meter | `passwordStrength` computed, tính local (length/uppercase/digit/special-char) | không gọi API | — |
| Checkbox "I agree to Terms..." | `agreeTerms` ref, **bắt buộc để enable nút submit** (`:disabled="!agreeTerms"`) | không gửi lên backend | — |
| Link "Sign in" | `<router-link :to="{ name: ROUTE_NAMES.LOGIN }">` | điều hướng sang `admin-login` | ✅ |

## 1. Register — nút "Create Account"

- **Service:** `authService.register(payload)` → `apiClient.post(API_ENDPOINTS.AUTH.REGISTER, payload)`
  = `POST '/auth/register'`.
- **Form gửi nguyên `form.value`** (không lọc field trước khi gửi):
  ```js
  { fullName, email, phone, dateOfBirth, password, confirmPassword }
  ```

### ⚠️ Mất dữ liệu thật — không chỉ là gap tài liệu

Backend `UserRequestDto` (đã xác minh, xem
[backend doc](../../../backend/api/customer-register/endpoints.md)) **chỉ nhận 3 field**:
`email`, `password`, `role` (optional). Spring/Jackson bind theo tên field — 4 field còn lại FE gửi
lên (`fullName`, `phone`, `dateOfBirth`, `confirmPassword`) **không có field tương ứng trong DTO nên
bị Jackson bỏ qua hoàn toàn, không có lỗi, không có cảnh báo**. Người dùng điền đầy đủ form, bấm
"Create Account", tài khoản vẫn tạo thành công (vì `email`+`password` hợp lệ) — nhưng **Họ tên, số
điện thoại, ngày sinh không được lưu ở đâu cả**. Đây là bug mất dữ liệu thật đang chạy trong code
hiện tại, không phải giả định.

| Field UI | Có gửi lên? | Backend có nhận? |
|---|---|---|
| `email` | ✅ | ✅ |
| `password` | ✅ | ✅ |
| `fullName` | ✅ gửi | ❌ bị bỏ qua |
| `phone` | ✅ gửi | ❌ bị bỏ qua |
| `dateOfBirth` | ✅ gửi | ❌ bị bỏ qua |
| `confirmPassword` | ✅ gửi (nên chặn ở FE trước khi gửi, không cần gửi lên) | ❌ bị bỏ qua |

**Không tự xử lý bằng cách đổi tên field ở FE** — theo backend doc, hướng xử lý đúng cần chốt với
backend trước (mở rộng `UserRequestDto`/`User` entity, hoặc tạo thêm API `PUT /api/profile/{userId}`
ghi vào entity `Profile` sẵn có).

### So với backend thật (path/port)

| | FE | Backend thật |
|---|---|---|
| Path | `{API_BASE_URL_SYSTEM}/auth/register` → `http://localhost:8000/api/auth/register` (Kong) | `8082/api/auth/register` (Kong chuyển tiếp `/api/*` tới đây) |

Path segment khớp (`/auth/register`) — giống `admin-login`.

### Response

- Thành công (backend trả 201): giống hệt response Login (`accessToken`+`refreshToken`) —
  `authStore.register()` xử lý y hệt `login()` (set token, tự decode JWT lấy user, điều hướng theo
  `isAdmin`). Vì backend không truyền `role` (form không có ô chọn role, mặc định `CUSTOMER` phía
  entity), user mới luôn được điều hướng vào `TRIP_VIEW`, không bao giờ vào `ADMIN_DASHBOARD` — đúng
  nghiệp vụ (đây là màn đăng ký khách hàng, không phải tạo admin).
- Thất bại: `toast.error(err?.message || 'Registration failed. Please try again.')`.

## Requirements

- [ ] (Blocking, ưu tiên cao) Chốt hướng lưu `fullName`/`phone`/`dateOfBirth` với backend (xem
      [backend doc](../../../backend/api/customer-register/endpoints.md)) trước khi coi màn này là
      "đã xong" — hiện tại submit thành công nhưng âm thầm mất 3 field.
- [ ] Set đúng `VITE_KONG_API_URL` (`http://localhost:8000/api`, qua Kong).
- [ ] Cân nhắc chặn `confirmPassword !== password` ở FE trước khi gọi API (hiện `handleRegister` không
      có bước so khớp 2 field này trước khi submit — chỉ có UI hiển thị 2 ô, không có validate).
