# Frontend API — Modal tạo tuyến đường

> Màn hình: [`.claude/docs/design/admin-create-route-modal.md`](../../../../docs/design/admin-create-route-modal.md)
>
> **Cập nhật task 0.2 (2026-09-21):** `API_ENDPOINTS` đã đổi `/buses`→`/bus`, `/routes`→`/route`, `/trips`→`/trip` (`BASE`, `BY_ID`), `/tickets`→`/ticket` (`BASE`). Các bảng "FE hiện tại" bên dưới ghi path **trước** 0.2; lỗi lệch số ít/nhiều đã hết, lỗi thiếu endpoint BE vẫn còn (giờ trả 405 thay vì 404). Xem `.claude/docs/review/0.2-api-endpoints.md`.
>
> Backend thật: [`references/backend/api/admin-create-route-modal/endpoints.md`](../../../backend/api/admin-create-route-modal/endpoints.md)
> Quy ước chung: [`../_conventions.md`](../_conventions.md)
> File thật: `src/components/common/Modal/ModalCreateRoute.vue`, mở từ
> [`admin-buses-routes`](../admin-buses-routes/endpoints.md) (nút "Add Route")
> **Modal nối payload đúng nhất trong toàn bộ 17 màn — chỉ còn lệch path/port, không lệch field nào.**

## Nút nào gọi API nào

| Nút/UI trên `ModalCreateRoute.vue` | Handler | API gọi | Trạng thái |
|---|---|---|---|
| Nút **"Create Route"** (submit) | `submitRoute()` → `routeService.create(payload)` | `POST /routes` | ⚠️ Field đúng, chỉ lệch path |
| `StatusToggle` "Route Status" | `form.active` (Boolean) | không gọi API | — |
| Nút "Cancel" / icon X | `closeModal()` | không gọi API | — |

## 1. Tạo Route — field khớp 100% với backend

```js
// ModalCreateRoute.vue — submitRoute()
await routeService.create({
  routeName: form.routeName.trim(),
  startPoint: form.startPoint.trim(),
  endPoint: form.endPoint.trim(),
  distanceKm: Number(form.distanceKm),
  status: form.active ? 'ACTIVE' : 'INACTIVE',
})
```

Đối chiếu `RouteRequestDto` thật (đã xác minh, xem
[backend doc](../../../backend/api/admin-create-route-modal/endpoints.md)):

| Field | FE gửi | Backend nhận | Khớp? |
|---|---|---|---|
| `routeName` | ✅ | ✅ | ✅ |
| `startPoint` | ✅ | ✅ | ✅ |
| `endPoint` | ✅ | ✅ | ✅ |
| `distanceKm` | ✅ (`Number`) | `BigDecimal` | ✅ |
| `status` | `'ACTIVE'` / `'INACTIVE'` | enum `RouteStatus` (`ACTIVE`/`INACTIVE`) | ✅ |

**Không có field thừa, không có field thiếu, không có lệch tên hay lệch enum** — đây là điểm khác
biệt lớn nhất so với [`admin-create-bus-modal`](../admin-create-bus-modal/endpoints.md) (3 lỗi cùng
lúc) — nếu dùng modal này làm mẫu để sửa các modal khác, đây là ví dụ nên copy cách đặt tên field.

### Chỉ còn lệch path/port

| | FE (`API_ENDPOINTS.ROUTES.BASE`) | Backend thật |
|---|---|---|
| Path | `POST /routes` | `POST /api/route` |

### Response

Backend trả lại `Route` object đã tạo (`data` không rỗng, khác hành vi `PUT`/Bus, xem backend doc mục
1). FE đọc đúng `response?.data?.data ?? response?.data ?? response` → nhận được object thật, dù hiện
tại `emit('created', createdRoute)` không được `BusesRoutes.vue` sử dụng trực tiếp (trang cha gọi lại
`fetchFleetNetwork()` thay vì dùng payload emit — không sai, chỉ là 1 round-trip API dư ra không bắt
buộc).

## Requirements

- [x] Sửa path `/routes` → `/route` (số ít) — đây là thay đổi DUY NHẤT cần làm cho modal này.
- [ ] Set đúng `VITE_KONG_API_URL` (`http://localhost:8000/api`, qua Kong).
- [ ] (Không blocking) Có thể bỏ việc gọi lại `fetchFleetNetwork()` toàn bộ sau khi tạo, dùng thẳng
      object trả về từ `emit('created', ...)` để giảm 1 request — không bắt buộc, chỉ là tối ưu.
