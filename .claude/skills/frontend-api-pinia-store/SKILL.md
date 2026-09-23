---
name: frontend-api-pinia-store
description: Create or update Pinia setup stores that wrap API service calls for this Vue booking-ticket project. Use when adding store state, getters, actions, loading, and error handling around backend APIs.
---

# API Pinia Store

Use this skill for files under `src/stores/`.

## Workflow

1. Read `.claude/references/frontend/pinia-store.md` for store patterns.
2. Read `.claude/references/frontend/rules/clean-code.md` before refactoring existing store logic.
3. Read `.claude/references/frontend/rules/api-service-rules.md` when the store calls or wraps an API service.
4. Inspect the matching service file before adding actions; do not invent service functions if the request is store-only.
5. Use `defineStore('domain', () => { ... })` setup-store syntax.
6. Organize stores as state refs, computed getters, async actions, then `return {}`.
7. Store actions call service functions; they do not call Axios directly.

## Rules

- Keep store files domain-focused, such as `auth.js`, `booking.js`, or `trip.js`.
- Use safe defaults: arrays as `ref([])`, nullable objects as `ref(null)`, booleans as `ref(false)`.
- Manage loading and error state around async actions when the UI depends on it.
- Rethrow errors when components need to show feedback.
- Use `storeToRefs` in components when destructuring store state.
- Do not create UI, route, or component wiring unless explicitly requested.

## Output Checklist

- State has safe defaults.
- Async actions set and clear loading/error consistently.
- Actions call service functions, not `apiClient`.
- All used state, getters, and actions are returned.
- Existing exports and unrelated store behavior are preserved.
