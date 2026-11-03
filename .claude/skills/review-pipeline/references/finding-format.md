# Finding format (reviewers and finding-verifier)

Answer in this format only. The orchestrator saves your answer verbatim and
another agent reads it, so free prose outside these blocks is lost.

Never copy a secret value (password, token, key, connection string with
credentials) into your answer, even as evidence: write the file:line and
`<redacted>` instead. The saved files are not scanned by the Stop hook.

## Reviewers

```
## Findings
| # | Severity | File:line | Finding | Why it matters | How to check |
|---|---|---|---|---|---|
| 1 | high | ticket-system/.../AvatarService.java:42 | ... | ... | `mvn -f ticket-system/pom.xml -pl manage-revenue-ticket -am -Dtest=AvatarServiceTest -Dsurefire.failIfNoSpecifiedTests=false test` |

## Residual risks
- <risk that is not a defect in this change>

## Not checked
- <files or areas you were given but could not review, and why>
```

- Severity: `high` = data loss, security hole, broken contract or build;
  `medium` = wrong behaviour in a realistic case, missing test for changed
  behaviour; `low` = style, naming, minor cleanup.
- `File:line` must point at a line you read. No line → write the file path and
  say why in `Finding`.
- `How to check` is one concrete command or code path. It is a suggestion: the
  verifier rebuilds the command from its own allowed templates and never runs
  your text verbatim.
- No findings → write `## Findings` followed by `none`, and still fill
  `Not checked`.

## finding-verifier

```
## Verdicts
| # | Source finding | Verdict | Evidence |
|---|---|---|---|
| 1 | backend-reviewer #1 | confirmed | `AvatarService.java:42` reads ... ; `-Dtest=AvatarServiceTest` → 1 failure: ... |

## Commands run
- `<command>` → <pass/fail counts or error>
```

- Verdict: `confirmed` (code or a test shows the defect), `refuted` (code or a
  test shows the claim is false — say what disproves it), `uncertain` (cannot
  decide, or a check could not run — say what is missing).
- Evidence names a file:line you read or a command you ran and its result.
  Reasoning alone is not enough for `confirmed` or `refuted`.
