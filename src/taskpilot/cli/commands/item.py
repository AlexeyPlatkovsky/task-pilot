"""``taskpilot item`` commands — list/show/create/update (task F003-T4, requirement F003-R4).

Thin adapters over the F002 item service. Enum-like fields (``type``, ``status``,
``priority``) are passed through as strings and validated by the service, which
is the single source of truth for domain rules — invalid values surface as a
``ValidationFailed`` mapped to exit code 1, before any file is written (F003-R4).
JSON output dumps the item model in canonical field order for determinism
(F003-R8).
"""

from __future__ import annotations

import getpass
from typing import Any, Optional

import typer

from taskpilot.cli.context import get_state
from taskpilot.cli.errors import service_errors
from taskpilot.cli.output import print_json, print_line, render_key_values, render_table
from taskpilot.cli.workspace import find_workspace
from taskpilot.core.models import Item
from taskpilot.services import comment_service, item_service, link_service


def _default_author() -> str:
    """Best-effort local author identity for comments when ``--author`` is omitted."""
    try:
        return getpass.getuser()
    except Exception:  # pragma: no cover - getuser is environment-dependent
        return "unknown"


__all__ = ["register"]

_HUMAN_SKIP = frozenset({"schema_version"})

item_app = typer.Typer(
    name="item",
    help="List, show, create, and update items.",
    no_args_is_help=True,
    add_completion=False,
)


def _emit_item(
    ctx: typer.Context, item: Item, *, human_prefix: str | None = None
) -> None:
    """Render a single item as JSON or a human key/value block (or a one-liner)."""
    if get_state(ctx).json:
        print_json(item.model_dump())
        return
    if human_prefix is not None:
        print_line(f"{human_prefix} {item.id}")
        return
    pairs = [
        (name, str(value))
        for name, value in item.model_dump().items()
        if value is not None and name not in _HUMAN_SKIP
    ]
    print_line(render_key_values(pairs))


@item_app.command("list")
def item_list(
    ctx: typer.Context,
    status: Optional[str] = typer.Option(None, "--status", help="Filter by status."),
    type: Optional[str] = typer.Option(None, "--type", help="Filter by item type."),
    project: Optional[str] = typer.Option(
        None, "--project", help="Filter by project key (id prefix)."
    ),
    include_deleted: bool = typer.Option(
        False, "--include-deleted", help="Include soft-deleted items."
    ),
) -> None:
    """List items in the current workspace."""
    with service_errors():
        paths = find_workspace()
        items = item_service.list_items(
            paths,
            project=project,
            status=status,
            type=type,
            include_deleted=include_deleted,
        )

    if get_state(ctx).json:
        print_json([item.model_dump() for item in items])
        return

    if not items:
        print_line("No items found.")
        return
    rows = [[i.id, i.type, i.status, i.priority, i.title] for i in items]
    print_line(render_table(["ID", "TYPE", "STATUS", "PRIORITY", "TITLE"], rows))


@item_app.command("show")
def item_show(
    ctx: typer.Context,
    item_id: str = typer.Argument(..., help="Item id, e.g. VP-1."),
) -> None:
    """Show a single item by id."""
    with service_errors():
        paths = find_workspace()
        item = item_service.read_item(paths, item_id)
    _emit_item(ctx, item)


@item_app.command("create")
def item_create(
    ctx: typer.Context,
    title: str = typer.Option(..., "--title", help="Item title (required)."),
    type: str = typer.Option(
        ..., "--type", help="Item type: epic|feature|task|bug (required)."
    ),
    priority: str = typer.Option(
        "normal", "--priority", help="Priority: low|normal|high."
    ),
    status: str = typer.Option("backlog", "--status", help="Initial status."),
    description: Optional[str] = typer.Option(
        None, "--description", help="Item description."
    ),
    parent: Optional[str] = typer.Option(None, "--parent", help="Parent item id."),
    tag: Optional[list[str]] = typer.Option(None, "--tag", help="Tag (repeatable)."),
    created_by: Optional[str] = typer.Option(
        None, "--created-by", help="Author identity."
    ),
) -> None:
    """Create a new item and print its id."""
    with service_errors():
        paths = find_workspace()
        item = item_service.create_item(
            paths,
            title=title,
            type=type,
            priority=priority,
            status=status,
            description=description,
            parent_id=parent,
            tags=tag or None,
            created_by=created_by,
        )
    _emit_item(ctx, item, human_prefix="Created")


