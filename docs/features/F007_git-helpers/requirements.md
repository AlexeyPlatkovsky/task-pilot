# F007 Git Helpers — Requirements

## Summary

Provide CLI commands that make Git-based synchronization transparent and safe. Commands wrap
common Git operations over the `.taskpilot/` task files, surfacing changed items, validating
before commit, and offering optional pull/push wrappers. All operations remain transparent —
the user can always fall back to raw Git commands.

## Serves

- `roadmap.md` Phase 7 — Git helpers
- `idea.md` — Git-friendly synchronization through text files

## Functional Requirements

| ID | Requirement | Priority |
| --- | --- | --- |
| F007-R1 | The system shall provide `taskpilot sync status` showing which task files have uncommitted changes | should |
| F007-R2 | The system shall provide `taskpilot sync validate` that runs validation and blocks commit-like operations if errors exist | should |
| F007-R3 | The system shall provide `taskpilot sync pull` that runs `git pull --rebase` and then `taskpilot index rebuild` | could |
| F007-R4 | The system shall provide `taskpilot sync push` that stages `.taskpilot/` files, commits with a standard message, and pushes | could |
| F007-R5 | The system shall provide `taskpilot sync export` to produce a summary of changed task files since a given ref | could |

## Acceptance Criteria

- **F007-R1:** After editing VP-1, `taskpilot sync status` lists `items/VP-1.yaml` as modified.
- **F007-R2:** With an invalid item file present, `taskpilot sync validate` exits non-zero and lists the errors.
- **F007-R3:** `taskpilot sync pull` rebases, then rebuilds the index successfully.
- **F007-R4:** `taskpilot sync push` stages `.taskpilot/` files, commits with message "Update TaskPilot tasks", and pushes to the remote.
- **F007-R5:** `taskpilot sync export --since HEAD~3` outputs a summary of changed items and comments over the last 3 commits.

## Constraints

- All sync commands are transparent wrappers around Git operations — no hidden sync logic.
- Sync commands print the underlying Git commands they execute.
- Push and pull commands confirm before executing destructive operations (or use a `--force`/`--yes` flag).
- Sync commands never modify files outside `.taskpilot/`.
- Index rebuild after pull is automatic.

## Out of Scope

- Conflict resolution helpers (future).
- `taskpilot repair` for fixing corrupted files.
- `taskpilot conflicts explain` for human-readable conflict summaries.
- Automatic sync on a schedule or file watcher.
- Sync with non-Git remotes.
