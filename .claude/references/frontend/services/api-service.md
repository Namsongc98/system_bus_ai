# API Service Reference Map

Use this file as a small navigation document for API service work. Mandatory service rules live in [api-service-rules.md](../rules/api-service-rules.md).

## References

- [api-json-service.md](./api-json-service.md): examples for normal JSON endpoints such as list, detail, create, update, and delete.
- [api-download-service.md](./api-download-service.md): examples for Blob/export/download endpoints.
- [api-error-handling.md](./api-error-handling.md): current Axios interceptor behavior and caller error shape.
- [`../api/README.md`](../api/README.md) + [`../api/_conventions.md`](../api/_conventions.md): real per-screen API reference (path/field/button grounded in actual code) — use this instead of `api-document.md`, which is superseded and kept only at [`../api/_legacy/api-document.md`](../api/_legacy/api-document.md) for history.

## Selection Guide

- Adding a normal endpoint in `src/services/*Service.js`: read `api-service-rules.md` and `api-json-service.md`.
- Adding export/download behavior: read `api-service-rules.md` and `api-download-service.md`.
- Debugging API error behavior: read `api-error-handling.md`.
- Generating services from backend docs: read [`../api/README.md`](../api/README.md) (per-screen, grounded in real code) after the rules — not the superseded `api-document.md`.
