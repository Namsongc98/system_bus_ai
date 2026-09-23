---
description: Generate a manual test case sheet (Excel) from a clear-spec design doc, for QA or non-technical handoff.
argument-hint: "<page or API name, path to its .claude/docs/design/*.md>"
allowed-tools: Read, Grep, Glob, Write, Bash
---

# Prompt: Make Testcase (Excel test case sheet for QA)

Use after `clear-spec` (or after implementation, to test actual behavior)
when the audience is QA or a non-technical reviewer who needs a spreadsheet,
not source code.

## Request Template

Make testcase for:
- Page or API:
- Design doc: `.claude/docs/design/<page-or-api-slug>.md`
- Existing testcase template to follow (if the customer has one):

## Claude Instructions

1. Read the design doc (or the implemented code + `.claude/references/frontend/rules`
   if no design doc exists yet).
2. Use the `xlsx` skill to build a spreadsheet at
   `.claude/docs/testcase/<page-or-api-slug>_testcase.xlsx` with columns: ID, Steps, Input
   data, Expected result, Actual result (leave blank), Notes.
3. Cover: happy path, each validation rule, each error/status transition, and
   pagination/filter edge cases where relevant.
4. Report the file path and a short coverage summary (how many cases per
   category) — do not claim QA has run these.

## Boundaries

- Output is a spreadsheet for manual testing, not automated test code
  (`backend-write-test` / `frontend-*` skills own automated tests).
- Do not tick any ledger line — QA/manual execution is a separate step from
  generating the sheet.
