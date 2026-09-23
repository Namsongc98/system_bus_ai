# Frontend API — Quản lý chuyến đi

> Màn hình: [`.claude/docs/design/admin-trips-management.md`](../../../../docs/design/admin-trips-management.md)
>
> **Cập nhật task 0.2 (2026-09-21):** `API_ENDPOINTS` đã đổi `/buses`→`/bus`, `/routes`→`/route`, `/trips`→`/trip` (`BASE`, `BY_ID`), `/tickets`→`/ticket` (`BASE`). Các bảng "FE hiện tại" bên dưới ghi path **trước** 0.2; lỗi lệch số ít/nhiều đã hết, lỗi thiếu endpoint BE vẫn còn (giờ trả 405 thay vì 404). Xem `.claude/docs/review/0.2-api-endpoints.md`.
>
> Backend thật: [`references/backend/api/admin-trips-management/endpoints.md`](../../../backend/api/admin-trips-management/endpoints.md)
> Quy ước chung: [`../_conventions.md`](../_conventions.md)
> File thật: `src/pages/admin/TripsManagement.vue`, `src/services/tripService.js` (gọi thẳng, **không
> qua `useTripStore`** — xem ghi chú ở [`admin-schedule-trip-review`](../admin-schedule-trip-review/endpoints.md))
> Modal liên quan: [`admin-create-trip-modal`](../admin-create-trip-modal/endpoints.md) +
> [`admin-schedule-trip-review`](../admin-schedule-trip-review/endpoints.md) (cùng 1 component),
> `ModalTripDetails.vue` (xem mục 3)
> **Tài liệu cũ đã review riêng màn này**: [`../_legacy/trips-management-api-readiness.md`](../_legacy/trips-management-api-readiness.md)
> (giữ lại tham khảo, nội dung dưới đây là bản cập nhật thay thế).

## Nút nào gọi API nào

| Nút/UI trên `TripsManagement.vue` | Handler | API gọi | Trạng thái |
|---|---|---|---|
| Vào trang (`onMounted`) | `fetchTrips()` → `tripService.getAll()` | `GET /trips` | ⚠️ Lệch path sâu hơn bình thường — xem mục 1 |
| Nút **"New Trip"** | `openCreateTripModal()` → mở `ModalCreateTrip` (`isCreateTripOpen`) | xem [`admin-create-trip-modal`](../admin-create-trip-modal/endpoints.md) | — |
| `BaseTabs` "Calendar/List" (`selectedView`) | đổi state local, không fetch lại | không gọi API | — |
| 3 `BaseSortFilter` (Status/Route/Bus Type) | lọc **local** trên `trips.value` đã fetch sẵn (`filteredTrips` computed) | không gọi API | ❌ Không gửi filter lên backend dù backend hỗ trợ ít filter hơn UI cho phép |
| Click 1 `TripsCalendarGrid`/`TripsListTable` row | `openTripDetails(trip)` → mở `ModalTripDetails` (readonly) | không gọi API — xem mục 3 | — |
| Sau khi tạo trip thành công (`@created` từ modal) | `fetchTrips()` | `GET /trips` (gọi lại) | — |

## 1. List chuyến — lệch path SÂU hơn kiểu số ít/nhiều thông thường

```js
tripService.getAll()   // GET '/trips'  — không truyền param nào
```

| | FE path | Backend thật |
|---|---|---|
| Path | `GET /trips` | `GET /api/trip/scheduled?page=&size=` |

**Đây không chỉ là lệch số ít/nhiều** (`trips` vs `trip`) — backend còn yêu cầu thêm segment
`/scheduled` phía sau, vì `GET /api/trip` (không có gì thêm) **không phải endpoint list** — path gốc
`/api/trip` chỉ nhận `POST` (tạo chuyến, xem
[`admin-schedule-trip-review`](../admin-schedule-trip-review/endpoints.md)). Nếu chỉ sửa
`/trips` → `/trip` mà không thêm `/scheduled`, request vẫn sai (gọi nhầm sang endpoint tạo chuyến với
method GET, sẽ bị 405 Method Not Allowed thay vì 404).

Ngoài path, backend `GET /api/trip/scheduled` **chỉ nhận `page`/`size`**, không nhận `status`,
`routeId`, `busId`, `driverId`, hay khoảng ngày (xem
[backend doc](../../../backend/api/admin-trips-management/endpoints.md)) — khớp với thực tế FE cũng
**không gửi filter nào lên server**, chỉ lọc local trên dữ liệu đã fetch. Về mặt hành vi hiện tại 2
phía "khớp nhau" (cùng không filter server-side), nhưng đây là false-positive: cả 2 đều thiếu tính
năng filter thật, không phải đã cố ý đồng bộ.

## 2. Sửa 1 chuyến — chưa có UI nối, dù backend + service đều sẵn sàng

Không có nút "Edit" nào trên `TripsListTable`/`TripHighlightCard` trong code đã đọc — `tripService.js`
có sẵn `update(id, payload)` → `PUT /trips/{id}` (khớp `PUT /api/trip/{id}` thật, chỉ lệch path số
ít/nhiều), nhưng **không được gọi ở đâu trong `TripsManagement.vue`**. Đây là 1 trong số ít trường
hợp API backend đã có, service FE đã viết, nhưng UI chưa nối nút gọi tới.

## 3. `ModalTripDetails.vue` — thuần hiển thị, không gọi API

Modal xem chi tiết 1 chuyến (mở từ click card/row) chỉ hiển thị lại field đã có sẵn trong object
`trip` truyền vào (từ list đã fetch) — không gọi thêm API nào (không có tương đương
`GET /api/trip/{id}` cho chi tiết 1 chuyến ở cả FE lẫn backend hiện tại). Component này **không nằm
trong 17 frame Figma gốc** đã review ở `.claude/docs/design/` — chưa có design-doc slug riêng, tạm coi là
phần mở rộng của `admin-trips-management`.

## 4. Doanh thu 1 chuyến — chưa có UI, dù backend đã có endpoint

`GET /api/trip/{tripId}/revenue` đã tồn tại ở backend (trả thẳng `RevenueResponse`, KHÔNG qua
`BaseResponseDto` — xem [backend doc](../../../backend/api/admin-trips-management/endpoints.md) mục
4), nhưng **không có service function nào ở FE gọi endpoint này**, và không có nút/UI nào hiển thị
doanh thu riêng theo từng chuyến trên `TripsManagement.vue` hay `ModalTripDetails.vue`.

## Requirements

- [ ] (Blocking) Sửa path list từ `/trips` sang `/trip/scheduled` — không chỉ đổi số ít/nhiều.
- [ ] (Blocking, phía backend) Bổ sung filter thật (`status`, `routeId`, `busId`, `driverId`, khoảng
      ngày) cho `GET /api/trip/scheduled` — hiện 3 `BaseSortFilter` trên UI chỉ lọc local, không phản
      ánh đúng "lọc trên toàn bộ dữ liệu" nếu có phân trang.
- [ ] Nối UI "Edit" cho 1 chuyến vào `tripService.update(id, payload)` đã có sẵn (chỉ cần sửa path
      `/trips/{id}` → `/trip/{id}`).
- [ ] Cân nhắc gọi `GET /api/trip/{id}/revenue` trong `ModalTripDetails.vue` nếu cần hiển thị doanh
      thu theo chuyến — lưu ý response KHÔNG qua `BaseResponseDto`, phải xử lý riêng.
- [ ] (Blocking, phía backend, dùng chung `admin-delete-confirmation`) Cần `DELETE /api/trip/{id}` —
      hiện chưa có UI xoá/huỷ chuyến nào trên trang này.
