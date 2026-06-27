# TaskPilot Design System

Implementation: `web/src/tokens.css`. This file is the single source of truth for all design
decisions — tokens, principles, patterns, states, and MCP tool constraints. All AI agents and
pipelines read this file; `docs/design.md` covers screen-level UX flows and is a companion, not
a duplicate. TaskPilot inherits its base visual language from the Agent Manifesto design system
and extends it with local-first product UI tokens for status, priority, feedback, dark theme, and
dense developer workflows.

---

## Product Experience

TaskPilot is a local developer tool for inspecting and changing structured work shared with AI
agents. The interface prioritizes fast scanning, explicit system state, keyboard use, and
Git-friendly transparency over dashboard decoration.

---

## Core Patterns

- Use a list or table as the primary scanning surface.
- Use a detail page or side panel for one item's content, metadata, links, and comments.
- Show validation close to the affected field and preserve visibility of invalid source files.
- Show statuses and relationship types with text; color may reinforce meaning but cannot own it.
- Keep destructive actions explicit and confirm effects that can remove canonical data.
- Keep domain rules and filesystem behavior outside UI components.

---

## Required States

Every applicable product flow accounts for:

- loading;
- empty results;
- recoverable error;
- invalid canonical file;
- missing or broken relation;
- unsaved or conflicting change;
- completed success state;
- narrow-screen layout.

---

## Accessibility Baseline

- All controls have accessible names.
- Keyboard order follows the visible task flow.
- Focus remains visible and moves deliberately after dialogs, drawers, and create actions.
- Native controls and accessible primitives are preferred.
- Status, priority, validation, and relationship meaning never depend on color alone.

**Contrast requirement:** all foreground/background token pairs used in production must meet
WCAG AA: 4.5:1 for normal text (< 18pt / 14pt bold), 3:1 for large text. See
`docs/specs/0003-design-token-system.md`.

---

## Responsive Baseline

- Desktop layouts optimize for scanning and side-by-side context.
- Narrow layouts preserve the primary action and item identity before secondary metadata.
- Tables may become stacked rows only when column meaning remains explicit.

---

## Visual Direction

- Agent Manifesto base identity: slate canvas, navy text, terracotta accent, Inter typography,
  explicit structure, restrained borders, and clear type hierarchy.
- Consistent spacing and density suitable for developer tools.
- Motion is limited to opacity and transforms that clarify state changes.
- Avoid glass effects, decorative gradients, dashboard-card overload, and hidden hover-only state.

**Token rule:** all production CSS must use tokens from `web/src/tokens.css`. No hardcoded hex,
rgba, rem, px radius, or box-shadow values in `web/src/components/*.module.css` or
`web/src/index.css`. Sub-token micro-padding literals (`0.125rem`, `0.375rem`) used only for
badge internal padding are the sole exemption.

**Theme switching:** light defaults live in `:root`. Dark overrides live in
`@media (prefers-color-scheme: dark) :root`. Explicit `[data-theme="light"]` and
`[data-theme="dark"]` attributes on `<html>` override OS preference. `[data-theme="light"]`
must explicitly declare every token that the dark `@media` block overrides, to prevent dark
values from persisting in forced-light mode.

---

## Color Tokens

Theme-aware. Light theme is the default; dark activates via `prefers-color-scheme: dark` or `[data-theme="dark"]`.
Agent Manifesto is light-only; TaskPilot adds dark tokens as a product-specific extension.

### Surface

| Token | Light | Dark | Usage |
|---|---|---|---|
| `--surface-app` | `#f8fafc` | `#111113` | Page background — inherited Agent Manifesto background |
| `--surface-base` | `#ffffff` | `#1c1c1e` | Card, panel background |
| `--surface-raised` | `#ffffff` | `#2c2c2e` | Modal, popover (elevated) |
| `--surface-overlay` | `rgba(0,0,0,0.5)` | `rgba(0,0,0,0.7)` | Modal backdrop |
| `--surface-muted` | `#f1f5f9` | `#28282a` | Inset / de-emphasized area |
| `--surface-column` | `#e5eaf0` | `#2c2c2e` | Kanban column background |

### Border

