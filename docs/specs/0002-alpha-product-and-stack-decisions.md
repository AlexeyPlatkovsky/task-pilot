# 0002: Alpha Product and Stack Decisions

## Status

draft

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

The system directory stores local registry, active/inactive project flags, cache/index data, and
local preferences. It is not committed to project repositories and is not canonical product data.

The WebUI serves active registered projects from the local system registry. A registered project
can be disabled locally without changing the project repository.

## Project Registration

Registration is explicit and current-folder-only.

Expected commands:

```bash
taskpilot init .
taskpilot register .
taskpilot serve
```

`taskpilot init .` creates repository-local TaskPilot files for a new project and registers the
current project root locally.

`taskpilot register .` registers an existing TaskPilot project in the current folder. It inspects
only the current folder and does not scan child or parent folders.

`taskpilot serve` serves all active registered projects by default.

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

The filename timestamp is the comment identity within the item. `created_at` should match the
filename timestamp. If two comments collide at the same second, TaskPilot should add a deterministic
suffix to the filename.

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
- invalid item/comment files are shown in a validation/errors surface;
- writes validate the target operation before changing files;
- writes do not silently rewrite unrelated invalid files.

## CLI and WebUI Write Surface

Alpha supports editing through both CLI and WebUI. Both surfaces must use the same Python core
services.

Minimal shared write operations:

- create item;
- update item fields;
- add comment;
- set, change, or remove `parent_id`;
- add or remove links;
- delete item by setting `status: deleted`.

Read operations should support deterministic JSON output where relevant.

## WebUI Direction

The WebUI is browser-based only. There is no desktop shell.

Primary workspace page: Kanban board.

Alpha Kanban board:

- columns: backlog, ready, in_progress, done, cancelled;
- hidden by default: deleted;
- shows all item types;
- sorts cards within each column by type order, then numeric item ID;
- type order: epic, feature, task, bug.

Beta adds filters.

Release UI capabilities include:

- expandable item trees, including epic -> feature -> task -> bug hierarchy;
- related item lists;
- drag item cards through columns to change status;
- open item in a modal on the same page;
- edit or delete item from the modal.

The item editor is a modal. Opening an item should not require leaving the current page.

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

## Acceptance Criteria

This decision capture is acceptable when:

- it records the current Alpha/Beta/Release terminology;
- it records one repo as one project;
- it records the local system registry and active-project serving model;
- it records pure YAML item files and separate Markdown comments;
- it records item fields, statuses, priorities, hierarchy, links, comments, and deletion behavior;
- it records the Kanban/modal WebUI direction;
- it records the Python/FastAPI/Typer/PyYAML/uv stack and React/Vite/TypeScript/npm WebUI stack;
- `docs/specs/README.md` links to this specification.

## Open Questions

- Should invalid files appear only in a validation panel/list or also as error cards on the
  Kanban board?
- What exact `project.yaml` fields are required?
- What exact CLI command names, options, exit codes, and JSON schemas are accepted?
- What exact REST API routes and response schemas are accepted?
- What timestamp precision and collision suffix format should comments use?
- What permanent-delete safeguards are required for Beta?
- What cache/index format is required, and when is it introduced?
