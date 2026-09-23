# Full-stack Page API Review

Use `$fullstack-page-api-review` for:

- Target page: `<path to .vue page>`
- Role/route: `<role and route if known>`
- Mode: `review-only` by default, or `review-and-implement`
- Compatibility: `<backward-compatible required | breaking change allowed>`

Review the page and all imported child, modal, and drawer flows. Identify every
API capability, trace FE endpoint constants/services/stores, inspect matching
Spring controllers/DTOs/services/repositories/security/tests, then produce:

1. Capability map and FE/BE evidence with file/line references.
2. FE-BE readiness matrix.
3. A disposition for every gap: keep BE, extend compatibly, change contract,
   create API, or defer.
4. Decision-complete API contracts for missing or mismatched capabilities.
5. A P0/P1/P2 file-level implementation plan and FE connection sequence.
6. Test, migration, compatibility, and acceptance checks.

In `review-only`, do not modify FE or BE code. In `review-and-implement`, finish
the review first and implement only the resolved scope.
