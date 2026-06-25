from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI

from taskpilot.server.routes import projects


def create_app(*, workspace: str, registry_dir: str) -> FastAPI:
    app = FastAPI(
        title="TaskPilot API",
        version="0.0.0",
        docs_url="/docs",
    )

    app.state.workspace = workspace
    app.state.registry_dir = registry_dir

    app.include_router(projects.router, prefix="/api")

    return app