| Token | Light | Dark | Usage |
|---|---|---|---|
| `--border-subtle` | `#e5eaf0` | `#3a3a3c` | Dividers, row separators — inherited Agent Manifesto border |
| `--border-default` | `#d9e2ec` | `#48484a` | Input, card borders |
| `--border-strong` | `#9fb3c8` | `#636366` | Focus rings, emphasized edges |

### Text

All pairs verified WCAG AA (≥ 4.5:1) on `--surface-base` in both themes.

| Token | Light | Dark | Contrast (light) | Usage |
|---|---|---|---|---|
| `--text-primary` | `#102a43` | `#f5f5f7` | ≫ 10:1 | Body text, headings — inherited Agent Manifesto foreground |
| `--text-secondary` | `#486581` | `#aeaeb2` | ~7.7:1 | Secondary labels — inherited Agent Manifesto muted |
| `--text-muted` | `#5d7892` | `#8e8e93` | ~4.6:1 | Timestamps, hints |
| `--text-disabled` | `#9fb3c8` | `#48484a` | decorative | Disabled controls (not content) |
| `--text-inverse` | `#ffffff` | — | — | Text on dark/colored surfaces |

### Accent

| Token | Light | Dark | Usage |
|---|---|---|---|
| `--brand-accent` | `#c65d2e` | `#c65d2e` | Agent Manifesto brand swatch; use for non-text marks and borders |
| `--accent` | `#a94a22` | `#e08a5d` | Primary action, link, in-progress status; accessible terracotta action token |
| `--accent-hover` | `#8c3d1c` | `#f2b08b` | Hover/focus state |
| `--accent-fg` | `#ffffff` | `#1a1a1a` | Text on accent bg |
| `--accent-subtle` | `#f6d6c6` | `#3a1d12` | Selected state, accent tint |

### Status

Each status has `-bg` / `-fg` pair. All pairs meet WCAG AA (≥ 4.5:1).

| Token prefix | Light bg | Light fg | Dark bg | Dark fg | Notes |
|---|---|---|---|---|---|
| `--status-backlog` | `#6c757d` | `#ffffff` | `#48484a` | `#f5f5f7` | |
| `--status-ready` | `#0f7a8a` | `#ffffff` | `#0a7d8c` | `#ffffff` | Darkened from #17a2b8 for AA (≈ 4.6:1) |
| `--status-inprogress` | `#a94a22` | `#ffffff` | `#e08a5d` | `#1a1a1a` | Uses accessible terracotta action token |
| `--status-done` | `#1e7d34` | `#ffffff` | `#1e7d34` | `#ffffff` | Darkened from #28a745 for AA (≈ 4.8:1) |
| `--status-cancelled` | `#ffc107` | `#343a40` | `#b38600` | `#1a1a1a` | Yellow fails AA with white; dark text required |
| `--status-deleted` | `#dc3545` | `#ffffff` | `#b02a37` | `#ffffff` | |

### Priority

All pairs verified WCAG AA.

| Token prefix | Light bg | Light fg | Dark bg | Dark fg |
|---|---|---|---|---|
| `--priority-low` | `#d1ecf1` | `#0c5460` | `#0c3d47` | `#7dd3e8` |
| `--priority-normal` | `#e2e3e5` | `#383d41` | `#3a3a3c` | `#aeaeb2` |
| `--priority-high` | `#f8d7da` | `#721c24` | `#4a1a1f` | `#f28b95` |

### Feedback

| Token | Light | Dark | Usage |
|---|---|---|---|
| `--feedback-error` | `#dc3545` | `#f28b95` | Error text / icon |
| `--feedback-error-bg` | `#f8d7da` | `#4a1a1f` | Error container |
| `--feedback-warning` | `#856404` | `#ffc107` | Warning text / icon |
| `--feedback-warning-bg` | `#fff3cd` | `#3d2e00` | Warning container |
| `--feedback-success` | `#155724` | `#75b798` | Success text / icon (light ≈ 9.1:1 on bg, dark ≈ 6.7:1) |
| `--feedback-success-bg` | `#d4edda` | `#0f2914` | Success container |

---

## Spacing

Invariant across themes. Base-4 progression (4 → 6 → 8 → 12 → 16 → 24 → 32 px).

