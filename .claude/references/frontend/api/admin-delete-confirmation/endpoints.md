# Frontend API — Pattern: Xác nhận xoá (Delete Confirmation)

> Màn hình: [`.claude/docs/design/admin-delete-confirmation.md`](../../../../docs/design/admin-delete-confirmation.md)
>
> **Cập nhật task 0.2 (2026-09-21):** `API_ENDPOINTS` đã đổi `/buses`→`/bus`, `/routes`→`/route`, `/trips`→`/trip` (`BASE`, `BY_ID`), `/tickets`→`/ticket` (`BASE`). Các bảng "FE hiện tại" bên dưới ghi path **trước** 0.2; lỗi lệch số ít/nhiều đã hết, lỗi thiếu endpoint BE vẫn còn (giờ trả 405 thay vì 404). Xem `.claude/docs/review/0.2-api-endpoints.md`.
>
> Backend thật: [`references/backend/api/admin-delete-confirmation/endpoints.md`](../../../backend/api/admin-delete-confirmation/endpoints.md)
> Quy ước chung: [`../_conventions.md`](../_conventions.md)
> File thật: `src/components/common/Modal/ModalDeleteRoute.vue` — **duy nhất 1 modal xoá được build
> đầy đủ trong toàn bộ codebase**, mở từ [`admin-buses-routes`](../admin-buses-routes/endpoints.md)
> (icon xoá trên `RouteNetworkCard`). Chưa có `ModalDeleteBus`/`ModalDeleteTrip`/`ModalDeleteUser`
> tương đương.
> **Backend hiện không có bất kỳ endpoint `DELETE` nào — nút xoá này chắc chắn fail nếu bấm.**

## Nút nào gọi API nào

| Nút/UI trên `ModalDeleteRoute.vue` | Handler | API gọi | Trạng thái |
|---|---|---|---|
| Ô nhập "Type route name here" (type-to-confirm) | `confirmation` ref, so khớp với `routeName` để enable nút xoá (`isConfirmed`) | không gọi API | — |
| Nút **"Delete Route"** (chỉ enable khi gõ đúng tên route) | `deleteRoute()` → `routeService.remove(routeId.value)` | `DELETE /routes/{id}` | ❌ Endpoint không tồn tại — chắc chắn lỗi |
| Nút "Cancel" / icon X | `closeModal()` (chặn khi đang `deleting`) | không gọi API | — |

## 1. Xoá Route — endpoint không tồn tại ở backend

```js
// ModalDeleteRoute.vue — deleteRoute()
await routeService.remove(routeId.value)   // DELETE '/routes/{id}'
```

`routeService.js` có sẵn hàm `remove(id)` gọi `apiClient.delete(API_ENDPOINTS.ROUTES.BY_ID(id))`.
Backend **hoàn toàn không có method `DELETE` nào ở `RouteController`** — toàn bộ endpoint xoá trong
hệ thống, không riêng Route, đều chưa được viết (xem
[backend doc](../../../backend/api/admin-delete-confirmation/endpoints.md)). Khi bấm nút "Delete
Route" đã type-to-confirm đúng, request sẽ nhận **404/405 từ backend** (route/method không khớp bất
kỳ mapping nào) — UI xử lý lỗi này qua `toast.error(err?.message || 'Unable to delete route')`, nên
người dùng sẽ thấy toast lỗi, không phải app crash, nhưng thao tác xoá không có tác dụng thật.

| | FE path | Backend thật |
|---|---|---|
| Path | `DELETE /routes/{id}` | *(không tồn tại — đề xuất `DELETE /api/route/{routeId}`)* |

## 2. Xoá Bus/Trip/User — chưa có UI ở FE, và cũng chưa có API ở backend

Không có modal xoá nào cho Bus (xem gap ở
[`admin-buses-routes`](../admin-buses-routes/endpoints.md#2-xoá-bus--không-có-ui-dù-đã-có-kế-hoạch-xoá-route)),
Trip (xem [`admin-trips-management`](../admin-trips-management/endpoints.md)), hay User (xem
[`admin-user-management`](../admin-user-management/endpoints.md)) — 2 phía đang **đồng bộ ở trạng
thái "chưa làm"** cho 3 đối tượng này (không phải FE đã làm mà backend thiếu, như trường hợp Route).
Khi backend bổ sung cả 4 endpoint `DELETE`, cách hợp lý nhất để tiết kiệm công FE là **tái sử dụng
`ModalDeleteRoute.vue` làm component chung** (đổi `route` prop thành generic `entity` +
`entityLabel`/`onConfirm` callback) thay vì viết lại 4 modal type-to-confirm riêng biệt — UI/UX (kể
cả text cảnh báo, ô gõ tên xác nhận) đã đúng thiết kế và có thể tái dùng ngay.

## Requirements

- [ ] (Blocking, phía backend trước — ưu tiên cao) Cần cả 4 endpoint `DELETE` (Route/Bus/Trip/User) —
      xem backend doc, bao gồm cả check ràng buộc dữ liệu (Trip active, v.v.) trước khi cho xoá.
- [x] Sửa path `/routes/{id}` → `/route/{id}` ngay khi backend có endpoint.
- [ ] Cân nhắc tổng quát hoá `ModalDeleteRoute.vue` thành component dùng chung cho cả 4 loại xoá thay
      vì viết 3 modal riêng — xem gợi ý mục 2.
