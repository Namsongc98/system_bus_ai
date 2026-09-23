# Claude Capability Roadmap

## Summary

This roadmap extends the existing Claude setup with project-local hooks and
read-only subagents. The goal is safer tool use, higher-quality review, and less
main-thread context noise during broad analysis.

## Hooks V1

Status: experimental.

Use cases:

- Block clearly destructive Bash commands before they run.
- Warn when escalation requests are vague or overbroad.
- Warn when user prompts appear to include secrets.
- Summarize failed Bash commands and suggest the next diagnostic step.
- Remind Claude to report changed files, verification, skipped checks, and risk.

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
- Security review across config, backend, frontend, and Claude scripts.
- Test coverage review.
- Claude configuration audits.

Custom agents:

- `backend-reviewer`
- `frontend-reviewer`
- `test-gap-reviewer`
- `config-reviewer`
- `security-reviewer`

Policy:

- V1 agents are read-only.
- Use subagents only when explicitly requested.
- Main agent waits for requested agents and consolidates findings.
- Avoid subagents for small tasks.

## Review Prompts

- `/review-hooks`
- `/parallel-review`
- `/config-audit`

## Future Phases

P1:

- Add MCP integration candidates for Figma, Playwright, GitHub, and docs.
- Add more precise hook payload parsing after observing real Claude hook payloads.
- Add a project config review checklist for `/hooks` trust state.

Implemented backend capabilities:

- Git diff secret warnings with redacted findings.
- Credential rotation workflow and environment-only backend secret configuration.
- Kafka and observability rules.
- Kafka event, database change, and release readiness skills.
- Testcontainers guidance and regression coverage requirements.
- Flyway/Liquibase migration policy and an optional OpenAPI workflow.

Implemented cross-project capabilities:

- Review-first Git worktree flow for isolated backend or frontend Claude tasks.
- Approval tokens bound to repository, remote default SHA, branch, and path.
- Shared `CLAUDE.md` and `.claude` wrapper context for sibling worktrees.
- Hook guards against force removal, direct branch deletion, and unmanaged
  worktree cleanup.

P2:

- ~~Package this setup as a plugin~~ — done: `system-bus-dev` plugin, built by
  `.claude/plugin/build_plugin.py` (see "Claude Removal" below).
- Add automations for monthly Claude config audit and release-readiness review.
- Consider write-capable subagents only after read-only workflows are stable.


## Ledger, Lead-Review, and Spec/Testcase Commands V1

Status: experimental. Added for Claude Code.

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
- `.claude/commands/clear-spec.md` — writes a design doc to `.claude/docs/design/`
  before implementation.
- `.claude/commands/make-testcase.md` — writes an Excel test case sheet to
  `.claude/docs/testcase/` via the `xlsx` skill.

Hook change:

- `handle_stop` in `.claude/hooks/claude_hook.py` now also warns (fail-open,
  never blocks) when any `.claude/ledger/*.md` file still has unticked
  checklist items.

Policy:

- Ledger and lead-review are opt-in; ordinary small changes skip them.
- `/lead-review` and `/clear-spec` never edit the ledger — only the user
  ticks `spec` and `lead-review` lines.

## Dotenv And Secret-Environment Enforcement

