---
description: Preview and apply a review-first Git worktree operation for the backend or frontend repository.
argument-hint: "<preview|create|list|cleanup-preview|cleanup> <backend|frontend> <task or approval token>"
allowed-tools: Read, Grep, Glob, Bash, Write, Edit
---

# Prompt: Claude Git Worktree

Use `.claude/skills/git-worktree/SKILL.md`.

## Request Template

Manage a Claude worktree.

- Action:
- Repository: backend or frontend
- Task slug:
- Approval token, only for an approved create or cleanup:

## Claude Instructions

- Always run preview before create or cleanup-preview before cleanup.
- Show the full plan and token, then stop for explicit approval.
- Never reuse an old token after repository or remote state changes.
- Do not push, create a PR, merge, or force cleanup.
