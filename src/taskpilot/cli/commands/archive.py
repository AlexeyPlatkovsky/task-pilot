"""``taskpilot archive`` commands — run, migrate, unarchive (feature F009, task TP-110).

Thin adapters over the archive service. All operations are manual/on-demand;
there is no scheduler in CLI mode.

JSON output dumps the result in a deterministic format for automation.
"""

from __future__ import annotations


import typer

from taskpilot.cli.context import get_state
from taskpilot.cli.errors import service_errors
from taskpilot.cli.output import print_json, print_line
from taskpilot.cli.workspace import find_workspace
from taskpilot.services import archive_service

__all__ = ["register"]

archive_app = typer.Typer(
    name="archive",
    help="Archive, migrate, and unarchive items.",
    no_args_is_help=True,
    add_completion=False,
)


@archive_app.command("run")
def archive_run(ctx: typer.Context) -> None:
    """Trigger archive check on eligible items."""
    with service_errors():
        paths = find_workspace()
        eligible = archive_service.scan_eligible_items(paths)
        item_ids = [item.id for item in eligible]
        archived_ids = archive_service.archive_items(paths, item_ids)

    if get_state(ctx).json:
        print_json({"archived": archived_ids})
        return
    if archived_ids:
        print_line(f"Archived {len(archived_ids)} item(s): {', '.join(archived_ids)}")
    else:
        print_line("No items eligible for archiving.")


@archive_app.command("migrate")
def archive_migrate(ctx: typer.Context) -> None:
    """One-time migration of all eligible items."""
    with service_errors():
        paths = find_workspace()
        archived_ids = archive_service.migrate_all_eligible(paths)

    if get_state(ctx).json:
        print_json({"archived_count": len(archived_ids), "archived_ids": archived_ids})
        return
    print_line(f"Archived {len(archived_ids)} item(s) via migration.")


@archive_app.command("migrate-storage")
def archive_migrate_storage(ctx: typer.Context) -> None:
    """Move compatible root-level archives into archive-month directories."""
    with service_errors():
        paths = find_workspace()
        migrated_ids = archive_service.migrate_legacy_archives(paths)

    if get_state(ctx).json:
        print_json({"migrated_count": len(migrated_ids), "migrated_ids": migrated_ids})
        return
    print_line(f"Migrated {len(migrated_ids)} archive item(s) to month storage.")


@archive_app.command("unarchive")
def archive_unarchive(
    ctx: typer.Context,
    item_id: str = typer.Argument(..., help="Item id to unarchive."),
) -> None:
    """Unarchive a single item."""
    with service_errors():
        paths = find_workspace()
        item = archive_service.unarchive_item(paths, item_id)

    if get_state(ctx).json:
        print_json(item.model_dump())
        return
    print_line(f"Unarchived {item_id}.")


def register(app: typer.Typer) -> None:
    """Attach the ``archive`` command group to ``app``."""
    app.add_typer(archive_app)
