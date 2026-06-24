# F002 Domain Services — Tasks

| ID | Task | Implements | Status | Depends on |
| --- | --- | --- | --- | --- |
| F002-T1 | Implement project service: create, read, list operations against `project.yaml` | F002-R1 | todo | F001-T1 |
| F002-T2 | Implement item service: create, read by ID, update fields, list with filters | F002-R2 | todo | F001-T3, F001-T4 |
| F002-T3 | Implement hierarchy validation: enforce type-based parent/child rules on parent_id changes | F002-R3 | todo | F002-T2 |
| F002-T4 | Implement link service: add link, remove link, query links for an item | F002-R4 | todo | F002-T2 |
| F002-T5 | Implement reverse link derivation: compute blocked_by and related_to from stored links | F002-R5 | todo | F002-T4 |
| F002-T6 | Implement comment service: add comment with timestamp filename, list comments chronologically | F002-R6 | todo | F001-T5, F001-T6 |
| F002-T7 | Implement item deletion: set status to deleted, preserve file, handle already-deleted items | F002-R7 | todo | F002-T2 |
| F002-T8 | Implement pre-write validation: validate operation input before touching filesystem | F002-R8 | todo | F001-T7, F002-T2 |

## Notes

- Services should be stateless — file state is read and written, not held in memory.
- Link service should validate that target item IDs exist.
- `next_id` allocation scans existing item filenames for the next numeric suffix. Gaps from deleted items are allowed.
