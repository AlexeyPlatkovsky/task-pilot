# Idea

## Problem

AI coding agents often need a persistent task context. A normal project repository has source
code, docs, and tests, but issues may live elsewhere: Jira, GitHub Issues, Linear, Notion, or
chat history. For local AI workflows this creates problems:

- agents lose task context between sessions;
- project work is fragmented between external trackers and code;
- task state is not always available offline;
- cloud issue trackers are too heavy for small local projects;
- local CLI-first tools may be hard to inspect visually;
- binary databases are poor Git citizens;
- AI agents need structured, machine-readable data, not only human notes.

## Users

- **Local developer using AI coding agents** — wants project work stored beside source code, with
  durable, inspectable task context accessible through deterministic agent commands.
- **AI coding agent** — needs to read and write tasks through a stable, machine-readable interface
  and maintain context across sessions.
- **MCP client (future)** — should access TaskPilot through a thin adapter without separate
  business logic.
- **Reviewer** — inspects task changes through normal Git diffs.

## Value Proposition

TaskPilot gives AI agents and humans a shared, inspectable, local task graph that lives close to
the code and can be synchronized through GitHub without opaque databases or cloud dependencies.

## Scope

### In scope

- local-first task graph with workspace initialization and file-based storage;
- project support with item create/read/update and comments;
- basic typed hierarchy and graph links between items;
- validation of canonical task files with visible errors;
- local WebUI with project selector, Kanban board, and item modal editing;
- CLI commands with human-readable and JSON output for AI agents;
- Git-friendly synchronization through text files, not binary databases.

### Out of scope

- real-time collaboration;
- user accounts, permissions, roles;
- hosted cloud sync;
- custom workflow builder;
- Gantt charts, sprint planning, story points;
- rich automation engine or plugin system;
- complex notifications;
- GitHub Issues sync as the core model;
- committed binary databases as a synchronization mechanism;
- desktop shell (WebUI is browser-based only).

## Non-Goals

TaskPilot is not a Jira replacement, an enterprise issue tracker, or a real-time collaboration
tool. It does not aim to manage large teams, replace GitHub Issues, or provide hosted cloud
services.

## Principles

- Works offline by default — no account, hosted service, or cloud dependency required.
- YAML and Markdown files are canonical task data.
- Canonical files are the only persisted source of truth for task data.
- One file per item minimizes Git conflicts.
- Comments are separate append-style files.
- Reverse links are derived, not stored independently.
- Serialization and JSON contracts are deterministic.
- Invalid files remain visible and actionable.
- CLI, REST API, WebUI, and future MCP adapters share one domain/service layer.

## Success Signals

- A developer can initialize a TaskPilot workspace in an existing repository, create items
  through CLI, inspect and edit supported fields through the WebUI, and see changes persisted as
  Git-friendly YAML/Markdown files.
- An AI coding agent can list, read, and update task state through deterministic CLI commands
  with JSON output.
- Task files produce readable Git diffs when changed.
- The WebUI shows a functional Kanban board with item detail editing and visible comments.
- Deleted or corrupted task files remain visible through validation rather than silently
  disappearing.
