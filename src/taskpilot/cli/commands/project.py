"""``taskpilot project list`` — list registered projects (task F003-T3, requirement F003-R3).

Lists entries from the local system registry (spec ``0002``: "``project list``
shows all registry entries, including disabled entries ... sorts by project
name"), not the single in-repo project. Output is deterministic (entries sorted
by name then id, canonical field order) so repeated ``--json`` calls are
byte-identical (F003-R8).
"""

from __future__ import annotations

import typer

from taskpilot.cli import registry
from taskpilot.cli.context import get_state
from taskpilot.cli.output import print_json, print_line, render_table

__all__ = ["register"]

project_app = typer.Typer(
    name="project",
    help="Inspect registered TaskPilot projects.",
    no_args_is_help=True,
    add_completion=False,
)


@project_app.command("list")
def project_list(ctx: typer.Context) -> None:
    """List projects registered on this machine."""
    state = get_state(ctx)
    entries = registry.list_projects(registry.default_registry_dir())

    if state.json:
        print_json([entry.model_dump() for entry in entries])
        return

    if not entries:
        print_line(
            "No registered projects. Run `taskpilot init .` in a project repository."
        )
        return

    rows = [[e.id, e.key, e.name, "yes" if e.active else "no", e.path] for e in entries]
    print_line(render_table(["ID", "KEY", "NAME", "ACTIVE", "PATH"], rows))


def register(app: typer.Typer) -> None:
    """Attach the ``project`` command group to ``app``."""
    app.add_typer(project_app)
