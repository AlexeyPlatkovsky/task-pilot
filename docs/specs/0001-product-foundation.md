# 0001: Product Foundation

## Status

draft

## Outcome

TaskPilot provides a local-first task graph for AI-assisted software development. It stores
canonical task data in human-readable YAML and Markdown files, exposes deterministic operations for AI
agents, and gives humans a local UI for inspecting and editing the same work graph.

Once accepted, this specification establishes the initial product contract that later feature
specifications must preserve unless they explicitly revise it.

## Scope

In scope:

- local system registry, project root, and project concepts;
- canonical file ownership and source-of-truth rules;
- initial item, comment, status, and link expectations;
- adapter boundaries for CLI, REST API, WebUI, and future MCP support;
- validation and invalid-file visibility requirements;
- early product sequencing and Alpha/Beta/Release acceptance direction.

Out of scope:

- exact file schema and serialization grammar;
- exact CLI commands, flags, exit codes, and JSON schemas;
- exact REST API routes and response contracts;
- UI layout, component system, and interaction details;
- SQLite schema, indexing strategy, and file-watcher design;
- packaging, release, and distribution mechanics.

Those details require follow-up accepted specifications before implementation.

## Users

Primary users:

- a local developer who wants project work stored beside source code;
- AI coding agents that need durable, inspectable task context through deterministic commands.

Secondary users:

- future MCP clients that should access TaskPilot through a thin adapter;
- reviewers who inspect task changes through normal Git diffs.

## Product Principles

- TaskPilot works offline by default.
- No account, hosted service, or cloud dependency is required for core use.
- YAML and Markdown files are the canonical task data.
- SQLite, if introduced, is disposable index/cache data and never the source of truth.
- Canonical files are written before any index refresh.
- One file per item minimizes Git conflicts.
- Comments are separate append-style files.
- Reverse links are derived, not stored independently.
- Serialization and JSON contracts are deterministic.
- Invalid files remain visible and actionable.
- CLI, REST API, WebUI, and future MCP adapters share one domain/service layer.

## Product Model

### System Registry

The local system registry is machine-specific TaskPilot state. It stores known project roots,
active/inactive project flags, cache/index state, and local preferences. It is not canonical product
data and must not be required for another user to understand a project's tasks after cloning that
project repository.

The system registry belongs in an operating-system app data location, not in a project repository.

### Project Root

A project root is a repository root containing canonical TaskPilot files for exactly one TaskPilot
project. A project repository owns its task files and commits them through that repository's Git
history.

The concrete folder layout remains provisional until a storage-format specification is accepted.
The current direction is a repository-local `.taskpilot/` directory.

### Project

A project is a named task collection with a readable key or prefix, such as `TP`. One repository
contains one TaskPilot project.

Projects should support, at minimum:

- stable identity;
- display name;
- readable key/prefix;
- optional description.

### Item

An item is a canonical work record stored as one YAML file.

Initial item types should include:

- epic;
- feature;
- task;
- bug.

Alpha workflow statuses should include:

- backlog;
- ready;
- in_progress;
- done;
- cancelled.

The `deleted` status is a reserved system status. It is stored as a regular item status, but it is
not a normal workflow column and cannot be renamed or removed when project-configured statuses are
introduced.

Items should support both typed hierarchy and non-hierarchy graph relationships. A follow-up
storage/model specification owns the exact field schema and validation rules.

### Comment

A comment is human-readable Markdown associated with an item. Comments are stored separately from
item files to reduce conflicts from multiple users or agents adding discussion to the same item.

### Link

A link is a graph relationship between two items. Canonical storage should record only one
direction when an inverse can be derived.

Examples:

- `blocks` derives `blocked by`;
- `parent_id` derives child relationships.

The exact link vocabulary and storage form require a follow-up item/link model specification.

## Architecture Effects

All product surfaces must use this boundary:

```text
canonical task files
  -> parser / validator
  -> domain model and services
  -> CLI | REST API | future MCP
  -> WebUI through REST API
```

Adapters translate inputs and outputs. They must not own business rules.

Filesystem and SQLite details must not leak into the domain model. If an index/cache is introduced,
it must be rebuildable from canonical files and contain no unique source-of-truth data.

## Initial Product Sequence

The preferred delivery sequence is:

1. Canonical project, item, and comment files, deterministic parsing/writing, and validation.
2. Shared domain/service operations for projects, items, comments, and links.
3. Stable CLI commands with human-readable and JSON output.
4. Local REST API and WebUI with project selection, Kanban board, item modal editing, and comments.
5. SQLite index/cache only when direct file access shows a measured need.
6. Kanban, tree, advanced filters, and relation visualization.
7. Transparent Git helpers.
8. Optional MCP adapter after core contracts stabilize.

## Acceptance Criteria

This product foundation is acceptable when:

- it preserves the local-first, file-canonical, Git-friendly product direction;
- it defines the initial system registry, project root, project, item, comment, and link vocabulary;
- it identifies which details remain unresolved and require follow-up specs;
- it keeps SQLite, MCP, hosted sync, accounts, and enterprise workflow outside the first product
  contract;
- it aligns with `docs/taskpilot_concept.md` without promoting provisional examples into final
  API or storage contracts;
- `docs/specs/README.md` links to this specification.

## Test and Validation Strategy

Documentation validation:

- inspect the final diff;
- verify relative links resolve;
- check consistency against `AGENTS.md`, `.claude/docs/project_specification.md`, and
  `docs/taskpilot_concept.md`;
- confirm unresolved contracts are explicitly marked as future specification work.

Implementation validation for later feature specs should cover:

- deterministic parsing and serialization;
- invalid file visibility;
- cross-platform path behavior;
- CLI JSON determinism;
- shared service behavior across adapters;
- source-of-truth ordering, with canonical files written before index refresh.

## Risks

- The spec may be too broad if later work treats it as an implementation-ready storage or API
  contract.
- Deferring exact schemas may delay implementation until the next specification is accepted.
- The initial type/status/link vocabulary may need revision after the first vertical slice.

## Assumptions

- The first useful release targets one local developer using AI coding agents.
- Git is the expected synchronization and review mechanism for canonical task files.
- Direct file access is acceptable until a measured need justifies SQLite indexing.
- CLI is the primary stable AI-facing interface.
- MCP is useful later, but not required for Alpha.

## Open Questions

- What exact project and item YAML serialization rules should canonical files use?
- What are the finalized project file fields?
- How should ID collisions be repaired across branches and concurrent agents?
- What timestamp format, timezone policy, and deterministic ordering rules are required?
- What are the first CLI commands, exit codes, and JSON schemas?
- What validation errors are warnings versus hard write blockers?
- What is the smallest accepted vertical slice after this product foundation?
