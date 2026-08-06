# Auto Archive: archive done/cancelled/deleted items after inactivity window

Status: in progress

## Outcome

Items with status `done`, `cancelled`, or `deleted` are automatically archived once their
`updated_at` timestamp exceeds a configurable age (default 14 days). Archived items are
moved to a dedicated subfolder under `.taskpilot/`, remain queryable through a new "Archived"
board tab, and can be unarchived back to their original location. A periodic background check
runs roughly every 3 hours when the runtime allows, with a manual/on-demand CLI command and
API endpoint available in environments without a scheduler.

## Context

TaskPilot currently preserves `deleted` items (soft-delete) and includes `done` and
`cancelled` items in default listings. As a workspace accumulates historical items, the
`items/` directory grows with items that are no longer actively worked on, creating noise
in listings, board views, and Git diffs. The product invariant states that invalid files
remain visible and actionable, but there is no equivalent invariant for completed or
cancelled items: they should be movable without disappearing.

The epic description (TP-110) identifies five scope deltas requiring explicit approval:
canonical on-disk layout change (archive subfolder), new persisted setting, new board/API
surface, and background mutation of task data without user action. This specification
addresses each delta.

## Scope

### In scope

- Archive-threshold project setting: stored in `project.yaml` as `archive_threshold_days`
  (integer, default 14, minimum 1, maximum 3650), settable via a new CLI subcommand
  `taskpilot project archive-threshold` and a PATCH endpoint on `/api/project`.
- Periodic archive check: a background task that runs roughly every 3 hours, scanning for
  items with status `done`, `cancelled`, or `deleted` whose `updated_at` exceeds the
  threshold. In environments without a scheduler (CLI foreground mode), a manual
  `taskpilot archive run` command and a `POST /api/projects/{project_id}/archive/run`
  endpoint trigger the same logic on demand.
- One-time migration: a CLI command `taskpilot archive migrate` and a `POST` endpoint that
  scans all existing items matching the archive criteria and archives them in a single
  pass, producing a summary of moved items.
- Archived board: an always-visible fourth tab in the WebUI (alongside Board and List) that
  surfaces archived items as a compact, non-columnar list. The list is ordered by item type
  (epic, feature, task, bug), then by numeric item ID; archived items retain their status
  indicators and can be opened for read-only detail inspection.
- Unarchive path: CLI command `taskpilot archive unarchive <item-id>` and API endpoint
  `POST /api/projects/{project_id}/items/{item_id}/unarchive` that moves an archived item
  back to `items/` with its original status restored.
- Canonical on-disk layout: archived items are stored under
  `.taskpilot/archived/YYYY-MM/`, selected from their immutable `archived_at` timestamp.
  Each month contains one YAML file per item (same format as `items/`) and a `metadata.json`
  document tracking the original project key and archive timestamp. Existing root-level
  archive data remains readable until an explicit, idempotent storage migration moves it.
- Cross-storage relationships: archiving an item does not invalidate its existing `parent_id`,
  forward links, derived reverse links, or children. Relationship resolution treats active and
  archived canonical items as one project graph without writing duplicate relationship data.

### Out of scope

- Configurable archive schedules (fixed at ~3 hours; no cron expressions).
- Per-project archive thresholds beyond the single `project.yaml` field (per-project
  override was considered but deferred).
- Hard delete of archived items (archived items are never permanently removed; they can
  always be unarchived).
- Archive notifications or audit log entries (Git history serves as the audit trail).
- Search or filtering of archived items beyond the Archived board view (List and Board
  views exclude archived items by default).
- Import/export of archived items as a batch operation.

## Requirements

### Functional

F1. The system stores an `archive_threshold_days` field in `project.yaml` with a default
    value of 14. The field is an integer between 1 and 3650.

F2. Items with status `done`, `cancelled`, or `deleted` whose `updated_at` exceeds
    `archive_threshold_days` days from the current time are eligible for archiving.

F3. A periodic background task scans eligible items and moves them to
    `.taskpilot/archived/` once every ~3 hours, when the runtime permits.
    In server mode, every active workspace registered with the running server receives an
    independent periodic check.

F4. A manual CLI command `taskpilot archive run` and API endpoint
    `POST /api/projects/{project_id}/archive/run` trigger the same archive logic on demand.

