# Local WebUI Component Library Standard

## Purpose

This convention defines how TaskPilot agents implement, maintain, update, and reuse the local WebUI
component library.

The local WebUI implementation is the canonical component library. Open Design prototypes and OD
component libraries are optional reference material unless the active route is an Open Design
route.

## Source of Truth

Use this order for production UI implementation decisions:

1. `web/src/tokens.css`
2. reusable React components under `web/src/components/`
3. component CSS modules colocated with those components
4. local component examples, previews, and tests
5. `designs/design.md` and `docs/design.md`
6. OD prototypes and OD component libraries, only when the user explicitly requests OD
   exploration, visual alternatives, OD design-system synchronization, or OD-to-code translation

Do not translate OD HTML/CSS into production code as a mechanical source of truth. Treat OD output
as visual reference unless the active route is `.claude/pipelines/od-to-code.md`.

## Component Reuse

- Prefer updating or extending an existing component before creating a new one.
- Extract a reusable component when the same UI pattern appears in two or more production places,
  or when a component has meaningful behavior, state, accessibility, or layout rules.
- Before adding or changing an interactive control, inventory existing controls in
  `web/src/components/` that solve the same job. If a matching pattern exists, reuse it or record
  why the new behavior must diverge.
- Replacing a native browser control with a custom control is allowed only when the required
  product behavior cannot be guaranteed by the native control, such as deterministic menu
  placement, shared selected-state styling, or consistent option highlighting.
- Keep one-off page composition inside the page until reuse is real.
- Keep component APIs small and domain-oriented.
- Keep domain and persistence rules out of UI components.
- Preserve desktop-only and local-only product constraints unless a user-approved product decision
  changes them.

## UI Interaction Contracts

Reusable interaction patterns must define their user-visible contract before implementation. At
minimum, document or test:

- trigger label, selected value display, icon/arrow state, and disabled state;
- open, hover, selected, focus-visible, empty, and error states where applicable;
- menu or popover placement and whether native browser placement is acceptable;
- close behavior on selection, blur, Escape, and view/project changes;
- keyboard path and accessible roles/names;
- reset/default behavior for controls with filters or temporary state;
- consistency with nearby controls that perform the same job.

For current TaskPilot UI, dropdown-style selectors share the same button, arrow, below-menu,
selected highlight, hover, focus, and option behavior. Dimensions may vary by context, but
interaction behavior and state styling should not silently fork.

## Tokens And Styling

- Use design tokens from `web/src/tokens.css` for colors, spacing, radii, typography, shadows, and
  shared layout constants.
- Do not hardcode token-owned values unless the value is truly component-private.
- If a required token is missing, update `designs/design.md`, `docs/design.md`, and
  `web/src/tokens.css` together before using it.
- Keep component CSS modules colocated with the component they style.
- Reuse established layout patterns before introducing a new layout primitive.

## Examples And Previews

- Add or update a local preview or example when a new shared component is used by two or more
  pages, or when a shared component changes state, accessibility behavior, layout behavior, or
  public props.
- A preview is optional for page-local changes and shared component refinements that do not change
  state, accessibility behavior, layout behavior, or public props.
- Do not add Storybook, a separate package, visual-regression tooling, or another component-library
  runtime without explicit user approval.

## Testing

- Add or update tests for shared components when behavior, accessibility, token usage, layout
  contracts, or cross-page reuse changes.
- Use `.claude/conventions/testing.md` to choose the lowest sufficient level.
- Prefer component tests for component behavior and CSS/token contract tests for layout invariants.
- Use Playwright evidence for major UI paths, browser-only behavior, drag/drop, keyboard journeys,
  or responsive behavior that lower-level tests cannot prove.
