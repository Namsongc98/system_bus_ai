# Page API Review Output

## Status values

| Status | Meaning |
|---|---|
| `READY` | FE call and BE endpoint match, with a usable contract. |
| `MISMATCH` | Both sides exist but method, path, parameters, or shape differ. |
| `MISSING_BE` | The page needs the API and FE may call it, but BE does not expose it. |
| `MISSING_FE` | BE supports the capability but FE has no service/store wiring. |
| `UNKNOWN_CONTRACT` | Route exists, but schema, auth, validation, or behavior is unclear. |
| `LOCAL_ONLY` | The capability currently depends on mock, fallback, or client-only data. |

## Capability map

| Capability | Trigger | Data needed | Read/write | Dependencies |
|---|---|---|---|---|

## FE-BE readiness matrix

| Capability | FE evidence | Expected effective request | BE evidence | Status | Gap/action |
|---|---|---|---|---|---|

## Backend API specification

For every missing or mismatched API, define:

- Priority and dependency.
- Method and canonical path.
- Authentication and role.
- Query/path parameters.
- Request body and validation.
- Success response DTO and status.
- Pagination/sorting/filtering rules.
- Error responses.
- Backend controller/service/repository changes.
- Contract and integration tests.

## Acceptance checklist

- Every page action appears in the capability map.
- Child modal/drawer APIs are included.
- Effective FE URLs are resolved from the actual Axios client.
- Every `READY` row has matching method, path, and required fields.
- Missing APIs have decision-complete contracts.
- Fallback data and placeholder actions are called out.
- Backend tests precede FE wiring for new contracts.
