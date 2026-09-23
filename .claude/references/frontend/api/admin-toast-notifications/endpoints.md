# Frontend API — Pattern: Toast Notification

> Màn hình: [`.claude/docs/design/admin-toast-notifications.md`](../../../../docs/design/admin-toast-notifications.md)
> Backend thật: [`references/backend/api/admin-toast-notifications/endpoints.md`](../../../backend/api/admin-toast-notifications/endpoints.md)
> Quy ước chung: [`../_conventions.md`](../_conventions.md)
> File thật: `src/composables/useToast.js` (state singleton `push`/`success`/`error`/`warning`/`info`),
> `src/components/common/ToastContainer.vue` (render qua `Teleport` + `TransitionGroup`)
> **Không có API riêng — hệ thống Toast là component thuần UI, đọc `message` từ response của API vừa
> gọi ở màn khác. Đây là hệ thống được implement đầy đủ và tái dùng tốt nhất trong toàn bộ codebase.**

## Cách các màn khác gọi Toast (không phải "nút" theo nghĩa 1 màn cụ thể)

| Nguồn Toast | Nơi gọi | Đọc field nào |
|---|---|---|
| `toast.success(...)` sau khi tạo/sửa thành công | `LoginPage`, `RegisterPage`, `ModalCreateBus`, `ModalCreateRoute`, `ModalDeleteRoute`, `ModalCreateTrip`, `UserManagement` (xoá user) | message hardcode ở FE (vd `'Bus created successfully'`), **không đọc `message` trả về từ backend** |
| `toast.error(err?.message || '<fallback message>')` khi API fail | Tất cả các màn có gọi API | `err.message` — xem mục 1 |

## 1. Vì sao `err?.message` đọc đúng dù tài liệu FE cũ ghi sai field `code`

Theo interceptor thật (xem [`../_conventions.md`](../_conventions.md#2-interceptor--requestresponse-đã-đọc-trực-tiếp-code-không-suy-đoán)
mục 2), khi lỗi, caller nhận `error.response?.data ?? error` — nếu backend trả đúng envelope
`{status, message, data, timestamp}` (đã xác minh thật, xem
[`backend/api/_conventions.md`](../../../backend/api/_conventions.md#2-response-envelope--đã-xác-minh-trong-code)),
object lỗi FE nhận được **có sẵn field `.message`** đúng nghĩa. Mọi nơi gọi `toast.error(err?.message
|| fallback)` trong code thật **đều đọc đúng**, dù các tài liệu FE khác
([`services/api-error-handling.md`](../../services/api-error-handling.md),
[`services/pinia-store.md`](../../services/pinia-store.md)) mô tả sai field envelope là `code` thay
vì `status` — vì không có chỗ nào trong code thật rẽ nhánh theo `err.code` để hiển thị Toast
(`err.code` chỉ bị đọc sai ở tầng build lại error object trong `revenueService.js`/
`loyaltyService.js`/`salaryService.js`, xem `../_conventions.md` mục 4, nhưng các service này không
liên quan trực tiếp tới Toast message).

## 2. Chuẩn hoá message — vấn đề ngôn ngữ lẫn lộn từ backend

Backend hiện trả message lẫn lộn tiếng Việt/tiếng Anh giữa các controller (vd `RouteController`:
`"Create Successfully"`, `RevenueController`: có thể trả tiếng Việt — xem
[backend doc](../../../backend/api/admin-toast-notifications/endpoints.md)). FE hiện **hiển thị
thẳng `err.message`/message backend trả về**, không có lớp dịch/chuẩn hoá nào trước khi đưa vào Toast
— nếu cần trải nghiệm nhất quán ngôn ngữ, cần thêm 1 bước map message ở tầng service/store trước khi
gọi `toast.error`/`toast.success`, hoặc backend tự chuẩn hoá trước.

## 3. Info Toast (hệ thống) — không có nguồn dữ liệu ở cả 2 phía

`useToast.js` đã hỗ trợ sẵn type `info` (và cả `warning`, nhiều hơn 3 type mà
`.claude/docs/design/admin-toast-notifications.md` mô tả), nhưng **không có nơi nào trong code gọi
`toast.info(...)` cho một thông báo hệ thống dạng "System maintenance scheduled..."** — khớp với
backend doc: không có WebSocket/SSE/endpoint polling nào phát thông báo dạng này. Nếu cần làm thật,
cả FE (gọi định kỳ hoặc lắng nghe WebSocket) lẫn backend (endpoint/kênh phát thông báo) đều cần viết
mới từ đầu.

## Requirements

- [ ] (Không blocking, phía backend) Chuẩn hoá ngôn ngữ `message` trả về giữa các controller (xem
      backend doc) — sẽ cải thiện trực tiếp trải nghiệm Toast mà không cần sửa FE.
- [ ] Nếu cần độ tin cậy cao hơn (không phụ thuộc backend trả đúng `message`), thêm lớp fallback
      message theo mã lỗi HTTP ở tầng interceptor hoặc từng service, thay vì luôn hiển thị thẳng
      `err.message`.
- [ ] Quyết định có cần channel Info Toast hệ thống thật hay bỏ khỏi phạm vi MVP (đồng nhất với backend
      doc).
