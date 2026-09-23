# Pattern dùng chung: Toast Notification

> Figma: node-id `2:4193` (tên frame: "Toast Notifications" — thực chất là màn Admin Dashboard với
> `TOAST NOTIFICATION STACK` overlay lên trên để minh hoạ component) — file "Ticket-Buses"
> (`fileKey=QgeicQW2IuhLakGxpsQnr1`)
> Nhóm: Admin Terminal — **shared UI component**, không phải 1 trang độc lập
> Slug: `admin-toast-notifications`

## 1. Tổng quan

Frame này không phải 1 màn hình nghiệp vụ riêng — nó minh hoạ component Toast (Success/Error/Info)
đặt chồng lên trang Dashboard để designer thể hiện vị trí + style. Cần tài liệu hoá riêng vì đây là
component dùng lại ở **mọi hành động ghi dữ liệu** trong Admin Terminal (tạo/sửa/xoá Trip, Bus,
Route, User…).

## 2. Basic Design

- `TOAST NOTIFICATION STACK`: xếp chồng góc trên-phải màn hình, 3 biến thể:
  - `Success Toast` (viền/icon xanh, có progress bar đếm ngược tự ẩn).
  - `Error Toast` (viền/icon đỏ).
  - `Info Toast` (viền/icon xanh dương).
- Mỗi toast có: icon trạng thái, heading ngắn, nội dung message, nút đóng (X).

## 3. Detail Design

| Loại | Ví dụ nội dung (Figma) | Khi nào dùng |
|---|---|---|
| Success | "Success! — Route #402 has been successfully updated in the terminal database." | sau khi `POST`/`PUT` thành công (Create/Update Route, Bus, Trip, User...) |
| Error | "Error! — Failed to synchronize ticket sales. Please check terminal connectivity." | khi API trả lỗi (4xx/5xx) hoặc mất kết nối mạng |
| Info | "Info! — System maintenance scheduled for 02:00 AM UTC. Estimated downtime: 15 mins." | thông báo hệ thống, không gắn với 1 action cụ thể của user (broadcast) |

**Behavior đề xuất:**
- Success/Error: tự ẩn sau X giây (Success Toast có `Progress Bar` đếm ngược trực quan trong Figma),
  cho phép đóng tay bằng nút X.
- Info: có thể không tự ẩn (thông báo hệ thống quan trọng hơn) — cần xác nhận với designer.
- Nhiều toast cùng lúc → xếp chồng (stack), toast mới nhất ở trên/dưới — cần xác nhận thứ tự.

## 4. Business Logic

Toast là **hệ quả** của các action khác, không có luồng nghiệp vụ riêng:
1. Mọi API call ghi dữ liệu (`POST`/`PUT`/`DELETE`) ở Admin Terminal → thành công show Success Toast,
   thất bại show Error Toast (message nên lấy từ `BaseResponseDto.message` nếu backend trả, fallback
   message generic khi lỗi network/parse).
2. Toast Info dùng cho thông báo hệ thống — hiện **chưa có API/WebSocket nào phát broadcast dạng
   này** ở backend (không thấy channel nào cho "system maintenance" notice).

## 5. API

| Method | Path | Trạng thái | Ghi chú |
|---|---|---|---|
| — | (không có API riêng cho Toast — Success/Error lấy trực tiếp từ response của action tương ứng) | — | Toast chỉ là tầng hiển thị, dùng lại `BaseResponseDto.message`/HTTP status |
| — | Kênh phát Info/system-broadcast (vd WebSocket/SSE) | **Cần tạo mới nếu muốn dùng đúng như Figma** | Hiện không có cơ chế push thông báo hệ thống realtime tới Admin Terminal |

## 6. Requirements

- [ ] Chuẩn hoá 1 component `Toast` dùng chung toàn bộ Admin Terminal (Success/Error/Info), nhận
      `title`, `message`, `type`, `autoHideMs`.
- [ ] Mọi form/modal ghi dữ liệu (Create Trip/Route/Bus/User, Delete...) đều bắn Toast qua component
      này thay vì tự dựng UI báo lỗi riêng lẻ.
- [ ] Error Toast nên phân biệt lỗi validate (4xx, hiển thị message cụ thể từ backend) và lỗi hệ
      thống/mạng (5xx/timeout, hiển thị message chung).
- [ ] (TODO/needs confirmation) Info Toast dạng "system maintenance" lấy dữ liệu từ đâu — nếu chưa có
      kênh broadcast thật, tạm thời có thể bỏ qua khỏi phạm vi MVP.
