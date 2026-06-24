# F006 Advanced Views — Requirements

## Summary

Extend the WebUI beyond the basic Kanban board with drag-and-drop status changes, a list view
with sorting and filtering, a tree view showing parent/child hierarchy, and a validation errors
panel. This builds on the F004 workspace foundation.

## Serves

- `roadmap.md` Phase 6 — Better views
- `design.md` — List view, tree view, drag-and-drop interaction

## Functional Requirements

| ID | Requirement | Priority |
| --- | --- | --- |
| F006-R1 | The system shall support dragging Kanban cards between columns to change item status | must |
| F006-R2 | The system shall provide a list view with sortable columns (ID, title, type, status, priority, dates) using TanStack Table | must |
| F006-R3 | The system shall provide filter controls in list view for status, type, priority, and time range | must |
| F006-R4 | The system shall provide a tree view showing expandable parent/child hierarchy based on parent_id | should |
| F006-R5 | The system shall display a validation errors panel showing items/files with validation failures, error messages, and links to open them | should |
| F006-R6 | The system shall provide navigation tabs to switch between Kanban, list, and tree views for the same project | must |

## Acceptance Criteria

- **F006-R1:** Dragging a card from "backlog" to "in_progress" updates the item's status via API, and the card appears in the target column.
- **F006-R2:** Clicking the List tab shows a table with all items. Clicking the "Status" column header sorts by status. Clicking again reverses sort order.
- **F006-R3:** Selecting "type=bug" and "status=done" in list view filters shows only completed bugs.
- **F006-R4:** The tree view shows epics at the root. Expanding an epic reveals its child features. Expanding a feature reveals its child tasks and bugs.
- **F006-R5:** If VP-3.yaml has a missing title, the validation panel lists it with the file path and error message. Clicking the error opens the item modal (if the item partially loaded).
- **F006-R6:** Tabs "Board", "List", "Tree" are visible. Clicking "List" switches from Kanban to list view without losing the selected project.

## Constraints

- Drag-and-drop uses dnd-kit with keyboard alternatives.
- List view uses TanStack Table with client-side sorting and filtering (data already loaded from API).
- Tree view uses parent_id from item data, not a separate hierarchy API.
- Validation panel data comes from a dedicated `/validate` API endpoint.
- View state (selected tab) persists within the session but not across page reloads.

## Out of Scope

- Advanced relation visualization (graph view).
- Custom column configuration (Beta).
- Saved filters or views.
- Export of list/tree to CSV or other formats.
- Swimlanes in Kanban.
