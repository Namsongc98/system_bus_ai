---
name: lead-review-fix
description: Fix the open FIX findings that /lead-review recorded for one screen-feature-plan task, re-verify, re-review, then hand back to /lead-review. Use when a lead review reported remaining errors, when /plan-task finds open FIX findings in the "Lead review" section of .claude/docs/review/<ID>-<slug>.md, or when the user invokes /lead-review-fix.
argument-hint: "<task ID from .claude/docs/plan/screen-feature-plan.md, e.g. 0.5, 1.1>"
allowed-tools: Read, Grep, Glob, Bash, Write, Edit
---

# Skill: Lead Review Fix (close the findings lead-review left open)

Also callable as the `/lead-review-fix` command
(`.claude/commands/lead-review-fix.md`). `/plan-task <ID>` routes here
automatically when the task already has open `FIX` findings, so the normal
loop is just two commands:

```
/lead-review <ID>  --OPEN-->  /plan-task <ID>  (fix mode = this skill)
      ^                              |
      +------------------------------+     at most 3 rounds, then ask the user
/lead-review <ID>  --CLEAN-->  user ticks `lead-review`
```

Input: the `## 7. Lead review` section of the task's spec-review doc
`.claude/docs/review/<ID>-<slug>.md`, written by `/lead-review` (one document
per task: spec-review sections 1–6, lead review in section 7).
Each finding row has an ID (`L1`, `L2`, …), severity, class and status:

| Class | Meaning | What this skill does |
|---|---|---|
| `FIX` | Fixable now, inside the task's scope (test broken by the change, high/medium review finding, a required check that can run but has not) | Fix it |
| `DEFER` | Real, but outside the approved scope | Record it as a plan blocker, do not fix |
| `NEEDS-USER` | Needs a business decision, credentials, or infrastructure | Leave it, list it |

## Request Template

Lead review fix for:
- Task ID:

## Claude Instructions

### 1. Gate (stop before editing anything)
1. The task's `spec` line in `.claude/ledger/screen-feature-plan.md` must be
   ticked. If not → stop, point to `/spec-review <ID>`.
2. The task's review doc `.claude/docs/review/<ID>-<slug>.md` must have a
   `## 7. Lead review` section with at least one `FIX` row with status `open`.
   Section missing → stop and tell the user to run `/lead-review <ID>`. No
   `FIX` open → stop: nothing to fix, run `/lead-review <ID>` again for sign-off.
3. Read the round number in that section. Round 3 with open `FIX` rows means
   the loop limit is reached → stop and ask the user how to proceed; do not
   start a fourth fix round on your own.

### 2. Re-verify each open `FIX`
The doc captured a point in time. For every open `FIX` row, re-read the cited
file/line or re-run the cited command. Already gone → set status
`fixed (already)` and say so in the report. Never re-fix something that no
longer exists.

### 3. Fix only the open `FIX` rows
- Follow `plan-task` sections **3–6** (`.claude/skills/plan-task/SKILL.md`):
  backend order and rules, backend tests in the same run, frontend wiring
  rules, verify. Do not restate or relax those rules here.
- One finding at a time, smallest change that closes it. Add or adjust a test
  that fails without the fix whenever the finding is about behaviour.
- A finding that says "no independent review has run" is fixed by running
  `/parallel-review` on the task's changed files and handling what it reports:
  its new high/medium findings in scope are fixed in this same run; anything
  else is classified as below.
- Do not widen scope. A new gap found while fixing is not silently fixed:
  in scope and small → add it as a new `FIX` row and fix it; otherwise treat it
  as `DEFER` or `NEEDS-USER`.

### 4. Handle `DEFER` and `NEEDS-USER`
- `DEFER`: if it has no blocker yet, append it to the blocker table in
  `.claude/docs/plan/screen-feature-plan.md` as `B<next>` (next unused number;
  check the table first), then set the row's status to `deferred (B<n>)`.
- `NEEDS-USER`: do not touch. Keep status `needs-user` and repeat it in the
  report as a question.

### 5. Verify and review
- Run the module checks for every module you touched and report pass/fail
  counts, not full logs:
  `mvn -f ticket-system/pom.xml -pl <module> -am test` (reactor form, so
  `common-library` is built from source, not taken from a possibly stale jar in
  `~/.m2` — see plan-task §6),
  `cd booking_ticket_vue && npm run test:unit -- --run && npm run build`.
  Pre-existing failures unrelated to the change: name them, show their root
  cause, do not claim they passed.
- Review the diff of this round with `backend-code-review` /
  `frontend-code-review` (screen tasks 1.x–4.x: `/parallel-review`). Fix
  high/medium findings in scope before reporting.

### 6. Update tracking
- In the `## 7. Lead review` section of `<ID>-<slug>.md`, update the `Status`
  column, add rows for new findings from step 3 (next `L<n>`), add this round's
  commands to `Commands run`, and append one `Fix round <n>` line to
  `Round history`. Do not change the verdict or round number — the next
  `/lead-review` recomputes them. Do not touch sections 1–6.
- Ledger: `implement` / `test` / `review` stay ticked only if this round's
  verify and review passed; if a check that used to pass now fails, untick
  that line and say why. **Never tick `spec` or `lead-review`.**

### 7. Report (in this order)
1. Each finding: `L<n>` → fixed / fixed (already) / deferred (B<n>) / needs-user,
   with files changed.
2. Commands run and their results.
3. Review findings of this round and how they were handled.
4. Open questions (`NEEDS-USER`).
5. End with: next step is `/lead-review <ID>`.

## Boundaries
- One task ID per run. Stop after the report; do not run `/lead-review` yourself.
- Only fix rows classified `FIX`; do not reclassify a row just to make the loop end.
- Do not edit `Infrastructure/`, `.env` files, or runtime data.
- Do not tick `spec` or `lead-review`.