Status: implemented, ported from the former `.codex` hook (since removed) —
it already blocked these; `.claude/hooks/claude_hook.py` did not, which was a real
gap for Claude Code sessions against the "Working Rules" in `CLAUDE.md` ("never read `.env`... never print the process environment...
never expand secret environment variables" requirement.

`blocked_command_reasons` in `.claude/hooks/claude_hook.py` now also blocks:

- `dotenv_file_access` — reading `.env`/`.env.*` files by any command.
- `environment_dump` — `env`, `printenv`, `export -p`, `declare -x`.
- `sensitive_environment_reference` — `$JWT_*`, `$DB_*`, `$MAIL_*`, `$MINIO_*`
  references or assignments in a Bash command.

Added `.claude/references/backend/environment-variable-names.md` (sanitized
variable names only, no values) so Claude can check required configuration
without touching `.env` files.

Added `.claude/hooks/test_claude_hook.py` covering the three new checks and
`scan_open_ledger_items`.


## Vibe Code Instructions

Added `.claude/VIBE_CODE_INSTRUCTIONS.md` — the single entry point for how
Claude Code is meant to be used in this repo: the end-to-end flow (ledger ->
clear-spec -> implement -> parallel-review -> make-testcase -> lead-review),
a full inventory of every `.claude/` surface (hooks, agents, commands,
skills, references, ledger), and which of those Claude acts on by itself
versus which require explicit human action. Update it alongside this roadmap
whenever a `.claude/` surface is added, renamed, or removed.

## Codex Removal And Path Fixes

Status: implemented.

- Removed `.codex/`, the root `AGENTS.md` (its shared rules moved to the
  "Working Rules" section of `CLAUDE.md`), `.claude/MIGRATION_REPORT.md`, and the
  `agents/openai.yaml` files inside skills.
- `ticket-system/AGENTS.md` and `booking_ticket_vue/AGENTS.md` renamed to
  `CLAUDE.md` in each subproject (auto-loaded by Claude Code there); their
  `../.codex/` paths now point to `../.claude/`.
- Hook renamed `codex_hook.py` → `claude_hook.py` (and its test); `settings.json`
  rewired. Behavior unchanged.
- `git-worktree` scripts: wrapper now symlinks `CLAUDE.md` and `.claude`; branch
  prefix `claude/<task>` instead of `codex/<task>`. Existing `codex/*` branches
  are not touched or renamed.
- All plain-text `docs/design/` and `docs/testcase/` mentions now say
  `.claude/docs/design/` and `.claude/docs/testcase/` (where the files really are).
- FE skills: 18 stale `references/frontend/*.md` paths repointed to
  `services/`, `components/`, `api/`.

## Spec Gate For Screen Tasks

Status: implemented.

Screens were coded before their API wiring was correct, so `plan-task` needed a
fresh, user-approved scope instead of the point-in-time evidence in the plan.

- Added `/spec-review <ID>` (`.claude/commands/spec-review.md`): runs
  `fullstack-page-api-review` plus a per-capability feature check against the
  design doc, writes `.claude/docs/review/<ID>-<slug>.md` (readiness matrix,
  fix scope `S1..Sn`, out of scope, proposed plan changes, open decisions).
  Read-only for code; never ticks the ledger.
- `plan-task` gate step 5: stops unless the task's `spec` line is ticked and
  the review doc exists; implementation scope = that doc's fix scope.
- Ledger README/TEMPLATE, the plan header, and `VIBE_CODE_INSTRUCTIONS.md`
  describe the `spec-review → user ticks spec → plan-task` order.

## Spec Review As A Skill

Status: implemented.

`/spec-review` only worked as an explicit command, so surfaces that load
skills but not commands (e.g. Cowork, per the note already in
`plan-task/SKILL.md`) could not run it at all.

- Added `.claude/skills/spec-review/SKILL.md` holding the real instructions
  (Request Template, Claude Instructions, Boundaries), matching the
  `git-worktree` pattern of command-as-thin-pointer.
- `.claude/commands/spec-review.md` is now a thin wrapper: keeps its
  frontmatter (`argument-hint`, `allowed-tools`) and Request Template, points
  to the skill for full instructions. `/spec-review <ID>` behavior is
  unchanged.
- `plan-task/SKILL.md` and `VIBE_CODE_INSTRUCTIONS.md` (§3 skills table) now
  note the skill as an alternate entry point to the same gate.
- This does not change the gate semantics: still read-only for code, one task
  ID per run, never ticks `spec` — Claude can now reach those instructions via
  skill-matching, but the human-tick requirement is unchanged either way.
