# ADR-006: System Registry in the CLI Adapter for Alpha

- **Status:** superseded — planned migration executed in F005 (see Amendment below)
- **Date:** 2026-06-25
- **Deciders:** TaskPilot project

## Context

Spec `0002` ("Repository and Registry Model") defines a local **system registry**:
machine-specific state in the OS application-data directory that lists every
registered project root with an `active` flag and cached `key`/`name`. `taskpilot
init` adds or enables a project there, and `taskpilot project list` reads it. The
future REST API / WebUI (F004) will also serve "active registered projects" from
this registry.

The registry was deferred by F001/F002 and first became necessary in F003 (CLI).
It is machine-local infrastructure state — not canonical product data and not a
domain rule — so it does not naturally belong to the F002 domain/service layer,
yet it is potentially shared by more than one adapter.

The placement question: build it now as a shared service-layer module (anticipating
F004), or keep it in the CLI adapter until a second consumer actually exists?

## Decision

For Alpha, the registry lives in the CLI adapter at
`src/taskpilot/cli/registry.py`. The CLI is its only consumer today. The module is
written to be **adapter-free**: pure data model (`Registry`/`RegistryEntry`),
filesystem read/write, and an OS-path resolver with a `TASKPILOT_HOME` test seam —
no Typer or CLI-specific types leak into it.

When F004 needs to serve registered projects, the module is promoted to the shared
service layer; because it carries no adapter coupling, that move is mechanical.

## Consequences

- F003 ships without waiting on F004 or speculative shared-layer design.
- The registry stays decoupled from Typer, so promotion to a service is a file move
  plus import updates, not a rewrite.
- There is a known, planned migration step in F004 — until then, only the CLI can
  read/write the registry (acceptable: no other adapter exists yet).
- The architecture boundary ("one shared service layer for all adapters") is
  temporarily relaxed for this infrastructure concern, recorded here so the
  deviation is intentional and visible.

## Alternatives Considered

- **Build the registry in the service layer now** — rejected for Alpha: it would
  design a shared seam against a single consumer and a not-yet-built second one
  (F004), risking rework when F004's real needs are known.
- **Defer the registry entirely; `project list` reads the single in-repo project**
  — rejected: it contradicts the spec wording for `init` (register) and `project
  list` (list registry entries) and the multi-project WebUI model.

## Amendment — F005 (2026-06-25)

The REST API server (`feat/f005-rest-api`) became the second consumer of the registry,
triggering the planned migration. The registry was promoted to the shared service layer
during F005 code-review remediation:

- **Old path:** `src/taskpilot/cli/registry.py`
- **New path:** `src/taskpilot/services/registry.py`

Import sites updated: `cli/commands/init.py`, `cli/commands/project.py`,
`cli/commands/serve.py`, and all relevant test files. The module carried no adapter
coupling (as designed), making the move a mechanical file-move plus import updates.
A known adapter-to-adapter violation (`cli/commands/serve.py` importing `server.app`)
is tracked as TP-4 for future extraction.

## Amendment — TP-4 resolved (2026-06-26)

The remaining `cli/commands/serve.py` → `server.app` adapter-to-adapter import was
removed. `server/app.py` now exposes `create_app_from_env()` (reads
`TASKPILOT_REGISTRY_DIR`); the `serve` command sets that variable and launches the
server via uvicorn's import-string factory
(`uvicorn.run("taskpilot.server.app:create_app_from_env", factory=True, ...)`) instead
of importing the server module. The CLI no longer imports `taskpilot.server` at all — a
source-level guard test (`test_serve_module_does_not_import_server_adapter`) locks this
in. The architecture boundary ("one shared service layer; adapters do not import each
other") is fully restored.
