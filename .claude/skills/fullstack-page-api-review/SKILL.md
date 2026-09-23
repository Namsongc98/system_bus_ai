---
name: fullstack-page-api-review
description: Review a Vue page and its child flows to identify required APIs, trace existing frontend endpoint/service/store usage, compare it with Spring Boot controllers and DTOs, and produce an FE-BE readiness matrix plus a prioritized backend API preparation plan. Use before connecting a page to real APIs, during page review, or when FE and BE endpoint contracts may be incomplete or mismatched.
---

# Full-stack Page API Review

Use this skill for evidence-based API planning. Do not infer backend support from
frontend constants or mock data.

## Workflow

1. Read the root, frontend, and backend `AGENTS.md` files.
2. Identify the target page and every user capability:
   initial load, filters, pagination, detail, create, update, delete, status
   transitions, downloads, and dependent option lists.
3. Follow imported child components, composables, stores, and services. Include
   modal and drawer flows even when they are not visible initially.
4. Inventory frontend evidence:
   endpoint constants, HTTP client/base URL, service methods, store actions,
   request payloads, response normalizers, fallback data, and placeholders.
5. Inventory backend evidence:
   controller mapping, HTTP method, request parameters/body, DTO validation,
   response shape, pagination, authorization, service/repository support, and
   tests.
6. Run
   `python3 scripts/inventory_api_surface.py --page booking_ticket_vue/src/pages/<page>.vue`
   from the skill directory, or pass the full script path from repository root.
   Verify relevant results by reading source. Script output is discovery, not
   proof of contract compatibility.
7. Build the readiness matrix using the statuses in
   `references/review-output-template.md`.
8. Specify missing backend APIs before proposing FE integration. Each proposed
   API must include method/path, purpose, request, response, pagination/filter
   semantics, authorization, validation, and failure cases.
9. Order implementation by dependency: lookup/read APIs, primary mutations,
   detail/update/status APIs, then secondary exports or analytics.

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

1. Page capability map.
2. FE API usage.
3. BE API inventory relevant to the page.
4. FE-BE readiness matrix.
5. Backend APIs to prepare, ordered P0/P1/P2.
6. Recommended connection sequence.
7. Test and acceptance checklist.
8. Open contract decisions only when evidence cannot resolve them.

Use `references/review-output-template.md` for the exact matrix fields.

## Boundaries

- Default to review and planning; do not implement endpoints unless requested.
- Do not change FE endpoint constants to hide a missing BE contract.
- Do not recommend one oversized endpoint when separate capabilities have
  different authorization, pagination, or mutation semantics.
- Reuse `backend-implement-api` and `frontend-integrate-api-from-doc` only after
  this review has produced an agreed contract.
