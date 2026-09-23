# Frontend API — Đăng nhập (Admin Terminal)

> Màn hình: [`.claude/docs/design/admin-login.md`](../../../../docs/design/admin-login.md)
> Backend thật: [`references/backend/api/admin-login/endpoints.md`](../../../backend/api/admin-login/endpoints.md)
> Quy ước chung: [`../_conventions.md`](../_conventions.md)
> File thật: `src/pages/auth/LoginPage.vue`, `src/stores/auth.js` (`useAuthStore.login`), `src/services/authService.js`

## Nút nào gọi API nào

| Nút/UI trên `LoginPage.vue` | Handler | API gọi | Trạng thái |
|---|---|---|---|
| Nút **"Login"** (submit form) | `handleLogin()` → `authStore.login(form.value)` | `POST {API_BASE_URL_SYSTEM}/auth/login` | ✅ Gọi qua Kong, path khớp backend |
| Icon mắt trong ô Password (toggle hiện/ẩn) | `togglePassword()` | không gọi API | — |
| Checkbox "Remember me" | `rememberMe` ref | không gọi API, không gửi lên backend, không lưu vào đâu cả | ❌ UI có, không có hiệu lực |
| Link "Forgot password?" | `<router-link to="/forgot-password">` | route `/forgot-password` không tồn tại trong `ROUTE_PATHS`/router — **404 khi click** | ❌ Route chưa tồn tại |
| Nút "Google" / "Facebook" (social login) | không có `@click` handler nào | không gọi API | ❌ Trang trí thuần, chưa có OAuth flow |
| Link "Sign up" | `<router-link to="/register">` | điều hướng sang `customer-register` | ✅ |

## 1. Login — nút "Login"

- **Service:** `authService.login(credentials)` (`src/services/authService.js`)
  ```js
  apiClient.post(API_ENDPOINTS.AUTH.LOGIN, credentials)  // POST '/auth/login'
  ```
- **Store:** `useAuthStore.login()` (`src/stores/auth.js`) — gọi `authService.login`, bóc payload bằng
  `getResponseData(res)` = `res?.data?.data ?? res?.data ?? res` (nhóm "trả nguyên AxiosResponse",
  xem [`../_conventions.md`](../_conventions.md#3-service-layer-hiện-tại-không-đồng-nhất-cách-bóc-response)
  mục 3), gọi `setTokens(data)` lưu `accessToken`/`refreshToken` vào `localStorage`, rồi
  `resolveCurrentUser(data)` — thử lấy `data.user`/`data.currentUser`/`data.profile` trước, nếu không
  có thì **tự decode JWT payload** (base64) để lấy user info (không gọi thêm API), fallback cuối mới
  gọi `authService.getMe()`.

### So với backend thật

| | FE gửi | Backend thật nhận (`AuthController.login` → `UserRequestDto`) |
|---|---|---|
| Path | `{API_BASE_URL_SYSTEM}/auth/login` → `http://localhost:8000/api/auth/login` (Kong) | `http://localhost:8082/api/auth/login` (Kong chuyển tiếp `/api/*` tới đây) |
| Body | `{ email, password }` (`form.value`, đúng 2 field `LoginPage.vue` có) | `{ email, password, role? }` — khớp, `role` không bắt buộc |

**Path segment sau `/api` khớp (`/auth/login` = `/auth/login`)**, FE gọi qua Kong `8000`
(xem [`../_conventions.md`](../_conventions.md#1-axios-client-thật-srcservicesaxiosjs-đã-đọc-trực-tiếp-code)
mục 1). Đây là 1 trong 4 domain path khớp hoàn toàn trong toàn hệ thống.

### Response — cách `LoginPage.vue` xử lý

- Thành công: `toast.success('Welcome back!')` rồi điều hướng theo `authStore.isAdmin` (đọc từ
  `user.value.role`, tự parse trong `normalizeRole()`: chứa chuỗi `"admin"` → `USER_ROLES.ADMIN`,
  ngược lại luôn là `USER_ROLES.USER`, **không phân biệt `DRIVER`/`COLLECTOR`/`CUSTOMER`** — 3 role
  này đều bị gộp chung thành "user" ở phía FE, chỉ tách Admin/không-Admin).
- Thất bại: `toast.error(err?.message || 'Login failed. Please check your credentials.')` — đọc
  đúng `.message` nên **vẫn hiển thị đúng message thật từ backend** dù object lỗi build sai field
  `code` ở nơi khác (xem `_conventions.md` mục 4).

### Gap cần biết khi debug màn này

- Nếu chưa set `VITE_KONG_API_URL=http://localhost:8000/api` (hoặc Kong chưa chạy), request sẽ lỗi
  (404 từ dev server hoặc connection-refused) — lỗi này KHÔNG liên quan gì đến sai email/password,
  dễ nhầm lẫn khi debug.
- Backend hiện **không chặn `isActive=false` khi login** (xem backend doc) — nếu FE có nhu cầu hiển
  thị thông báo "tài khoản đã bị khoá", backend cần bổ sung trước.
- `refreshToken` được lưu vào `localStorage` (`setTokens`) nhưng **`authService.refreshToken()` gọi
  tới `/auth/refresh` — endpoint này không tồn tại ở backend** (xem `../_conventions.md` mục 5) —
  nếu access token hết hạn, FE hiện không có cách nào tự làm mới, sẽ rơi vào nhánh 401 → tự logout.

## Requirements

- [ ] (Blocking) Set `VITE_KONG_API_URL` trỏ về Kong `http://localhost:8000/api` và bật Kong trước khi test bất kỳ luồng nào.
- [ ] Quyết định có cần route `/forgot-password` và nút Google/Facebook thật hay bỏ khỏi UI (hiện là
      dead UI, không nối API/route nào).
- [ ] `authService.refreshToken`/`.getMe`/`.logout` đang gọi `/auth/refresh`, `/auth/me`, `/auth/logout`
      — cả 3 đều không tồn tại ở backend thật (chỉ có `/auth/login`, `/auth/register`,
      `/auth/update-password`) — cần backend bổ sung hoặc FE bỏ các lời gọi này.
