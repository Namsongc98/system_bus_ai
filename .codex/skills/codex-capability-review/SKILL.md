---
name: codex-capability-review
description: Choose and design the right Codex extension surface for future repo capabilities, including hooks, subagents, MCP, plugins, automations, skills, prompts, and AGENTS.md.
---

# Codex Capability Review

Use this skill when designing future Codex capabilities for this repository.

## Decision Flow

1. If the behavior is a durable coding convention, use `AGENTS.md`.
2. If the behavior is a reusable task workflow, use a skill under `.codex/skills/`.
3. If the behavior is a quick task template, use a prompt under `.codex/prompts/`.
4. If the behavior enforces or observes Codex lifecycle events, use hooks.
5. If the behavior benefits from parallel read-only exploration or review, use subagents.
6. If the behavior needs live external tools or data, use MCP.
7. If the behavior must be installed as a reusable bundle, use a plugin.
8. If the behavior is scheduled, recurring, or follow-up based, use an automation.

## Review Checklist

- Define the capability goal and trigger.
- Identify the smallest Codex surface that fits the goal.
- Decide whether it is root, frontend, backend, or cross-project.
- Check overlap with existing `.codex/skills`, `.codex/prompts`, hooks, and agents.
- Prefer read-only behavior for v1 unless enforcement is clearly necessary.
- Require explicit user invocation for subagents.
- Require a dry-run or inspection command for hooks.
- Document the acceptance criteria and residual risk.

## Output Format

Return:

- Recommended surface.
- Why it fits.
- What to avoid.
- Files or config to add.
- Verification plan.
- Rollout priority: P0, P1, or P2.
