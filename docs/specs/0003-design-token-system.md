# 0003: CSS Design Token System and Icon Library

Status: ✅ accepted

## Outcome

> 2026-06-27 amendment: TaskPilot now inherits base visual identity from the Agent Manifesto design
> system. The token system remains the production source of truth, but the base accent, typography,
> and radii now use the parent design system values plus TaskPilot-specific dark/status extensions.

Replace all hardcoded color, spacing, radius, shadow, and typography values in the web frontend
with a single CSS custom-property token file (`web/src/tokens.css`). Add light and dark themes that
switch automatically by OS preference and can be overridden by a `data-theme` attribute on `<html>`.
Replace Unicode glyph characters in JSX with a thin wrapper over `lucide-react` icons. All changes
are purely presentational — no domain rules, REST contracts, or canonical file formats change.

## Context

The web frontend (`web/src/`) has ~50 hardcoded hex values scattered across 9 CSS Module files and
`index.css`. Colors, spacing, radii, and shadows are duplicated with no shared reference. There is
no dark-mode support. Item-type icons are Unicode glyphs embedded as string literals, which are
inaccessible and visually inconsistent.

This spec covers only the Alpha UI visual layer. It does not add a theme-toggle control, change
layout or interaction behavior, or introduce new screens.

## Scope

**In scope:**
- `web/src/tokens.css` — 57 semantic CSS custom properties, light defaults, dark overrides.
- `web/src/index.css` — import tokens; replace 4 hardcoded values.
- All 9 `web/src/components/*.module.css` files — replace hardcoded values with token references.
- `web/package.json` — add `lucide-react` dependency.
- `web/src/components/ui/Icon.tsx` — accessible icon wrapper.
- `web/src/components/KanbanCard.tsx` — replace 4 Unicode type-icon glyphs with `<Icon>`.
- `web/src/components/ItemModal.tsx` — replace `×` close button with `<Icon icon={X}>`.

**Out of scope:**
- Theme-toggle UI control (no `ThemeProvider`, no toggle button in this spec).
- New screens, layout changes, or interaction behavior changes.
- Tailwind, CSS-in-JS, or any styling methodology change.
- Changes to REST API, domain model, CLI, or canonical files.

## Requirements

### Functional

F1. `web/src/tokens.css` defines all 57 tokens in `:root` (light defaults) and overrides
theme-sensitive tokens in `@media (prefers-color-scheme: dark) { :root { } }`.

F2. Explicit `[data-theme="dark"]` on `<html>` applies dark tokens regardless of OS preference.
Explicit `[data-theme="light"]` on `<html>` applies light tokens regardless of OS preference.

F3. No CSS Module file or `index.css` contains a hardcoded hex color, hardcoded rgba color,
hardcoded spacing rem value with a direct visual-system meaning, hardcoded border-radius px value,
or hardcoded box-shadow value after migration. Sub-token micro-padding literals (`0.125rem`,
`0.375rem`) used only for badge internal padding are exempt.

F4. `Icon.tsx` accepts an `icon` prop (Lucide component type), optional `size` (default `16`),
and optional `label` (string). When `label` is present the rendered SVG has `aria-label={label}`
and `aria-hidden="false"`. When `label` is absent the SVG has `aria-hidden="true"`.

F5. `KanbanCard.tsx` uses `<Icon>` for the four item-type icons (epic, feature, task, bug). Each
icon has an `aria-label` set to the type name.

F6. `ItemModal.tsx` uses `<Icon icon={X} label="Close" />` for the modal close button.

F7. All existing component tests pass without modification to test assertions.

### Quality

Q1. All foreground/background token pairs used in production meet WCAG AA contrast: 4.5:1 for
normal text (< 18px / < 14px bold), 3:1 for large text.

Q2. Dark-mode token values for status and priority badges meet the same contrast requirement on
their respective dark background tokens.

Q3. Type check (`tsc --noEmit`) and lint (`oxlint`) pass with zero errors after migration.

Q4. `lucide-react` is tree-shaken — only imported icon symbols are included in the bundle. No
`import * from 'lucide-react'` usage.

## Design

### Domain and invariants

None. This spec touches only the presentation layer. `ItemType`, `Priority`, `Status` enums and
their label mappings in `web/src/types/` are unchanged.

### Canonical file effects

None. No `.taskpilot/` files, no SQLite schema, no server routes.

### CLI / API contracts

None changed.

### UI states

All existing UI states (loading, empty, populated, error, invalid item, drag-in-progress, modal
open/edit/delete-confirm) continue to render. The visual output changes (token-sourced colors, icon
SVGs instead of glyphs) but state behavior does not change.

Dark-mode rendering: all states that exist in light mode must also render coherently in dark mode.
No new states are introduced.

## Acceptance Criteria

**AC-1 (token coverage):** After migration, running
`grep -rn "#[0-9a-fA-F]\{3,6\}" web/src/components/ web/src/index.css` returns zero matches.

**AC-2 (token count):** `web/src/tokens.css` defines exactly the 57 tokens listed in the approved
plan, including `--brand-accent` and `--radius-pill`. Each token appears in `:root` and, for
theme-sensitive tokens, in the dark override block.

**AC-3 (dark theme auto-switch):** When a Playwright test sets
`page.emulateMedia({ colorScheme: 'dark' })` and navigates to the board, the computed value of
`--surface-app` on `<html>` equals `#111113`.

**AC-4 (dark theme explicit override):** When a Playwright test sets `data-theme="dark"` on
`document.documentElement`, the computed value of `--surface-app` equals `#111113` regardless of
the media query value.

**AC-5 (light theme explicit override):** When a Playwright test sets `data-theme="light"` on
`document.documentElement` while OS preference is dark, the computed value of `--surface-app`
equals `#f8fafc`.

