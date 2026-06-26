from __future__ import annotations

import os

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from taskpilot.server.routes import projects
from taskpilot.services.errors import NotFound, ValidationFailed

#: Environment variable carrying the registry directory for :func:`create_app_from_env`.
REGISTRY_DIR_ENV = "TASKPILOT_REGISTRY_DIR"


def create_app(*, registry_dir: str) -> FastAPI:
    app = FastAPI(
        title="TaskPilot API",
        version="0.0.0",
        docs_url="/docs",
    )

    app.state.registry_dir = registry_dir

    app.include_router(projects.router, prefix="/api")

    @app.exception_handler(NotFound)
    def _not_found(request: Request, exc: NotFound) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(ValidationFailed)
    def _validation_failed(request: Request, exc: ValidationFailed) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    return app


def create_app_from_env() -> FastAPI:
    """Build the app from the ``TASKPILOT_REGISTRY_DIR`` environment variable.

    Used as a uvicorn import-string factory (``taskpilot.server.app:create_app_from_env``)
    so adapters such as the CLI ``serve`` command can launch the server without importing
    this module directly, keeping the cli/server adapter boundary intact (TP-4).
    """
    registry_dir = os.environ.get(REGISTRY_DIR_ENV)
    if not registry_dir:
        raise RuntimeError(f"{REGISTRY_DIR_ENV} is not set; cannot build the API app")
    return create_app(registry_dir=registry_dir)
