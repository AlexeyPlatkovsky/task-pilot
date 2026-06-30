# Roadmap

## Release Levels

- **✅ Alpha**: MVP used to validate the concept. Core workflow works end-to-end.
- **⏳ Beta**: Product-ready and releasable. Feature-complete with polished UX.
- **⏳ Release**: All or almost all initial features implemented with documentation and tests.

## Next Release Roadmap

Goal: make the core item-management loop release-ready, defer non-essential surfaces, and make
the first release repeatable through an npm-distributed CLI package.

Prerequisites and gaps:
- The Board and List date filter contract includes both `updated_at` and `created_at` time ranges,
  using `Any time`, `Last 7 days`, `Last 14 days`, and `Last 30 days`.
- The Tree view is implemented and F006 still records it as a visible advanced view, but it is not
  release-ready. The next release should hide it rather than spend release capacity refining a
  secondary surface.
- The WebUI currently keeps the selected project in page state only. A reload or app restart does
  not reopen the last project by default.
- The WebUI currently refreshes after its own mutations and normal query staleness. CLI/API/file
  changes made outside the current browser interaction are not guaranteed to appear without a page
  reload within a release-defined freshness window.
- The current item detail modal already exposes many fields, but the release needs a clearer task
  view hierarchy and relationship/child visibility for day-to-day item management.
- The release package target is the unscoped npm CLI package `taskpilot`. The current WebUI package
  is private and named `web`, so release work must create clean npm package metadata/staging rather
  than publishing the current `web/package.json` package as-is.
- The npm package bundles Python source and built WebUI assets. It requires user Python `>=3.11`
  with `venv` and `pip`, then lazily creates a user-cache runtime from a bundled
  `requirements.lock`.
- Beta publishing is manual from GitHub Actions. The workflow validates the release, performs an
  npm dry-run, and publishes to npm through Trusted Publishing with the `beta` dist-tag.
- Settings, Git helpers, MCP, advanced relation visualization, import/export, search, hosted sync,
  accounts, and other non-core surfaces should stay out of this release unless already required by
  the item-management path below.

### 1. Board and List Filter Readiness

Add a Board view filter bar that matches the List view filter bar sizing, spacing, dropdown
behavior, and visual style. Add created time range filtering to List so Beta date filters are
consistent across the primary release views.

Scope:
- filters: type, priority, updated time range, created time range;
- updated and created time ranges use `Any time`, `Last 7 days`, `Last 14 days`, and
  `Last 30 days`;
- Clear resets all Board filters to their defaults and restores every board card;
- List adds created time range alongside its existing filters;
- filtered empty columns remain visible and stable.

Acceptance:
- Board filters use the same shared dropdown selector pattern as List filters.
- Filtering by type and priority hides non-matching cards without changing item status or order.
- Filtering by updated and created time range uses the same local, deterministic reference-time
  behavior as List filters.
- List created time range combines correctly with existing List filters and Clear behavior.
- Component, functional E2E, and browser-contract coverage prove option coverage, reset behavior,
  filtered-empty state, and layout consistency with List filters.

### 2. Hide Tree View for Release

Trim the release UI by hiding the Tree view until its interaction contract is worth finishing.
This is a release-scope exception to F006's current visible Tree tab, not a deletion of the
underlying implementation or a permanent product decision.

Scope:
- hide the Tree tab from the main project workspace for the release;
- keep the existing Tree implementation available in code unless cleanup is explicitly routed;
- avoid adding Tree filters, metadata, expansion persistence, or invalid-hierarchy UX in this
  release;
- record Tree refinement as post-release discovery work.

Acceptance:
- The release WebUI exposes Board and List as the primary project views, with no visible Tree tab.
- Hidden Tree code does not affect Board, List, validation panel, project selection, or item detail
  behavior.
- Tests and documentation for release paths do not require users to exercise Tree view.
- Post-release notes preserve the known Tree questions: filters, metadata, invalid parents,
  expansion persistence, keyboard behavior, and hierarchy validation display.

### 3. Last Opened Project

Remember the last opened project so reloads and app restarts return the user to the same working
context by default.

Scope:
- persist the last selected project in server-side non-canonical `ui-state.yaml` under the existing
  TaskPilot system directory;
- expose local UI state through `GET /api/ui-state` and `PATCH /api/ui-state`;
- auto-select it on load when the stored registry project ID still exists and is active;
- fall back to the normal project selector when the stored project is missing, inactive, invalid,
  or unavailable;
- avoid adding a settings screen for this behavior.

Acceptance:
- Selecting a project, reloading the page, or restarting the local app opens that project by
  default.
- If the stored project is no longer available, the UI recovers to the standard no-project-selected
  state without a broken workspace.
- The persisted value is machine-local UI state and does not alter canonical task files,
  `.taskpilot/`, or `registry.yaml`.
- Component and browser-level coverage prove default selection, fallback, and no-project states.

### 4. WebUI Freshness for External Updates

Reflect task changes made outside the current browser interaction, including CLI commands and API
updates, in the WebUI without requiring a page reload.

Scope:
- poll every 5 seconds and refetch on window focus or visibility return;
- cover Board, List, selected item detail, and validation status where affected by item changes;
- preserve local-first operation and avoid hosted synchronization, accounts, or real-time
  collaboration scope;
- do not add WebSocket/SSE unless a later specification explicitly chooses push updates.

