---
name: spec-review
description: Spec gate for one screen-feature-plan task — re-check the coded screen against design doc + real BE, write the agreed fix scope, then ask the user to tick `spec`. Use when the user asks for a spec review, a spec gate, or to re-check a coded screen's API/feature scope before plan-task starts, or invokes /spec-review.
---

# Skill: Spec Review (the step before the user ticks `spec`)

Also callable as the `/spec-review` command (`.claude/commands/spec-review.md`);
that file is a thin pointer to this skill so metadata (`argument-hint`,
`allowed-tools`) has one place to live. Behavior is identical either way.

Screens are already coded, but their API wiring and features were built from
evidence that may be stale. This refreshes that evidence for **one**
plan task and turns it into a fix scope the user can approve. `plan-task` will
not start a task until its `spec` line is ticked, and it implements exactly
the scope written here.

Flow: spec-review (task ID) → user reads the doc → user ticks `spec` in
`.claude/ledger/screen-feature-plan.md` → `/plan-task <ID>`.

## Request Template

Spec review for:
- Task ID:
- Known broken behaviour (optional, e.g. "list shows mock data", "save returns 404"):

## Claude Instructions

1. **Locate the task.** Read the Task Registry in
   `.claude/skills/plan-task/SKILL.md` and the matching section of
   `.claude/docs/plan/screen-feature-plan.md`. Take the page file, design docs,
   and open decisions from there. Unknown ID → list valid IDs and stop.
   Task with no design doc (4.1, 4.2) → stop and tell the user to run
   `/clear-spec` first.
2. **Screen tasks (1.x–4.x): run the `fullstack-page-api-review` skill** on the
   page (`booking_ticket_vue/src/pages/<area>/<Page>.vue`), including child
   modals/drawers, the store and service it uses, and the matching controllers
   and DTOs. Also read `.claude/references/frontend/api/<slug>/endpoints.md` and
   `.claude/references/backend/api/<slug>/endpoints.md` for each design doc slug.
   Foundation tasks (0.x): no page review — re-read the files the plan cites for
   that row and check whether the problem still exists.
3. **Feature check per screen.** For every capability in the design doc
   (load, filter, paginate, create, update, delete, status change, download),
   record what happens today with evidence (file:line): real API, `MISMATCH`,
   `MISSING_BE`, `MISSING_FE`, `LOCAL_ONLY` (mock/fallback), placeholder handler,
   missing loading/error/empty state. Use the status values from
   `.claude/skills/fullstack-page-api-review/references/review-output-template.md`.
4. **Diff against the plan.** Compare with the task's table in
   `screen-feature-plan.md`: what is already fixed, what is new, what the plan
   got wrong. Do not edit the plan here — list proposed plan edits instead.
5. **Write** `.claude/docs/review/<task-id>-<slug>.md` (overwrite if it exists)
   with these sections, in order:
   1. Summary — one line per capability: status now → target.
   2. FE-BE readiness matrix (from the skill).
   3. Fix scope for `plan-task`, split **BE** (method, path, auth, request,
      response, validation, errors) / **FE** (endpoint constant, service, store,
      page handler, states) / **Tests**. Each item has an ID (`S1`, `S2`, …).
   4. Out of scope — things found but not part of this task, with the task ID
      they belong to.
   5. Proposed plan changes (if any).
   6. Open decisions — only what evidence cannot resolve, as `(TODO/needs confirmation)`.

   Section 7 (`## 7. Lead review`) belongs to `/lead-review`. When overwriting
   an existing doc, copy its section 7 unchanged to the end of the new doc —
   it is the record of past review rounds and fixes.
6. **Stop and hand over.** Report the doc path, the count of items per status,
   and the open decisions as one combined question. End by asking the user to
   read the doc and tick `spec` for this task themselves.

## Boundaries

- Read-only for code: the only file written is the review doc under
  `.claude/docs/review/`.
- Do not tick `spec` (or any ledger line) — the user does.
- Do not invent business rules; unresolved rules go to Open decisions.
- One task ID per run.
- A design doc that disagrees with real BE is not silently "fixed": record the
  difference; if the design doc itself must change, say so and let the user
  update it (or run `/clear-spec`) before ticking `spec`.
