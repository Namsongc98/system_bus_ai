# System Bus Codex Instructions

This repository contains a Vue frontend and a Spring Boot backend. Use this root
file for shared Codex behavior, then read the nearest project-specific
`AGENTS.md` before changing code.

## Project Boundaries

- Frontend code lives in `booking_ticket_vue/`.
- Backend code lives in `ticket-system/`.
- Shared reusable Codex assets live in `.codex/`.
- Do not recreate `.codex` folders inside `booking_ticket_vue/` or
  `ticket-system/`.

## Required Context

Before working in a subproject:

1. Read this root `AGENTS.md`.
2. Read `booking_ticket_vue/AGENTS.md` for frontend work or
   `ticket-system/AGENTS.md` for backend work.
3. Load only the root `.codex` prompt, skill, rule, workflow, or reference files
   that match the task.
4. Inspect the closest existing source files before editing.

## Shared Rules

- Preserve user changes already present in the workspace.
- Keep changes scoped to the requested frontend, backend, or Codex config area.
- Do not commit secrets, tokens, credentials, local environment files, or runtime
  data.
- Prefer existing project patterns over new abstractions.
- Do not delete, move, or rewrite documentation outside the requested scope.
- Report verification commands run and any checks that could not be run.
- For Git worktree creation or cleanup, use
  `.codex/skills/codex-git-worktree/scripts/worktree_flow.py`.
- Always show the preview and wait for explicit approval of its current token
  before creating or removing a worktree.
- Do not run force worktree removal or direct branch deletion for Codex
  worktrees.

## Root Codex Layout

- `.codex/prompts/`: reusable task prompts, prefixed with `frontend-` or
  `backend-`.
- `.codex/skills/`: reusable skills, each as a directory containing `SKILL.md`.
- `.codex/references/backend/`: backend project context, rules, and workflows.
- `.codex/references/frontend/`: frontend rules and reference documents.
- `.codex/hooks.json` and `.codex/hooks/`: project-local Codex lifecycle hooks.
- `.codex/agents/`: project-local read-only subagents for broad review tasks.
- `.codex/CODEX_CAPABILITY_ROADMAP.md`: roadmap for future Codex hooks,
  subagents, MCP, plugin, and automation capabilities.
