# API — Pattern: Xác nhận xoá (Delete Confirmation)

> Màn hình: [`.claude/docs/design/admin-delete-confirmation.md`](../../../../docs/design/admin-delete-confirmation.md) · Figma `2:4370`
> Quy ước chung: [`../_conventions.md`](../_conventions.md)
> **Không có bất kỳ API `DELETE` nào tồn tại trong toàn bộ backend hiện tại** — toàn bộ bảng dưới đây là đề xuất.

## Endpoint dùng ở màn này — tất cả ❌ Cần tạo mới

| Đối tượng bị xoá | Method | Path (đề xuất) | Controller cần sửa |
|---|---|---|---|
| Route | DELETE | `/api/route/{routeId}` | `RouteController` |
| Bus | DELETE | `/api/bus/{busId}` | `BusController` |
| Trip | DELETE | `/api/trip/{tripId}` | `TripController` |
| User | DELETE | `/api/user/{id}` | `UserController` (đang rỗng) |

## 1. Xoá Route (ví dụ minh hoạ trong Figma: "Skyline-Express-042")

- **Method & Path đề xuất:** `DELETE /api/route/{routeId}`
- **Request:** không cần body, `routeId` trên path. FE gửi kèm giá trị Confirmation Input chỉ để
  validate ở phía FE (không nhất thiết phải gửi lên server), **nhưng nên có bước server tự kiểm tra
  Route không bị Trip nào đang tham chiếu ở trạng thái `SCHEDULED`/`ONGOING`** trước khi xoá.
- **Response đề xuất (200):**
```json
{ "status": 200, "message": "Delete Successfully", "data": null, "timestamp": 1733728800000 }
```
- **Lỗi đề xuất:** `409 Conflict` kèm message rõ ràng khi Route đang được Trip active tham chiếu (không cho xoá), `404` khi `routeId` không tồn tại.

## 2. Xoá Bus

- **Method & Path đề xuất:** `DELETE /api/bus/{busId}`
- **Ràng buộc tương tự Route:** chặn xoá nếu Bus đang gắn Trip `SCHEDULED`/`ONGOING`.

## 3. Xoá/Huỷ Trip

- **Method & Path đề xuất:** `DELETE /api/trip/{tripId}`
- **Khuyến nghị khác Route/Bus:** nếu Trip đã có `Ticket` (đã bán vé) → **không cho xoá cứng**, chỉ
  cho phép đổi `status = CANCELLED` (giữ lịch sử phục vụ báo cáo doanh thu ở `admin-revenue-reports`).
  Nếu chưa có vé nào → cho xoá cứng bình thường.

## 4. Xoá User

- **Method & Path đề xuất:** `DELETE /api/user/{id}`
- **Bắt buộc soft-delete** (`isActive=false`), không xoá cứng — User có quan hệ với `Ticket.customer`,
  `Ticket.seller`, `Trip.driver`. Xem chi tiết ở [`admin-user-management/endpoints.md`](../admin-user-management/endpoints.md).

## Việc chung cho cả 4 endpoint (áp dụng khi implement)

- Toàn bộ nên trả về cùng 1 dạng response (`BaseResponseDto` với `data: null`, `message` rõ ràng).
- Toàn bộ nên dùng chung 1 error shape khi bị chặn do ràng buộc dữ liệu (409), để FE dùng chung 1
  component xử lý lỗi thay vì viết riêng cho từng loại đối tượng.
- Yêu cầu `@RoleRequired(ADMIN)` — hành động xoá là rủi ro cao nhất trong toàn hệ thống, không thể để
  ở trạng thái "chỉ cần JWT hợp lệ" như phần lớn API khác hiện tại.

## Requirements liên quan tới backend

- [ ] (Blocking) Tạo cả 4 endpoint `DELETE` trước khi màn hình này có tác dụng thật (hiện tại bấm xoá không có API để gọi).
- [ ] (Blocking) Thêm check ràng buộc dữ liệu (Route/Bus đang gắn Trip active) trước khi cho xoá.
- [ ] (Blocking, riêng Trip) Không xoá cứng Trip đã có vé — chỉ đổi status.
- [ ] (Bảo mật, Blocking) Cả 4 endpoint đều phải có `@RoleRequired(ADMIN)` ngay từ khi viết, không được để chung tình trạng "chỉ cần JWT" như các API khác.
