# Frontend API — Modal tạo xe

> Màn hình: [`.claude/docs/design/admin-create-bus-modal.md`](../../../../docs/design/admin-create-bus-modal.md)
>
> **Cập nhật task 0.2 (2026-09-21):** `API_ENDPOINTS` đã đổi `/buses`→`/bus`, `/routes`→`/route`, `/trips`→`/trip` (`BASE`, `BY_ID`), `/tickets`→`/ticket` (`BASE`). Các bảng "FE hiện tại" bên dưới ghi path **trước** 0.2; lỗi lệch số ít/nhiều đã hết, lỗi thiếu endpoint BE vẫn còn (giờ trả 405 thay vì 404). Xem `.claude/docs/review/0.2-api-endpoints.md`.
>
> Backend thật: [`references/backend/api/admin-create-bus-modal/endpoints.md`](../../../backend/api/admin-create-bus-modal/endpoints.md)
> Quy ước chung: [`../_conventions.md`](../_conventions.md)
> File thật: `src/components/common/Modal/ModalCreateBus.vue`, mở từ
> [`admin-buses-routes`](../admin-buses-routes/endpoints.md) (nút "Add New Bus")

## Nút nào gọi API nào

| Nút/UI trên `ModalCreateBus.vue` | Handler | API gọi | Trạng thái |
|---|---|---|---|
| Nút **"Add Bus"** (submit form) | `submitBus()` → `busService.create(payload)` | `POST /buses` | ⚠️ Có gọi API, 3 lỗi field khác nhau — xem mục 1 |
| 3 nút segmented "Active/Inactive/Maintenance" | `form.status = option.value` | không gọi API | — |
| Nút "Cancel" / icon X | `closeModal()` | không gọi API | — |

## 1. Tạo Bus — payload lệch backend ở 3 điểm cùng lúc

```js
// ModalCreateBus.vue — submitBus()
await busService.create({
  busNumber: form.busNumber.trim(),
  licensePlate: form.licensePlate.trim(),
  capacity: Number(form.capacity),
  status: form.status,          // 'AVAILABLE' | 'IN_USE' | 'MAINTENANCE'
})
```

Backend `BusRequest` DTO (đã xác minh, xem
[backend doc](../../../backend/api/admin-create-bus-modal/endpoints.md)) chỉ nhận **3 field**:
`plateNumber`, `capacity`, `status` (String tự do, không ép enum).

| Vấn đề | Chi tiết |
|---|---|
| **Sai tên field biển số** | FE gửi `licensePlate`, backend đọc `plateNumber` — **2 tên khác hẳn nhau, không phải chỉ khác quy ước đặt tên**. Jackson bind theo tên field JSON, nên `licensePlate` gửi lên sẽ **không map vào `plateNumber` của backend**, kết quả: mọi Bus tạo qua modal này có `plateNumber = null` cho tới khi sửa tên field. |
| **Field thừa không có ở backend** | `busNumber` — không tồn tại trong `BusRequest`/entity `Buses`, bị Jackson bỏ qua âm thầm, không có cảnh báo. |
| **Enum status hoàn toàn khác** | FE 3 lựa chọn: `AVAILABLE`/`IN_USE`/`MAINTENANCE`. Backend enum `BusStatus` thật: `ACTIVE`/`INACTIVE`/`PENDING` (đã xác minh). Vì `BusRequest.status` là `String` tự do (không validate enum ở backend), request **vẫn được backend chấp nhận (không lỗi 400)** — nhưng lưu vào DB 1 giá trị (`"AVAILABLE"`) không khớp bất kỳ giá trị nào mà phần còn lại của hệ thống hiểu (list Bus, filter theo status...) mong đợi. Đây là bug dữ liệu âm thầm, không phải chỉ là gap validate. |

### So với path

| | FE (`API_ENDPOINTS.BUSES.BASE`) | Backend thật |
|---|---|---|
| Path | `POST /buses` | `POST /api/bus` |

Lệch số ít/nhiều như [`admin-buses-routes`](../admin-buses-routes/endpoints.md).

### Response

Backend `POST /api/bus` trả `data: null` (không trả lại object vừa tạo, xem backend doc mục 2). FE
`submitBus()` đọc `response?.data?.data ?? response?.data ?? response` — dù bóc đúng lớp, kết quả vẫn
sẽ là `null` vì backend không trả gì. `emit('created', createdBus)` truyền `null` lên
`BusesRoutes.vue`, nhưng trang cha xử lý bằng cách **gọi lại `fetchFleetNetwork()`** (không dựa vào
payload emit) nên không bị ảnh hưởng bởi việc `data` rỗng.

## Requirements

- [ ] (Blocking) Đổi field gửi lên từ `licensePlate` → `plateNumber` cho khớp `BusRequest` — nếu
      không sửa, mọi Bus tạo qua UI đều mất biển số.
- [ ] (Blocking) Đổi `BUS_STATUS_OPTIONS` sang giá trị enum thật (`ACTIVE`/`INACTIVE`/`PENDING`) thay
      vì `AVAILABLE`/`IN_USE`/`MAINTENANCE` — cân nhắc giữ label UI tiếng Anh thân thiện
      ("Active"/"Inactive"/"Maintenance") nhưng đổi `value` gửi lên.
- [ ] Bỏ field `busNumber` khỏi payload (không có nơi lưu ở backend), hoặc yêu cầu backend thêm field
      này vào `BusRequest`/entity nếu nghiệp vụ thực sự cần số hiệu xe riêng biệt biển số.
- [x] Sửa path `/buses` → `/bus`.
- [ ] (Phía backend) Ép `BusRequest.status` sang enum `BusStatus` thay vì `String` tự do — xem backend
      doc — để lỗi enum sai bị chặn ngay ở backend (400) thay vì âm thầm lưu giá trị rác.
