"""Tests for ``taskpilot update`` in the npm wrapper (spec 0011, TP-140).

The wrapper runs under ``node`` with a stub ``npm`` first on ``PATH``; the stub
records every invocation and answers ``npm view`` / ``npm install`` from
environment variables, so no test touches the network or the real global install.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
WRAPPER = REPO_ROOT / "bin" / "taskpilot"
PACKAGE = "@alexey_platkovsky/taskpilot"
INSTALLED = json.loads((REPO_ROOT / "package.json").read_text(encoding="utf-8"))[
    "version"
]
HINT = f"taskpilot: update manually with: npm install -g {PACKAGE}@latest"

pytestmark = [
    pytest.mark.skipif(sys.platform == "win32", reason="POSIX npm stub"),
    pytest.mark.skipif(shutil.which("node") is None, reason="node is required"),
]

_STUB = """#!/bin/sh
printf '%s\\n' "$*" >> "$NPM_STUB_LOG"
case "$1" in
  view)
    if [ -n "$NPM_STUB_VIEW_FAIL" ]; then
      echo "npm error code ENOTFOUND" >&2
      echo "npm error network request to https://registry.npmjs.org failed" >&2
      echo "npm error A complete log of this run can be found in: /tmp/x-debug-0.log" >&2
      exit 1
    fi
    printf '%s\\n' "$NPM_STUB_LATEST"
    ;;
  install)
    exit "${NPM_STUB_INSTALL_EXIT:-0}"
    ;;
esac
"""


def _bump(version: str, *, part: int, delta: int) -> str:
    numbers = [int(n) for n in version.split(".")]
    numbers[part] += delta
    return ".".join(str(n) for n in numbers)


NEWER = _bump(INSTALLED, part=1, delta=1)


@pytest.fixture
def run(tmp_path: Path):
    stub_dir = tmp_path / "stub-bin"
    stub_dir.mkdir()
    npm = stub_dir / "npm"
    npm.write_text(_STUB, encoding="utf-8")
    npm.chmod(0o755)
    log = tmp_path / "npm-calls.log"

    def _run(*args: str, **stub_env: str):
        wrapper = stub_env.pop("WRAPPER_PATH", str(WRAPPER))
        prefix = [a for a in stub_env.pop("PREFIX_ARGS", "").split() if a]
        env = {
            **os.environ,
            "PATH": f"{stub_dir}{os.pathsep}{os.environ['PATH']}",
            "NPM_STUB_LOG": str(log),
            # Point Python discovery at nothing: update must not need a runtime.
            "TASKPILOT_PYTHON": str(tmp_path / "no-python"),
            **stub_env,
        }
        result = subprocess.run(
            ["node", wrapper, *prefix, "update", *args],
            capture_output=True,
            text=True,
            env=env,
            timeout=60,
        )
        calls = log.read_text(encoding="utf-8").splitlines() if log.exists() else []
        return result, calls

    return _run


def test_check_reports_newer_version_without_installing(run):
    result, calls = run("--check", NPM_STUB_LATEST=NEWER)

    assert result.returncode == 0, result.stderr
    assert (
        f"Update available: {INSTALLED} -> {NEWER}. Run: taskpilot update"
        in result.stdout
    )
    assert calls == [f"view {PACKAGE} version"]


def test_update_installs_exact_latest_version(run):
    result, calls = run(NPM_STUB_LATEST=NEWER)

    assert result.returncode == 0, result.stderr
    assert f"taskpilot: updating {INSTALLED} -> {NEWER}..." in result.stderr
    assert f"taskpilot: updated to {NEWER}" in result.stderr
    assert calls == [
        f"view {PACKAGE} version",
        f"install -g {PACKAGE}@{NEWER}",
    ]


@pytest.mark.parametrize(
    "latest",
    [
        INSTALLED,
        _bump(INSTALLED, part=2, delta=-1)
        if INSTALLED.split(".")[2] != "0"
        else _bump(INSTALLED, part=0, delta=-1),
    ],
    ids=["equal", "older"],
)
@pytest.mark.parametrize("args", [(), ("--check",)], ids=["update", "check"])
def test_up_to_date_does_not_install(run, latest, args):
    result, calls = run(*args, NPM_STUB_LATEST=latest)

    assert result.returncode == 0, result.stderr
    assert f"taskpilot is up to date ({INSTALLED})" in result.stdout
    assert calls == [f"view {PACKAGE} version"]


def test_numeric_comparison_treats_minor_10_as_newer_than_minor_9(run, tmp_path):
    # Run a copy of the wrapper whose package.json says X.9.0, against latest X.10.0.
    major = INSTALLED.split(".")[0]
    copy = tmp_path / "pkg"
    (copy / "bin").mkdir(parents=True)
    shutil.copy(WRAPPER, copy / "bin" / "taskpilot")
    (copy / "package.json").write_text(
        json.dumps({"name": PACKAGE, "version": f"{major}.9.0"}), encoding="utf-8"
    )
    result, calls = run(
        "--check",
        NPM_STUB_LATEST=f"{major}.10.0",
        WRAPPER_PATH=str(copy / "bin" / "taskpilot"),
    )

    assert result.returncode == 0, result.stderr
    assert f"Update available: {major}.9.0 -> {major}.10.0" in result.stdout
    assert calls == [f"view {PACKAGE} version"]


def test_leading_json_flag_still_runs_wrapper_update(run):
    result, calls = run(NPM_STUB_LATEST=INSTALLED, PREFIX_ARGS="--json")

    assert result.returncode == 0, result.stderr
    assert f"taskpilot is up to date ({INSTALLED})" in result.stdout
    assert calls == [f"view {PACKAGE} version"]


@pytest.mark.parametrize(
    "stub_env",
    [{"NPM_STUB_VIEW_FAIL": "1"}, {"NPM_STUB_LATEST": "not-a-version"}],
    ids=["registry-error", "unparseable"],
)
def test_registry_failure_exits_1_with_hint(run, stub_env):
    result, calls = run(**stub_env)

    assert result.returncode == 1
    assert "taskpilot: could not check for updates:" in result.stderr
    assert HINT in result.stderr
    assert "complete log of this run" not in result.stderr
    if "NPM_STUB_VIEW_FAIL" in stub_env:
        assert "code ENOTFOUND: network request" in result.stderr
    assert not any(c.startswith("install") for c in calls)


def test_missing_npm_exits_1_with_hint(tmp_path: Path):
    env = {**os.environ, "PATH": str(tmp_path)}  # no npm anywhere
    node = shutil.which("node")
    assert node is not None
    result = subprocess.run(
        [node, str(WRAPPER), "update"],
        capture_output=True,
        text=True,
        env=env,
        timeout=60,
    )
    assert result.returncode == 1
    assert "taskpilot: could not check for updates:" in result.stderr
    assert HINT in result.stderr


def test_install_failure_exits_1_with_hint(run):
    result, calls = run(NPM_STUB_LATEST=NEWER, NPM_STUB_INSTALL_EXIT="243")

    assert result.returncode == 1
    assert "taskpilot: npm install failed (exit 243)" in result.stderr
    assert HINT in result.stderr
    assert "updated to" not in result.stderr


@pytest.mark.parametrize("args", [("--force",), ("--check", "--check"), ("now",)])
def test_unknown_arguments_print_usage_without_npm(run, args):
    result, calls = run(*args, NPM_STUB_LATEST=NEWER)

    assert result.returncode == 1
    assert "taskpilot: usage: taskpilot update [--check]" in result.stderr
    assert calls == []
