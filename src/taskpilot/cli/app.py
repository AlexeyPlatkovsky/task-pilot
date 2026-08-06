"""TaskPilot CLI entry point and root Typer app (task F003-T1, requirement F003-R8).

Defines the root ``taskpilot`` command group and its global ``--json`` and
``--version``/``-v`` (TP-123, spec 0006) options. Subcommands (``init``,
``project``, ``item``, ``validate``, ``serve``) are registered onto :data:`app`
by their own modules in later F003 tasks. The console-script entry point in
``pyproject.toml`` points at :data:`app`.
"""

from __future__ import annotations

import importlib.metadata

import typer

from taskpilot.cli.context import CLIState
from taskpilot.cli.exit_codes import EXIT_OK, EXIT_USER_ERROR

__all__ = ["app"]

app = typer.Typer(
    name="taskpilot",
    help="TaskPilot — local-first, file-based task management.",
    no_args_is_help=True,
    add_completion=False,
)


def _print_version(value: bool) -> None:
    """Eager ``--version``/``-v`` callback: print and exit before dispatch.

    Runs before ``--json``/``CLIState`` are resolved, so output is always
    plain text regardless of ``--json`` — matching the npm wrapper's
    ``--version`` handling in ``bin/taskpilot``.
    """
    if not value:
        return
    try:
        version = importlib.metadata.version("taskpilot")
    except importlib.metadata.PackageNotFoundError:
        typer.echo(
            "taskpilot: package metadata not found — is taskpilot installed? "
            "(try `pip install -e .`)",
            err=True,
        )
        raise typer.Exit(code=EXIT_USER_ERROR) from None
    typer.echo(version)
    raise typer.Exit(code=EXIT_OK)


@app.callback()
def main(
    ctx: typer.Context,
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        help="Print the installed TaskPilot version and exit.",
        is_eager=True,
        callback=_print_version,
    ),
    json: bool = typer.Option(
        False,
        "--json",
        help="Emit machine-readable JSON to stdout instead of human-readable text.",
    ),
) -> None:
    """Resolve global options once and store them for every subcommand."""
    ctx.obj = CLIState(json=json)


def _register_commands() -> None:
    """Attach every command module to :data:`app`.

    Imported here (not at module top) so command modules can import from this
    module without a circular import.
    """
    from taskpilot.cli.commands import archive as archive_cmd
    from taskpilot.cli.commands import daemon as daemon_cmd
    from taskpilot.cli.commands import init as init_cmd
    from taskpilot.cli.commands import item as item_cmd
    from taskpilot.cli.commands import project as project_cmd
    from taskpilot.cli.commands import serve as serve_cmd
    from taskpilot.cli.commands import validate as validate_cmd

    init_cmd.register(app)
    project_cmd.register(app)
    item_cmd.register(app)
    validate_cmd.register(app)
    serve_cmd.register(app)
    daemon_cmd.register(app)
    archive_cmd.register(app)


_register_commands()


if __name__ == "__main__":  # pragma: no cover - manual invocation convenience
    app()