| Token | Value | px | Usage |
|---|---|---|---|
| `--space-1` | `0.25rem` | 4 | Icon gaps, tight insets |
| `--space-1_5` | `0.375rem` | 6 | Badge/chip horizontal padding, tight row gaps |
| `--space-2` | `0.5rem` | 8 | Inner element padding |
| `--space-3` | `0.75rem` | 12 | Component inner padding |
| `--space-4` | `1rem` | 16 | Panel padding, section gap |
| `--space-6` | `1.5rem` | 24 | Between sections |
| `--space-8` | `2rem` | 32 | Major section gap |

> Badge vertical padding (0.125rem / 2px) is component-specific — not a token.

---

## Radius

Invariant across themes.

| Token | Value | Usage |
|---|---|---|
| `--radius-sm` | `10px` | Badges, chips, small inline elements |
| `--radius-md` | `16px` | Cards, inputs, buttons, comment threads |
| `--radius-lg` | `20px` | Columns, modals, dialogs |
| `--radius-pill` | `999px` | Full pills, CTAs, nav links, eyebrow labels |

> **Agent Manifesto adoption:** `tokens.css` now declares Agent Manifesto radii —
> sm=10px, md=16px, lg=20px, pill=999px. The former compact 4px/6px/8px radii were replaced by
> the parent design system.

---

## Shadow

Invariant across themes.

| Token | Value | Usage |
|---|---|---|
| `--shadow-card` | `0 1px 3px rgba(0,0,0,0.1)` | Default card |
| `--shadow-card-hover` | `0 2px 6px rgba(0,0,0,0.15)` | Card hover |
| `--shadow-modal` | `0 10px 40px rgba(0,0,0,0.2)` | Modal, dialog |

---

## Typography

Invariant across themes.

### Font Family

| Token | Value | Usage |
|---|---|---|
| `--font-family-base` | `Inter, system-ui, -apple-system, "Segoe UI", "Helvetica Neue", Arial, sans-serif` | All UI text (body, headings, labels, inputs) |
| `--font-family-mono` | `ui-monospace, SFMono-Regular, Menlo, monospace` | File paths, code identifiers, terminal-style output |

> Inter is inherited from Agent Manifesto. System fallbacks keep the UI local-first when Inter is
> unavailable. `--font-family-mono` is TaskPilot-specific for file-path display.

### Font Size

| Token | Value | px | Usage |
|---|---|---|---|
| `--font-size-xs` | `0.75rem` | 12 | Badge labels, status/priority chips |
| `--font-size-sm` | `0.8125rem` | 13 | Secondary labels, timestamps |
| `--font-size-base` | `0.875rem` | 14 | Body text, inputs |
| `--font-size-lg` | `1.25rem` | 20 | Modal titles, dialog headings |

> **Merges:** 0.6875rem + 0.75rem → `--font-size-xs` (1px diff). 1.125rem + 1.25rem → `--font-size-lg` (2px diff, both heading contexts).
> `--font-size-xs` and `--font-size-lg` are in `tokens.css` and applied in component CSS (F009-T0).

### Font Weight

| Token | Value | Usage |
|---|---|---|
| `--font-weight-normal` | `400` | Body text |
| `--font-weight-semibold` | `600` | Labels, headings, emphasis |

> In `tokens.css` (F009-T0). The former `font-weight: bold` (700) in `KanbanCard` was unified to `--font-weight-semibold`.

### Line Height

| Token | Value | Usage |
|---|---|---|
| `--line-height-tight` | `1.4` | Card descriptions, compact text |
| `--line-height-base` | `1.5` | Body text, forms (global default) |
| `--line-height-relaxed` | `1.6` | Modal reading text |

> In `tokens.css` and applied in component CSS (F009-T0).

### Letter Spacing

| Token | Value | Usage |
|---|---|---|
| `--letter-spacing-wide` | `0.05em` | Uppercase section labels |

> In `tokens.css` and applied in component CSS (F009-T0).

---

## Icon Library

`lucide-react` is the project icon library. All icon usage must go through
`web/src/components/ui/Icon.tsx`.

