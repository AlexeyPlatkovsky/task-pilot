"""Item domain service: create, read, update, list (task F002-T2, requirement F002-R2).

Stateless operations over canonical ``items/<id>.yaml`` files. IDs are allocated
as ``<PROJECT_KEY>-<n>`` where ``n`` is one past the highest existing numeric
suffix (gaps from deleted items are not reused). Model construction validates
enums/timestamps, so invalid input is rejected before any file is written
(F002-R8); richer pre-write validation is consolidated in F002-T8.

Hierarchy rules for ``parent_id`` (F002-T3) and links (F002-T4/T5) are layered on
in their own tasks; this service owns plain field create/read/update/list.
"""

from __future__ import annotations

from pydantic import ValidationError

from taskpilot.core.item_io import ItemParseError, parse_item_file, write_item
from taskpilot.core.layout import WorkspacePaths
from taskpilot.core.models import Item
from taskpilot.core.timestamps import utc_now_iso
from taskpilot.services.errors import NotFound, ValidationFailed
from taskpilot.services.hierarchy import validate_can_parent_children, validate_parent
from taskpilot.services.operation_validation import build_validated_item
from taskpilot.services.project_service import read_project

__all__ = [
    "create_item",
    "read_item",
    "update_item",
    "delete_item",
    "list_items",
    "next_id",
]


def _numeric_suffix(item_id: str, key: str) -> int | None:
    """Return the numeric suffix of ``item_id`` for project ``key``, else ``None``."""
    prefix = f"{key}-"
    if not item_id.startswith(prefix):
        return None
    rest = item_id[len(prefix) :]
    return int(rest) if rest.isdigit() else None


def next_id(paths: WorkspacePaths, key: str) -> str:
    """Allocate the next item id for project ``key`` as ``<key>-<max+1>``.

    Scans existing ``items/*.yaml`` filenames for the highest numeric suffix.
    Gaps left by deleted items are not reused (see ``tasks.md`` notes).
    """
    highest = 0
    if paths.items_dir.is_dir():
        for file in paths.items_dir.glob("*.yaml"):
            suffix = _numeric_suffix(file.stem, key)
            if suffix is not None and suffix > highest:
                highest = suffix
    return f"{key}-{highest + 1}"


def create_item(
    paths: WorkspacePaths,
    *,
    title: str,
    type: str,
    priority: str = "normal",
    status: str = "backlog",
    description: str | None = None,
    parent_id: str | None = None,
    tags: list[str] | None = None,
    created_by: str | None = None,
    now: str | None = None,
) -> Item:
    """Create a new item with an allocated id and return it (F002-R2).

    Requires an initialized project (its key prefixes the id). ``created_at`` and
    ``updated_at`` are set to ``now`` (current UTC by default). Raises
    :class:`NotFound` when no project exists and :class:`ValidationFailed` for
    invalid field values — no file is written in the latter case.
    """
    project = read_project(paths)  # raises NotFound when absent
    timestamp = now or utc_now_iso()
    item_id = next_id(paths, project.key)
    item = build_validated_item(
        {
            "id": item_id,
            "title": title,
            "type": type,
            "priority": priority,
            "status": status,
            "created_at": timestamp,
            "updated_at": timestamp,
            "description": description,
            "parent_id": parent_id,
            "tags": tags,
            "created_by": created_by,
        }
    )
    validate_parent(
        paths, child_id=item.id, child_type=item.type, parent_id=item.parent_id
    )
    write_item(paths, item)
    return item


def read_item(paths: WorkspacePaths, item_id: str) -> Item:
    """Read an item by id (F002-R2).

    Raises :class:`NotFound` when the file is absent and :class:`ValidationFailed`
    when it exists but cannot be parsed/validated.
    """
    target = paths.item_file(item_id)
    if not target.is_file():
        raise NotFound(f"No item found with id {item_id!r}")
    try:
        return parse_item_file(target)
    except (ItemParseError, ValidationError, UnicodeDecodeError, OSError) as exc:
        raise ValidationFailed(f"Invalid item file for {item_id!r}: {exc}") from exc


