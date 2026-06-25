"""Local system registry of known TaskPilot projects (task F003-T2).

The registry is *machine-specific* state (spec ``0002`` "Repository and Registry
Model"): a YAML file in the OS application-data directory that lists every
project root known on this machine, with an ``active`` flag and cached ``key`` /
``name`` for display. It is never committed to a project repository and is not
canonical product data.

Test seam: the directory is resolved by :func:`default_registry_dir`, which
honors the ``TASKPILOT_HOME`` environment variable so tests never touch a real
home directory.
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

from pydantic import BaseModel, ConfigDict, StringConstraints, field_validator
from typing_extensions import Annotated

from taskpilot.core.timestamps import is_canonical_iso, utc_now_iso
from taskpilot.core.yaml_io import dump_yaml, load_yaml

__all__ = [
    "SCHEMA_VERSION",
    "REGISTRY_FILENAME",
    "RegistryEntry",
    "Registry",
    "default_registry_dir",
    "registry_file",
    "load_registry",
    "save_registry",
    "register_project",
    "list_projects",
]

#: Current registry schema version.
SCHEMA_VERSION = 1
#: Registry filename inside the system directory.
REGISTRY_FILENAME = "registry.yaml"

_NonEmptyStr = Annotated[str, StringConstraints(min_length=1)]


class RegistryEntry(BaseModel):
    """One registered project root on this machine.

    ``path`` is an absolute, normalized filesystem path; ``key``/``name`` are
    cached from the project's ``project.yaml`` for display without opening it.
    Field order is the canonical write order (matches spec ``0002``).
    """

    model_config = ConfigDict(extra="forbid")

    id: _NonEmptyStr
    key: _NonEmptyStr
    name: _NonEmptyStr
    path: _NonEmptyStr
    active: bool = True
    registered_at: str

    @field_validator("registered_at")
    @classmethod
    def _check_registered_at(cls, value: str) -> str:
        if not is_canonical_iso(value):
            raise ValueError(
                f"registered_at must be canonical UTC ISO 8601 (YYYY-MM-DDTHH:MM:SSZ): {value!r}"
            )
        return value


class Registry(BaseModel):
    """The whole registry document: a schema version and a list of entries."""

    model_config = ConfigDict(extra="forbid")

    schema_version: int = SCHEMA_VERSION
    projects: list[RegistryEntry] = []


def default_registry_dir() -> Path:
    """Resolve the OS application-data directory that holds the registry.

    ``TASKPILOT_HOME`` overrides everything (used by tests and power users).
    Otherwise: macOS ``~/Library/Application Support/TaskPilot``, Windows
    ``%APPDATA%/TaskPilot``, else ``$XDG_DATA_HOME`` or
    ``~/.local/share/TaskPilot``.
    """
    override = os.environ.get("TASKPILOT_HOME")
    if override:
        return Path(override)
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "TaskPilot"
    if os.name == "nt":
        appdata = os.environ.get("APPDATA")
        return (Path(appdata) if appdata else Path.home()) / "TaskPilot"
    xdg = os.environ.get("XDG_DATA_HOME")
    return (Path(xdg) if xdg else Path.home() / ".local" / "share") / "TaskPilot"


def registry_file(registry_dir: Path) -> Path:
    """Path to the registry YAML file inside ``registry_dir``."""
    return registry_dir / REGISTRY_FILENAME


def load_registry(registry_dir: Path) -> Registry:
    """Load the registry, returning an empty one when the file is absent."""
    path = registry_file(registry_dir)
    if not path.is_file():
        return Registry()
    data = load_yaml(path.read_text(encoding="utf-8"))
    if data is None:
        return Registry()
    return Registry.model_validate(data)


def save_registry(registry_dir: Path, registry: Registry) -> None:
    """Write ``registry`` to disk atomically, creating the directory if needed.

    Serializes first, then publishes via ``os.replace`` so a crash mid-write
    cannot leave a truncated registry.
    """
    registry_dir.mkdir(parents=True, exist_ok=True)
    content = dump_yaml(registry.model_dump()).encode("utf-8")
    fd, tmp = tempfile.mkstemp(
        dir=str(registry_dir), prefix=".registry_", suffix=".tmp"
    )
    try:
        os.write(fd, content)
    except BaseException:
        os.close(fd)
        os.unlink(tmp)
        raise
    os.close(fd)
    try:
        os.replace(tmp, str(registry_file(registry_dir)))
    except BaseException:
        os.unlink(tmp)
        raise


def register_project(
    registry_dir: Path,
    *,
    id: str,
    key: str,
    name: str,
    path: str,
    now: str | None = None,
) -> RegistryEntry:
    """Add the project to the registry, or re-enable/refresh an existing entry.

    Alpha allows only one registered path per ``project.id`` (spec ``0002``): if
    an entry with the same ``id`` exists it is updated in place — ``path``,
    ``key``, ``name`` refreshed and ``active`` set true — preserving the original
    ``registered_at``. Otherwise a new active entry is appended. The stored
    ``path`` is absolute and normalized.
    """
    normalized_path = str(Path(path).resolve())
    registry = load_registry(registry_dir)

    for existing in registry.projects:
        if existing.id == id:
            existing.key = key
            existing.name = name
            existing.path = normalized_path
            existing.active = True
            save_registry(registry_dir, registry)
            return existing

    entry = RegistryEntry(
        id=id,
        key=key,
        name=name,
        path=normalized_path,
        active=True,
        registered_at=now or utc_now_iso(),
    )
    registry.projects.append(entry)
    save_registry(registry_dir, registry)
    return entry


def list_projects(registry_dir: Path) -> list[RegistryEntry]:
    """Return registered projects sorted by name (spec ``0002``: ``project list``
    "sorts by project name").

    ``id`` is a secondary key so the order is total and deterministic (F003-R8)
    even when two projects share a display name.
    """
    return sorted(load_registry(registry_dir).projects, key=lambda e: (e.name, e.id))
