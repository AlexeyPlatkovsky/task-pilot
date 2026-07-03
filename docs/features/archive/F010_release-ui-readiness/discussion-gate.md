# F010-T13: Task Detail Redesign Discussion Gate

**Status:** Held. Implementation gated per F010-R12.

## Decision

The task detail redesign (expanding item detail view information architecture,
editable fields, relationship/child display, comments behavior, invalid/partial
item states, and required UI test levels) remains a release blocker for TaskPilot
Beta but **shall not be implemented** until a separate discussion or accepted
specification defines the items above.

## Current state

The current `ItemModal` / `ItemDetailView` components provide basic read-only
detail view with Type/Status/Priority badges, description, metadata fields,
comments, and validation findings. Editing is limited to Title, Description,
Priority, and Status via `ItemEditForm`.

## Required before implementation

1. A separate discussion or accepted specification (new F0xx feature) defining:
   - Detail view information architecture
   - Full list of editable fields
   - Relationship and child item display
   - Comments behavior in the redesign
   - Invalid/partial item handling
   - Required UI test levels (component, functional E2E, browser contract)

## Residual risk

- Current detail view is read-only and limited in editing scope.
  Users cannot edit tags, DOR, DOD, links, attachments, or parent
  relationships through the WebUI. These remain CLI-only.
- Validation issues for individual items are visible in the detail view
  but not actionable through the WebUI (must fix via CLI).

## Next steps

Route a separate feature (e.g., F011) through the full SDD pipeline:
requirements → specification → tests → implementation → validation → review.
