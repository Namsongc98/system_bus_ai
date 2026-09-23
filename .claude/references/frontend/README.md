# Frontend References — Mục lục

Thư mục này chứa toàn bộ tài liệu tham chiếu cho frontend (`booking_ticket_vue`, Vue 3 + Vite +
Pinia + Vue Router + Axios + Tailwind + Nuxt UI). Đã tái tổ chức từ dạng file `.md` nằm rời rạc sang
theo nhóm chức năng — mỗi nhóm có README/`_conventions.md` riêng, không cần đọc lại toàn bộ thư mục
mỗi lần.

## Bắt đầu từ đâu

| Cần gì | Đọc gì |
|---|---|
| Kiến trúc tổng thể, quy tắc code, cấu trúc thư mục `src/` | [`frontend-instructions.md`](./frontend-instructions.md), [`folder-structure.md`](./folder-structure.md) (ở gốc) |
| Viết/sửa service gọi API cho 1 màn cụ thể | [`api/<slug>/endpoints.md`](./api/) — tra theo tên màn, khớp `.claude/docs/design/` và `references/backend/api/` |
| Quy ước chung của toàn bộ API (port, cách bóc response, path nào khớp backend) | [`api/_conventions.md`](./api/_conventions.md) |
| Viết Pinia store / service layer JSON / service export-Blob / xử lý lỗi API | [`services/`](./services/) |
| Tạo component tái dùng, ghép trang từ Figma, danh sách component sẵn có | [`components/`](./components/) |
| Quy tắc bắt buộc (component, clean code, style Tailwind/Figma, API service) | [`rules/`](./rules/) |

## Cây thư mục sau khi tái tổ chức

```text
references/frontend/
├── README.md                         # file này
├── frontend-instructions.md          # kiến trúc tổng thể (giữ ở gốc — điểm vào đầu tiên)
├── folder-structure.md               # cấu trúc src/ thật (giữ ở gốc — điểm vào đầu tiên)
├── api/                               # API theo từng màn (17 slug, khớp .claude/docs/design/ + backend/api/)
│   ├── _conventions.md
│   ├── README.md
│   ├── _legacy/                      # tài liệu API cũ đã bị thay thế — giữ tham khảo, không còn là nguồn thật
│   │   ├── api-document.md
│   │   └── trips-management-api-readiness.md
│   └── <17 thư mục theo slug màn hình>/endpoints.md
├── services/                          # quy tắc + ví dụ viết service/store layer
│   ├── api-service.md
│   ├── api-json-service.md
│   ├── api-download-service.md
│   ├── api-error-handling.md
│   └── pinia-store.md
├── components/                        # quy tắc + registry component tái dùng
│   ├── component-registry.md
│   ├── component-reuse-patterns.md
│   └── page-integration-patterns.md
└── rules/                             # quy tắc bắt buộc (không đổi vị trí)
    ├── api-service-rules.md
    ├── clean-code.md
    ├── figma-style-rules.md
    └── rule-component.md
```

## Vì sao tách `api/` khỏi `services/`

- **`api/`** = "API nào tồn tại, path/field thật là gì, màn nào/nút nào gọi nó, có khớp backend
  không" — dữ liệu tra cứu theo màn hình, cập nhật khi backend/FE code đổi.
- **`services/`** = "cách viết 1 service/store mới theo đúng convention của dự án" — quy tắc chung,
  không gắn với 1 màn cụ thể, ít thay đổi hơn.

Trước đây `api-document.md` (dữ liệu tra cứu) và `api-service.md`/`pinia-store.md` (quy tắc viết code)
nằm chung 1 cấp thư mục, dễ nhầm giữa "đây là API thật" và "đây là cách viết code" — đặc biệt khi
`api-document.md` mô tả sai gần như toàn bộ path/field thật (xem
[`api/README.md`](./api/README.md) mục "Phát hiện xuyên suốt" phần 10). Tách riêng để `api/` luôn là
nguồn tra cứu bám sát code thật (backend + frontend), còn `services/`/`components/`/`rules/` là quy
tắc ổn định, không cần cập nhật mỗi khi 1 endpoint đổi path.
