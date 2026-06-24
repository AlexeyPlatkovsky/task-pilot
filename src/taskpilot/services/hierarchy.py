"""Type-based parent/child hierarchy rules (task F002-T3, requirement F002-R3).

Enforced whenever an item's ``parent_id`` is set (on create or update). Allowed
parent -> child types (see ``docs/architecture.md`` "Hierarchy"):

    epic    -> feature, task
    feature -> task
    task    -> bug
    bug     -> (none)

Also rejects an item parenting itself and any change that would close a cycle.
The strictly-decreasing type table already makes cycles impossible for valid
types; the self/cycle guards are explicit so intent survives future table
changes and so error messages are precise.
"""

from __future__ import annotations

from taskpilot.core.layout import WorkspacePaths
from taskpilot.services.errors import NotFound, ValidationFailed

__all__ = ["ALLOWED_CHILD_TYPES", "validate_parent", "validate_can_parent_children"]

#: Allowed child types keyed by parent type.
ALLOWED_CHILD_TYPES: dict[str, set[str]] = {
    "epic": {"feature", "task"},
    "feature": {"task"},
    "task": {"bug"},
    "bug": set(),
}


def validate_parent(
    paths: WorkspacePaths,
    *,
    child_id: str,
    child_type: str,
    parent_id: str | None,
) -> None:
    """Validate that ``child`` may have ``parent_id`` as its parent.

    No-op when ``parent_id`` is ``None``. Raises :class:`ValidationFailed` when the
    parent is the child itself, does not exist, is a type that cannot parent
    ``child_type``, or when the assignment would close an ancestor cycle.
    """
    from taskpilot.services.item_service import read_item  # local import avoids a cycle

    if parent_id is None:
        return
    if parent_id == child_id:
        raise ValidationFailed(f"Item {child_id!r} cannot be its own parent")

    try:
        parent = read_item(paths, parent_id)
    except NotFound as exc:
        raise ValidationFailed(
            f"parent_id references unknown item {parent_id!r}"
        ) from exc

    allowed = ALLOWED_CHILD_TYPES.get(parent.type, set())
    if child_type not in allowed:
        raise ValidationFailed(
            f"A {parent.type} cannot be the parent of a {child_type} "
            f"(allowed children of {parent.type}: {sorted(allowed) or 'none'})"
        )

    # Walk the parent's ancestors; reaching child_id means this closes a cycle.
    seen: set[str] = set()
    cursor = parent
    while cursor.parent_id:
        if cursor.parent_id == child_id:
            raise ValidationFailed(
                f"Setting parent of {child_id!r} to {parent_id!r} would create a cycle"
            )
        if cursor.parent_id in seen:
            break  # pre-existing cycle elsewhere; stop rather than loop forever
        seen.add(cursor.parent_id)
        try:
            cursor = read_item(paths, cursor.parent_id)
        except (NotFound, ValidationFailed):
            break


def validate_can_parent_children(
    paths: WorkspacePaths,
    *,
    parent_id: str,
    parent_type: str,
) -> None:
    """Ensure ``parent_type`` may still parent every item currently pointing at it.

    Called when an item's ``type`` changes: a parent must not be retyped into a
    type that cannot legally parent its existing children (which would persist an
    item-graph the hierarchy table forbids). Raises :class:`ValidationFailed`
    naming the first offending child.
    """
    from taskpilot.services.item_service import list_items  # local import avoids a cycle

    allowed = ALLOWED_CHILD_TYPES.get(parent_type, set())
    for child in list_items(paths, include_deleted=True):
        if child.parent_id == parent_id and child.type not in allowed:
            raise ValidationFailed(
                f"Cannot change {parent_id!r} to type {parent_type!r}: it parents "
                f"{child.id!r} (a {child.type}), which a {parent_type} cannot parent"
            )
