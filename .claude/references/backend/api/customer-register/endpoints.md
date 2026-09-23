# API — Đăng ký tài khoản khách hàng

> Màn hình: [`.claude/docs/design/customer-register.md`](../../../../docs/design/customer-register.md) · Figma `2:3525`
> Quy ước chung: [`../_conventions.md`](../_conventions.md)
> Controller: `AuthController` (`manage-revenue-ticket`, port `8082`)

## Endpoint dùng ở màn này

| Button/Hành động UI | Method | Path | Trạng thái | Auth |
|---|---|---|---|---|
| Nút CTA tạo tài khoản | POST | `/api/auth/register` | ⚠️ Đã có (thiếu field) | Public (`@PublicApi`) |

## 1. Register

- **Gọi khi:** user điền form (Full Name, Email, Phone, DOB, Password, Confirm Password, tick Terms)
  và bấm nút CTA.
- **Method & Path:** `POST /api/auth/register`
- **Controller:** `AuthController.java:38` (method `register`)
- **Auth:** Public.

### Request — **theo `UserRequestDto` thật, KHÔNG khớp đủ field UI**

```json
{
  "email": "john@voyager.com",
  "password": "StrongPass123",
  "role": "CUSTOMER"
}
```

| Field | Type | Required | Ghi chú |
|---|---|---|---|
| `email` | string | có | `@Email @NotBlank` |
| `password` | string | có | `@NotBlank @Size(min=6)` |
| `role` | string (enum `UserRole`) | không | optional — nếu không truyền, entity `User` mặc định `CUSTOMER` (`User.java:40`) |

**Gap (Blocking):** UI có `Full Name`, `Phone`, `Date of Birth`, `Confirm Password` — **không field nào
trong 4 field này có trong `UserRequestDto` hay entity `User`**. `Confirm Password` chỉ nên validate ở
FE (không gửi lên server). 3 field còn lại (`fullName`, `phone`, `dateOfBirth`) cần 1 trong 2 hướng xử
lý trước khi FE có thể lưu được:
1. Thêm field vào `UserRequestDto` + `User` entity.
2. Hoặc map sang entity `Profile` đã có sẵn (`entity/Profile.java`) — cần đọc `Profile.java` để xác
   nhận field tương ứng trước khi quyết định, và làm rõ API nào ghi vào `Profile` (có thể cần
   `POST /api/auth/register` trả về `userId` rồi gọi thêm 1 API `PUT /api/profile/{userId}` — **API
   này hiện không tồn tại, cần tạo mới nếu chọn hướng 2**).

### Response (201)

```json
{
  "status": 201,
  "message": "Register successfully",
  "data": {
    "accessToken": "eyJhbGciOiJIUzI1NiIs...",
    "refreshToken": "eyJhbGciOiJIUzI1NiIs..."
  },
  "timestamp": 1733728800000
}
```

Giống hệt response của Login — đăng ký xong tự động có token, không cần gọi thêm login.

**Lưu ý:** không thấy code ghi session Redis trong nhánh `register` (khác với `login` có ghi) — cần
xác nhận đây có phải chủ đích không, vì nếu không ghi Redis session, hành vi "đăng nhập tự động sau
khi đăng ký" có thể không nhất quán với các API khác đang dựa vào Redis session.

### Lỗi có thể gặp

| Status | Khi nào |
|---|---|
| 400 | vi phạm `@Email`/`@NotBlank`/`@Size` |
| 409 (đề xuất) | email đã tồn tại — cần xác nhận `authService.register` có check trùng và trả đúng status này không (chưa đọc `AuthService`) |

## Requirements liên quan tới backend

- [ ] (Blocking) Quyết định nơi lưu `fullName`/`phone`/`dateOfBirth` trước khi FE build form đầy đủ.
- [ ] Xác nhận `AuthService.register` có check email trùng và trả lỗi rõ ràng (409) không.
- [ ] Xác nhận có cần ghi Redis session ngay sau register giống `login` không, để hành vi nhất quán.
