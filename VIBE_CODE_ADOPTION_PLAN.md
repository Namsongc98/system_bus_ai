# Kế hoạch áp dụng "Vibe Code chuẩn hóa" vào System_bus

*So sánh 2 nguồn tham khảo (`skillbase-sample`, `command_and_rule_cusor`) với `.claude/` hiện tại của System_bus, và lộ trình nâng cấp.*

---

## 0. Kết luận nhanh

`System_bus/.claude/` **đã khá mạnh** — mạnh hơn phần lớn ví dụ trong `skillbase-sample` về mặt cấu trúc: đã có 21 Skills dạng SKILL.md, 5 subagent review chuyên biệt (backend/frontend/security/config/test-gap), hook an toàn (chặn lệnh phá hoại, dò secret), references tách theo domain rất chi tiết (backend rules/workflows, frontend rules/patterns).

Cái **chưa có** — và là phần giá trị nhất nên lấy từ `skillbase-sample` — là lớp **"kỷ luật quy trình"**: ép Claude đi đúng thứ tự spec → code → test → review → người duyệt, thay vì chỉ dựa vào rule khuyên nhủ. Cụ thể 4 việc nên làm, xếp theo độ ưu tiên:

1. Thêm command **`/lead-review`** — gate DoD do người ký, tách khỏi review tự động đã có.
2. Thêm **ledger** (bảng trạng thái) theo từng feature lớn để biết đang ở bước nào.
3. Nâng cấp `claude_hook.py` (Stop hook) để **chặn Claude tự tuyên bố "done"** khi chưa build/test pass.
4. Khi cần làm hàng loạt màn hình/API tương tự → thêm **batch runner** (bash, vì máy Mac) chạy 1 session riêng cho mỗi đối tượng.

Phần dưới giải thích chi tiết từng mục, kèm checklist hành động.

---

## 1. Bảng đối chiếu

| Thành phần | `skillbase-sample` / `command_and_rule_cusor` | System_bus hiện tại | Việc cần làm |
|---|---|---|---|
| Constitution (CLAUDE.md) | 7 mục cố định: metadata, AR rules có severity, DO NOT, bảng task→ref→command, checklist | `CLAUDE.md` đã có kiến trúc, lệnh, quy ước — khá đầy đủ, hơi thiếu bảng "task type → ref → command" tường minh | Bổ sung 1 bảng routing ngắn (tùy chọn, không cấp thiết) |
| Rules chi tiết theo domain | `.claude/rules/*.md` (routing, MVC, style, DB, security, component) | `.claude/references/{backend,frontend}/rules/*.md` — **đã tương đương, còn chi tiết hơn** (api, architecture, clean-code, database, docker, kafka, observability, redis, security, testing…) | Không cần làm gì thêm |
| Commands mỏng | Front-matter + WHAT/WHY/WHEN + `<gate_criteria>` + Post-review 5 chiều | 12 command trong `.claude/commands/` — có review, fix-bug, implement, nhưng **không có `/clear-spec`, `/make-testcase`, `/lead-review`** | Thêm 3 command này (mục 3, 4) |
| Skills | Không có khái niệm Skill riêng (dùng command) | 21 Skills đầy đủ (`SKILL.md`, có skill còn kèm `agents/openai.yaml`, script Python) | **Không cần làm gì — System_bus đang tiến bộ hơn ở điểm này** |
| Subagent review | Không có | 5 subagent review read-only (backend/frontend/security/config/test-gap) trong `.claude/agents/` | Đã tốt — có thể tái dùng cho `/lead-review` (mục 3) |
| Hook enforcement | 5 hook: gate-check, coverage-gate, evidence-lint, post-build, **stop-verify** — chặn ghi code/tuyên bố "done" khi chưa đạt điều kiện | `claude_hook.py` mới dừng ở **an toàn** (chặn `rm -rf`, `git push --force`, dò secret) — Stop hook hiện chỉ "nhắc", chưa **chặn** | Nâng cấp Stop hook (mục 5) |
| Ledger (nguồn sự thật của gate) | 1 bảng trạng thái mỗi pipeline: work-unit × bước = ô trạng thái, chỉ user set "verified" | Không có | Thêm ledger nhẹ theo feature lớn (mục 2) |
| Batch tự động hàng loạt | `.claude/batch/*.ps1` — 1 session/đối tượng, chạy đêm, log/report riêng | Không có (System_bus có `git-worktree` skill để chạy song song, nhưng không có vòng lặp theo danh sách đối tượng) | Thêm khi cần làm nhiều màn/API cùng dạng (mục 4) |
| Test case Excel cho QA | `/make-testcase` xuất `.xlsx` theo template khách | `backend-write-test`, `frontend-*` chỉ sinh unit test code, không xuất Excel cho non-dev | Thêm nếu có nhu cầu bàn giao QA/khách hàng (mục 4) |
| Định dạng Cursor (`.mdc`) | `command_and_rule_cusor` toàn bộ ở `.cursor/` | Không có `.cursor/` trong System_bus | Chỉ cần nếu team cũng dùng Cursor (mục 6) |
| Ý tưởng cấu trúc store 4-file (model/service/store/index) | `store-create.mdc` (Angular + NgRx) | `pinia-store.md` đã có template tương đương cho Vue + Pinia | Không cần copy, chỉ tham khảo ý tưởng tách file nếu muốn |

