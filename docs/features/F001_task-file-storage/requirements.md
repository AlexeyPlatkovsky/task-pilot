# F001 Task File Storage — Requirements

## Summary

Define the `.taskpilot/` workspace folder layout and implement deterministic parsing and writing
of canonical YAML item files and Markdown comment files. This is the storage foundation — every
other feature reads and writes through this layer. One file per item minimizes Git conflicts.

## Serves

- `roadmap.md` Phase 1 — File model and parser
- `idea.md` — local-first task graph with file-based storage

## Functional Requirements

| ID | Requirement | Priority |
| --- | --- | --- |
| F001-R1 | The system shall initialize a `.taskpilot/` workspace with `project.yaml`, `items/`, `comments/`, and `cache/` directories | must |
| F001-R2 | The system shall parse item YAML files from `.taskpilot/items/*.yaml` into a structured model with all mandatory and optional fields | must |
| F001-R3 | The system shall write item YAML files with deterministic formatting, preserving field order and stable output on re-serialization | must |
| F001-R4 | The system shall parse comment Markdown files from `.taskpilot/comments/<ITEM_ID>/*.md` with YAML frontmatter and Markdown body | must |
| F001-R5 | The system shall write comment files with deterministic filename timestamps, including disambiguation suffix on second-resolution collisions | must |
| F001-R6 | The system shall validate item files for required fields, valid field values, unique IDs, and valid project references | must |
| F001-R7 | The system shall report validation errors without blocking loading of valid items — invalid files remain visible and actionable | must |

## Acceptance Criteria

- **F001-R1:** Running `taskpilot init .` in an empty directory creates the full `.taskpilot/` tree with default `project.yaml`.
- **F001-R2:** Given a directory of valid `.taskpilot/items/*.yaml` files, parsing produces a list of item models with all fields populated.
- **F001-R3:** Writing an item, reading it back, and writing again produces byte-identical output.
- **F001-R4:** Given a `comments/TP-1/` directory with `.md` files, parsing produces a chronologically ordered list of comment models.
- **F001-R5:** Two comments created in the same second receive filenames like `2026-06-23T10-00-00Z.md` and `2026-06-23T10-00-00Z_2.md`.
- **F001-R6:** An item file missing `title` produces a validation error listing the missing field and the file path.
- **F001-R7:** A project with 5 valid items and 1 invalid item loads 5 items and surfaces the 1 error — no items are silently dropped.

## Constraints

- File paths use `/` separators regardless of platform.
- Item file encoding is UTF-8.
- `project.yaml` is canonical, not a system registry file.
- Attachment paths in item YAML must be relative and must not escape the repository root.
- The `cache/` directory is Git-ignored and contains no source-of-truth data.

## Out of Scope

- SQLite index/cache implementation (F005).
- File watching for auto-rebuild (F005).
- Comment edit/delete (Beta).
- Project file schema beyond initialization defaults.
- Migration between storage format versions.
