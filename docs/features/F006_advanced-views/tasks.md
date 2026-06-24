# F006 Advanced Views — Tasks

| ID | Task | Implements | Status | Depends on |
| --- | --- | --- | --- | --- |
| F006-T1 | Add dnd-kit to Kanban board: drag cards between columns, update status via API on drop | F006-R1 | todo | F004-T3, F004-T4 |
| F006-T2 | Implement list view component with TanStack Table: columns for ID, title, type, status, priority, dates | F006-R2 | todo | F004-T3, API for item list |
| F006-T3 | Implement sorting in list view: click column header to sort asc/desc | F006-R2 | todo | F006-T2 |
| F006-T4 | Implement filter bar for list view: dropdowns for status, type, priority; preset time ranges | F006-R3 | todo | F006-T2 |
| F006-T5 | Implement tree view component: build tree from parent_id, expand/collapse nodes | F006-R4 | todo | F004-T3, API for items |
| F006-T6 | Implement validation errors panel: fetch validation results, display errors with file paths, link to items | F006-R5 | todo | API for validation |
| F006-T7 | Implement view navigation tabs (Board / List / Tree) with state management | F006-R6 | todo | F004-T3 |

## Notes

- dnd-kit collision detection should use `closestCenter` for column-to-column drops.
- Keyboard alternatives for drag-and-drop: select card, press key to move left/right through statuses.
- Tree view uses a recursive component to render nested children.
- Filter state clears when switching projects.
