"""``taskpilot serve`` — start the local REST API server (task F005-T6, requirement F005-R6).

Resolves the TaskPilot workspace and registry, then runs the FastAPI application
via uvicorn. The server binds to ``127.0.0.1`` on port ``7152`` by default,
matching the Vite dev proxy target in ``web/vite.config.ts``.
"""

from __future__ import annotations

import typer
import uvicorn

from taskpilot.cli.exit_codes import EXIT_SYSTEM_ERROR
from taskpilot.cli.registry import default_registry_dir
from taskpilot.cli.workspace import find_workspace
from taskpilot.server.app import create_app

__all__ = ["register"]


def serve_command(
    ctx: typer.Context,
    host: str = typer.Option(
        "127.0.0.1", "--host", help="Host interface to bind."
    ),
    port: int = typer.Option(
        7152, "--port", help="Port to listen on."
    ),
    workspace: str | None = typer.Option(
        None,
        "--workspace",
        help="Workspace root path (default: auto-detect from cwd).",
    ),
) -> None:
    """Start the local REST API server."""
    if workspace is not None:
        from pathlib import Path
        from taskpilot.core.layout import WorkspacePaths
        ws = WorkspacePaths.for_root(Path(workspace))
        if not ws.exists():
            typer.echo(f"Error: no TaskPilot workspace at {ws.root}", err=True)
            raise typer.Exit(EXIT_SYSTEM_ERROR)
    else:
        try:
            ws = find_workspace()
        except Exception as exc:
            typer.echo(f"Error: {exc}", err=True)
            raise typer.Exit(EXIT_SYSTEM_ERROR) from exc

    registry_dir = default_registry_dir()
    app = create_app(workspace=str(ws.root), registry_dir=str(registry_dir))

    typer.echo(f"TaskPilot API server starting on http://{host}:{port}")
    typer.echo(f"OpenAPI docs at http://{host}:{port}/docs")
    uvicorn.run(app, host=host, port=port)


def register(app: typer.Typer) -> None:
    """Attach the ``serve`` command to ``app``."""
    app.command("serve")(serve_command)
