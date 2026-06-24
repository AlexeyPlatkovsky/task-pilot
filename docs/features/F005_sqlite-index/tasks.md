# F005 SQLite Index — Tasks

| ID | Task | Implements | Status | Depends on |
| --- | --- | --- | --- | --- |
| F005-T1 | Design SQLite schema: items table, links table, comments table matching canonical model | F005-R1, F005-R4 | todo | F001-T3 |
| F005-T2 | Implement index builder: iterate canonical files, parse with F001 parsers, insert into SQLite | F005-R1 | todo | F005-T1, F001-T3, F001-T5 |
| F005-T3 | Implement `taskpilot index rebuild` CLI command (full teardown + build) | F005-R2 | todo | F005-T2, F003-T1 |
| F005-T4 | Implement `taskpilot index status` CLI command (item count, rebuild timestamp, staleness check) | F005-R3 | todo | F005-T2, F003-T1 |
| F005-T5 | Implement indexed item query: filter by project, status, type, priority, sort by type+id | F005-R4 | todo | F005-T1, F005-T2 |
| F005-T6 | Implement reverse link derivation in index: populate blocked_by, related_to columns on rebuild | F005-R5 | todo | F005-T1, F005-T2 |
| F005-T7 | Update `.taskpilot/.gitignore` to include `cache/` directory | F005-R6 | todo | F001-T2 |
| F005-T8 | Integrate write operations: update index after canonical file writes | F005-R7 | todo | F005-T2, F002-T2, F002-T4, F002-T6 |

## Notes

- Use `CREATE TABLE IF NOT EXISTS` to make rebuild idempotent.
- Reverse links stored as indexed columns, derived during rebuild, not persisted in item files.
- Index freshness determined by comparing `MAX(file_mtime)` against index rebuild timestamp.
