# Styling Rules — Vue 3 + Tailwind CSS v4 + Nuxt UI

Project styling stack: **Tailwind CSS v4** + **Nuxt UI v4**. SCSS has been removed entirely.

---

## Rule 1 — Tailwind Utility Classes First

**Always reach for Tailwind utility classes before anything else.**

```vue
<!-- ✅ Correct -->
<div class="flex items-center gap-4 px-6 py-3 bg-white rounded-xl shadow-md">

<!-- ❌ Wrong — do not write custom CSS for this -->
<div style="display:flex; align-items:center; gap:16px">
```

- Layout → `flex`, `grid`, `items-center`, `justify-between`
- Spacing → `p-4`, `gap-2`, `mt-6`
- Typography → `text-sm`, `font-semibold`, `text-zinc-700`
- Color → `bg-sky-500`, `text-white`, `border-gray-200`
- State → `hover:bg-sky-600`, `focus:ring-2`, `disabled:opacity-50`
- Responsive → `md:flex-row`, `lg:text-xl` (mobile-first)

---

## Rule 2 — Do NOT Override Nuxt UI Component CSS Directly

Never target Nuxt UI internal classes with custom CSS. Use the **`:ui` prop** instead.

```vue
<!-- ✅ Correct — override via :ui prop -->
<UInput :ui="{ base: 'bg-stone-100 py-4 rounded-none' }" />

<!-- ❌ Wrong — never do this -->
<style>
.u-input input { background: #f5f5f4; }
</style>
```

The `:ui` prop accepts an object matching the component's slot structure. Check Nuxt UI docs for each component's available slots (`base`, `wrapper`, `leading`, `trailing`, etc.).

---

## Rule 3 — No `<style>` Blocks

**Do not add `<style>` or `<style scoped>` to any SFC.** All styling must be expressible via Tailwind classes.

```vue
<!-- ✅ Correct — no style block needed -->
<template>
  <div class="relative overflow-hidden rounded-2xl bg-white/80 backdrop-blur-md">
</template>

<!-- ❌ Wrong -->
<style scoped>
.card { backdrop-filter: blur(12px); background: rgba(255,255,255,0.8); }
</style>
```

**Exception (rare):** Custom `@keyframes` animations that Tailwind cannot express. If needed, add to `src/assets/css/main.css` using `@layer` — never inside a component.

---

## Rule 4 — Limit Global CSS

`src/assets/css/main.css` is the **only** place for global styles. Keep it minimal.

```css
/* src/assets/css/main.css */
@import "tailwindcss";   /* includes Preflight reset */
@import "@nuxt/ui";

/* Only truly global things below */
@layer base {
  /* Custom scrollbar, selection color, etc. */
}
```

**Never add component-specific styles here.** If a style only applies to one component, it should be expressible via Tailwind classes in that component's template.

---

## Rule 5 — Use Nuxt UI Design Tokens

Nuxt UI exposes CSS variables for colors, radius, and shadows. Use them via Tailwind or the `:ui` prop rather than hardcoding values.

```vue
<!-- ✅ Use semantic Tailwind colors that map to Nuxt UI tokens -->
<UButton color="primary" />
<UBadge color="success" />

<!-- ❌ Avoid hardcoding colors not in the Tailwind theme -->
<div class="bg-[#0ea5e9]">   <!-- only use arbitrary values when necessary -->
```

Prefer Tailwind palette colors (`sky-500`, `violet-600`, `zinc-900`) over arbitrary hex values. Arbitrary values (`bg-[#hex]`) are acceptable only for brand colors not in the default palette.

---

## Rule 6 — No Mixed CSS Systems

Use **one system per project**. Do not mix:

| System | Status |
|--------|--------|
| `@/components/elements/` Base* components | ✅ **Priority 1A** — always check first |
| `@/components/common/` Common* components | ✅ **Priority 1B** — check before building new |
| Nuxt UI `U*` components | ✅ **Priority 2** — when no Base*/Common* exists |
| Tailwind CSS v4 utility classes | ✅ **Priority 3** — for all layout and styling |
| Nuxt UI `:ui` prop overrides | ✅ Use to customize Nuxt UI internals |
| `src/assets/css/main.css` `@layer` | ✅ Use (sparingly, truly global only) |
| SCSS / Sass | ❌ Removed — do NOT add back |
| Inline `style="..."` | ❌ Forbidden |
| CSS Modules (`.module.css`) | ❌ Forbidden |
| `<style>` blocks in SFC | ❌ Forbidden |
| `@apply` in any file | ❌ Forbidden |

---

## Rule 7 — Standard Vue + Tailwind SFC Structure

