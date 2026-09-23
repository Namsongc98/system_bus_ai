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

- Review-first Git worktree flow for isolated backend or frontend Codex tasks.
- Approval tokens bound to repository, remote default SHA, branch, and path.
- Shared `AGENTS.md` and `.codex` wrapper context for sibling worktrees.
- Hook guards against force removal, direct branch deletion, and unmanaged
  worktree cleanup.

P2:

- Package this setup as a plugin if multiple developers need identical Codex
  capabilities.
- Add automations for monthly Codex config audit and release-readiness review.
- Consider write-capable subagents only after read-only workflows are stable.


## Ledger, Lead-Review, and Spec/Testcase Commands V1

Status: experimental. Added for Claude Code only (this repository no longer
maintains parallel Codex tooling).

Use cases:

- Track multi-work-unit features (many similar pages/APIs) without relying on
  memory or ad hoc status reports.
- Add a human sign-off gate after automated review, instead of letting Claude
  declare a work-unit done on its own.
- Produce a short design doc before implementation for ambiguous or complex
  pages/APIs, and a QA-facing Excel test case sheet from it.

New surfaces:

- `.claude/ledger/` — opt-in per-feature checklist (`spec / implement / test /
  review / lead-review`); `README.md` explains the convention, `TEMPLATE.md`
  is the copy source. Not used for small fixes.
- `.claude/commands/lead-review.md` — consolidates existing review subagent
  findings and ledger status; read-only; never ticks the ledger itself.
- `.claude/commands/clear-spec.md` — writes a design doc to `docs/design/`
  before implementation.
- `.claude/commands/make-testcase.md` — writes an Excel test case sheet to
  `docs/testcase/` via the `xlsx` skill.

Hook change:

- `handle_stop` in `.claude/hooks/codex_hook.py` now also warns (fail-open,
  never blocks) when any `.claude/ledger/*.md` file still has unticked
  checklist items.

Policy:

- Ledger and lead-review are opt-in; ordinary small changes skip them.
- `/lead-review` and `/clear-spec` never edit the ledger — only the user
  ticks `spec` and `lead-review` lines.

## Dotenv And Secret-Environment Enforcement

Status: implemented, ported from the (now unused) `.codex` hook of the same
name — `.codex/hooks/codex_hook.py` already blocked these; `.claude/hooks/codex_hook.py`
did not, which was a real gap for Claude Code sessions against the
`AGENTS.md` "never read `.env`... never print the process environment...
never expand secret environment variables" requirement.

`blocked_command_reasons` in `.claude/hooks/codex_hook.py` now also blocks:

- `dotenv_file_access` — reading `.env`/`.env.*` files by any command.
- `environment_dump` — `env`, `printenv`, `export -p`, `declare -x`.
- `sensitive_environment_reference` — `$JWT_*`, `$DB_*`, `$MAIL_*`, `$MINIO_*`
  references or assignments in a Bash command.

Added `.claude/references/backend/environment-variable-names.md` (sanitized
variable names only, no values) so Claude can check required configuration
without touching `.env` files, mirroring the equivalent `.codex` reference.

Added `.claude/hooks/test_codex_hook.py` covering the three new checks and
`scan_open_ledger_items`.


## Vibe Code Instructions

Added `.claude/VIBE_CODE_INSTRUCTIONS.md` — the single entry point for how
Claude Code is meant to be used in this repo: the end-to-end flow (ledger ->
clear-spec -> implement -> parallel-review -> make-testcase -> lead-review),
a full inventory of every `.claude/` surface (hooks, agents, commands,
skills, references, ledger), and which of those Claude acts on by itself
versus which require explicit human action. Update it alongside this roadmap
whenever a `.claude/` surface is added, renamed, or removed.
