---
name: frontend-integrate-download-api
description: Add or update Vue service-layer functions for Blob, export, report, PDF, Excel, image, or browser download API endpoints.
---

# Integrate Download API

Use this skill when an endpoint returns a file or Blob instead of normal JSON.

## Workflow

1. Read `.claude/references/frontend/rules/api-service-rules.md` for mandatory service-layer rules.
2. Read `.claude/references/frontend/api-download-service.md` for download implementation examples.
3. Read `.claude/references/frontend/api-document.md` when endpoint details must come from the project API docs.
4. Identify the target service file, such as `src/services/reportService.js`.
5. Preserve existing exports and append new functions; do not overwrite unrelated service functions.
6. Use `apiClient` with `responseType: 'blob'`.
7. Keep UI feedback outside the service.

## Download Rules

- Use this skill for export Excel, export PDF, generated reports, image downloads, QR downloads, and other Blob responses.
- Prefer a clear function name such as `exportRevenueReport`, `downloadTicketPdf`, or `downloadQrCode`.
- Return nothing unless the existing caller expects a Blob, object URL, or metadata.
- Do not use this skill for JSON endpoints; use `integrate-api` instead.
