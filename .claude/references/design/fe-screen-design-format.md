# Screen Design Doc Format — cho `/clear-spec`

Nguồn: đối chiếu cấu trúc từ `Document/FE_Screen/(KSBM105) Result Update-SUID.xlsx`
(12 sheet: Cover, Overview, Screen(...), Ảnh màn hình, Check(...), Check(Common),
Print label, 別紙(詳細設計), 画面-APIリクエスト, Process, 画面API実行処理一覧).

Mục đích: mọi `.claude/docs/design/<slug>.md` do `/clear-spec` sinh ra phải đủ các mục dưới
đây — để `backend-implement-api`, `frontend-figma-to-vue`/`integrate-component`,
`fullstack-page-api-review`, và review sau này không phải hỏi lại thông tin cơ bản.

## Nguyên tắc chung

- 1 file `.claude/docs/design/<slug>.md` = 1 màn hình. `<slug>` khớp 1:1 với
  `.claude/references/{backend,frontend}/api/<slug>/`.
- Mục nào không áp dụng cho màn này thì ghi `N/A — <lý do>`, không xóa mục khỏi
  file (giữ mọi file design cùng khung để dễ quét).
- Phần có nhiều dòng lặp cùng cấu trúc (field, check, API...) viết bằng bảng
  Markdown, không viết văn xuôi.
- Không copy nguyên câu chữ/thuật ngữ nội bộ khách hàng cũ (VD tiếng Nhật trong
  mẫu gốc) — chỉ giữ lại cấu trúc và ý tưởng tổ chức thông tin.
- Feature nhỏ (sửa 1 field, không đổi luồng): chỉ cần viết lại phần thay đổi ở
  mục 4, 10, 11 — không viết lại toàn bộ file.

## Cấu trúc bắt buộc (đúng thứ tự)

### 1. Header
- Tên màn hình + mã màn (nếu dự án đặt mã, VD `[ADM-012]`).
- Route/path FE, role được truy cập.
- Ngày tạo/sửa gần nhất, 1 dòng đổi mới nhất (không cần bảng Revision History
  đầy đủ như bản gốc trừ khi feature lớn nhiều lần sửa).

### 2. Overview
*(nguồn: sheet Overview)*
- Mục đích màn hình: liệt kê từng hành vi nghiệp vụ cụ thể (kiểu "1) ... 2) ...
  3) ..." trong mẫu gốc), KHÔNG mô tả UI ở mục này.
- Component Structure: các component Vue con dự kiến tách (nếu biết trước),
  hoặc ghi "chưa xác định, quyết định lúc implement".

### 3. Screen Image
*(nguồn: sheet Ảnh màn hình)*
- Link Figma (bắt buộc nếu đã có mockup).
- Ảnh chụp mockup hiện tại (embed hoặc link file trong repo), ghi rõ đây là
  mockup hay bản final.

### 4. Item Definition
*(nguồn: sheet Screen(...) mục "3. Item Definition")*

| # | Item | Loại (label/input/table/image/...) | Nguồn dữ liệu (field nào từ API nào — tham chiếu mục 10) | Ghi chú |
|---|---|---|---|---|

### 5. Control Definition
*(nguồn: sheet Screen(...) mục "4. Control Definition")*

| # | Control | Hành vi khi tương tác | Điều kiện enable/disable | API gọi (tham chiếu mục 10) |
|---|---|---|---|---|

### 6. Confirmation Message
*(nguồn: sheet Screen(...) mục "5. Confirmation Message")*

| # | Trigger (nhấn control nào) | Nội dung message | Loại (confirm/error/success) |
|---|---|---|---|

### 7. Individual Check
*(nguồn: sheet Check(...))*

Validate riêng cho field/control của MÀN NÀY (không lặp lại rule chung ở mục 8):

| # | Field/Control | Điều kiện check | Kết quả khi fail |
|---|---|---|---|

### 8. Common Check
*(nguồn: sheet Check(Common))*
- Nếu màn dùng đúng rule chung đã có sẵn (mandatory, half-width alphanumeric,
  numeric...) → chỉ trỏ tới nơi rule chung đã định nghĩa 1 lần
  (`.claude/references/frontend/rules/...`), KHÔNG copy lại bảng vào từng file.
- Chỉ liệt kê case màn này có rule chung KHÁC hoặc BỔ SUNG so với chuẩn.

### 9. Data-to-API Mapping (chi tiết thiết kế)
*(nguồn: sheet 別紙(詳細設計))*

Ánh xạ thông tin hiển thị trên màn ↔ field trả về từ API nào (dùng alias để
tránh lặp URL dài khi 1 field được nhiều nơi trên màn tham chiếu):

| Alias | API | Field trả về | Hiển thị ở đâu trên màn (tham chiếu # ở mục 4) |
|---|---|---|---|

### 10. Required APIs
*(nguồn: sheet 画面-APIリクエスト)*

Liệt kê MỌI API màn này gọi:

| Trigger (vào màn / nhấn control nào) | API Name | Method | URL | Sync/Async | Request param (nguồn field nào trên màn) | Tham chiếu tài liệu API BE |
|---|---|---|---|---|---|---|

Cột cuối bắt buộc trỏ tới `.claude/references/backend/api/<slug>/endpoints.md`
(API thuộc màn này) hoặc slug/API dùng chung khác nếu tái sử dụng.

### 11. Process
*(nguồn: sheet Process + 画面API実行処理一覧)*

- Flow chart Mermaid (`graph TD` hoặc `sequenceDiagram`) cho luồng chính: vào
  màn → API nào gọi trước → điều kiện → API tiếp theo.
- Bảng xử lý theo từng API ở mục 10:

| Action | API | Khi thành công | Khi lỗi (mã lỗi nếu biết) → FE xử lý thế nào |
|---|---|---|---|

## Liên kết chéo

- Mục 10 là điểm nối duy nhất giữa file này và tài liệu API BE — mọi thông tin
  chi tiết về API (request/response field, business rule phía BE) không lặp
  lại ở đây, chỉ tham chiếu.
- Nếu API phức tạp cần "detailed design" riêng (nhiều bảng, transaction, rẽ
  nhánh nghiệp vụ), xem `.claude/references/design/be-api-design-format.md`.
