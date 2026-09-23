> ⚠️ **Đã superseded** — nội dung màn "Trips Management" đã được cập nhật đầy đủ hơn (grounded lại
> theo code thật, đối chiếu cả FE lẫn backend) tại
> [`../admin-trips-management/endpoints.md`](../admin-trips-management/endpoints.md). Giữ file này lại
> chỉ để tham khảo lịch sử review trước đó.

---

# Trips Management API Readiness

Reviewed page: `booking_ticket_vue/src/pages/admin/TripsManagement.vue`

## Capability map

| Capability | Required data/API |
|---|---|
| Calendar and list load | Paginated trips with route, bus, driver, status, capacity, booking count, departure, and arrival |
| Status/route/bus filters | Server query filters for scalable data; current page filters loaded records locally |
| Trip details | Trip detail by ID, or a complete list DTO |
| Create trip | Active routes, available buses, available drivers, then create mutation |
| Refresh after create | Reload trip collection |

## Readiness matrix

| Capability | FE request | BE evidence | Status | Gap/action |
|---|---|---|---|---|
| List trips | `GET /api/trips` | `GET /api/trip/scheduled` | `MISMATCH` | Align canonical path. BE response omits trip ID, status, driver, and booked seats required by the page. |
| Create trip | `POST /api/trips` | `POST /api/trip` | `MISMATCH` | Align path and return a stable response DTO instead of the entity. Add validation and authorization. |
| Trip detail | `GET /api/trips/{id}` | No matching endpoint | `MISSING_BE` | Add detail endpoint if list DTO remains summary-only. |
| Update trip | `PUT /api/trips/{id}` | `PUT /api/trip/{tripId}` | `MISMATCH` | Align path and define partial/full update semantics. |
| Complete trip | `PUT /api/trips/{id}/complete` | No matching endpoint | `MISSING_BE` | Add explicit status transition endpoint with conflict rules. |
| Delete trip | `DELETE /api/trips/{id}` | No matching endpoint | `MISSING_BE` | Decide cancel vs hard delete; prefer cancellation for operational history. |
| Active route options | `GET /api/routes?status=ACTIVE` | No GET route endpoint | `MISSING_BE` | Add paginated/list lookup endpoint returning ID and display fields. |
| Available bus options | `GET /api/buses` | `GET /api/bus` | `MISMATCH` | Align path and support availability/status filtering. |
| Driver options | `GET /api/users?role=DRIVER` | `UserController` exposes no endpoint | `MISSING_BE` | Add driver lookup endpoint with role and availability filters. |

## Backend preparation order

### P0

1. Establish canonical resource paths: `/api/trips`, `/api/routes`,
   `/api/buses`, and `/api/users`.
2. Add `GET /api/trips` with pagination and filters: status, routeId, busId,
   driverId, and departure range.
3. Define `TripSummaryResponse` with all fields used by calendar, list,
   highlights, filters, and detail modal.
4. Add active route, available bus, and available driver lookup APIs.
5. Align `POST /api/trips` with validated `CreateTripRequest` and a response DTO.

## Proposed P0 contracts

### `GET /api/trips`

- Role: `ADMIN`.
- Query: `page`, `size`, `status`, `routeId`, `busId`, `driverId`,
  `departureFrom`, `departureTo`, and `sort`.
- Default sort: `departureTime,asc`.
- Response: standard envelope containing a paginated `TripSummaryResponse`.
- `TripSummaryResponse`: `id`, `code`, `routeId`, `routeName`, `origin`,
  `destination`, `busId`, `busLabel`, `busType`, `driverId`, `driverName`,
  `departureTime`, `arrivalTime`, `status`, `bookedSeats`, `capacity`, and
  `loadFactor`.
- Errors: `400` for invalid date ranges/filter values, `401` unauthenticated,
  `403` non-admin.

### `GET /api/routes/options`

- Role: `ADMIN`.
- Query: `status=ACTIVE`, optional `q`, `page`, and `size`.
- Item response: `id`, `name`, `origin`, `destination`, `distanceKm`, `status`.
- The endpoint must return IDs usable by `CreateTripRequest`.

### `GET /api/buses/options`

- Role: `ADMIN`.
- Query: `availability=AVAILABLE`, optional `q`, `page`, and `size`.
- Item response: `id`, `busNumber`, `plateNumber`, `type`, `capacity`,
  `availability`.
- BE must standardize the available value; current code uses `PENDING`/status
  checks while FE filters for `AVAILABLE`.

### `GET /api/users/options`

- Role: `ADMIN`.
- Query: `role=DRIVER`, `availability=AVAILABLE`, optional `q`, `page`, and
  `size`.
- Item response: `id`, `name`, `email`, `role`, `availability`.
- Do not return password, token, salary, or unrelated profile fields.

### `POST /api/trips`

- Role: `ADMIN`.
- Request: `routeId`, `busId`, `driverId`, `departureTime`, `arrivalTime`.
- Validation: IDs required and existing; arrival after departure; route active;
  bus and driver available; no overlapping assignment.
- Success: `201` with `TripSummaryResponse`.
- Errors: `400` invalid input, `404` missing resource, `409` schedule or
  availability conflict, `401`/`403` auth failures.
- Mutation and bus/driver state changes must run in one transaction.

### P1

1. Add `GET /api/trips/{id}` if summary data is insufficient.
2. Align update semantics for `PUT /api/trips/{id}`.
3. Add explicit status transition APIs such as complete or cancel, including
   invalid-transition responses.

### P2

1. Move filters and month/date-range loading to server-side queries when trip
   volume requires it.
2. Add export or operational analytics only after the primary CRUD contracts
   are stable.

## Required tests

- Controller contract tests for paths, roles, validation, pagination, and error
  responses.
- Service tests for bus/driver availability and schedule conflicts.
- Repository tests for trip date-range and filter queries.
- FE service tests for effective URLs and parameters.
- Page integration tests for load, filter, create refresh, and API failures.
