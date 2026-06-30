# Roadmap

## Release Levels

- **✅ Alpha**: MVP used to validate the concept. Core workflow works end-to-end.
- **⏳ Beta**: Product-ready and releasable. Feature-complete with polished UX.
- **⏳ Release**: All or almost all initial features implemented with documentation and tests.

## Next Release Roadmap

Goal: polish the advanced WebUI views enough for daily use, then make the first release
repeatable through an npm-distributed CLI package.

Prerequisites and gaps:
- The Board date filter contract is `updated_at` time range parity with List view, using `Any time`,
  `Last 7 days`, `Last 14 days`, and `Last 30 days`. `created_at` filtering is out of scope for
  this release unless a later spec adds it.
- The Tree view item below is discovery first. Tree implementation is not ready to start until the
  interaction contract, metadata, invalid-parent behavior, and expansion persistence decisions are
  documented.
- The release package target is the unscoped npm CLI package `taskpilot`. The current WebUI package
  is private and named `web`, so release work must create clean npm package metadata/staging rather
  than publishing the current `web/package.json` package as-is.
- The npm package bundles Python source and built WebUI assets. It requires user Python `>=3.11`
  with `venv` and `pip`, then lazily creates a user-cache runtime from a bundled
  `requirements.lock`.
- The current GitHub workflow is pull-request CI only. Release automation needs two-stage publish:
  dry-run first, then manual approval before real npm publish.

### 1. Board Filter Bar

Add a Board view filter bar that matches the List view filter bar sizing, spacing, dropdown
behavior, and visual style.

Scope:
- filters: type, updated time range, priority;
- updated time range follows the List view `updated_at` model: `Any time`, `Last 7 days`,
  `Last 14 days`, and `Last 30 days`;
- Clear resets all Board filters to their defaults and restores every board card;
- filtered empty columns remain visible and stable.

Acceptance:
- Board filters use the same shared dropdown selector pattern as List filters.
- Filtering by type and priority hides non-matching cards without changing item status or order.
- Filtering by updated time range uses the same local, deterministic reference-time behavior as
  List filters.
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

Implementation gate:
- Do not implement Tree view changes until discovery is accepted.
- After discovery, create a separate implementation slice with explicit acceptance criteria for
  node rendering, keyboard interaction, invalid hierarchy states, view-switch behavior, and browser
  layout evidence.

### 4. Release Automation

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
- publish only after npm dry-run succeeds and a maintainer manually approves real publish.

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
- After the manual approval flow is proven, should a future release trigger use tag push, GitHub
  Release creation, or another explicit release command?

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