Usage rules:
- Icons conveying meaning (type indicators, status markers, action buttons) require `label` prop →
  rendered with `aria-label={label}` and `aria-hidden="false"`.
- Decorative icons (visual reinforcement of adjacent visible text) omit `label` → `aria-hidden="true"`.
- No Unicode glyph characters (`⬛`, `▶`, `□`, `×`, etc.) in JSX; use `<Icon>` instead.
- Import only named Lucide components used; tree-shaking is critical for bundle size.

Current icon assignments:

| Context | Icon | Lucide name |
|---|---|---|
| Epic type | Layer stack | `Layers` |
| Feature type | Lightning | `Zap` |
| Task type | Checkbox | `CheckSquare` |
| Bug type | Bug | `Bug` |
| Modal close | X mark | `X` |

---

## MCP Design Tools

### Pencil MCP Limitations

All `.pen` design files live in `designs/`. The shared component library is
`designs/shared-components-lib.pen`. Access `.pen` files only via the `pencil` MCP tools — never
with `Read` or `Grep` directly.

1. **File creation.** Pencil MCP cannot create `.pen` files. Use the `Write` tool with the minimal
   scaffold `{"version":"2.14","children":[]}` to create new files on disk before populating them
   via `batch_design`.

2. **Active-editor writes.** All `batch_design` modifications land in the currently active editor
   file (reported by `get_editor_state`), regardless of which `filePath` is passed. The `filePath`
   parameter selects variable/import context for reads; it does not direct writes. To populate a
   different `.pen` file, open it in Pencil desktop first, then verify the active editor changed
   via `get_editor_state`.

3. **Unified canvas.** Pencil reads all `.pen` files under `designs/` as one combined design space.
   Individual files function as entry points, not isolated documents.

4. **Screenshot vision.** Pencil `get_screenshot` returns an image that may not be processable by
   all AI models. Rely on `snapshot_layout` and `batch_get` structural inspection for verification
   when screenshots are unavailable.

### Open Design MCP Constraints

1. **Project context.** OD tools can default to an active project, and that active context expires.

2. **Generation runs.** OD generation and refinement run asynchronously and can take several
   minutes.

3. **Artifact bundles.** OD artifacts are multi-file bundles; an entry artifact can reference
   sibling source files and assets.

4. **Design-system resources.** OD design systems are MCP resources such as
   `od://design-systems/<id>/DESIGN.md`.

5. **Production boundary.** OD HTML, JSX, CSS, and assets are design evidence, not production code
   to copy wholesale. Implementation must still use TaskPilot components, tokens, accessibility
   rules, REST boundaries, and tests.

---

## Merge Log

| Merged from | Into | Diff | Rationale |
|---|---|---|---|
| TaskPilot blue accent | Agent Manifesto terracotta accent | identity change | Shared parent brand language across projects |
| TaskPilot compact radii `4px/6px/8px` | Agent Manifesto radii `10px/16px/20px/999px` | posture change | Shared parent component shape across projects |
| TaskPilot system font | Agent Manifesto Inter stack | typography change | Shared parent type system with local fallbacks |
| `0.6875rem` + `0.75rem` (hard-coded) | `--font-size-xs: 0.75rem` | 1 px | Both badge/label contexts in same component |
| `1.125rem` + `1.25rem` (hard-coded) | `--font-size-lg: 1.25rem` | 2 px | Both modal/dialog heading contexts |

---

## Tokens Not Yet in tokens.css

All previously pending tokens were added to `tokens.css` in F009-T0. `tokens.css` is now in full
sync with this document. New tokens go to `tokens.css` and this file together.

---

## Design Debt

- Token system established (spec 0003) and later aligned to the Agent Manifesto parent design
  system. Breakpoints and interaction behavior remain provisional
  until List View and Tree View are implemented.
- No theme-toggle UI control yet (spec 0003 out-of-scope). OS preference switches theme
  automatically; `[data-theme]` override requires manual JS until a toggle is built.
- Token sync complete (F009-T0, updated for Agent Manifesto parent): radii now use
  sm=10px/md=16px/lg=20px plus `--radius-pill`; all typography and spacing tokens are present;
  component CSS references tokens rather than literals.
- Update this file when an accepted specification or implemented UI establishes a durable pattern.
