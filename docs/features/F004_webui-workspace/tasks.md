# F004 WebUI Workspace — Tasks

| ID | Task | Implements | Status | Depends on |
| --- | --- | --- | --- | --- |
| F004-T1 | Scaffold React+Vite+TypeScript project with CSS Modules, Radix UI, TanStack Query, React Hook Form | F004-R1 | done | — |
| F004-T2 | Implement project selector component with loading, empty, and error states | F004-R1 | done | F004-T1, API endpoint for projects |
| F004-T3 | Implement Kanban board layout with fixed columns and per-column scrolling | F004-R2 | done | F004-T1 |
| F004-T4 | Implement Kanban card component with ID, title, type icon, priority badge | F004-R3 | done | F004-T3, API endpoint for items |
| F004-T5 | Implement item detail modal in read mode: all fields, links, comments displayed | F004-R4 | done | F004-T4, API endpoint for item details |
| F004-T6 | Implement item detail modal in edit mode for title, description, priority, and status with validation and save/cancel | F004-R5 | done | F004-T5, React Hook Form |
| F004-T7 | Implement read-only comment thread component | F004-R6 | done | F004-T5, item detail API comments |
| F004-T8 | Implement delete action with confirmation using status `deleted` | F004-R7 | done | F004-T5 |
| F004-T9 | Add dnd-kit Kanban drag/drop for valid cards with API status updates and keyboard alternatives | F004-R9 | done | F004-T3, F004-T4 |

## Notes

- Review-fix pass 2026-06-25: fixed drag/drop mutation timing (handleDragEnd only), added Markdown rendering with DOMPurify, added KanbanBoard error/loading/retry states, added ItemModal retry button, extracted shared label constants, tightened Zod schema with EDITABLE_STATUSES, added Vitest component test suite (25 tests).
- TanStack Query manages server state with cache invalidation on mutations.
- CSS Modules naming: `ComponentName.module.css` co-located with component files.
- Type definitions shared between frontend and backend through OpenAPI schema or a shared types package (future).
- Initially, mock API responses can be used for frontend development before the FastAPI server is ready.
- Drag/drop does not apply to invalid item cards.
