# API Service Reference Map

Use this file as a small navigation document for API service work. Mandatory service rules live in [api-service-rules.md](rules/api-service-rules.md).

## References

- [api-json-service.md](./api-json-service.md): examples for normal JSON endpoints such as list, detail, create, update, and delete.
- [api-download-service.md](./api-download-service.md): examples for Blob/export/download endpoints.
- [api-error-handling.md](./api-error-handling.md): current Axios interceptor behavior and caller error shape.
- [api-document.md](./api-document.md): backend API documentation used when endpoint details are needed.

## Selection Guide

- Adding a normal endpoint in `src/services/*Service.js`: read `api-service-rules.md` and `api-json-service.md`.
- Adding export/download behavior: read `api-service-rules.md` and `api-download-service.md`.
- Debugging API error behavior: read `api-error-handling.md`.
- Generating services from backend docs: read `api-document.md` after the rules.
