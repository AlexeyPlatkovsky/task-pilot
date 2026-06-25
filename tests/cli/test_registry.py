"""Unit tests for the local system registry (task F003-T2).

The registry is machine-specific state listing known project roots. These tests
use an explicit temp directory (never a real home) and cover add/enable
semantics, the one-entry-per-id rule, and deterministic listing.
"""

from pathlib import Path

from taskpilot.cli import registry


def test_register_adds_entry_and_lists_it(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    entry = registry.register_project(
        tmp_path / "home",
        id="vp",
        key="VP",
        name="VoicePilot",
        path=str(repo),
        now="2026-06-24T10:00:00Z",
    )
    assert entry.active is True
    assert entry.path == str(repo.resolve())

    listed = registry.list_projects(tmp_path / "home")
    assert [e.id for e in listed] == ["vp"]


def test_load_registry_is_empty_when_absent(tmp_path: Path):
    assert registry.list_projects(tmp_path / "missing") == []


def test_register_is_idempotent_per_id(tmp_path: Path):
    home = tmp_path / "home"
    repo = tmp_path / "repo"
    repo.mkdir()
    registry.register_project(
        home,
        id="vp",
        key="VP",
        name="VoicePilot",
        path=str(repo),
        now="2026-06-24T10:00:00Z",
    )
    registry.register_project(
        home,
        id="vp",
        key="VP",
        name="VoicePilot Renamed",
        path=str(repo),
        now="2026-06-25T10:00:00Z",
    )
    listed = registry.list_projects(home)
    assert len(listed) == 1
    # Display fields refresh, but the original registration time is preserved.
    assert listed[0].name == "VoicePilot Renamed"
    assert listed[0].registered_at == "2026-06-24T10:00:00Z"


def test_reregister_reenables_inactive_entry(tmp_path: Path):
    home = tmp_path / "home"
    repo = tmp_path / "repo"
    repo.mkdir()
    registry.register_project(
        home,
        id="vp",
        key="VP",
        name="VoicePilot",
        path=str(repo),
        now="2026-06-24T10:00:00Z",
    )
    reg = registry.load_registry(home)
    reg.projects[0].active = False
    registry.save_registry(home, reg)

    registry.register_project(
        home,
        id="vp",
        key="VP",
        name="VoicePilot",
        path=str(repo),
        now="2026-06-25T10:00:00Z",
    )
    assert registry.list_projects(home)[0].active is True


def test_list_projects_sorted_by_name(tmp_path: Path):
    home = tmp_path / "home"
    # ids and names sort differently so we truly test name ordering (spec 0002).
    for pid, name in [("p1", "Zeta"), ("p2", "Alpha"), ("p3", "Mid")]:
        repo = tmp_path / pid
        repo.mkdir()
        registry.register_project(
            home,
            id=pid,
            key=pid.upper(),
            name=name,
            path=str(repo),
            now="2026-06-24T10:00:00Z",
        )
    assert [e.name for e in registry.list_projects(home)] == ["Alpha", "Mid", "Zeta"]
    assert [e.id for e in registry.list_projects(home)] == ["p2", "p3", "p1"]


def test_save_load_round_trip(tmp_path: Path):
    home = tmp_path / "home"
    repo = tmp_path / "repo"
    repo.mkdir()
    registry.register_project(
        home,
        id="vp",
        key="VP",
        name="VoicePilot",
        path=str(repo),
        now="2026-06-24T10:00:00Z",
    )
    assert registry.registry_file(home).is_file()
    reloaded = registry.load_registry(home)
    assert reloaded.schema_version == registry.SCHEMA_VERSION
    assert reloaded.projects[0].key == "VP"


def test_default_registry_dir_honors_env_override(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("TASKPILOT_HOME", str(tmp_path / "custom"))
    assert registry.default_registry_dir() == tmp_path / "custom"
