"""Reverse link derivation (task F002-T5, requirement F002-R5).

Reverse relationships are computed from stored forward links at query time and
never persisted (the source item is the single place a link is recorded):

    forward ``blocks``     -> reverse ``blocked_by``
    forward ``relates_to`` -> reverse ``related_to``

If A ``blocks`` B then B is ``blocked_by`` A. Target lists are sorted by numeric
id for deterministic output.
"""

from __future__ import annotations

from collections import defaultdict

from taskpilot.core.layout import WorkspacePaths
from taskpilot.services import item_service

__all__ = ["derive_reverse_links", "reverse_links_for"]

#: Forward link type -> reverse link name.
_REVERSE_OF = {"blocks": "blocked_by", "relates_to": "related_to"}


def _numeric_id_key(item_id: str) -> tuple[int, str]:
    _, _, suffix = item_id.rpartition("-")
    return (int(suffix), item_id) if suffix.isdigit() else (-1, item_id)


def derive_reverse_links(paths: WorkspacePaths) -> dict[str, dict[str, list[str]]]:
    """Derive reverse links for every item that has incoming links (F002-R5).

    Returns ``{target_id: {"blocked_by": [...], "related_to": [...]}}``. Items
    with no incoming links are omitted. Considers all items (including deleted)
    so a stored link is always reflected; sorting is numeric for determinism.
    """
    reverse: dict[str, dict[str, list[str]]] = defaultdict(
        lambda: {"blocked_by": [], "related_to": []}
    )
    for item in item_service.list_items(paths, include_deleted=True):
        if item.links is None:
            continue
        for forward, reverse_name in _REVERSE_OF.items():
            for target in getattr(item.links, forward):
                reverse[target][reverse_name].append(item.id)

    for entry in reverse.values():
        for name in ("blocked_by", "related_to"):
            entry[name].sort(key=_numeric_id_key)
    return dict(reverse)


def reverse_links_for(paths: WorkspacePaths, item_id: str) -> dict[str, list[str]]:
    """Return derived reverse links for a single item (F002-R5).

    Always returns both keys; empty lists when the item has no incoming links.
    """
    full = derive_reverse_links(paths)
    return full.get(item_id, {"blocked_by": [], "related_to": []})
