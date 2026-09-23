---
name: frontend-wire-api-to-event
description: Wire an API, store action, or composable method into a Vue component event handler. Use for button clicks, form submits, and existing empty or incomplete handlers.
---

# Wire API to Event

Use this skill when connecting a user interaction to existing data behavior.

## Workflow

1. Read the full target component before editing.
2. Identify the triggering template event and handler name.
3. Prefer the highest-level abstraction already present: store action, then composable method, then service call.
4. Read `.claude/references/frontend/rules/api-service-rules.md` and `.claude/references/frontend/pinia-store.md` only if service/store contracts are unclear.
5. Make the handler `async` when awaiting work.
6. Reuse existing `loading`, `error`, result refs, and toast composables instead of creating duplicates.

## Rules

- Do not import a service directly if the component already uses a store or composable for the same domain.
- Infer parameters from existing refs, forms, filters, route params, or selected IDs.
- Wrap async calls in `try/catch/finally` when UI state must be updated.
- Refresh data after successful mutations when the page already has a fetch handler.
- Do not invent template fields or payload properties absent from the component or API docs.
