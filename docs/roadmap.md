# Roadmap

## Release Levels

- **✅ Alpha**: MVP used to validate the concept. Core workflow works end-to-end.
- **⏳ Beta**: Product-ready and releasable. Feature-complete with polished UX.
- **⏳ Release**: All or almost all initial features implemented with documentation and tests.

## Next Release Roadmap

Goal: polish the advanced WebUI views enough for daily use, then make releases repeatable through
an automated npm publishing workflow.

### 1. Board Filter Bar

Add a Board view filter bar that matches the List view filter bar sizing, spacing, dropdown
behavior, and visual style.

Scope:
- filters: type, date, priority;
- date filter follows the List view time-range model unless a future spec defines a separate board
  date contract;
- Clear resets all Board filters to their defaults and restores every board card;
- filtered empty columns remain visible and stable.

Acceptance:
- Board filters use the same shared dropdown selector pattern as List filters.
- Filtering by type and priority hides non-matching cards without changing item status or order.
- Filtering by date uses the same local, deterministic reference-time behavior as List filters.
- Component, functional E2E, and browser-contract coverage prove option coverage, reset behavior,
  filtered-empty state, and layout consistency with List filters.

### 2. Validation Success Contrast

Lighten the `All items valid` success message so it reads as a success state instead of near-black
text in the active theme.

Scope:
- adjust only the success status color/token usage unless inspection finds a shared token defect;
- preserve WCAG AA contrast and existing validation error states.

Acceptance:
- `All items valid` is visibly lighter than body text while remaining readable.
- Browser-contract evidence covers the computed color in the active theme.
- Component coverage confirms the valid and invalid validation states still render correctly.

### 3. Tree View Refinement Discovery

Refine the Tree view only after a short discovery pass. The current route is to inspect real usage
and define the exact interaction contract before implementation.

Discovery questions:
- Should Tree filters match Board/List filters, or stay hierarchy-only?
- What node metadata should be visible by default: type, priority, status, parent, child count, or
  validation state?
- Should expansion state persist across view switches during the session?
- How should orphaned items, cycles, and invalid parent references be surfaced?

Acceptance for discovery:
- Document the chosen Tree interaction contract in `docs/design.md` or a feature spec.
- Map the contract to component, functional E2E, and browser-contract coverage before production
  code changes.
- Keep Tree view derived from `parent_id`; do not introduce stored reverse links.

### 4. Automated Release Pipeline

Create a repeatable release workflow with version bumping and npm publishing after the UI polish
items are accepted.

Scope:
- define package ownership and publish target before enabling npm release;
- add a version bump command or workflow step with deterministic changelog/release notes;
- run tests, lint, build, and relevant browser checks before publish;
- publish only from an intentional release trigger, not from every push.

Acceptance:
- The release workflow fails before publish if validation, tests, lint, build, or package metadata
  checks fail.
- Version bump and npm publish steps are auditable in CI logs.
- Dry-run evidence is captured before the first real npm publication.
- Release documentation explains credentials, trigger path, rollback expectations, and local
  verification.

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

### ✅ Phase 1 — File model and parser

Define workspace folder layout. Implement parser for item YAML files and comment Markdown files.
Implement writer with deterministic formatting. Implement validation. Add basic tests.

Serves: [F001: Task File Storage](features/F001_task-file-storage/)

### ✅ Phase 2 — Domain/service layer

Project operations, item operations, comment operations, link operations, validation rules.
No UI yet.

Serves: [F002: Domain Services](features/F002_domain-services/)

### ✅ Phase 3 — CLI

`init`, project list, item list/show/create/update, comments, JSON output, validation
command.

Serves: [F003: CLI Interface](features/F003_cli-interface/)

### ✅ Phase 4 — Local WebUI

Backend REST API, React app, project selector, Kanban board, item detail modal, read-only comments.

Serves: [F004: WebUI Workspace](features/F004_webui-workspace/)
Serves: [F005: REST API](features/F005_rest-api/)

### ⏳ Phase 5 — Better views

Tree view, filters, sorting, and relation display.

Serves: [F006: Advanced Views](features/F006_advanced-views/)

### ⏳ Phase 6 — Git helpers

Sync status, changed task files summary, validation before commit, optional pull/push wrappers.

Serves: [F007: Git Helpers](features/F007_git-helpers/)

### ⏳ Phase 7 — MCP adapter

Expose core operations as MCP tools. No separate logic. Only after CLI/API stabilizes.

Serves: [F008: MCP Adapter](features/F008_mcp-adapter/)

## Recommended First Usable Slice

```text
Local WebUI + project selector + item list + item detail + read-only comments + file storage
```

Then: CLI + validation + links

Then: Kanban drag-and-drop + tree view + Git sync helpers

Then: MCP adapter
