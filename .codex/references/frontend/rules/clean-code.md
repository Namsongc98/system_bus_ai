# JavaScript Clean Code Rules

1. Functions must have a single responsibility.
2. Keep functions short and easy to understand.
3. Use meaningful and intention-revealing names.
4. Avoid boolean flag arguments that change behavior.
5. Avoid functions with multiple modes or responsibilities.
6. Prefer early returns over deep nested conditions.
7. Avoid duplicated logic; extract reusable utilities.  
8. Do not hardcode magic strings or magic numbers.
9. Group strongly related parameters into objects.
10. Avoid passing more than 5-6 parameters to a function.
11. Keep modules focused on one concern.
12. Separate business logic from infrastructure and UI logic.
13. Prefer pure functions when possible.
14. Avoid hidden side effects and implicit mutations.
15. Do not mutate function arguments unless explicitly required.
16. Handle async flows explicitly with proper error handling.
17. Avoid large utility files with unrelated helpers.
18. Keep data flow predictable and explicit.
19. Use constants and enums for shared conditional logic.
20. Remove dead code, unused variables, and commented-out code.
21. Prefer composition over large monolithic abstractions.
22. Avoid premature abstraction and unnecessary generic code.
23. Keep public APIs small, stable, and predictable.
24. Validate inputs at system boundaries.
25. Prefer readability and maintainability over short clever code.

## Screen Constants

- Repeated options, table columns, nav links, fallback records, sample screen data, and static Figma-derived lists are constants, not component logic.
- Put admin screen constants in `src/constants/admin/<screen>.js` and user screen constants in `src/constants/user/<screen>.js`.
- Do not move service calls, normalizers, computed values, event handlers, or component-private visual class maps into constants files.
