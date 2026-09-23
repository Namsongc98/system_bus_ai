---
description: Consolidate automated review findings and ledger status, then require explicit human sign-off before a work-unit counts as done.
argument-hint: "<work-unit name, branch, PR, or ledger file>"
allowed-tools: Read, Grep, Glob
---

# Prompt: Lead Review (human sign-off gate)

Use this after `parallel-review` (or `backend-review` / `frontend-code-review`)
has already run and findings are addressed. This command does **not** replace
automated review — it consolidates it and asks the user to confirm.

## Request Template

Lead review for:
- Work-unit / branch / PR:
- Ledger file (if any): `.claude/ledger/<feature-slug>.md`

## Claude Instructions

1. Re-read the latest findings from `backend-reviewer` / `frontend-reviewer` /
   `security-reviewer` / `test-gap-reviewer` for this change (rerun
   `parallel-review` if no recent findings exist).
2. If a ledger file is referenced, read it and report the current checklist
   state for this work-unit (`spec / implement / test / review / lead-review`).
3. Report, in order:
   - Outstanding findings by severity (none unaddressed should remain).
   - Build/test commands run and their result.
   - Any `(TODO/needs confirmation)` or open contract decisions left.
4. Do **not** edit the ledger file yourself and do not claim the work-unit is
   done. End with an explicit request for the user to confirm and tick the
   `lead-review` line themselves.

## Boundaries

- Read-only: no code edits, no ledger edits.
- If no automated review has run yet, say so and stop — do not review from
  scratch inside this command.
