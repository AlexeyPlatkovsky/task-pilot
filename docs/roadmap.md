# Roadmap

## Release Levels

- **Alpha**: MVP used to validate the concept. Core workflow works end-to-end.
- **Beta**: Product-ready and releasable. Feature-complete with polished UX.
- **Release**: All or almost all initial features implemented with documentation and tests.

## Alpha Scope

Target: a developer can initialize a TaskPilot workspace, create items through CLI, inspect and
edit supported item fields through the WebUI, and
persist them as Git-friendly YAML files.

In scope:
- workspace initialization;
- file-based task storage (YAML items, Markdown comments);
- project support;
- item create, read, update;
- comments (append-only);
- basic links (blocks, relates_to);
- validation (`taskpilot validate`);
- local WebUI with Kanban board and item detail modal;
- CLI read/write commands with JSON output.

Direct file reading is the current storage access model.

## Beta Scope

Target: feature-complete product with polished UX and permanent data model.

Adds over Alpha:
- project-configured workflow statuses (Alpha list as default);
- full item field editing (dor, dod, tags, attachments, external_refs);
- comment edit/delete;
- permanent item delete with safeguards for links and comments;
- list view and tree view;
- filters across all views;
- Git sync helpers (status, changed files summary, commit validation);
- validation panel in WebUI;
- structured error visibility for invalid files.

## Release Scope

Target: all planned features implemented and documented.

Adds over Beta:
- MCP adapter exposing core operations as MCP tools;
- advanced relation visualization;
- item search with full-text capabilities;
- export/import helpers;
- comprehensive test coverage across all layers.

## Implementation Phases

### Phase 1 — File model and parser

Define workspace folder layout. Implement parser for item YAML files and comment Markdown files.
Implement writer with deterministic formatting. Implement validation. Add basic tests.

Serves: [F001: Task File Storage](features/F001_task-file-storage/)

### Phase 2 — Domain/service layer

Project operations, item operations, comment operations, link operations, validation rules.
No UI yet.

Serves: [F002: Domain Services](features/F002_domain-services/)

### Phase 3 — CLI

`init`, project list, item list/show/create/update, comments, JSON output, validation
command.

Serves: [F003: CLI Interface](features/F003_cli-interface/)

### Phase 4 — Local WebUI

Backend REST API, React app, project selector, Kanban board, item detail modal, read-only comments.

Serves: [F004: WebUI Workspace](features/F004_webui-workspace/)

### Phase 5 — Better views

Tree view, filters, sorting, and relation display.

Serves: [F006: Advanced Views](features/F006_advanced-views/)

### Phase 6 — Git helpers

Sync status, changed task files summary, validation before commit, optional pull/push wrappers.

Serves: [F007: Git Helpers](features/F007_git-helpers/)

### Phase 7 — MCP adapter

Expose core operations as MCP tools. No separate logic. Only after CLI/API stabilizes.

Serves: [F008: MCP Adapter](features/F008_mcp-adapter/)

## Recommended First Usable Slice

```text
Local WebUI + project selector + item list + item detail + read-only comments + file storage
```

Then: CLI + validation + links

Then: Kanban drag-and-drop + tree view + Git sync helpers

Then: MCP adapter
