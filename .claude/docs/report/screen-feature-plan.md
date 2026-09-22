# Report — Kế hoạch xây dựng tính năng theo màn hình (FE ↔ BE)

Plan: `.claude/docs/plan/screen-feature-plan.md` · Ledger: `.claude/ledger/screen-feature-plan.md`.
Mỗi task CLEAN ở `/lead-review` có 1 mục bên dưới (viết bởi skill `plan-report`).

## 0.4 — Khoá endpoint public (B8)

Date: 2026-09-22 · Lead review: round 2, CLEAN · Review doc: `.claude/docs/review/0.4-lock-public-endpoints.md`

### Kết quả
- DoD (plan): `/api/ticket/summary/excel`: không token → 401 do Spring Security trả; token
  CUSTOMER/DRIVER/COLLECTOR → 403; token ADMIN → 200 → **đạt**, chứng minh bởi
  `TicketExcelSecurityChainTest` (7 ca, chạy chuỗi Spring Security thật + `AuthInterceptor`;
  hoàn tác riêng S1, S2 hoặc S3 đều làm test đỏ).
- S1 `@RoleRequired(UserRole.ADMIN)` trên `exportTicketSummaryToExcel` — done.
- S2 bỏ `/api/ticket/summary/excel` khỏi `permitAll` của `SecurityConfig` — done.
- S3 bỏ bypass tương ứng trong `JwtAuthFilter` — done.
- S4 `TicketControllerTest` — done (thêm ca lỗi 500 ở fix round 1).
- S5 curl thủ công — không chạy; bạn chấp nhận test tự động thay thế (L7).

### Endpoint thay đổi
| Method | Path | Auth | Change |
|---|---|---|---|
| GET | `/api/ticket/summary/excel` | ADMIN | Trước: mọi role đã đăng nhập tải được (Spring Security `permitAll` + filter bypass; chỉ interceptor đòi JWT). Sau: ADMIN ở cả 2 lớp; body 401 giờ là của `CustomAuthEntryPoint` như các endpoint khác |

### File thay đổi
**ticket-system** (branch at report time: `main`)
- `common-library/src/main/java/com/ticket_system/common/security/SecurityConfig.java` — S2 [mixed — also contains earlier uncommitted rewrite of the `permitAll` rules (HEAD had `"/**".permitAll()`)]
- `common-library/src/main/java/com/ticket_system/common/filter/JwtAuthFilter.java` — S3, L9 constructor injection [mixed — also contains earlier uncommitted work: role taken from JWT instead of hardcoded ADMIN, `System.out` and `AccessDeniedException` catch removed]
- `manage-revenue-ticket/src/main/java/com/ticket_system/manage_revenue_ticket/controller/TicketController.java` — S1, L3 SLF4J, constructor injection [mixed — also contains task 0.5: `@RoleRequired(ADMIN)` on `addTicket`, `updateTicket`, `getTicketSummaryByBusAndTime`]
- `manage-revenue-ticket/src/test/java/com/ticket_system/manage_revenue_ticket/ManageRevenueTicketApplicationTests.java` — L6 Testcontainers `contextLoads`
- `manage-revenue-ticket/src/test/java/com/ticket_system/manage_revenue_ticket/controller/TicketControllerTest.java` — S4 (new)
- `manage-revenue-ticket/src/test/java/com/ticket_system/manage_revenue_ticket/controller/TicketExcelSecurityChainTest.java` — L2 (new)
- `common-library/src/test/java/com/ticket_system/common/filter/JwtAuthFilterTest.java` — L9 constructor change [mixed — the file itself is earlier uncommitted work (test for the JWT-role fix)]

**Not self-contained:** a commit of only these files does not build on its own. It relies on
uncommitted work outside 0.4: `manage-revenue-ticket/pom.xml` (Testcontainers dependencies — HEAD
has none), `AuthInterceptor.java`, `RoleRequired.java`, `GlobalExceptionHandler.java`, the Flyway
setup from task 0.3 (`db/migration/V1__baseline.sql`, `application.properties`) and
`src/test/resources/mockito-extensions/`. The 48/48 test result is for the whole working tree.

**Root repo** (branch at report time: `develop`)
- `.claude/docs/report/screen-feature-plan.md` — this report (new)
- `.claude/docs/review/0.4-lock-public-endpoints.md` — spec review + lead review of 0.4 (new)
- `.claude/docs/plan/screen-feature-plan.md` — B8 wording, 0.4 DoD, blockers B17–B19 [mixed — whole file never committed: the entire plan, incl. B16 and other tasks]
- `.claude/ledger/screen-feature-plan.md` — 0.4 checklist [mixed — whole file never committed: all tasks' lines]

**booking_ticket_vue** — no files (0.4 is BE only).

### Test
- `mvn -f ticket-system/pom.xml -pl manage-revenue-ticket,booking_ticket -am test` → 48/48, BUILD SUCCESS (lead review round 2; `booking_ticket` has no tests).

### Review
- Implementation: self-applied `backend-code-review`.
- Lead review 1 → OPEN: no independent review (L1), no status-code test (L2), stdout logging (L3).
- Fix round 1: independent `security-reviewer` (lockdown sound), `backend-reviewer`, `test-gap-reviewer`; L1–L3 and L9 fixed; found and fixed a stale installed `common-library` jar (L10); `contextLoads` moved to Testcontainers (L6); verify command switched to the reactor form.
- Lead review 2 → CLEAN.

### Còn lại
- DEFER: L4 → B17 (CORS) · L5 → task 2.3 (`/confirm`, `/email` public) · L11 → B18 (error bodies / info leak) · L12 → B19 (JWT hygiene) · L13 → task 3.2 (`fromDate ≤ toDate`) · L14 → task 2.3 (log forging).
- NEEDS-USER: L15 — 0.4 not committed; handled by `plan-commit` below.

### Commit
Committed 2026-09-22, local only (not pushed).
1. `booking_ticket_vue` — no files for 0.4: FE tests and commit skipped.
2. `ticket-system` — BE tests `mvn -f ticket-system/pom.xml -pl manage-revenue-ticket,booking_ticket -am test`
   → 48/48 + `common-library` 1/1, BUILD SUCCESS. Branch `task/0.4-lock-public-endpoints` (from
   `main`), commit `99bab9c`, 7 files. Mixed: `SecurityConfig.java`, `JwtAuthFilter.java`,
   `TicketController.java` (includes 0.5), `JwtAuthFilterTest.java`. Not self-contained (see above).
3. Root repo — branch `task/0.4-lock-public-endpoints` (from `develop`), no tests; hash in chat.

First run was blocked at the gate by pre-existing staged entries in `ticket-system`
(`.env.example` deletion, `booking_ticket/.gitignore`); both were unstaged, files unchanged.
