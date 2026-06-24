# F005 SQLite Index — Requirements

## Summary

Build a disposable local SQLite database under `.taskpilot/cache/index.db` to provide fast
sorting, filtering, and querying for the WebUI. The index is rebuilt from canonical YAML and
Markdown files on demand or when files change. It contains no unique source-of-truth data and
can be deleted and rebuilt safely.

## Serves

- `roadmap.md` Phase 5 — SQLite index/cache
- `architecture.md` — SQLite index/cache component

## Functional Requirements

| ID | Requirement | Priority |
| --- | --- | --- |
| F005-R1 | The system shall build a SQLite index from all canonical item and comment files under `.taskpilot/` | must |
| F005-R2 | The system shall provide a `taskpilot index rebuild` command that regenerates the entire index | must |
| F005-R3 | The system shall provide a `taskpilot index status` command reporting index freshness and item count | should |
| F005-R4 | The index shall support queries equivalent to item list with filtering by project, status, type, and priority | must |
| F005-R5 | The index shall derive and cache reverse links so queries for blocked_by and related_to are fast | must |
| F005-R6 | The index shall be stored under `.taskpilot/cache/index.db` and excluded from Git by default | must |
| F005-R7 | All write operations shall update canonical files first, then refresh or incrementally update the index | must |

## Acceptance Criteria

- **F005-R1:** Running `taskpilot index rebuild` after creating items through the domain layer produces an `index.db` with the same item count.
- **F005-R2:** Deleted `index.db` is fully restored after running `taskpilot index rebuild`.
- **F005-R3:** `taskpilot index status` shows item count, last rebuild timestamp, and whether the index is stale relative to file modification times.
- **F005-R4:** Querying items with `status=ready AND type=task` through the index returns the same result set as scanning all YAML files.
- **F005-R5:** After adding `blocks: VP-2` to VP-1 and rebuilding the index, querying blocked_by for VP-2 returns VP-1 without scanning all files.
- **F005-R6:** `.gitignore` includes `.taskpilot/cache/` by default when workspace is initialized.
- **F005-R7:** Creating an item writes the YAML file first, then the item is immediately queryable through the index.

## Constraints

- SQLite library accessible from Python (via `better-sqlite3` or `sqlite3` from stdlib).
- Index schema mirrors the canonical model — no new fields invented in the index.
- Index rebuild is idempotent — multiple rebuilds produce the same state.
- Index is not committed to Git.
- File watcher (auto-rebuild) is optional and deferred to Beta.

## Out of Scope

- Incremental index updates on individual file changes (full rebuild is acceptable for Alpha).
- File watcher for auto-rebuild.
- Full-text search index.
- Index sharding or performance optimization beyond correctness.
- Index for comments beyond basic listing.
