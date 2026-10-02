# Header Project Actions: Theme Toggle, Unregister, Doctor

Status: implemented

Backlog: TP-102 (theme persistence), TP-138 (unregister), TP-139 (doctor).

## Outcome

From the WebUI header a user can:

1. pick `auto`, `light`, or `dark` theme with a three-icon toggle, and have the choice survive a
   reload (TP-102);
2. unregister the selected project from this machine after a confirmation dialog, without touching
   the project's `.taskpilot/` files (TP-138);
3. open a Doctor dialog that previews deterministic, safe repairs for the selected project's
   validation findings and applies them on confirmation, while listing the findings it cannot fix
   (TP-139).

Unregister and Doctor are domain capabilities shared by CLI, REST, and WebUI.

## Context

- `ThemeSwitcher` is a two-option dropdown (`light`/`dark`) that sets `data-theme` on `<html>` but
  does not persist anything; on reload the OS preference wins. Spec `0003` excluded a theme-toggle
  control; this spec amends that exclusion.
- The machine registry (`services/registry.py`) supports only `register_project` and
  `list_projects`. Nothing removes an entry.
- `core/validation.py` reports findings but nothing repairs them. The npm wrapper's
  `taskpilot doctor --rebuild-runtime` repairs the managed runtime, not the workspace, and is
  unaffected by this spec.

## Scope

In scope: the theme toggle and its `localStorage` persistence; `registry.unregister_project`;
`services/doctor_service.py`; `taskpilot project unregister`; `taskpilot validate --fix`;
`DELETE /api/projects/{id}`; `GET /api/projects/{id}/doctor`;
`POST /api/projects/{id}/doctor/apply`; the header Doctor and Unregister icon buttons and their
dialogs.

Out of scope: deleting project files; deactivating (`active=false`) entries; repairing
`invalid_yaml`, `unreadable_file`, `duplicate_id`, attachment, or comment findings; editing raw
files from the UI; server-side theme persistence; the npm wrapper's `doctor` command.

## Requirements

### R1 Theme toggle and persistence (TP-102)

- R1.1 The header shows a radio group labelled "Theme" with three icon-only options in order
  `auto` (monitor icon), `light` (sun icon), `dark` (moon icon). Each option has an accessible name
  ("Auto theme", "Light theme", "Dark theme") and exactly one is checked.
- R1.2 Selecting `light` or `dark` sets `data-theme` on `<html>` to that value. Selecting `auto`
  removes the attribute so `prefers-color-scheme` applies, including live OS changes.
- R1.3 The selection is stored in `localStorage` under `taskpilot.theme` as `auto`, `light`, or
  `dark`.
- R1.4 On load the stored value is applied before the first paint by an inline script in
  `web/index.html`; a missing, unknown, or unreadable value resolves to `auto`. Storage access
  failures never break rendering.

### R2 Unregister project (TP-138)

- R2.1 `registry.unregister_project(registry_dir, project_id)` removes the entry with that `id`
  under the registry lock, writes the registry atomically, and returns the removed entry. An unknown
  id raises `NotFound`. Project files are never read, written, or deleted.
- R2.2 When `ui-state.yaml` `last_opened_project_id` equals the removed id it is reset to `null`.
  Owned by `project_service.unregister_project`, which every adapter calls.
- R2.3 CLI: `taskpilot project unregister <id>` prints `Unregistered <id>` (exit `0`); `--json`
  prints the removed entry; unknown id exits `1`.
- R2.4 REST: `DELETE /api/projects/{id}` returns `200` with the removed `ProjectSummary`; unknown
  id returns `404`.
- R2.5 WebUI: a trash icon button "Unregister project" sits left of the theme toggle while a
  project is selected. It opens an alert dialog naming the project and stating that files on disk
  are kept. Confirm calls the API, refreshes the project list, and selects the first remaining
  project, or the empty state when none remain. A failure shows an inline error and keeps the
  dialog open. Cancel changes nothing.

### R3 Doctor (TP-139)

- R3.1 `doctor_service.plan_fixes(paths) -> DoctorPlan` is read-only. It returns `fixes` (safe
  repairs) and `manual` (findings with no safe repair), each sorted deterministically.