**AC-6 (icon accessibility — label present):** Rendering `<Icon icon={Layers} label="epic" />`
produces an SVG element with `aria-label="epic"` and `aria-hidden="false"`.

**AC-7 (icon accessibility — decorative):** Rendering `<Icon icon={Layers} />` produces an SVG
element with `aria-hidden="true"` and no `aria-label` attribute.

**AC-8 (icon size default):** Rendering `<Icon icon={Layers} />` without a `size` prop produces
an SVG with `width="16"` and `height="16"`.

**AC-9 (KanbanCard type icons):** The KanbanCard component renders a Lucide SVG (not a text node
with a Unicode character) for each of the four item types. Each SVG has `aria-label` equal to the
type name string.

**AC-10 (ItemModal close button):** The close button in `ItemModal` renders a Lucide X icon SVG
with `aria-label="Close"`.

**AC-11 (no regressions):** All existing Vitest component tests pass after migration.

**AC-12 (type check):** `tsc --noEmit` in `web/` exits with code 0.

**AC-13 (lint):** `oxlint` in `web/` exits with code 0 or reports only pre-existing warnings.

## Test Strategy

| Area | Level | Rationale |
|---|---|---|
| `Icon.tsx` props contract | Component (Vitest) | Props determine accessibility contract; testable with jsdom |
| Token CSS custom properties on `:root` | Component (Vitest + `getComputedStyle`) | Verify tokens load in jsdom document |
| Dark theme token override | E2E (Playwright) | `prefers-color-scheme` emulation requires a real browser |
| Explicit `data-theme` override | E2E (Playwright) | Same — requires computed style in real browser |
| KanbanCard type icons (no Unicode glyphs) | Component (Vitest) | Verify rendered SVG presence and aria-label |
| ItemModal close icon | Component (Vitest) | Verify aria-label on close button icon |
| No regressions | Component (Vitest) | Run full existing suite after each module migration |

Pre-migration: capture Playwright baseline screenshots of the board in light mode before any CSS
change. Post-migration: compare against baseline and confirm no layout shift; capture dark-mode
screenshots as new evidence.

## Implementation Slices

Slice 1 — Token file + index.css:
- Create `web/src/tokens.css` with all 57 tokens (light + dark).
- Add `@import './tokens.css';` as first line of `web/src/index.css`.
- Replace 4 hardcoded values in `index.css`.
- Observable: `getComputedStyle(document.documentElement).getPropertyValue('--accent')` returns a non-empty string in jsdom tests.

Slice 2 — CSS Module migration (9 files):
- Migrate in order: `SortableKanbanCard` → `CommentThread` → `ProjectSelector` → `KanbanBoard` → `KanbanColumn` → `DeleteConfirmDialog` → `KanbanCard` → `ItemEditForm` → `ItemModal`.
- Run `vitest run` after each file. All tests must pass before proceeding.
- Observable: grep returns zero hex matches in each migrated file.

Slice 3 — Icon library:
- `npm install lucide-react` in `web/`.
- Create `web/src/components/ui/Icon.tsx`.
- Write component tests for AC-6, AC-7, AC-8.
- Observable: `Icon.tsx` tests pass.

Slice 4 — Component icon replacements:
- Update `KanbanCard.tsx` (4 type icons).
- Update `ItemModal.tsx` (close button).
- Observable: KanbanCard and ItemModal component tests verify SVG presence and aria-labels.

Slice 5 — Final validation:
- Run full Vitest suite — zero failures.
- Run `tsc --noEmit` — zero errors.
- Run `oxlint` — zero new errors.
- Run Playwright: light-mode board screenshot + dark-mode board screenshot.
- Observable: AC-1 through AC-13 all satisfied.

## Risks and Compatibility

R1 — CSS specificity: CSS custom properties on `:root` may be overridden by inline styles or
more-specific selectors in existing modules. Migration must verify computed values in the browser
rather than assuming the token is in effect.

R2 — jsdom CSS limitations: jsdom does not support `@media (prefers-color-scheme)`. Dark-mode token
tests must use Playwright, not Vitest/jsdom. Do not write jsdom assertions for media-query behavior.

R3 — lucide-react bundle size: Lucide ships ~1500 icons. All imports must be named (e.g.,
`import { Layers } from 'lucide-react'`), never namespace imports, to ensure tree-shaking works in
the Vite build.

R4 — Existing snapshot tests: There are no snapshot tests in the current suite. If snapshots are
added during this work, they must be committed alongside the implementation.

R5 — `0.6875rem` font-size: used for type and priority badges, this value falls between the two
defined typography tokens (`--font-size-sm: 0.8125rem` and `--font-size-base: 0.875rem`). It stays
as a literal (badge-specific micro-value); no token is added.

## Assumptions

A1. The two typography tokens (`--font-size-sm`, `--font-size-base`) cover all tokenized font-size
usage. The `0.6875rem`, `0.75rem`, `1.25rem`, and `1.125rem` values used for badges and modal
headings remain as literals because they appear in one place each and are not part of the shared
visual rhythm.

A2. No JS theme-toggle control is in scope for this spec. The `data-theme` attribute is set
manually in tests and can be wired to a future toggle without changing the token contract.

A3. `#e0e0e0` in `index.css` (header `border-bottom`) maps to `--border-subtle` (`#e5eaf0`). The
visual difference is imperceptible; no new token is added.

A4. The `filter: brightness(0.9)` approach for delete-button hover state is acceptable CSS because
the danger color at hover is not a distinct semantic concept requiring its own token.

## Open Questions

None. All decisions resolved by the approved plan.
