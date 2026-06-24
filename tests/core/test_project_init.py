"""Unit tests for workspace initialization (task F001-T2, requirement F001-R1).

Scope is the storage-layer primitive only: creating the .taskpilot/ tree and a
minimal project.yaml, idempotently, without overwriting canonical files. The CLI
command and registry are F003/F002.
"""

import re
from pathlib import Path

import pytest
from pydantic import ValidationError

from taskpilot.core.layout import WorkspacePaths
from taskpilot.core.project import (
    ProjectMeta,
    init_workspace,
    read_project,
    write_project,
)

ISO_Z = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


def _init(tmp_path: Path, **kw):
    defaults = dict(project_id="task-pilot", key="TP", name="TaskPilot")
    defaults.update(kw)
    return init_workspace(tmp_path, **defaults)


def test_init_creates_full_workspace_tree(tmp_path: Path):
    _init(tmp_path)
    paths = WorkspacePaths.for_root(tmp_path)

    assert paths.workspace_dir.is_dir()
    assert paths.items_dir.is_dir()
    assert paths.comments_dir.is_dir()
    assert paths.project_file.is_file()


def test_init_writes_project_identity(tmp_path: Path):
    _init(tmp_path, project_id="task-pilot", key="TP", name="TaskPilot")
    meta = read_project(WorkspacePaths.for_root(tmp_path))

    assert meta.id == "task-pilot"
    assert meta.key == "TP"
    assert meta.name == "TaskPilot"
    assert meta.schema_version == 1
    assert ISO_Z.match(meta.created_at)


def test_project_yaml_has_canonical_field_order(tmp_path: Path):
    _init(tmp_path, now="2026-06-24T10:00:00Z")
    text = WorkspacePaths.for_root(tmp_path).project_file.read_text(encoding="utf-8")

    keys = [line.split(":", 1)[0] for line in text.splitlines() if line and not line.startswith(" ")]
    assert keys == ["schema_version", "id", "key", "name", "created_at"]


def test_created_at_uses_provided_timestamp(tmp_path: Path):
    _init(tmp_path, now="2026-06-24T10:00:00Z")
    meta = read_project(WorkspacePaths.for_root(tmp_path))

    assert meta.created_at == "2026-06-24T10:00:00Z"


def test_init_result_reports_created_state(tmp_path: Path):
    result = _init(tmp_path)

    assert result.created is True
    assert ".taskpilot/project.yaml" in result.created_paths


def test_init_is_idempotent_and_preserves_project_identity(tmp_path: Path):
    _init(tmp_path, project_id="task-pilot", key="TP", name="Original")
    result = _init(tmp_path, project_id="other", key="OT", name="Changed")

    meta = read_project(WorkspacePaths.for_root(tmp_path))
    assert meta.name == "Original"  # not overwritten
    assert meta.id == "task-pilot"
    assert result.created is False
    assert ".taskpilot/project.yaml" in result.existing_paths


def test_init_creates_missing_dirs_without_touching_existing_files(tmp_path: Path):
    paths = WorkspacePaths.for_root(tmp_path)
    paths.items_dir.mkdir(parents=True)
    existing = paths.items_dir / "TP-1.yaml"
    existing.write_text("id: TP-1\n", encoding="utf-8")

    _init(tmp_path)

    assert existing.read_text(encoding="utf-8") == "id: TP-1\n"
    assert paths.comments_dir.is_dir()
    assert paths.project_file.is_file()


@pytest.mark.parametrize("bad", [dict(project_id=""), dict(key=""), dict(name="")])
def test_init_rejects_empty_identity(tmp_path: Path, bad: dict):
    with pytest.raises(ValidationError):
        _init(tmp_path, **bad)


def test_init_rejects_malformed_timestamp(tmp_path: Path):
    with pytest.raises(ValidationError):
        _init(tmp_path, now="not-a-timestamp")


def test_write_then_read_project_round_trips(tmp_path: Path):
    paths = WorkspacePaths.for_root(tmp_path)
    paths.workspace_dir.mkdir()
    meta = ProjectMeta(id="task-pilot", key="TP", name="TaskPilot", created_at="2026-06-24T10:00:00Z")

    write_project(paths, meta)

    assert read_project(paths) == meta
