# F004 WebUI Workspace — Requirements

## Summary

Implement the local browser-based WebUI with the Kanban board as the primary workspace page,
project selector, item detail modal with edit capability, and comment thread. The WebUI calls
the REST API (FastAPI) and does not reimplement domain logic. Built with React, Vite,
TypeScript, CSS Modules, and Radix UI primitives.

## Serves

- `roadmap.md` Phase 4 — Local WebUI
- `idea.md` — local WebUI for humans
- `design.md` — Kanban board, item modal, project selector

## Functional Requirements

| ID | Requirement | Priority |
| --- | --- | --- |
| F004-R1 | The system shall display a project selector listing all registered projects with their names and keys | must |
| F004-R2 | The system shall display a Kanban board with fixed columns (backlog, ready, in_progress, done, cancelled) for the selected project | must |
| F004-R3 | Kanban cards shall display item ID, title, type icon/label, and priority indicator, sorted by type order then numeric ID within each column | must |
| F004-R4 | Clicking a Kanban card shall open an item detail modal showing all item fields, links, and comments in read mode | must |
| F004-R5 | The item detail modal shall support edit mode for title, description, priority, type, status, parent_id, tags, dor, dod, attachments, and external_refs | must |
| F004-R6 | The item detail modal shall display a comment thread and allow adding new comments | must |
| F004-R7 | The item detail modal shall provide actions to add links, create child items, and delete (set status: deleted) with confirmation | must |
| F004-R8 | The system shall handle empty, loading, and error states gracefully in all views | must |

## Acceptance Criteria

- **F004-R1:** Navigating to the WebUI when no projects are registered shows a message with the `taskpilot register .` command. When projects exist, they are listed and clickable.
- **F004-R2:** Selecting a project displays a Kanban board with visible columns, even if some are empty.
- **F004-R3:** Within the `backlog` column, epics sort before features, which sort before tasks, which sort before bugs. Items with the same type sort by numeric ID ascending.
- **F004-R4:** Clicking a task card opens a modal. The modal shows the task title, type badge, status badge, priority label, description (rendered Markdown), parent, children, links, and comments.
- **F004-R5:** Clicking Edit in the modal switches fields to editable inputs. Changing status to `in_progress` and saving updates the card position on the Kanban board.
- **F004-R6:** The comment thread shows existing comments in chronological order. Typing a message and submitting adds a new comment visible immediately.
- **F004-R7:** Clicking Add Link opens a search/select for target items. Clicking Delete shows a confirmation dialog and then sets status to `deleted`.
- **F004-R8:** A project with zero items shows an empty board with a prompt to create the first item. A slow API call shows a loading indicator. An API error shows a retryable error message.

## Constraints

- WebUI calls FastAPI REST API only — no direct filesystem access.
- All form validation feedback is inline near the offending field.
- Modals use Radix UI dialog primitives for focus trapping and accessibility.
- The Kanban board handles overflow with per-column scrolling.
- CSS Modules for styling — no global CSS except reset/normalization.
- TypeScript with strict mode.

## Out of Scope

- Drag-and-drop to change status (F006).
- List view and tree view (F006).
- Filters and sorting controls (F006).
- Validation/errors panel (F006).
- Real-time updates (no WebSocket).
- Mobile/responsive layout (future).
- Dark mode (future).
