# Màn hình: Đăng ký tài khoản khách hàng

> Figma: node-id `2:3525` (tên frame: "Register") — file "Ticket-Buses" (`fileKey=QgeicQW2IuhLakGxpsQnr1`)
> Nhóm: Passenger/Public UI
> Slug: `customer-register`

## 1. Tổng quan

Form đăng ký tài khoản cho khách hàng đặt vé (Full Name, Email, Phone, Date of Birth, Password +
Confirm Password, Terms checkbox). Có strength-meter cho password ("Strong Security").

## 2. Basic Design

- Layout 1 cột, có background trang trí (SVG decorative).
- Khối chính: Header (heading) → Form Section (các field) → nút CTA "Button - CTA" → Footer Link
  (sang Login).

## 3. Detail Design

| Field | Loại | Placeholder mẫu (Figma) | Validate (đề xuất) |
|---|---|---|---|
| Full Name | text | "Johnathan Doe" | required |
| Email | text | "john@voyager.com" | required, format email |
| Phone | text | "901234567" | required, format số điện thoại |
| Date of Birth | 3 spinbutton (mm/dd/yyyy) | — | required, tuổi tối thiểu theo chính sách (chưa xác định) |
| Password | password | `••••••••` | required, có strength meter hiển thị "Strong Security" |
| Confirm Password | password | `••••••••` | required, phải khớp Password |
| Terms | checkbox/label | — | required tick trước khi submit |
| Nút CTA | button | "Button - CTA" (tên generic, cần xác nhận text thật, khả năng "Create Account") | disable khi form invalid |

**States:** default, password-strength theo thời gian gõ, lỗi từng field (inline), lỗi submit
(email đã tồn tại), loading khi submit.

## 4. Business Logic

1. Validate toàn bộ field ở client (bắt buộc, định dạng, khớp password).
2. Gọi `POST /api/auth/register`.
3. Backend tạo `User` mới với `role` (mặc định `CUSTOMER` theo `User.java:40` nếu không truyền),
   trả về `TokenResponse` → tự động đăng nhập sau khi đăng ký thành công (giống `login`, cũng ghi
   session Redis theo code hiện tại của `login`, cần xác nhận `register` có ghi Redis session
   tương tự không — hiện tại code `register` KHÔNG thấy ghi Redis, chỉ sinh token).
4. Điều hướng vào trang chủ / trang tìm chuyến sau khi đăng ký thành công.

## 5. API

| Method | Path | Trạng thái | Request | Response | Nguồn |
|---|---|---|---|---|---|
| POST | `/api/auth/register` | Đã có (nhưng thiếu field) | `UserRequestDto` (chỉ có `email`, `password`, `role` optional) | `BaseResponseDto<TokenResponse>` | `AuthController.java:38`, `UserRequestDto.java` |

**Gap quan trọng:** `UserRequestDto` hiện tại **không có** `fullName`, `phone`, `dateOfBirth` —
3 field này có trên UI nhưng backend chưa nhận/lưu được. Cần 1 trong 2 hướng:
1. Bổ sung field vào `UserRequestDto` + entity `User` (hiện `User.java` cũng không có các field này).
2. Hoặc tách sang một entity `Profile` riêng (đã thấy `Profile.java` tồn tại trong `entity/` — cần
   kiểm tra xem `Profile` có chứa các field này không trước khi thêm mới, tránh trùng).

## 6. Requirements

- [ ] Validate password confirm khớp password trước khi gọi API.
- [ ] Hiển thị lỗi rõ ràng khi email đã được đăng ký.
- [ ] (Blocking) Xác nhận nơi lưu `fullName`/`phone`/`dateOfBirth` — bổ sung DTO/entity trước khi
      implement FE form đầy đủ.
- [ ] (TODO/needs confirmation) Text thật của nút CTA (Figma đặt tên generic "Button - CTA").
- [ ] (TODO/needs confirmation) Có bắt buộc xác thực email/OTP sau đăng ký không, hay tự động active.
