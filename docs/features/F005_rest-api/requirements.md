# F005 REST API — Requirements

## Summary

Implement a local FastAPI HTTP server that exposes domain operations over a REST API so the
WebUI can read and update task data without direct filesystem access. The server delegates all
business logic to the existing domain service layer; it owns only HTTP routing, request
validation, and response serialization. JSON contracts are deterministic and match the
TypeScript types already defined in the WebUI client.

## Serves

- `roadmap.md` Phase 4 — Local WebUI (Backend REST API)
- `architecture.md` — REST API server component (`src/taskpilot/server/`)

## Functional Requirements

| ID | Requirement | Priority |
| --- | --- | --- |
| F005-R1 | The system shall provide a FastAPI application scaffolded at `src/taskpilot/server/` with a router structure and OpenAPI docs served at `/docs` | must |
| F005-R2 | The server shall expose `GET /api/projects` returning all registered projects with `id`, `key`, `name`, and `active` fields | must |
| F005-R3 | The server shall expose `GET /api/projects/{project_id}/items` returning all non-deleted items for the project as summaries (`id`, `title`, `type`, `status`, `priority`, `valid`, `findings`) | must |
| F005-R4 | The server shall expose `GET /api/projects/{project_id}/items/{item_id}` returning full item detail including all fields and the comment thread | must |
| F005-R5 | The server shall expose `PATCH /api/projects/{project_id}/items/{item_id}` accepting partial updates for `title`, `description`, `priority`, and `status`, returning the updated item detail | must |
| F005-R6 | The system shall provide a `taskpilot serve` CLI command that starts the FastAPI server, accepting `--host`, `--port`, and `--workspace` options | must |
| F005-R7 | All API responses shall use deterministic JSON serialization matching the TypeScript type contracts in `web/src/types/index.ts` | must |
| F005-R8 | All error responses shall return `{"detail": "<message>"}` with appropriate HTTP status codes: 404 for unknown project or item, 422 for invalid input, 500 for unexpected errors | must |
| F005-R9 | The Vite dev server shall be configured to proxy `/api` requests to the FastAPI server so the frontend can be developed against the real server | should |

## Acceptance Criteria

- **F005-R1:** Starting the server and navigating to `http://localhost:8000/docs` returns an OpenAPI UI with all defined routes listed.
- **F005-R2:** `GET /api/projects` returns a JSON array; each element has `id`, `key`, `name`, and `active`. When no projects are registered, the response is `[]`.
- **F005-R3:** `GET /api/projects/{project_id}/items` for an existing project returns a JSON array of item summaries. Items with `status: deleted` are not included.
- **F005-R4:** `GET /api/projects/{project_id}/items/{item_id}` for an existing item returns all fields defined in `ItemDetail` (TypeScript), including `comments` as a list.
- **F005-R5:** `PATCH /api/projects/{project_id}/items/{item_id}` with `{"status": "in_progress"}` updates the item file and returns the updated `ItemDetail`. Sending an unknown status field returns HTTP 422.
- **F005-R6:** Running `taskpilot serve` starts the server. `taskpilot serve --port 9000` binds to port 9000. Ctrl-C stops it cleanly.
- **F005-R7:** The same item serialized via `GET /api/.../items/{id}` twice produces identical JSON.
- **F005-R8:** `GET /api/projects/unknown-project/items` returns HTTP 404 with `{"detail": "Project not found: unknown-project"}`. Sending `{"status": "invalid"}` to PATCH returns HTTP 422.
- **F005-R9:** Running `npm run dev` in `web/` and starting `taskpilot serve` allows the frontend to call `/api/projects` without CORS errors in the browser.

## Constraints

- The server calls domain services directly — no reimplementation of validation or write rules.
- Canonical files are written before any response is returned.
- The server does not add SQLite or any persistence layer beyond what the domain layer already uses.
- JSON field order matches the canonical model field order for determinism.
- FastAPI and uvicorn are added as production dependencies in `pyproject.toml`.
- The `taskpilot serve` command is a Typer subcommand consistent with existing CLI structure.

## Out of Scope

- Authentication or authorization (local-only tool).
- WebSocket or real-time push updates.
- Serving the built WebUI static files (deferred; dev proxy covers Alpha).
- `POST /api/projects/{project_id}/items` — item creation via API (CLI-only for Alpha).
- `POST /api/projects/{project_id}/items/{item_id}/comments` — comment creation via API (CLI-only for Alpha).
- `DELETE /api/projects/{project_id}/items/{item_id}` — hard delete (soft-delete via PATCH status is sufficient).
- Rate limiting, pagination, or query parameter filtering (F006).
- HTTPS / TLS termination.
