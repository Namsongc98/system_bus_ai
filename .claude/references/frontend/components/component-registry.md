# Component Registry

Concise registry of reusable project components. Always inspect the actual component file before relying on details here.

## Elements

| Component | Path | Key props | Emits |
|---|---|---|---|
| `BaseAvatar` | `@/components/elements/BaseAvatar.vue` | inspect file | inspect file |
| `BaseBell` | `@/components/elements/BaseBell.vue` | inspect file | inspect file |
| `BaseButton` | `@/components/elements/BaseButton.vue` | `label`, `type`, `size`, `loading`, `block`, `htmlType`, `unstyled` | `click` |
| `BaseCard` | `@/components/elements/BaseCard.vue` | `shadow`, `padding`, `rounded`, `hoverable` | slot-based |
| `BaseInput` | `@/components/elements/BaseInput.vue` | `modelValue`, `type`, `label`, `placeholder`, `error`, `disabled`, `required`, `size`, `color`, `variant`, `ui` | `update:modelValue`, `blur` |
| `BaseSortFilter` | `@/components/elements/BaseSortFilter.vue` | `modelValue`, `options`, `label`, `disabled` | `update:modelValue` |
| `BaseTabs` | `@/components/elements/BaseTabs.vue` | `modelValue`, `options`, `disabled`, `ariaLabel` | `update:modelValue`, `change` |

## Common

| Component | Path | Key props | Emits |
|---|---|---|---|
| `BaseFormSelectPayment` | `@/components/common/BaseFormSelectPayment.vue` | inspect file | inspect file |
| `BaseMapCar` | `@/components/common/BaseMapCar.vue` | inspect file | inspect file |
| `BaseModal` | `@/components/common/BaseModal.vue` | inspect file | inspect file |
| `BaseSavePaymentForm` | `@/components/common/BaseSavePaymentForm.vue` | inspect file | inspect file |
| `BaseSearchForm` | `@/components/common/BaseSearchForm.vue` | `loading`, `initialValues` | `search`, `reset` |
| `BaseTicketCard` | `@/components/common/BaseTicketCard.vue` | `ticket`, `actionLabel`, `disabled` | `view-pass`, `expand` |
| `BaseTripCard` | `@/components/common/BaseTripCard.vue` | inspect file | inspect file |
| `ToastContainer` | `@/components/common/ToastContainer.vue` | none | none |

## Icons

Project icons live in `src/assets/icons/Icon*.vue`. Check this folder before using `UIcon` or creating a new icon.
