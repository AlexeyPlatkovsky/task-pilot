# F004 WebUI Workspace — Tasks

| ID | Task | Implements | Status | Depends on |
| --- | --- | --- | --- | --- |
| F004-T1 | Scaffold React+Vite+TypeScript project with CSS Modules, Radix UI, TanStack Query, React Hook Form | F004-R1 | todo | — |
| F004-T2 | Implement project selector component with loading, empty, and error states | F004-R1 | todo | F004-T1, API endpoint for projects |
| F004-T3 | Implement Kanban board layout with fixed columns and per-column scrolling | F004-R2 | todo | F004-T1 |
| F004-T4 | Implement Kanban card component with ID, title, type icon, priority badge | F004-R3 | todo | F004-T3, API endpoint for items |
| F004-T5 | Implement item detail modal in read mode: all fields, links, comments displayed | F004-R4 | todo | F004-T4, API endpoint for item details |
| F004-T6 | Implement item detail modal in edit mode: form fields with validation, save/cancel | F004-R5 | todo | F004-T5, React Hook Form |
| F004-T7 | Implement comment thread component with add comment functionality | F004-R6 | todo | F004-T5, API endpoint for comments |
| F004-T8 | Implement modal actions: add link dialog, create child item, delete with confirmation | F004-R7 | todo | F004-T5 |

## Notes

- TanStack Query manages server state with cache invalidation on mutations.
- CSS Modules naming: `ComponentName.module.css` co-located with component files.
- Type definitions shared between frontend and backend through OpenAPI schema or a shared types package (future).
- Initially, mock API responses can be used for frontend development before the FastAPI server is ready.
