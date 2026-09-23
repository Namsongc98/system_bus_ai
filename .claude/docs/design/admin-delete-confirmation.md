# Pattern dùng chung: Xác nhận xoá (Delete Confirmation)

> Figma: node-id `2:4370` (tên frame: "Delete Confirmation") — file "Ticket-Buses" (`fileKey=QgeicQW2IuhLakGxpsQnr1`)
> Nhóm: Admin Terminal — **shared UI component** (ví dụ minh hoạ trong Figma là xoá Route)
> Slug: `admin-delete-confirmation`

## 1. Tổng quan

Modal xác nhận hành động xoá mang tính phá huỷ, có bước "type-to-confirm" (gõ lại tên đối tượng để
xác nhận) — mẫu trong Figma minh hoạ xoá 1 Route tên "Skyline-Express-042".

## 2. Basic Design

- `Compact Modal (420px)`: kích thước nhỏ, tập trung 1 hành động.
- `Header Content`: icon cảnh báo (vòng tròn đỏ, hiệu ứng pulsing) + heading "Confirmation Required".
- `Affected Data Glass Card`: hiển thị đối tượng sắp bị xoá — label "AFFECTED ROUTE" + tên
  ("Skyline-Express-042").
- `Confirmation Input`: input yêu cầu gõ lại đúng tên đối tượng ("Type route name here") mới cho phép
  bấm nút xoá.
- `Action Buttons`: nút Cancel (an toàn) + nút Xoá (destructive, màu đỏ, disable cho tới khi input
  khớp tên).

## 3. Detail Design

| Field/Control | Loại | Validate |
|---|---|---|
| Confirmation Input | text | phải khớp chính xác (case-sensitive — cần xác nhận) với tên đối tượng đang hiển thị (`routeName`/`plateNumber`/mã trip...) mới enable nút xoá |
| Nút xoá | button (destructive) | disable mặc định, chỉ enable khi input khớp |
| Nút Cancel | button | đóng modal, không thực hiện gì |

**States:** input chưa khớp (nút xoá disable), input khớp (nút xoá enable), đang xoá (loading), lỗi
xoá (giữ modal mở, hiện lỗi — vd không xoá được vì còn ràng buộc dữ liệu).

## 4. Business Logic

1. User bấm icon xoá ở 1 dòng/card (Route, Bus, Trip, User...) → mở modal này, truyền theo tên +
   `id` của đối tượng.
2. User gõ lại chính xác tên đối tượng vào Confirmation Input → nút xoá được enable.
3. Bấm xoá → gọi API `DELETE` tương ứng theo loại đối tượng.
4. Thành công → đóng modal, refresh danh sách, hiện Success Toast (xem `admin-toast-notifications.md`).
5. Thất bại (vd đối tượng đang được tham chiếu, không xoá được) → giữ modal mở, hiện Error Toast/inline
   error, giải thích lý do không xoá được.

## 5. API — **toàn bộ `DELETE` endpoint dưới đây đều chưa tồn tại ở backend, cần tạo mới**

| Đối tượng | Method | Path (đề xuất) | Trạng thái |
|---|---|---|---|
| Route | DELETE | `/api/route/{routeId}` | **Cần tạo mới** |
| Bus | DELETE | `/api/bus/{busId}` | **Cần tạo mới** |
| Trip | DELETE | `/api/trip/{tripId}` | **Cần tạo mới** (khuyến nghị: chỉ cho xoá cứng khi `status = SCHEDULED` và chưa bán vé; nếu đã bán vé thì đổi `status = CANCELLED` thay vì xoá) |
| User | DELETE | `/api/user/{id}` | **Cần tạo mới**, phụ thuộc toàn bộ `admin-user-management.md` (khuyến nghị soft-delete) |

## 6. Requirements

- [ ] (Blocking) Toàn bộ API `DELETE` cho Route/Bus/Trip/User cần được tạo trước khi modal này có
      tác dụng thật (hiện tại bấm xoá sẽ không có API để gọi).
- [ ] Component modal này nên dùng chung 1 lần cho mọi loại đối tượng (Route/Bus/Trip/User), truyền
      vào `objectType`, `objectName`, `objectId`, `deleteApiFn` — không viết riêng 4 modal xoá khác nhau.
- [ ] Backend cần trả lỗi rõ ràng (không phải lỗi 500 chung chung) khi không xoá được do ràng buộc dữ
      liệu (vd Route đang gắn Trip active), để FE hiển thị đúng lý do trong Error Toast.
- [ ] Với Trip đã có vé bán ra, cân nhắc **không cho xoá cứng** — chỉ cho đổi status `CANCELLED` (giữ
      lịch sử cho báo cáo doanh thu).
- [ ] (TODO/needs confirmation) Confirmation Input có phân biệt hoa/thường khi so khớp tên không.