```vue
<script setup>
// imports, props, logic only
</script>

<template>
  <!-- All styling via Tailwind classes -->
</template>

<!-- NO <style> block -->
```

**Class organization order** (for readability):

```
layout → sizing → spacing → typography → colors → borders → effects → state → responsive
```

Example:
```vue
<div class="flex flex-col w-full max-w-md gap-6 px-8 py-10 text-sm text-zinc-700 bg-white border border-gray-200 rounded-2xl shadow-xl hover:shadow-2xl md:flex-row">
```

---

## Rule 8 — Dynamic Classes via Computed / Object Syntax

For conditional styling, use object syntax or computed strings — not `<style>` blocks.

```vue
<!-- ✅ Object syntax -->
<div :class="{ 'opacity-50 pointer-events-none': isDisabled, 'ring-2 ring-red-500': hasError }">

<!-- ✅ Computed ref -->
<script setup>
const inputClass = computed(() =>
  error.value ? 'border-red-500 bg-red-50' : 'border-gray-200 bg-white'
)
</script>

<!-- ❌ Wrong — do not use <style> for conditional states -->
```

---

## Rule 9 — Responsive Design (Mobile-First)

Always write mobile styles first, then add `md:` / `lg:` overrides.

```vue
<!-- ✅ Mobile-first -->
<div class="flex flex-col gap-4 md:flex-row md:gap-8">

<!-- ❌ Do not design desktop-first -->
<div class="flex flex-row gap-8 max-md:flex-col">
```

Standard breakpoints: `sm` (640px) · `md` (768px) · `lg` (1024px) · `xl` (1280px)

---

## Rule 10 — Icons

**Priority order:**

1. **`src/assets/icons/Icon*.vue`** — always check first. Available: `IconArrow`, `IconAvatar`, `IconBell`, `IconCalendar`, `IconEye`, `IconEyeOff`, `IconHexagon`, `IconLock`, `IconMail`, `IconPhone`, `IconUser`
2. **`<UIcon name="i-heroicons-*">`** — when no asset icon matches. **Infer** the closest name:

| Need | Heroicons name |
|------|----------------|
| envelope / email | `i-heroicons-envelope` |
| lock / password | `i-heroicons-lock-closed` |
| eye / show | `i-heroicons-eye` |
| eye-off / hide | `i-heroicons-eye-slash` |
| user / profile | `i-heroicons-user` |
| phone | `i-heroicons-phone` |
| calendar / date | `i-heroicons-calendar-days` |
| search | `i-heroicons-magnifying-glass` |
| close / x | `i-heroicons-x-mark` |
| check | `i-heroicons-check` |
| arrow right | `i-heroicons-arrow-right` |
| chevron down | `i-heroicons-chevron-down` |
| bell / notification | `i-heroicons-bell` |
| home | `i-heroicons-home` |
| settings | `i-heroicons-cog-6-tooth` |
| logout | `i-heroicons-arrow-right-on-rectangle` |
| plus / add | `i-heroicons-plus` |
| edit / pencil | `i-heroicons-pencil` |
| delete / trash | `i-heroicons-trash` |
| upload | `i-heroicons-arrow-up-tray` |
| download | `i-heroicons-arrow-down-tray` |

3. **Create new** `src/assets/icons/IconName.vue` — only if neither above covers the icon

```vue
<!-- ✅ Custom project icon -->
<IconMail class="size-4 text-gray-400" />

<!-- ✅ Nuxt UI icon fallback (infer name) -->
<UIcon name="i-heroicons-envelope" class="size-4 text-gray-400" />

<!-- ❌ Never inline raw SVG in templates -->
```

Icons inherit color via `text-*` classes (`currentColor`). Size via `size-4` (`w-4 h-4`).

---

## Quick Reference Cheatsheet

| Need | Solution |
|------|----------|
| UI element (button, input, card…) | Check `@/components/elements/` first → Nuxt UI → raw HTML |
| Page-level block (modal, card list…) | Check `@/components/common/` first → build new if absent |
| Layout / spacing | Tailwind utility classes |
| Override Nuxt UI internals | `:ui="{ slot: 'classes' }"` prop |
| Icon | `src/assets/icons/` → `<UIcon name="i-heroicons-*">` → create new |
| Animation | `animate-*` Tailwind class → if complex, `@layer` in `main.css` |
| Global reset | Tailwind Preflight (auto via `@import "tailwindcss"`) |
| Conditional class | `:class` object syntax or computed |
| Component-specific style | Tailwind classes inline — no `<style>` block |
| Custom color not in palette | `bg-[#hex]` arbitrary value |
