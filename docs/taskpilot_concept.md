# TaskPilot — Local-First Task Graph for AI Agents

This document records product intent and principles at a high level, kept in sync with the
implemented product. It does not own contract detail: `docs/architecture.md` owns current
structure, `docs/decisions/` owns the rationale for each choice, and `docs/specs/` owns accepted
product behavior. Where this document and an ADR appear to disagree, that is a defect in this
document — report it rather than following it.

## 1. Product Idea

 A local-first task graph for AI coding agents, with a human-friendly UI and transparent file-based storage.

The system should help humans and AI agents share the same structured understanding of work: epics, features, tasks, subtasks, blockers, tests, comments, and current status.

The key design principle is simplicity and transparency:

- no cloud dependency;
- no mandatory account;
- no hidden embedded tools;
- no complex database synchronization;
- no opaque binary source of truth;
- no magic AI behavior;
- all important project/task data should be readable and reviewable in Git.

TaskPilot should be usable by:

- a human through a local WebUI;
- AI coding agents through CLI commands;
- optionally, MCP clients later through a thin adapter over the same core logic.

## 2. Core Problem

AI coding agents often need a persistent task context.

A normal project repository has source code, docs, tests, and issues may exist somewhere else: Jira, GitHub Issues, Linear, Notion, or plain chat history.

For local AI workflows, this creates several problems:

- agents lose task context between sessions;
- project work is fragmented between external trackers and code;
- task state is not always available offline;
- cloud issue trackers are too heavy for small local projects;
- local CLI-first tools may be hard to inspect visually;
- binary databases are poor Git citizens;
- AI agents need structured, machine-readable data, not only human notes.

TaskPilot should provide a small local task system that lives near the codebase and can be safely used by both humans and agents.

## 3. Design Goals

### 3.1 Local-first

TaskPilot should work fully offline.

A user should be able to run it locally on:

- macOS;
- Linux / Ubuntu;
- Windows.

The default mode should not require a server, cloud account, or remote database.

### 3.2 Git-friendly

The canonical task data should be stored in text files that can be committed to Git.

GitHub should be usable as a simple synchronization layer:

- task changes are visible in diffs;
- pull requests can review task changes;
- branches can merge task changes better than binary databases;
- conflicts are limited by using one file per item where possible.

### 3.3 Human-readable

A developer should be able to open the task files directly and understand them without TaskPilot running.

Items are stored as pure YAML files. Comments are Markdown files with YAML frontmatter. See
ADR-003 for why item files carry no Markdown body.

### 3.4 AI-readable

AI agents should be able to read and write tasks through a stable interface.

The primary AI interface should be CLI commands with JSON output.

MCP can be added later, but it should be an adapter, not the core.

### 3.5 Simple workflow

TaskPilot should not start as a full enterprise issue tracker.

The default workflow is intentionally small:

- backlog;
- ready;
- in progress;
- done;
- cancelled.

`deleted` exists as a reserved system status for soft deletion and is not part of the user-facing
workflow.

The system may support custom statuses later, but this fixed set is enough for the current
releases.

### 3.6 Transparent implementation

No hidden embedded tools.

No agent-only behavior that a human cannot inspect.

Every important operation should be visible through:

- task files;
- UI state;
- CLI output;
- activity/log history where useful.

## 4. Non-goals for Early Versions

The first versions should avoid:

- real-time collaboration;
- user accounts;
- hosted cloud sync;
- permissions/roles;
- custom workflow builder;
- Gantt charts;
- sprint planning;
- story points complexity;
- rich automation engine;
- plugin system;
- complex notifications;
- GitHub Issues sync as the core model;
- committed binary databases as the main synchronization mechanism.

These can be explored later if the project proves useful.

## 5. High-Level Architecture

The recommended architecture:

