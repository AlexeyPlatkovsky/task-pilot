# F005 REST API — Tasks

| ID | Task | Implements | Status | Depends on |
| --- | --- | --- | --- | --- |
| F005-T1 | Add `fastapi` and `uvicorn[standard]` to `pyproject.toml`; scaffold `src/taskpilot/server/__init__.py`, `app.py`, and `routes/` package with a health-check route | F005-R1 | done | — |
| F005-T2 | Implement `GET /api/projects` endpoint; serialize registered projects to `ProjectSummary` response shape | F005-R2, F005-R7 | done | F005-T1 |
| F005-T3 | Implement `GET /api/projects/{project_id}/items` endpoint; exclude deleted items; serialize to `ItemSummary` response shape | F005-R3, F005-R7, F005-R8 | done | F005-T1 |
| F005-T4 | Implement `GET /api/projects/{project_id}/items/{item_id}` endpoint; load comments; serialize to `ItemDetail` response shape | F005-R4, F005-R7, F005-R8 | done | F005-T1 |
| F005-T5 | Implement `PATCH /api/projects/{project_id}/items/{item_id}` endpoint with `ItemUpdateInput` body; call `update_item` service; return updated `ItemDetail` | F005-R5, F005-R7, F005-R8 | done | F005-T4 |
| F005-T6 | Add `taskpilot serve` Typer command with `--host`, `--port`, and `--workspace` options; start uvicorn programmatically | F005-R6 | done | F005-T1 |
| F005-T7 | Configure Vite dev proxy: add `/api` → `http://localhost:8000` proxy entry in `vite.config.ts` | F005-R9 | done | F005-T1 |
| F005-T8 | Write API integration tests using FastAPI `TestClient` covering all endpoints, 404 paths, and 422 validation errors | F005-R2, F005-R3, F005-R4, F005-R5, F005-R8 | done | F005-T2, F005-T3, F005-T4, F005-T5 |

## Notes

- T1 must land before all other server tasks; T7 (Vite proxy) can be done in parallel with T2–T5.
- The Vite proxy already targeted `http://127.0.0.1:7152` (matching the `--port` default in spec 0002); no change was needed beyond verification.
- The `TaskPaths` / workspace resolution in `taskpilot serve` should reuse the same workspace-loading logic as the CLI context (`cli/context.py`).
- Response Pydantic models should be defined in `src/taskpilot/server/schemas.py` and kept in sync with the TypeScript types in `web/src/types/index.ts`. The OpenAPI schema is the bridge.
- `uvicorn[standard]` is needed for reload support during development (`--reload` flag).
- Deleted items must be excluded from the items list endpoint (F005-R3) but remain loadable via the detail endpoint (F005-R4) for direct lookup and validation use-cases.
