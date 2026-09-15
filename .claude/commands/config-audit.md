---
description: Audit AGENTS.md, .claude skills, prompts, references, hooks, and custom subagents for consistency.
argument-hint: "<optional focus area>"
allowed-tools: Read, Grep, Glob
---

# Prompt: Claude Config Audit

Use this prompt to review Claude Code configuration health.

## Request Template

Audit the Claude configuration in this repository.

Focus:
- AGENTS entrypoints:
- Skills and prompts:
- References and links:
- Hooks:
- Custom agents:
- Migration or roadmap drift:

## Claude Instructions

- Prefer `config-reviewer` for large audits.
- For small audits, inspect directly in the main thread.
- Check for stale nested `.claude` references.
- Check broken markdown links.
- Check duplicate `name:` frontmatter in prompts and skills.
- Check that hook and agent behavior matches v1 read-only/review-first policy.
- Return findings first, then verification commands.
