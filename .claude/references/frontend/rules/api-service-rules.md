# API Service Rules

These rules are mandatory for service-layer code in this Vue 3/Vite booking-ticket frontend.

## Location And Naming

- Put service modules in `src/services/`.
- Name files by domain, for example `authService.js`, `ticketService.js`, `tripService.js`, or `busRouteService.js`.
- Use named exports for service functions.

## Axios Client

Always import the shared Axios client:

```js
import apiClient from '@/services/axios'
```

Do not import raw `axios` inside service files.

## Service Responsibilities

Services must:

- Call backend endpoints through `apiClient`.
- Format query params, path params, and request bodies.
- Return `res.data` for JSON endpoints.
- Use `responseType: 'blob'` for download/export endpoints.

Services must not:

- Manage loading state.
- Show toast or UI feedback.
- Import components, router, composables, or Pinia stores.
- Implement `try/catch` for normal JSON endpoints.
- Mutate shared state directly.

## Data Flow

Use this direction:

```text
Page/Component -> composable/store -> service -> apiClient -> backend
```

Stores may call services. Services must never call stores.

## Error Behavior

`src/services/axios.js` unwraps API errors with `error.response?.data ?? error`. Callers should read `error?.message` and `error?.code` unless the local code has converted the error into another shape.

Read [api-error-handling.md](../services/api-error-handling.md) before changing interceptor or caller error behavior.
