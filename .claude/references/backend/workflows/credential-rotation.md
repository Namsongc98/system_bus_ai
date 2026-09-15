# Workflow: Exposed Credential Rotation

Use this workflow whenever a password, token, private key, JWT secret, or service credential appears in source, Git history, logs, prompts, or build artifacts.

## Contain

1. Stop sharing or committing the exposed value.
2. Identify the credential owner, affected environments, permissions, and exposure window.
3. Revoke or rotate the credential at its provider:
   - Regenerate JWT signing material and expire existing sessions/tokens as required.
   - Change the MySQL password and update authorized runtime secret stores.
   - Revoke the Gmail App Password and create a replacement only if mail remains enabled.
   - Rotate MinIO access and secret keys and review bucket permissions.
4. Store replacements in environment variables or the deployment secret manager. Never write replacement values into the repository.

## Repair

1. Replace hardcoded configuration with required environment placeholders.
2. Add only redacted placeholders to `.env.example`.
3. Search tracked files, staged changes, logs, artifacts, and relevant Git history for copies.
4. Rewrite Git history only after coordinating with collaborators; rotation is still required because history removal does not invalidate a credential.
5. Verify old credentials fail and new credentials work in each affected environment.

## Report

- Record credential type and affected systems, never the secret value.
- Record rotation time, owner, validation result, and any sessions or deployments restarted.
- Treat unknown exposure scope as compromised until proven otherwise.
