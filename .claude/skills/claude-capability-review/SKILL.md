---
name: claude-capability-review
description: Choose and design the right Claude Code extension surface for future repo capabilities, including hooks, subagents, MCP, plugins, automations, skills, prompts, and CLAUDE.md.
---

# Claude Capability Review

Use this skill when designing future Claude Code capabilities for this repository.

## Decision Flow

1. If the behavior is a durable coding convention, use `CLAUDE.md`.
2. If the behavior is a reusable task workflow, use a skill under `.claude/skills/`.
3. If the behavior is a quick task template, use a prompt under `.claude/commands/`.
4. If the behavior enforces or observes Claude Code lifecycle events, use hooks.
5. If the behavior benefits from parallel read-only exploration or review, use subagents.
6. If the behavior needs live external tools or data, use MCP.
7. If the behavior must be installed as a reusable bundle, use a plugin.
8. If the behavior is scheduled, recurring, or follow-up based, use an automation.

## Review Checklist

- Define the capability goal and trigger.
- Identify the smallest Claude Code surface that fits the goal.
- Decide whether it is root, frontend, backend, or cross-project.
- Check overlap with existing `.claude/skills`, `.claude/commands`, hooks, and agents.
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
