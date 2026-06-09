---
name: prompt-backend-fix-bug
description: Guide Codex to diagnose and fix a backend bug with focused verification.
argument-hint: "<module or service> <bug description or failing command>"
---

# Prompt: Fix Bug

Use this prompt to guide Codex when fixing a backend bug.

## Request Template

Fix this backend bug.

Problem:
- What fails:
- Expected behavior:
- Actual behavior:
- Error message or stack trace:
- Reproduction command or API call:

Scope:
- Suspected module:
- Suspected class or endpoint:
- Infrastructure required:

Verification:
- Command that should pass:
- Test that should be added or updated:

## Codex Instructions

- Reproduce or inspect the failure before editing when possible.
- If Maven startup fails, rerun with `-e`.
- Fix the root cause with the smallest safe change.
- Add a regression test for the failing behavior when feasible.
- Report what was verified and any remaining risk.
