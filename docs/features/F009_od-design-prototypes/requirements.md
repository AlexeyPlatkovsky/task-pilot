# F009 OD Design Prototypes — Requirements

## Summary

Establish an Open Design (OD) project that contains the TaskPilot design system, a reusable
component library, and browser-viewable page prototypes for every screen in the Alpha scope.
These artifacts serve as the design specification gate that must be reviewed and accepted
before any new UI screen proceeds to the `od-to-code` implementation pipeline.

OD artifacts are design evidence, not production code. All implementation must still use
TaskPilot tokens, REST boundaries, and tests per `AGENTS.md` and the relevant specs.

## Serves

- `designs/design.md` — design system, tokens, accessibility rules, OD constraints
- `docs/design.md` — screen inventory and UX principles
- `roadmap.md` Phase 4 — Local WebUI (design gate before implementation)
- `roadmap.md` Phase 5 — Better views (design gate before F006 implementation)

## Functional Requirements

| ID | Requirement | Priority |
| --- | --- | --- |
| F009-R1 | An OD project named `taskpilot-design` must exist with a design system resource that encodes all tokens from `designs/design.md` as OD variables | must |
| F009-R2 | A component library artifact must define all reusable UI components with all required states | must |
| F009-R3 | A page prototype must exist for the Project Selector screen | must |
| F009-R4 | A page prototype must exist for the Kanban Board screen, covering empty, populated, and card-detail states | must |
| F009-R5 | A page prototype must exist for the Item Detail Modal, covering view mode, edit mode, validation error, and save error states | must |
| F009-R6 | A page prototype must exist for the List View screen | should |
| F009-R7 | A page prototype must exist for the Tree View screen | should |
| F009-R11 | A page prototype must exist for the Validation Panel screen, covering the empty state (all items valid) and the populated state (list of validation errors with file path and message) | should |
| F009-R8 | All prototypes must pass `design-reviewer` with no Critical or High findings before the corresponding feature proceeds to `od-to-code` | must |
| F009-R9 | All prototype states must cover the Required States defined in `designs/design.md` | must |
| F009-R10 | `web/src/tokens.css` must declare every token listed in `designs/design.md` before any component that uses it is implemented. Missing tokens must be added, Agent Manifesto parent tokens must be reflected locally (`--brand-accent`, terracotta `--accent`, Inter, sm=10px/md=16px/lg=20px/999px pill radii), and all hardcoded values in `web/src/components/*.module.css` that have a canonical token must be replaced with token references | must |

## Component Library Scope (R2)

The component library artifact must include the following components with all visible states:

| Component | States |
| --- | --- |
| StatusBadge | backlog, ready, in_progress, done, cancelled, deleted |
| PriorityBadge | low, normal, high |
| TypeBadge | epic, feature, task, bug |
| ItemCard (Kanban) | default, hover, focused |
| ItemRow (List) | default, hover, focused, selected |
| ItemDetailModal shell | loading, view, edit, error |
| Button | primary, secondary, destructive; default/hover/focus/disabled per variant |
| TextInput | default, focus, error, disabled |
| SelectDropdown | closed, open, selected |
| Icon (Lucide wrapper) | labeled, decorative |
| EmptyState | with CTA, without CTA |
| FeedbackBanner | error, warning |
| ValidationErrorRow | parse-failure, field-level error |

## Acceptance Criteria

- **F009-R1:** `mcp__open_design__get_project()` returns a project with id `taskpilot-design` and a
  design system resource. Reading the resource shows all token groups from `designs/design.md` as
  variables with correct values.
- **F009-R2:** The component library artifact contains one section per component in the scope table,
  with all listed states visible. No hardcoded hex, rgba, or rem values — only token references.
- **F009-R3:** The Project Selector prototype shows the empty state (no projects) and populated state
  (list of projects). Error state (unreadable project) is also shown.
- **F009-R4:** The Kanban Board prototype shows five columns (backlog, ready, in_progress, done,
  cancelled), each with an empty and populated variant. At least one card shows all card fields.
- **F009-R5:** The Item Detail Modal prototype shows view mode (all Alpha read-only fields), edit
  mode (editable title, description, priority, status), validation error inline, and save error
  banner.
- **F009-R6:** The List View prototype shows a populated table with header sort indicators and an
  empty state.
- **F009-R7:** The Tree View prototype shows a two-level hierarchy (epic → feature → task) with
  expand/collapse and an empty state.
- **F009-R11:** The Validation Panel prototype shows an empty state (a success message: all items
  valid) and a populated state (a list of error rows each showing file path, item ID if parseable,
  and error message). Rows with fatal parse failures are visually distinguishable from rows with
  field-level validation errors.
- **F009-R8:** Each prototype was reviewed by `design-reviewer` and received at most Low findings
  before being accepted.
- **F009-R9:** Every applicable Required State from `designs/design.md` is represented in at least
  one prototype or explicitly marked out-of-scope with a recorded rationale.
- **F009-R10:** `tokens.css` :root includes all ten previously missing tokens
  (`--space-1_5`, `--font-family-base`, `--font-size-xs`, `--font-size-lg`,
  `--font-weight-normal`, `--font-weight-semibold`, `--line-height-tight`,
  `--line-height-base`, `--line-height-relaxed`, `--letter-spacing-wide`); Agent Manifesto parent
  tokens are present (`--brand-accent: #c65d2e`, `--accent: #a94a22`, Inter font stack, and
  sm=10px/md=16px/lg=20px plus `--radius-pill: 999px`); `--radius-xl` remains removed; and
  hardcoded `font-weight: 600`, `0.75rem`, `1.25rem`,
  `1.125rem`, `letter-spacing: 0.05em`, and `line-height` literals in component CSS files are
  replaced with the corresponding token references.

## Constraints

- OD design system token values must exactly match `designs/design.md`. `designs/design.md` is
  always authoritative; OD is derived.
- WCAG AA contrast must be maintained for all component state pairings (see `designs/design.md`
  Accessibility Baseline).
- Icon usage must match the Icon Library in `designs/design.md`. No ad hoc glyphs.
- Prototypes use light theme by default; dark theme variants are optional for Alpha, but the
  canonical token system includes dark theme values.

## Out of Scope

- Dedicated dark theme prototype pages (Beta).
- Mobile/narrow layout variants (can be added once desktop layouts are accepted).
- Drag-and-drop interaction simulation.
- Validation panel prototype is now in scope (F009-R11).
- Production code — `od-to-code` pipeline handles translation.
