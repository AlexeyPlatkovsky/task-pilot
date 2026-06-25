"""Project metadata model and workspace initialization (task F001-T2).

This is the storage-layer primitive that lays down the canonical ``.taskpilot/``
tree and a minimal ``project.yaml``. It does not handle the CLI command, the
local project registry, or project-service orchestration (those are F003/F002).
"""

from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from pydantic import BaseModel, ConfigDict, StringConstraints, field_validator
from typing_extensions import Annotated

from taskpilot.core.layout import WorkspacePaths
from taskpilot.core.timestamps import is_canonical_iso, utc_now_iso
from taskpilot.core.yaml_io import dump_yaml, load_yaml

__all__ = [
    "SCHEMA_VERSION",
    "ProjectMeta",
    "InitResult",
    "init_workspace",
    "read_project",
    "write_project",
]

#: Current canonical schema version for project.yaml.
SCHEMA_VERSION = 1


class ProjectMeta(BaseModel):
    """Canonical project identity, persisted as ``.taskpilot/project.yaml``.

    Field declaration order is the canonical write order (see ``docs/specs/0002``
    "Project Metadata").
    """

    model_config = ConfigDict(extra="forbid")

    schema_version: int = SCHEMA_VERSION
    id: Annotated[str, StringConstraints(min_length=1)]
    key: Annotated[str, StringConstraints(min_length=1)]
    name: Annotated[str, StringConstraints(min_length=1)]
    created_at: str

    @field_validator("created_at")
    @classmethod
    def _check_created_at(cls, value: str) -> str:
        if not is_canonical_iso(value):
            raise ValueError(
                f"created_at must be canonical UTC ISO 8601 (YYYY-MM-DDTHH:MM:SSZ): {value!r}"
            )
        return value


@dataclass
class InitResult:
    """Outcome of :func:`init_workspace`.

    ``created`` is True only when a new ``project.yaml`` was written this call.
    Paths are workspace-root-relative POSIX strings.
    """

    workspace_dir: Path
    created: bool
    created_paths: list[str] = field(default_factory=list)
    existing_paths: list[str] = field(default_factory=list)


def write_project(paths: WorkspacePaths, meta: ProjectMeta) -> None:
    """Write ``meta`` to the canonical ``project.yaml`` deterministically.

    Serialization happens first, then the content is written to a temp file in the
    same directory and ``os.replace`` publishes it atomically. A crash or error
    after serialization cannot leave ``project.yaml`` truncated or empty.
    """
    content = dump_yaml(meta.model_dump()).encode("utf-8")
    fd, tmp = tempfile.mkstemp(
        dir=str(paths.workspace_dir), prefix=".project_", suffix=".tmp"
    )
    try:
        os.write(fd, content)
    except BaseException:
        os.close(fd)
        os.unlink(tmp)
        raise
    os.close(fd)
    try:
        os.replace(tmp, str(paths.project_file))
    except BaseException:
        os.unlink(tmp)
        raise


def read_project(paths: WorkspacePaths) -> ProjectMeta:
    """Read and validate ``project.yaml`` into a :class:`ProjectMeta`."""
    data = load_yaml(paths.project_file.read_text(encoding="utf-8"))
    return ProjectMeta.model_validate(data)


def init_workspace(
    root: Path | str,
    *,
    project_id: str,
    key: str,
    name: str,
    now: str | None = None,
) -> InitResult:
    """Create the ``.taskpilot/`` tree under ``root`` without overwriting canonical files.

    Missing directories (``.taskpilot/``, ``items/``, ``comments/``) and a missing
    ``project.yaml`` are created. Existing canonical files are left untouched, so
    re-running init is safe and preserves project identity.
    """
    paths = WorkspacePaths.for_root(root)
    created: list[str] = []
    existing: list[str] = []

    for directory in (paths.workspace_dir, paths.items_dir, paths.comments_dir):
        rel = paths.relative_posix(directory)
        if directory.is_dir():
            existing.append(rel)
        else:
            directory.mkdir(parents=True, exist_ok=True)
            created.append(rel)

    project_rel = paths.relative_posix(paths.project_file)
    project_created = False
    if paths.project_file.exists():
        existing.append(project_rel)
    else:
        meta = ProjectMeta(
            id=project_id,
            key=key,
            name=name,
            created_at=now or utc_now_iso(),
        )
        write_project(paths, meta)
        created.append(project_rel)
        project_created = True

    return InitResult(
        workspace_dir=paths.workspace_dir,
        created=project_created,
        created_paths=created,
        existing_paths=existing,
    )
