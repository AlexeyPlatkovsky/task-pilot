# F006 Advanced Views — Tasks

| ID | Task | Implements | Status | Depends on |
| --- | --- | --- | --- | --- |
| F006-T1 | Implement list view component with TanStack Table: columns for ID, title, type, status, priority, dates | F006-R1 | ⏳ todo | F004-T3, API for item list |
| F006-T2 | Implement sorting in list view: click column header to sort asc/desc | F006-R1 | ⏳ todo | F006-T1 |
| F006-T3 | Implement filter bar for list view: dropdowns for status, type, priority; preset time ranges | F006-R2 | ⏳ todo | F006-T1 |
| F006-T4 | Implement tree view component: build tree from parent_id, expand/collapse nodes | F006-R3 | ⏳ todo | F004-T3, API for items |
| F006-T5 | Implement validation errors panel: fetch validation results, display errors with file paths, link to items | F006-R4 | ⏳ todo | API for validation |
| F006-T6 | Implement view navigation tabs (Board / List / Tree) with state management | F006-R5 | ⏳ todo | F004-T3 |

## Notes

- Tree view uses a recursive component to render nested children.
- Filter state clears when switching projects.