F5. A one-time migration command `taskpilot archive migrate` and API endpoint
    `POST /api/projects/{project_id}/archive/migrate` scan all existing items matching
    the archive criteria and archive them in a single pass, producing a summary.

F6. A new "Archived" tab is always present in project workspace navigation. It surfaces
    archived items as a plain, non-columnar list ordered by type (epic, feature, task, bug)
    and then numeric item ID.

F7. Archived items can be unarchived via CLI command `taskpilot archive unarchive
    <item-id>` and API endpoint `POST /api/projects/{project_id}/items/{item_id}/unarchive`,
    restoring them to `.taskpilot/items/` with their original status.

F8. Archived item files use the same YAML format as active items, preserving all fields.

F9. The `metadata.json` index under `.taskpilot/archived/` records the original item ID,
    original project key, archive timestamp, and original status for each archived item.

F10. Default listings (Board, List) exclude archived items. The Archived board shows only
     archived items.

F11. Archive files and metadata are partitioned by the UTC year and month of `archived_at` as
     `.taskpilot/archived/YYYY-MM/<item-id>.yaml` and
     `.taskpilot/archived/YYYY-MM/metadata.json`. The root archive directory retains only
     operational lock/recovery files and legacy data pending migration.

F12. `taskpilot archive migrate-storage` and
     `POST /api/projects/{project_id}/archive/migrate-storage` explicitly migrate legacy
     root-level archived YAML and metadata into their archive-month directories. The operation
    is idempotent, preserves YAML bytes and archive timestamps, and reports moved IDs.

F13. Relationship validation and resolution treat active items and archived items in the same
     project as one graph. An item may reference an archived parent or link target, and archived
     items retain visible active or archived children and derived reverse links. Unknown IDs remain
     validation errors.

### Quality

Q1. Archive operations are idempotent: running archive on an already-archived item is a
    no-op.

Q2. Archive operations preserve `created_at` and do not modify `updated_at` of the source
    item (the file is moved, not rewritten).

Q3. Archive operations are atomic at the file level: temp-file + `os.replace` pattern,
    matching the existing write strategy in `core/item_io.py`.

Q4. The system validates that the target `archived/` directory exists before writing; it
    creates the directory if missing.

Q5. Invalid (unparseable) items are never archived; they remain in `items/` and are
    surfaced by the validation panel.

Q6. An archived item ID remains reserved while its archived file exists. Unarchiving
    fails without changing either file or metadata when an active
    `items/<item-id>.yaml` file already exists.

Q7. Archive and unarchive operations are serialized per workspace by an advisory
    `.archived.lock`. Each operation writes a durable `.transaction.json` intent before
    relocating a YAML file and removes it only after the matching metadata publication.
    A later archive-service operation recovers an interrupted intent deterministically.

Q8. Scheduler startup is idempotent per workspace. Server shutdown cancels every started
    workspace scheduler, and a failure in one workspace loop does not stop checks for others.

Q9. Cross-storage relationship reads are deterministic and do not rewrite YAML, metadata, or
    reverse-link data. Active Board and List listings remain active-only; the Archived list remains
    archive-only.

## Design

### Domain and invariants

- `archive_threshold_days` is a project-level setting, not per-item. It defaults to 14
  when absent from `project.yaml`.
- Only items with status `done`, `cancelled`, or `deleted` are eligible. Items in
  `backlog`, `ready`, or `in_progress` are never archived, regardless of age.
- An item is eligible when `(current_time - updated_at) >= archive_threshold_days * 86400`.
- Archived items retain their original status. The Archived list shows that status without
  creating Kanban columns.
- Unarchive restores the item to `.taskpilot/items/` with its original status. The
  `metadata.json` entry is removed.

### Canonical file effects

Current layout:
```
.taskpilot/
  project.yaml
  items/
    TP-1.yaml
  comments/
    TP-1/
      2026-06-23T10-00-00Z.md
```

New layout (after archive feature):
```
.taskpilot/
  project.yaml
  items/
    TP-1.yaml
  comments/
    TP-1/
      2026-06-23T10-00-00Z.md
  archived/
    .archived.lock
    .transaction.json  # present only while an operation is incomplete
    2026-08/
      metadata.json
      TP-1.yaml
```

