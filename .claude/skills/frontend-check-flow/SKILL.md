---
name: frontend-check-flow
description: Trace and debug a complete Vue feature flow from UI event to store, service, Axios, and backend response. Use when a feature is broken but the failing layer is unclear.
---

# Check Flow

Use this skill to diagnose broken application behavior across layers.

## Workflow

1. Identify the user action or lifecycle entrypoint.
2. Trace the component handler and template binding.
3. Trace the Pinia store action or composable method.
4. Trace the service function and Axios client usage.
5. Read `.claude/references/frontend/rules/api-service-rules.md` and `.claude/references/frontend/services/api-error-handling.md` when API behavior is involved.
6. Compare request and response handling against `.claude/references/frontend/api/_conventions.md` plus the screen's `.claude/references/frontend/api/<slug>/endpoints.md` when needed.
7. Report the failing layer, root cause, and minimal fix before or while applying changes.

## Checklist

- Handler exists and is bound correctly.
- Async work is awaited.
- Store state is kept reactive with `storeToRefs` when destructured.
- Service uses the correct HTTP method, params/body shape, and endpoint.
- Errors are not swallowed before the UI can respond.
- Loading, empty, success, and failure states render correctly.

## Report Format

- Entry point: user action, lifecycle hook, or route.
- Failing layer: component, store, service, Axios, router, or backend contract.
- Root cause: concrete mismatch or broken assumption.
- Fix: smallest code change that restores the flow.
- Verification: command run or reason it was not run.