@item_app.command("update")
def item_update(
    ctx: typer.Context,
    item_id: str = typer.Argument(..., help="Item id to update."),
    title: Optional[str] = typer.Option(None, "--title", help="New title."),
    type: Optional[str] = typer.Option(None, "--type", help="New type."),
    priority: Optional[str] = typer.Option(None, "--priority", help="New priority."),
    status: Optional[str] = typer.Option(None, "--status", help="New status."),
    description: Optional[str] = typer.Option(
        None, "--description", help="New description."
    ),
    parent: Optional[str] = typer.Option(None, "--parent", help="New parent item id."),
    tag: Optional[list[str]] = typer.Option(
        None, "--tag", help="Replace tags (repeatable)."
    ),
) -> None:
    """Update fields on an existing item.

    Only the options you pass are changed; ``--parent`` and ``--tag`` set new
    values (they do not merge). Every update refreshes ``updated_at``.
    """
    fields: dict[str, Any] = {}
    if title is not None:
        fields["title"] = title
    if type is not None:
        fields["type"] = type
    if priority is not None:
        fields["priority"] = priority
    if status is not None:
        fields["status"] = status
    if description is not None:
        fields["description"] = description
    if parent is not None:
        fields["parent_id"] = parent
    if tag is not None:
        fields["tags"] = tag

    with service_errors():
        paths = find_workspace()
        item = item_service.update_item(paths, item_id, **fields)
    _emit_item(ctx, item, human_prefix="Updated")


def _emit_relationship(ctx: typer.Context, item: Item, message: str) -> None:
    """Render a relationship change: the updated source item (JSON) or a confirmation."""
    if get_state(ctx).json:
        print_json(item.model_dump())
        return
    print_line(message)


@item_app.command("parent")
def item_parent(
    ctx: typer.Context,
    child_id: str = typer.Argument(..., help="Child item id."),
    parent_id: str = typer.Argument(..., help="Parent item id."),
) -> None:
    """Set ``child_id``'s parent to ``parent_id`` (hierarchy rules apply)."""
    with service_errors():
        paths = find_workspace()
        item = item_service.update_item(paths, child_id, parent_id=parent_id)
    _emit_relationship(ctx, item, f"{child_id} parent set to {parent_id}.")


@item_app.command("unparent")
def item_unparent(
    ctx: typer.Context,
    child_id: str = typer.Argument(..., help="Child item id."),
) -> None:
    """Clear ``child_id``'s parent."""
    with service_errors():
        paths = find_workspace()
        item = item_service.update_item(paths, child_id, parent_id=None)
    _emit_relationship(ctx, item, f"{child_id} parent cleared.")


@item_app.command("blocks")
def item_blocks(
    ctx: typer.Context,
    source_id: str = typer.Argument(..., help="Item that blocks."),
    target_id: str = typer.Argument(..., help="Item that is blocked."),
) -> None:
    """Record that ``source_id`` blocks ``target_id`` (idempotent)."""
    with service_errors():
        paths = find_workspace()
        item = link_service.add_link(paths, source_id, "blocks", target_id)
    _emit_relationship(ctx, item, f"{source_id} now blocks {target_id}.")


@item_app.command("unblocks")
def item_unblocks(
    ctx: typer.Context,
    source_id: str = typer.Argument(..., help="Item that blocks."),
    target_id: str = typer.Argument(..., help="Item that is blocked."),
) -> None:
    """Remove a ``blocks`` link from ``source_id`` to ``target_id`` (idempotent)."""
    with service_errors():
        paths = find_workspace()
        item = link_service.remove_link(paths, source_id, "blocks", target_id)
    _emit_relationship(ctx, item, f"{source_id} no longer blocks {target_id}.")


@item_app.command("relates")
def item_relates(
    ctx: typer.Context,
    source_id: str = typer.Argument(..., help="Source item."),
    target_id: str = typer.Argument(..., help="Related item."),
) -> None:
    """Record that ``source_id`` relates to ``target_id`` (idempotent)."""
    with service_errors():
        paths = find_workspace()
        item = link_service.add_link(paths, source_id, "relates_to", target_id)
    _emit_relationship(ctx, item, f"{source_id} now relates to {target_id}.")


@item_app.command("unrelates")
def item_unrelates(
    ctx: typer.Context,
    source_id: str = typer.Argument(..., help="Source item."),
    target_id: str = typer.Argument(..., help="Related item."),
) -> None:
    """Remove a ``relates_to`` link from ``source_id`` to ``target_id`` (idempotent)."""
    with service_errors():
        paths = find_workspace()
        item = link_service.remove_link(paths, source_id, "relates_to", target_id)
    _emit_relationship(ctx, item, f"{source_id} no longer relates to {target_id}.")


@item_app.command("comment")
def item_comment(
    ctx: typer.Context,
    item_id: str = typer.Argument(..., help="Item id to comment on."),
    text: str = typer.Argument(..., help="Comment body."),
    author: Optional[str] = typer.Option(
        None, "--author", help="Comment author (defaults to the local user)."
    ),
) -> None:
    """Add a comment to an item and print the comment filename."""
    with service_errors():
        paths = find_workspace()
        written = comment_service.add_comment(
            paths, item_id, body=text, created_by=author or _default_author()
        )

    if get_state(ctx).json:
        print_json(
            {
                "item_id": item_id,
                "filename": written.name,
                "path": paths.relative_posix(written),
            }
        )
        return
    print_line(written.name)


def register(app: typer.Typer) -> None:
    """Attach the ``item`` command group to ``app``."""
    app.add_typer(item_app)
