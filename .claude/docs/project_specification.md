# TaskPilot Project Specification

## Profile Status

- Profiled from repository evidence on 2026-06-20.
- This document records project context and working expectations; it does not replace accepted
  feature specifications or architecture decisions.
- External best-practice research was not used.

## Project Purpose

TaskPilot is a local-first task graph for AI-assisted software development. It gives humans and AI
coding agents a shared, persistent, inspectable representation of project work close to the source
code.

The product is intended to:

- store epics, features, tasks, bugs, comments, status, and graph relationships in Git-friendly
  Markdown/YAML files;
- work fully offline without accounts, cloud services, or a remote database;
- provide a local WebUI for human use;
- provide a deterministic CLI, including JSON output, for AI agents and automation;
- expose all adapters through one domain/service layer;
- optionally add a thin MCP adapter after the CLI and service contracts stabilize.

TaskPilot is not intended to begin as an enterprise issue tracker. Early versions deliberately
exclude hosted collaboration, accounts and permissions, complex workflow configuration, sprint
planning, rich automation, plugins, and opaque synchronization.

## User Role

The user is the product owner and main executor for TaskPilot.

The role combines:

- product ownership and scope decisions;
- requirements definition and acceptance;
- architecture and technical design;
- primary software implementation;
- test design, execution, and QA;
- code review and regression assessment;
- documentation maintenance.

The user is the final authority for product behavior, public contracts, persistence choices,
architecture changes, production dependencies, and release scope.

## Recurring Duties

The instruction system should support these recurring work areas:

1. Convert product concepts into implementation-ready specifications and acceptance criteria.
2. Identify the smallest vertical slice that produces observable user value.
3. Implement domain, storage, CLI, REST API, and WebUI changes without duplicating business rules.
4. Design and implement unit, integration, contract, CLI, API, and browser tests as appropriate.
5. Validate formatting, types, tests, builds, file compatibility, and user-facing behavior.
6. Review diffs independently for correctness, regression risk, data loss, and contract drift.
7. Investigate defects across canonical files, parsing, services, adapters, and UI boundaries.
8. Keep concept, specifications, architecture decisions, commands, and operational documentation
   synchronized with implemented facts.
9. Evaluate UI flows for a simple local product, especially project selection, list/detail,
   comments, validation errors, and later graph-oriented views.
10. Maintain narrow changes and preserve unrelated work in a repository commonly edited by agents.

Release, packaging, deployment, and external research support are secondary duties that become
active only when the corresponding product phase requires them.

## Delivery Approach

TaskPilot uses specification-driven development for non-trivial behavior, public contracts,
persistence, cross-layer changes, and architecture.

The preferred workflow is:

1. Discover relevant concepts, specifications, decisions, code, tests, and constraints.
2. Create or update an accepted specification under `docs/specs/`.
3. Define observable acceptance criteria and required test levels.
4. Plan the smallest vertical implementation slice.
5. Implement through the shared domain/service architecture.
6. Run the smallest sufficient validation matrix, including failure paths.
7. Review the final diff independently.
8. Update documentation and decisions when facts or contracts changed.

Small, local, low-risk fixes may proceed without a new specification when expected behavior is
already explicit. That classification must be stated.

## AI Tool Mode and Tool Surface

The project uses a multi-tool, AI-agnostic instruction model.

Tools currently evidenced:

- Codex, used in the active repository workflow;
- Claude Code, configured through `.claude/CLAUDE.md` as a thin adapter to `AGENTS.md`;
- shell and Git tooling available to coding agents for local inspection and validation.

The canonical tool-independent entry point is `AGENTS.md`. Tool-specific adapters must remain thin
and must not create competing policy.

AI-facing product interfaces planned for TaskPilot:

- CLI as the primary stable agent interface;
- deterministic JSON output for read operations and automation;
- REST API through the same service layer;
- optional MCP support later as a thin adapter, not a separate implementation.

## Known Capability Triggers

| Trigger | Required capability |
| --- | --- |
| Non-trivial behavior, contract, persistence, cross-layer, or architecture work | Specification and acceptance criteria |
| Approved production change | Implementation against the accepted specification |
| New or changed behavior | Test design and implementation at the lowest sufficient level |
| User-facing WebUI work | UI-change pipeline, maintained design book, browser-level verification, and isolated design review |
| Read-only assessment or independent regression pass | Findings-first code review |
| Claimed completion of a non-trivial change | Evidence-based final validation and final diff inspection |
| Changed behavior, commands, architecture, domain facts, or known failure modes | Documentation synchronization |
| Runtime instruction-system creation or material change | Instruction maintenance, isolated instruction evaluation, scenario acceptance, and validation |
| Isolated implementation or independent judgment is materially useful | Specialized project agent |

All runtime AI capabilities are authoritative under `.claude/skills/`, `.claude/pipelines/`,
`.claude/agents/`, and `.claude/conventions/`. `AGENTS.md` is the sole root contract outside
`.claude/`. Tool-specific configuration must not create competing procedures. The responsibility
boundaries in `AGENTS.md` remain authoritative.

The routing manager is packaged as `.claude/skills/manager/SKILL.md` for Claude discovery and
startup import. It remains a manager-equivalent routing artifact, not an execution skill.

## Domain Vocabulary

