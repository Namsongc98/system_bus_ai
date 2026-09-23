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
| `JPA_DDL_AUTO` | Hibernate schema behavior. | `update` locally; `validate` in production. |

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

## Codex Boundary

Codex must not read dotenv files or receive these secret variables in its
subprocess environment. Start services that require secrets from a separate
developer terminal and provide Codex only redacted logs for diagnosis.

For local dotenv files, restrict OS permissions to the owning user:

```bash
chmod 600 path/to/.env
```

File permissions reduce exposure to other OS users, but they do not replace the
Codex permission profile because Codex normally runs as the same user.