Acceptance:
- Updating an item status through CLI or REST API becomes visible in the open WebUI without a page
  reload inside the accepted freshness window.
- Board column placement, List row values, open item detail, and validation status refresh from the
  canonical files/API consistently.
- Refresh behavior does not interrupt an in-progress local edit with silent data loss.
- Tests cover external update detection for at least status changes, plus stale selected-item and
  validation refresh behavior.

### 5. Task Detail View Redesign Discovery Gate

Keep task detail redesign as a release blocker, but do not implement it until a separate discussion
defines the information architecture and editing scope.

Scope:
- discuss the detail-view information architecture before implementation;
- decide which fields are editable, read-only, or deferred;
- decide how relationship context, child items, comments, DOR/DOD, tags, timestamps, ownership
  fields, invalid items, and partial item loading should be presented;
- map the accepted detail-view contract to component, functional E2E, and browser-contract
  coverage before production code changes.

Acceptance:
- The redesign does not start until the discussion or accepted specification settles the required
  information architecture and editing scope.
- The implementation route reports a blocker if task detail redesign is attempted without that
  accepted contract.
- Existing item detail behavior remains unchanged until the redesign is explicitly routed.

### 6. Validation Success Contrast

Lighten the `All items valid` success message so it reads as a success state instead of near-black
text in the active theme.

Scope:
- add and use a `validation-success-muted` token for the success status;
- preserve WCAG AA contrast and existing validation error states.

Acceptance:
- `All items valid` is visibly lighter than body text while remaining readable.
- Browser-contract evidence covers the computed color in the active theme.
- Component coverage confirms the valid and invalid validation states still render correctly.

### 7. Release Automation

Create a repeatable npm-first release workflow after the UI polish items are accepted. The release
artifact is a global npm CLI package named `taskpilot` that wraps the bundled Python
implementation and packaged WebUI assets.

Scope:
- assemble a clean npm staging directory with package metadata, wrapper files, Python source,
  `requirements.lock`, and built WebUI assets;
- require `package.json` and `pyproject.toml` versions to match;
- require a committed `CHANGELOG.md` entry for the target version;
- support `npm install -g taskpilot` as the first install path; pnpm, yarn, and `npx` are out of
  scope for the first release;
- run the full current quality suite before publish, with full checks on macOS and CLI/WebUI asset
  smoke checks on Windows and Ubuntu;
- publish only from the manual GitHub workflow after npm dry-run succeeds.

Acceptance:
- The release workflow blocks publish if the npm package name is not `taskpilot`, if package name
  availability is unresolved, if versions mismatch, if the target changelog entry is missing, or if
  any required quality gate fails.
- First-run setup discovers Python via `TASKPILOT_PYTHON` or common commands, rejects incompatible
  Python with specific errors, and creates a user-cache runtime keyed by npm version and Python
  major/minor.
- Setup failure deletes the partial cache and reports a concise error, setup log path, last 20-50
  lines of `pip` output, and exact offline/setup instructions.
- `taskpilot --version` works without runtime setup, and `taskpilot doctor --rebuild-runtime`
  rebuilds the runtime cache before delegating to Python.
- Packaged `taskpilot serve` starts API routes even when WebUI assets are missing; the WebUI route
  shows a clear packaging error.
- Release documentation explains npm-only support, credentials, approval, setup logs, offline
  failure recovery, cache rebuild, and rollback by `npm deprecate` plus a corrected version.

Open questions after first npm release:
- Should `npx`, pnpm, or yarn become supported install paths?
- Should a future release include a managed Python runtime or vendored wheels for fully offline
  fresh installs?
- After the manual Beta flow is proven, should a future release trigger use tag push, GitHub
  Release creation, or another explicit release command, and should it promote to the `latest`
  npm dist-tag?

## Release Readiness Review

Current implementation snapshot:
- Board, List, validation panel, project selector, and item modal exist as the current WebUI
  management loop.
- List filters and sorting are ahead of Board; Board still needs parity filters.
- Tree exists but should be hidden for release because the refinement contract is unsettled.
- Item detail already displays substantial metadata, links, comments, and validation information,
  but needs a release-quality task-view redesign.
- API item updates write through the same local service layer, but the WebUI does not yet guarantee
  visible refresh after external CLI/API updates without reload.
- Release automation has requirements, tasks, and scenarios under
  `docs/features/F009_release-automation/`, but implementation is still a release blocker.
- Release UI readiness has requirements, tasks, and scenarios under
  `docs/features/F010_release-ui-readiness/`, but implementation is still a release blocker.

Release blockers:
- Board filter parity and List created time range filtering.
- Tree view hidden from the release UI.
- Last opened project persistence with safe fallback.
- WebUI refresh/freshness for external task updates.
- Task detail view redesign discussion gate before implementation.
- `All items valid` contrast correction.
- F009 npm release automation implementation and validation.
- F010 release UI readiness implementation and validation.

Explicitly skipped for this release unless already required by a blocker above:
- settings or preferences screens;
- Git helper UX beyond existing core file/CLI workflow;
- MCP adapter;
- advanced relation graph visualization;
- import/export helpers;
- full-text item search;
- hosted sync, accounts, collaboration, permissions, or cloud services;
- custom workflow builder, sprint planning, notifications, plugins, or enterprise administration.

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
