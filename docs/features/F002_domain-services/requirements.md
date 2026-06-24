# F002 Domain Services — Requirements

## Summary

Implement the shared domain/service layer for project, item, comment, and link operations.
This is the single source of business rules used by CLI, REST API, and future MCP adapters.
No UI or I/O adapters — pure business logic operating on validated models.

## Serves

- `roadmap.md` Phase 2 — Domain/service layer
- `idea.md` — shared domain/service layer across adapters

## Functional Requirements

| ID | Requirement | Priority |
| --- | --- | --- |
| F002-R1 | The system shall provide project operations: create project with key and name, read project metadata, list registered projects | must |
| F002-R2 | The system shall provide item operations: create item with mandatory fields, read item by ID, update item fields, list items filterable by project/status/type | must |
| F002-R3 | The system shall enforce type-based parent/child hierarchy rules when setting parent_id | must |
| F002-R4 | The system shall provide link operations: add link (blocks, relates_to), remove link, list links for an item | must |
| F002-R5 | The system shall derive reverse links (blocked_by, related_to) at query time without storing them | must |
| F002-R6 | The system shall provide comment operations: add comment to item, list comments for item chronologically | must |
| F002-R7 | The system shall handle item deletion by setting `status: deleted` and keeping the file | must |
| F002-R8 | The system shall validate operations before writing — reject invalid operations with descriptive errors | must |

## Acceptance Criteria

- **F002-R1:** Creating a project "VoicePilot" with key "VP" writes `project.yaml` with those values and returns the project model.
- **F002-R2:** Updating an item's status from `backlog` to `in_progress` updates `updated_at` and persists the change to the YAML file.
- **F002-R3:** Attempting to set a bug's parent to another bug returns an error; setting a task's parent to a feature succeeds.
- **F002-R4:** Adding `links.blocks: [TP-9]` to TP-3 updates only TP-3's file. The link is queryable from TP-3.
- **F002-R5:** After adding `blocks: TP-9` to TP-3, querying "what blocks TP-9" returns TP-3 through derived reverse links.
- **F002-R6:** Adding a comment to TP-1 creates a timestamped `.md` file in `comments/TP-1/` without updating `TP-1.yaml`.
- **F002-R7:** Deleting TP-5 sets its `status: deleted` in the YAML file; the file remains on disk and is findable by direct lookup.
- **F002-R8:** Attempting to create an item with `status: imaginary_status` returns a validation error and does not write a file.

## Constraints

- Domain layer must not import CLI, FastAPI, or file-system specifics beyond the canonical file access layer (F001).
- All write operations write canonical files first, then notify index (when F005 exists).
- Adding/removing a link updates only the source item file.
- Reverse link derivation must be consistent with the stored link direction.
- No operation silently overwrites or deletes files outside a validated write path.

## Out of Scope

- SQLite index queries (F005).
- Comment edit/delete (Beta).
- Permanent item delete (Beta).
- Project-configured workflow statuses (Beta).
- Bulk operations (future).
