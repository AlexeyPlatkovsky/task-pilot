# Design

> Design token reference, icon library, accessibility rules, and MCP tool constraints: see `designs/design.md`.
> TaskPilot inherits its base visual language from the Agent Manifesto design system and extends it
> with local-first product UI states, dark theme, status, priority, and feedback tokens.

## UX Principles

- **Local-first feel**: the WebUI should feel instant, with no loading spinners for normal
  operations. All data is on the local machine.
- **Desktop-only workspace**: TaskPilot is a local desktop WebUI. It supports constrained desktop
  windows, but does not provide mobile or tablet layouts.
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

## Application Header

The header appears on every screen. It displays the TaskPilot compass board logo (`designs/task-pilot-compass-board.svg`, also used as the favicon), the product name "TaskPilot", and the project selector dropdown. The header is styled with `--surface-base` background, a `--border-subtle` bottom border, and rounded corners.

## Project Selector

The first screen after `taskpilot serve`. Shows a list of registered projects with their display
names and keys. A project can be disabled locally without changing the repository.

The project selector uses the shared dropdown selector pattern defined in `designs/design.md`.
Its dimensions may be wider than compact filters, but the trigger, arrow, selected option
highlight, hover/focus state, and below-menu behavior match list filters and the theme selector.

States:
- **Empty**: No registered projects. Show a message with the `taskpilot init .` command hint.
- **Populated**: List of projects. Clicking one navigates to its Kanban board.
- **Error**: A registered project has an unreadable root. Show warning with path.

## Kanban Board

The primary workspace page for a selected project.

### Layout

Five columns fixed in Alpha: backlog, ready, in_progress, done, cancelled. Deleted items are hidden
from the normal board.

The board is designed for desktop use. The supported app viewport starts at `1280px`; `1440px` is
the comfortable target, and the primary workspace caps at `1760px` to preserve readable scan
distances on large displays. In narrower desktop windows, the board keeps its column structure and
uses horizontal scrolling instead of switching to a mobile/tablet layout.

Kanban columns use a minimum readable width of `248px` with token-based spacing between columns.
Columns stretch with `1fr` to fill the board up to the primary workspace cap instead of using a
fixed maximum column width.

Runtime layout values are tokenized as `--viewport-min-width`, `--content-width-comfortable`,
`--content-max-width`, and `--kanban-column-min`. `--kanban-column-max` is deprecated and should
not be used for active Kanban layout.

The column title/code block aligns with card text inside the same lane. The count badge remains
aligned to the header edge.

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

List filters use the shared dropdown selector pattern defined in `designs/design.md`. Filter labels
and triggers sit on the same row. A trailing Clear button resets all filters to default values and
restores the unfiltered list.

Sortable headers use the canonical top/down arrow indicators from `designs/design.md`: `△▽` by
default, `▲▽` for ascending, and `△▼` for descending.

Clicking a row opens the item detail modal.

Tables preserve their tabular structure in constrained desktop windows and use horizontal overflow
when needed. They do not collapse into stacked mobile rows.

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
- Shared dropdown selectors have button triggers, listbox options, selected-state announcement,
  Escape/blur close behavior, and visible focus.
- Modal uses Radix UI dialog primitives for focus trapping and screen reader announcements.
- Drag and drop has keyboard alternatives for status changes.
- Color is not the only indicator for priority — text labels accompany color badges.
- Form fields have associated labels.
- Error messages are announced to screen readers.
- Color token pairs used in this product meet WCAG AA contrast for all text sizes defined in `web/src/tokens.css`.
