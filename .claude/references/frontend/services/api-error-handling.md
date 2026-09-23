# API Error Handling

`src/services/axios.js` currently unwraps backend errors before they reach stores, composables, or components.

## Backend Error Shape

```json
{
  "code": 400,
  "message": "Error message",
  "data": null
}
```

## Interceptor Behavior

The response interceptor rejects with:

```js
error.response?.data ?? error
```

For most API failures, callers receive the unwrapped backend object, not a raw Axios error.

## Caller Pattern

```js
catch (error) {
  const message = error?.message || 'Unexpected error'
  const code = error?.code || 500
}
```

Do not add `try/catch` inside normal service functions just to normalize errors. Let stores, composables, or pages handle user-facing feedback.


---

## ⚠️ Đính chính — field envelope thật của backend là `status`, không phải `code`

Ví dụ ở trên (`{ "code": 400, "message": ..., "data": null }`) là mô tả CŨ, không khớp code backend
thật. Backend thật dùng `BaseResponseDto` với field **`status`** (đã xác minh trực tiếp code), xem
[`../api/_conventions.md`](../api/_conventions.md#4-response-envelope-backend--fe-đang-tài-liệu-sai-cần-đọc-theo-bản-backend-thật)
mục 4. `error?.code` trong ví dụ "Caller Pattern" ở trên sẽ luôn `undefined` khi đọc lỗi thật từ
backend — dùng `error?.status` nếu cần đọc mã lỗi HTTP từ response, hoặc chỉ dựa vào `error?.message`
(cách này vẫn hoạt động đúng vì field `message` không đổi tên).
