"""Project domain service: create, read, list (task F002-T1, requirement F002-R1).

Orchestrates the F001 storage primitives in :mod:`taskpilot.core.project`.
Business rules owned here:

- creating a project over an already-initialized workspace is a conflict;
- the project ``id`` is derived from the display name when not supplied;
- ``read``/``list`` translate "missing or invalid" into domain errors rather
  than leaking storage exceptions.

One repository holds exactly one TaskPilot project (see ``docs/architecture.md``),
so :func:`list_projects` returns the single registered project or an empty list.
"""

from __future__ import annotations

import re

import yaml
from pydantic import ValidationError

from taskpilot.core.layout import WorkspacePaths
from taskpilot.core.project import (
    ProjectMeta,
    init_workspace,
    read_project as _read_project_file,
)
from taskpilot.services.errors import ConflictError, NotFound, ValidationFailed

__all__ = ["create_project", "read_project", "list_projects", "slugify"]

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def slugify(value: str) -> str:
    """Derive a filesystem/identity-safe slug from ``value``.

    Lowercases, replaces runs of non-alphanumeric characters with a single ``-``,
    and trims leading/trailing dashes. ``"Voice Pilot"`` -> ``"voice-pilot"``.
    """
    return _SLUG_RE.sub("-", value.lower()).strip("-")


def create_project(
    paths: WorkspacePaths,
    *,
    key: str,
    name: str,
    project_id: str | None = None,
    now: str | None = None,
) -> ProjectMeta:
    """Create a new project and return its model (F002-R1).

    Writes ``project.yaml`` with the given ``key`` and ``name``. ``project_id``
    defaults to a slug of ``name``. Raises :class:`ValidationFailed` for empty
    identity fields and :class:`ConflictError` when a project already exists.
    """
    if not key or not key.strip():
        raise ValidationFailed("Project key must not be empty")
    if not name or not name.strip():
        raise ValidationFailed("Project name must not be empty")

    if paths.project_file.exists():
        raise ConflictError(
            f"A project already exists at {paths.relative_posix(paths.project_file)}"
        )

    resolved_id = project_id if project_id else slugify(name)
    if not resolved_id:
        raise ValidationFailed(
            f"Cannot derive a project id from name {name!r}; supply project_id"
        )

    result = init_workspace(
        paths.root, project_id=resolved_id, key=key, name=name, now=now
    )
    if not result.created:
        # Lost a race: another writer initialized the project between our check and init.
        raise ConflictError(
            f"A project already exists at {paths.relative_posix(paths.project_file)}"
        )
    return read_project(paths)


def read_project(paths: WorkspacePaths) -> ProjectMeta:
    """Read project metadata (F002-R1).

    Raises :class:`NotFound` when ``project.yaml`` is absent and
    :class:`ValidationFailed` when it exists but is unreadable/invalid.
    """
    if not paths.project_file.exists():
        raise NotFound(
            f"No project found at {paths.relative_posix(paths.project_file)}"
        )
    try:
        return _read_project_file(paths)
    except (ValidationError, yaml.YAMLError, UnicodeDecodeError, OSError) as exc:
        raise ValidationFailed(
            f"Invalid project file {paths.relative_posix(paths.project_file)}: {exc}"
        ) from exc


def list_projects(paths: WorkspacePaths) -> list[ProjectMeta]:
    """List registered projects (F002-R1).

    Returns the single registered project, or an empty list when the workspace
    has no project. (One repository holds one project.)
    """
    if not paths.project_file.exists():
        return []
    return [read_project(paths)]
