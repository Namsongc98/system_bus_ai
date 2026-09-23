# Frontend API — Quản lý người dùng

> Màn hình: [`.claude/docs/design/admin-user-management.md`](../../../../docs/design/admin-user-management.md)
> Backend thật: [`references/backend/api/admin-user-management/endpoints.md`](../../../backend/api/admin-user-management/endpoints.md)
> Quy ước chung: [`../_conventions.md`](../_conventions.md)
> File thật: `src/pages/admin/UserManagement.vue`, `src/stores/user.js` (`useUserStore`), `src/services/userService.js`
> **`UserController` ở backend là class rỗng hoàn toàn — mọi API ở màn này đều sẽ 404. Đây là màn bị
> chặn nặng nhất trong 17 màn, khớp với đánh giá "ưu tiên cao nhất" ở backend doc.**

## Nút nào gọi API nào

| Nút/UI trên `UserManagement.vue` | Handler | API gọi | Trạng thái |
|---|---|---|---|
| Vào trang / đổi tab role (All/Admin/Driver/Collector/Customer) | `fetchUsers()` → `userStore.fetchAll(params)` | `GET /users?role=&page=&size=` | ❌ Chắc chắn 404 (`UserController` rỗng) |
| Nút chuyển trang (`BasePagination` prev/next) | `goToPrevPage()`/`goToNextPage()` → `fetchUsers()` | cùng API trên | ❌ |
| Icon thùng rác (xoá user, từng row) | `deleteUser(user)` → `window.confirm(...)` → `userStore.deleteUser(user.id)` | `DELETE /users/{id}` | ❌ |
| — (không có nút "Create"/FAB trong code đã đọc) | — | — | ❌ Thiếu UI tạo user — xem mục 3 |

## 1. List user theo role/trang — toàn bộ path không tồn tại

```js
userStore.fetchAll(params)  → userService.getAll(params)  → GET '/users?role=&page=&size='
```

| | FE path | Backend thật |
|---|---|---|
| Path | `/users` | ❌ **Không tồn tại — `UserController.java` là class rỗng, không có method nào** |

Khác các domain khác (chỉ lệch số ít/nhiều hoặc thiếu 1 phần path), ở đây **sửa path đúng số ít cũng
vô ích** vì không có bất kỳ method nào được map trong `UserController` — mọi request tới
`/api/user/**` đều 404 bất kể path chính xác đến đâu.

`useUserStore.fetchAll()` xử lý response khá kỹ (bóc payload qua `getPayload`, nhận diện collection
qua nhiều shape `Array`/`.content`/`.items`/`.data`, tính `total` qua nhiều tên field
`totalElements`/`total`/`pagination.total`) — code store đã sẵn sàng nhận đúng response ngay khi
backend có API thật, không cần sửa lại tầng store.

`UserManagement.vue` khi fetch fail: `pagination.total.value = 0`, `warning.value = err?.message ||
'Unable to load users. Showing sample user management data.'` — **nhưng khi đó `visibleUsers` fallback
sang `USER_MANAGEMENT_FALLBACK_USERS` (constant mẫu)**, và banner cảnh báo (`BaseEmptyState` màu
vàng) **CÓ hiển thị đúng** — khác với gap đã nêu ở [`my-tickets`](../my-tickets/endpoints.md) (nơi lỗi
bị nuốt hoàn toàn), màn này xử lý lỗi đúng cách dù API vẫn chưa hoạt động.

## 2. Xoá user — cùng gap, thêm rủi ro data integrity nếu backend làm ẩu

```js
userStore.deleteUser(id)  → userService.deleteById(id)  → DELETE '/users/{id}'
```
Cùng lý do 404 như mục 1. Khi backend implement, **cần soft-delete** (không xoá cứng) vì `User` có
quan hệ với `Ticket.customer`/`Ticket.seller`/`Trip.driver` (xem backend doc mục 5) — nút xoá ở FE
hiện tại (`window.confirm` đơn giản, không phải type-to-confirm như
[`admin-delete-confirmation`](../admin-delete-confirmation/endpoints.md)) không phân biệt được
xoá-mềm hay xoá-cứng, chỉ cần backend trả `200` là coi như thành công và filter user khỏi list local
(`users.value.filter(...)`) — không có rủi ro gì thêm ở tầng FE, rủi ro nằm hoàn toàn ở cách backend
implement.

## 3. Không có UI tạo user mới trên trang này

Backend doc đề xuất tái dùng `POST /api/auth/register` (xem
[`customer-register`](../customer-register/endpoints.md)) để tạo user với `role` bất kỳ thay vì viết
API riêng — nhưng ở phía FE, `UserManagement.vue` **không có nút "Create"/FAB nào** gọi
`authService.register()` hay mở modal tạo user. Đây là gap UI cần bổ sung riêng, độc lập với việc
backend có API hay chưa (API tái dùng đã sẵn sàng ở `authService.register()`).

## Requirements

- [ ] (Blocking, ưu tiên cao nhất toàn hệ thống — chặn cả màn này lẫn dropdown Driver ở
      [`admin-create-trip-modal`](../admin-create-trip-modal/endpoints.md)) Implement `UserController`
      — xem danh sách endpoint đề xuất đầy đủ ở backend doc.
- [ ] Sau khi có API, sửa path `/users` → `/user` (số ít).
- [ ] Thêm UI tạo user (nút "Create"/FAB) nối vào `authService.register()` đã có sẵn — hiện thiếu hoàn
      toàn ở trang này dù API tái dùng đã tồn tại.
- [ ] Xác nhận field UI hiển thị (avatar, "2 mins ago", "Shift: Night Route 402", "Station: Central
      Terminal", "Mobile App (iOS)") **không có trong entity `User`** — cần chốt với backend trước khi
      map field thật (xem backend doc mục 1, danh sách field thiếu đầy đủ).
