---
name: frontend-figma-to-vue
description: Convert Figma generated HTML/CSS, design notes, or screenshots into a clean Vue 3 single-file component for this booking-ticket project. Use when creating or refactoring Vue UI from Figma output.
---

# Figma to Vue

Use this skill when the user provides Figma markup, design specs, or asks to build a Vue component/page from Figma.

## Workflow

1. Read `.claude/references/frontend/frontend-instructions.md` for project architecture rules.
2. Read `.claude/references/frontend/rules/figma-style-rules.md` when exact visual conversion or style mapping is needed.
3. Read `.claude/references/frontend/rules/clean-code.md` and `.claude/references/frontend/rules/rule-component.md` for coding rules and component creation / update rules.
4. Read `.claude/references/frontend/component-registry.md` before replacing or creating UI components.
5. For full page composition, read `.claude/references/frontend/page-integration-patterns.md`.
6. Inspect existing components in `src/components/elements`, `src/components/common`, and `src/assets/icons` before creating new markup.
7. Output or edit Vue SFCs using `<script setup>` followed by `<template>`.
8. Use Tailwind utility classes and Nuxt UI where appropriate; avoid new `<style>` blocks unless Tailwind cannot express the behavior.
9. Reuse `Base*` components first, then Nuxt UI primitives, then raw semantic HTML.

## Rules

- Do not inline SVG icons if an `Icon*.vue` asset or suitable `UIcon` exists.
- Replace Figma absolute positioning with flex/grid layouts.
- Remove inline styles and Figma-specific attributes.
- Add semantic HTML, labels, alt text, explicit button types, and accessible names.
- Keep data flow props-down/events-up for extracted child components.
