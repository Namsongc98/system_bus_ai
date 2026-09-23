# Frontend Booking Ticket — Claude Instructions

## Project Overview

Booking Ticket is a Vue 3 single-page application that connects to Java Spring Boot REST APIs. The app supports `admin` and `user` roles. UI work should follow the existing component system and Figma-derived layouts when the user provides design context.

For the current source layout, see [folder-structure.md](./folder-structure.md).

For the real per-screen API reference (which button calls which endpoint, grounded in actual code — not aspirational), see [`api/README.md`](./api/README.md). For service/store-writing conventions and reuse patterns, see [`services/`](./services/) and [`components/`](./components/). See [`README.md`](./README.md) for the full map of this references folder.

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | Vue 3 Composition API with `<script setup>` |
| Build | Vite 8 |
| Routing | Vue Router 5 in `src/router/` |
| State | Pinia 3 setup stores in `src/stores/` |
| HTTP | Axios through `src/services/axios.js` |
| Styling | Tailwind CSS 4.2.4 and Nuxt UI |
| Testing | Vitest unit tests and Playwright end-to-end tests |

## Architecture Rules

### Imports

- Use the `@/` alias for internal imports.
- Import route names from `@/constants/routes`; do not hardcode route names.
- Import API endpoint constants from `@/constants/api_endpoint`; do not scatter endpoint strings.

### Stores

- Use Pinia setup-store style: `defineStore('name', () => { ... })`.
- Organize stores as state refs, computed getters, async actions, then `return {}`.
- Stores call services for data fetching and mutations.
- Stores must not call Axios clients directly.
- Use `src/stores/`; do not create `src/store/`.

### Services

- Service files live in `src/services/` and export plain service objects.
- Service methods map to backend endpoints using `API_ENDPOINTS`.
- Services use `apiClient` or the appropriate exported client from `src/services/axios.js`.
- Services do not hold state, import stores, navigate routes, or show UI feedback.
- The shared Axios response interceptor returns the full Axios response on success and rejects with normalized backend error data when available.

### Components

- Reusable primitives live in `src/components/elements/` and use the `Base*` prefix.
- Reusable composed UI blocks live in `src/components/common/`.
- Layout shell components live in `src/components/layout/` or `src/layouts/`.
- Page components own route-level workflow state and may call stores or composables.
- `elements/` components are props-in/events-out only: no stores, services, or router.
- Reuse or extend existing components before creating new ones.
- Page-level static data such as tabs, filter options, table columns, fallback records, sample Figma data, and nav links must be imported from `src/constants/admin/<screen>` or `src/constants/user/<screen>`.

### Router

- All route names live in `ROUTE_NAMES` in `src/constants/routes.js`.
- Role-specific route modules live under `src/router/routes/`.
- Navigation guards live in `src/router/guards.js` and are registered from `src/router/index.js`.
- Use route `meta` for auth and role checks.

## Styling Rules

- Prefer Tailwind utility classes directly in Vue templates.
- Use Nuxt UI components when no project `Base*` component covers the need.
- Use `src/assets/css/main.css` only for minimal global CSS, Tailwind imports, Nuxt UI imports, and unavoidable global rules.
- Do not add component-specific global CSS when Tailwind classes can express the styling.
- Do not use inline `style` attributes for generated UI.
- Keep layouts mobile-first with responsive prefixes such as `sm:`, `md:`, `lg:`, and `xl:`.

## Coding Standards

- Always use `<script setup>`.
- Declare props with `defineProps()` and defaults.
- Declare emitted events with `defineEmits()`.
- Avoid Options API.
- Use ES modules, single quotes, no semicolons, and two-space indentation.
- Use JSDoc typedefs in `src/types/index.js` for shared domain models when needed.

## Naming

| Artifact | Convention | Example |
|---|---|---|
| Page SFC | PascalCase + `View` or `Page` | `TripView.vue`, `LoginPage.vue` |
| Base component | PascalCase + `Base` prefix | `BaseButton.vue`, `BaseTabs.vue` |
| Layout component | PascalCase + `Layout` or `App` prefix | `UserLayout.vue`, `AppHeader.vue` |
| Composable | camelCase with `use` prefix | `useAuth.js` |
| Store file | camelCase domain | `booking.js` |
| Service file | camelCase + `Service` | `ticketService.js` |
| Constants | SCREAMING_SNAKE_CASE | `ROUTE_NAMES`, `API_ENDPOINTS` |

## State & Data Flow

```text
Page -> composable/store -> service -> Axios client -> Java API
```

Pages coordinate UI state, child component props, emitted events, navigation, loading states, and user feedback. Lower-level reusable components should stay focused on presentation and local interaction.

## Authentication Flow

- JWT values are stored using `LOCAL_STORAGE_KEYS` constants.
- The Axios request interceptor attaches the access token.
- Non-auth `401` responses clear local auth data and redirect to `ROUTE_NAMES.LOGIN`.
- Role checks are handled through auth state and router metadata.

## Adding a New Feature

1. Add endpoint constants in `src/constants/api_endpoint.js`.
2. Add or update a service module in `src/services/`.
3. Add or update a Pinia store in `src/stores/` when shared state is needed.
4. Add route names in `src/constants/routes.js`.
5. Add route records under `src/router/routes/`.
6. Add page components under `src/pages/`.
7. For Figma/page builds, create a screen constants file under `src/constants/admin/` or `src/constants/user/` for static tabs, options, columns, fallback records, and sample data.

## What Not To Do

- Do not hardcode API URLs or route name strings.
- Do not keep page-level tabs, filter options, table columns, fallback records, sample screen data, or nav links inside components/pages.
- Do not call Axios directly from components or pages.
- Do not put business logic inside `components/elements/`.
- Do not duplicate existing reusable components.
- Do not use `$store` or Vuex patterns.
- Do not commit secrets, tokens, or environment-specific credentials.

## Build & Dev Commands

```bash
npm run dev          # Start Vite dev server
npm run build        # Production build
npm run preview      # Preview production build
npm run test:unit    # Vitest unit tests
npm run test:e2e     # Playwright end-to-end tests
npm run format       # Format src/ with Prettier
```
