# 0002: Alpha Product and Stack Decisions

## Status

accepted

This specification is production-ready as the accepted Alpha product and stack contract. Feature
requirements, ADRs, and implementation work must align with it unless a newer accepted
specification explicitly revises a decision.

## Outcome

This specification captures the current working decisions for TaskPilot Alpha and the planned
Beta/Release direction. It records product structure, canonical storage, item/comment behavior,
WebUI expectations, and the initial technology stack.

Once accepted, this specification supersedes conflicting provisional examples in
`docs/taskpilot_concept.md`.

## Release Levels

TaskPilot uses product release levels instead of `v0.1` language:

- Alpha: MVP used to validate the concept.
- Beta: product-ready and releasable.
- Release: all or almost all initial features are implemented.

## Repository and Registry Model

Each project repository owns its canonical TaskPilot files.

```text
repo-root/
  .taskpilot/
    project.yaml
    items/
      TP-1.yaml
    comments/
      TP-1/
        2026-06-23T10-00-00Z.md
```

One repository contains exactly one TaskPilot project.

TaskPilot also has a local system directory for machine-specific state:

```text
macOS: ~/Library/Application Support/TaskPilot/
Windows: %APPDATA%/TaskPilot/
```

The system directory stores local registry, active/inactive project flags, and local preferences.
It is not committed to project repositories and is not canonical product data.

The WebUI serves active registered projects from the local system registry. A registered project
can be disabled locally without changing the project repository.

Registry entries use unique project IDs. Alpha allows only one registered path per `project.id`.
The registry stores absolute normalized paths only and caches project `name` and `key` for display.

Example registry entry:

```yaml
schema_version: 1
projects:
  - id: task-pilot
    key: TP
    name: TaskPilot
    path: /Users/aleksei/Projects/task-pilot
    active: true
    registered_at: 2026-06-24T10:00:00Z
```

Registry paths are local-only and do not need to be portable across machines.

## Project Initialization

Alpha has no separate `register` command. `taskpilot init .` is the single onboarding command for
new and existing TaskPilot projects.

Expected commands:

```bash
taskpilot init .
taskpilot serve
```

`taskpilot init .` inspects only the current folder. It does not scan child or parent folders.

For a new project, `init` creates missing repository-local TaskPilot structure and project metadata,
then adds or enables the project in the local registry.

For an existing or partially existing TaskPilot project, `init` creates only missing required
folders/files, does not overwrite existing canonical files, adds or enables the project in the
local registry when project identity is available, validates the project, and prints findings.

If inconsistencies exist, `init` reports them and suggests manual correction or future Beta repair
tooling. Alpha does not silently repair inconsistent data.

If `project.yaml` exists, `init` must not overwrite immutable identity fields.

`taskpilot serve` serves all active registered projects by default.

## Project Metadata

Alpha `project.yaml` is minimal:

```yaml
schema_version: 1
id: task-pilot
key: TP
name: TaskPilot
created_at: 2026-06-24T10:00:00Z
```

Project metadata is set during `taskpilot init .` and is not editable through Alpha CLI or WebUI.

Fields:

- `schema_version`: required, system-owned;
- `id`: required, user-supplied on init, immutable after init;
- `key`: required, used as the item ID prefix, immutable in Alpha;
- `name`: required display name, immutable in Alpha;
- `created_at`: required, system-created.

## Canonical File Formats

Canonical item and project records use YAML.

TaskPilot owns canonical YAML formatting. When TaskPilot writes a YAML file, custom manual YAML
comments or unusual formatting may be normalized.

Comments use Markdown files with YAML frontmatter and Markdown body.

Product specs and documentation remain Markdown.

## Item Files

Items are stored as pure YAML files under `.taskpilot/items/`.

File names match item IDs:

```text
.taskpilot/items/TP-1.yaml
```

Item IDs are sequential per project:

```text
<PROJECT_KEY>-<NUMBER>
TP-1
TP-2
TP-10
```

The next item ID is allocated by scanning existing item files and choosing the next numeric suffix.
Gaps are allowed. Duplicate IDs are validation errors.

TaskPilot writes item YAML deterministically:

- fixed field order;
- absent optional fields omitted;
- UTC ISO 8601 timestamps with seconds, such as `2026-06-24T10:00:00Z`;
- comments and unusual manual YAML formatting may be normalized;
- unknown fields are preserved where practical when updating parseable item files.

Alpha item field order:

