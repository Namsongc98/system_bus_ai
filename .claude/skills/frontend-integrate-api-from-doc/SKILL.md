---
name: frontend-integrate-api-from-doc
description: Convert backend API documentation or endpoint specs into Vue service-layer functions, selecting JSON or download patterns as needed.
---

# Integrate API From Doc

Use this skill when the user provides API documentation, endpoint specs, request/response schemas, or asks Claude to generate services from `.claude/references/frontend/api-document.md`.

## Workflow

1. Read `.claude/references/frontend/rules/api-service-rules.md` for mandatory service-layer rules.
2. Read `.claude/references/frontend/api-document.md` or the user-provided API documentation.
3. Determine the endpoint type:
   - JSON response: follow `.claude/references/frontend/api-json-service.md`.
   - Blob/download response: follow `.claude/references/frontend/api-download-service.md`.
   - Error behavior unclear: check `.claude/references/frontend/api-error-handling.md`.
4. Map each endpoint to the correct service module under `src/services/`.
5. Reuse endpoint constants from the current endpoint module where available.
6. Add named exports without replacing unrelated service functions.

## Output Rules

- Generate only the service functions needed by the request.
- Keep schema comments minimal unless they clarify ambiguous request data.
- Do not create stores, event handlers, or UI wiring unless the user also asks for them.