```text
Markdown/YAML task files = source of truth
        ↓
Parser / validator
        ↓
Domain model / service layer
        ↓
REST API
        ↓
Local WebUI

CLI commands call the same domain/service layer.
MCP, if added later, also calls the same domain/service layer.
```

The main idea:

- files are canonical;
- UI reads through the REST API;
- CLI and API never bypass domain rules;
- MCP is optional and thin.

## 6. Storage Strategy

### 6.1 Source of truth

The source of truth should be text files inside the repository or inside a selected workspace directory.

Structure:

```text
.taskpilot/
  project.yaml
  items/
    TP-1.yaml
    TP-2.yaml
    TP-3.yaml
  comments/
    TP-1/
      2026-06-19T18-20-00Z.md
```

One workspace holds one project. Multiple projects are supported by registering several workspaces
in a per-machine registry outside the repository, not by nesting projects inside `.taskpilot/`.

Committed to Git:

```text
.taskpilot/project.yaml
.taskpilot/items/**/*
.taskpilot/comments/**/*
```

### 6.2 Item files

Each item should have its own file.

This is important for Git merge behavior.

Bad approach:

```text
items.json
```

Better approach:

```text
items/TP-1.yaml
items/TP-2.yaml
items/TP-3.yaml
```

One-file-per-item gives cleaner diffs and reduces merge conflicts when different agents or users work on different items.

### 6.3 Item file format

Items are pure YAML, with the description as an ordinary field rather than a Markdown body:

```yaml
schema_version: 1
id: TP-42
type: feature
title: Add OpenAI transcription benchmark
status: in_progress
priority: high
created_at: '2026-06-19T18:00:00Z'
updated_at: '2026-06-19T18:30:00Z'
parent_id: TP-10
blocks:
  - TP-51
description: |
  Description goes here.
```

A single format for the whole file keeps parsing and deterministic serialization simple, and avoids
the ambiguity of a body that is sometimes structured and sometimes prose. Unknown fields are
preserved rather than dropped, so a human or agent can add data the current schema does not know
about. See ADR-003.

### 6.4 Comments

Comments should be stored separately from item files to reduce merge conflicts.

Recommended structure:

```text
comments/
  TP-42/
    2026-06-19T18-31-00Z_agent.md
    2026-06-19T18-45-00Z_user.md
```

Each comment can be append-only.

This avoids many conflicts caused by multiple agents editing the same task file only to add comments.

### 6.5 Links

Links should be stored only in one direction.

Example:

```text
TP-42 blocks TP-51
```

The system should calculate the reverse relation:

```text
TP-51 is blocked by TP-42
```

Do not manually store both directions in source files unless there is a very strong reason.

This prevents duplicated data and inconsistent state.

Implemented link types:

- parent / child;
- blocks / blocked by;
- relates to.

`tests / tested by` and `duplicates / duplicated by` were considered and are not implemented.

Internally, the system defines canonical link types and derived reverse names.

## 7. Direct File Reading Strategy

TaskPilot reads canonical project files directly through the parser, validator, and domain/service
layer.

The local WebUI should request data from the REST API. The REST API and CLI should share the same
domain operations so sorting, filtering, grouping, searching, and validation behavior remain
consistent across surfaces.

Important properties:

- canonical files remain the only persisted task data;
- all reads are derived from project files;
- all write operations update source files through the validated write path;
- performance work must preserve deterministic serialization and invalid-file visibility.

## 8. Synchronization via GitHub

TaskPilot should not synchronize by committing binary task databases. Synchronization should happen
through Git-friendly task files.

Basic manual flow:

```bash
git pull --rebase
# work with tasks
git add .taskpilot/
git commit -m "Update TaskPilot tasks"
git push
```

Later TaskPilot can provide helper commands:

```bash
taskpilot sync status
taskpilot sync pull
taskpilot sync push
taskpilot sync export
taskpilot sync import
```

But these commands should remain wrappers around transparent Git/file operations.

The user should never be forced into hidden sync logic.

## 9. Project Model

