---
description: Run the review-pipeline skill — parallel read-only reviewers matched to the changed files, finding-verifier on every high/medium finding, verified summary saved for /lead-review.
argument-hint: "<task ID, branch, or changed files>"
allowed-tools: Read, Grep, Glob, Bash, Write, Agent, Skill
---

# Prompt: Parallel Review

Entry point for the `review-pipeline` skill
(`.claude/skills/review-pipeline/SKILL.md`). `plan-task` and `lead-review-fix`
call this command at their review step; `/lead-review` reads the summary it
writes.

## Request Template

Review this change with parallel subagents.

Target:
- Task ID (or branch / changed files):
- Only part (optional, e.g. "only security", "re-verify R3"):

## Claude Instructions

- Run the `review-pipeline` skill with the target above and follow it exactly.
- Output: `.claude/docs/review/_workspace/<ID>/round-<N>/03_main_summary.md`
  plus a short chat summary (counts by verdict and severity, missing agents,
  next step).
