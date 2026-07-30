# API and CLI Contract

This document owns the TaskPilot contract surface: CLI commands and options, exit codes, REST
endpoints, request/response models, and validation finding codes. `docs/architecture.md` owns
system structure, `docs/decisions/` owns the rationale for each choice, and `docs/specs/` owns
accepted product behavior.

Every enumerable list here is asserted against source by a drift test, so a divergence fails CI
rather than rotting silently. Do not add an entry without verifying it against the implementation.

## CLI

### Global options

`--json` is a global option and must precede the subcommand:

```bash
taskpilot --json item list      # correct
taskpilot item list --json      # error: No such option: --json
```

### Exit codes

| Code | Meaning |
| --- | --- |
| `0` | Success |
| `1` | User error — bad input, not found, or conflict; the caller can fix it |
| `2` | System error — an unexpected failure the caller cannot fix |

Exit codes are fixed so scripts and AI agents can branch on them reliably.

### Commands

| Command | Positional | Options |
| --- | --- | --- |
| `taskpilot init` | — | `--id`, `--key`, `--name` |
| `taskpilot validate` | — | — |
| `taskpilot serve` | — | `--host`, `--port`, `--workspace` |
| `taskpilot project list` | — | — |
| `taskpilot item list` | — | `--status`, `--type`, `--project`, `--include-deleted` |
| `taskpilot item show` | `<item-id>` | — |
| `taskpilot item create` | — | `--title`\*, `--type`\*, `--priority`, `--status`, `--description`, `--parent`, `--tag`, `--created-by` |
| `taskpilot item update` | `<item-id>` | `--title`, `--description`, `--priority`, `--status`, `--parent`, `--tag`, `--type` |
| `taskpilot item parent` | `<child-id> <parent-id>` | — |
| `taskpilot item unparent` | `<child-id>` | — |
| `taskpilot item blocks` | `<source-id> <target-id>` | — |
| `taskpilot item unblocks` | `<source-id> <target-id>` | — |
| `taskpilot item relates` | `<source-id> <target-id>` | — |
| `taskpilot item unrelates` | `<source-id> <target-id>` | — |
| `taskpilot item comment` | `<item-id> <text>` | `--author` |

\* required.

Notes:

- `item create` prints the new item id. `item comment` prints the new comment filename.
- `item update` changes only the options passed; `updated_at` refreshes automatically. An update
  whose values all match the current ones short-circuits without a write.
- `--tag` is repeatable and replaces the whole tag list on `item update`.
- Link operations use explicit verb pairs rather than a generic `link`/`unlink`. All are idempotent.
- There is no `item delete` command. Soft deletion is reachable by setting `--status deleted`.
- `taskpilot doctor --rebuild-runtime` is provided by the npm wrapper, not the Python CLI; it
  repairs the managed runtime rather than the workspace.

### Invalid-file handling differs by adapter

This divergence is deliberate. Treat it as contract, not as a defect:

| Surface | Behavior on an unparseable item file |
| --- | --- |
| `taskpilot item list` | Skips the file silently; no invalid marker |
| `taskpilot item show` | Fails with a validation error (exit `1`) |
| `taskpilot validate` | Reports the file with findings — the CLI diagnosis path |
| REST / WebUI | Surfaces the item as a stub carrying its findings |

## REST API

All routes are mounted under the `/api` prefix.

| Method | Path | Response model |
| --- | --- | --- |
| `GET` | `/api/health` | — |
| `GET` | `/api/projects` | `list[ProjectSummary]` |
| `GET` | `/api/projects/{project_id}/items` | `list[ItemSummary]` |
| `GET` | `/api/projects/{project_id}/items/{item_id}` | `ItemDetail` |
| `PATCH` | `/api/projects/{project_id}/items/{item_id}` | `ItemDetail` |
| `GET` | `/api/projects/{project_id}/validate` | `ValidationReportOut` |
| `GET` | `/api/ui-state` | `UIStateOut` |
| `PATCH` | `/api/ui-state` | `UIStateOut` |

Behavior notes:

- Item routes verify the item belongs to the requested project and return `404` otherwise, so an ID
  valid in one project cannot be read through another.
- FastAPI docs are served at `/docs`.
- When built WebUI assets are missing, the server serves a packaging-error page with `503` and keeps
  the API available rather than failing at startup.
- `ui-state` is per-machine WebUI state stored outside any repository; it is never canonical task
  data.

### Models

| Model | Fields |
| --- | --- |
| `ProjectSummary` | `id`, `key`, `name`, `active` |
| `CommentOut` | `schema_version`, `created_at`, `created_by`, `body` |
| `ValidationFindingOut` | `severity`, `code`, `path`, `field`, `item_id`, `message` |
| `ValidationSummaryOut` | `errors`, `warnings` |
| `ValidationReportOut` | `ok`, `summary`, `findings` |
| `ItemCoreSummary` | `id`, `title`, `type`, `status`, `priority`, `valid` — base for the two summary shapes below |
| `ItemSummary` | `ItemCoreSummary` + `created_at`, `updated_at`, `parent_id`, `findings` |
| `ItemRelationshipSummary` | `ItemCoreSummary` with no additional fields |
| `ItemRelationships` | `parent`, `children`, `blocks`, `blocked_by`, `relates_to`, `related_to` |
| `ItemDetail` | the domain `Item` + `comments`, `relationships`, `valid`, `findings` |
| `ItemUpdateInput` | `title`, `description`, `priority`, `status` — all optional |
| `UIStateOut` | `last_opened_project_id` |
| `UIStatePatch` | `last_opened_project_id` |

`ItemUpdateInput` is the full PATCH surface: `tags`, `parent_id`, and `type` are **not** writable
over REST, though the CLI can change all three.

## Validation finding codes

17 codes are defined in the domain validator. `parse_error` is emitted only by the REST adapter for
an item stub it could not parse, and has no domain-layer counterpart.

| Code | Concern |
| --- | --- |
| `missing_required_field` | A required item field is absent |
| `invalid_field` | A field value fails its type or constraint |
| `invalid_enum` | A value is outside the allowed set for `type`, `status`, or `priority` |
| `invalid_yaml` | The file is not parseable YAML |
| `unreadable_file` | The file cannot be read from disk |
| `id_filename_mismatch` | The `id` field disagrees with the filename |
| `duplicate_id` | Two files claim the same item id |
| `missing_reference` | A link or `parent_id` names an item that does not exist |
| `link_to_deleted` | A link points at a soft-deleted item |
| `attachment_empty` | An attachment path is empty |
| `attachment_not_relative` | An attachment path is not relative |
| `attachment_outside_repo` | An attachment path escapes the repository root |
| `missing_attachment` | A referenced attachment file is absent |
| `invalid_comment` | A comment file fails validation |
| `comment_unreadable` | A comment file cannot be read |
| `comment_filename_not_timestamp` | A comment filename is not a canonical timestamp stem |
| `comment_timestamp_mismatch` | A comment filename stem disagrees with its `created_at` |
| `parse_error` | REST adapter only — the item file could not be parsed into a stub |

Invalid files stay visible and actionable rather than disappearing from listings.
