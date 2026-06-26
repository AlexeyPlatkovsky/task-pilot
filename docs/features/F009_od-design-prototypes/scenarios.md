# F009 OD Design Prototypes — Scenarios

## Scenarios

### F009-S1: Token fidelity in design system resource

Covers: F009-R1

```gherkin
Scenario: OD design system matches canonical tokens
  Given the OD project `taskpilot-design` is open
  When the design-system resource is read via `od://design-systems/<id>/DESIGN.md`
  Then the resource lists a variable for every token group in `designs/design.md`:
    surface, border, text, accent, status, priority, feedback, spacing, radius, shadow, typography
  And the value of `--accent` in the resource matches `#0066cc`
  And the value of `--status-done-bg` in the resource matches `#1e7d34`
```

### F009-S2: Component library state coverage

Covers: F009-R2, F009-R9

```gherkin
Scenario: Component library covers all required states
  Given the component library artifact is pulled
  When a design-reviewer inspects the artifact
  Then StatusBadge shows all six status variants (backlog, ready, in_progress, done, cancelled, deleted)
  And PriorityBadge shows low, normal, and high variants
  And Button primary variant shows default, hover, focus, and disabled states
  And no hardcoded color or spacing values appear — only token references
```

### F009-S3: Kanban Board prototype state coverage

Covers: F009-R4, F009-R9

```gherkin
Scenario: Kanban Board prototype covers required states
  Given the Kanban Board page prototype is pulled
  When a design-reviewer checks state coverage against `designs/design.md` Required States
  Then an empty-board variant shows all five columns with an empty-state prompt
  And a populated variant shows cards in multiple columns
  And at least one card shows item ID, title, type badge, and priority badge
  And the loading state is represented (spinner or skeleton in the board area)
```

### F009-S4: Item Detail Modal view and edit states

Covers: F009-R5, F009-R9

```gherkin
Scenario: Item Detail Modal covers view and edit modes
  Given the Item Detail Modal prototype is pulled
  When inspecting available frames
  Then a view-mode frame shows all Alpha read-only fields: ID, title, type, status, priority, description, parent, comments
  And an edit-mode frame shows title as a text input, description as a textarea, priority as a dropdown, status as a dropdown
  And an inline-validation frame shows an error message adjacent to the offending field
  And a save-error frame shows a FeedbackBanner with an error message
```

### F009-S5: Design review gate before implementation

Covers: F009-R8

```gherkin
Scenario: Prototype is accepted before implementation begins
  Given a page prototype has been created for the Kanban Board
  When `design-reviewer` is run on the prototype
  Then the reviewer reports no Critical or High findings
  And the `Agent: design-reviewer - output below` artifact is recorded in F009-T9
  And the corresponding od-to-code pipeline may begin for F004
```

### F009-S6: tokens.css completeness and component token compliance

Covers: F009-R10

```gherkin
Scenario: tokens.css declares every canonical token and components use only token references
  Given designs/design.md is the authoritative design source
  When tokens.css is inspected
  Then the :root block includes --space-1_5, --font-family-base, --font-size-xs, --font-size-lg,
    --font-weight-normal, --font-weight-semibold, --line-height-tight, --line-height-base,
    --line-height-relaxed, and --letter-spacing-wide
  And --radius-sm is 4px, --radius-md is 6px, --radius-lg is 8px
  And --radius-xl does not appear anywhere in tokens.css or component CSS files
  And no file under web/src/components/ contains a hardcoded hex color, font-size literal,
    font-weight literal, letter-spacing literal, or line-height literal where a token exists
    (sub-token badge micro-padding 0.125rem / 0.375rem are the only permitted literals)
```

### F009-S7: Validation Panel prototype state coverage

Covers: F009-R11, F009-R9

```gherkin
Scenario: Validation Panel prototype covers empty and populated states
  Given the Validation Panel page prototype is pulled
  When a design-reviewer checks state coverage
  Then an empty-state frame shows a success message indicating all items are valid
  And a populated frame shows a list of ValidationErrorRow components
  And at least one row shows a parse-failure variant (fatal, file unreadable)
  And at least one row shows a field-level error variant (file parsed, specific field invalid)
  And each row displays the file path and a human-readable error message
  And the two error variants are visually distinguishable without relying on color alone
```

## Manual Verification Checklist

- [ ] (F009-R1) Every token in the `Tokens Not Yet in tokens.css` table in `designs/design.md` is
      also defined in the OD design system resource, even if not yet in `tokens.css`.
- [ ] (F009-R2) No component in the library uses a hardcoded color, border-radius, or spacing value
      where a token exists.
- [ ] (F009-R9) Required States checklist completed for each prototype:
      - [ ] loading
      - [ ] empty results
      - [ ] recoverable error
      - [ ] invalid canonical file (where applicable)
      - [ ] missing/broken relation (where applicable)
      - [ ] unsaved/conflicting change (Item Detail Modal only)
      - [ ] completed success state
- [ ] (F009-R8) Each accepted prototype has a recorded `Agent: design-reviewer - output below`
      artifact with no unresolved Critical or High findings.
- [ ] (F009-R10) `tokens.css` contains all ten previously missing tokens.
- [ ] (F009-R10) `--radius-xl` does not appear in any file under `web/src/`.
- [ ] (F009-R10) `grep -r "font-weight: 6\|font-size: 0\.75rem\|font-size: 1\.\(25\|125\)rem\|letter-spacing: 0\.05em\|line-height: 1\.\(5\|6\)" web/src/components/` returns no matches.
