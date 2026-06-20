# TaskPilot — Local-First Task Graph for AI Agents

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

The preferred storage format is Markdown with YAML frontmatter, or YAML files with Markdown bodies.

### 3.4 AI-readable

AI agents should be able to read and write tasks through a stable interface.

The primary AI interface should be CLI commands with JSON output.

MCP can be added later, but it should be an adapter, not the core.

### 3.5 Simple workflow

TaskPilot should not start as a full enterprise issue tracker.

The default workflow should be intentionally small:

- backlog;
- next;
- ready;
- in progress;
- done;
- cancelled.

The system should support custom statuses later, but fixed statuses are enough for v0.1.

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
- direct SQLite commits as the main synchronization mechanism.

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
Local SQLite index/cache
        ↓
REST API
        ↓
Local WebUI

CLI commands call the same domain/service layer.
MCP, if added later, also calls the same domain/service layer.
```

The main idea:

- files are canonical;
- SQLite is disposable;
- UI uses SQLite/indexing for speed;
- CLI and API never bypass domain rules;
- MCP is optional and thin.

## 6. Storage Strategy

### 6.1 Source of truth

The source of truth should be text files inside the repository or inside a selected workspace directory.

Example structure:

```text
.taskpilot/
  config.yaml
  projects/
    voicepilot/
      items/
        TP-1.md
        TP-2.md
        TP-3.md
      comments/
        TP-1/
          2026-06-19T18-20-00Z.md
      attachments/
  cache/
    index.db
```

Committed to Git:

```text
.taskpilot/config.yaml
.taskpilot/projects/**/*
```

Ignored by Git:

```text
.taskpilot/cache/
```

The SQLite index should never be treated as canonical state.

### 6.2 Item files

Each item should have its own file.

This is important for Git merge behavior.

Bad approach:

```text
items.json
```

Better approach:

```text
items/TP-1.md
items/TP-2.md
items/TP-3.md
```

One-file-per-item gives cleaner diffs and reduces merge conflicts when different agents or users work on different items.

### 6.3 Preferred file format

Preferred item format:

```markdown
---
id: TP-42
type: feature
title: Add OpenAI transcription benchmark
status: in_progress
priority: high
created_at: 2026-06-19T18:00:00Z
updated_at: 2026-06-19T18:30:00Z
links:
  parent:
    - TP-10
  blocks:
    - TP-51
---

# Add OpenAI transcription benchmark