TaskPilot supports multiple projects.

One TaskPilot workspace holds exactly one project, and each project lives in its own repository
next to the code it describes. Several workspaces are registered in a per-machine registry stored
outside any repository, so the WebUI can switch between projects without any project owning
another.

A project has:

- id;
- name;
- key/prefix, for example `VP`, `PF`, `SP`.

Per-project default statuses, default priorities, and UI preferences were considered and are not
implemented. Per-machine WebUI state, such as the last opened project, is stored in the registry
directory rather than in the project.

Item IDs can use project prefixes:

```text
VP-1
PF-12
SP-4
```

This is more readable than global numeric IDs.

## 10. Item Model

The first version should support a small set of item types:

- epic;
- feature;
- task;
- bug.

Items support graph-like links, not only strict hierarchy.

An item can have:

- parent item;
- child items;
- blockers;
- blocked items;
- related items.

A task can be a parent for another task.

The model should not force every task to belong to an epic or feature.

Useful mandatory fields for early versions:

- id;
- project;
- type;
- title;
- status;
- created_at;
- updated_at.

Useful optional fields:

- description;
- priority;
- assignee/actor;
- tags;
- links;
- completed_at;
- external references.

No database schema should be defined at this stage. The exact schema can be decided during implementation.

## 11. Views in Local WebUI

The WebUI should be local-only by default.

Initial command:

```bash
taskpilot serve
```

Then the UI opens or becomes available at:

```text
http://localhost:<port>
```

### 11.1 Project selector

The UI should allow switching between projects.

The selected project controls list, board, tree, and item detail views.

### 11.2 List view

The list view is the most important MVP view.

It should support:

- item title;
- item type;
- status;
- priority;
- creation date;
- updated date;
- sorting;
- filtering;
- opening item details.

Basic filters:

- all;
- last 7 days;
- last 14 days;
- last month;
- status;
- type;
- priority.

### 11.3 Item detail view

The item detail page/drawer is the core interaction surface.

It should show:

- title;
- type;
- status;
- priority;
- description;
- links;
- child items;
- blocking relationships;
- comments;
- metadata.

It should allow:

- editing title/description/status/priority;
- adding comments;
- adding/removing links;
- creating child items.

### 11.4 Kanban view

The Kanban board is the primary workspace page. See ADR-005.

Columns match the user-facing workflow statuses:

- backlog;
- ready;
- in progress;
- done;
- cancelled.

Drag and drop updates item status. Advanced swimlanes and custom workflows remain out of scope.

### 11.5 Tree view

Tree view shows expandable hierarchy. It is implemented but hidden from navigation in the current
release.

Example:

```text
Epic
  Feature
    Task
      Subtask
```

But hierarchy should be based on parent/child links, not hardcoded type rules.

A task can have child tasks.
A feature can have tasks.
An epic can have features and tasks.

The tree view should not be the only way to understand relationships, because the model is a graph.

## 12. CLI Interface

The CLI is the most important agent-facing interface.

It should be stable, explicit, and scriptable.

All read commands should support JSON output.

Example commands:

```bash
taskpilot --json project list

taskpilot --json item list --status ready
taskpilot --json item show VP-42
taskpilot item create --type feature --title "OpenAI transcription benchmark"
taskpilot item update VP-42 --status in_progress
taskpilot item blocks VP-42 VP-51
taskpilot item comment VP-42 "Investigated current implementation"
```

`--json` is a global option and must precede the subcommand. Link operations use explicit verb
pairs — `parent`/`unparent`, `blocks`/`unblocks`, `relates`/`unrelates` — rather than a generic
`link`/`unlink`.

Recommended CLI principles:

- deterministic output;
- JSON support for agents;
- human-readable default output;
- clear exit codes;
- no hidden side effects;
- dry-run mode for risky operations;
- validation before writes;
- safe errors with actionable messages.

