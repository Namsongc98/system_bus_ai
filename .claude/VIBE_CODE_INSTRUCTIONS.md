# Hướng Dẫn Vibe Code

Đọc file này trước khi làm "vibe code" trong System_bus với Claude Code — tức
là mô tả ý định bằng ngôn ngữ tự nhiên và để Claude sinh/sửa code. File gồm 2
phần: (1) luồng Claude đi từ ý tưởng đến merge, và (2) danh mục đầy đủ
`.claude/`, ghi rõ phần nào Claude tự làm, phần nào cần người.

Repo này trước đây có chạy song song Codex với cây `.codex/` riêng. Giờ
không dùng nữa — chỉ còn duy trì `.claude/`. File này không mô tả `.codex/`.

---

## 1. "Vibe code" ở repo này nghĩa là gì

Bạn mô tả ý định bằng ngôn ngữ tự nhiên; Claude đọc, lên kế hoạch, và sửa
code. Để việc này không hỗn loạn qua nhiều session/nhiều người, có 4 lớp
ràng buộc, mỗi lớp được đọc vì 1 lý do khác nhau:

```
CLAUDE.md              -> kiến trúc, lệnh, quy ước (Claude đọc mỗi session)
  .claude/references/   -> luật chi tiết theo domain, đọc theo từng task
    .claude/skills/      -> workflow đóng gói sẵn, Claude tự chọn khi khớp task
      .claude/commands/   -> template mỏng, bạn gọi tường minh
        .claude/hooks/     -> lưới an toàn, tự chạy trên mọi hành động liên quan
```

Tài liệu thiết kế (`docs/design/*.md` sinh từ `/clear-spec`) là nguồn sự
thật khi đã có cho 1 trang/API. Đổi yêu cầu thì sửa tài liệu thiết kế TRƯỚC,
rồi mới sửa code — không để 2 bên lệch nhau.

---

## 2. Luồng từ đầu đến cuối

```
 (tùy chọn, việc có nhiều work-unit)
 .claude/ledger/<feature>.md  ---- theo dõi spec/implement/test/review/lead-review
        |                          cho từng work-unit
        v
 [0] /clear-spec  ----------------- tài liệu thiết kế tại docs/design/<slug>.md
        |                            (tùy chọn; dùng cho trang/API mới hoặc chưa rõ)
        v
 [0.5] page-api-review / skill fullstack-page-api-review --- bảng đối chiếu FE-BE
        |                                                      (trước khi nối trang với API thật)
        v
 [1] Implement -------------------- backend-implement / skill backend-implement-api
        |                            frontend: figma-to-vue / integrate-component / reuse-component /
        |                            frontend-integrate-api* / frontend-wire-api-to-event /
        |                            frontend-api-pinia-store
        v
 [2] Review tự động --------------- backend-review, frontend-code-review, hoặc parallel-review
        |                            (gọi các subagent backend-reviewer / frontend-reviewer /
        |                             security-reviewer / test-gap-reviewer, chỉ đọc)
        v
 [3] /make-testcase --------------- file Excel test case tại docs/testcase/ (tùy chọn, cho QA)
        |
        v
 [4] /lead-review ----------------- người xác nhận; chỉ bạn được tick dòng `lead-review`
        |                            trong ledger
        v
      merge (dọn worktree nếu có dùng, qua skill/command git-worktree)
```

Các nhánh phụ, dùng khi cần chứ không theo thứ tự cố định:

| Cần gì | Dùng gì |
|---|---|
| Sửa bug backend | `/backend-fix-bug` |
| Sửa bug/lỗi frontend | skill `frontend-fix-error` |
| Giải thích hành vi backend hiện có | `/backend-explain` |
| Truy vết 1 luồng FE bị lỗi (UI -> store -> service -> API) | skill `frontend-check-flow` |
| Chẩn đoán lỗi build/DB/Redis/Kafka/Docker backend | skill `backend-debug` |
| Refactor service Spring mà không đổi hành vi | skill `backend-refactor-service` |
| Đổi entity JPA, schema, migration | skill `backend-database-change` |
| Thêm/đổi producer/consumer Kafka | skill `backend-kafka-event` |
| Viết/cải thiện test backend | skill `backend-write-test` |
| Audit 1 release | skill `backend-release-readiness` |
| Tách việc ra 1 Git worktree riêng | `/git-worktree` hoặc skill `git-worktree` |
| Xoay 1 credential bị lộ | `.claude/references/backend/workflows/credential-rotation.md` |
| Audit chính `.claude/` | `/config-audit` (hoặc agent `config-reviewer`), `/review-hooks` |
| Quyết định 1 năng lực mới nên đặt ở đâu | skill `claude-capability-review` |

---

## 3. Danh mục đầy đủ `.claude/`

Mỗi mục được gắn nhãn cách nó được kích hoạt:
**[command]** bạn gõ `/tên-lệnh` để gọi tường minh.
**[skill]** Claude tự chọn khi task khớp với phần mô tả của nó — không cần
gõ lệnh.
**[agent]** 1 subagent chỉ-đọc mà Claude triệu hồi, chỉ từ 1 review command,
không bao giờ tự ý.
**[hook]** tự chạy trên 1 sự kiện lifecycle, không ai gọi.
**[reference]** kiến thức thụ động, được 1 skill/command/agent đọc khi cần —
tự nó không làm gì cả.
**[human gate]** chỉ bạn được cập nhật.

### `CLAUDE.md` (gốc repo) — [reference]
Claude đọc file này mỗi session. Kiến trúc, bản đồ module, các lệnh, role,
trạng thái, config, và trỏ tới tài liệu chi tiết ở `ticket-system/.github/`.

### `.claude/settings.json` — [hook wiring]
Danh sách `deny` quyền Read/Write với `.env`/`.env.*`, và nối
`.claude/hooks/codex_hook.py` vào 5 sự kiện: `PreToolUse` (Bash),
`PermissionRequest` (Bash), `PostToolUse` (Bash), `UserPromptSubmit`, `Stop`.

### `.claude/hooks/` — [hook]
- `codex_hook.py` — policy thật sự, chạy trên mọi sự kiện đã wire ở trên:
  - **PreToolUse (Bash)** — CHẶN CỨNG (exit 2) các lệnh phá hoại (`rm -rf`,
    `git reset --hard`, `git clean -f`, force push, `chmod 777`, xóa
    worktree không quản lý, xóa trực tiếp branch/ref) và giờ còn chặn cả
    truy cập dotenv/biến môi trường nhạy cảm: đọc file `.env`/`.env.*`, dump
    môi trường (`env`, `printenv`, `export -p`, `declare -x`), hoặc tham
    chiếu `$JWT_*`/`$DB_*`/`$MAIL_*`/`$MINIO_*` trong 1 lệnh.
  - **PermissionRequest (Bash)** — chỉ cảnh báo (không chặn) nếu lý do xin
    quyền ngắn hơn 12 ký tự hoặc nghe quá rộng ("anything", "full access",
    "bypass"...).
  - **PostToolUse (Bash)** — cảnh báo nếu lệnh vừa chạy có exit code khác 0,
    kèm gợi ý riêng cho Maven/npm.
  - **UserPromptSubmit** — cảnh báo nếu nội dung prompt trông có vẻ chứa
    secret.
  - **Stop** — cảnh báo (không bao giờ chặn) nếu git diff/file chưa track có
    vẻ chứa secret, và cảnh báo nếu còn `.claude/ledger/*.md` nào chưa tick
    hết; nếu không thì nhắc Claude báo cáo file đã đổi, lệnh verify đã chạy,
    check nào bị bỏ qua, và rủi ro còn lại trước khi trả lời cuối.
  - Tất cả check trừ PreToolUse đều là cảnh báo (fail-open theo thiết kế) —
    chỉ `PreToolUse` mới thực sự chặn.
- `test_codex_hook.py` — unit test cho policy (chạy bằng `python3
  .claude/hooks/test_codex_hook.py`).