- `.taskpilot/archived/YYYY-MM/` holds one YAML file per item archived in that UTC calendar
  month, using the same filename convention as `items/`. A month name must be exactly
  `YYYY-MM`; it is derived from the canonical `archived_at` timestamp and is never inferred
  from a file modification time.
- Each month-local `metadata.json` is a JSON object mapping that month's item IDs to archive
  metadata:
  ```json
  {
    "TP-1": {
      "original_id": "TP-1",
      "project_key": "VP",
      "archived_at": "2026-08-05T12:00:00Z",
      "original_status": "done"
    }
  }
  ```
- Month-local `metadata.json` documents are the source of truth for archived IDs. The service
  aggregates them in deterministic item-ID order for listings and ID reservation. A legacy
  root-level `metadata.json` and YAML files are read compatibly until the explicit storage
  migration succeeds; new archives are never written at the root.
- `.archived.lock` is a persistent advisory lock file, not task data. It coordinates every
  archive-service operation within one workspace on Unix and Windows.
- `.transaction.json` is a transient, atomically-written recovery journal. It records the
  operation, source/destination item ID, and intended metadata before the YAML relocation.
  On the next archive-service operation, the service finishes the recorded relocation and
  metadata publication, then removes the journal. If neither expected file exists, it leaves
  the journal in place and reports the unrecoverable state rather than silently dropping data.
- Moving an item to `archived/` does NOT modify the source file in `items/`. The source
  file is deleted (not moved) and written to `archived/`. This avoids `updated_at` changes
  on the source.

### Service operations

New service module: `services/archive_service.py`

Exported functions:

- `get_archive_threshold(paths: WorkspacePaths) -> int`: Read `archive_threshold_days` from
  `project.yaml`, defaulting to 14.

- `set_archive_threshold(paths: WorkspacePaths, threshold: int) -> int`: Validate (1-3650),
  write to `project.yaml`, return the new threshold.

- `scan_eligible_items(paths: WorkspacePaths, now: str | None = None) -> list[Item]`: Return
  all items with status `done`, `cancelled`, or `deleted` whose `updated_at` exceeds the
  threshold. Excludes already-archived items (those listed in `metadata.json`).

- `archive_items(paths: WorkspacePaths, item_ids: list[str], now: str | None = None) -> list[str]`:
  Move the specified items to the month directory selected from `now`, update that month's
  `metadata.json`, return the list of archived item IDs. Idempotent: already-archived items
  are skipped.

- `migrate_all_eligible(paths: WorkspacePaths, now: str | None = None) -> list[str]`: Scan
  all eligible items (including those still in `items/`) and archive them. Returns the list
  of archived item IDs.

- `unarchive_item(paths: WorkspacePaths, item_id: str, now: str | None = None) -> Item`:
  Move an archived item from its archive-month (or compatible legacy root location) back to
  `.taskpilot/items/`, update the matching metadata document, and return the restored item.
  Raise `ConflictError` without changing either canonical item or metadata when
  `items/<item-id>.yaml` already exists.

- `migrate_legacy_archives(paths: WorkspacePaths) -> list[str]`: Move legacy root-level
  archived YAML and metadata into the archive-month derived from each entry's `archived_at`.
  Return moved IDs in deterministic order. Repeating a completed or partially completed
  migration is safe and does not rewrite item content or timestamps.

- `list_archived_items(paths: WorkspacePaths) -> list[Item]`: Read `metadata.json`, load
  each archived item file, return the list.

- `is_archived(paths: WorkspacePaths, item_id: str) -> bool`: Check `metadata.json` for
  the item ID.

- Relationship lookups used by validation, hierarchy checks, link checks, REST detail, and reverse
  derivation resolve an item ID across active and archived canonical files. They retain deterministic
  numeric-ID ordering and do not persist derived relationships.

Existing services touched:

- `project_service.py`: Add `archive_threshold_days` to `ProjectMeta` model and
  `read_project`/`create_project` handling.

- `item_service.py`: `list_items` excludes archived items (those in `metadata.json`).
  A new parameter `include_archived: bool = False` allows including them.

### CLI / API contracts

New CLI command group: `taskpilot archive`

Subcommands:

- `taskpilot archive run` — Trigger archive check on eligible items. JSON output: list of
  archived item IDs.

- `taskpilot archive migrate` — One-time migration of all eligible items. JSON output:
  summary object with `archived_count`, `archived_ids` list.

- `taskpilot archive migrate-storage` — Migrate legacy root-level archive storage into
  month partitions. JSON output: `{ "migrated_count": N, "migrated_ids": [...] }`.

- `taskpilot archive unarchive <item-id>` — Unarchive a single item. JSON output: restored
  item model. If the active item ID is occupied, it exits non-zero and reports the conflict;
  it does not overwrite either item.

- `taskpilot project archive-threshold [--threshold N]` — Get or set the archive threshold.
  Without `--threshold`, prints current value. With `--threshold`, sets it (validates
  1-3650).

New API endpoints:

- `POST /api/projects/{project_id}/archive/run` — Trigger archive. Response: `{ "archived": [item_id, ...] }`.

- `POST /api/projects/{project_id}/archive/migrate` — One-time migration. Response: `{ "archived_count": N, "archived_ids": [...] }`.

- `POST /api/projects/{project_id}/archive/migrate-storage` — Migrate legacy root-level
  archive storage. Response: `{ "migrated_count": N, "migrated_ids": [...] }`.

- `POST /api/projects/{project_id}/items/{item_id}/unarchive` — Unarchive an item. Response: `ItemDetail`.
  If the active item ID is occupied, returns `409` with the standard error `detail`; neither
  canonical item nor archive metadata is changed.

- `GET /api/projects/{project_id}/settings` — Get project settings including `archive_threshold_days`. Response: `{ "archive_threshold_days": 14 }`.

- `PATCH /api/projects/{project_id}/settings` — Update project settings. Request: `{ "archive_threshold_days": 30 }`. Response: updated settings.

- `GET /api/projects/{project_id}/items/{item_id}` — Returns item detail for an active item
  or an archived item belonging to the project. Archived item detail is read-only in the WebUI;
  mutation endpoints continue to target active items only.

### UI states

- New "Archived" tab in `ProjectWorkspace`, always visible alongside Board and List. No
  visibility toggle or persisted visibility state exists.

- The Archived tab renders a plain, non-columnar list showing only archived items. Its default
  order is epic, feature, task, bug, then numeric item ID within each type. The list is not a
  Kanban board and has no status columns.

- Archived items in the Archived board show the same status indicator, type, priority,
  and title as active items.

- Selecting an archived row opens the existing item-detail modal. The modal displays the
  archived item detail without an API 404 and does not expose edit or delete actions; unarchive
  remains available from the Archived list.

- Item detail relationship rows resolve parent, children, forward links, and derived reverse links
  across active and archived storage. The Tree view uses that same combined graph when it is shown;
  Board and List retain their active-only listing behavior.

- An "Unarchive" button/link on each archived item in the Archived board, opening a
  confirmation dialog before restoring the item.

## Acceptance Criteria

AC1. `project.yaml` without `archive_threshold_days` defaults to 14. Setting it to any
    integer 1-3650 persists correctly and is reflected in CLI/API output.

AC2. `taskpilot archive run` archives all eligible items (status done/cancelled/deleted,
    age > threshold) and prints their IDs in JSON mode.

AC3. `taskpilot archive migrate` archives all existing eligible items in one pass and
    prints a summary with `archived_count` and `archived_ids`.

AC4. `taskpilot archive unarchive <item-id>` moves the item from `.taskpilot/archived/`
    back to `.taskpilot/items/` and restores its original status.

AC5. `POST /api/projects/{project_id}/archive/run` returns `{ "archived": [...] }` with
    the same logic as the CLI command.

AC6. `POST /api/projects/{project_id}/items/{item_id}/unarchive` returns the restored
    `ItemDetail`.

AC7. The WebUI always shows an "Archived" tab, with no show/hide control. It renders only
    archived items in a plain non-columnar list ordered epic, feature, task, bug, then numeric
    item ID within each type.

AC8. Default Board and List views exclude archived items.

AC9. Archive operations are idempotent: running archive on an already-archived item is a
    no-op that does not modify files.

AC10. Archive operations do not modify the source item's `updated_at` (the file is moved,
      not rewritten).

