# Page API Review Output

## Review scope

- Target page:
- Route and role:
- Review mode: `review-only` or `review-and-implement`
- Backend modules inspected:
- Compatibility requirement:
- Assumptions:

## Status values

| Status | Meaning |
|---|---|
| `READY` | FE call and BE endpoint match, with a usable contract. |
| `MISMATCH` | Both sides exist but method, path, parameters, or shape differ. |
| `MISSING_BE` | The page needs the API and FE may call it, but BE does not expose it. |
| `MISSING_FE` | BE supports the capability but FE has no service/store wiring. |
| `UNKNOWN_CONTRACT` | Route exists, but schema, auth, validation, or behavior is unclear. |
| `LOCAL_ONLY` | The capability currently depends on mock, fallback, or client-only data. |

## Disposition values

| Disposition | Meaning |
|---|---|
| `KEEP_BE` | Keep the backend contract and add or repair FE wiring. |
| `EXTEND_BE_COMPATIBLY` | Add optional backend behavior without breaking current callers. |
| `CHANGE_BE_CONTRACT` | Correct the existing backend contract and migrate affected callers. |
| `CREATE_BE_API` | Add a new endpoint with a distinct responsibility. |
| `DEFER` | Exclude the capability for now and define temporary UI behavior. |

## Capability map

| Capability | Trigger | Data needed | Read/write | Dependencies |
|---|---|---|---|---|

## FE-BE readiness matrix

| Capability | FE evidence | Expected effective request | BE evidence | Status | Gap/action |
|---|---|---|---|---|---|

## API decision register

Every non-`READY` matrix row must have one decision.

| Capability | Disposition | Reason | Compatibility impact | Priority |
|---|---|---|---|---|

## API contract specification

For every missing or mismatched API, define:

- Priority and dependency.
- Disposition.
- Owning backend module.
- Method and canonical path.
- Authentication and role.
- Query/path parameters.
- Request body and validation.
- Success response DTO and status.
- Pagination/sorting/filtering rules.
- Error responses.
- Existing callers and backward-compatibility impact.
- Backend controller/service/repository changes.
- Contract and integration tests.

## File-level implementation plan

| Order | Priority | Area | File/module | Change | Depends on | Verification |
|---|---|---|---|---|---|---|

The plan must explicitly cover applicable DTO, controller, service, repository,
security, database migration, Kafka/Redis contract, tests, FE endpoint/service,
store, page/component wiring, and API documentation changes.

## FE connection sequence

| Order | Capability | Endpoint/service | Store/page wiring | Blocked by |
|---|---|---|---|---|

## Acceptance checklist

- Every page action appears in the capability map.
- Child modal/drawer APIs are included.
- Effective FE URLs are resolved from the actual Axios client.
- Every `READY` row has matching method, path, and required fields.
- Every non-`READY` row has a disposition.
- Missing or changed APIs have decision-complete contracts.
- Breaking changes list affected callers and migration steps.
- The plan names concrete modules/files or the exact discovery step needed to
  locate them.
- Fallback data and placeholder actions are called out.
- Backend tests precede FE wiring for new contracts.
- Acceptance checks cover success, empty, validation, authorization, conflict,
  not-found, and pagination/filter behavior where applicable.
