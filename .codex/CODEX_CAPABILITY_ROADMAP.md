# Codex Capability Roadmap

## Summary

This roadmap extends the existing Codex setup with project-local hooks and
read-only subagents. The goal is safer tool use, higher-quality review, and less
main-thread context noise during broad analysis.

## Hooks V1

Status: experimental.

Use cases:

- Block clearly destructive Bash commands before they run.
- Warn when escalation requests are vague or overbroad.
- Warn when user prompts appear to include secrets.
- Summarize failed Bash commands and suggest the next diagnostic step.
- Remind Codex to report changed files, verification, skipped checks, and risk.

Implemented events:

- `PreToolUse` for `Bash`
- `PermissionRequest` for `Bash`
- `PostToolUse` for `Bash`
- `UserPromptSubmit`
- `Stop`

Policy:

- Destructive commands block hard.
- Secret detection, broad approval detection, failed command summaries, and stop
  reminders are warnings only.
- Hooks do not edit files or run formatters.
- Hook timeout is 10 seconds.

## Subagents V1

Status: experimental.

Use cases:

- Broad PR or branch review.
- Large FE/BE changes where separate reviewers reduce context noise.
- Security review across config, backend, frontend, and Codex scripts.
- Test coverage review.
- Codex configuration audits.

Custom agents:

- `backend-reviewer`
- `frontend-reviewer`
- `test-gap-reviewer`
- `codex-config-reviewer`
- `security-reviewer`

Policy:

- V1 agents are read-only.
- Use subagents only when explicitly requested.
- Main agent waits for requested agents and consolidates findings.
- Avoid subagents for small tasks.

## Review Prompts

- `prompt-codex-review-hooks-roadmap`
- `prompt-codex-parallel-pr-review`
- `prompt-codex-config-audit`

## Future Phases

P1:

- Add MCP integration candidates for Figma, Playwright, GitHub, and docs.
- Add more precise hook payload parsing after observing real Codex hook payloads.
- Add a project config review checklist for `/hooks` trust state.

Implemented backend capabilities:

- Git diff secret warnings with redacted findings.
- Credential rotation workflow and environment-only backend secret configuration.
- Kafka and observability rules.
- Kafka event, database change, and release readiness skills.
- Testcontainers guidance and regression coverage requirements.
- Flyway/Liquibase migration policy and an optional OpenAPI workflow.

Implemented cross-project capabilities:

- Review-first dual Git worktree flow for isolated backend or frontend Codex
  tasks.
- Approval tokens bind both the common and selected project repository,
  including remote default SHAs, branches, and paths.
- The common repository worktree supplies `.codex`, `AGENTS.md`, and
  `.gitignore`; the selected project worktree is nested beneath it.
- Hook guards against force removal, direct branch deletion, and unmanaged
  worktree cleanup.

P2:

- Package this setup as a plugin if multiple developers need identical Codex
  capabilities.
- Add automations for monthly Codex config audit and release-readiness review.
- Consider write-capable subagents only after read-only workflows are stable.