### `.claude/agents/` — [agent]
5 subagent chỉ-đọc (`tools: Read, Grep, Glob` — không sửa file), được
`parallel-review` (hoặc 1 command `*-review` cụ thể) triệu hồi, không bao
giờ tự ý hoạt động:
- `backend-reviewer` — API Spring Boot, security, transaction, tính nhất
  quán dữ liệu, Redis/Kafka, test còn thiếu.
- `frontend-reviewer` — Vue, Pinia, Axios, routing, accessibility, Tailwind,
  tái sử dụng component.
- `security-reviewer` — secret, auth/authz, log không an toàn, config nguy
  hiểm, hành vi Claude/tooling rủi ro.
- `test-gap-reviewer` — test unit/integration/e2e còn thiếu.
- `config-reviewer` — sự nhất quán của `CLAUDE.md`, chính `.claude/` (tham
  chiếu cũ, link markdown hỏng, skill trùng lặp, hook quá nguy hiểm/chậm,
  subagent được phép sửa file, roadmap bị lệch).

### `.claude/commands/` — [command]
Các template lệnh mỏng (front-matter + template yêu cầu + hướng dẫn cho
Claude), liệt kê theo phạm vi:

| Command | Công dụng |
|---|---|
| `/backend-explain` | Giải thích hành vi, trách nhiệm, rủi ro của code backend. |
| `/backend-fix-bug` | Chẩn đoán và sửa 1 bug backend, có verify tập trung. |
| `/backend-implement` | Cài đặt 1 tính năng backend (Spring Boot). |
| `/backend-review` | Review thay đổi backend (đúng/sai, security, an toàn dữ liệu, test) qua skill `backend-code-review`. |
| `/clear-spec` | Viết tài liệu thiết kế vào `docs/design/` trước khi code. |
| `/config-audit` | Audit `AGENTS.md`, skill/prompt/reference/hook/subagent trong `.claude`. |
| `/figma-to-vue` | Chuyển HTML/CSS từ Figma thành 1 Vue 3 SFC theo quy ước dự án. |
| `/git-worktree` | Xem trước và áp dụng 1 thao tác Git worktree kiểu review-first. |
| `/integrate-component` | Ghép 1 trang Vue từ HTML Figma bằng các component tái sử dụng có sẵn. |
| `/lead-review` | Tổng hợp kết quả review + trạng thái ledger; gate xác nhận của người. |
| `/make-testcase` | Xuất 1 file Excel test case vào `docs/testcase/` từ tài liệu clear-spec. |
| `/page-api-review` | Review 1 trang Vue về mức độ sẵn sàng API, khớp hợp đồng FE-BE. |
| `/parallel-review` | Chạy đồng thời 4 subagent backend/frontend/security/test-gap. |
| `/reuse-component` | Tạo/điền/refactor 1 component Base/Common tái sử dụng từ HTML Figma. |
| `/review-hooks` | Review thiết kế hook, rủi ro chính sách, mô hình tin cậy, kế hoạch verify. |

### `.claude/skills/` — [skill]
Các workflow đóng gói sẵn mà Claude tự khớp với task qua phần `description`
— không cần gõ lệnh, chỉ cần mô tả việc cần làm:

