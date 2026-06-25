from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from taskpilot.server.routes import projects
from taskpilot.services.errors import NotFound, ValidationFailed


def create_app(*, workspace: str, registry_dir: str) -> FastAPI:
    app = FastAPI(
        title="TaskPilot API",
        version="0.0.0",
        docs_url="/docs",
    )

    app.state.workspace = workspace
    app.state.registry_dir = registry_dir

    app.include_router(projects.router, prefix="/api")

    @app.exception_handler(NotFound)
    def _not_found(request: Request, exc: NotFound) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(ValidationFailed)
    def _validation_failed(request: Request, exc: ValidationFailed) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    return app
