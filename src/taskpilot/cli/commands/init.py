"""``taskpilot init <path>`` — workspace creation + registration (task F003-T2, F003-R1).

Creates the repository-local ``.taskpilot/`` structure and ``project.yaml`` via
the F002 project service, then adds/enables the project in the local system
registry (spec ``0002`` "Project Initialization"). Identity is derived from the
target folder name and overridable with ``--id`` / ``--key`` / ``--name``.

``init`` is idempotent: re-running it on an already-initialized workspace does
not overwrite canonical identity (the service refuses that) but still re-enables
the project in the registry and reports it as already initialized.
"""

from __future__ import annotations

import re
from pathlib import Path

import typer

from taskpilot.cli import registry
from taskpilot.cli.context import get_state
from taskpilot.cli.errors import service_errors
from taskpilot.cli.output import print_json, print_line
from taskpilot.core.layout import WorkspacePaths
from taskpilot.services import project_service
from taskpilot.services.errors import ConflictError, ValidationFailed

__all__ = ["register", "derive_key"]

_TOKEN_RE = re.compile(r"[A-Za-z0-9]+")


def derive_key(name: str) -> str:
    """Derive a default project key (item-id prefix) from a display ``name``.

    Multi-word names use the uppercased first letter of each token
    (``"Voice Pilot"`` / ``"voice-pilot"`` -> ``"VP"``); a single token is
    uppercased whole (``"voicepilot"`` -> ``"VOICEPILOT"``). Returns ``""`` when
    ``name`` has no alphanumeric characters, so the caller can prompt for ``--key``.
    """
    tokens = _TOKEN_RE.findall(name)
    if not tokens:
        return ""
    if len(tokens) == 1:
        return tokens[0].upper()
    return "".join(token[0] for token in tokens).upper()


def init_command(
    ctx: typer.Context,
    path: str = typer.Argument(".", help="Repository root to initialize (only this folder is inspected)."),
    key: str = typer.Option(None, "--key", help="Project key used as the item-ID prefix. Derived from the folder name if omitted."),
    name: str = typer.Option(None, "--name", help="Project display name. Defaults to the folder name."),
    project_id: str = typer.Option(None, "--id", help="Project id. Derived from the name if omitted."),
) -> None:
    """Initialize a TaskPilot workspace and register the project."""
    state = get_state(ctx)
    target = Path(path).resolve()
    resolved_name = name or target.name
    resolved_key = key or derive_key(resolved_name)
    paths = WorkspacePaths.for_root(target)

    with service_errors():
        if not resolved_key:
            raise ValidationFailed(
                f"Cannot derive a project key from {resolved_name!r}; pass --key"
            )
        try:
            meta = project_service.create_project(
                paths, key=resolved_key, name=resolved_name, project_id=project_id
            )
            created = True
        except ConflictError:
            # Already initialized: keep canonical identity, just re-enable in the registry.
            meta = project_service.read_project(paths)
            created = False

        entry = registry.register_project(
            registry.default_registry_dir(),
            id=meta.id,
            key=meta.key,
            name=meta.name,
            path=str(target),
        )

    if state.json:
        print_json(
            {
                "created": created,
                "workspace": paths.relative_posix(paths.workspace_dir),
                "project": meta.model_dump(),
                "registered": entry.model_dump(),
            }
        )
        return

    if created:
        print_line(f"Initialized TaskPilot workspace at {target / '.taskpilot'}")
    else:
        print_line(f"Workspace already initialized at {target / '.taskpilot'}")
    print_line(f"Registered project {meta.key} ({meta.name}).")


def register(app: typer.Typer) -> None:
    """Attach the ``init`` command to ``app``."""
    app.command("init")(init_command)
