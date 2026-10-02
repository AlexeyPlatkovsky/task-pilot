"""``taskpilot update`` for installs without the npm wrapper (spec 0011 R7).

Self-update is provided by the npm entry point (``bin/taskpilot``), which handles
``update`` itself and never reaches this command. A pip or source install has no
npm package to upgrade, so this command only explains the npm path and never
touches the network.
"""

from __future__ import annotations

import typer

from taskpilot.cli.exit_codes import EXIT_USER_ERROR

__all__ = ["register"]

NPM_PACKAGE = "@alexey_platkovsky/taskpilot"


def update_command() -> None:
    """Explain how to update; self-update is provided by the npm package."""
    typer.echo(
        "taskpilot: self-update is provided by the npm package. Install or update it with:\n"
        f"  npm install -g {NPM_PACKAGE}@latest",
        err=True,
    )
    raise typer.Exit(EXIT_USER_ERROR)


def register(app: typer.Typer) -> None:
    """Attach the ``update`` command to ``app``."""
    app.command("update")(update_command)
