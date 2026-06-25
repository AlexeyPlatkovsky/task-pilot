"""Unit tests for the link service (task F002-T4, requirement F002-R4).

Links (blocks, relates_to) are stored on the source item only. Adding/removing a
link touches only the source file; querying returns the item's stored links.
"""

from pathlib import Path

import pytest

from taskpilot.core.layout import WorkspacePaths
from taskpilot.services import item_service, link_service, project_service
from taskpilot.services.errors import NotFound, ValidationFailed


def _workspace(tmp_path: Path) -> WorkspacePaths:
    paths = WorkspacePaths.for_root(tmp_path)
    project_service.create_project(
        paths, key="VP", name="VoicePilot", now="2026-06-20T10:00:00Z"
    )
    return paths


def _two_items(paths: WorkspacePaths):
    a = item_service.create_item(
        paths, title="a", type="task", now="2026-06-20T11:00:00Z"
    )
    b = item_service.create_item(
        paths, title="b", type="task", now="2026-06-20T11:00:00Z"
    )
    return a, b


def test_add_link_updates_only_source_file(tmp_path: Path):
    paths = _workspace(tmp_path)
    a, b = _two_items(paths)
    before_b = paths.item_file(b.id).read_text(encoding="utf-8")

    updated = link_service.add_link(
        paths, a.id, "blocks", b.id, now="2026-06-21T09:00:00Z"
    )

    assert updated.links is not None
    assert b.id in updated.links.blocks
    # source persisted
    assert b.id in item_service.read_item(paths, a.id).links.blocks
    # target untouched
    assert paths.item_file(b.id).read_text(encoding="utf-8") == before_b


def test_query_links_returns_stored_links(tmp_path: Path):
    paths = _workspace(tmp_path)
    a, b = _two_items(paths)
    link_service.add_link(paths, a.id, "blocks", b.id)

    links = link_service.query_links(paths, a.id)
    assert links == {"blocks": [b.id], "relates_to": []}


def test_query_links_empty_when_none(tmp_path: Path):
    paths = _workspace(tmp_path)
    a, _ = _two_items(paths)
    assert link_service.query_links(paths, a.id) == {"blocks": [], "relates_to": []}


def test_add_link_is_idempotent(tmp_path: Path):
    paths = _workspace(tmp_path)
    a, b = _two_items(paths)
    link_service.add_link(paths, a.id, "blocks", b.id)
    link_service.add_link(paths, a.id, "blocks", b.id)
    assert item_service.read_item(paths, a.id).links.blocks == [b.id]


def test_add_relates_to_link(tmp_path: Path):
    paths = _workspace(tmp_path)
    a, b = _two_items(paths)
    link_service.add_link(paths, a.id, "relates_to", b.id)
    assert link_service.query_links(paths, a.id) == {"blocks": [], "relates_to": [b.id]}


def test_add_link_rejects_unknown_link_type(tmp_path: Path):
    paths = _workspace(tmp_path)
    a, b = _two_items(paths)
    with pytest.raises(ValidationFailed):
        link_service.add_link(paths, a.id, "duplicates", b.id)


def test_add_link_rejects_unknown_target(tmp_path: Path):
    paths = _workspace(tmp_path)
    a, _ = _two_items(paths)
    with pytest.raises(ValidationFailed):
        link_service.add_link(paths, a.id, "blocks", "VP-999")


def test_add_link_rejects_self_link(tmp_path: Path):
    paths = _workspace(tmp_path)
    a, _ = _two_items(paths)
    with pytest.raises(ValidationFailed):
        link_service.add_link(paths, a.id, "blocks", a.id)


def test_add_link_unknown_source_raises_not_found(tmp_path: Path):
    paths = _workspace(tmp_path)
    a, _ = _two_items(paths)
    with pytest.raises(NotFound):
        link_service.add_link(paths, "VP-999", "blocks", a.id)


def test_remove_link(tmp_path: Path):
    paths = _workspace(tmp_path)
    a, b = _two_items(paths)
    link_service.add_link(paths, a.id, "blocks", b.id)

    updated = link_service.remove_link(paths, a.id, "blocks", b.id)
    assert b.id not in (updated.links.blocks if updated.links else [])
    assert link_service.query_links(paths, a.id)["blocks"] == []


def test_remove_link_idempotent_no_write_when_absent(tmp_path: Path):
    paths = _workspace(tmp_path)
    a, b = _two_items(paths)
    before = paths.item_file(a.id).read_text(encoding="utf-8")
    # removing a link that was never added does not error and does not rewrite
    link_service.remove_link(paths, a.id, "blocks", b.id)
    assert paths.item_file(a.id).read_text(encoding="utf-8") == before


def test_update_item_rejects_dangling_link_on_write_path(tmp_path: Path):
    """links reaching the canonical write path directly are still validated."""
    paths = _workspace(tmp_path)
    a, _ = _two_items(paths)
    with pytest.raises(ValidationFailed):
        item_service.update_item(
            paths, a.id, links={"blocks": ["VP-999"], "relates_to": []}
        )
    assert item_service.read_item(paths, a.id).links is None


def test_update_item_rejects_self_link_on_write_path(tmp_path: Path):
    paths = _workspace(tmp_path)
    a, _ = _two_items(paths)
    with pytest.raises(ValidationFailed):
        item_service.update_item(
            paths, a.id, links={"blocks": [a.id], "relates_to": []}
        )
