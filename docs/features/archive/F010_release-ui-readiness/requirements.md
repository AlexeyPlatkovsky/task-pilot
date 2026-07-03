# F010 Release UI Readiness — Requirements

## Summary

Prepare the Beta WebUI item-management loop for release by closing the non-F009 release gaps:
filter parity for Board/List, hiding the unfinished Tree surface from release paths, remembering the
last opened project through local UI state, refreshing externally changed task data without page
reload, correcting validation success contrast, and gating the task detail redesign behind a
separate pre-implementation discussion.

F010 is Beta scope. Text search, settings screens, Git helper UX, MCP, hosted sync, advanced graph
visualization, import/export, and other non-core surfaces remain out of scope for this feature.

## Serves

- `roadmap.md` Next Release Roadmap — release UI readiness items 1-6

## Functional Requirements

| ID | Requirement | Priority |
| --- | --- | --- |
| F010-R1 | Board view shall provide release filter controls for type, priority, updated time range, and created time range using the shared dropdown selector pattern | must |
| F010-R2 | List view shall add a created time range filter using the same date-range options and deterministic filtering behavior as the updated time range filter | must |
| F010-R3 | Board and List date range filters shall support `Any time`, `Last 7 days`, `Last 14 days`, and `Last 30 days` for both updated and created timestamps | must |
| F010-R4 | The release WebUI shall hide the Tree tab from release-facing navigation while keeping the Tree implementation importable | must |
| F010-R5 | The server shall persist local WebUI state in `ui-state.yaml` in the existing TaskPilot system directory, not in canonical workspace files | must |
| F010-R6 | The REST API shall expose `GET /api/ui-state` and `PATCH /api/ui-state` for validated UI-state reads and partial updates | must |
| F010-R7 | The WebUI shall restore the last opened project by loading UI state before project validation and selecting the stored registry project ID only when it is active and available | must |
| F010-R8 | The WebUI shall save the last opened project only after explicit user project selection and shall keep the current session usable if the save fails | must |
| F010-R9 | The WebUI shall refresh project item data every 5 seconds and on window focus or visibility return so CLI/API changes become visible without page reload | must |
| F010-R10 | Background refresh shall not overwrite dirty local edit fields in an open item detail form | must |
| F010-R11 | The validation success message shall use a new `validation-success-muted` design token that is lighter than body text while preserving WCAG AA contrast | must |
| F010-R12 | Task detail redesign shall remain a release blocker but shall not be implemented until a separate discussion defines its information architecture and editing scope | must |

## Acceptance Criteria

- **F010-R1:** Board filters are visible above the board using the same trigger/menu sizing,
  placement, selected state, hover/focus behavior, and Clear behavior as the List filter controls.
  Filtering by type, priority, updated range, or created range hides non-matching cards without
  changing item status or order. Filtered-empty columns remain visible and stable.
- **F010-R2:** List view includes a created time range filter. Combining created and updated ranges
  with existing List filters produces deterministic results and Clear restores the unfiltered list.
- **F010-R3:** Both created and updated date filters use the same option set: `Any time`,
  `Last 7 days`, `Last 14 days`, and `Last 30 days`. Filtering uses the same local deterministic
  reference-time behavior already required for List updated-time filtering.
- **F010-R4:** The release navigation shows Board and List but no visible Tree tab. Release-facing
  tests and docs do not require Tree navigation. Tree code remains importable and is not deleted as
  part of this feature.
- **F010-R5:** `ui-state.yaml` is stored under the same machine-specific TaskPilot system directory
  used for the registry and honors the existing `TASKPILOT_HOME` override. The file is never written
  under `.taskpilot/` and never changes canonical task files.
- **F010-R6:** `GET /api/ui-state` returns at least `last_opened_project_id`, where the value is a
  registry project `id` rather than the display key. Missing UI state
  returns an empty/default state. `PATCH /api/ui-state` accepts partial updates, accepts `null` to
  clear `last_opened_project_id`, rejects unknown fields, and rejects unknown or inactive project
  IDs.
- **F010-R7:** On startup, the WebUI requests UI state first, then loads active projects to validate
  the stored ID. If the stored project is present and active, that project opens by default. If UI
  state fails to load, the stored ID is missing, or the project is unavailable, the WebUI silently
  falls back to the normal no-project-selected state and keeps the project selector usable.
- **F010-R8:** When the user explicitly selects a project, the WebUI opens it immediately and sends
  a UI-state update. If that update fails, the current-session selection remains active and no
  blocking error prevents item management. Auto-restore alone does not rewrite UI state.
- **F010-R9:** When an item status or other listed field is changed through CLI or REST API outside
  the current browser interaction, Board cards, List rows, selected item detail, and validation
  status refresh without page reload within the 5-second polling window or on focus/visibility
  return.
- **F010-R10:** If an item detail form has dirty local edits, background refresh does not replace
  those dirty fields. Clean fields and surrounding list/board data may refresh normally.
- **F010-R11:** The `All items valid` success message uses `validation-success-muted`, renders
  lighter than body text in the supported theme, and remains readable at WCAG AA contrast. Existing
  validation error/warning states keep their current semantics.
- **F010-R12:** Before task detail redesign implementation starts, a new discussion or accepted
  specification defines the detail view information architecture, editable fields, relationship and
  child display, comments behavior, invalid/partial item states, and required UI test levels.

## Constraints

- F010 must not introduce text search; search remains Release scope, not Beta scope.
- F010 must not add a settings or preferences screen. UI state is internal local state exposed only
  through the REST API contract above.
- F010 must not introduce WebSocket, SSE, push updates, hosted synchronization, accounts, or
  collaboration behavior.
- UI state is machine-specific and non-canonical. It must not change item YAML, comment Markdown,
  project metadata, or the project registry schema.
- The simplest Beta-suitable behavior is preferred over complex recovery flows. UI-state failures
  must not block core item management.
- Tree view hiding is release-path trimming, not deletion or a permanent rejection of Tree view.

## Out of Scope

- Text search.
- Task detail redesign implementation before the required discussion.
- Editing every item field from the task detail view.
- Settings/preferences screens.
- Git helper UX.
- MCP adapter.
- Advanced relation graph visualization.
- Import/export helpers.
- Hosted sync, accounts, permissions, collaboration, notifications, plugin systems, or enterprise
  administration.