---

## 2. Thêm Ledger nhẹ (ưu tiên cao, rẻ, không cần hook ngay)

**Vấn đề:** với feature lớn (nhiều trang admin, nhiều API), hiện không có nơi nào ghi "trang X đã xong spec chưa, đã review chưa, đã QA chưa" — dễ quên bước hoặc report sai tiến độ.

**Cách làm:** với mỗi feature/đợt việc lớn, tạo 1 file `docs/ledger/<feature-slug>.md`:

```markdown
| Work-unit (trang/API) | spec | implement | test | review | lead-review |
|---|---|---|---|---|---|
| admin/trip-management | done | done | done | done | ☐ |
| admin/bus-management  | done | doing | ☐ | ☐ | ☐ |
| POST /api/trips        | done | done | done | ☐ | ☐ |
```

- Mỗi command (`backend-implement`, `frontend-*`, `backend-review`…) tự cập nhật ô của mình khi xong.
- **Chỉ người dùng** được đánh dấu cột `lead-review` — đây là quy ước, chưa cần ép bằng hook ở bước này.

---

## 3. Thêm command `/lead-review` (ưu tiên cao)

System_bus đã có review tự động rất tốt (`backend-review`, `frontend-code-review`, `parallel-review` chạy 5 subagent). Cái thiếu là **gate cuối do người ký** trước khi coi 1 work-unit là "Definition of Done" — đúng tinh thần "tuyến review 2 tầng" của `skillbase-sample`.

Gợi ý nội dung `.claude/commands/lead-review.md`:

- **WHAT/WHY/WHEN**: chạy sau khi `parallel-review` đã pass, trước khi merge/đóng ticket.
- Tổng hợp kết quả từ các subagent review + trạng thái ledger (mục 2).
- Liệt kê rõ: đã build pass? đã test pass? còn `(TODO/cần xác nhận)` nào không?
- Xuất báo cáo ngắn để người dùng đọc và **tự tay** đánh dấu ledger — Claude không tự đánh dấu `lead-review = done`.

---

## 4. Batch runner + `/clear-spec` + `/make-testcase` (khi khối lượng việc lớn)

Chỉ cần làm khi bạn có **nhiều đối tượng lặp lại cùng dạng** — ví dụ chuẩn hóa lại toàn bộ các trang admin CRUD (tuyến, xe, chuyến, vé, tài khoản) hoặc rà toàn bộ endpoint của `manage-revenue-ticket`. Nếu chỉ làm lẻ tẻ từng trang thì gõ tay slash command là đủ, không cần batch.

**`/clear-spec`** (thiết kế chi tiết trước khi code — hiện System_bus chưa có bước này tường minh):
- Input: mockup Figma + `.claude/references/frontend/trips-management-api-readiness.md`-style doc, hoặc API spec.
- Output: 1 file thiết kế chi tiết cho trang/API đó (field, validation, trạng thái, luồng), review xong mới cho `/backend-implement` hoặc `frontend-integrate-api` chạy.

**`/make-testcase`**: sinh test case dạng bảng/Excel từ file `/clear-spec` xuất ra — dùng `xlsx` skill sẵn có của Claude, theo đúng nguyên tắc trong `creating_outputs`, để bàn giao QA/khách hàng không đọc code được.

**Batch runner** (`scripts/batch/` — dùng **bash**, không dùng `.ps1` vì máy bạn là macOS):

