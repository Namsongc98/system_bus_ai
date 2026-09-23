---
name: frontend-integrate-api
description: Add or update normal JSON Vue service-layer functions for backend API endpoints. Use for GET, POST, PUT, PATCH, and DELETE endpoints that return JSON data.
---

# Integrate API

Use this skill to create or update normal JSON API service functions under `src/services/`.

## Workflow

1. Read `.claude/references/frontend/rules/api-service-rules.md` for mandatory service-layer rules.
2. Read `.claude/references/frontend/services/api-json-service.md` for normal JSON endpoint examples.
3. Read `.claude/references/frontend/api/_conventions.md` plus the screen's `.claude/references/frontend/api/<slug>/endpoints.md` only when endpoint details must come from the project API docs.
4. Identify the target service file, such as `src/services/ticketService.js`.
5. Preserve existing exports and append new functions; do not overwrite unrelated service functions.
6. Use the shared Axios client from `src/services/axios.js`.
7. Use endpoint constants from the current endpoint module where available.

## Service Rules

- Services are stateless and contain no UI logic.
- JSON requests return the API response data expected by existing callers.
- Let the shared Axios interceptor and caller layer handle normal API errors.
- Do not import stores, composables, router, or components into services.
