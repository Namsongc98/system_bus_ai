# API — Đăng nhập (Admin Terminal)

> Màn hình: [`.claude/docs/design/admin-login.md`](../../../../docs/design/admin-login.md) · Figma `13:2`
> Quy ước chung: [`../_conventions.md`](../_conventions.md)
> Controller: `AuthController` (`manage-revenue-ticket`, port `8082`)

## Endpoint dùng ở màn này

| Button/Hành động UI | Method | Path | Trạng thái | Auth |
|---|---|---|---|---|
| Nút "Login" | POST | `/api/auth/login` | ✅ Đã có | Public (`@PublicApi`, có trong `permitAll`) |

## 1. Login

- **Gọi khi:** user điền Email + Password, bấm nút **"Login"**.
- **Method & Path:** `POST /api/auth/login`
- **Controller:** `AuthController.java:65` (method `login`)
- **Auth:** Public — không cần token để gọi API này (đây chính là API tạo token).

### Request

```json
{
  "email": "admin@fluidvoyager.com",
  "password": "your-password"
}
```

| Field | Type | Required | Ghi chú |
|---|---|---|---|
| `email` | string | có | không có annotation validate ở `UserRequestDto` cho field này khi dùng cho login (validate `@Email`/`@NotBlank` chỉ chắc chắn áp dụng ở `register`, cần FE tự validate thêm) |
| `password` | string | có | so khớp password đã hash trong DB |
| `role` | string (enum `UserRole`) | không | field có tồn tại trong `UserRequestDto` nhưng không cần thiết khi login (chỉ dùng để tạo `User` object tạm ở code, không ảnh hưởng logic xác thực) |

### Response (200)

```json
{
  "status": 200,
  "message": "Login successfully",
  "data": {
    "accessToken": "eyJhbGciOiJIUzI1NiIs...",
    "refreshToken": "eyJhbGciOiJIUzI1NiIs..."
  },
  "timestamp": 1733728800000
}
```

| Field | Type | Ghi chú |
|---|---|---|
| `data.accessToken` | string (JWT) | dùng cho header `Authorization: Bearer <accessToken>` ở mọi API sau |
| `data.refreshToken` | string (JWT) | **không có endpoint `/api/auth/refresh` nào để đổi lại access token hết hạn** — cần tạo mới nếu muốn refresh-token flow hoạt động |

### Hiệu ứng phụ (side effect) cần biết

- Server ghi session vào Redis: key `session:<userId>`, TTL **1 ngày** (`redisTemplate.opsForValue().set(...)`, `AuthController.java` trong `login`). Payload lưu: `userId`, `email`, `role`, `loginTime`.
- Không thấy logic kiểm tra `isActive=false` trước khi cho login — **user bị khoá (`isActive=false`)
  vẫn đăng nhập được** theo code hiện tại, cần xác nhận có phải là gap hay chủ đích.

### Lỗi có thể gặp

| Status | Khi nào |
|---|---|
| 400/401 | sai email/password — message cụ thể tuỳ implement `authService.login` (chưa đọc chi tiết `AuthService`) |
| 401 | thiếu/sai định dạng token ở các API gọi *sau* bước login (không áp dụng cho chính API này) |

## Requirements liên quan tới backend

- [ ] (Blocking, nếu cần) Tạo API refresh token — hiện có `refreshToken` trả về nhưng không nơi nào dùng lại.
- [ ] Xác nhận có chặn user `isActive=false` đăng nhập hay không; nếu chưa, bổ sung.
- [ ] Không có rate-limit/lockout sau N lần sai — cân nhắc bổ sung trước production (đã ghi ở `.claude/docs/design/admin-login.md`).