- R3.2 Safe fix kinds:
  - `remove_link` — an active item (`items/`) whose `links.blocks` or `links.relates_to` entry
    produces `missing_reference` or `link_to_deleted`; the entry is removed.
  - `clear_parent` — an active item whose `parent_id` produces `missing_reference`; `parent_id` is
    cleared.
  - `migrate_archive_storage` — legacy root-level archive metadata exists; runs
    `archive_service.migrate_legacy_archives`.
- R3.3 Every other finding — including references from archived items and `parent_id` pointing at
  a deleted item — appears in `manual` unchanged. Safety rules for reference fixes:
  - a fix is offered only for a validator finding with the same path, field, and message, so the
    fix set is always a subset of what validation reports;
  - an id is known when any item file carries it by filename stem or recoverable `id`, so a
    schema-invalid or unparseable (e.g. merge-conflicted) file never causes references to it to
    be removed;
  - files with `id_filename_mismatch` or `duplicate_id` findings are never repaired;
  - each item's combined repair is dry-run through the item service while planning; an item whose
    repaired form would still be rejected (e.g. a hierarchy violation) keeps its findings in
    `manual`.
- R3.4 `doctor_service.apply_fixes(paths) -> DoctorResult` recomputes the plan from current disk
  state (it never trusts a client-provided plan), applies every fix through existing domain
  services (canonical files written first, one write per item), and returns `applied`, `failed`
  (each `{fix, error}` for a fix a service rejected at apply time, e.g. a conflicting legacy
  archive), and a fresh validation report. A failure never stops the remaining fixes. Running it
  twice in a row applies nothing the second time. A legacy-archive migration that fails part-way
  keeps entries migrated before the conflicting one, as `migrate_legacy_archives` does.
- R3.5 CLI: `taskpilot validate` output and exit codes are unchanged, except that human mode adds a
  final stderr hint `N issue(s) can be fixed automatically: run taskpilot validate --fix` when the
  plan has fixes. `taskpilot validate --fix` applies the plan, prints one line per applied fix to
  stdout and one `Could not apply: <description>: <error>` line per failed fix to stderr, then
  reports validation of the repaired workspace; exit code follows that report.
  `--fix --json` prints `{"applied": [...], "failed": [...], "report": {...}}`.
- R3.6 REST: `GET /api/projects/{id}/doctor` returns the plan; `POST /api/projects/{id}/doctor/apply`
  returns `200` with `{applied, failed, report}`; per-fix service errors are reported in `failed`,
  never as an error status. Unknown project returns `404`.
- R3.7 WebUI: a stethoscope icon button "Doctor" sits left of the unregister button while a project
  is selected. It opens a dialog listing the safe fixes and the manual findings (with path and
  message). "Apply N fixes" ("Apply 1 fix" when N is 1) is disabled when N is 0. Applying shows the
  applied count ("Applied N fixes." / "Applied 1 fix.") and, when any fix failed, an alert
  "Could not apply N fixes:" listing each description with its reason; then it refreshes items,
  validation status, and the plan. A request failure shows "Failed to apply fixes: <detail>". Manual findings show their item id when
  known, so the user can open the item from the board.

### Quality

- Adapters translate only; registry and repair rules live in `services/`.
- Plans, applied lists, and JSON are deterministically ordered by `(path, field, target, kind)`.
- No new production dependency (icons come from `lucide-react`, already a dependency).

## Data Shapes

```json
// DoctorFix
{"kind": "remove_link", "item_id": "TP-5", "path": ".taskpilot/items/TP-5.yaml",
 "field": "links.blocks", "target": "TP-9", "description": "Remove links.blocks -> TP-9 from TP-5"}
// DoctorPlan
{"fixes": [DoctorFix], "manual": [Finding]}
// DoctorFailure
{"fix": DoctorFix, "error": "Cannot migrate 'TP-1': legacy and month files conflict"}
// DoctorResult
{"applied": [DoctorFix], "failed": [DoctorFailure], "report": ValidationReport}
```

`migrate_archive_storage` fixes use `item_id: null`, `field: null`, `target: null`,
`path: ".taskpilot/archived/metadata.json"`.

## Acceptance Criteria

- AC1 Given no stored theme, when the app loads, then `auto` is checked and `<html>` has no
  `data-theme`.
- AC2 Given the user selects `dark`, when the page reloads, then `dark` is checked and
  `data-theme="dark"` is present before React mounts.