| Skill | Công dụng |
|---|---|
| `backend-code-review` | Review thay đổi backend: bug, regression, security, tính nhất quán dữ liệu, test còn thiếu. |
| `backend-database-change` | Entity JPA, repository, native query, transaction, locking, index, Flyway/Liquibase. |
| `backend-debug` | Chẩn đoán lỗi build/startup/API/DB/Redis/Kafka/Docker ở backend. |
| `backend-implement-api` | Thêm hoặc đổi 1 endpoint REST Spring Boot. |
| `backend-kafka-event` | Producer/consumer Kafka, event DTO, retry, DLQ, idempotency, transaction. |
| `backend-refactor-service` | Refactor tầng service Spring mà vẫn giữ hành vi. |
| `backend-release-readiness` | Audit 1 release: build, test regression, secret bị lộ, config production, migration, tương thích Kafka, observability, rủi ro deploy. |
| `backend-write-test` | Thêm/cải thiện test backend, kể cả Testcontainers. |
| `claude-capability-review` | Quyết định đúng "bề mặt" nào trong `.claude/` (hook/skill/command/agent/MCP/plugin/automation) cho 1 năng lực mới. |
| `frontend-api-pinia-store` | Tạo/cập nhật Pinia store bọc quanh các lời gọi API. |
| `frontend-check-flow` | Truy vết 1 luồng tính năng Vue từ đầu đến cuối khi chưa rõ tầng nào lỗi. |
| `frontend-code-review` | Review Vue 3 SFC về đúng/sai, quy ước, accessibility, Tailwind, kiến trúc. |
| `frontend-figma-to-vue` | Chuyển HTML/ghi chú/ảnh chụp từ Figma thành 1 Vue 3 SFC sạch. |
| `frontend-fix-error` | Debug/sửa lỗi Vue, Pinia, Axios, router, runtime, build. |
| `frontend-integrate-api` | Thêm/cập nhật hàm service Vue trả về JSON (GET/POST/PUT/PATCH/DELETE). |
| `frontend-integrate-api-from-doc` | Chuyển tài liệu/spec API backend thành hàm service Vue. |
| `frontend-integrate-download-api` | Thêm/cập nhật hàm service Vue cho Blob/export/report/PDF/Excel/ảnh tải về. |
| `frontend-reuse-component` | Phát hiện và tái sử dụng component Vue có sẵn trước khi tạo UI mới. |
| `frontend-wire-api-to-event` | Nối 1 API/store action/composable vào 1 event handler của component. |
| `fullstack-page-api-review` | Bảng đối chiếu FE-BE + kế hoạch chuẩn bị backend cho các API của 1 trang. |
| `git-worktree` | Xem trước/tạo/liệt kê/dọn dẹp 1 Git worktree độc lập. |

Một vài skill còn có thêm `agents/openai.yaml` — 1 lớp mô tả display-name/
description để expose cùng skill đó cho 1 agent runner khác ngoài Claude.
Claude Code không đọc file này; nó không thuộc luồng Claude.

### `.claude/references/` — [reference]
Kiến thức domain thụ động, được skill/command/agent đọc khi cần — tự nó
không bao giờ hành động.

- `backend/project-context.md` — bối cảnh backend cấp dự án.
- `backend/environment-variable-names.md` — chỉ liệt kê **tên** biến môi
  trường, không có giá trị; đây là thứ `PreToolUse` dùng để giải thích vì
  sao nó chặn truy cập `.env`.
- `backend/rules/` — `api`, `architecture`, `backend`, `clean-code`,
  `database`, `docker`, `kafka`, `observability`, `redis`, `security`,
  `testing`.
- `backend/workflows/` — `credential-rotation`, `database-change`,
  `docker-kafka-setup`, `docker-redis-setup`, `implement-endpoint`,
  `investigate-issue`, `openapi-contract`.
- `frontend/` — `api-document`, `api-download-service`, `api-error-handling`,
  `api-json-service`, `api-service`, `component-registry`,
  `component-reuse-patterns`, `folder-structure`, `frontend-instructions`,
  `page-integration-patterns`, `pinia-store`, `trips-management-api-readiness`.
- `frontend/rules/` — `api-service-rules`, `clean-code`, `figma-style-rules`,
  `rule-component`.

### `.claude/ledger/` — [human gate] + [reference]
Theo dõi tiến độ tùy chọn cho feature có nhiều work-unit:
- `README.md` — giải thích quy ước.
- `TEMPLATE.md` — bản gốc để copy thành 1 ledger mới.
- Các ledger đang hoạt động (tạo khi cần) — checklist cho từng work-unit:
  `spec / implement / test / review / lead-review`. Các command tự tick
  dòng của mình; **chỉ bạn được tick `lead-review`** (và trên thực tế nên tự
  xác nhận cả dòng `spec` sau khi đọc tài liệu `/clear-spec`).

