# Folder Structure — Key Conventions

This file describes the current source layout for the Vue booking-ticket frontend.

```text
src/
├── App.vue
├── main.js
├── __tests__/                 # Vitest unit tests
├── assets/
│   ├── css/
│   │   └── main.css           # Tailwind and Nuxt UI imports plus minimal global CSS
│   ├── icons/                 # Icon*.vue components
│   └── image/                 # Image assets processed by Vite
├── components/
│   ├── elements/              # Stateless Base* primitives
│   │   ├── BaseAvatar.vue
│   │   ├── BaseBell.vue
│   │   ├── BaseButton.vue
│   │   ├── BaseCard.vue
│   │   ├── BaseInput.vue
│   │   ├── BaseSortFilter.vue
│   │   └── BaseTabs.vue
│   ├── common/                # Reusable composed UI blocks
│   │   ├── BaseFormSelectPayment.vue
│   │   ├── BaseMapCar.vue
│   │   ├── BaseModal.vue
│   │   ├── BaseSavePaymentForm.vue
│   │   ├── BaseSearchForm.vue
│   │   ├── BaseTicketCard.vue
│   │   ├── BaseTripCard.vue
│   │   └── ToastContainer.vue
│   └── layout/                # App shell components
│       ├── admin/
│       └── user/
├── composables/               # Reusable Composition API logic
├── constants/
│   ├── api_endpoint.js        # API_ENDPOINTS and API base URLs
│   ├── admin/                 # Admin screen constants: tabs, options, columns, fallback data
│   ├── index.js
│   ├── routes.js              # ROUTE_NAMES and ROUTE_PATHS
│   └── user/                  # User screen constants: nav links, options, sample/fallback data
├── errors/
├── layouts/                   # Full page route layouts
├── pages/
│   ├── admin/
│   ├── auth/
│   ├── user/
│   │   ├── MyTickets.vue
│   │   ├── ProfileView.vue
│   │   ├── QRConfirmPopup.vue
│   │   ├── SeatView.vue
│   │   └── TripView.vue
│   └── NotFoundPage.vue
├── router/
│   ├── guards.js
│   ├── index.js
│   └── routes/
├── services/                  # Axios-backed API service modules
├── stores/                    # Pinia setup stores by domain
├── types/                     # JSDoc typedefs
└── utils/                     # Pure helpers and storage utilities
```

## Placement Rules

- Put route-level workflow screens in `src/pages/`.
- Put reusable primitive controls in `src/components/elements/`.
- Put composed reusable UI blocks in `src/components/common/`.
- Put app shell UI in `src/components/layout/` and full route wrappers in `src/layouts/`.
- Put API access in `src/services/`; do not call Axios from components.
- Put shared route names and API endpoints in `src/constants/`.
- Put admin page-level static data in `src/constants/admin/<screen>.js`.
- Put user page-level static data in `src/constants/user/<screen>.js`.
- Constants files should export named `UPPER_SNAKE_CASE` values and must not import Vue, stores, services, router instances, or assets.
- Put images, icons, and CSS entry files under `src/assets/`.
