# Backend Environment Variable Names

This file lists configuration names only. It must not contain real credentials,
tokens, passwords, or environment-specific secret values.

## Required Secrets

| Variable | Used for |
|---|---|
| `JWT_SECRET` | JWT signing material shared by both backend services. |
| `DB_PASSWORD` | MySQL password used by both backend services. |

## Database And JPA

| Variable | Purpose | Typical non-secret default |
|---|---|---|
| `DB_URL` | JDBC connection URL. | Local MySQL database URL. |
| `DB_USERNAME` | MySQL username. | `root` for local development only. |
| `JPA_DDL_AUTO` | Hibernate schema behavior. | `validate` in every environment; the schema is created by Flyway migrations (`manage-revenue-ticket`). |

## JWT

| Variable | Purpose | Typical non-secret default |
|---|---|---|
| `JWT_EXPIRATION_MS` | Access-token lifetime in milliseconds. | `86400000` |

## Mail

| Variable | Purpose |
|---|---|
| `MAIL_USERNAME` | SMTP account name. |
| `MAIL_PASSWORD` | SMTP credential. |

## MinIO

| Variable | Purpose | Typical non-secret default |
|---|---|---|
| `MINIO_URL` | MinIO service URL. | Local MinIO URL. |
| `MINIO_ACCESS_KEY` | MinIO access credential. | None. |
| `MINIO_SECRET_KEY` | MinIO secret credential. | None. |
| `MINIO_BUCKET` | Avatar/object bucket name. | `user-avatars` |

## Claude Boundary

Claude must not read dotenv files or receive these secret variables in its
subprocess environment — `.claude/hooks/claude_hook.py` blocks `.env` reads,
environment dumps, and direct references to these variable names in Bash
commands (see `dotenv_file_access`, `environment_dump`, and
`sensitive_environment_reference` in that hook). Start services that require
secrets from a separate developer terminal and share only redacted logs with
Claude for diagnosis.

For local dotenv files, restrict OS permissions to the owning user:

```bash
chmod 600 path/to/.env
```

File permissions reduce exposure to other OS users, but they do not replace the
Claude Code permission profile because Claude normally runs as the same user.
