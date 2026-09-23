---
description: Turn a requirement, mockup, or page-API review into a short detailed-design doc before implementation starts.
argument-hint: "<page or API name, plus source: mockup path / requirement doc / fullstack-page-api-review output>"
allowed-tools: Read, Grep, Glob, Write
---

# Prompt: Clear Spec (detailed design before implementation)

Use before `backend-implement-api` or `frontend-integrate-api*` for a new or
ambiguous page/API, so implementation has one agreed source of truth instead of
being decided ad hoc while coding.

## Request Template

Clear spec for:
- Page or API:
- Source material (mockup, requirement doc, `fullstack-page-api-review` output):
- Related ledger (if any): `.claude/ledger/<feature-slug>.md`

## Claude Instructions

1. Read the source material and the relevant `.claude/references/{frontend,backend}`
   rules/workflows for this area.
2. Produce one design doc at `.claude/docs/design/<page-or-api-slug>.md` covering:
   fields/params, validation, states/status transitions, error cases,
   pagination/filter semantics (if list), and authorization.
3. Mark anything not resolvable from the source material as `(TODO/needs confirmation)`
   — do not invent business rules.
4. If a ledger entry exists for this work-unit, remind the user to tick `spec`
   once they have reviewed this doc — do not tick it yourself.
5. Stop after the doc is written. Do not start implementation in the same run
   unless explicitly asked.

## Boundaries

- Output is a design doc, not code.
- Do not mark the ledger `spec` line as done — that is a user confirmation
  after review, same as `lead-review`.
