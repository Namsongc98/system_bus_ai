# Frontend API — Modal tạo chuyến (Bước 1-3: Route & Vehicle → Schedule → Preview)

> Màn hình: [`.claude/docs/design/admin-create-trip-modal.md`](../../../../docs/design/admin-create-trip-modal.md)
>
> **Cập nhật task 0.2 (2026-09-21):** `API_ENDPOINTS` đã đổi `/buses`→`/bus`, `/routes`→`/route`, `/trips`→`/trip` (`BASE`, `BY_ID`), `/tickets`→`/ticket` (`BASE`). Các bảng "FE hiện tại" bên dưới ghi path **trước** 0.2; lỗi lệch số ít/nhiều đã hết, lỗi thiếu endpoint BE vẫn còn (giờ trả 405 thay vì 404). Xem `.claude/docs/review/0.2-api-endpoints.md`.
>
> Backend thật: [`references/backend/api/admin-create-trip-modal/endpoints.md`](../../../backend/api/admin-create-trip-modal/endpoints.md)
> Quy ước chung: [`../_conventions.md`](../_conventions.md)
> **File thật: `src/components/common/Modal/ModalCreateTrip.vue` — 1 component DUY NHẤT triển khai cả
> 4 bước wizard**, gộp chung với [`admin-schedule-trip-review`](../admin-schedule-trip-review/endpoints.md)
> (bước 4 — nơi thật sự submit). File này chỉ mô tả bước 1-3 (load dữ liệu, KHÔNG submit).
> Mở từ [`admin-buses-routes`](../admin-buses-routes/endpoints.md) (nút "Add New Bus" — **không**,
> chính xác là nút "Create Trip" trên [`admin-trips-management`](../admin-trips-management/endpoints.md)).

## Nút nào gọi API nào (chỉ bước 1-3, submit thật xem file `admin-schedule-trip-review`)

| Nút/UI trên `ModalCreateTrip.vue` (bước 1-3) | Handler | API gọi | Trạng thái |
|---|---|---|---|
| Mở modal (`watch modelValue, immediate`) | `loadOptions()` → `Promise.allSettled([routeService.getAll({status:'ACTIVE'}), busService.getAll(), userService.getAll({role:'DRIVER'})])` | `GET /routes?status=ACTIVE`, `GET /buses`, `GET /users?role=DRIVER` | ❌ Cả 3 lệch path, 2/3 chặn hoàn toàn |
| Bước 1 — chọn `USelect` "Route" | `form.routeId = $event` | không gọi API | — |
| Bước 2 — chọn `USelect` "Bus Unit" / "Assigned Driver" | `form.busId`/`form.driverId = $event` | không gọi API | — |
| Bước 3 — nhập "Departure"/"Estimated Arrival" (`datetime-local`) | `form.departureTime`/`form.arrivalTime` | không gọi API | — |
| Nút **"Next"** (bước 1→2→3) | `goNext()` → validate step hiện tại rồi chuyển `currentStep` | không gọi API | — |
| Nút **"Back to {step}"** | `goBack()` | không gọi API | — |
| Nút "Cancel" / icon X | `closeModal()` → `resetForm()` | không gọi API | — |

## 1. Load Route (autocomplete/select) — 2 tầng gap

```js
routeService.getAll({ status: 'ACTIVE' })   // GET '/routes?status=ACTIVE'
```

| | FE path | Backend thật |
|---|---|---|
| Path | `/routes?status=ACTIVE` | ❌ **`GET /api/route` không tồn tại** (không chỉ lệch số ít/nhiều — chưa có endpoint) |

Giống hệt gap đã nêu ở [`admin-buses-routes`](../admin-buses-routes/endpoints.md) mục 1 — dùng chung
1 nguồn API đề xuất, xem backend doc.

## 2. Load Bus khả dụng — path lệch, và thiếu filter overlap lịch

```js
busService.getAll()   // GET '/buses'
```

| | FE path | Backend thật |
|---|---|---|
| Path | `/buses` | `/api/bus?page=&size=` |

Sau khi sửa path, endpoint **có tồn tại và trả dữ liệu được** — nhưng cả 2 phía đều **không filter
được "khả dụng trong khung giờ đã chọn"**: FE tự lọc `bus.status === 'AVAILABLE'` ở client
(`normalizeBus` trong `ModalCreateTrip.vue`), nhưng vì
[`admin-create-bus-modal`](../admin-create-bus-modal/endpoints.md) đang gửi enum sai
(`AVAILABLE`/`IN_USE`/`MAINTENANCE` thay vì `ACTIVE`/`INACTIVE`/`PENDING` thật), **filter này gần như
luôn khớp sai** — Bus có status thật là `ACTIVE` (nếu tạo đúng chuẩn qua Postman) sẽ **bị lọc bỏ**
khỏi dropdown vì FE đang so sánh với chuỗi `'AVAILABLE'`. Đây là hệ quả trực tiếp của bug enum ở modal
tạo Bus, không phải bug riêng của modal này.

## 3. Load Driver khả dụng — chặn hoàn toàn bởi `UserController` rỗng

```js
userService.getAll({ role: 'DRIVER' })   // GET '/users?role=DRIVER'
```

| | FE path | Backend thật |
|---|---|---|
| Path | `/users?role=DRIVER` | ❌ **`UserController` là class rỗng — không có endpoint nào, kể cả sau khi sửa path** |

Dropdown "Assigned Driver" **chắc chắn luôn rỗng** cho tới khi `UserController` được implement (xem
[`admin-user-management`](../admin-user-management/endpoints.md) — gap ưu tiên cao nhất toàn hệ
thống). `normalizeDriver()` đã viết sẵn logic map `{id, label, name, detail}` từ response User — sẵn
sàng dùng ngay khi backend có API, không cần sửa gì thêm ở tầng này.

## Requirements

- [ ] (Blocking, phía backend, ưu tiên cao nhất) Implement `UserController` — chặn cả dropdown Driver
      ở đây lẫn toàn bộ [`admin-user-management`](../admin-user-management/endpoints.md).
- [ ] (Blocking, phía backend) Cần `GET /api/route` (list) — chặn dropdown Route.
- [x] Sửa path `/buses` → `/bus`.
- [ ] Sau khi sửa enum ở [`admin-create-bus-modal`](../admin-create-bus-modal/endpoints.md), xác nhận
      lại filter `status === 'AVAILABLE'` ở `normalizeBus()` cũng cần đổi theo (`ACTIVE`), nếu không
      dropdown Bus vẫn rỗng dù API đã trả đúng dữ liệu.
- [ ] (Blocking, phía backend, dùng chung với `admin-schedule-trip-review`) Thêm check overlap lịch
      Bus/Driver — hiện không có filter "khả dụng đúng khung giờ" ở bất kỳ endpoint nào.