- AC3 Given `taskpilot.theme` holds `"purple"`, when the app loads, then `auto` applies.
- AC4 Given two registered projects, when one is unregistered through the service, then the
  registry lists only the other and the removed project's `.taskpilot/` tree is byte-identical.
- AC5 Given `last_opened_project_id` is the removed id, then it becomes `null`; otherwise it is
  unchanged.
- AC6 Given an unknown id, then the service raises `NotFound`, the CLI exits `1`, and REST
  returns `404`.
- AC7 Given the user confirms the unregister dialog, then the project disappears from the selector
  and another project (or the empty state) is shown; cancel leaves everything unchanged.
- AC8 Given an active item linking to a missing id and to a deleted item, and one with a missing
  parent, when the plan is computed, then it holds exactly two `remove_link` and one
  `clear_parent` fixes in deterministic order and no file changed.
- AC9 Given that plan, when `apply_fixes` runs, then the links and parent are removed, `updated_at`
  is refreshed, the returned report has no `missing_reference`/`link_to_deleted` findings for those
  items, and a second run applies nothing.
- AC10 Given an `invalid_yaml` file or an archived item with a dangling link, then it appears in
  `manual` and its file is untouched by apply.
- AC11 Given legacy root archive metadata, then the plan contains `migrate_archive_storage` and
  apply moves it into month storage; a conflicting legacy archive is reported in `failed`, its
  files are unchanged, and other fixes still apply.
- AC14 Given a schema-invalid or unparseable item file, then no fix removes references to its id.
- AC15 Given an item whose repair would still violate the hierarchy, or a file with an id/filename
  mismatch, then its findings stay in `manual` and fixes for other items still apply.
- AC12 Given fixable findings, `taskpilot validate` prints the hint and keeps its exit code;
  `taskpilot validate --fix` applies and exits `0` when the repaired workspace has no errors.
- AC13 Given the Doctor dialog with fixes, when the user clicks "Apply", then the applied count is
  shown and the header validation status refreshes; with no fixes the button is disabled.

## Test Strategy

| Behavior | Level |
| --- | --- |
| registry unregister, ui-state reset, doctor plan/apply | Python unit/service |
| CLI `project unregister`, `validate --fix`, hint | CLI (Typer runner) |
| REST routes and error codes | API (TestClient) |
| ThemeSwitcher, UnregisterProjectDialog, DoctorDialog | Vitest component |
| inline theme bootstrap before mount | Vitest on `index.html` script logic + E2E reload |
| header unregister and doctor journeys, theme persistence across reload | Playwright functional E2E |

## Slices

1. Theme toggle + persistence (web only).
2. Unregister: service, CLI, REST, WebUI dialog.
3. Doctor: service, CLI flag, REST, WebUI dialog.

## Risks

- Repairs write canonical files: limited to deterministic removals through `item_service`, which
  validates before writing; archived files are never rewritten.
- Unregister while another tab views the project: that tab's next request gets `404` and shows its
  existing error state.
- A doctor apply racing a manual edit: the plan is recomputed at apply time; removal is idempotent.

## Assumptions

- Removing a link to a soft-deleted item is acceptable as a "safe" repair (decided in brainstorm,
  2026-10-02); clearing a parent that points at a deleted item is not.

## Acceptance Evidence

Implemented on branch `feature/TP-102-theme-unregister-doctor` (2026-10-02).

| Criteria | Evidence |
| --- | --- |
| AC1–AC3 | `web/src/components/__tests__/ThemeSwitcher.test.tsx`; `web/e2e/functional/tp-102-header-actions.spec.ts` (reload persistence) |
| AC4–AC6 | `tests/services/test_unregister_project.py`; `tests/cli/test_header_actions_cli.py`; `tests/server/test_header_actions_api.py` |
| AC7 | `web/src/components/__tests__/UnregisterProjectDialog.test.tsx`; `web/src/__tests__/App.test.tsx`; functional E2E unregister journey |
| AC8–AC11, AC14–AC15 | `tests/services/test_doctor_service.py`; `tests/server/test_header_actions_api.py` |
| AC12 | `tests/cli/test_header_actions_cli.py` |
| AC13 | `web/src/components/__tests__/DoctorDialog.test.tsx`; functional E2E doctor journey |
| Style/focus contract | `web/browser-contract/tp-102-header-actions.spec.ts` |