1. `schema_version`
2. `id`
3. `title`
4. `priority`
5. `type`
6. `status`
7. `created_at`
8. `updated_at`
9. `parent_id`
10. `tags`
11. `description`
12. `attachments`
13. `dor`
14. `dod`
15. `links`
16. `created_by`
17. `performed_by`
18. `external_refs`

Unknown fields, when preserved, are written after known fields in deterministic key order.

## Item Types and Hierarchy

Item types are fixed through Release:

- epic;
- feature;
- task;
- bug.

Hierarchy is typed and each item has at most one parent.

Allowed parent/child rules:

| Parent type | Allowed child types |
| --- | --- |
| epic | feature, task |
| feature | task |
| task | bug |
| bug | none |

Epics are always root items.

Hierarchy is stored through `parent_id`, not as a general graph link.

## Statuses

Alpha workflow statuses are fixed:

- backlog;
- ready;
- in_progress;
- done;
- cancelled.

The system status is:

- deleted.

`deleted` is stored as a regular status value in item YAML, but it is reserved system behavior. It
is hidden from the normal Kanban UI, cannot be changed by project status configuration, and cannot
be used as a normal workflow column.

Beta introduces project-configured workflow statuses with the Alpha list as the default.

`cancelled` remains visible in the Kanban board.

## Item Fields

Alpha shows all supported item fields in the UI, but not all fields are required.

Mandatory user-editable fields:

- `title`;
- `priority`;
- `type`;
- `status`.

Mandatory non-user-editable fields:

- `schema_version`;
- `id`;
- `created_at`;
- `updated_at`.

Optional user-editable fields:

- `tags`;
- `description`;
- `attachments`;
- `dor`;
- `dod`;
- `links`;
- `parent_id`;
- `created_by`;
- `performed_by`;
- `external_refs`.

`id` is generated and visible, but not normally user-editable because it is coupled to file names,
links, and comment paths.

`created_by` and `performed_by` are simple strings.

## Priority

Priority is required and defaults to `normal`.

Allowed values:

- low;
- normal;
- high.

## Optional Field Shapes

`tags` are optional strings and are available from Alpha onward.

`dor` and `dod` are optional lists of strings in Alpha:

```yaml
dor:
  - Parent item is clear.
  - Acceptance criteria are written.
dod:
  - Tests pass.
  - Documentation is updated.
```

`attachments` are optional lists of relative paths in Alpha and Beta:

```yaml
attachments:
  - docs/mockup.png
  - screenshots/kanban-flow.png
```

TaskPilot does not upload, copy, or manage attachment files through Beta. Validation should require
relative paths, reject paths that escape the repository root, prefer `/` separators, and treat
missing files as warnings rather than hard errors.

`external_refs` are optional lists of strings in Alpha:

```yaml
external_refs:
  - https://github.com/org/repo/issues/123
  - JIRA-456
```

## Links

Alpha supports these non-parent link types:

- `blocks`;
- `relates_to`.

Links are stored as a map of link type to item IDs:

```yaml
links:
  blocks:
    - TP-9
  relates_to:
    - TP-12
```

`blocks` is directional and can target any item type.

`relates_to` has symmetric meaning, but is stored only on the item where the user added it.

Reverse relationships are derived at read/query time. Adding or removing a link updates only the
source item file and does not update target item `updated_at`.

Alpha does not support `duplicates`.

## Comments

Comments are separate append-only Markdown files through Alpha.

Comment path:

```text
.taskpilot/comments/TP-1/2026-06-23T10-00-00Z.md
```

The folder name is the owning item ID, so comment frontmatter does not duplicate `item_id`.

Comment files use YAML frontmatter plus Markdown body:

```markdown
---
schema_version: 1
created_at: 2026-06-23T10:00:00Z
created_by: Aleksei
---

Investigated current parser behavior.
```

The filename timestamp is the comment identity within the item. Timestamps use UTC seconds.
`created_at` should match the filename timestamp. If two comments collide at the same second,
TaskPilot adds a numeric suffix to the filename:

```text
2026-06-23T10-00-00Z.md
2026-06-23T10-00-00Z-2.md
2026-06-23T10-00-00Z-3.md
```

Adding a comment does not update the parent item `updated_at`. `updated_at` means the item YAML
changed. A future `last_activity_at` value can be derived from item timestamps and comment
timestamps.

Comment edit/delete is deferred until Beta or later.

## Deletion

Alpha deletion sets item `status: deleted`.

Deleted item files remain in the repository. Deleted items are hidden from the normal WebUI, but
remain visible to validation and direct item lookup.

Beta may add permanent delete with safeguards for links and comments.

