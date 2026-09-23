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

**Ghi chú sau (2026-09-23):**
- Sau commit này, nhánh `task/0.4-lock-public-endpoints` của `ticket-system` có thêm commit
  `10b0bde` (message = tên nhánh, 48 file, đã push) — không do `plan-commit` tạo. Nó chứa bản
  sớm của 0.5 (RevenueController 9 method, chưa có L4/L12) và work không thuộc 0.4/0.5
  (admin dashboard, Flyway V1, Kong/TLS/k8s/CI, bản viết lại `AuthInterceptor`). **Không merge
  nguyên nhánh 0.4 sau 0.5** — xem kế hoạch xử lý ở mục 0.5.
- **Đính chính:** nhánh 0.4 (kể cả `10b0bde`) **đã được merge vào `develop` qua PR #2**
  (`308e7c9`, 2026-09-22) trước khi làm 0.5; ghi chú "không merge" ở trên dựa trên `develop` cục
  bộ chưa fetch. Chồng lấn với 0.5 đã giải ở merge `6b2d8d5` (xem mục 0.5).
- Dấu tick `lead-review` của 0.4 trong ledger nằm ở commit root của 0.5 (`d63eaef`), không có
  trên nhánh 0.4.

## 0.5 — Chặn tự đăng ký ADMIN (B11) + gắn `@RoleRequired` (B12)

Date: 2026-09-23 · Lead review: round 2, CLEAN · Review doc: `.claude/docs/review/0.5-register-role-required.md`

### Kết quả
- DoD (plan): Register với `role=ADMIN` → tài khoản vẫn là CUSTOMER; CUSTOMER gọi `POST /api/bus` → 403
  → **đạt**. Chứng minh bởi `AuthControllerTest.registerWithAdminRoleInBodyIssuesCustomerToken`
  (201, role lưu là CUSTOMER, JWT access + refresh đều CUSTOMER) và
  `BusControllerAuthTest.rejectsCustomerTokenOnBusCreation` (403) + `allowsAdminTokenOnBusCreation` (200).
  Cả hai chạy qua `AuthInterceptor` thật.
- S1 `AuthService.register` luôn CUSTOMER, constructor injection — done.
- S2 `BusController` `@RoleRequired(ADMIN)` class + 3 method — done.
- S3 `RouteController` class + 2 method — done.
- S4 `TripController` class + 4 method, bỏ field `@Autowired` thừa — done.
- S5 `RevenueController` class + method — done. Commit `62b44cf` có 5 method (nhánh tạo từ `99bab9c`);
  sau merge `origin/develop` (`6b2d8d5`) đủ 9 method, đều `@RoleRequired(ADMIN)`.
- S6 `TicketController` 3 method — done (đã nằm trong commit 0.4 `99bab9c`).
- S7 `AuthServiceTest`, S8 `RoleRequiredCoverageTest` — done.
- S9 verify thủ công — **chưa chạy** (L14): backend đang chạy là code trước 0.5; test in-process thay thế.
- Ngoài scope gốc, theo quyết định của bạn: L4 (`update-password` lấy tài khoản từ JWT) và L12
  (khoá ADMIN cho Salary / BaseSalary / BaseLoyalty / LoyaltyReward / RedisTest).

### Endpoint thay đổi
| Method | Path | Auth | Change |
|---|---|---|---|
| POST | `/api/auth/register` | public | `role` trong body bị bỏ qua, luôn tạo CUSTOMER |
| PUT | `/api/auth/update-password` | mọi role đã đăng nhập | Tài khoản lấy từ JWT (`id`), không từ `email` trong body; body chỉ còn `oldPassword`, `password` (validated); sai mật khẩu cũ → 400 (trước 500); thành công → 200 (trước 201) |
| GET/POST/PUT | `/api/bus`, `/api/bus/{busId}` | ADMIN | Trước: bất kỳ JWT hợp lệ (theo interceptor mới) |
| POST/PUT | `/api/route`, `/api/route/{routeId}` | ADMIN | như trên |
| POST/GET/PUT | `/api/trip`, `/api/trip/scheduled`, `/api/trip/{tripId}`, `/api/trip/{tripId}/revenue` | ADMIN | như trên |
| GET | `/api/revenue/bus`, `/employee`, `/user`, `/bus/{busId}/range`, `/bus/all` | ADMIN | như trên |
| POST/GET | `/api/salary`, `/api/salary/driver` | ADMIN | L12 — trước (trên nhánh này): mọi JWT hợp lệ |
| POST/PUT/GET | `/api/base_salary`, `/api/base_salary/{id}` | ADMIN | L12 |
| POST/PUT | `/api/base_loyalty_point`, `/{id}` | ADMIN | L12 |
| POST/PUT | `/api/loyalty/rewards`, `/{id}` | ADMIN | L12 |
| GET | `/api/test-redis/ping` | ADMIN | L12 |

