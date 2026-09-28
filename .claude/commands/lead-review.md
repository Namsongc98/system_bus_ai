---
description: Consolidate automated review findings and ledger status into the "Lead review" section of the task's review doc, with a verdict; OPEN sends the task back to /plan-task, CLEAN writes the task report, shows the changed files and stops (the user runs /git-commit).
argument-hint: "<work-unit name, branch, PR, or ledger file>"
allowed-tools: Read, Grep, Glob, Bash, Write, Edit, Skill
---

# Prompt: Lead Review (human sign-off gate)

Use this after `parallel-review` (or `backend-review` / `frontend-code-review`)
has already run. This command does **not** replace automated review — it
consolidates it, records what is still wrong, and either sends the work back
for fixing or asks the user to confirm.

Loop for screen-feature-plan tasks (the user runs each command):

```
/lead-review <ID>  --OPEN-->  /plan-task <ID>  (fix mode: skill lead-review-fix)
      ^                              |
      +------------------------------+     at most 3 rounds, then ask the user
/lead-review <ID>  --CLEAN-->  plan-report --> STOP (user reads the changed-file list)
/git-commit <ID>  (user runs it: commits FE → BE → root, then pushes) --> user ticks `lead-review`
```

## Request Template

Lead review for:
- Work-unit / branch / PR:
- Ledger file (if any): `.claude/ledger/<feature-slug>.md`

## Claude Instructions

1. Re-read the latest findings from `backend-reviewer` / `frontend-reviewer` /
   `security-reviewer` / `test-gap-reviewer` for this change (rerun
   `parallel-review` if no recent findings exist). If only a self-applied
   checklist (`backend-code-review` / `frontend-code-review`) has run on a
   security- or auth-related change, record "no independent review" as a `FIX`
   finding.
2. If a ledger file is referenced, read it and report the current checklist
   state for this work-unit (`spec / implement / test / review / lead-review`).
3. Re-run the build/test commands for the touched modules and use today's
   result, not a remembered one. Backend: `mvn -f ticket-system/pom.xml -pl
   <module> -am test` (reactor form; a module-only build uses the installed
   `common-library` jar, which may be stale).
4. Classify every remaining finding:
   - `FIX` — fixable now inside the task's scope: a test or build broken by the
     change, a high/medium review finding, a required check that can run but
     has not. **Only `FIX` rows block sign-off.**
   - `DEFER` — real but outside the approved scope (belongs to a plan blocker
     `B<n>` or another task).
   - `NEEDS-USER` — needs a business decision, credentials, or infrastructure
     (for example a test that fails because the local DB password is wrong).
   Do not downgrade a finding to `DEFER`/`NEEDS-USER` just to reach `CLEAN`.
5. For a screen-feature-plan task, record the result in the task's existing
   spec-review doc `.claude/docs/review/<ID>-<slug>.md` — one document per task,
   no separate lead-review file. Replace its `## 7. Lead review` section, or
   append it at the end if absent; leave sections 1–6 untouched. If the section
   exists, read its round number and use round + 1; otherwise round 1. Format:

   ```
   ## 7. Lead review

   Round <N> · <YYYY-MM-DD> · Verdict: OPEN | CLEAN

   | ID | Severity | Class | Finding | Evidence (file:line / command) | Status |
   |---|---|---|---|---|---|
   | L1 | high | FIX | ... | ... | open |

   ### Commands run
   ### Open questions (NEEDS-USER)
   ### Round history
   | Round | Date | Result |
   ```

   Keep finding IDs stable across rounds: carry over rows that are still true
   with their current status, keep resolved rows (they are the record of what
   was fixed), and add new findings as the next `L<n>`. Append one line to
   `Round history` per lead-review round.
6. Report, in order:
   - Verdict and outstanding findings by severity and class.
   - Build/test commands run and their result.
   - Any `(TODO/needs confirmation)` or open contract decisions left.
7. End according to the verdict:
   - `OPEN` (at least one `FIX` open) and round < 3 → do not ask for sign-off.
     Tell the user the next step is `/plan-task <ID>` (it runs in fix mode via
     `lead-review-fix`), then `/lead-review <ID>` again.
   - `OPEN` at round 3 → stop the loop and ask the user how to proceed
     (accept the risk, reclassify with their decision, or keep fixing).
   - `CLEAN` (no `FIX` open) → list the `DEFER` / `NEEDS-USER` rows so the user
     knows what they accept. For a screen-feature-plan task, then run the
     `plan-report` skill (it writes the task report `.claude/docs/report/<ID>-<slug>.md`
     plus its row in the index `.claude/docs/report/<plan-file-name>.md`) and
     **stop there** — do not commit or push. Show the per-repo changed-file list
     from the report (with `mixed` marks) so the user can inspect the changes.
     Tell the user the next step is `/git-commit <ID>` when they are ready (it
     commits `booking_ticket_vue`, `ticket-system`, then the root docs repo, and
     pushes those branches), and that they tick the `lead-review` line themselves.

## Boundaries

- No code edits and no ledger edits. This command itself writes only the
  `## 7. Lead review` section of `.claude/docs/review/<ID>-<slug>.md`; on
  `CLEAN` the `plan-report` skill it runs writes the report and the index row.
- Never commit or push from this command — committing starts only when the
  user runs `/git-commit <ID>`.
- Never tick `lead-review` and never claim the work-unit is done.
- If no automated review has run yet, say so and stop — do not review from
  scratch inside this command.
