# API Rules

## REST Contract

- Use resource-oriented paths under `/api`.
- Use HTTP methods consistently: `GET` for reads, `POST` for create/actions, `PUT` or `PATCH` for updates, `DELETE` for deletion or cancellation if already established.
- Return a consistent response wrapper when the module already uses one, usually containing `code`, `message`, and `data`.
- Use `ResponseEntity` when status codes differ by result.

## Validation

- Validate request DTOs with Jakarta Validation annotations.
- Add `@Valid` to controller parameters.
- Validate path and query parameters where invalid values can cause wrong business behavior.
- Do not rely only on database failures for client input validation.

## Status Codes

- `200 OK`: successful read or update.
- `201 Created`: successful creation.
- `204 No Content`: successful deletion with no body, if consistent with the module.
- `400 Bad Request`: malformed request or validation failure.
- `401 Unauthorized`: missing or invalid authentication.
- `403 Forbidden`: authenticated user lacks permission.
- `404 Not Found`: resource does not exist.
- `409 Conflict`: duplicate resource, invalid state transition, or concurrent conflict.
- `500 Internal Server Error`: unexpected server failure.

## Security

- Public endpoints must be explicit, for example register and login.
- Protected endpoints must require a valid bearer token.
- Management endpoints must check role requirements, especially for ADMIN-only operations.
- Never accept user role or user id from a request body when the authenticated principal should determine it.

## Pagination And Filtering

- List endpoints should support `page`, `size`, and relevant filters.
- Avoid returning unbounded lists for users, tickets, trips, revenue records, audit logs, or reports.
- Keep filter naming stable and predictable.

