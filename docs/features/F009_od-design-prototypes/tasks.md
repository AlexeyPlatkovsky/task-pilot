# F009 OD Design Prototypes — Tasks

| ID | Task | Implements | Status | Depends on |
| --- | --- | --- | --- | --- |
| F009-T0 | Sync `tokens.css` with `designs/design.md`: (a) add all ten missing tokens; (b) adopt Agent Manifesto parent tokens (`--brand-accent`, terracotta `--accent`, Inter, sm=10px/md=16px/lg=20px/999px pill radii); (c) keep `--radius-xl` removed; (d) replace every hardcoded `font-weight: 600`, `0.75rem`, `1.25rem`, `1.125rem`, `letter-spacing: 0.05em`, `line-height: 1.5`, and `line-height: 1.6` literal in `web/src/components/*.module.css` and `web/src/index.css` with the corresponding token reference | F009-R10 | ✅ done | — |
| F009-T1 | Check for an existing OD project named `taskpilot-design` via `list_projects`; create it if absent. Define the design system resource with all token groups from `designs/design.md` as OD variables | F009-R1 | ✅ done | — |
| F009-T2 | Create component library artifact: StatusBadge, PriorityBadge, TypeBadge with all status/priority/type variants | F009-R2 | ✅ done | F009-T1 |
| F009-T3 | Extend component library: ItemCard (Kanban), ItemRow (List), Button (primary/secondary/destructive), TextInput, SelectDropdown | F009-R2 | ✅ done | F009-T2 |
| F009-T4 | Extend component library: Icon wrapper (labeled/decorative), EmptyState, FeedbackBanner, ValidationErrorRow (parse-failure and field-level error variants), ItemDetailModal shell states | F009-R2 | ✅ done | F009-T3 |
| F009-T5 | Design-review component library with `design-reviewer`; fix Critical/High findings | F009-R2, F009-R8 | ✅ done | F009-T4 |
| F009-T6 | Create page prototype: Project Selector (empty, populated, error states) | F009-R3 | ✅ done | F009-T5 |
| F009-T7 | Create page prototype: Kanban Board (five columns, empty columns, populated columns, at least one card with all fields) | F009-R4 | ✅ done | F009-T5 |
| F009-T8 | Create page prototype: Item Detail Modal (view mode, edit mode, inline validation error, save error banner) | F009-R5 | ✅ done | F009-T5 |
| F009-T9 | Design-review Project Selector, Kanban Board, and Item Detail Modal prototypes; fix Critical/High findings | F009-R3, F009-R4, F009-R5, F009-R8, F009-R9 | ⏳ todo | F009-T6, F009-T7, F009-T8 |
| F009-T10 | Create page prototype: List View (header row, populated rows, empty state, sort indicator) | F009-R6 | ⏳ todo | F009-T5 |
| F009-T11 | Create page prototype: Tree View (two-level hierarchy, expand/collapse, empty state) | F009-R7 | ⏳ todo | F009-T5 |
| F009-T12 | Design-review List View and Tree View prototypes; fix Critical/High findings | F009-R6, F009-R7, F009-R8, F009-R9 | ⏳ todo | F009-T10, F009-T11 |
| F009-T13 | Create page prototype: Validation Panel (empty/all-valid state with success message, populated state with a list of ValidationErrorRows showing file path and error, parse-failure rows visually distinct from field-level rows) | F009-R11 | ⏳ todo | F009-T5 |
| F009-T14 | Design-review Validation Panel prototype; fix Critical/High findings | F009-R11, F009-R8, F009-R9 | ⏳ todo | F009-T13 |

## Notes

- F009-T0 (tokens.css sync) can run in parallel with F009-T1 (OD design system creation) because
  T1 reads `designs/design.md` directly, not `tokens.css`. However, T0 must be complete before any
  `od-to-code` pipeline runs, since the generated React code will reference the new token names.
- F009-T0 was updated after Agent Manifesto became TaskPilot's parent design system. Existing OD
  prototypes must include the synced token override block before they are treated as current.
- Every task that runs `design-reviewer` must produce an `Agent: design-reviewer - output below`
  artifact before the task is considered done.
- Tasks F009-T2 through F009-T4 may be batched into fewer OD runs if the OD skill can handle
  the scope in one pass; split only if the artifact bundle becomes too large to review coherently.
- F009-T10 and F009-T11 (List View and Tree View) are lower priority than the Alpha screen set;
  they can be deferred until F006 implementation begins if OD capacity is constrained.
- OD is the default MCP design path. If the OD MCP is unavailable when a task begins, route
  through the Pencil pipeline and note the substitution in the task output artifact.
- Accepted prototypes feed directly into the `od-to-code` pipeline for the corresponding feature
  (F004/F005 for Kanban/Modal, F006 for List/Tree/Validation Panel).
- F009-T13 and F009-T14 (Validation Panel) can run in parallel with T10–T12 (List/Tree).
