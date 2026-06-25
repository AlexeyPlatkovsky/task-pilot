"""Tests for ``taskpilot project list`` (task F003-T3, requirements F003-R3/R8,
scenario F003-S2).
"""

import json
from pathlib import Path

from typer.testing import CliRunner

from taskpilot.services import registry
from taskpilot.cli.app import app

runner = CliRunner()


def _seed(home: Path, *ids: str) -> None:
    for pid in ids:
        repo = home.parent / pid
        repo.mkdir(exist_ok=True)
        registry.register_project(
            home,
            id=pid,
            key=pid[:2].upper(),
            name=pid.title(),
            path=str(repo),
            now="2026-06-24T10:00:00Z",
        )


def test_project_list_json_returns_array(tmp_path: Path):
    home = tmp_path / "home"
    _seed(home, "vp")
    result = runner.invoke(
        app, ["--json", "project", "list"], env={"TASKPILOT_HOME": str(home)}
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert isinstance(payload, list) and len(payload) == 1
    assert payload[0]["key"] == "VP"
    assert payload[0]["name"] == "Vp"


def test_project_list_json_is_byte_identical(tmp_path: Path):
    home = tmp_path / "home"
    _seed(home, "vp", "tp")
    env = {"TASKPILOT_HOME": str(home)}
    first = runner.invoke(app, ["--json", "project", "list"], env=env)
    second = runner.invoke(app, ["--json", "project", "list"], env=env)
    assert first.output == second.output


def test_project_list_json_sorted_by_name(tmp_path: Path):
    home = tmp_path / "home"
    # _seed sets name = id.title(), so name order matches: Alpha before Zeta.
    _seed(home, "zeta", "alpha")
    result = runner.invoke(
        app, ["--json", "project", "list"], env={"TASKPILOT_HOME": str(home)}
    )
    payload = json.loads(result.output)
    assert [e["name"] for e in payload] == ["Alpha", "Zeta"]


def test_project_list_human_table(tmp_path: Path):
    home = tmp_path / "home"
    _seed(home, "vp")
    result = runner.invoke(app, ["project", "list"], env={"TASKPILOT_HOME": str(home)})
    assert result.exit_code == 0
    assert "KEY" in result.output and "VP" in result.output


def test_project_list_empty(tmp_path: Path):
    home = tmp_path / "home"
    home.mkdir()
    result = runner.invoke(app, ["project", "list"], env={"TASKPILOT_HOME": str(home)})
    assert result.exit_code == 0
    assert "No registered projects" in result.output


def test_project_list_empty_json_is_array(tmp_path: Path):
    home = tmp_path / "home"
    home.mkdir()
    result = runner.invoke(
        app, ["--json", "project", "list"], env={"TASKPILOT_HOME": str(home)}
    )
    assert result.exit_code == 0
    assert json.loads(result.output) == []
