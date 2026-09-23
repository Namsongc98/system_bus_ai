# Quy ước dùng chung cho toàn bộ API reference (đọc trước khi vào từng màn)

> Áp dụng cho mọi file trong `references/backend/api/<màn>/endpoints.md`. Không lặp lại nội dung này
> ở từng file con — chỉ trỏ về đây.

## 1. Service & Base URL

| Module (Maven) | Port mặc định | Ghi chú |
|---|---|---|
| `booking_ticket` | `8081` | Chỉ có `BookingController` (`/api/booking`) — nhận request đặt vé, đẩy vào Kafka |
| `manage-revenue-ticket` | `8082` | Toàn bộ API quản trị: Auth, Trip, Route, Bus, Ticket, Revenue, Admin Dashboard, Loyalty, Salary |

## 2. Response Envelope — **đã xác minh trong code, không phải suy đoán**

Tất cả response REST (trừ export file nhị phân như `.xlsx`) đi qua `BaseResponseDto<T>`
(`common-library/.../Dto/response/BaseResponseDto.java`):

```json
{
  "status": 200,
  "message": "Get Successfully",
  "data": { },
  "timestamp": 1733728800000
}
```

- Field tên là **`status`**, không phải `code` (file `frontend/api-document.md` hiện ghi sai là `code`
  — nếu đang dựa vào file đó để code FE, cần sửa lại theo field thật `status`).
- `data` bị lược bỏ khỏi JSON khi `null` (`@JsonInclude(NON_NULL)`), không phải luôn trả `"data": null`.
- Lỗi cũng dùng chung envelope này qua `BaseResponseDto.error(status, message)` — không có `data`.

## 3. Xác thực (Authentication) — 2 lớp, đã xác minh trong code

### Lớp 1 — Spring Security filter chain (`common-library/.../security/SecurityConfig.java`)

Mặc định **mọi request đều yêu cầu `authenticated()`**, trừ danh sách `permitAll()` sau (áp dụng cho
toàn bộ service dùng `common-library`):

```
/api/auth/**
/avatars/**
/api/ticket/summary/excel
/api/ticket/email
/api/ticket/confirm
/ticket/confirm-page
```

**Lưu ý bảo mật cần soát lại:** `/api/ticket/summary/excel` (export doanh thu ra Excel) đang nằm
trong danh sách public — nghĩa là ai cũng tải được báo cáo doanh thu mà không cần đăng nhập. Đây là
gap bảo mật, không phải chủ đích thiết kế rõ ràng (không thấy comment giải thích) — nên xác nhận lại
trước khi lên production.

Request không public → phải có header:
```
Authorization: Bearer <accessToken>
```
Thiếu/sai token → Spring Security trả lỗi qua `CustomAuthEntryPoint` (401).

### Lớp 2 — `AuthInterceptor` (chỉ có ở module `manage-revenue-ticket`)

Chạy sau lớp 1, tự parse lại header `Authorization`, set `request.setAttribute("id", userId)` và
`request.setAttribute("role", userRole)` để controller/service dùng. Có 2 annotation điều khiển:

- `@PublicApi` — bỏ qua toàn bộ check của interceptor này (dùng ở `AuthController.register/login`,
  `TicketController.email/confirm`, `TicketWebController.confirm-page`).
- `@RoleRequired(UserRole.XXX)` — bắt buộc đúng role mới cho qua, ngược lại ném
  `UnauthorizedRoleException` (403).

**Gap quan trọng cần biết khi đọc từng màn Admin bên dưới:** tính đến thời điểm review,
`@RoleRequired` **chỉ được dùng ở `AdminDashboardController`**. Toàn bộ API còn lại (Trip, Route,
Bus, Ticket, Revenue, Salary, Loyalty...) **chỉ yêu cầu có JWT hợp lệ (bất kỳ role nào), KHÔNG check
role ADMIN** dù UI (Figma) chỉ hiển thị các chức năng này trong Admin Terminal. Nghĩa là hiện tại 1
tài khoản `CUSTOMER` đăng nhập vẫn gọi thẳng được `POST /api/trip`, `POST /api/route`,
`POST /api/bus`... nếu biết endpoint. **Phải bổ sung `@RoleRequired(UserRole.ADMIN)` (hoặc tương
đương) cho các API này trước khi go-live**, không chỉ chặn ở FE.

## 4. Status code chuẩn (theo `references/backend/rules/api.md`)

| Code | Khi nào |
|---|---|
| 200 | Đọc/sửa thành công |
| 201 | Tạo mới thành công |
| 400 | Request sai định dạng/validate fail |
| 401 | Thiếu/sai JWT |
| 403 | Có JWT hợp lệ nhưng sai role (`UnauthorizedRoleException`) |
| 404 | Không tìm thấy resource |
| 409 | Trùng dữ liệu, xung đột trạng thái |
| 500 | Lỗi server không mong muốn |

**Thực tế trong code hiện tại:** nhiều controller (`TripController`, `RouteController`, `BusController`)
trả `200`/`201` cứng bằng `BaseResponseDto.success(201, ...)` kể cả khi dùng `ResponseEntity.ok(...)`
(HTTP status thật là 200 nhưng field `status` trong body lại ghi `201`) — **HTTP status và field
`status` trong body có thể lệch nhau**, FE nên đọc `response.data.status` để biết kết quả thay vì chỉ
dựa HTTP status. Đây là điểm cần thống nhất lại, không phải hành vi chuẩn nên copy tiếp cho code mới.

## 5. Ký hiệu "Trạng thái" dùng trong các bảng endpoint

| Ký hiệu | Ý nghĩa |
|---|---|
| ✅ Đã có | Endpoint tồn tại trong code, đã kiểm tra trực tiếp |
| ⚠️ Đã có (chưa hoàn chỉnh) | Endpoint tồn tại nhưng thiếu logic thật (stub/giả lập) hoặc thiếu tham số |
| ❌ Cần tạo mới | Không tồn tại, phải viết mới trước khi FE có thể tích hợp |

## 6. Liên kết

- Thiết kế UI/UX từng màn: [`.claude/docs/design/<slug>.md`](../../../../docs/design/)
- Quy tắc REST chung: [`../rules/api.md`](../rules/api.md)
- Quy tắc bảo mật: [`../rules/security.md`](../rules/security.md)
- Workflow thêm endpoint mới: [`../workflows/implement-endpoint.md`](../workflows/implement-endpoint.md)