## Validation

Projects load even when invalid item or comment files exist.

Invalid files must remain visible and actionable. Valid items should still load normally.

Expected behavior:

- `taskpilot validate` reports all validation errors and exits non-zero when errors exist;
- valid items can still be listed and displayed;
- invalid item files are shown in item lists and on the Kanban board where possible;
- invalid comments are shown through validation output, not as Kanban cards;
- writes validate the target operation before changing files;
- writes do not silently rewrite unrelated invalid files.

Validation severities:

- errors make `taskpilot validate` exit non-zero;
- warnings do not make `taskpilot validate` exit non-zero;
- missing attachment files are warnings;
- attachment paths that are absolute or escape the repository root are errors;
- links to missing item IDs are errors;
- links to existing `status: deleted` items are warnings.

Invalid item handling:

- invalid items with recoverable non-deleted status appear in that Kanban column with a red `!`
  indicator;
- invalid items without recoverable status appear in the backlog column with a red `!` indicator;
- invalid items with recoverable `status: deleted` are hidden from the normal Kanban board like
  valid deleted items;
- invalid item cards are not draggable;
- clicking an invalid item card opens read-only validation details in Alpha.

`taskpilot item list` includes invalid item files with an invalid marker where possible. Deleted
items, including invalid items with recoverable `status: deleted`, are excluded by default unless
`--include-deleted` is used.

`taskpilot item show <item-id>` works for invalid items when the item ID is recoverable and shows
read-only validation details.

`taskpilot item update <item-id>` can update invalid item files only when YAML parses as a mapping
and `id` is recoverable. Completely unparseable YAML cannot be updated by Alpha item commands.

`taskpilot validate --json` returns a summary plus a flat findings list:

```json
{
  "ok": false,
  "summary": {
    "errors": 1,
    "warnings": 2
  },
  "findings": [
    {
      "severity": "error",
      "code": "missing_required_field",
      "path": ".taskpilot/items/TP-1.yaml",
      "field": "title",
      "item_id": "TP-1",
      "message": "Missing required field: title"
    }
  ]
}
```

`ok` means no errors. Warnings may still be present when `ok` is `true`.

## CLI Scope and Output

Alpha commands:

```bash
taskpilot init .
taskpilot validate
taskpilot serve
taskpilot project list

taskpilot item list
taskpilot item show <item-id>
taskpilot item create
taskpilot item update <item-id>
taskpilot item comment <item-id>
taskpilot item delete <item-id>

taskpilot item parent <item-id> <parent-id>
taskpilot item unparent <item-id>
taskpilot item blocks <item-id> <target-id>
taskpilot item unblocks <item-id> <target-id>
taskpilot item relates <item-id> <target-id>
taskpilot item unrelates <item-id> <target-id>
```

Alpha does not include generic `link` / `unlink` commands.

All commands except `serve` and `project list` are local-only and work in the current project
repository.

Beta adds:

```bash
taskpilot project enable <project-id>
taskpilot project disable <project-id>
taskpilot repair
```

Alpha does not include `doctor`; `validate` is the single diagnosis/validation command.

Read/list commands support `--json`:

- `taskpilot project list --json`;
- `taskpilot item list --json`;
- `taskpilot item show <item-id> --json`;
- `taskpilot validate --json`.

Write commands also support `--json` and return deterministic operation results or changed
resources.

Default human output:

- list commands use plain text tables;
- `item show` uses readable sections and includes comments by default;
- write commands use concise success summaries.

`taskpilot item list` default columns:

- ID;
- Type;
- Status;
- Priority;
- Title;
- Valid marker.

`taskpilot item list` sorts by numeric item ID in Alpha and excludes deleted items by default.
It supports basic filters: `--status`, `--type`, and `--priority`.

`taskpilot item list --json` returns item summaries only, including invalid summaries with
findings. It does not include comments.

`taskpilot item show <item-id>` and `taskpilot item show <item-id> --json` include comments by
default.

`taskpilot item delete <item-id>` is immediate, uses the same core update path as setting
`status: deleted`, and does not prompt. Deleted items can be shown or updated by direct ID.

`taskpilot project list` shows all registry entries, including disabled entries if they exist, and
sorts by project name. It does not check filesystem health in Alpha.

## WebUI Direction

The WebUI is browser-based only. There is no desktop shell.

Primary workspace page: Kanban board.

The WebUI project selector is a simple dropdown of active registered projects sorted by project
name. Projects are loaded lazily when selected/requested.

