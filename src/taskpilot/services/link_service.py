"""Link domain service: add, remove, query (task F002-T4, requirement F002-R4).

Non-parent graph links (``blocks``, ``relates_to``) are stored as a map on the
*source* item. Adding or removing a link rewrites only the source file (the
target is never touched); reverse relationships are derived elsewhere (F002-T5),
never stored. Link targets must reference an existing item.
"""

from __future__ import annotations

from taskpilot.core.layout import WorkspacePaths
from taskpilot.core.models import Item
from taskpilot.services import item_service
from taskpilot.services.errors import NotFound, ValidationFailed

__all__ = ["LINK_TYPES", "add_link", "remove_link", "query_links"]

#: Link types supported through Alpha.
LINK_TYPES = ("blocks", "relates_to")


def _require_link_type(link_type: str) -> None:
    if link_type not in LINK_TYPES:
        raise ValidationFailed(
            f"Unknown link type {link_type!r}; expected one of {list(LINK_TYPES)}"
        )


def _links_as_dict(item: Item) -> dict[str, list[str]]:
    if item.links is None:
        return {"blocks": [], "relates_to": []}
    return {"blocks": list(item.links.blocks), "relates_to": list(item.links.relates_to)}


def add_link(
    paths: WorkspacePaths,
    source_id: str,
    link_type: str,
    target_id: str,
    *,
    now: str | None = None,
) -> Item:
    """Add ``link_type`` from ``source_id`` to ``target_id`` (F002-R4).

    Validates the link type, rejects self-links, and requires the target to
    exist. Idempotent: adding an existing link rewrites nothing. Raises
    :class:`NotFound` when the source is missing and :class:`ValidationFailed`
    for an unknown link type, self-link, or unknown target.
    """
    _require_link_type(link_type)
    source = item_service.read_item(paths, source_id)  # NotFound propagates
    if source_id == target_id:
        raise ValidationFailed(f"Item {source_id!r} cannot link to itself")
    if not paths.item_file(target_id).is_file():
        raise ValidationFailed(f"Link target references unknown item {target_id!r}")

    links = _links_as_dict(source)
    if target_id in links[link_type]:
        return source  # idempotent: already linked
    links[link_type].append(target_id)
    return item_service.update_item(paths, source_id, now=now, links=links)


def remove_link(
    paths: WorkspacePaths,
    source_id: str,
    link_type: str,
    target_id: str,
    *,
    now: str | None = None,
) -> Item:
    """Remove ``link_type`` from ``source_id`` to ``target_id`` (F002-R4).

    Idempotent: removing an absent link rewrites nothing and returns the source
    unchanged. Raises :class:`NotFound` when the source is missing and
    :class:`ValidationFailed` for an unknown link type.
    """
    _require_link_type(link_type)
    source = item_service.read_item(paths, source_id)  # NotFound propagates

    links = _links_as_dict(source)
    if target_id not in links[link_type]:
        return source  # idempotent: nothing to remove
    links[link_type] = [t for t in links[link_type] if t != target_id]
    return item_service.update_item(paths, source_id, now=now, links=links)


def query_links(paths: WorkspacePaths, item_id: str) -> dict[str, list[str]]:
    """Return ``item_id``'s stored (forward) links as ``{type: [target_ids]}`` (F002-R4).

    Reverse links (``blocked_by``, ``related_to``) are derived separately (F002-T5).
    Raises :class:`NotFound` when the item is missing.
    """
    return _links_as_dict(item_service.read_item(paths, item_id))
