# Frontend API — Modal tạo chuyến (Bước 4: Final Review)

> Màn hình: [`.claude/docs/design/admin-schedule-trip-review.md`](../../../../docs/design/admin-schedule-trip-review.md)
>
> **Cập nhật task 0.2 (2026-09-21):** `API_ENDPOINTS` đã đổi `/buses`→`/bus`, `/routes`→`/route`, `/trips`→`/trip` (`BASE`, `BY_ID`), `/tickets`→`/ticket` (`BASE`). Các bảng "FE hiện tại" bên dưới ghi path **trước** 0.2; lỗi lệch số ít/nhiều đã hết, lỗi thiếu endpoint BE vẫn còn (giờ trả 405 thay vì 404). Xem `.claude/docs/review/0.2-api-endpoints.md`.
>
> Backend thật: [`references/backend/api/admin-schedule-trip-review/endpoints.md`](../../../backend/api/admin-schedule-trip-review/endpoints.md)
> Quy ước chung: [`../_conventions.md`](../_conventions.md)
> **File thật: cùng 1 file `src/components/common/Modal/ModalCreateTrip.vue` như
> [`admin-create-trip-modal`](../admin-create-trip-modal/endpoints.md)** (bước 1-3 load dữ liệu, file
> này là bước 4 — nơi DUY NHẤT gọi API submit thật). Đây là phát hiện cấu trúc quan trọng: 2 file
> thiết kế/backend riêng biệt tương ứng với **1 component Vue duy nhất**.

## Nút nào gọi API nào

| Nút/UI ở bước "Review" | Handler | API gọi | Trạng thái |
|---|---|---|---|
| Nút **"Schedule Trip"** (submit cuối wizard) | `submitTrip()` → `tripStore.create(payload)` → `tripService.create(payload)` | `POST /trips` | ⚠️ Field khớp DTO, chỉ lệch path/port |
| Nút "Back to Schedule" (`goBack()`, quay bước 3) | — | không gọi API | — |
| Nút "Cancel" | `closeModal()` → `resetForm()` | không gọi API | — |

## 1. Tạo chuyến — submit cuối wizard

```js
// ModalCreateTrip.vue — submitTrip()
const createdTrip = await tripStore.create({
  routeId: resolveOptionValue(routeOptions.value, form.routeId),
  busId: resolveOptionValue(busOptions.value, form.busId),
  driverId: resolveOptionValue(driverOptions.value, form.driverId),
  departureTime: form.departureTime,
  arrivalTime: form.arrivalTime,
  status: 'SCHEDULED',
})
```

`tripStore.create()` (`stores/trip.js`, **duy nhất action không phải placeholder** trong store này) →
`tripService.create(payload)` → `apiClient.post(API_ENDPOINTS.TRIPS.BASE, payload)` = `POST '/trips'`.

### Field khớp `TripRequestDto` thật

| Field | FE gửi | Backend nhận | Khớp? |
|---|---|---|---|
| `routeId` | ✅ | ✅ | ✅ |
| `busId` | ✅ | ✅ | ✅ |
| `driverId` | ✅ | ✅ | ✅ |
| `departureTime` | `datetime-local` string (vd `"2026-04-10T08:00"`) | `LocalDateTime` | ✅ (format tương thích) |
| `arrivalTime` | cùng dạng | `LocalDateTime` | ✅ |
| `status` | `'SCHEDULED'` (hardcode) | enum `TripStatus` | ✅ |
| `revenue` | **không gửi** | optional, backend tự mặc định `0` | ✅ (không cần gửi, backend tự set) |

Đây là ví dụ tốt thứ 2 (sau [`admin-create-route-modal`](../admin-create-route-modal/endpoints.md))
về payload khớp DTO backend — vấn đề duy nhất còn lại là **path**:

| | FE (`API_ENDPOINTS.TRIPS.BASE`) | Backend thật |
|---|---|---|
| Path | `POST /trips` | `POST /api/trip` |

### Response

Backend trả lại `Trip` object đầy đủ (`data` không rỗng, xem backend doc). `tripStore.create()` đọc
`getPayload(response)` = `response?.data?.data ?? response?.data ?? response`, nếu có `createdTrip`
thì `trips.value = [createdTrip, ...trips.value]` — **cập nhật state local trực tiếp, không gọi lại
list API** — nhưng lưu ý `trips` ref trong `useTripStore` **không được `admin-trips-management`
dùng** (trang đó tự quản lý `trips` local riêng, gọi thẳng `tripService.getAll()` — xem
[`admin-trips-management`](../admin-trips-management/endpoints.md)), nên việc cập nhật state ở store
này hiện **không có tác dụng hiển thị** — trang danh sách tự `fetchTrips()` lại qua sự kiện
`@created="fetchTrips"` gắn trên `<ModalCreateTrip>`, không phụ thuộc vào `tripStore.trips`.

## Requirements

- [x] Sửa path `/trips` → `/trip`.
- [ ] Set đúng `VITE_KONG_API_URL` (`http://localhost:8000/api`, qua Kong).
- [ ] (Blocking, phía backend, dùng chung với `admin-create-trip-modal`) Thêm validate
      `arrivalTime > departureTime` và check overlap lịch Bus/Driver — xem backend doc, hiện hoàn
      toàn chưa có ở bất kỳ tầng nào.
- [ ] (Không blocking) Cân nhắc dọn `useTripStore.trips`/`total` nếu không có trang nào thực sự đọc từ
      đó — tránh state trùng lặp gây nhầm lẫn khi debug (trang danh sách dùng `ref` local riêng, không
      dùng store).