At a high level the command surface covers workspace setup (`init`), the local server (`serve`),
project inspection, item read and write, hierarchy and link verbs, comments, and `validate`. The
authoritative command list is `taskpilot --help`; no document currently owns the full contract
(tracked as TP-117).

## 13. MCP Position

MCP is not required for v0.1.

If CLI commands are good, many AI tools can already use TaskPilot through shell commands.

MCP should be treated as an optional adapter for MCP-native clients.

It should not contain separate business logic.

Recommended layering:

```text
Domain/service layer
  ↑
CLI adapter
REST API adapter
MCP adapter
```

Possible future MCP tools:

- `project_list`;
- `item_create`;
- `item_update`;
- `item_link`;
- `item_search`;
- `item_ready`;
- `item_tree`.

MCP should call the same core operations as CLI and WebUI.

## 14. Backend / API Layer

The backend is lightweight:

- Python;
- FastAPI;
- local filesystem access;
- REST API for the WebUI.

The backend does not own business rules alone.

Business rules should live in a domain/service layer used by:

- REST API;
- CLI;
- future MCP adapter.

The backend should provide endpoints for:

- projects;
- items;
- item links;
- comments;
- search/filtering;
- validation results.

No API contract needs to be finalized now, but the boundaries should remain clear.

## 15. Frontend / WebUI Layer

Frontend stack:

- React;
- Vite;
- TypeScript;
- CSS Modules with a semantic design-token layer;
- Radix UI primitives and lucide-react icons;
- TanStack Query for data fetching, TanStack Table for the list view;
- dnd-kit for Kanban drag and drop.

The UI focuses on usability, not enterprise complexity.

Implemented screens:

- project selector;
- Kanban board (primary);
- list view;
- item detail modal with comments;
- validation status.

Tree view is implemented but hidden from navigation. A sync status view remains out of scope.

## 16. Validation Rules

Because files are editable by humans and agents, validation is critical.

TaskPilot should validate:

- item IDs are unique inside project/workspace;
- required fields exist;
- status values are valid;
- type values are valid;
- links point to existing items;
- no invalid link type is used;
- timestamps are parseable;
- project references are valid;
- frontmatter is valid YAML.

Validation should be available through:

```bash
taskpilot validate
```

The UI should also show validation errors.

Invalid files should not silently disappear.
They should be visible and fixable.

## 17. Activity and Audit Trail

Early versions can rely on Git history for audit.

However, TaskPilot may still benefit from local activity events.

There are two possible approaches:

### Simple approach

Store updated timestamps and comments only.

Use Git history for detailed audit.

This is enough for v0.1.

### Event-log approach

Later, TaskPilot can store append-only events:

```text
.taskpilot/events/
  2026-06-19T18-00-00Z_item-created.yaml
  2026-06-19T18-05-00Z_status-changed.yaml
  2026-06-19T18-10-00Z_comment-added.yaml
```

This gives strong auditability and better merge behavior, but adds complexity.

Event sourcing should not be part of the first MVP unless the project intentionally chooses an architecture-heavy path.

## 18. Conflict Handling

Git conflicts will still happen.

TaskPilot should minimize them by design:

- one file per item;
- separate comment files;
- no single giant JSON database;
- no committed binary task database;
- no duplicated reverse links;
- stable formatting;
- deterministic serialization.

When conflicts happen, they should be normal text conflicts that developers can resolve.

Future tooling can help:

```bash
taskpilot validate
taskpilot repair
taskpilot conflicts explain
```

But the first version only needs validation.

## 19. Packaging and Running

TaskPilot is distributed as an npm package whose wrapper provisions and caches a managed Python
runtime on first run, so users install it with a single familiar command without needing a Python
toolchain of their own.

User-facing commands:

```bash
taskpilot init
taskpilot serve
taskpilot validate
```

A desktop packaging path (standalone binaries, Tauri) remains out of scope. A local WebUI is
enough.

## 20. MVP Scope

