---
name: prompt-codex-config-audit
description: Audit AGENTS.md, .codex skills, prompts, references, hooks, and custom subagents for consistency.
argument-hint: "<optional focus area>"
---

# Prompt: Codex Config Audit

Use this prompt to review Codex configuration health.

## Request Template

Audit the Codex configuration in this repository.

Focus:
- AGENTS entrypoints:
- Skills and prompts:
- References and links:
- Hooks:
- Custom agents:
- Migration or roadmap drift:

## Codex Instructions

- Prefer `codex-config-reviewer` for large audits.
- For small audits, inspect directly in the main thread.
- Check for stale nested `.codex` references.
- Check broken markdown links.
- Check duplicate `name:` frontmatter in prompts and skills.
- Check that hook and agent behavior matches v1 read-only/review-first policy.
- Return findings first, then verification commands.
