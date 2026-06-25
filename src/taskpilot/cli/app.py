"""TaskPilot CLI entry point and root Typer app (task F003-T1, requirement F003-R8).

Defines the root ``taskpilot`` command group and its global ``--json`` option.
Subcommands (``init``, ``project``, ``item``, ``validate``, ``serve``) are
registered onto :data:`app` by their own modules in later F003 tasks. The
console-script entry point in ``pyproject.toml`` points at :data:`app`.
"""

from __future__ import annotations

import typer

from taskpilot.cli.context import CLIState

__all__ = ["app"]

app = typer.Typer(
    name="taskpilot",
    help="TaskPilot — local-first, file-based task management.",
    no_args_is_help=True,
    add_completion=False,
)


@app.callback()
def main(
    ctx: typer.Context,
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
    from taskpilot.cli.commands import init as init_cmd
    from taskpilot.cli.commands import item as item_cmd
    from taskpilot.cli.commands import project as project_cmd
    from taskpilot.cli.commands import validate as validate_cmd

    init_cmd.register(app)
    project_cmd.register(app)
    item_cmd.register(app)
    validate_cmd.register(app)


_register_commands()


if __name__ == "__main__":  # pragma: no cover - manual invocation convenience
    app()
