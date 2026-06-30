from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from taskpilot.server.routes import projects
from taskpilot.services.errors import NotFound, ValidationFailed

#: Environment variable carrying the registry directory for :func:`create_app_from_env`.
REGISTRY_DIR_ENV = "TASKPILOT_REGISTRY_DIR"

#: Environment variable pointing to the staged WebUI production assets directory.
WEB_DIST_ENV = "TASKPILOT_WEB_DIST"


def create_app(*, registry_dir: str) -> FastAPI:
    app = FastAPI(
        title="TaskPilot API",
        version="0.0.0",
        docs_url="/docs",
    )

    app.state.registry_dir = registry_dir

    app.include_router(projects.router, prefix="/api")

    _mount_webui(app)

    @app.exception_handler(NotFound)
    def _not_found(request: Request, exc: NotFound) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(ValidationFailed)
    def _validation_failed(request: Request, exc: ValidationFailed) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    return app


def _mount_webui(app: FastAPI) -> None:
    """Mount the WebUI static files from ``TASKPILOT_WEB_DIST`` if available.

    When the directory exists and contains ``index.html`` the app serves:
    - static assets under ``/assets/``
    - ``index.html`` as the SPA fallback for all non-API routes

    When the directory is missing or unreadable the WebUI route returns
    a clear packaging error instead of a blank page.
    """
    web_dist = os.environ.get(WEB_DIST_ENV)
    if not web_dist:
        return

    web_dist_path = Path(web_dist)

    if web_dist_path.is_dir() and (web_dist_path / "index.html").is_file():
        # Mount static assets (JS, CSS, SVGs, etc.)
        app.mount("/assets", StaticFiles(directory=str(web_dist_path / "assets")), name="webui_assets")

        # SPA fallback: serve index.html for all non-API routes
        index_path = web_dist_path / "index.html"

        @app.get("/{full_path:path}", include_in_schema=False)
        async def _spa_fallback(request: Request, full_path: str) -> FileResponse:
            return FileResponse(index_path)

        @app.get("/", include_in_schema=False)
        async def _root_fallback(request: Request) -> FileResponse:
            return FileResponse(index_path)
    else:
        # WebUI assets are missing or unreadable — show a clear error
        error_body = _PACKAGING_ERROR_HTML

        @app.get("/{full_path:path}", include_in_schema=False)
        async def _packaging_error(request: Request, full_path: str) -> HTMLResponse:
            return HTMLResponse(content=error_body, status_code=503)

        @app.get("/", include_in_schema=False)
        async def _root_packaging_error(request: Request) -> HTMLResponse:
            return HTMLResponse(content=error_body, status_code=503)


_PACKAGING_ERROR_HTML = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>TaskPilot — WebUI unavailable</title>
<style>
  body { font-family: system-ui, sans-serif; max-width: 600px; margin: 80px auto; padding: 0 20px; color: #333; }
  h1 { font-size: 1.4rem; }
  code { background: #f0f0f0; padding: 2px 6px; border-radius: 4px; }
</style>
</head>
<body>
<h1>WebUI assets are not available</h1>
<p>
  The TaskPilot API is running, but the packaged WebUI assets could not be found.
  This can happen when the npm package was built without WebUI assets, or
  the <code>TASKPILOT_WEB_DIST</code> environment variable points to a missing
  or unreadable directory.
</p>
<p>
  To fix this, reinstall the TaskPilot npm package or set
  <code>TASKPILOT_WEB_DIST</code> to a directory containing a production
  WebUI build.
</p>
<p>
  The REST API is still available at <a href="/docs">/docs</a>.
</p>
</body>
</html>
"""


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
