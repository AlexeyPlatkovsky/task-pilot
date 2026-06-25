"""Tests for ``taskpilot init`` (task F003-T2, requirement F003-R1, scenario F003-S1).

Exercise the command end-to-end through Typer's runner with an isolated registry
home (``TASKPILOT_HOME``) and a temp target repository.
"""

import json
from pathlib import Path

from typer.testing import CliRunner

from taskpilot.services import registry
from taskpilot.cli.app import app
from taskpilot.cli.commands.init import derive_key

runner = CliRunner()


def _env(home: Path) -> dict:
    return {"TASKPILOT_HOME": str(home)}


# --- key derivation ----------------------------------------------------------


def test_derive_key_multiword_uses_initials():
    assert derive_key("Voice Pilot") == "VP"
    assert derive_key("task-pilot") == "TP"


def test_derive_key_single_word_uppercased():
    assert derive_key("voicepilot") == "VOICEPILOT"


def test_derive_key_empty_when_no_alphanumerics():
    assert derive_key("___") == ""


# --- init command ------------------------------------------------------------


def test_init_creates_workspace_and_registers(tmp_path: Path):
    repo = tmp_path / "voice-pilot"
    repo.mkdir()
    home = tmp_path / "home"

    result = runner.invoke(app, ["init", str(repo)], env=_env(home))

    assert result.exit_code == 0, result.output
    assert (repo / ".taskpilot" / "project.yaml").is_file()
    assert (repo / ".taskpilot" / "items").is_dir()
    assert "Initialized" in result.output
    entries = registry.list_projects(home)
    assert len(entries) == 1
    assert entries[0].key == "VP"
    assert entries[0].path == str(repo.resolve())
    assert entries[0].active is True


def test_init_honors_overrides(tmp_path: Path):
    repo = tmp_path / "whatever"
    repo.mkdir()
    home = tmp_path / "home"

    result = runner.invoke(
        app,
        ["init", str(repo), "--key", "ZZ", "--name", "Zeta", "--id", "zeta-proj"],
        env=_env(home),
    )
    assert result.exit_code == 0, result.output
    entry = registry.list_projects(home)[0]
    assert (entry.id, entry.key, entry.name) == ("zeta-proj", "ZZ", "Zeta")


def test_init_json_output(tmp_path: Path):
    repo = tmp_path / "voice-pilot"
    repo.mkdir()
    home = tmp_path / "home"

    result = runner.invoke(app, ["--json", "init", str(repo)], env=_env(home))
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["created"] is True
    assert payload["project"]["key"] == "VP"
    assert payload["registered"]["active"] is True


def test_init_is_idempotent(tmp_path: Path):
    repo = tmp_path / "voice-pilot"
    repo.mkdir()
    home = tmp_path / "home"

    first = runner.invoke(app, ["init", str(repo)], env=_env(home))
    assert first.exit_code == 0
    second = runner.invoke(app, ["init", str(repo)], env=_env(home))

    assert second.exit_code == 0, second.output
    assert "already initialized" in second.output.lower()
    # No duplicate registry entry, still active.
    entries = registry.list_projects(home)
    assert len(entries) == 1
    assert entries[0].active is True


def test_init_preserves_existing_files(tmp_path: Path):
    repo = tmp_path / "voice-pilot"
    repo.mkdir()
    keep = repo / "README.md"
    keep.write_text("keep me", encoding="utf-8")
    home = tmp_path / "home"

    result = runner.invoke(app, ["init", str(repo)], env=_env(home))
    assert result.exit_code == 0
    assert keep.read_text(encoding="utf-8") == "keep me"