| Term | Meaning |
| --- | --- |
| Workspace | A local TaskPilot data root containing configuration and one or more projects. |
| Project | A named task collection with a readable key/prefix such as `VP`. |
| Item | A canonical work record stored as one Markdown/YAML file. |
| Item type | An initial category such as epic, feature, task, or bug. |
| Status | A workflow state; initially backlog, next, ready, in progress, done, or cancelled. |
| Link | A graph relationship between items, stored canonically in one direction. |
| Reverse link | A derived inverse relationship, never independently maintained as source data. |
| Parent/child | A hierarchy expressed through links rather than rigid type rules. |
| Blocker | An item that prevents another item from progressing. |
| Comment | A separate append-style Markdown file associated with an item. |
| Canonical files | Human-readable Markdown/YAML task data that forms the source of truth. |
| Index/cache | Disposable SQLite data rebuilt from canonical files; never authoritative. |
| Adapter | CLI, REST API, WebUI-facing API handler, or future MCP surface translating to the shared service layer. |
| Validation error | A visible, actionable problem in canonical project or item data; invalid files must not disappear silently. |

## Product and Architecture Invariants

- TaskPilot must work offline and remain local-first by default.
- Markdown/YAML files are canonical task data.
- SQLite, when introduced, is disposable index/cache data and contains no unique information.
- Writers update canonical files first and refresh indexes afterward.
- One file per item and separate append-style comment files reduce Git conflicts.
- Reverse relationships are derived rather than stored twice.
- Business rules live in the domain/service layer.
- CLI, REST API, WebUI, and future MCP adapters use the same domain/service operations.
- Filesystem and SQLite implementation details do not leak into the domain model.
- Serialization and JSON contracts are deterministic and stable.
- Invalid files and validation failures remain visible and actionable.
- Important operations remain inspectable through files, CLI output, UI state, or logs.
- The product avoids cloud dependencies, mandatory accounts, hidden synchronization, and
  speculative enterprise scope.
- Direct file reading is preferred until measured needs justify SQLite indexing complexity.

## Authoritative Local Sources

Authority follows this order:

1. User instructions in the active conversation.
2. `AGENTS.md` for repository-wide agent behavior and quality gates.
3. Accepted specifications under `docs/specs/`.
4. `docs/taskpilot_concept.md` for the product concept, goals, boundaries, and provisional direction.
5. Architecture decisions under `docs/decisions/`.
6. Existing code, tests, and established project conventions.

Additional framework sources under `.claude/manifesto/` govern construction of the AI instruction
system, not TaskPilot product behavior.

Conflicts that affect product behavior, public contracts, persistence, or architecture must be
reported rather than silently resolved.

## Quality Expectations

- Map every non-trivial change to explicit, independently testable acceptance criteria.
- Test at the lowest level that proves behavior, then test boundaries that cross adapters,
  processes, storage, or the browser.
- Cover failure paths, invalid files, deterministic output, and relevant Windows/macOS/Linux path
  behavior.
- Preserve strong assertions; do not delete tests, weaken checks, or broadly update snapshots to
  force a pass.
- Run relevant formatting, type checking, tests, build, CLI, API, and UI checks available in the
  repository.
- Report skipped or blocked checks and their residual risk.
- Lead code review reports with findings.
- Inspect the final diff before claiming completion.
- Preserve unrelated user changes and keep diffs narrow.
- Do not commit, push, rewrite history, discard changes, or run destructive operations without
  explicit user authorization.

## Preferred Product Delivery Sequence

Current concept evidence supports this progression:

1. Canonical workspace/project/item files, deterministic parsing/writing, and validation.
2. Shared domain/service operations for projects, items, comments, and links.
3. Stable CLI commands with human-readable and JSON output.
4. Local REST API and WebUI with project selection, item list/detail, editing, and comments.
5. SQLite index/cache only when direct file access shows a measured need.
6. Kanban, tree, advanced filters, and relation visualization.
7. Transparent Git helpers.
8. Optional MCP adapter after core contracts stabilize.

Each phase is directional, not an accepted implementation specification. Work begins from the
smallest accepted vertical slice rather than implementing an entire phase at once.

## Accepted Assumptions

- The user is currently the sole or primary product decision-maker, developer, reviewer, and QA
  executor.
- The project will optimize first for a single local developer using AI coding agents.
- Git is the expected synchronization and review mechanism for canonical task files.
- TypeScript, Node.js, a lightweight REST backend, React/Vite, Vitest, and related libraries are
  candidates from the concept document, not yet binding production dependencies.
- Fixed initial item types and statuses are acceptable for early versions, subject to an accepted
  specification.
- Git history plus timestamps and comments is sufficient for the initial audit model; event
  sourcing is deferred.
- Desktop packaging, hosted operation, and real-time collaboration are deferred.
- External best-practice research is not required for this profile and must not override local
  authority if used later.

## Rejected or Deferred Assumptions

- SQLite is not assumed to be required for the first usable release.
- MCP is not assumed to be required for v0.1.
- The concept document's example file schema, commands, API shape, and library list are not treated
  as finalized contracts.
- TaskPilot is not assumed to manage Git invisibly or automatically.
- Enterprise workflow, permissions, accounts, hosted sync, plugins, notifications, and advanced
  planning features are outside the early product scope.

## Open Profile Gaps

These details remain deliberately unresolved until a specification or architecture decision needs
them:

- the exact first vertical slice and v0.1 acceptance boundary;
- final package manager, monorepo/package layout, backend framework, CLI library, UI component
  system, and SQLite library;
- exact canonical workspace, project, item, link, and comment schemas;
- timestamp, identifier allocation, locking, concurrent write, and atomic update rules;
- finalized CLI exit codes and JSON contracts;
- finalized REST API contracts and UI interaction states;
- indexing threshold and file-watching strategy;
- packaging and release process;
- supported Node.js versions and explicit browser support;
- licensing and contribution workflow beyond the existing repository license.

These gaps do not block later instruction-system stages. They must be resolved through SDD when
they become relevant to product behavior or implementation.
