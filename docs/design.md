# Design

> Design token reference, icon library, and Pencil design file conventions: see `.claude/docs/design-book.md`.

## UX Principles

- **Local-first feel**: the WebUI should feel instant, with no loading spinners for normal
  operations. All data is on the local machine.
- **Kanban as home**: the primary workspace is a Kanban board. Users land there after project
  selection.
- **Modal editing**: opening an item opens a modal on the current page. Users should not navigate
  away from their board or list to edit an item.
- **Minimal chrome**: the interface should prioritize task content over navigation and toolbars.
- **Visible errors**: validation issues are surfaced in a dedicated panel. Invalid items are never
  silently hidden.

## Screen Inventory

| Screen | Purpose | Key states |
| --- | --- | --- |
| Project selector | Choose which registered project to work on | empty (no projects), listing, error |
| Kanban board | Primary workspace with columns by status | empty columns, populated, drag in progress |
| List view | Tabular filterable/sortable item list | empty, populated, filtered empty |
| Tree view | Expandable parent/child hierarchy | empty, populated, loading branch |
| Item detail modal | View and edit a single item | view mode, edit mode, save error, delete confirm |
| Validation panel | Show items/files with validation errors | empty (all valid), list of errors |

## Project Selector

The first screen after `taskpilot serve`. Shows a list of registered projects with their display
names and keys. A project can be disabled locally without changing the repository.

States:
- **Empty**: No registered projects. Show a message with the `taskpilot init .` command hint.
- **Populated**: List of projects. Clicking one navigates to its Kanban board.
- **Error**: A registered project has an unreadable root. Show warning with path.

## Kanban Board

The primary workspace page for a selected project.

### Layout

Five columns fixed in Alpha: backlog, ready, in_progress, done, cancelled. Deleted items are hidden
from the normal board.

Within each column, cards are sorted by type order then numeric item ID:
epic > feature > task > bug.

### Card

Each card shows: item ID, title, type icon/label, priority indicator. Cards are compact and
single-line where possible.

### Interaction

- Clicking a card opens the item detail modal.
- Drag a card to another column to change its status.
- Drag and drop uses the library specified in `architecture.md`.
- Columns scroll independently on overflow.

### States

- **Empty board**: All columns empty. Show a prompt to create the first item with the CLI.
- **Populated board**: Cards visible across columns.
- **All items in one column**: Normal state. Columns may be empty.

## Item Detail Modal

The core interaction surface for viewing and editing an item.

### View mode

Displays read-only: item ID, title, type, status, priority, description (rendered Markdown),
parent item link, child items list, blocking relationships, related items, DOR/DOD checklists,
tags, attachments, external references, comments thread, created/updated timestamps and authors.

### Edit mode

Toggled by an Edit button. Alpha fields become editable:
- title (text input);
- description (textarea or Markdown editor);
- priority (dropdown: low, normal, high);
- status (dropdown: backlog, ready, in_progress, done, cancelled).

All other Alpha item fields are visible read-only until later phases.

Save commits changes. Cancel reverts. Validation errors surface inline near the offending field.

### Comment thread

Comments display in chronological order with author and timestamp. Comments are read-only in the
Alpha WebUI. Comment creation is available through the CLI and moves into the WebUI later.

### Actions

- Edit (toggle edit mode);
- Delete (sets status: deleted, with confirmation dialog).

### States

- **Loading**: The modal background appears with the item ID visible. Content loads in place.
- **Not found**: Item ID doesn't resolve. Show error message.
- **Validation error**: Item file exists but has validation errors. Show a warning banner and
  display what fields parsed successfully.
- **Edit conflict**: Item was modified between open and save. Show conflict message with option
  to reload or force save.
- **Save error**: Backend rejected the write. Show error message with details.

## List View

An alternative to the Kanban board with tabular layout.

Columns: ID, title, type, status, priority, created_at, updated_at.

Supports sorting by any column, filtering by status, type, priority, and time range (all, last 7
days, last 14 days, last month). Uses TanStack Table.

Clicking a row opens the item detail modal.

## Tree View

Expandable hierarchy showing parent/child relationships through parent_id links.

Root items (epics) are top-level nodes. Expanding a node reveals its children. Items without a
parent appear at the root level.

Tree view is structurally derived from parent_id; it is not a graph view showing all link types.

## States

Every view and component handles:
- **Empty**: no data yet, with a contextual call to action.
- **Loading**: data is being fetched (edge case in local-first, but handled for initial load).
- **Error**: data could not be loaded, with an actionable message.
- **Populated**: normal state with data visible.

## Accessibility

- All interactive elements are keyboard-navigable.
- Modal uses Radix UI dialog primitives for focus trapping and screen reader announcements.
- Drag and drop has keyboard alternatives for status changes.
- Color is not the only indicator for priority — text labels accompany color badges.
- Form fields have associated labels.
- Error messages are announced to screen readers.
- Color token pairs used in this product meet WCAG AA contrast for all text sizes defined in `web/src/tokens.css`.
