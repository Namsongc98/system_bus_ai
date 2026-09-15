# Security Rules

## Authentication

- JWT validation must verify signature and expiration.
- Authorities must come from trusted token claims or persisted user data, never from hardcoded values.
- Use the `ROLE_` prefix consistently when Spring Security expects role authorities.
- Public endpoints must be deliberately marked and limited.

## Passwords And Secrets

- Passwords must be hashed with a configured `PasswordEncoder` bean, normally BCrypt with an appropriate strength.
- Do not instantiate password encoders ad hoc in services.
- Do not log passwords, tokens, SMTP credentials, database passwords, or JWT secrets.
- Prefer environment variables for secrets:
  - `DB_PASSWORD`
  - `JWT_SECRET`
  - `MAIL_PASSWORD`
  - other service credentials

## Authorization

- ADMIN-only operations must enforce ADMIN access.
- DRIVER, COLLECTOR, and CUSTOMER workflows must only allow actions appropriate to the role.
- Do not trust client-provided role, user id, seller id, or customer id without checking against the authenticated principal and business rules.

## API Hardening

- Validate request bodies and parameters.
- Use parameterized queries.
- Return safe error messages to clients.
- Rate limiting should be considered for authentication and high-risk endpoints.
- Keep CORS and CSRF behavior explicit and appropriate for stateless JWT APIs.

