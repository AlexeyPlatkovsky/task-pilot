"""Unit tests for reverse link derivation (task F002-T5, requirement F002-R5).

Reverse links (blocked_by, related_to) are computed at query time from stored
forward links and never persisted.
"""

from pathlib import Path

from taskpilot.core.layout import WorkspacePaths
from taskpilot.services import item_service, link_service, project_service
from taskpilot.services.reverse_links import derive_reverse_links, reverse_links_for


def _workspace(tmp_path: Path) -> WorkspacePaths:
    paths = WorkspacePaths.for_root(tmp_path)
    project_service.create_project(
        paths, key="VP", name="VoicePilot", now="2026-06-20T10:00:00Z"
    )
    return paths


def _items(paths: WorkspacePaths, n: int):
    return [
        item_service.create_item(paths, title=f"i{k}", type="task") for k in range(n)
    ]


def test_blocked_by_is_derived_from_blocks(tmp_path: Path):
    paths = _workspace(tmp_path)
    v1, v2, v3 = _items(paths, 3)
    link_service.add_link(paths, v1.id, "blocks", v2.id)
    link_service.add_link(paths, v3.id, "blocks", v2.id)

    rev = reverse_links_for(paths, v2.id)
    assert rev["blocked_by"] == [v1.id, v3.id]


def test_reverse_links_not_persisted(tmp_path: Path):
    paths = _workspace(tmp_path)
    v1, v2, _ = _items(paths, 3)
    link_service.add_link(paths, v1.id, "blocks", v2.id)

    text = paths.item_file(v2.id).read_text(encoding="utf-8")
    assert "blocked_by" not in text


def test_related_to_is_derived_from_relates_to(tmp_path: Path):
    paths = _workspace(tmp_path)
    v1, v2, _ = _items(paths, 3)
    link_service.add_link(paths, v1.id, "relates_to", v2.id)

    assert reverse_links_for(paths, v2.id)["related_to"] == [v1.id]
    # the source has no incoming relation
    assert reverse_links_for(paths, v1.id)["related_to"] == []


def test_derive_reverse_links_full_map(tmp_path: Path):
    paths = _workspace(tmp_path)
    v1, v2, v3 = _items(paths, 3)
    link_service.add_link(paths, v1.id, "blocks", v2.id)
    link_service.add_link(paths, v3.id, "blocks", v2.id)

    full = derive_reverse_links(paths)
    assert full[v2.id]["blocked_by"] == [v1.id, v3.id]
    # items with no incoming links are absent or empty
    assert full.get(v1.id, {"blocked_by": []})["blocked_by"] == []


def test_reverse_links_sorted_numerically(tmp_path: Path):
    paths = _workspace(tmp_path)
    items = _items(paths, 12)  # VP-1 .. VP-12
    target = items[0]
    # everything blocks VP-1
    for src in items[1:]:
        link_service.add_link(paths, src.id, "blocks", target.id)

    blocked_by = reverse_links_for(paths, target.id)["blocked_by"]
    assert blocked_by[:2] == ["VP-2", "VP-3"]
    assert blocked_by[-1] == "VP-12"  # numeric ordering, not lexical


def test_reverse_links_empty_for_unlinked_item(tmp_path: Path):
    paths = _workspace(tmp_path)
    v1, _, _ = _items(paths, 3)
    assert reverse_links_for(paths, v1.id) == {"blocked_by": [], "related_to": []}
