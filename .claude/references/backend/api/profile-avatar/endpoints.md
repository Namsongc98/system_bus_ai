# API — Avatar hồ sơ

> Màn hình dùng: ProfileView (task 4.1, chưa có design doc — chạy `/clear-spec` trước khi làm FE)
> Quy ước chung: [`../_conventions.md`](../_conventions.md)
> Controller: `ProfileAvatarController` (`manage-revenue-ticket`, port `8082`), service `AvatarService`,
> lưu file trên MinIO (S3 API) — task **4.1a**, 2026-11-03.

## Endpoint

| Hành động UI | Method | Path | Trạng thái | Auth |
|---|---|---|---|---|
| Chọn ảnh → lưu (tạo hoặc thay) | PUT | `/api/profile/avatar` | ✅ Có | JWT, mọi role |
| Hiển thị avatar của mình | GET | `/api/profile/avatar` | ✅ Có | JWT, mọi role |
| Xoá avatar | DELETE | — | ❌ Chưa làm (4.1a D3: FE 4.1 quyết) | — |

- `userId` **luôn lấy từ JWT** (`request.getAttribute("id")` do `AuthInterceptor` đặt) — không có
  path/query param id, mỗi user chỉ đọc/ghi avatar của chính mình. Tài khoản bị khoá → 403.
- Một user một avatar, object key `avatars/{userId}` trong bucket `user-avatars`; upload lại là ghi đè.
- MinIO không public: ảnh luôn đi qua BE. Không có URL public nào cho ảnh (matcher `/avatars/**` đã bỏ ở 4.1a).

## 1. Upload / thay avatar

- **Method & Path:** `PUT /api/profile/avatar`
- **Content-Type:** `multipart/form-data`, đúng 1 part tên **`file`**.
- **Ràng buộc:** ≤ 2MB (`spring.servlet.multipart.max-file-size=2MB`, request ≤ 3MB); chỉ JPEG / PNG / WEBP,
  nhận diện bằng byte đầu file (magic bytes) — header `Content-Type` của part bị bỏ qua.

### Response 200

```json
{
  "status": 200,
  "message": "Upload avatar successfully",
  "data": { "contentType": "image/png", "size": 48213 }
}
```

### Lỗi

FE luôn đọc `status` + `message`; các field khác tuỳ nơi sinh lỗi:

| Nơi sinh lỗi | Body |
|---|---|
| `GlobalExceptionHandler` (400, 404, 405, 413, 415, 500) | `{status, error, message, path, timestamp}` |
| Spring Security `CustomAuthEntryPoint` (401 thiếu/sai JWT) | `{status, message}` |
| `AuthInterceptor` (401 user không còn, 403 tài khoản khoá) | `{status, message, timestamp}` (`BaseResponseDto`) |
| `JwtAuthFilter` catch-all (lỗi lạ phía sau filter) | 401 `{status, message, timestamp}` với `message` không cố định — lỗi đã biết, sửa ở 5.1 (plan B38 d) |

| HTTP | Khi nào | `message` |
|---|---|---|
| 400 | Part `file` rỗng | `Chưa chọn ảnh` |
| 400 | Không phải JPEG/PNG/WEBP (kể cả đổi đuôi `.png`) | `Chỉ nhận ảnh JPEG, PNG hoặc WEBP` |
| 400 | Thiếu part `file` (sai tên field) | `Thiếu phần 'file' trong form` |
| 400 | File > 2MB **chỉ khi** giới hạn multipart bị nới (dự phòng trong `AvatarService`) | `Ảnh tối đa 2MB` |
| 401 | Không có / sai / hết hạn token (Spring Security, trước khi tới controller) | `Token không hợp lệ hoặc đã hết hạn` |
| 401 | Token hợp lệ nhưng user không còn (`AuthInterceptor`) | `Unauthorized - Invalid or missing JWT` |
| 403 | Tài khoản bị khoá (`AuthInterceptor`, `AccountLockedException.MESSAGE`) | `Tài khoản đã bị khoá` |
| 405 | Sai method (ví dụ `POST`), header `Allow` có `GET`, `PUT` | `Phương thức không được hỗ trợ` |
| 413 | File > 2MB (chặn ở multipart resolver, `spring.servlet.multipart.max-file-size=2MB`; test `AvatarMultipartLimitTest` kiểm giá trị Spring thực sự áp) | `Tệp vượt quá dung lượng cho phép` |
| 415 | Body không phải multipart (ví dụ JSON) | `Định dạng nội dung không được hỗ trợ` |
| 500 | MinIO sập / sai key / quá 10s | `Lỗi hệ thống, vui lòng thử lại sau` (4.1a D2) |

## 2. Đọc avatar

- **Method & Path:** `GET /api/profile/avatar`
- **Response 200:** byte ảnh, `Content-Type` lấy lại từ magic bytes lúc đọc (`image/jpeg|png|webp`) — không tin
  Content-Type lưu trên object; `Cache-Control: no-cache, private`, `X-Content-Type-Options: nosniff`.
- **404** `Chưa có ảnh đại diện` khi user chưa upload; 401/403 như trên; 500 `Lỗi hệ thống…` khi MinIO lỗi, hết
  thời gian (gọi S3 tối đa 10s) hoặc object trong bucket không phải ảnh (ghi từ ngoài app).

## Ghi chú cho FE (task 4.1)

- Thêm constant vào `src/constants/api_endpoint.js`, gọi qua `apiClient` (có JWT) trong `src/services/`,
  store gọi service — không gọi axios trong page.
- Upload: `const form = new FormData(); form.append('file', file)` → `apiClient.put(url, form)`
  (để axios tự đặt boundary, không set `Content-Type` tay).
- Hiển thị: **không dùng thẳng `<img src="/api/profile/avatar">`** vì thẻ `img` không gửi header
  `Authorization`. Gọi `apiClient.get(url, { responseType: 'blob' })` → `URL.createObjectURL(blob)`,
  nhớ `URL.revokeObjectURL` khi đổi ảnh / rời trang. 404 → hiện avatar mặc định, không coi là lỗi.
- Kiểm trước ở FE (≤ 2MB, `accept="image/jpeg,image/png,image/webp"`) chỉ để báo sớm; BE vẫn là nơi quyết định.
