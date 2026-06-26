# TaskPilot Design Book

Status: baseline

## Product Experience

TaskPilot is a local developer tool for inspecting and changing structured work shared with AI
agents. The interface prioritizes fast scanning, explicit system state, keyboard use, and
Git-friendly transparency over dashboard decoration.

## Core Patterns

- Use a list or table as the primary scanning surface.
- Use a detail page or side panel for one item's content, metadata, links, and comments.
- Show validation close to the affected field and preserve visibility of invalid source files.
- Show statuses and relationship types with text; color may reinforce meaning but cannot own it.
- Keep destructive actions explicit and confirm effects that can remove canonical data.
- Keep domain rules and filesystem behavior outside UI components.

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

## Accessibility Baseline

- All controls have accessible names.
- Keyboard order follows the visible task flow.
- Focus remains visible and moves deliberately after dialogs, drawers, and create actions.
- Native controls and accessible primitives are preferred.
- Status, priority, validation, and relationship meaning never depend on color alone.

## Responsive Baseline

- Desktop layouts optimize for scanning and side-by-side context.
- Narrow layouts preserve the primary action and item identity before secondary metadata.
- Tables may become stacked rows only when column meaning remains explicit.

## Visual Direction

- Neutral surfaces, restrained borders, one functional accent, and clear type hierarchy.
- Consistent spacing and density suitable for developer tools.
- Motion is limited to opacity and transforms that clarify state changes.
- Avoid glass effects, decorative gradients, dashboard-card overload, and hidden hover-only state.

## Design Token Reference

All production CSS must use tokens from `web/src/tokens.css`. No hardcoded hex, rgba, rem, px
radius, or box-shadow values are permitted in `web/src/components/*.module.css` or `web/src/index.css`.
Sub-token micro-padding literals (`0.125rem`, `0.375rem`) used only for badge internal padding are
the sole exemption.

Token groups (55 tokens total):

| Group | Tokens | Notes |
|---|---|---|
| Surface | `--surface-app`, `--surface-base`, `--surface-raised`, `--surface-overlay`, `--surface-muted`, `--surface-column` | Layer hierarchy: app → base → raised |
| Border | `--border-subtle`, `--border-default`, `--border-strong` | Use subtle for dividers, default for inputs |
| Text | `--text-primary`, `--text-secondary`, `--text-muted`, `--text-disabled`, `--text-inverse` | `--text-disabled` intentionally fails WCAG (inactive UI, WCAG 1.4.3 exempt) |
| Accent | `--accent`, `--accent-hover`, `--accent-fg`, `--accent-subtle` | `--accent-fg` is the foreground color on `--accent` backgrounds |
| Status | `--status-{backlog,ready,inprogress,done,cancelled,deleted}-{bg,fg}` | All 12 pairs verified WCAG AA |
| Priority | `--priority-{low,normal,high}-{bg,fg}` | All 6 pairs verified WCAG AA |
| Feedback | `--feedback-error`, `--feedback-error-bg`, `--feedback-warning`, `--feedback-warning-bg` | Use `--text-primary` as text color on feedback backgrounds |
| Spacing | `--space-{1,2,3,4,6,8}` | rem scale: 0.25–2rem |
| Radius | `--radius-{sm,md,lg,xl}` | 3px–8px; use `--radius-xl` for pill badges |
| Shadow | `--shadow-card`, `--shadow-card-hover`, `--shadow-modal` | — |
| Typography | `--font-size-sm`, `--font-size-base` | 0.8125rem, 0.875rem |

**Contrast requirement:** all foreground/background token pairs used in production must meet WCAG AA:
4.5:1 for normal text (< 18pt / 14pt bold), 3:1 for large text. See `docs/specs/0003-design-token-system.md`.

**Theme switching:** light defaults live in `:root`. Dark overrides live in
`@media (prefers-color-scheme: dark) :root`. Explicit `[data-theme="light"]` and
`[data-theme="dark"]` attributes on `<html>` override OS preference.
`[data-theme="light"]` must explicitly declare every token that the dark `@media` block overrides,
to prevent dark values from persisting in forced-light mode.

Cross-reference: `docs/design.md` for screen-level inventory and component states.

## Pencil Design Files

All `.pen` design files live in `designs/`. The shared component library is
`designs/shared-components-lib.pen`. Access `.pen` files only via the `pencil` MCP tools — never
with `Read` or `Grep` directly.

- Design-only sessions: governed by the `pen-design` pipeline (`.claude/pipelines/pen-design.md`).
- Design-to-implementation sessions: governed by the `pen-to-code` pipeline (`.claude/pipelines/pen-to-code.md`).
- The `pencil-design` skill governs all `.pen` file operations within those pipelines.

### Pencil MCP Limitations

These constraints are dictated by the Pencil MCP protocol:

1. **File creation.** Pencil MCP cannot create `.pen` files. Use the `Write` tool with the minimal
   scaffold `{"version":"2.14","children":[]}` to create new files on disk before populating them
   via `batch_design`.

2. **Active-editor writes.** All `batch_design` modifications land in the currently active editor
   file (reported by `get_editor_state`), regardless of which `filePath` is passed. The `filePath`
   parameter selects variable/import context for reads; it does not direct writes. To populate a
   different `.pen` file, open it in Pencil desktop first, then verify the active editor changed
   via `get_editor_state`.

3. **Unified canvas.** Pencil reads all `.pen` files under `designs/` as one combined design space.
   Individual files function as entry points, not isolated documents. Do not expect "one page per
   file" container isolation for reading — batch_design writes DO land in the active editor file.

4. **Screenshot vision.** Pencil `get_screenshot` returns an image that may not be processable by
   all AI models. Rely on `snapshot_layout` and `batch_get` structural inspection for verification
   when screenshots are unavailable. The `design-reviewer` agent in the pen-design pipeline requires
   screenshot evidence; if the model cannot analyze images, skip design-reviewer and report it as
   a skipped step with snapshot_layout as compensating evidence.

## Open Design Artifacts

Open Design (OD) stores browser-viewable design artifacts in local projects. An OD project can
contain an entry artifact plus referenced HTML, JSX, CSS, SVG, image, and Markdown files.

### Open Design MCP Constraints

These constraints are dictated by the OD MCP project/artifact model:

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

## Design Debt

- Token system established (spec 0003). Breakpoints and interaction behavior remain provisional
  until List View and Tree View are implemented.
- No theme-toggle UI control yet (spec 0003 out-of-scope). OS preference switches theme
  automatically; `[data-theme]` override requires manual JS until a toggle is built.
- Update this book when an accepted specification or implemented UI establishes a durable pattern.
