# Page Integration Patterns

Use this reference with `figma-to-vue` and `reuse-component` when composing a page from Figma markup or existing components.

## Workflow

1. Identify the target page, route, and layout.
2. Read the current route module and route name constants.
3. Scan `src/components/elements/` and `src/components/common/` for reusable blocks.
4. Replace matching Figma blocks with existing Base/Common components.
5. Map remaining simple UI to Nuxt UI or semantic HTML with Tailwind classes.
6. Keep page-level state, store calls, navigation, loading, errors, and empty states in the page.
7. Pass data down through props and handle child emits in page functions.

## Component Replacement Priority

1. Existing `src/components/elements/Base*.vue` primitives.
2. Existing `src/components/common/*.vue` composed components.
3. Nuxt UI components.
4. Semantic HTML plus Tailwind utilities.

## Wiring Hints

- Search form emit -> store fetch action.
- Card/list item select emit -> router navigation or selected state update.
- Modal close emit -> local open state update.
- Sort/filter `update:modelValue` -> local ref or query/store update.
- Submit emit -> store mutation action followed by refresh or navigation.

## Page State Checklist

- Loading state for initial fetch or user-triggered async work.
- Error state with visible feedback.
- Empty state for no data.
- Success state or list/detail rendering.
- Route params/query handling when the URL controls data.
- Cleanup/reset behavior when leaving or reusing the page.

## Page Boundaries

- Pages may import stores, composables, router, services only through existing architecture patterns.
- Common and element components should not import page stores or router.
- Do not hardcode route names; use `ROUTE_NAMES`.
- Do not hardcode API URLs; use service/store layers.

## Output Expectations

- A complete SFC or patch to the target page.
- Short wiring summary naming placed components and event handlers.
- TODO list only for intentionally deferred backend or product decisions.
