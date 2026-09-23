---
name: frontend-code-review
description: Review Vue 3 SFCs and related project files for correctness, conventions, accessibility, Tailwind usage, and architecture compliance. Use for review, cleanup, refactor, or pre-merge checks.
---

# Code Review

Use this skill when the user asks for review or cleanup.

## Workflow

1. Read `.claude/references/frontend/frontend-instructions.md` for project conventions.
2. Read `.claude/references/frontend/rules/clean-code.md` for general quality checks.
3. Read `.claude/references/frontend/rules/rule-component.md` when reusable components are involved.
4. Read `.claude/references/frontend/rules/figma-style-rules.md` when reviewing Figma-derived UI or Tailwind-heavy changes.
5. Inspect the target file and adjacent components, stores, services, or constants as needed.
6. Lead with findings ordered by severity.
7. Apply code changes only when the user asks for cleanup, refactor, or fixes.
8. Run relevant checks or explain why they were not run.

## Review Focus

- Composition API and `<script setup>` conventions.
- Import paths, route constants, endpoint constants, and service boundaries.
- Props/emits, data flow, store usage, and async error handling.
- Semantic HTML, labels, buttons, links, alt text, and keyboard/focus behavior.
- Tailwind class clarity, responsive layout, duplicate markup, and component reuse.
- Security concerns such as `v-html`, leaked tokens, or sensitive console output.

## Output Format

- Findings: bugs, regressions, architecture risks, or missing tests first, with file/line references when possible.
- Open questions: only when an assumption blocks a confident recommendation.
- Summary: short note of reviewed scope or applied fixes.
- Verification: commands run or residual risk if checks were not run.
