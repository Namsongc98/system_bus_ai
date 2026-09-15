# Component Reuse Patterns

Use this reference with the `reuse-component` skill when creating or refactoring reusable Vue components.

## Pattern A — Primitive Element

Use for a single reusable UI primitive in `src/components/elements/`, such as a button, input, segmented control, badge, avatar, or card shell.

- File path: `src/components/elements/BaseName.vue`.
- Component name: PascalCase with `Base` prefix.
- No Pinia, services, router, or business logic.
- Use `defineOptions({ inheritAttrs: false })` and bind `$attrs` on the root interactive or wrapper element when useful.
- Expose state through props and user interaction through emits.
- Use Nuxt UI internally only when it provides the primitive behavior.

## Pattern B — Common Composed Component

Use for reusable UI blocks in `src/components/common/` that compose several primitives, such as forms, cards, modals, maps, ticket cards, or search blocks.

- File path: `src/components/common/BaseName.vue`.
- Compose existing `Base*` elements first.
- No direct API calls, Pinia stores, or route navigation.
- Parent pages own workflow state and pass data down.
- Emit user intent upward, such as `submit`, `select`, `close`, `reset`, or `update:modelValue`.

## Placement Rules

| Need | Folder |
|---|---|
| Stateless primitive | `src/components/elements/` |
| Reusable composed UI block | `src/components/common/` |
| Header, footer, sidebar shell | `src/components/layout/` |
| Full route wrapper | `src/layouts/` |
| Route-level workflow screen | `src/pages/` |

## Props Inference

| Figma or markup signal | Prop shape |
|---|---|
| Text that changes by data | named `String` prop or grouped object prop |
| Numeric value | named `Number` prop or grouped object prop |
| Related domain fields | one object prop, e.g. `ticket`, `trip`, `user` |
| Selected/active state | `modelValue` or `selected` |
| Option list | `options: Array` |
| Visual variant | `variant`, `type`, `status`, or `size` string |
| Loading state | `loading: Boolean` |
| Disabled state | `disabled: Boolean` |

Avoid more than 5-6 unrelated props. Group strongly related data into an object prop.

## Emits Inference

| User action | Emit |
|---|---|
| Input value changes | `update:modelValue` |
| Form submit | `submit` or domain-specific verb |
| Search | `search` |
| Reset or clear | `reset` |
| Select item | `select` with selected item/value |
| Open/close | `open`, `close`, or `update:modelValue` |
| Delete/cancel | `delete`, `cancel`, or domain-specific verb |

## Slots Inference

| Flexible region | Slot |
|---|---|
| Main content | `default` |
| Leading icon/content | `leading` or `icon-left` |
| Trailing icon/content | `trailing` or `icon-right` |
| Header area | `header` |
| Footer/actions area | `footer` or `actions` |

Only add slots when the parent needs customization.

## Conversion Rules

- Scan existing components before creating a new one.
- Preserve the design intent, not Figma wrapper noise.
- Remove `data-*` Figma attributes and inline styles.
- Replace absolute positioning with flex/grid unless absolute positioning is truly required.
- Keep accessibility: labels, `alt`, explicit button types, keyboard-friendly controls.
- Prefer Tailwind utilities and project components over custom CSS.
