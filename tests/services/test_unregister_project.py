"""Tests for project unregistration (spec 0010 R2, TP-138)."""

from __future__ import annotations

from pathlib import Path

import pytest

from taskpilot.core.layout import WorkspacePaths
from taskpilot.services import project_service, registry, ui_state
from taskpilot.services.errors import NotFound

NOW = "2026-01-01T00:00:00Z"


@pytest.fixture
def home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    home = tmp_path / "home"
    monkeypatch.setenv("TASKPILOT_HOME", str(home))
    return home


def _register(home: Path, tmp_path: Path, pid: str, key: str) -> WorkspacePaths:
    paths = WorkspacePaths.for_root(tmp_path / pid)
    project_service.create_project(paths, key=key, name=pid.title(), now=NOW)
    registry.register_project(
        home, id=pid, key=key, name=pid.title(), path=str(paths.root), now=NOW
    )
    return paths


def _tree(paths: WorkspacePaths) -> dict[str, bytes]:
    return {
        str(p.relative_to(paths.root)): p.read_bytes()
        for p in sorted(paths.workspace_dir.rglob("*"))
        if p.is_file()
    }


def test_registry_unregister_removes_only_that_entry(home, tmp_path):
    _register(home, tmp_path, "alpha", "AL")
    beta = _register(home, tmp_path, "beta", "BE")
    before = _tree(beta)

    removed = registry.unregister_project(home, "beta")

    assert removed.id == "beta"
    assert [e.id for e in registry.list_projects(home)] == ["alpha"]
    assert _tree(beta) == before


def test_registry_unregister_unknown_raises_not_found(home, tmp_path):
    _register(home, tmp_path, "alpha", "AL")
    with pytest.raises(NotFound):
        registry.unregister_project(home, "nope")
    assert [e.id for e in registry.list_projects(home)] == ["alpha"]


def test_service_unregister_resets_matching_last_opened(home, tmp_path):
    _register(home, tmp_path, "alpha", "AL")
    ui_state.save_ui_state(ui_state.UIState(last_opened_project_id="alpha"))

    project_service.unregister_project(home, "alpha")

    assert ui_state.load_ui_state().last_opened_project_id is None


def test_service_unregister_keeps_other_last_opened(home, tmp_path):
    _register(home, tmp_path, "alpha", "AL")
    _register(home, tmp_path, "beta", "BE")
    ui_state.save_ui_state(ui_state.UIState(last_opened_project_id="alpha"))

    project_service.unregister_project(home, "beta")

    assert ui_state.load_ui_state().last_opened_project_id == "alpha"


def test_unregistered_project_can_be_registered_again(home, tmp_path):
    alpha = _register(home, tmp_path, "alpha", "AL")
    registry.unregister_project(home, "alpha")
    registry.register_project(
        home, id="alpha", key="AL", name="Alpha", path=str(alpha.root), now=NOW
    )
    assert [e.id for e in registry.list_projects(home)] == ["alpha"]
