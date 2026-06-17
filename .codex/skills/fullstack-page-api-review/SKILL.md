---
name: fullstack-page-api-review
description: Review a Vue page and its child flows to identify required APIs, trace existing frontend endpoint/service/store usage, compare it with Spring Boot controllers and DTOs, and produce an FE-BE readiness matrix plus a prioritized backend API preparation plan. Use before connecting a page to real APIs, during page review, or when FE and BE endpoint contracts may be incomplete or mismatched.
---

# Full-stack Page API Review

Use this skill for evidence-based API planning. Do not infer backend support from
frontend constants or mock data.

## Workflow

1. Read the root, frontend, and backend `AGENTS.md` files.
2. Confirm the target page, route/role, and review mode:
   - `review-only`: analyze and produce a decision-complete plan.
   - `review-and-implement`: analyze first, then implement only the approved or
     explicitly requested API scope.
3. Identify the target page and every user capability:
   initial load, filters, pagination, detail, create, update, delete, status
   transitions, downloads, and dependent option lists.
4. Follow imported child components, composables, stores, and services. Include
   modal and drawer flows even when they are not visible initially.
5. Inventory frontend evidence:
   endpoint constants, HTTP client/base URL, service methods, store actions,
   request payloads, response normalizers, fallback data, and placeholders.
6. Inventory backend evidence:
   controller mapping, HTTP method, request parameters/body, DTO validation,
   response shape, pagination, authorization, service/repository support, and
   tests.
7. Run
   `python3 scripts/inventory_api_surface.py --page booking_ticket_vue/src/pages/<page>.vue`
   from the skill directory, or pass the full script path from repository root.
   Verify relevant results by reading source. Script output is discovery, not
   proof of contract compatibility.
8. Build the readiness matrix using the statuses in
   `references/review-output-template.md`.
9. For every non-`READY` row, choose one disposition:
   - `KEEP_BE`: backend contract is suitable; add or fix FE wiring only.
   - `EXTEND_BE_COMPATIBLY`: preserve the current contract while adding optional
     fields, filters, or a dedicated response DTO.
   - `CHANGE_BE_CONTRACT`: correct an unsuitable contract and document affected
     callers plus migration steps.
   - `CREATE_BE_API`: add a new endpoint because no existing responsibility
     matches.
   - `DEFER`: explicitly exclude a nonessential capability and state the UI
     behavior while deferred.
10. Specify missing or changed backend APIs before proposing FE integration.
    Each API must include method/path, purpose, request, response,
    pagination/filter semantics, authorization, validation, failure cases, and
    compatibility impact.
11. Produce a file-level implementation plan covering controller, DTO, service,
    repository/query, security, migration, tests, FE service/store/page wiring,
    and API documentation where applicable.
12. Order implementation by dependency: lookup/read APIs, primary mutations,
    detail/update/status APIs, then secondary exports or analytics.
13. In `review-and-implement` mode, stop after the review if unresolved contract
    decisions could cause a breaking or destructive change. Otherwise implement
    the scoped plan using the matching backend/frontend skills and verify it.

## API Change Decision Rules

- Prefer `KEEP_BE` when the mismatch is only missing FE wiring or normalization.
- Prefer `EXTEND_BE_COMPATIBLY` for additive optional filters or response fields.
- Use `CHANGE_BE_CONTRACT` only when the existing method, path, ownership, data
  shape, security, or semantics are incorrect. List every known caller first.
- Use `CREATE_BE_API` when combining the capability with an existing endpoint
  would mix authorization, pagination, mutation, or bounded-context ownership.
- Do not expose JPA entities merely to avoid defining a page-specific response
  DTO.
- A route is not `READY` until required fields, auth, validation, error behavior,
  and pagination semantics are usable by the page.
- Database, Kafka, Redis, or cross-service changes must be called out as
  separate implementation and rollout risks.

## Required Inputs

- Target Vue page path. A route name or screenshot is insufficient unless it can
  be resolved to source.
- Intended user role when the page is role-sensitive.
- Review mode. Default to `review-only`.

Optional inputs:

- Product acceptance notes or screenshot.
- Known backend module or service owner.
- Whether backward compatibility is mandatory.
- Whether implementation should follow immediately after review.

## Evidence Rules

- `API_ENDPOINTS` proves only FE intent.
- A service method proves only an FE call path.
- A controller annotation proves route existence, not response suitability.
- Confirm the effective URL after combining Axios `baseURL` and endpoint path.
- Treat singular/plural differences, missing path segments, and different HTTP
  methods as `MISMATCH`.
- Treat entity responses, undocumented maps, absent DTO validation, or unknown
  auth as `UNKNOWN_CONTRACT` until verified.
- Mark fallback/sample data and placeholder store actions explicitly.
- Use file and line references for all important findings.

## Output

Return these sections in order:

1. Review scope and assumptions.
2. Page capability map.
3. FE API usage.
4. BE API inventory relevant to the page.
5. FE-BE readiness matrix.
6. API decisions and contracts for every non-`READY` row.
7. Backend implementation plan, ordered P0/P1/P2 and grouped by dependency.
8. FE connection sequence.
9. Test and acceptance checklist.
10. Open contract decisions only when evidence cannot resolve them.

Use `references/review-output-template.md` for the exact fields.

## Boundaries

- Default to review and planning; do not implement endpoints unless the user
  requests `review-and-implement` or separately approves implementation.
- Do not change FE endpoint constants to hide a missing BE contract.
- Do not recommend one oversized endpoint when separate capabilities have
  different authorization, pagination, or mutation semantics.
- Reuse `backend-implement-api`, `backend-database-change`,
  `backend-write-test`, `frontend-integrate-api-from-doc`,
  `frontend-api-pinia-store`, and `frontend-wire-api-to-event` only after this
  review has produced an agreed contract.
