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
| Domain services | Business rules for projects, items, comments, links. All adapters call this layer. | Python core under `src/taskpilot/services/`, shared across all surfaces |
| CLI adapter | Translates command-line input to domain operations. Supports human-readable and JSON output. | `src/taskpilot/cli/`, uses Typer |
| REST API server | Exposes domain operations over HTTP for the WebUI. FastAPI. | `src/taskpilot/server/`; see [F005](features/archive/F005_rest-api/) |
| WebUI | React browser application. Calls REST API. Board/list/tree workspace views, validation panel, item modal, project selector. | `web/`, Vite + TypeScript |
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

Adapters translate inputs and outputs; they do not own domain rules. Filesystem details do not leak
into the domain model.

## Data Model

### Source of truth

Canonical task data is stored as text files under `.taskpilot/` in the project repository root:

```text
.taskpilot/
  project.yaml
  items/
    TP-1.yaml
  comments/
    TP-1/
      2026-06-23T10-00-00Z.md
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

### Field constraints

`id` and `title` are non-empty strings; an empty or whitespace-only title is rejected at parse and
write time. Unknown fields present in an item file are preserved rather than dropped, so a human or
agent may add data the current schema does not know about without losing it on the next write.
Timestamps use a single canonical ISO form (`2026-06-23T10:00:00Z`); other shapes are a validation
finding.

### Item IDs

IDs are allocated by taking one past the highest existing numeric suffix. Gaps left by deleted
items are never reused, so an ID always refers to at most one item over the life of a project.

### Hierarchy

Typed hierarchy with at most one parent per item, stored via `parent_id`. Epics are root items and
bugs are leaves; the authoritative parent/child type table is owned by
[specs/0002](specs/0002-alpha-product-and-stack-decisions.md) as an accepted product contract.

Three guards protect the hierarchy on write:

- an item cannot be its own parent;
- reparenting walks the ancestor chain and rejects any edge that would create a cycle;
- changing an item's `type` is rejected when its existing children would become invalid under the
  table above.

### Links

Non-parent graph links stored as a map on the source item. Alpha types: `blocks`, `relates_to`.
Reverse relationships are derived at read time. Adding a link updates only the source item file.

Self-links are rejected, and a link naming an item that does not exist is rejected at write time
rather than being written and reported later by validation.

### Comments

Separate append-only Markdown files with YAML frontmatter. Folder name is the owning item ID.
Filename timestamp (`2026-06-23T10-00-00Z.md`) is the comment identity. Adding a comment does
not update the parent item's `updated_at`.

### Deletion

Alpha deletion sets `status: deleted`. Deleted item files remain in the repository. Deleted items
are hidden from the normal WebUI but remain visible to validation and direct lookup.

Deletion is idempotent: deleting an already-deleted item does not rewrite the file and leaves
`updated_at` untouched, so a repeated delete produces no Git diff. The same principle applies to
updates generally — an update whose fields all match current values short-circuits without a write.

## Tech Stack

### Core, CLI, and API server

- **Language**: Python
- **Project manager**: uv
- **Models and validation**: Pydantic
- **YAML read/write**: PyYAML
- **CLI framework**: Typer
- **REST API**: FastAPI
- **Testing**: pytest

### WebUI

- **Framework**: React
- **Build tool**: Vite
- **Language**: TypeScript
- **Package manager**: npm
- **Styling**: CSS Modules
- **UI primitives**: Radix UI (modal, dialog)
- **Drag and drop**: dnd-kit
- **Server state**: TanStack Query
- **Tables**: TanStack Table
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
- **Attachments**: Relative paths only, validated to not escape the repository root, missing files
  are warnings not errors. TaskPilot does not upload or manage attachment files through Beta.
- **Invalid-file surfacing**: The domain layer exposes invalid items as stubs carrying their
  findings, so an unparseable file stays visible instead of vanishing. Adapters differ in whether
  they use it: the REST API and WebUI surface invalid stubs, while `item list` on the CLI skips
  files it cannot parse and `taskpilot validate` is the CLI diagnosis path.
- **Registry concurrency**: The per-machine project registry is guarded by a lock file so
  concurrent CLI and server processes cannot interleave writes. `TASKPILOT_HOME` overrides the
  registry location, which is how tests isolate it from the real machine state.
- **WebUI asset packaging**: The server mounts built WebUI assets when present. When they are
  missing it serves an explicit packaging-error page with HTTP 503 and keeps the REST API
  available, rather than refusing to start.
- **Project scoping**: Item routes verify the requested item belongs to the requested project and
  return 404 otherwise, so a valid ID from one project cannot be read through another.
- **Data freshness**: The WebUI treats query data as stale after 30 seconds, polls every 5 seconds,
  refetches on window focus or visibility return, and retries a failed query once. Canonical files
  can be edited outside the app, so the UI is built to converge on external changes rather than
  assume it is the only writer.

## Contract Surface

The exact contract — 15 CLI commands and their options, the three exit codes, 8 REST endpoints, 13
request/response models, and 18 validation finding codes — is owned by
[api.md](api.md). This document describes structure; that one describes the interface.

## Key Decisions

- See `decisions/ADR-001-file-source-of-truth.md` — canonical YAML/Markdown files as the source of truth
- See `decisions/ADR-002-python-fast-mvp-stack.md` — Python/uv/Typer/FastAPI stack for core and API
- See `decisions/ADR-003-yaml-item-format.md` — pure YAML item files instead of Markdown with YAML frontmatter
- See `decisions/ADR-004-separate-comments.md` — append-only comment files separate from item files
- See `decisions/ADR-005-kanban-first-webui.md` — Kanban board as the primary workspace page
