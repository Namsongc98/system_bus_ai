---
name: codex-git-worktree
description: Use when Codex needs to preview, create, list, or safely clean up an isolated Git worktree for the System_bus backend or frontend repository.
---

# Codex Git Worktree

Use `scripts/worktree_flow.py` for all worktree operations. Do not run raw
`git worktree add`, `git worktree remove`, or branch deletion commands.

## Required Flow

1. Run `preview --repo backend|frontend --task <slug>`.
2. Show the user the complete preview, including warnings and approval token.
3. Wait for explicit approval of that exact token.
4. Run `create --approve <token>`.
5. Open the generated wrapper workspace, not only the nested repository.

Cleanup follows the same pattern:

1. Run `cleanup-preview --repo backend|frontend --task <slug>`.
2. Wait for explicit approval of the cleanup token.
3. Run `cleanup --approve <token>`.

## Commands

```bash
python3 .codex/skills/codex-git-worktree/scripts/worktree_flow.py preview \
  --repo backend --task ticket-validation

python3 .codex/skills/codex-git-worktree/scripts/worktree_flow.py create \
  --approve '<token>'

python3 .codex/skills/codex-git-worktree/scripts/worktree_flow.py list

python3 .codex/skills/codex-git-worktree/scripts/worktree_flow.py cleanup-preview \
  --repo backend --task ticket-validation

python3 .codex/skills/codex-git-worktree/scripts/worktree_flow.py cleanup \
  --approve '<token>'
```

## Guardrails

- Treat previews as read-only; they may query `origin` but do not fetch.
- Never infer approval from a prior general request. Approval must include the
  current token.
- Stop if the source repository, remote default SHA, branch, or destination
  changed after preview.
- Dirty source changes remain in the source checkout and are not copied.
- Do not push, create a PR, merge, or force cleanup.
- Work only below the sibling `System_bus-worktrees` directory.