### `.claude/worktrees/` — đầu ra runtime, không phải config
Các bản checkout Git worktree thật sự, tạo bởi skill/command `git-worktree`
cho các task cần tách biệt. Không phải chỗ bạn tự sửa trực tiếp; dọn dẹp qua
`/git-worktree`, không bao giờ `rm -rf` (hook đã chặn việc xóa force không
quản lý rồi).

### `.claude/CLAUDE_CAPABILITY_ROADMAP.md` và `.claude/MIGRATION_REPORT.md`
Tài liệu changelog/lý do sống cho những gì có trong `.claude/` và vì sao.
Cập nhật `CLAUDE_CAPABILITY_ROADMAP.md` mỗi khi thêm/đổi/xóa 1 năng lực
trong `.claude/`, theo đúng phong cách các mục đã có.

---

## 4. Ai làm, và khi nào

| Kích hoạt bởi | Ví dụ | Có cần bạn gọi không? | Có được sửa code không? |
|---|---|---|---|
| **Hook** | `codex_hook.py` trên sự kiện Bash/prompt/stop | Không — tự chạy trên mọi sự kiện khớp | Không — chỉ chặn hoặc cảnh báo |
| **Skill** | `backend-implement-api`, `frontend-fix-error`,... | Không — Claude tự chọn theo mô tả task | Có |
| **Command** | `/clear-spec`, `/lead-review`,... | Có — bạn gõ `/tên-lệnh` | Tùy lệnh (các lệnh implement thì có; các lệnh review/lead-review chỉ-đọc theo thiết kế) |
| **Agent** | `backend-reviewer`, `security-reviewer`,... | Gián tiếp — chỉ được 1 review command triệu hồi | Không — chỉ đọc |
| **Reference** | `.claude/references/**` | Không bao giờ trực tiếp — được đọc ngầm bởi các mục trên | Không áp dụng |
| **Ledger** | `.claude/ledger/*.md` | Bạn tick `spec`/`lead-review`; các command tick phần còn lại | Bạn được sửa trực tiếp nếu muốn |

Quy tắc cứng xuyên suốt: review tự động (`agents/`) và kết quả `/lead-review`
chỉ mang tính đề xuất — **chỉ bạn được tick dòng `lead-review`**, Claude
không bao giờ tự đánh dấu 1 work-unit là xong thay bạn.

---

## 5. Ví dụ đầy đủ — thêm 1 trang admin mới

1. (Nếu là 1 phần của nhiều trang tương tự) tạo
   `.claude/ledger/<feature-slug>.md` từ `TEMPLATE.md`.
2. `/clear-spec` — sinh `docs/design/<page>.md` từ mockup/yêu cầu. Bạn đọc
   và xác nhận.
3. Skill `fullstack-page-api-review` (hoặc `/page-api-review`) — xác nhận API
   backend nào đã có, API nào cần xây mới.
4. Backend: skill `backend-implement-api` cho endpoint còn thiếu.
   Frontend: `frontend-figma-to-vue` / `integrate-component` cho trang, rồi
   `frontend-integrate-api` / `frontend-api-pinia-store` /
   `frontend-wire-api-to-event` để nối vào.
5. `/parallel-review` — triệu hồi 4 subagent review; sửa các finding.
6. `/make-testcase` — tùy chọn, nếu QA cần 1 file Excel.
7. `/lead-review` — Claude tổng hợp; bạn xác nhận và tick `lead-review`
   trong ledger.
8. Merge (dọn worktree qua `/git-worktree` nếu có dùng).

---

## 6. Sửa chính `.claude/`

Dùng skill `claude-capability-review` để quyết định 1 năng lực mới nên đặt ở
đâu trước khi thêm. Sau khi sửa `.claude/`, chạy `/config-audit` (hoặc agent
`config-reviewer`), và riêng với thay đổi hook thì chạy thêm `/review-hooks`
và `python3 .claude/hooks/test_codex_hook.py`. Ghi lại thay đổi vào
`CLAUDE_CAPABILITY_ROADMAP.md`.
