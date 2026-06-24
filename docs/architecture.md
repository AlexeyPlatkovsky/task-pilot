# Architecture

## System Context

TaskPilot is a local-first task graph that runs on a developer's machine. It has no cloud
dependency and operates on project repositories. External actors are limited to:

- the **local developer** using the WebUI or CLI;
- **AI coding agents** consuming the CLI with JSON output;
- **Git** for synchronization and collaboration across machines;
- future **MCP clients** accessing tasks through a thin adapter.

The system does not integrate with hosted services, issue trackers, or authentication providers.

## Components

| Component | Responsibility | Notes |
| --- | --- | --- |
| File parser/validator | Reads and writes canonical YAML item files and Markdown comment files. Validates structure, required fields, and references. | Python core under `src/taskpilot/core/` |
| Domain services | Business rules for projects, items, comments, links. All adapters call this layer. | Python core, shared across all surfaces |
| CLI adapter | Translates command-line input to domain operations. Supports human-readable and JSON output. | `src/taskpilot/cli/`, uses Typer |
| REST API server | Exposes domain operations over HTTP for the WebUI. FastAPI. | `src/taskpilot/server/` |
| WebUI | React browser application. Calls REST API. Kanban board, item modal, project selector. | `web/`, Vite + TypeScript |
| SQLite index/cache | Disposable local index for fast WebUI queries. Rebuildable from canonical files. | `better-sqlite3` via Python, under `.taskpilot/cache/` |
| Local system registry | Machine-specific state: active/inactive project roots, preferences, cache paths. Not committed to Git. | OS app data directory |
| MCP adapter (future) | Thin adapter exposing domain operations as MCP tools. | Same domain layer, no separate logic |

Architecture boundary:

```text
canonical task files
  -> parser / validator
  -> domain model and services
  -> CLI | REST API | future MCP
  -> WebUI through REST API
```

Adapters translate inputs and outputs; they do not own domain rules. Filesystem and SQLite details
do not leak into the domain model.

## Data Model

### Source of truth

Canonical task data is stored as text files under `.taskpilot/` in the project repository root:

```text
.taskspilot/
  project.yaml
  items/
    TP-1.yaml
  comments/
    TP-1/
      2026-06-23T10-00-00Z.md
  cache/
    index.db          (Git-ignored, disposable)
```

### Project

One repository contains exactly one TaskPilot project. A project has a stable identity, display
name, and a readable key prefix (e.g. `TP`).

### Item

Items are pure YAML files named by ID (`TP-1.yaml`). Item IDs are sequential per project with
gaps allowed. Supported types: epic, feature, task, bug. Workflow statuses: backlog, ready,
in_progress, done, cancelled. The `deleted` status is a reserved system status.

Mandatory fields: `schema_version`, `id`, `title`, `priority`, `type`, `status`, `created_at`,
`updated_at`. Optional fields: `description`, `tags`, `parent_id`, `links`, `dor`, `dod`,
`attachments`, `external_refs`, `created_by`, `performed_by`.

### Hierarchy

Typed hierarchy with at most one parent per item. Stored via `parent_id`. Allowed rules:

| Parent type | Allowed child types |
| --- | --- |
| epic | feature, task |
| feature | task |
| task | bug |
| bug | none |

### Links

Non-parent graph links stored as a map on the source item. Alpha types: `blocks`, `relates_to`.
Reverse relationships are derived at read time. Adding a link updates only the source item file.

### Comments

Separate append-only Markdown files with YAML frontmatter. Folder name is the owning item ID.
Filename timestamp (`2026-06-23T10-00-00Z.md`) is the comment identity. Adding a comment does
not update the parent item's `updated_at`.

### Deletion

Alpha deletion sets `status: deleted`. Deleted item files remain in the repository. Deleted items
are hidden from the normal WebUI but remain visible to validation and direct lookup.

### SQLite index

A disposable local SQLite database under `.taskpilot/cache/index.db`. Built from canonical files,
ignored by Git, and rebuildable on demand or on file change. Contains no unique source-of-truth
data. Writes always update canonical files first, then refresh the index.

## Tech Stack

### Core, CLI, and API server

- **Language**: Python
- **Project manager**: uv
- **Models and validation**: Pydantic
- **YAML read/write**: PyYAML
- **CLI framework**: Typer
- **REST API**: FastAPI
- **SQLite**: better-sqlite3 (via Python bindings)
- **Testing**: pytest

### WebUI

- **Framework**: React
- **Build tool**: Vite
- **Language**: TypeScript
- **Package manager**: npm
- **Styling**: CSS Modules
- **UI primitives**: Radix UI (modal, dialog)
- **Drag and drop**: dnd-kit (future)
- **Server state**: TanStack Query
- **Forms**: React Hook Form

### Repository structure

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
directly. The WebUI calls FastAPI and does not reimplement canonical validation or write rules.

## Integrations

No external API or service integrations in Alpha/Beta. The only external dependency is Git for
synchronization, treated as a transparent tool rather than an API.

## Constraints

- Offline-first: all core operations must work without network access.
- Cross-platform: macOS, Linux, and Windows paths must be handled.
- Deterministic: serialization, JSON output, and file formatting must be stable across writes.
- Git-friendly: one file per item, separate comments, no committed binary databases.
- Local WebUI only: browser-based, no desktop shell.

## Cross-Cutting Concerns

- **Validation**: Invalid files do not block project loading. Valid items still display. Validation
  available through `taskpilot validate` and a WebUI errors panel.
- **Error handling**: Writes validate the target operation before changing files. Writes do not
  silently rewrite unrelated invalid files.
- **File watching**: Optional future watcher to auto-rebuild the SQLite index on canonical file
  changes.
- **Attachments**: Relative paths only, validated to not escape the repository root, missing files
  are warnings not errors. TaskPilot does not upload or manage attachment files through Beta.

## Key Decisions

- See `decisions/ADR-001-file-source-of-truth.md` — canonical YAML/Markdown files as the source of truth
- See `decisions/ADR-002-python-fast-mvp-stack.md` — Python/uv/Typer/FastAPI stack for core and API
- See `decisions/ADR-003-yaml-item-format.md` — pure YAML item files instead of Markdown with YAML frontmatter
- See `decisions/ADR-004-separate-comments.md` — append-only comment files separate from item files
- See `decisions/ADR-005-kanban-first-webui.md` — Kanban board as the primary workspace page