The recommended v0.1 scope:

- workspace initialization;
- file-based task storage;
- project support;
- item create/read/update;
- comments;
- basic links;
- validation;
- local WebUI;
- list view;
- item detail view;
- CLI read/write commands;
- JSON output for CLI.

Recommended first usable slice:

```text
Local WebUI + project selector + item list + item detail + comments + file storage
```

Then add:

```text
CLI + validation + links
```

Then add:

```text
Kanban + tree view + Git sync helpers
```

## 21. Suggested Implementation Phases

### Phase 1 — File model and parser

- define workspace folder layout;
- implement parser for item files;
- implement writer with deterministic formatting;
- implement validation;
- add basic tests.

### Phase 2 — Domain/service layer

- project operations;
- item operations;
- comment operations;
- link operations;
- validation rules;
- no UI yet.

### Phase 3 — CLI

- `init`;
- project list/create;
- item list/show/create/update;
- comments;
- JSON output;
- validation command.

### Phase 4 — Local WebUI

- backend API;
- React app;
- project selector;
- item list;
- item detail;
- comments.

### Phase 5 — Better views

- Kanban board;
- tree view;
- filters;
- sorting;
- relation display.

### Phase 6 — Git helpers

- sync status;
- changed task files summary;
- validation before commit;
- optional pull/push wrappers.

### Phase 7 — MCP adapter

- only after CLI/API stabilizes;
- expose core operations as MCP tools;
- no separate logic.

## 22. Recommended Tech Stack

Current stack:

```text
Core language: Python, managed with uv
Models and validation: Pydantic
YAML read/write: PyYAML
CLI: Typer
Backend: FastAPI, served by uvicorn
Core tests: pytest
Frontend: React + Vite + TypeScript, npm
UI: CSS Modules + design tokens, Radix UI primitives, lucide-react icons
Tables: TanStack Table
Data fetching: TanStack Query
Kanban: dnd-kit
Frontend tests: Vitest + Testing Library, Playwright for E2E and browser contract
Storage source of truth: YAML item files, Markdown comment files
Distribution: npm wrapper around a managed Python runtime
```

Python owns the core, CLI, and API so business rules live in one place; the WebUI is TypeScript and
calls the REST API without reimplementing canonical validation or write rules. See ADR-002.

## 23. Naming and Positioning

Possible names:

- TaskPilot;
- IssuePilot;
- TaskGraph;
- AgentBoard;
- PilotBoard.

TaskPilot is acceptable and fits the user’s existing “Pilot” naming family.

Best short positioning:

> TaskPilot is a local-first task graph for AI coding agents.

Longer positioning:

> TaskPilot stores project tasks as Git-friendly Markdown/YAML files and exposes the same task
> graph to humans through a WebUI and to AI agents through CLI commands.

## 24. Key Architectural Decisions

1. YAML item files are the canonical source of truth (ADR-001).
2. One file per item to reduce Git merge conflicts.
3. Comments are separate append-style Markdown files (ADR-004).
4. Reverse links are derived, not stored manually.
5. CLI is the primary AI-facing interface.
6. MCP is optional and should be added later as an adapter.
7. WebUI is local-first and starts simple.
8. The Kanban board is the primary workspace page (ADR-005).
9. GitHub synchronization happens through normal Git over text files, not binary task data.
10. Python owns the core, CLI, and API; the WebUI is TypeScript over the REST API (ADR-002).

## 25. Final Summary

TaskPilot should be a small, local, transparent issue/task system optimized for AI-assisted development.

The strongest architecture is:

```text
Git-friendly Markdown/YAML files as source of truth
+
local WebUI for humans
+
CLI with JSON output for AI agents
+
optional MCP adapter later
```

The main value is not replacing Jira.

The main value is giving AI agents and humans a shared, inspectable, local task graph that lives close to the code and can be synchronized through GitHub without opaque databases or cloud dependencies.
