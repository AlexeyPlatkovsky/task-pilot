"""Unit tests for the project loader (task F001-T8, F001-R7).

Covers scenario F001-S7: valid items load alongside invalid files, which are
surfaced as findings rather than silently dropped or crashing the loader.
"""

from pathlib import Path

from taskpilot.core.layout import WorkspacePaths
from taskpilot.core.loader import load_project
from taskpilot.core.project import init_workspace

VALID = """\
schema_version: 1
id: {id}
title: {title}
priority: normal
type: task
status: backlog
created_at: 2026-06-23T10:00:00Z
updated_at: 2026-06-23T10:00:00Z
"""


def _init(tmp_path: Path) -> WorkspacePaths:
    init_workspace(
        tmp_path,
        project_id="task-pilot",
        key="TP",
        name="TaskPilot",
        now="2026-06-24T10:00:00Z",
    )
    return WorkspacePaths.for_root(tmp_path)


def _item(paths: WorkspacePaths, item_id: str, title: str = "A title"):
    (paths.items_dir / f"{item_id}.yaml").write_text(
        VALID.format(id=item_id, title=title), encoding="utf-8"
    )


def test_loads_valid_items_and_surfaces_invalid(tmp_path: Path):
    paths = _init(tmp_path)
    for n in range(1, 6):
        _item(paths, f"TP-{n}")
    (paths.items_dir / "TP-6.yaml").write_text(
        "id: TP-6\n  bad: : indent\n", encoding="utf-8"
    )

    loaded = load_project(paths)

    assert [i.id for i in loaded.items] == ["TP-1", "TP-2", "TP-3", "TP-4", "TP-5"]
    assert loaded.ok is False
    assert any(f.path == ".taskpilot/items/TP-6.yaml" for f in loaded.report.findings)


def test_valid_project_loads_cleanly_with_metadata(tmp_path: Path):
    paths = _init(tmp_path)
    _item(paths, "TP-1")

    loaded = load_project(paths)

    assert loaded.ok is True
    assert loaded.project is not None
    assert loaded.project.key == "TP"
    assert [i.id for i in loaded.items] == ["TP-1"]


def test_items_sorted_by_numeric_id(tmp_path: Path):
    paths = _init(tmp_path)
    for item_id in ("TP-10", "TP-2", "TP-1"):
        _item(paths, item_id)

    loaded = load_project(paths)

    assert [i.id for i in loaded.items] == ["TP-1", "TP-2", "TP-10"]


def test_missing_project_yaml_reports_finding(tmp_path: Path):
    paths = WorkspacePaths.for_root(tmp_path)
    paths.items_dir.mkdir(parents=True)

    loaded = load_project(paths)

    assert loaded.project is None
    assert any(f.code == "project_missing" for f in loaded.report.findings)
    assert loaded.ok is False


def test_invalid_project_yaml_reports_finding(tmp_path: Path):
    paths = WorkspacePaths.for_root(tmp_path)
    paths.workspace_dir.mkdir(parents=True)
    paths.project_file.write_text(
        "schema_version: 1\nid: x\n", encoding="utf-8"
    )  # missing key/name

    loaded = load_project(paths)

    assert loaded.project is None
    assert any(f.code == "project_invalid" for f in loaded.report.findings)


def test_empty_workspace_loads_without_items(tmp_path: Path):
    paths = _init(tmp_path)

    loaded = load_project(paths)

    assert loaded.items == []
    assert loaded.ok is True


def test_structurally_valid_items_with_cross_file_errors_still_load(tmp_path: Path):
    # Contract: duplicate-id / id-mismatch items parse and appear in items even
    # though they carry error findings (ok is False). Nothing is silently dropped.
    paths = _init(tmp_path)
    (paths.items_dir / "a.yaml").write_text(
        VALID.format(id="TP-1", title="A"), encoding="utf-8"
    )
    (paths.items_dir / "b.yaml").write_text(
        VALID.format(id="TP-1", title="B"), encoding="utf-8"
    )

    loaded = load_project(paths)

    assert [i.id for i in loaded.items] == ["TP-1", "TP-1"]
    assert loaded.ok is False
    assert any(f.code == "duplicate_id" for f in loaded.report.findings)


def test_non_numeric_ids_sort_without_crashing(tmp_path: Path):
    paths = _init(tmp_path)
    (paths.items_dir / "TP-3.yaml").write_text(
        VALID.format(id="TP-3", title="N"), encoding="utf-8"
    )
    (paths.items_dir / "odd.yaml").write_text(
        VALID.format(id="odd", title="Odd").replace("id: odd", "id: weird-id"),
        encoding="utf-8",
    )

    loaded = load_project(paths)

    # Non-numeric ids sort ahead of numeric ones; no exception raised.
    assert [i.id for i in loaded.items] == ["weird-id", "TP-3"]


def test_loader_does_not_crash_on_only_invalid_items(tmp_path: Path):
    paths = _init(tmp_path)
    (paths.items_dir / "TP-1.yaml").write_text("- not\n- a mapping\n", encoding="utf-8")

    loaded = load_project(paths)

    assert loaded.items == []
    assert loaded.ok is False