AC11. Invalid (unparseable) items are never archived.

AC12. The `metadata.json` file is created on first archive, updated on each archive/unarchive,
      and removed when the last item is unarchived.

AC13. Archive threshold CLI command `taskpilot project archive-threshold` prints the current
      value without arguments and sets it with `--threshold N`.

AC14. Creating an item after an archive allocates an ID greater than every active and archived
      ID with the project key. An unarchive whose destination ID is already active fails with
      a CLI non-zero error and API `409`; the active YAML, archived YAML, and metadata are
      unchanged.

AC15. Overlapping archive/unarchive operations for one workspace serialize through
      `.archived.lock` and leave one valid metadata document. If metadata publication fails or
      the process stops after a relocation, `.transaction.json` retains the intended operation;
      the next archive-service operation completes it without rewriting item content or losing
      the archive timestamp.

AC16. With multiple active registry entries, server startup starts one periodic archive loop per
      distinct workspace and skips inactive entries. Repeated starts do not duplicate a loop;
      shutdown cancels all loops.

AC17. An archive created at `2026-08-05T12:00:00Z` is stored as
      `archived/2026-08/<item-id>.yaml` with its metadata in
      `archived/2026-08/metadata.json`. Listings, ID reservation, and unarchive aggregate all
      month directories in deterministic ID order.

AC18. Legacy root-level archive data remains listable and unarchivable. `archive migrate-storage`
      and its API endpoint move it into the timestamp-selected month without rewriting YAML
      bytes; repeated calls return an empty deterministic summary and do not alter canonical
      data. Root lock and transaction files are never moved.

AC19. Selecting an archived item opens its detail modal successfully. `GET
      /api/projects/{project_id}/items/{item_id}` returns its detail when the item is archived
      in that project, while PATCH and delete remain unavailable from the archived detail view.

AC20. Archiving a referenced item does not create `missing_reference` validation findings. Active
      and archived item detail views show their parents, children, forward links, and derived reverse
      links across storage; Tree shows the same hierarchy. A truly unknown project-local ID still
      reports `missing_reference`, and Board, List, and Archived list membership remain unchanged.

## Test Strategy

Test levels (per `.claude/skills/test-change/references/test-strategy.md`):

- **Unit tests** (`pytest`): Archive service functions — `scan_eligible_items`,
  `archive_items`, `migrate_all_eligible`, `unarchive_item`, `list_archived_items`,
  `is_archived`, `get_archive_threshold`, `set_archive_threshold`. Boundary conditions:
  threshold 0 (rejected), threshold 3651 (rejected), threshold 1 (accepted), items at
  exactly the threshold boundary, items with `updated_at` in the future.
  Archive transaction tests cover metadata-write failure, recovery before and after relocation,
  and concurrent operations against one workspace.
  Month-shard tests cover boundary months, deterministic aggregation, legacy discovery,
  byte-preserving/idempotent storage migration, and recovery with a monthly destination.

- **Contract tests** (pytest): CLI commands `archive run`, `archive migrate`,
  `archive migrate-storage`,
  `archive unarchive`, `project archive-threshold` — JSON output shape, exit codes,
  error messages for invalid item IDs, non-existent projects, and restore collisions.

- **API contract tests** (pytest): All new endpoints — request/response shapes, error
  codes (404 for unknown project/item, 400 for invalid threshold, 409 for restore collision),
  idempotency, and archived item detail reads through the existing item-detail route.

- **Service and validation tests** (pytest): archived parent/link targets are valid for read and
  write-time relationship checks; reverse links and children aggregate both stores; unknown IDs
  remain rejected; no archive operation rewrites relationship fields.

- **Component tests** (Vitest): Always-visible Archived navigation, non-columnar type-first
  archive list rendering/order, archived-detail selection, and unarchive button behavior.

- **Functional E2E tests** (Playwright): Archive flow — create items, wait/set threshold,
  run archive, verify the always-visible Archived list and an archived item detail modal,
  unarchive, verify items return to active views.

- **Component and functional E2E tests**: relationship detail and Tree retain active/archived
  parent-child and link connections while Board/List and Archived list filters remain separate.

- **Browser-contract tests**: Archived list has no Kanban columns, stays token-aligned with
  workspace lists, and renders status indicators correctly.

