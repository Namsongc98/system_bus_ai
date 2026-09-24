# Ledger — pipeline progress tracking per work-unit

## When to use

Use a ledger when a body of work has **many work-units repeating the same
pipeline** (several admin pages, several APIs...) and you need to know exactly
which stage each one is at — to avoid mis-reporting progress or skipping the
review step.

Small work — a one- or two-file fix, a single bug — does **not** need a
ledger; use the slash commands directly.

## How to use

1. Copy `TEMPLATE.md` to `<feature-slug>.md` (e.g. `trip-management.md`) in
   this same directory.
2. Each work-unit is one `##` heading with a fixed 5-line checklist: `spec /
   implement / test / review / lead-review`.
3. `spec` — for `screen-feature-plan.md`, run `/spec-review <ID>` first; it
   writes `.claude/docs/review/<ID>-<slug>.md` (current FE-BE state + fix
   scope). **The user ticks `spec`** after reading it; `plan-task` refuses to
   start until then. For other ledgers, `spec` follows `/clear-spec`.
4. Each related command ticks its own line when its step is done
   (`backend-implement`, `frontend-*`, `backend-review`...).
5. **Only the user ticks the `spec` and `lead-review` lines** — `lead-review` is the final DoD
   gate, run through `/lead-review` (see `.claude/commands/lead-review.md`). It records
   its findings in section `7. Lead review` of the task's own review doc
   (`.claude/docs/review/<ID>-<slug>.md`, one document per task) with a verdict: `OPEN` means fixable
   findings remain → run `/plan-task <ID>` again (fix mode, skill `lead-review-fix`),
   then `/lead-review <ID>`, at most 3 rounds; `CLEAN` runs `plan-report`
   (task report `.claude/docs/report/<ID>-<slug>.md` + index row in
   `.claude/docs/report/<plan-file-name>.md`) and stops so the user can inspect the
   changed files; the user then runs `/git-commit <ID>` (three local commits on
   `task/<ID>-<slug>`: `booking_ticket_vue` after FE unit tests, `ticket-system`
   after BE unit tests, then the root docs repo without tests, then pushes those branches to
   origin, never force), after which the user may tick.
6. The `Stop` hook (`.claude/hooks/claude_hook.py`) automatically warns
   (without blocking) if any ledger still has an unticked line when Claude is
   about to end the turn — a reminder only, it never blocks the session.

## Conventions

- `README.md` and `TEMPLATE.md` are excluded from the hook's scan so they are
  never mistaken for an in-progress ledger.
- Delete or archive a ledger once its feature has merged, so stale warnings
  do not linger.
