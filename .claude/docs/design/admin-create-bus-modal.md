# Màn hình: Modal tạo xe

> Figma: node-id `2:3949` (tên frame: "Create Bus Modal") — file "Ticket-Buses" (`fileKey=QgeicQW2IuhLakGxpsQnr1`)
> Nhóm: Admin Terminal (modal)
> Slug: `admin-create-bus-modal`

## 1. Tổng quan

Modal tạo/sửa xe — form gọn, khớp gần đúng với `BusRequest`. Có preview card dạng bento + phần
"Seat Visualization" trực quan hoá số ghế theo capacity nhập vào.

## 2. Basic Design

- `Header`: tiêu đề + nút đóng.
- `Content Area`:
  - `Bus Preview Card`: ảnh minh hoạ xe (placeholder).
  - `Form Fields`: Plate Number, Status Segmented Control (3 nút — ACTIVE/INACTIVE/PENDING), Capacity
    Slider & input.
  - `Seat Visualization`: sơ đồ ghế minh hoạ theo `capacity` nhập vào (chỉ để xem trước, không phải
    sơ đồ ghế thật dùng khi bán vé).
- `Footer`: 2 nút (Cancel / Save).

## 3. Detail Design

| Field | Loại | Placeholder (Figma) | Map (`BusRequest`) | Validate |
|---|---|---|---|---|
| Plate Number | text | "FV-0000-XX" | `plateNumber` | required, unique (chưa xác nhận backend có check unique không) |
| Operational Status | segmented control (3 nút) | — | `status` — **lưu ý: `BusRequest.status` là kiểu `String`, không phải enum `BusStatus`** → FE phải tự đảm bảo gửi đúng 1 trong 3 giá trị `ACTIVE`/`INACTIVE`/`PENDING`, backend không validate enum ở tầng DTO | required |
| Capacity | slider + input số | — | `capacity` | required, > 0, số nguyên |
| Seat Visualization | read-only, tính từ Capacity | — | — | chỉ hiển thị minh hoạ, không gửi lên server |

**States:** default (tạo mới), edit (điền sẵn), lỗi validate, đang lưu.

## 4. Business Logic

1. Nhập Plate Number, chọn Status, chọn Capacity (slider đồng bộ 2 chiều với input số).
2. `Seat Visualization` cập nhật realtime theo Capacity, chỉ là preview.
3. Submit → `POST /api/bus` (tạo mới) hoặc `PUT /api/bus/{busId}` (sửa).
4. Do `BusRequest.status` là `String` tự do, **cần validate chặt ở FE** (dropdown/segmented control,
   không cho nhập tự do) để tránh gửi giá trị không khớp enum `BusStatus` ở entity, gây lỗi ngầm khi
   backend parse.

## 5. API

| Method | Path | Trạng thái | Request | Response | Nguồn |
|---|---|---|---|---|---|
| POST | `/api/bus` | Đã có | `BusRequest` (`plateNumber`, `capacity`, `status: String`) | `BaseResponseDto<Buses>` (body hiện trả `null`) | `BusController.java:38` |
| PUT | `/api/bus/{busId}` | Đã có | `BusRequest` | `BaseResponseDto<Buses>` (body hiện trả `null`) | `BusController.java:44` |

## 6. Requirements

- [ ] Dùng segmented control/dropdown cố định giá trị Status (không cho nhập tự do) để khớp enum
      `BusStatus` phía backend.
- [ ] Validate Plate Number theo định dạng biển số thực tế (VN hoặc theo format `FV-0000-XX` như mẫu
      — cần xác nhận quy tắc đặt biển số nội bộ của hệ thống).
- [ ] Capacity phải là số nguyên dương, đồng bộ slider ↔ input.
- [ ] (TODO/needs confirmation) Backend có check `plateNumber` trùng lặp không — nếu chưa, cần bổ
      sung unique constraint trước khi go-live.