So với commit `99bab9c`: interceptor cũ trả 403 cho **mọi** user ở endpoint không có `@RoleRequired`, nên
các endpoint trên trước đây không ai gọi được (kể cả ADMIN); interceptor mới (carry từ `10b0bde`)
cho qua mọi JWT hợp lệ khi không có `@RoleRequired`.

### File thay đổi
**ticket-system** (branch at report time: `task/0.5-register-role-required`, từ `develop` = `99bab9c`)
- `manage-revenue-ticket/src/main/java/com/ticket_system/manage_revenue_ticket/service/AuthService.java` — S1, L4
- `manage-revenue-ticket/src/main/java/com/ticket_system/manage_revenue_ticket/controller/AuthController.java` — L4, constructor injection, bỏ `UserService` không dùng
- `manage-revenue-ticket/src/main/java/com/ticket_system/manage_revenue_ticket/Dto/request/UserUpdatePasswordRequestDto.java` — L4
- `manage-revenue-ticket/src/main/java/com/ticket_system/manage_revenue_ticket/controller/BusController.java` — S2
- `manage-revenue-ticket/src/main/java/com/ticket_system/manage_revenue_ticket/controller/RouteController.java` — S3
- `manage-revenue-ticket/src/main/java/com/ticket_system/manage_revenue_ticket/controller/TripController.java` — S4
- `manage-revenue-ticket/src/main/java/com/ticket_system/manage_revenue_ticket/controller/RevenueController.java` — S5
- `manage-revenue-ticket/src/main/java/com/ticket_system/manage_revenue_ticket/controller/SalaryController.java` — L12
- `manage-revenue-ticket/src/main/java/com/ticket_system/manage_revenue_ticket/controller/BaseSalaryController.java` — L12
- `manage-revenue-ticket/src/main/java/com/ticket_system/manage_revenue_ticket/controller/BaseLoyaltyPointsController.java` — L12
- `manage-revenue-ticket/src/main/java/com/ticket_system/manage_revenue_ticket/controller/LoyaltyRewardController.java` — L12
- `manage-revenue-ticket/src/main/java/com/ticket_system/manage_revenue_ticket/controller/RedisTestController.java` — L12
- `manage-revenue-ticket/src/main/java/com/ticket_system/manage_revenue_ticket/interceptor/AuthInterceptor.java` — L11 [mixed — whole change is earlier uncommitted work carried from `10b0bde` (0.4 prerequisite): class-level `@RoleRequired`, no-annotation endpoints need only a valid JWT, constructor injection]
- `common-library/src/main/java/com/ticket_system/common/exception/GlobalExceptionHandler.java` — L11 [mixed — 0.4 prerequisite from `10b0bde`: `@RestControllerAdvice`]
- `manage-revenue-ticket/pom.xml` — L11 [mixed — 0.4 prerequisite: Testcontainers test dependencies + version]
- `manage-revenue-ticket/src/test/java/com/ticket_system/manage_revenue_ticket/service/AuthServiceTest.java` — S7 (new)
- `manage-revenue-ticket/src/test/java/com/ticket_system/manage_revenue_ticket/controller/RoleRequiredCoverageTest.java` — S8, L12 (new)
- `manage-revenue-ticket/src/test/java/com/ticket_system/manage_revenue_ticket/controller/BusControllerAuthTest.java` — L2 (new)
- `manage-revenue-ticket/src/test/java/com/ticket_system/manage_revenue_ticket/controller/AuthControllerTest.java` — L2, L4 (new)
- `manage-revenue-ticket/src/test/java/com/ticket_system/manage_revenue_ticket/controller/SalaryControllerAuthTest.java` — L12 (new)
- `manage-revenue-ticket/src/test/java/com/ticket_system/manage_revenue_ticket/interceptor/AuthInterceptorTest.java` — L11 (new) [mixed — test of the carried `AuthInterceptor` rewrite, earlier work]
- `manage-revenue-ticket/src/test/resources/mockito-extensions/org.mockito.plugins.MockMaker` — L11 (new) [mixed — 0.4 prerequisite]

