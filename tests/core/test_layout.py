"""Unit tests for the .taskpilot/ workspace layout constants and path resolver.

Covers F001-R1 storage foundation (task F001-T1): layout constants and path
resolution helpers that every other F001 task builds on.
"""

from pathlib import Path

import pytest

from taskpilot.core import layout
from taskpilot.core.layout import WorkspacePaths


def test_layout_constants_match_canonical_spec():
    # Canonical names per docs/specs/0002 "Repository and Registry Model".
    assert layout.WORKSPACE_DIRNAME == ".taskpilot"
    assert layout.PROJECT_FILENAME == "project.yaml"
    assert layout.ITEMS_DIRNAME == "items"
    assert layout.COMMENTS_DIRNAME == "comments"
    assert layout.ITEM_FILE_SUFFIX == ".yaml"
    assert layout.COMMENT_FILE_SUFFIX == ".md"


def test_for_root_resolves_top_level_paths(tmp_path: Path):
    paths = WorkspacePaths.for_root(tmp_path)

    assert paths.root == tmp_path
    assert paths.workspace_dir == tmp_path / ".taskpilot"
    assert paths.project_file == tmp_path / ".taskpilot" / "project.yaml"
    assert paths.items_dir == tmp_path / ".taskpilot" / "items"
    assert paths.comments_dir == tmp_path / ".taskpilot" / "comments"


def test_for_root_normalizes_relative_root_to_absolute(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    paths = WorkspacePaths.for_root(Path("."))

    assert paths.root.is_absolute()
    assert paths.workspace_dir == tmp_path / ".taskpilot"


def test_item_file_uses_item_id_and_yaml_suffix(tmp_path: Path):
    paths = WorkspacePaths.for_root(tmp_path)

    assert paths.item_file("TP-1") == tmp_path / ".taskpilot" / "items" / "TP-1.yaml"
    assert paths.item_file("TP-10") == tmp_path / ".taskpilot" / "items" / "TP-10.yaml"


def test_item_comments_dir_is_named_for_owning_item(tmp_path: Path):
    paths = WorkspacePaths.for_root(tmp_path)

    assert paths.item_comments_dir("TP-1") == (
        tmp_path / ".taskpilot" / "comments" / "TP-1"
    )


def test_comment_file_nests_under_item_comment_dir(tmp_path: Path):
    paths = WorkspacePaths.for_root(tmp_path)

    expected = tmp_path / ".taskpilot" / "comments" / "TP-1" / "2026-06-23T10-00-00Z.md"
    assert paths.comment_file("TP-1", "2026-06-23T10-00-00Z.md") == expected


def test_relative_posix_uses_forward_slashes_regardless_of_platform(tmp_path: Path):
    paths = WorkspacePaths.for_root(tmp_path)

    # Constraint F001: canonical reference paths use "/" separators on all platforms.
    assert paths.relative_posix(paths.item_file("TP-1")) == ".taskpilot/items/TP-1.yaml"
    assert paths.relative_posix(paths.project_file) == ".taskpilot/project.yaml"
    assert (
        paths.relative_posix(paths.comment_file("TP-1", "c.md"))
        == ".taskpilot/comments/TP-1/c.md"
    )


def test_relative_posix_rejects_path_outside_root(tmp_path: Path):
    paths = WorkspacePaths.for_root(tmp_path)

    with pytest.raises(ValueError):
        paths.relative_posix(tmp_path.parent / "elsewhere" / "x.yaml")


def test_exists_reflects_presence_of_workspace_dir(tmp_path: Path):
    paths = WorkspacePaths.for_root(tmp_path)

    assert paths.exists() is False
    paths.workspace_dir.mkdir()
    assert paths.exists() is True


def test_exists_false_when_workspace_path_is_a_file(tmp_path: Path):
    paths = WorkspacePaths.for_root(tmp_path)
    paths.workspace_dir.write_text("not a directory")

    assert paths.exists() is False


@pytest.mark.parametrize("bad_id", ["", "TP/1", "TP\\1", "..", "../TP-1", "TP-1/.."])
def test_item_file_rejects_unsafe_item_ids(tmp_path: Path, bad_id: str):
    paths = WorkspacePaths.for_root(tmp_path)

    with pytest.raises(ValueError):
        paths.item_file(bad_id)


@pytest.mark.parametrize("bad_id", ["", "TP/1", "..", "../TP-1"])
def test_item_comments_dir_rejects_unsafe_item_ids(tmp_path: Path, bad_id: str):
    paths = WorkspacePaths.for_root(tmp_path)

    with pytest.raises(ValueError):
        paths.item_comments_dir(bad_id)


@pytest.mark.parametrize("bad_name", ["", "a/b.md", "..", "../x.md", "sub\\x.md"])
def test_comment_file_rejects_unsafe_filenames(tmp_path: Path, bad_name: str):
    paths = WorkspacePaths.for_root(tmp_path)

    with pytest.raises(ValueError):
        paths.comment_file("TP-1", bad_name)


def test_workspace_paths_is_immutable(tmp_path: Path):
    paths = WorkspacePaths.for_root(tmp_path)

    with pytest.raises((AttributeError, TypeError)):
        paths.root = tmp_path / "other"  # type: ignore[misc]
