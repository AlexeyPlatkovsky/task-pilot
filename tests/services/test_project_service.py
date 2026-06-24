"""Unit tests for the project service (task F002-T1, requirement F002-R1).

The project service is the domain-layer entry point for project create/read/list.
It orchestrates the F001 storage primitives and owns business rules such as
"creating over an existing project is a conflict" and id derivation.
"""

from pathlib import Path

import pytest

from taskpilot.core.layout import WorkspacePaths
from taskpilot.core.project import ProjectMeta
from taskpilot.services.errors import ConflictError, NotFound
from taskpilot.services import project_service


def _paths(tmp_path: Path) -> WorkspacePaths:
    return WorkspacePaths.for_root(tmp_path)


def test_create_project_writes_values_and_returns_model(tmp_path: Path):
    paths = _paths(tmp_path)

    meta = project_service.create_project(paths, key="VP", name="VoicePilot", now="2026-06-24T10:00:00Z")

    assert isinstance(meta, ProjectMeta)
    assert meta.name == "VoicePilot"
    assert meta.key == "VP"
    # project.yaml on disk reflects the same values
    on_disk = project_service.read_project(paths)
    assert on_disk.name == "VoicePilot"
    assert on_disk.key == "VP"


def test_create_project_derives_id_from_name(tmp_path: Path):
    meta = project_service.create_project(_paths(tmp_path), key="VP", name="Voice Pilot")
    assert meta.id == "voice-pilot"


def test_create_project_honors_explicit_id(tmp_path: Path):
    meta = project_service.create_project(_paths(tmp_path), key="VP", name="VoicePilot", project_id="vp-core")
    assert meta.id == "vp-core"


def test_create_project_conflicts_when_already_exists(tmp_path: Path):
    paths = _paths(tmp_path)
    project_service.create_project(paths, key="VP", name="VoicePilot")

    with pytest.raises(ConflictError):
        project_service.create_project(paths, key="OT", name="Other")

    # original is preserved
    assert project_service.read_project(paths).name == "VoicePilot"


def test_read_project_raises_not_found_when_absent(tmp_path: Path):
    with pytest.raises(NotFound):
        project_service.read_project(_paths(tmp_path))


def test_list_projects_returns_single_registered_project(tmp_path: Path):
    paths = _paths(tmp_path)
    project_service.create_project(paths, key="VP", name="VoicePilot")

    projects = project_service.list_projects(paths)

    assert [p.key for p in projects] == ["VP"]


def test_list_projects_empty_when_uninitialized(tmp_path: Path):
    assert project_service.list_projects(_paths(tmp_path)) == []


@pytest.mark.parametrize("bad", [dict(key="", name="X"), dict(key="VP", name="")])
def test_create_project_rejects_empty_identity(tmp_path: Path, bad: dict):
    from taskpilot.services.errors import ValidationFailed

    with pytest.raises(ValidationFailed):
        project_service.create_project(_paths(tmp_path), **bad)
