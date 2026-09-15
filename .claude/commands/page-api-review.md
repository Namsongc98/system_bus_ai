---
description: "Review a Vue page and its child flows for API readiness, FE-BE contract match, and backend preparation plan."
argument-hint: "<target Vue page path>"
allowed-tools: Read, Grep, Glob
---

# Full-stack Page API Review

Use `$fullstack-page-api-review` for the target Vue page.

Review the page and all child modal/drawer flows. Identify every API capability
the page needs, trace FE endpoint constants/services/stores, inspect matching
Spring controllers/DTOs/services/repositories, and produce:

1. Page capability map.
2. FE-BE readiness matrix.
3. Missing or mismatched API contracts.
4. Prioritized backend preparation plan.
5. FE connection sequence and acceptance tests.

Do not modify FE or BE code unless explicitly requested after the contract
review.
