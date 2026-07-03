# F003 CLI Interface — Tasks

| ID | Task | Implements | Status | Depends on |
| --- | --- | --- | --- | --- |
| F003-T1 | Scaffold Typer CLI app with global --json flag and output formatter | F003-R8 | ✅ done | — |
| F003-T2 | Implement `taskpilot init <path>` with workspace creation and project registration | F003-R1 | ✅ done | F001-T2, F002-T1 |
| F003-T3 | Implement `taskpilot project list` command | F003-R3 | ✅ done | F002-T1, F003-T1 |
| F003-T4 | Implement `taskpilot item list`, `show`, `create`, `update` commands | F003-R4 | ✅ done | F002-T2, F003-T1 |
| F003-T5 | Implement explicit relationship commands: parent/unparent, blocks/unblocks, relates/unrelates | F003-R5 | ✅ done | F002-T4, F003-T1 |
| F003-T6 | Implement `taskpilot item comment` command | F003-R6 | ✅ done | F002-T6, F003-T1 |
| F003-T7 | Implement `taskpilot validate` command with structured error output and exit codes | F003-R7 | ✅ done | F001-T7, F003-T1 |
| F003-T8 | Implement `taskpilot serve` command that starts FastAPI server | F003-R2 | stub — blocked on F004 | F004 REST API/server layer |

## Status note

T1–T7 are implemented. T8 (`taskpilot serve`) is a temporary placeholder that
reports the REST API server is unavailable and exits with the system-error code:
the FastAPI/REST server layer it must start belongs to Phase 4 / F004 (WebUI
Workspace — "Backend REST API") and is not yet implemented. Replace the stub with
the real server command once F004 lands.

## Deferred (spec 0002 detail beyond the F003-R1…R8 acceptance table)

Independent code review (F003 branch) surfaced spec-`0002` command-surface detail
not enumerated in this feature's requirements; several need F002 service changes
and are tracked for a follow-up rather than expanding F003 scope:

- `item delete <id>` dedicated command (deletion is currently via
  `item update --status deleted`).
- `item list`: `--priority` filter, a valid/invalid marker column, and
  summary-with-findings JSON that surfaces invalid item files (today invalid
  files are silently skipped by `item_service.list_items`).
- `item show`: embed comments by default (human sections + a `comments` JSON key)
  via `comment_service.list_comments`.
- `item update`: an explicit affordance to clear optional scalars (e.g.
  `description`); only `--parent` has a clear path today (`unparent`).

Applied during review: `serve` default port set to spec value `7152`;
`project list` sorts by project name (id tiebreaker) per spec.

## Notes

- Use Typer's callback for global `--json` option.
- Human output format: table for lists, key-value for show, one-liner for create/update confirmations.
- JSON output uses Pydantic model serialization for deterministic field ordering.
