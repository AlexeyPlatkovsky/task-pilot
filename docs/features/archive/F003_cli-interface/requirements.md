# F003 CLI Interface — Requirements

## Summary

Implement the TaskPilot CLI using Typer, providing stable, explicit, and scriptable commands
for AI agents and developers. All read commands support JSON output. All commands route through
the shared domain service layer (F002). Exit codes are deterministic. Error messages are
actionable.

## Serves

- `roadmap.md` Phase 3 — CLI
- `idea.md` — CLI is the primary AI-facing interface

## Functional Requirements

| ID | Requirement | Priority |
| --- | --- | --- |
| F003-R1 | The system shall provide `taskpilot init <path>` to initialize a workspace and register the project | must |
| F003-R2 | The system shall provide `taskpilot serve` to start the local REST API server on a configurable port | must |
| F003-R3 | The system shall provide `taskpilot project list` with human-readable and JSON output | must |
| F003-R4 | The system shall provide `taskpilot item list`, `item show`, `item create`, and `item update` with field validation and JSON output | must |
| F003-R5 | The system shall provide explicit relationship commands: `item parent`, `item unparent`, `item blocks`, `item unblocks`, `item relates`, and `item unrelates` | must |
| F003-R6 | The system shall provide `taskpilot item comment <ID> "<text>"` for adding comments | must |
| F003-R7 | The system shall provide `taskpilot validate` reporting all validation errors with exit code 0 on clean, non-zero on errors | must |
| F003-R8 | Read and write commands shall support `--json` where applicable, producing deterministic JSON output to stdout | must |

## Acceptance Criteria

- **F003-R1:** `taskpilot init .` creates `.taskpilot/` structure and registers the current project.
- **F003-R2:** `taskpilot serve --port 8080` starts a server listening on port 8080. Output confirms the URL.
- **F003-R3:** `taskpilot project list --json` outputs a JSON array of project objects with deterministic field ordering.
- **F003-R4:** `taskpilot item create --title "Task" --type task` in the current project repository creates a new item and prints its ID.
- **F003-R5:** `taskpilot item blocks VP-1 VP-2` adds the link; running it again is idempotent.
- **F003-R6:** `taskpilot item comment VP-1 "Reviewed implementation"` creates a comment file and prints the filename.
- **F003-R7:** `taskpilot validate` with a valid workspace outputs nothing to stderr and exits 0; with invalid items, lists errors to stderr and exits non-zero.
- **F003-R8:** Two successive calls to `taskpilot item list --json` from the same project repository with no changes produce byte-identical output.

## Constraints

- CLI must call F002 domain services directly — not through HTTP.
- JSON output fields are ordered deterministically.
- JSON output goes to stdout; human output to stdout; errors to stderr.
- Exit code 0 = success, 1 = user error, 2 = system error.
- `--json` is supported by read commands and write commands, producing deterministic operation results where applicable.
- All field values validated before files are touched.

## Out of Scope

- `taskpilot sync` commands (F007).
- Interactive mode or prompts.
- Shell completion (future).
- Colored output in JSON mode.
- Dry-run mode (future).
