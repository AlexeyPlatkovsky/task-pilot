"""``taskpilot serve`` — placeholder until the REST API exists (task F003-T8, requirement F003-R2).

The real command starts the local FastAPI REST server, but that server layer is
owned by Phase 4 / F004 (WebUI Workspace — "Backend REST API"), which is not yet
implemented. Until then this command exists so the interface is discoverable and
stable, but it reports that serving is unavailable and exits with the system-error
code rather than pretending to start a server.

The ``--host``/``--port`` options are accepted now so the command-line contract
(F003-R2: configurable port) does not change when the server lands.
"""

from __future__ import annotations

import typer

from taskpilot.cli.exit_codes import EXIT_SYSTEM_ERROR

__all__ = ["register"]


def serve_command(
    ctx: typer.Context,
    host: str = typer.Option(
        "127.0.0.1", "--host", help="Host interface to bind (reserved for F004)."
    ),
    port: int = typer.Option(
        7152, "--port", help="Port to listen on (reserved for F004)."
    ),
) -> None:
    """Start the local REST API server (not yet available — see F004)."""
    typer.echo(
        "`taskpilot serve` is not available yet: the local REST API server "
        "(feature F004) is not implemented.",
        err=True,
    )
    raise typer.Exit(EXIT_SYSTEM_ERROR)


def register(app: typer.Typer) -> None:
    """Attach the ``serve`` command to ``app``."""
    app.command("serve")(serve_command)
