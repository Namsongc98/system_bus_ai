---
name: frontend-fix-error
description: Debug and fix Vue, Pinia, Axios, router, runtime, or build errors in this project. Use when the user provides an error message, stack trace, failing behavior, or broken code.
---

# Fix Error

Use this skill for targeted debugging and minimal fixes.

## Workflow

1. Read the error message, stack trace, and referenced files.
2. Classify the layer: component, composable, store, service, Axios, router, build, or runtime.
3. Inspect nearby project patterns before changing code.
4. Identify the root cause and apply the smallest fix that preserves architecture.
5. Read `.claude/references/frontend/services/api-error-handling.md` when the error involves Axios, API responses, auth redirects, or interceptor behavior.
6. Add or update focused tests when the risk justifies it.
7. Re-run the failing command, build, or targeted test when practical.

## Common Checks

- Missing or wrong imports, especially relative paths where `@/` should be used.
- Ref misuse: missing `.value`, unsafe `undefined` access, or lost reactivity.
- Missing `await`, swallowed errors, or incomplete `try/catch/finally`.
- Direct Axios calls outside services.
- Wrong endpoint constants or response unwrapping assumptions.
- Router names, guards, or auth state mismatches.

## Scope Rules

- Fix the reported failure first; avoid broad refactors during error repair.
- Preserve unrelated user changes and existing behavior.
- Prefer one focused patch over multiple style-only changes.

## Output Format

- Root cause: concrete reason for the failure.
- Fix: files changed and behavior restored.
- Verification: command run, result, or why it was skipped.