Description goes here.
```

The frontmatter contains structured fields.
The Markdown body contains longer human-readable description.

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

Recommended initial link types:

- parent / child;
- blocks / blocked by;
- tests / tested by;
- relates to;
- duplicates / duplicated by.

Internally, the system can define canonical link types and derived reverse names.

## 7. SQLite Indexing Strategy

SQLite should be used as a local index/cache, not as the source of truth.

The local WebUI needs fast sorting, filtering, grouping, and searching.

Reading hundreds or thousands of Markdown/YAML files on every UI request is possible at first, but eventually inefficient.

The solution:

- parse files from `.taskpilot/projects/**`;
- validate them;
- build an SQLite index under `.taskpilot/cache/index.db`;
- use SQLite for fast UI queries;
- rebuild the index whenever files change or on explicit command.

Important properties:

- SQLite cache can be deleted safely;
- cache can be rebuilt from task files;
- cache should be ignored by Git;
- cache should not contain unique information unavailable in files;
- all write operations should update source files first, then refresh/update the index.

Possible commands:

```bash
taskpilot index rebuild
taskpilot index validate
taskpilot index status
```

## 8. Synchronization via GitHub

TaskPilot should not synchronize by committing SQLite databases.

SQLite is a binary file. Git can version it, but merging is painful and diffs are unreadable.

Instead, synchronization should happen through Git-friendly task files.

Basic manual flow:

```bash
git pull --rebase
taskpilot index rebuild
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

TaskPilot should support multiple projects.

One TaskPilot workspace can contain several projects.

Each project has its own items, comments, and attachments.

Example:

```text
.taskpilot/projects/
  voicepilot/
  playforge/
  sidepilot/
```

A project should have:

- name;
- key/prefix, for example `VP`, `PF`, `SP`;
- optional description;
- optional default statuses;
- optional default priorities;
- optional UI preferences.

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
- bug;
- test/check, optional later.

Items should support graph-like links, not only strict hierarchy.

An item can have:

- parent item;
- child items;
- blockers;
- blocked items;
- related items;
- tests/checks;
- duplicated/duplicate relationship.

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

Kanban can be added after list/detail flow works.

Columns:

- backlog;
- next;
- ready;
- in progress;
- done;
- cancelled.

The first version can support simple drag/drop status updates.

Advanced swimlanes and custom workflows should be delayed.

### 11.5 Tree view

Tree view should show expandable hierarchy.

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
taskpilot project list --json
taskpilot project create "VoicePilot" --key VP

taskpilot item list --project VP --status ready --json
taskpilot item show VP-42 --json
taskpilot item create --project VP --type feature --title "OpenAI transcription benchmark"
taskpilot item update VP-42 --status in_progress
taskpilot item link VP-42 blocks VP-51
taskpilot item comment VP-42 "Investigated current implementation"
```

Recommended CLI principles:

- deterministic output;
- JSON support for agents;
- human-readable default output;
- clear exit codes;
- no hidden side effects;
- dry-run mode for risky operations;
- validation before writes;
- safe errors with actionable messages.

Possible early commands:

```bash
taskpilot init
taskpilot serve
taskpilot project list
taskpilot project create
taskpilot item list
taskpilot item show
taskpilot item create
taskpilot item update
taskpilot item link
taskpilot item unlink
taskpilot item comment
taskpilot index rebuild
taskpilot validate
```

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

The backend should be lightweight.

Recommended stack for fast MVP:

- Node.js;
- Fastify or Hono;
- TypeScript;
- local filesystem access;
- SQLite index/cache;
- REST API for WebUI.

The backend should not own business rules alone.

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
- index status;
- validation results.

No API contract needs to be finalized now, but the boundaries should remain clear.

## 15. Frontend / WebUI Layer

Recommended frontend stack:

- React;
- Vite;
- TypeScript;
- TanStack Table for list view;
- dnd-kit for Kanban later;
- shadcn/ui or another lightweight component system.

The UI should focus on usability, not enterprise complexity.

Initial screens:

- project selector;
- list view;
- item detail drawer/page;
- comments;
- basic create/edit forms.

Later screens:

- Kanban board;
- tree view;
- validation/errors view;
- sync status view.

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
- no committed SQLite database;
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

MVP can run as a normal Node.js app.

Development commands:

```bash
npm install
npm run dev
```

User-facing commands later:

```bash
taskpilot init
taskpilot serve
taskpilot validate
taskpilot index rebuild
```

Possible packaging options later:

- npm package with CLI;
- standalone binaries via pkg/nexe/bun compile, if suitable;
- Tauri desktop app later, if local desktop UX becomes important.

Do not start with desktop packaging.

A local WebUI is enough for MVP.

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
- JSON output for CLI;
- local SQLite index/cache if needed.

If time is limited, SQLite index can be delayed.
For the first hundred items, direct file reading may be enough.

Recommended first usable slice:

```text
Local WebUI + project selector + item list + item detail + comments + file storage
```

Then add:

```text
CLI + validation + links + SQLite index
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

### Phase 5 — SQLite index/cache

- build local index;
- rebuild command;
- file watcher or manual refresh;
- use index for fast UI queries.

### Phase 6 — Better views

- Kanban board;
- tree view;
- filters;
- sorting;
- relation display.

### Phase 7 — Git helpers

- sync status;
- changed task files summary;
- validation before commit;
- optional pull/push wrappers.

### Phase 8 — MCP adapter

- only after CLI/API stabilizes;
- expose core operations as MCP tools;
- no separate logic.

## 22. Recommended Tech Stack

Fast MVP stack:

```text
Language: TypeScript
Runtime: Node.js
Backend: Fastify or Hono
Frontend: React + Vite
UI: shadcn/ui or simple custom components
Tables: TanStack Table
Kanban later: dnd-kit
Storage source of truth: Markdown + YAML frontmatter
Index/cache: SQLite
SQLite library: better-sqlite3
CLI: commander, yargs, or cac
Validation: zod
Markdown/frontmatter: gray-matter or equivalent
Testing: Vitest
```

The exact choices can change, but TypeScript across CLI, backend, and frontend keeps the implementation simple.

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

> TaskPilot stores project tasks as Git-friendly Markdown/YAML files, builds a local SQLite index for fast UI queries, and exposes the same task graph to humans through a WebUI and to AI agents through CLI commands.

## 24. Key Architectural Decisions

1. Markdown/YAML files are the canonical source of truth.
2. SQLite is only a local disposable index/cache.
3. One file per item to reduce Git merge conflicts.
4. Comments are separate append-style Markdown files.
5. Reverse links are derived, not stored manually.
6. CLI is the primary AI-facing interface.
7. MCP is optional and should be added later as an adapter.
8. WebUI is local-first and should start simple.
9. The first useful view is list + item detail, not Kanban.
10. GitHub synchronization should happen through normal Git over text files, not SQLite commits.

## 25. Final Summary

TaskPilot should be a small, local, transparent issue/task system optimized for AI-assisted development.

The strongest architecture is:

```text
Git-friendly Markdown/YAML files as source of truth
+
local SQLite index/cache for fast UI
+
local WebUI for humans
+
CLI with JSON output for AI agents
+
optional MCP adapter later
```

The main value is not replacing Jira.

The main value is giving AI agents and humans a shared, inspectable, local task graph that lives close to the code and can be synchronized through GitHub without opaque databases or cloud dependencies.