def update_item(
    paths: WorkspacePaths,
    item_id: str,
    *,
    now: str | None = None,
    **fields: object,
) -> Item:
    """Update ``item_id``'s fields and refresh ``updated_at`` (F002-R2).

    Reads the current item, applies ``fields``, re-validates, and persists.
    ``id`` and ``created_at`` cannot be changed. Raises :class:`NotFound` when the
    item is absent and :class:`ValidationFailed` for invalid values (the file is
    left unchanged in that case).
    """
    current = read_item(paths, item_id)

    for immutable in ("id", "created_at"):
        if immutable in fields:
            raise ValidationFailed(f"Field {immutable!r} cannot be updated")

    data = current.model_dump()
    data.update(fields)
    data["updated_at"] = now or utc_now_iso()
    updated = build_validated_item(data)

    validate_parent(
        paths, child_id=updated.id, child_type=updated.type, parent_id=updated.parent_id
    )
    if updated.type != current.type:
        validate_can_parent_children(
            paths, parent_id=updated.id, parent_type=updated.type
        )
    _validate_links(paths, updated)
    write_item(paths, updated)
    return updated


def _validate_links(paths: WorkspacePaths, item: Item) -> None:
    """Reject self-links or links to unknown items on the canonical write path.

    ``add_link``/``remove_link`` validate before delegating here, but ``links``
    can also reach :func:`update_item` directly, so the shared write path must
    enforce the same rules (F002-R4/R8) — no dangling or self links may persist.
    """
    if item.links is None:
        return
    for link_type in ("blocks", "relates_to"):
        for target in getattr(item.links, link_type):
            if target == item.id:
                raise ValidationFailed(f"Item {item.id!r} cannot link to itself")
            if not paths.item_file(target).is_file():
                raise ValidationFailed(
                    f"links.{link_type} references unknown item {target!r}"
                )


def delete_item(paths: WorkspacePaths, item_id: str, *, now: str | None = None) -> Item:
    """Soft-delete an item by setting ``status: deleted`` (F002-R7).

    The file is preserved on disk and stays findable by direct lookup; default
    listings exclude it. Idempotent: deleting an already-deleted item returns it
    unchanged without rewriting the file. Raises :class:`NotFound` when absent.
    """
    current = read_item(paths, item_id)  # raises NotFound when absent
    if current.status == "deleted":
        return current  # idempotent: no rewrite, updated_at preserved
    return update_item(paths, item_id, now=now, status="deleted")


def _numeric_id_key(item: Item) -> tuple[int, str]:
    _, _, suffix = item.id.rpartition("-")
    return (int(suffix), item.id) if suffix.isdigit() else (-1, item.id)


def list_items(
    paths: WorkspacePaths,
    *,
    project: str | None = None,
    status: str | None = None,
    type: str | None = None,
    include_deleted: bool = False,
) -> list[Item]:
    """List items, filtered and sorted by numeric id (F002-R2).

    Filters: ``project`` (item-id key prefix), ``status``, ``type``. ``deleted``
    items are excluded unless ``include_deleted`` is true. Structurally invalid
    files are skipped here; surfacing them is the validation layer's job (F001-T7).
    """
    items: list[Item] = []
    if paths.items_dir.is_dir():
        for file in paths.items_dir.glob("*.yaml"):
            if not file.is_file():
                continue
            try:
                items.append(parse_item_file(file))
            except (ItemParseError, ValidationError, UnicodeDecodeError, OSError):
                continue

    if project is not None:
        prefix = f"{project}-"
        items = [i for i in items if i.id.startswith(prefix)]
    if status is not None:
        items = [i for i in items if i.status == status]
    if type is not None:
        items = [i for i in items if i.type == type]
    if not include_deleted:
        items = [i for i in items if i.status != "deleted"]

    items.sort(key=_numeric_id_key)
    return items
