# Codex Config Migration Report

## Summary

Codex configuration for `ticket-system` and `booking_ticket_vue` was migrated
into one shared root structure under `System_bus/.codex`.

Nested project Codex folders were removed:

- `ticket-system/.codex`
- `booking_ticket_vue/.codex`

Instruction entrypoints are now:

- `AGENTS.md`: shared repository rules.
- `ticket-system/AGENTS.md`: backend-specific rules.
- `booking_ticket_vue/AGENTS.md`: frontend-specific rules.

## Source To Destination Mapping

Backend references:

- `ticket-system/.codex/memory/project-context.md` -> `.codex/references/backend/project-context.md`
- `ticket-system/.codex/rules/*.md` -> `.codex/references/backend/rules/*.md`
- `ticket-system/.codex/workflows/*.md` -> `.codex/references/backend/workflows/*.md`

Frontend references:

- `booking_ticket_vue/.codex/rules/*.md` -> `.codex/references/frontend/rules/*.md`
- `booking_ticket_vue/.codex/references/*.md` -> `.codex/references/frontend/*.md`

Prompts:

- `ticket-system/.codex/prompts/explain-code.md` -> `.codex/prompts/backend-explain-code.md`
- `ticket-system/.codex/prompts/fix-bug.md` -> `.codex/prompts/backend-fix-bug.md`
- `ticket-system/.codex/prompts/implement-feature.md` -> `.codex/prompts/backend-implement-feature.md`
- `ticket-system/.codex/prompts/review-code.md` -> `.codex/prompts/backend-review-code.md`
- `booking_ticket_vue/.codex/prompts/figma-to-vue.md` -> `.codex/prompts/frontend-figma-to-vue.md`
- `booking_ticket_vue/.codex/prompts/integrate-component-to-page.md` -> `.codex/prompts/frontend-integrate-component-to-page.md`
- `booking_ticket_vue/.codex/prompts/reuse-component.md` -> `.codex/prompts/frontend-reuse-component.md`

Skills:

- `ticket-system/.codex/skills/code-review.md` -> `.codex/skills/backend-code-review/SKILL.md`
- `ticket-system/.codex/skills/debug-backend.md` -> `.codex/skills/backend-debug/SKILL.md`
- `ticket-system/.codex/skills/implement-api.md` -> `.codex/skills/backend-implement-api/SKILL.md`
- `ticket-system/.codex/skills/refactor-service.md` -> `.codex/skills/backend-refactor-service/SKILL.md`
- `ticket-system/.codex/skills/write-test.md` -> `.codex/skills/backend-write-test/SKILL.md`
- `booking_ticket_vue/.codex/skills/api-pinia-store` -> `.codex/skills/frontend-api-pinia-store`
- `booking_ticket_vue/.codex/skills/check-flow` -> `.codex/skills/frontend-check-flow`
- `booking_ticket_vue/.codex/skills/code-review` -> `.codex/skills/frontend-code-review`
- `booking_ticket_vue/.codex/skills/figma-to-vue` -> `.codex/skills/frontend-figma-to-vue`
- `booking_ticket_vue/.codex/skills/fix-error` -> `.codex/skills/frontend-fix-error`
- `booking_ticket_vue/.codex/skills/integrate-api` -> `.codex/skills/frontend-integrate-api`
- `booking_ticket_vue/.codex/skills/integrate-api-from-doc` -> `.codex/skills/frontend-integrate-api-from-doc`
- `booking_ticket_vue/.codex/skills/integrate-download-api` -> `.codex/skills/frontend-integrate-download-api`
- `booking_ticket_vue/.codex/skills/reuse-component` -> `.codex/skills/frontend-reuse-component`
- `booking_ticket_vue/.codex/skills/wire-api-to-event` -> `.codex/skills/frontend-wire-api-to-event`

AGENTS files:

- `ticket-system/.codex/AGENTS.md` was merged into `ticket-system/AGENTS.md`.
- `booking_ticket_vue/.codex/AGENTS.md` was merged into `booking_ticket_vue/AGENTS.md`.
- A new root `AGENTS.md` was added for shared repository rules.

## Conflict Decisions

- Duplicate `clean-code.md` files were preserved as scoped references:
  - Backend: `.codex/references/backend/rules/clean-code.md`
  - Frontend: `.codex/references/frontend/rules/clean-code.md`
- Duplicate `code-review` skills were renamed and preserved:
  - Backend: `.codex/skills/backend-code-review/SKILL.md`
  - Frontend: `.codex/skills/frontend-code-review/SKILL.md`
- Obsolete instructions that treated nested `.codex` folders as local project
  instruction roots were removed or rewritten to use the shared root `.codex`.
- Skill frontmatter names were prefixed with `backend-` or `frontend-` to avoid
  collisions.
- Prompt frontmatter names were prefixed with `prompt-backend-` or
  `prompt-frontend-` to avoid collisions with skills.

## Verification Checklist

- Confirm no nested Codex folders remain:
  `find ticket-system booking_ticket_vue -path '*/.codex*'`
- Confirm root assets exist:
  `find .codex -maxdepth 4 -type f | sort`
- Search for stale nested Codex references:
  `rg 'ticket-system/\.codex|booking_ticket_vue/\.codex|\.codex/(rules|memory|workflows)|\.codex/skills/code-review'`
- Verify all skills use `SKILL.md`:
  `find .codex/skills -mindepth 2 -maxdepth 2 -name SKILL.md | sort`
- Verify skill names are unique:
  `rg '^name:' .codex/skills`

No verification steps were intentionally skipped.
