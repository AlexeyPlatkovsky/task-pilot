"""``taskpilot serve`` — start the local WebUI/API server (task F005-T6, requirement F005-R6).

Resolves the machine registry, then runs the FastAPI application via uvicorn.
The server binds to ``127.0.0.1`` on port ``7152`` by default, matching the
Vite dev proxy target in ``web/vite.config.ts``.
"""

from __future__ import annotations

import os
from pathlib import Path

import typer
import uvicorn

from taskpilot.cli.exit_codes import EXIT_USER_ERROR
from taskpilot.core.layout import WorkspacePaths
from taskpilot.services.registry import default_registry_dir

#: Import-string for uvicorn's app factory. Passing a string (not an imported symbol)
#: keeps the CLI adapter from importing the server adapter directly (TP-4).
_APP_FACTORY = "taskpilot.server.app:create_app_from_env"
_REGISTRY_DIR_ENV = "TASKPILOT_REGISTRY_DIR"

__all__ = ["register"]


def _validate_workspace(ws: WorkspacePaths) -> bool:
    """Return True only when both the workspace dir and project.yaml exist."""
    return ws.exists() and ws.project_file.is_file()


def serve_command(
    host: str = typer.Option("127.0.0.1", "--host", help="Host interface to bind."),
    port: int = typer.Option(7152, "--port", help="Port to listen on."),
    workspace: str | None = typer.Option(
        None,
        "--workspace",
        help="Validate this workspace root before startup.",
    ),
) -> None:
    """Start the local WebUI/API server."""
    if workspace is not None:
        ws = WorkspacePaths.for_root(Path(workspace))
        if not _validate_workspace(ws):
            typer.echo(
                f"Error: no initialized TaskPilot workspace at {ws.root} "
                f"(missing .taskpilot/ or project.yaml)",
                err=True,
            )
            raise typer.Exit(EXIT_USER_ERROR)

    registry_dir = default_registry_dir()
    os.environ[_REGISTRY_DIR_ENV] = str(registry_dir)

    typer.echo(f"TaskPilot server starting on http://{host}:{port}")
    typer.echo(f"OpenAPI docs at http://{host}:{port}/docs")
    uvicorn.run(_APP_FACTORY, factory=True, host=host, port=port)


def register(app: typer.Typer) -> None:
    """Attach the ``serve`` command to ``app``."""
    app.command("serve")(serve_command)
