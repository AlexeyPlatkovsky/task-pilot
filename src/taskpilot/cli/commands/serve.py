"""``taskpilot serve`` — start the local REST API server (task F005-T6, requirement F005-R6).

Resolves the TaskPilot workspace and registry, then runs the FastAPI application
via uvicorn. The server binds to ``127.0.0.1`` on port ``7152`` by default,
matching the Vite dev proxy target in ``web/vite.config.ts``.
"""

from __future__ import annotations

from pathlib import Path

import typer
import uvicorn

from taskpilot.cli.exit_codes import EXIT_USER_ERROR
from taskpilot.cli.workspace import find_workspace
from taskpilot.core.layout import WorkspacePaths
# cli->server adapter import: tracked as TP-4 for future extraction to a service factory
from taskpilot.server.app import create_app
from taskpilot.services.errors import NotFound
from taskpilot.services.registry import default_registry_dir

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
        help="Workspace root path (default: auto-detect from cwd).",
    ),
) -> None:
    """Start the local REST API server."""
    if workspace is not None:
        ws = WorkspacePaths.for_root(Path(workspace))
        if not _validate_workspace(ws):
            typer.echo(
                f"Error: no initialized TaskPilot workspace at {ws.root} "
                f"(missing .taskpilot/ or project.yaml)",
                err=True,
            )
            raise typer.Exit(EXIT_USER_ERROR)
    else:
        try:
            ws = find_workspace()
        except NotFound as exc:
            typer.echo(f"Error: {exc}", err=True)
            raise typer.Exit(EXIT_USER_ERROR) from exc

    if not _validate_workspace(ws):
        typer.echo(
            f"Error: workspace at {ws.root} is missing project.yaml",
            err=True,
        )
        raise typer.Exit(EXIT_USER_ERROR)

    registry_dir = default_registry_dir()
    app = create_app(registry_dir=str(registry_dir))

    typer.echo(f"TaskPilot API server starting on http://{host}:{port}")
    typer.echo(f"OpenAPI docs at http://{host}:{port}/docs")
    uvicorn.run(app, host=host, port=port)


def register(app: typer.Typer) -> None:
    """Attach the ``serve`` command to ``app``."""
    app.command("serve")(serve_command)