## Implementation Slices

Slice 1 — **Project setting**: Add `archive_threshold_days` to `ProjectMeta`, CLI get/set,
  API get/PATCH. (Observable: CLI prints/sets threshold, API returns it.)

Slice 2 — **Archive service core**: `scan_eligible_items`, `archive_items`,
  `metadata.json` read/write. (Observable: CLI `archive run` archives items, files appear
  in `.taskpilot/archived/`.)

Slice 3 — **Migration + unarchive**: `migrate_all_eligible`, `unarchive_item`, CLI
  `archive migrate` and `archive unarchive`, API endpoints. (Observable: CLI archives
  all existing items in one pass; unarchive restores an item.)

Slice 4 — **Archived board UI**: Always-visible Archived tab, non-columnar type-first list,
  archived read-only detail, and unarchive confirmation. (Observable: WebUI lists archived
  items without columns, opens detail, and restores an item.)

Slice 5 — **Periodic scheduler + integration**: Background task integration, exclude
  archived items from default listings, integration tests. (Observable: Items auto-archived
  after threshold period in long-running server mode.)

## Risks and Compatibility

R1. **Canonical layout change**: Adding `.taskpilot/archived/` changes the on-disk layout.
    Existing workspaces will not have this directory; it is created on first archive.
    Migration of existing items is opt-in via `archive migrate`.

R2. **`metadata.json` as single source of truth**: If `metadata.json` is corrupted or
    deleted, the system may re-archive items that are already archived. Mitigation:
    `scan_eligible_items` checks both `metadata.json` and file existence in `archived/`.

R3. **Concurrent archive operations**: Two archive runs overlapping could attempt to
    archive the same item or publish stale metadata. Mitigation: cross-platform advisory
    locking (`.archived.lock`), a durable transaction journal, and idempotent recovery.

R4. **Periodic scheduler in CLI mode**: The CLI foreground mode does not have a built-in
    scheduler. The ~3-hour periodic check is only relevant for long-running server mode.
    CLI users must use `taskpilot archive run` manually.

R5. **Large workspaces**: Scanning all items for archive eligibility could be slow in
    workspaces with thousands of items. Mitigation: scan is synchronous but fast (file
    glob + timestamp comparison); deferred optimization (index) is out of scope.

R6. **Comment files for archived items**: When an item is archived, its comment files
    remain in `comments/<item_id>/`. They are not moved. This is acceptable because
    comments are append-only and the item ID remains the same. A future enhancement
    could move comment files alongside the item.

R7. **ID collision after archive**: Active-only ID allocation can reuse an archived ID and
    cause a later restore to overwrite canonical data. Mitigation: allocate above the maximum
    active or archived numeric ID and reject an occupied unarchive destination before any write.

R8. **Storage migration interruption**: A root-to-month move can be interrupted after either
    file relocation or metadata publication. Mitigation: archive operations continue to discover
    both roots, migration validates entry timestamps and merges only identical entries; a retry
    completes a partial move without rewriting YAML bytes.

## Assumptions

A1. The default archive threshold is 14 days, as stated in the epic.

A2. "Roughly every 3 hours" means the scheduler fires at ~3-hour intervals; exact timing
    is not guaranteed (no cron precision required).

A3. Every month-local `metadata.json` is canonical archive metadata for that month. It is
    atomically published and must not be discarded; canonical YAML remains the recovery
    evidence when metadata publication is interrupted.

A4. Archived items are never permanently deleted; they can always be unarchived.

A5. The periodic scheduler is only active in server mode (long-running `taskpilot serve`).
    CLI commands are always manual/on-demand.

## Open Questions

O1. Should the archive threshold be configurable per-project (beyond the single
    `project.yaml` field) when multiple projects are registered? Current design stores
    it in each project's `project.yaml`, so per-project configuration is implicit.

O2. Should archived items' comment files be moved to `.taskpilot/archived/comments/`
    alongside the item, or remain in `comments/`? Current design keeps them in place
    (assumption A5 above).

O4. Should there be a soft-deletion safeguard for archived items (e.g., preventing
    archive of items that have active blockers or children)? Not in scope for v1.

O5. Should the archive threshold default be configurable at the system level (not per
    project)? Not in scope; 14 days is the default.