If a selected project cannot load because the path is missing, `.taskpilot/` is missing,
`project.yaml` is missing, or the project file is too invalid to load, the UI shows an empty
Kanban board with a large centered error message. The registry is not automatically changed.

Alpha Kanban board:

- columns: backlog, ready, in_progress, done, cancelled;
- hidden by default: deleted;
- shows all item types;
- sorts cards within each column by type order, then numeric item ID;
- type order: epic, feature, task, bug;
- supports drag/drop status changes for valid item cards;
- allows dragging valid cards into `cancelled` without confirmation;
- shows invalid item cards with a red `!` indicator where possible;
- does not allow dragging invalid item cards.

Beta adds filters.

Release UI capabilities include:

- expandable item trees, including epic -> feature -> task -> bug hierarchy;
- related item lists;
- drag item cards through columns to change status;
- open item in a modal on the same page;
- edit or delete item from the modal.

The item editor is a modal. Opening an item should not require leaving the current page.

Alpha WebUI item modal:

- edits only `title`, `status`, `priority`, and `description`;
- deletes an item by setting `status: deleted` after confirmation;
- shows comments read-only;
- shows all other Alpha item fields read-only;
- does not create items;
- does not add, edit, or delete comments;
- does not edit `parent_id` or non-parent links;
- shows invalid items as read-only validation details.

Comment add/edit/delete starts in Beta. WebUI item creation starts after Alpha.

Recommended frontend libraries:

- React;
- Vite;
- TypeScript;
- npm;
- CSS Modules;
- Radix UI primitives for accessible modal/dialog behavior;
- dnd-kit for drag and drop;
- TanStack Query for server state;
- React Hook Form for item edit forms.

## Technology Stack

TaskPilot uses Python for the core, CLI, and API server.

Python stack:

- Python project managed with `uv`;
- Pydantic for models and validation;
- PyYAML for YAML read/write;
- Typer for CLI;
- FastAPI for REST API;
- pytest for tests.

WebUI stack:

- React;
- Vite;
- TypeScript;
- npm;
- CSS Modules.

The intended repository structure is:

```text
task-pilot/
  pyproject.toml
  uv.lock
  src/taskpilot/
    core/
    cli/
    server/
  tests/
  web/
    package.json
    package-lock.json
    vite.config.ts
    src/
```

Business rules live in the Python core. The CLI calls the core directly. FastAPI calls the core
directly. The WebUI calls FastAPI and must not reimplement canonical validation or write rules.

## Server and API

`taskpilot serve` behavior in Alpha:

- binds to `127.0.0.1` only;
- uses port `7152` by default;
- supports `--port` override;
- does not open a browser by default;
- supports `--open` to open the browser;
- requires built WebUI assets and fails at startup if they are missing;
- checks WebUI assets only at startup;
- serves FastAPI docs at `/docs`;
- serves all active registered projects, loaded lazily.

Development may use a separate Vite dev server. Alpha uses npm directly for WebUI builds and does
not add a `taskpilot web build` command.

REST API routes use `/api/...` and identify projects by `project.id`.

Alpha API shape:

```text
GET /api/projects
GET /api/projects/{project_id}/items
GET /api/projects/{project_id}/items/{item_id}
PATCH /api/projects/{project_id}/items/{item_id}
```

Item update uses `PATCH` with partial fields. Drag/drop status changes use the same `PATCH`
endpoint. WebUI delete uses the same `PATCH` endpoint with `status: deleted`. Alpha does not need a
REST `DELETE` endpoint for items.

Item detail embeds comments. Alpha API does not expose a comment creation endpoint because WebUI
comments are read-only and CLI comment creation calls the Python core directly.

Alpha reads canonical project files directly.

## Acceptance Criteria

This decision capture is acceptable when:

- it records the current Alpha/Beta/Release terminology;
- it records one repo as one project;
- it records the local system registry and active-project serving model;
- it records `taskpilot init .` as the single Alpha onboarding command;
- it records pure YAML item files and separate Markdown comments;
- it records item fields, statuses, priorities, hierarchy, links, comments, and deletion behavior;
- it records the Kanban/modal WebUI direction;
- it records Alpha CLI command scope and JSON output rules;
- it records Alpha API route shape and serve behavior;
- it records the Python/FastAPI/Typer/PyYAML/uv stack and React/Vite/TypeScript/npm WebUI stack;
- `docs/specs/README.md` links to this specification.

## Open Questions

- What permanent-delete safeguards are required for Beta?
- What exact JSON response schemas should each Alpha CLI/API operation return?