**Root repo** (branch at report time: `task/0.5-register-role-required`, từ `task/0.4-lock-public-endpoints`)
- `.claude/docs/report/screen-feature-plan.md` — this section
- `.claude/docs/review/0.5-register-role-required.md` — spec review + lead review of 0.5 (new)
- `.claude/ledger/screen-feature-plan.md` — [mixed — only change is your 0.4 `lead-review` tick; 0.5 lines were already committed in `e4033e0`]

**booking_ticket_vue** — no files (0.5 is BE only; FE `updatePassword` payload still accepted — extra `email` is ignored).

### Test
- `mvn -f ticket-system/pom.xml -pl manage-revenue-ticket -am clean test` → **49/49, BUILD SUCCESS** (lead review round 2).
- `mvn -f ticket-system/pom.xml -pl booking_ticket -am test-compile` → OK; `mvn -f ticket-system/pom.xml install -DskipTests` → OK.

### Review
- Lead review 1 (trên bản copy `10b0bde`) → OPEN: chưa có review độc lập (L1), S9 thay thế chưa đủ (L2), 0.5 không có commit riêng (L3), lỗi ownership `update-password` (L4).
- L1: `security-reviewer`, `backend-reviewer`, `test-gap-reviewer` độc lập — S1–S6 đúng scope.
- Fix round 1: nhánh mới từ `develop`; `develop` không compile được test → carry prerequisite (L11); L2, L4 fixed; `security-reviewer` tìm ra L12.
- L12 (quyết định a) fixed; `security-reviewer` xác nhận. Lead review 2 → CLEAN.

### Còn lại
- DEFER: L5 → task 1.1 / 3.2, ghi ở plan B12 (chain test cho từng controller admin) · L6 → B20 / task 4.3 · L7 → B19 · L8 → B19 · L9 → B18 · L10 → B7 · L13 → B20 / task 4.3 (`LoyaltyPointsController`, `createTicketByLoyalty`: role + ownership check).
- NEEDS-USER: L14 — S9 live chưa chạy (restart backend trên nhánh 0.5 rồi chạy, hoặc chấp nhận test in-process).

### Commit
Committed 2026-09-23, local only (not pushed yet — `plan-push`).
1. `booking_ticket_vue` — no files for 0.5: FE tests and commit skipped.
2. `ticket-system` — BE tests `mvn -f ticket-system/pom.xml -pl manage-revenue-ticket,booking_ticket -am test`
   → `common-library` 1/1 + `manage-revenue-ticket` 48/48, BUILD SUCCESS. Branch
   `task/0.5-register-role-required` (from `develop` = `99bab9c`, i.e. stacked on the 0.4 commit),
   commit `62b44cf`, 22 files. Mixed: `AuthInterceptor.java`, `AuthInterceptorTest.java`,
   `GlobalExceptionHandler.java`, `manage-revenue-ticket/pom.xml`, `MockMaker` (0.4 prerequisites
   carried from `10b0bde`).
3. Root repo — branch `task/0.5-register-role-required` (from `task/0.4-lock-public-endpoints`,
   stacked on the 0.4 docs commit `e4033e0`), no tests; hash in chat.
4. **Merge vào develop (2026-09-23):** `origin/develop` đã có nhánh 0.4 qua PR #2 (`308e7c9`, gồm
   `10b0bde`). Merge nó vào `task/0.5-register-role-required` → `6b2d8d5` (conflict: `AuthService`,
   `BusControllerAuthTest`, `RoleRequiredCoverageTest` lấy phía 0.5; `pom.xml` chỉ khác khoảng
   trắng). Test `mvn -f ticket-system/pom.xml -pl manage-revenue-ticket,booking_ticket -am clean test`
   → 1/1 + 61/61, BUILD SUCCESS. `ticket-system` `develop` fast-forward tới `6b2d8d5`, đã push.
   Root `develop` fast-forward tới nhánh 0.5 của root, đã push.
