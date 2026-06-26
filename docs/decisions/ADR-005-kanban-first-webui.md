# ADR-005: Kanban Board as Primary Workspace Page

- **Status:** ✅ accepted
- **Date:** 2026-06-23
- **Deciders:** TaskPilot project

## Context

The WebUI needs a primary workspace page — the default view after project selection. The
options are a list view (table of items, common in issue trackers), a Kanban board (columns
by status), or a tree view (parent/child hierarchy).

The choice shapes the user's mental model of their work. A list emphasizes individual items
and filtering. A Kanban board emphasizes workflow state and movement. A tree view emphasizes
structure and decomposition.

TaskPilot's target users (local developers and AI agents) benefit most from seeing work state
at a glance and moving items through a workflow. The workflow is intentionally simple (6
statuses in Alpha), making Kanban a natural fit.

## Decision

The primary workspace page is a Kanban board with columns for each workflow status (backlog,
ready, in_progress, done, cancelled). Deleted items are hidden by default. Cards are sorted
by type order (epic > feature > task > bug) then numeric item ID.

List view and tree view are secondary views available alongside the Kanban board.

## Consequences

- Users land on a visual workflow board, not a flat list.
- The workflow drives the primary interaction pattern (moving items between columns).
- Drag-and-drop status changes are intuitive and can be added later (Release).
- Opening an item uses a modal, keeping the board context visible.
- Sorting within columns by type+id provides stable visual order.
- Future custom status columns (Beta) extend naturally from the Kanban layout.
- A list-first approach would have prioritized filtering and sorting over workflow visualization.

## Alternatives Considered

- **List/table as primary** — rejected because the workflow is simple enough that a Kanban
  communicates state more effectively, and list views can still be a secondary tab.
- **Tree view as primary** — rejected because not all items have parent/child relationships,
  and a tree does not communicate workflow state as clearly as columns.
- **Dashboard/summary page** — rejected as unnecessary for a focused local tool; a board
  with all items is a sufficient starting point.
