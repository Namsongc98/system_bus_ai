---
name: frontend-reuse-component
description: Detect, reuse, and integrate existing Vue 3 reusable components before creating new UI. Use for duplicate UI cleanup, Base component adoption, or component hierarchy enforcement.
---

# Reuse Component

Use this skill before adding new UI components or when refactoring duplicated markup.

## Workflow

1. Read `.claude/references/frontend/frontend-instructions.md` if project hierarchy details are needed.
2. Read `.claude/references/frontend/rules/clean-code.md` and `.claude/references/frontend/rules/rule-component.md` for coding rules and component creation / update rules.
3. Read `.claude/references/frontend/component-reuse-patterns.md` for Pattern A/B, props/emits, slots, and placement guidance.
4. Read `.claude/references/frontend/component-registry.md` for the current reusable component inventory, then inspect actual component files before using them.
5. Scan `src/components/elements` for primitive `Base*` components.
6. Scan `src/components/common` for reusable composed UI blocks.
7. Scan `src/components/layout` and `src/layouts` for shell components.
8. Prefer reuse as-is; if insufficient, extend the existing component with backward-compatible props or slots.
9. Create a new component only when no existing component fits the same visual or behavioral role.

## Placement Rules

- `components/elements`: stateless primitives, props/emits only, no stores, services, or router.
- `components/common`: reusable composed UI, no direct API or Pinia dependency.
- `components/layout`: app shell, navigation, headers, sidebars, footers.
- `pages`: route-level state, store/service coordination, workflow orchestration.

## Guardrails

- Do not create domain-specific buttons or inputs when `BaseButton` or `BaseInput` can be reused.
- Do not move business logic into lower-level components.
- Preserve props-down/events-up data flow.