```
scripts/batch/
├── unit-ids.txt          # 1 dòng/đối tượng, "#" = comment
├── run-command.sh         # đọc unit-ids.txt, với mỗi id: claude -p "/cmd <id>" --dangerously-skip-permissions, 1 session riêng
├── logs/                  # log theo <cmd>-<id>-<timestamp>.log
└── README.md
```

Nguyên tắc an toàn khi dùng batch (rút từ `skillbase-sample`):
- Chạy **tuần tự**, không song song, để dễ trace lỗi.
- `--dangerously-skip-permissions` chỉ dùng trong repo tin cậy, luôn `git diff` trước khi commit.
- Nên chạy các batch nặng (implement/review hàng loạt) ngoài giờ, sáng hôm sau review kết quả.

---

## 5. Nâng cấp hook Stop để **chặn** thay vì chỉ nhắc (ưu tiên trung bình)

`claude_hook.py` hiện tại đã wire sẵn event `Stop` (xem `.claude/settings.json`) nhưng theo `CLAUDE_CAPABILITY_ROADMAP.md` thì Stop hook mới ở dạng "reminder", chưa chặn cứng. Theo mẫu `stop-verify.ps1.tmpl` của `skillbase-sample`, có thể mở rộng để:

- Regex hẹp bắt các câu kiểu "đã hoàn thành/verified/done" trong response cuối.
- Nếu bắt được mà **không** thấy log build/test pass gần nhất (hoặc cờ trong ledger) → chặn (exit khác 0 theo cơ chế hook hiện có) và yêu cầu chạy build/test trước.
- **Fail-open**: nếu hook lỗi hạ tầng → cho qua, nhưng log rõ lý do bỏ qua (tránh việc hook lỗi làm treo toàn bộ session).
- Có override (`disable-check`) để tránh false-positive với các đoạn văn bản phân tích không phải tuyên bố hoàn thành thật.

Đây là thay đổi có rủi ro (có thể chặn nhầm) — nên làm sau, test kỹ trên 1 nhánh trước khi bật mặc định.

---

## 6. Việc không cần/chỉ làm nếu có lý do cụ thể

- **Không copy `.ps1`/`.cmd`** từ `skillbase-sample` — máy bạn (macOS) cần bash, không phải PowerShell.
- **Không copy trực tiếp phần COBOL/VB6** (`cobolマイグレーション`, `vb6マイグレーション`, `COBOL_Modernization_Prompt_Kit`) — khác domain hoàn toàn, System_bus không migrate hệ COBOL/VB6. Chỉ tham khảo *ý tưởng* discovery-first (ASSUMPTIONS.md / ISSUES.md ghi lại giả định & vấn đề mở khi làm việc lớn) nếu thấy hữu ích.
- **`.cursor/rules/*.mdc`, `.cursor/commands/*.md`** trong `command_and_rule_cusor` chỉ nên mirror sang System_bus **nếu team cũng dùng Cursor IDE** song song với Claude Code. Nếu chỉ dùng Claude Code thì bỏ qua — 2 hệ thống này không tự động đồng bộ với nhau.
- **`store-create.mdc`** dùng Angular + NgRx (`@zsf/front-lib`) — khác hoàn toàn stack Vue 3 + Pinia của System_bus. `pinia-store.md` đã có sẵn, chỉ nên tham khảo *ý tưởng* tách 4 file (model/service/store/index) nếu muốn thống nhất hóa các store hiện tại, không copy code mẫu.

---

## 7. Checklist hành động

- [ ] Tạo `docs/ledger/` + 1 file ledger mẫu cho feature đang làm dở (mục 2).
- [ ] Viết `.claude/commands/lead-review.md` (mục 3), cập nhật bảng lệnh trong `CLAUDE.md`.
- [ ] Nếu sắp làm hàng loạt trang/API tương tự: viết `/clear-spec`, `/make-testcase`, và `scripts/batch/` (mục 4).
- [ ] Khi các bước trên đã chạy ổn định vài lần thủ công: nâng cấp `claude_hook.py` Stop event để chặn thật (mục 5), test trên nhánh riêng trước.
- [ ] Hỏi lại team: có dùng Cursor không? Nếu có, mirror rule cốt lõi từ `.claude/references/*/rules/*.md` sang `.cursor/rules/*.mdc` (mục 6).
