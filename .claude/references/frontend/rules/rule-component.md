# Vue Component Creation Rules

Before creating any component:

1. Search existing components first.
2. Prefer reusable components in this order: `src/components/common` -> `src/components/elements` -> Nuxt UI/library components -> native HTML tags.
3. Do not duplicate similar components.
4. If UI differs only by status/type/variant, create one component with variant prop.
5. Do not use raw native controls such as `<button>`, `<input>`, `<select>`, or modal markup when a matching shared component exists.
6. Use native semantic HTML for document structure such as `section`, `header`, `main`, `article`, `ul`, `li`, `p`, and headings.
7. Use Vue 3 Composition API and `<script setup>`.
8. Define props with `defineProps`; use JSDoc typedefs when object shape clarity is needed.
9. Define emitted events with `defineEmits`.
10. Define slots if layout needs customization.
11. Keep component single responsibility.
12. Avoid API calls inside presentational components.
13. Avoid hard-coded business data inside components or pages.
14. Extract page-level static data to constants files. Admin screen data belongs in `src/constants/admin/<screen>.js`; user screen data belongs in `src/constants/user/<screen>.js`.
15. Extract reusable logic to composables.
16. Use PascalCase component names.
17. Use Base prefix for primitive components.
18. Use App/Common prefix for shared layout components.
19. Use feature folder for business-specific components.
20. Do not create new icons if existing project or UI library icons can be reused.
21. Match existing project style before introducing new style.
22. After implementation, provide a short component contract summary.
23. Avoid passing more than 6 props to a component.
24. If multiple props belong to the same domain entity, group them into an object prop.

## Constants Boundary

- Page-level tabs, filter options, table columns, fallback records, sample cards, nav links, and static screen lists must live in `src/constants/admin/` or `src/constants/user/` using screen-named files.
- Export constants with `UPPER_SNAKE_CASE` named exports only.
- Keep constants files free of Vue refs/computed, API calls, stores, router instances, service imports, and asset imports.
- Local constants are allowed for props validators, tiny component-private class maps, single-use derived config, and small arrays created inside functions for computation.
