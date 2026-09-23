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
3. Each related command ticks its own line when its step is done
   (`backend-implement`, `frontend-*`, `backend-review`...).
4. **Only the user ticks the `lead-review` line** — this is the final DoD
   gate, run through `/lead-review` (see `.claude/commands/lead-review.md`).
5. The `Stop` hook (`.claude/hooks/codex_hook.py`) automatically warns
   (without blocking) if any ledger still has an unticked line when Claude is
   about to end the turn — a reminder only, it never blocks the session.

## Conventions

- `README.md` and `TEMPLATE.md` are excluded from the hook's scan so they are
  never mistaken for an in-progress ledger.
- Delete or archive a ledger once its feature has merged, so stale warnings
  do not linger.
