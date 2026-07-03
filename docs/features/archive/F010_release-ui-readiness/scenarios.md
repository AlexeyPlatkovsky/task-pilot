# F010 Release UI Readiness — Scenarios

## Scenarios

### F010-S1: Filter Board cards by release filters

Covers: F010-R1, F010-R3

```gherkin
Scenario: Filter Board cards by release filters
  Given the Board view shows items with different types, priorities, created_at values, and updated_at values
  When the user selects type "bug", priority "high", created range "Last 14 days", and updated range "Last 7 days"
  Then only matching cards remain visible
    And non-matching cards are hidden without changing status or order
    And empty columns remain visible
```

### F010-S2: Clear Board filters

Covers: F010-R1, F010-R3

```gherkin
Scenario: Clear Board filters
  Given Board filters hide some cards
  When the user clicks Clear
  Then type, priority, created range, and updated range return to their defaults
    And every board card is visible again
```

### F010-S3: Filter List by created range

Covers: F010-R2, F010-R3

```gherkin
Scenario: Filter List by created range
  Given the List view contains items created across multiple dates
  When the user selects created range "Last 30 days"
  Then the list shows only items created within the deterministic 30-day window
    And existing List filters can still be combined with the created range
```

### F010-S4: Hide Tree from release navigation

Covers: F010-R4

```gherkin
Scenario: Hide Tree from release navigation
  Given a project is selected in the release WebUI
  When the workspace navigation renders
  Then Board and List tabs are visible
    And the Tree tab is not visible
    And Tree implementation modules are still importable by tests
```

### F010-S5: Read default UI state

Covers: F010-R5, F010-R6

```gherkin
Scenario: Read default UI state
  Given no ui-state.yaml file exists in the TaskPilot system directory
  When the WebUI calls GET /api/ui-state
  Then the API returns a default UI state
    And last_opened_project_id is null
    And no canonical workspace file is created or changed
```

### F010-S6: Save and clear last opened project

Covers: F010-R5, F010-R6, F010-R8

```gherkin
Scenario: Save and clear last opened project
  Given project id "task-pilot" with key "TP" is active in the local registry
  When the WebUI patches UI state with last_opened_project_id "task-pilot"
  Then ui-state.yaml records "task-pilot" in the TaskPilot system directory
  When the WebUI patches UI state with last_opened_project_id null
  Then ui-state.yaml clears the remembered project
```

### F010-S7: Reject invalid UI-state updates

Covers: F010-R6

```gherkin
Scenario: Reject invalid UI-state updates
  Given project id "old-project" is inactive or unknown
  When the WebUI patches UI state with last_opened_project_id "old-project"
  Then the API rejects the request
    And the previous UI state remains unchanged
```

### F010-S8: Restore last opened project on startup

Covers: F010-R7

```gherkin
Scenario: Restore last opened project on startup
  Given ui-state.yaml remembers project id "task-pilot"
    And the registry lists project id "task-pilot" with key "TP" as active
  When the WebUI starts
  Then it loads UI state before validating projects
    And opens project id "task-pilot" by default
```

### F010-S9: Fall back when UI state is unavailable

Covers: F010-R7

```gherkin
Scenario: Fall back when UI state is unavailable
  Given GET /api/ui-state fails
    And GET /api/projects succeeds
  When the WebUI starts
  Then no project is selected
    And the normal project selector remains usable
```

### F010-S10: Keep selected project when saving UI state fails

Covers: F010-R8

```gherkin
Scenario: Keep selected project when saving UI state fails
  Given the project selector is usable
    And PATCH /api/ui-state will fail
  When the user selects an active project
  Then that project opens for the current session
    And item management is not blocked by the failed UI-state save
```

### F010-S11: Refresh external item updates without reload

Covers: F010-R9

```gherkin
Scenario: Refresh external item updates without reload
  Given the WebUI is open on the Board view
    And item "TP-1" is currently in status "ready"
  When a CLI command or REST API call changes "TP-1" to status "done"
  Then the WebUI shows "TP-1" in the done column without a page reload
    And the update appears within the 5-second polling window or on focus return
```

### F010-S12: Preserve dirty detail edits during background refresh

Covers: F010-R10

```gherkin
Scenario: Preserve dirty detail edits during background refresh
  Given the item detail view is open
    And the user has unsaved changes in an editable field
  When background polling fetches a newer server version of the item
  Then the dirty local field is not overwritten
    And the user can still save or cancel the local edit
```

### F010-S13: Render muted validation success

Covers: F010-R11

```gherkin
Scenario: Render muted validation success
  Given validation returns no findings
  When the validation status renders "All items valid"
  Then the message uses the validation-success-muted token
    And the computed color is lighter than body text
    And the message still meets WCAG AA contrast
```

### F010-S14: Gate task detail redesign

Covers: F010-R12

```gherkin
Scenario: Gate task detail redesign
  Given implementation planning reaches the task detail redesign item
  When no accepted detail-view discussion or specification exists
  Then implementation of the redesign does not start
    And the missing information architecture and editing-scope decisions are reported
```

## Manual Verification Checklist

- [ ] (F010-R1) Confirm Board filters use the shared dropdown selector pattern and include type,
      priority, updated range, and created range.
- [ ] (F010-R2) Confirm List created range combines correctly with existing List filters.
- [ ] (F010-R3) Confirm created and updated range options are exactly `Any time`, `Last 7 days`,
      `Last 14 days`, and `Last 30 days`.
- [ ] (F010-R4) Confirm release navigation has no visible Tree tab while Tree code still imports.
- [ ] (F010-R5) Confirm `ui-state.yaml` is written under the TaskPilot system directory and not
      under `.taskpilot/`.
- [ ] (F010-R6) Confirm UI-state API rejects unknown fields and unknown/inactive projects.
- [ ] (F010-R7) Confirm active remembered project restores and invalid/unavailable state falls back
      to the normal project selector.
- [ ] (F010-R8) Confirm failed UI-state save does not block current-session project selection.
- [ ] (F010-R9) Confirm CLI/API item updates appear in Board, List, item detail, and validation
      status without page reload.
- [ ] (F010-R10) Confirm polling does not overwrite dirty local detail-edit fields.
- [ ] (F010-R11) Confirm `All items valid` uses `validation-success-muted` and passes contrast.
- [ ] (F010-R12) Confirm task detail redesign is not implemented before the required discussion.
