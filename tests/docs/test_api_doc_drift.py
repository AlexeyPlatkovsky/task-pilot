"""Guard ``docs/api.md`` against drifting away from the implementation.

The contract doc enumerates four sets of facts: validation finding codes, CLI
commands, CLI option names, and REST endpoints. Hand maintenance let finding-code
coverage rot to 2 of 18 and left ten phantom behaviors in an accepted spec, so
these tests compare the documented sets against source and fail on any divergence
in either direction. The doc stays hand-written; only the enumerations are checked.

Each parser is scoped to its own table so a pattern cannot pick up rows from a
neighbouring section.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from fastapi import FastAPI

REPO_ROOT = Path(__file__).resolve().parents[2]
API_DOC = REPO_ROOT / "docs" / "api.md"


def _doc_text() -> str:
    return API_DOC.read_text(encoding="utf-8")


def _section(text: str, heading: str) -> str:
    """Return the body of the ``##``/``###`` section titled ``heading``.

    Scoping every parser to a single section is what keeps the endpoint table
    from being mistaken for the model table and vice versa.
    """
    pattern = rf"^#{{2,3}} {re.escape(heading)}\s*$"
    match = re.search(pattern, text, re.M)
    assert match is not None, f"docs/api.md is missing a '{heading}' section"
    rest = text[match.end() :]
    next_heading = re.search(r"^#{2,3} ", rest, re.M)
    return rest[: next_heading.start()] if next_heading else rest


# --------------------------------------------------------------------------
# Validation finding codes
# --------------------------------------------------------------------------


def _source_finding_codes() -> set[str]:
    core = (REPO_ROOT / "src" / "taskpilot" / "core" / "validation.py").read_text(
        encoding="utf-8"
    )
    adapter = (
        REPO_ROOT / "src" / "taskpilot" / "server" / "routes" / "projects.py"
    ).read_text(encoding="utf-8")
    return set(re.findall(r'code="([a-z_]+)"', core)) | set(
        re.findall(r'code="([a-z_]+)"', adapter)
    )


def _documented_finding_codes() -> set[str]:
    body = _section(_doc_text(), "Validation finding codes")
    return set(re.findall(r"^\| `([a-z_]+)` \|", body, re.M))


def test_documented_finding_codes_match_source() -> None:
    documented = _documented_finding_codes()
    source = _source_finding_codes()
    assert documented == source, (
        f"docs/api.md finding codes drifted.\n"
        f"  missing from doc: {sorted(source - documented)}\n"
        f"  in doc but not in source: {sorted(documented - source)}"
    )


# --------------------------------------------------------------------------
# REST endpoints
# --------------------------------------------------------------------------


def _source_endpoints() -> set[tuple[str, str]]:
    """Read the published contract from the OpenAPI schema.

    Deliberately not ``app.routes``: this FastAPI version keeps an included
    router as a single ``_IncludedRouter`` entry instead of flattening its
    sub-routes, so walking that list finds no ``/api`` paths at all. The schema
    is also the more honest source — it is what clients actually see, and it
    excludes the ``include_in_schema=False`` SPA fallback.
    """
    from taskpilot.server.app import create_app

    app: FastAPI = create_app(registry_dir=str(REPO_ROOT))
    schema = app.openapi()
    return {
        (method.upper(), path)
        for path, operations in schema["paths"].items()
        for method in operations
    }


def _documented_endpoints() -> set[tuple[str, str]]:
    body = _section(_doc_text(), "REST API")
    return {
        (m.group(1), m.group(2))
        for m in re.finditer(r"^\| `([A-Z]+)` \| `([^`]+)` \|", body, re.M)
    }


def test_documented_endpoints_match_source() -> None:
    documented = _documented_endpoints()
    source = _source_endpoints()
    assert documented == source, (
        f"docs/api.md REST endpoints drifted.\n"
        f"  missing from doc: {sorted(source - documented)}\n"
        f"  in doc but not in source: {sorted(documented - source)}"
    )


# --------------------------------------------------------------------------
# CLI commands and options
# --------------------------------------------------------------------------


def _typer_commands() -> dict[str, set[str]]:
    """Map ``"item list"`` -> the set of its long option names.

    Duck-typed on ``commands`` and ``param_type_name`` rather than using
    ``isinstance`` against ``click``: Typer's ``TyperGroup`` does not subclass
    ``click.Group`` in every supported version, so an isinstance check silently
    treats the root group as a leaf command and finds nothing.
    """
    from typer.main import get_command

    from taskpilot.cli.app import app as cli_app

    root = get_command(cli_app)
    commands: dict[str, set[str]] = {}

    def walk(cmd: object, trail: list[str]) -> None:
        subcommands = getattr(cmd, "commands", None)
        if subcommands:
            for name, sub in subcommands.items():
                walk(sub, [*trail, name])
            return
        opts = {
            opt
            for param in getattr(cmd, "params", [])
            if getattr(param, "param_type_name", "") == "option"
            for opt in getattr(param, "opts", [])
            if opt.startswith("--") and opt != "--help"
        }
        commands[" ".join(trail)] = opts

    walk(root, [])
    commands.pop("", None)  # the root callback itself is not a command
    return commands


def _documented_commands() -> dict[str, set[str]]:
    body = _section(_doc_text(), "Commands")
    commands: dict[str, set[str]] = {}
    for line in body.splitlines():
        match = re.match(r"^\| `taskpilot ([a-z -]+)` \|([^|]*)\|(.*)\|\s*$", line)
        if not match:
            continue
        name = match.group(1).strip()
        opts = set(re.findall(r"`(--[a-z-]+)`", match.group(3)))
        commands[name] = opts
    return commands


def test_documented_cli_commands_match_source() -> None:
    documented = set(_documented_commands())
    source = set(_typer_commands())
    assert documented == source, (
        f"docs/api.md CLI commands drifted.\n"
        f"  missing from doc: {sorted(source - documented)}\n"
        f"  in doc but not in source: {sorted(documented - source)}"
    )


@pytest.mark.parametrize("command", sorted(_typer_commands()))
def test_documented_cli_options_match_source(command: str) -> None:
    documented = _documented_commands().get(command, set())
    source = _typer_commands()[command]
    assert documented == source, (
        f"docs/api.md options for `taskpilot {command}` drifted.\n"
        f"  missing from doc: {sorted(source - documented)}\n"
        f"  in doc but not in source: {sorted(documented - source)}"
    )


def test_global_json_option_is_documented() -> None:
    """``--json`` is a root callback option, so it must precede the subcommand."""
    text = _doc_text()
    assert "taskpilot --json item list" in text
    assert "--json` is a global option" in text
