# API Design Doc Format — Basic Design cho API phức tạp

Nguồn: đối chiếu cấu trúc từ `Document/BE_API/API_GR007_Transaction.xlsx`
(Cover + các cặp sheet `<METHOD> <Tên tính năng>` / `SQL_<METHOD> <Tên tính
năng>`, VD `POST A Transaction` / `SQL_POST A Transaction`).

Mục đích: đặc tả trước khi code cho API đủ phức tạp (nhiều bảng liên quan, có
transaction/lock, hoặc nghiệp vụ rẽ nhánh) — mà `endpoints.md` hiện tại (ngắn
gọn, chỉ method/path/mẫu request-response) không đủ chi tiết để implement mà
không phải hỏi lại.

Áp dụng cho: bước chuẩn bị trước `backend-implement-api` /
`backend-database-change` khi cần transaction/lock phức tạp; tham chiếu ngược
từ `.claude/docs/design/<slug>.md` mục 10 (Required APIs) của mọi màn có gọi API này —
xem `.claude/references/design/fe-screen-design-format.md`.

## Khi nào dùng format này

- **Dùng khi:** nhiều bảng liên quan trong 1 request, có transaction/lock,
  hoặc nghiệp vụ rẽ nhiều case xử lý khác nhau (VD tạo mới vs cập nhật vs xóa
  trong cùng 1 API).
- **Không cần dùng khi:** API CRUD đơn giản, 1 bảng, không transaction phức
  tạp — `endpoints.md` hiện có là đủ, không cần bật file design riêng.

## Quy ước đặt tên

- 1 API = 1 khối gồm 2 phần:
  - **`<METHOD> <Tên tính năng>`** — business flow, request/response.
  - **`SQL_<METHOD> <Tên tính năng>`** — các bước SQL/transaction thực thi,
    khớp số bước với phần "Process" ở khối trên.
- Tên tính năng bằng tiếng Anh, mô tả HÀNH ĐỘNG chứ không mô tả URL
  (VD `A Transaction`, không phải `/real-goods-receipts`).
- Nhiều API cùng 1 entity gộp vào 1 file — tương đương
  `.claude/references/backend/api/<slug>/design.md`, nhiều khối bên trong
  theo entity đó (tương tự 1 file `API_<mã nhóm>_<Entity>.xlsx` chứa nhiều
  API trong mẫu gốc).

## Cấu trúc khối `<METHOD> <Tên tính năng>`

1. **Summary** — 1 câu mô tả nghiệp vụ, không mô tả kỹ thuật.
2. **URL** — path thật, gồm path/query param.
3. **Method** — GET/POST/PUT/PATCH/DELETE.
4. **Request** — bảng field:

   | Field | Type | Required | Validate | Mô tả |
   |---|---|---|---|---|

5. **Process** — các bước xử lý theo thứ tự, đánh số (1, 2, 3...), nêu rõ mỗi
   bước tác động entity/bảng nào, check điều kiện gì trước khi ghi.
6. **Response** — bảng theo HTTP code, bắt buộc có ít nhất: thành công
   (200/201), validate fail (400), và mọi mã lỗi nghiệp vụ riêng (409 conflict,
   404 not found...):

   | HTTP Code | Message ID (nếu có mã lỗi chuẩn) | Response body / Message |
   |---|---|---|

## Cấu trúc khối `SQL_<METHOD> <Tên tính năng>`

1. **Alias** — bảng rút gọn tên bảng/entity dùng ở các bước dưới (A, B, C...
   → tên bảng thật), tránh lặp tên bảng dài mỗi bước:

   | Alias | Tên bảng/entity thật |
   |---|---|

2. Từng bước xử lý dữ liệu, đánh số KHỚP với bước ở mục "Process" của khối API
   phía trên, mỗi bước gồm:
   - **No.** — khớp số bước.
   - **Overview** — bước này làm gì, tương ứng bước nào trong flow chart.
   - **Usage** — kết quả bước này dùng để làm gì tiếp theo.
   - **Retrieved/Updated content** — field lấy ra hoặc ghi vào:

     | # | Alias.Field | Ghi chú |
     |---|---|---|

3. API có update/delete nhiều bảng theo nhiều case nghiệp vụ khác nhau: tách
   mục con riêng theo từng case (VD "Case dữ liệu đã tồn tại" / "Case tạo
   mới") — không viết chung 1 luồng nếu logic rẽ nhánh khác nhau, vì mỗi
   nhánh thường khác nhau về bảng bị ảnh hưởng và điều kiện lock.

## Liên kết chéo bắt buộc

- Tên entity/slug ở đầu file phải khớp với API Name dùng ở mục 10 (Required
  APIs) trong MỌI `.claude/docs/design/<slug>.md` có gọi API này.
- API dùng chung nhiều màn (prefix `COM*` hoặc tương đương) đặt ở
  `.claude/references/backend/api/_common/`, không gắn vào 1 slug màn cụ thể
  — tránh trùng lặp khi nhiều màn cùng tham chiếu.
