"""Archive service: scan, archive, unarchive (feature F009, task TP-110).

Manages the lifecycle of archived items: scanning for eligible items,
moving them to ``.taskpilot/archived/``, and restoring them via unarchive.

Business rules owned here:
- Only items with status ``done``, ``cancelled``, or ``deleted`` are eligible.
- Items are eligible when ``(current_time - updated_at) >= threshold * 86400``.
- Archive operations are idempotent: already-archived items are skipped.
- Source files are moved (not rewritten) to preserve ``updated_at``.
- Invalid (unparseable) items are never archived.
- ``metadata.json`` is the single source of truth for which items are archived.
"""

from __future__ import annotations

import json
import os
import re
import tempfile
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterator

from pydantic import ValidationError

from taskpilot.core.item_io import ItemParseError, parse_item_file
from taskpilot.core.layout import WorkspacePaths
from taskpilot.core.models import Item, ItemStatus
from taskpilot.core.timestamps import is_canonical_iso, utc_now_iso
from taskpilot.services.errors import ConflictError, NotFound, ValidationFailed
from taskpilot.services.item_service import list_items, read_item
from taskpilot.services.project_service import read_project

__all__ = [
    "get_archive_threshold",
    "set_archive_threshold",
    "scan_eligible_items",
    "archive_items",
    "migrate_all_eligible",
    "migrate_legacy_archives",
    "unarchive_item",
    "list_archived_items",
    "read_archived_item",
    "archived_item_file",
    "list_invalid_archived_item_stubs",
    "archived_item_ids",
    "is_archived",
]

#: Minimum allowed archive threshold (days).
_MIN_THRESHOLD = 1
#: Maximum allowed archive threshold (days).
_MAX_THRESHOLD = 3650
#: Directory holding archived item files.
_ARCHIVED_DIRNAME = "archived"
#: Metadata index file tracking archived items.
_METADATA_FILENAME = "metadata.json"
_LOCK_FILENAME = ".archived.lock"
_TRANSACTION_FILENAME = ".transaction.json"
_ARCHIVE_MONTH_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


def _archived_dir(paths: WorkspacePaths) -> Path:
    """Path to the ``.taskpilot/archived/`` directory."""
    return paths.workspace_dir / _ARCHIVED_DIRNAME


def _metadata_file(paths: WorkspacePaths, month: str | None = None) -> Path:
    """Return a metadata path (root is the compatible legacy location)."""
    if month is None:
        return _archived_dir(paths) / _METADATA_FILENAME
    _validate_archive_month(month)
    return _archived_dir(paths) / month / _METADATA_FILENAME


def _validate_archive_month(month: str) -> None:
    if not _ARCHIVE_MONTH_RE.fullmatch(month):
        raise ValidationFailed(f"Invalid archive month {month!r}")


def _archive_month(archived_at: str) -> str:
    """Return the UTC calendar month that canonically owns an archive entry."""
    if not is_canonical_iso(archived_at):
        raise ValidationFailed("Archive metadata has an invalid archived_at timestamp")
    return archived_at[:7]


def _metadata_path_for_entry(paths: WorkspacePaths, entry: dict) -> Path:
    archived_at = entry.get("archived_at")
    if not isinstance(archived_at, str):
        raise ValidationFailed("Archive metadata has an invalid archived_at timestamp")
    return _metadata_file(paths, _archive_month(archived_at))


def _archive_file(
    paths: WorkspacePaths,
    item_id: str,
    entry: dict,
    metadata_path: Path | None = None,
) -> Path:
    """Return the existing archive file, preferring the entry's month location."""
    monthly = _metadata_path_for_entry(paths, entry).parent / f"{item_id}.yaml"
    legacy = _archived_dir(paths) / f"{item_id}.yaml"
    if metadata_path is not None:
        candidate = metadata_path.parent / f"{item_id}.yaml"
        if candidate.exists():
            return candidate
    if monthly.exists():
        return monthly
    if legacy.exists():
        return legacy
    return monthly


def _transaction_file(paths: WorkspacePaths) -> Path:
    """Path to the transient archive recovery journal."""
    return _archived_dir(paths) / _TRANSACTION_FILENAME


@contextmanager
def _archive_lock(paths: WorkspacePaths) -> Iterator[None]:
    """Serialize archive mutations across processes on Unix and Windows."""
    _ensure_archived_dir(paths)
    lock_path = _archived_dir(paths) / _LOCK_FILENAME
    with lock_path.open("a+b") as lock_file:
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(lock_file.fileno(), msvcrt.LK_LOCK, 1)
            try:
                yield
            finally:
                lock_file.seek(0)
                msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def _ensure_archived_dir(paths: WorkspacePaths) -> None:
    """Create the ``.taskpilot/archived/`` directory if it does not exist."""
    _archived_dir(paths).mkdir(parents=True, exist_ok=True)


def _load_metadata_file(meta_path: Path) -> dict:
    """Load one metadata document, treating missing/corrupt data as unavailable."""
    if not meta_path.exists():
        return {}
    try:
        text = meta_path.read_text(encoding="utf-8")
        metadata = json.loads(text)
        return metadata if isinstance(metadata, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def _metadata_locations(paths: WorkspacePaths) -> list[Path]:
    """Return compatible metadata locations in deterministic priority order."""
    root = _archived_dir(paths)
    locations: list[Path] = []
    legacy = _metadata_file(paths)
    if legacy.exists():
        locations.append(legacy)
    if root.exists():
        locations.extend(
            directory / _METADATA_FILENAME
            for directory in sorted(root.iterdir(), key=lambda path: path.name)
            if directory.is_dir()
            and _ARCHIVE_MONTH_RE.fullmatch(directory.name)
            and (directory / _METADATA_FILENAME).exists()
        )
    return locations


def _metadata_records(paths: WorkspacePaths) -> dict[str, tuple[dict, Path]]:
    """Aggregate legacy and monthly metadata; monthly entries win partial migrations."""
    records: dict[str, tuple[dict, Path]] = {}
    for meta_path in _metadata_locations(paths):
        for item_id, entry in _load_metadata_file(meta_path).items():
            if isinstance(item_id, str) and isinstance(entry, dict):
                records[item_id] = (entry, meta_path)
    return {item_id: records[item_id] for item_id in sorted(records)}


def _load_metadata(paths: WorkspacePaths) -> dict:
    """Return all compatible archive metadata in deterministic item-ID order."""
    return {
        item_id: entry
        for item_id, (entry, _meta_path) in _metadata_records(paths).items()
    }


def _write_metadata_file(meta_path: Path, metadata: dict) -> None:
    """Atomically save one metadata document."""
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    content = (json.dumps(metadata, indent=2, sort_keys=True) + "\n").encode("utf-8")
    fd, tmp = tempfile.mkstemp(
        dir=str(meta_path.parent), prefix=".metadata_", suffix=".tmp"
    )
    try:
        os.write(fd, content)
    finally:
        os.close(fd)
    try:
        os.replace(tmp, meta_path)
    except BaseException:
        os.unlink(tmp)
        raise


def _save_metadata(paths: WorkspacePaths, metadata: dict) -> None:
    """Save a single month metadata document (legacy compatibility helper)."""
    if not metadata:
        _metadata_file(paths).unlink(missing_ok=True)
        return
    months = {
        _archive_month(entry["archived_at"])
        for entry in metadata.values()
        if isinstance(entry, dict) and isinstance(entry.get("archived_at"), str)
    }
    if len(months) != 1:
        _write_metadata_file(_metadata_file(paths), metadata)
        return
    _write_metadata_file(_metadata_file(paths, months.pop()), metadata)


def _save_transaction(paths: WorkspacePaths, transaction: dict) -> None:
    """Persist a recovery intent before relocating an item file."""
    _ensure_archived_dir(paths)
    target = _transaction_file(paths)
    content = (json.dumps(transaction, indent=2, sort_keys=True) + "\n").encode("utf-8")
    fd, tmp = tempfile.mkstemp(
        dir=str(target.parent), prefix=".transaction_", suffix=".tmp"
    )
    try:
        os.write(fd, content)
    finally:
        os.close(fd)
    try:
        os.replace(tmp, target)
    except BaseException:
        os.unlink(tmp)
        raise


def _clear_transaction(paths: WorkspacePaths) -> None:
    _transaction_file(paths).unlink(missing_ok=True)


def _load_transaction(paths: WorkspacePaths) -> dict | None:
    target = _transaction_file(paths)
    if not target.exists():
        return None
    try:
        return json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationFailed("Archive transaction journal is unreadable") from exc


def _publish_metadata(paths: WorkspacePaths, metadata: dict) -> None:
    if metadata:
        _save_metadata(paths, metadata)
    else:
        _metadata_file(paths).unlink(missing_ok=True)


def _publish_metadata_at(
    paths: WorkspacePaths, metadata: dict, meta_path: Path
) -> None:
    """Publish metadata at a known location, preserving legacy journal compatibility."""
    if not metadata:
        meta_path.unlink(missing_ok=True)
    elif meta_path == _metadata_file(paths):
        _write_metadata_file(meta_path, metadata)
    else:
        _publish_metadata(paths, metadata)


def _recover_transaction_locked(paths: WorkspacePaths) -> None:
    transaction = _load_transaction(paths)
    if transaction is None:
        return
    operation = transaction.get("operation")
    item_id = transaction.get("item_id")
    metadata_entry = transaction.get("metadata")
    if operation not in {"archive", "unarchive"} or not isinstance(item_id, str):
        raise ValidationFailed("Archive transaction journal has invalid content")
    if not isinstance(metadata_entry, dict):
        raise ValidationFailed("Archive transaction journal has invalid content")
    if metadata_entry.get("original_id") != item_id:
        raise ValidationFailed("Archive transaction journal has invalid content")
    project_key = metadata_entry.get("project_key")
    archived_at = metadata_entry.get("archived_at")
    original_status = metadata_entry.get("original_status")
    if (
        not isinstance(project_key, str)
        or not project_key
        or not isinstance(archived_at, str)
        or not is_canonical_iso(archived_at)
        or not isinstance(original_status, str)
    ):
        raise ValidationFailed("Archive transaction journal has invalid content")
    try:
        ItemStatus(original_status)
    except ValueError as exc:
        raise ValidationFailed(
            "Archive transaction journal has invalid content"
        ) from exc
    archive_month = transaction.get("archive_month")
    if archive_month is None:
        metadata_path = _metadata_file(paths)
        archived = _archived_dir(paths) / f"{item_id}.yaml"
    elif isinstance(archive_month, str):
        _validate_archive_month(archive_month)
        if archive_month != _archive_month(archived_at):
            raise ValidationFailed("Archive transaction journal has invalid content")
        metadata_path = _metadata_file(paths, archive_month)
        archived = metadata_path.parent / f"{item_id}.yaml"
    else:
        raise ValidationFailed("Archive transaction journal has invalid content")
    active = paths.item_file(item_id)
    metadata = _load_metadata_file(metadata_path)
    if operation == "archive":
        if active.exists() and archived.exists():
            raise ConflictError(
                f"Cannot recover archive for {item_id!r}: both files exist"
            )
        if active.exists():
            archived.parent.mkdir(parents=True, exist_ok=True)
            os.replace(active, archived)
        elif not archived.exists():
            raise NotFound(
                f"Cannot recover archive for {item_id!r}: item file is missing"
            )
        metadata[item_id] = metadata_entry
    else:
        if active.exists() and archived.exists():
            raise ConflictError(
                f"Cannot recover unarchive for {item_id!r}: both files exist"
            )
        if archived.exists():
            active.parent.mkdir(parents=True, exist_ok=True)
            os.replace(archived, active)
        elif not active.exists():
            raise NotFound(
                f"Cannot recover unarchive for {item_id!r}: item file is missing"
            )
        metadata.pop(item_id, None)
    _publish_metadata_at(paths, metadata, metadata_path)
    _clear_transaction(paths)


def get_archive_threshold(paths: WorkspacePaths) -> int:
    """Read ``archive_threshold_days`` from ``project.yaml``, defaulting to 14.

    Returns the integer threshold in days.
    """
    project = read_project(paths)
    return getattr(project, "archive_threshold_days", 14)


def set_archive_threshold(paths: WorkspacePaths, threshold: int) -> int:
    """Validate and set ``archive_threshold_days`` in ``project.yaml``.

    Raises :class:`ValidationFailed` when ``threshold`` is outside 1-3650.
    Returns the new threshold.
    """
    if (
        isinstance(threshold, bool)
        or not isinstance(threshold, int)
        or threshold < _MIN_THRESHOLD
        or threshold > _MAX_THRESHOLD
    ):
        raise ValidationFailed(
            f"archive_threshold_days must be between {_MIN_THRESHOLD} and {_MAX_THRESHOLD}, got {threshold}"
        )
    project = read_project(paths)
    project.archive_threshold_days = threshold
    from taskpilot.core.project import write_project

    write_project(paths, project)
    return threshold


def _is_eligible(item: Item, paths: WorkspacePaths, now: str) -> bool:
    """Check if an item is eligible for archiving.

    An item is eligible when:
    - Its status is ``done``, ``cancelled``, or ``deleted``.
    - Its ``updated_at`` exceeds the threshold (14 days by default).
    """
    if item.status not in (ItemStatus.done, ItemStatus.cancelled, ItemStatus.deleted):
        return False
    threshold = get_archive_threshold(paths)
    # Parse timestamps and check age
    updated = datetime.fromisoformat(item.updated_at.replace("Z", "+00:00"))
    current = datetime.fromisoformat(now.replace("Z", "+00:00"))
    age_seconds = (current - updated).total_seconds()
    return age_seconds >= threshold * 86400


def scan_eligible_items(paths: WorkspacePaths, now: str | None = None) -> list[Item]:
    """Return all items with status done/cancelled/deleted whose ``updated_at``
    exceeds the threshold, excluding already-archived items.

    Raises :class:`NotFound` when no project exists.
    """
    project = read_project(paths)  # raises NotFound when absent
    current = now or utc_now_iso()
    metadata = _load_metadata(paths)
    archived_ids = set(metadata.keys())

    items = list_items(paths, project=project.key, include_deleted=True)
    eligible: list[Item] = []
    for item in items:
        if item.id in archived_ids:
            continue
        if _is_eligible(item, paths, current):
            eligible.append(item)
    return eligible


def archive_items(
    paths: WorkspacePaths, item_ids: list[str], now: str | None = None
) -> list[str]:
    """Move the specified items to their archive month and return their IDs.

    Idempotent: already-archived items are skipped.
    Invalid (unparseable) items are never archived.
    """
    current = now or utc_now_iso()
    project = read_project(paths)
    with _archive_lock(paths):
        _recover_transaction_locked(paths)
        metadata = _load_metadata(paths)
        archived_ids: list[str] = []
        for item_id in item_ids:
            if item_id in metadata:
                continue
            try:
                item = read_item(paths, item_id)
            except (NotFound, ValidationFailed):
                continue
            if not _is_eligible(item, paths, current):
                continue
            src = paths.item_file(item_id)
            if not src.exists():
                continue
            entry = {
                "original_id": item_id,
                "project_key": project.key,
                "archived_at": current,
                "original_status": item.status,
            }
            archive_month = _archive_month(current)
            metadata_path = _metadata_file(paths, archive_month)
            dst = metadata_path.parent / f"{item_id}.yaml"
            _save_transaction(
                paths,
                {
                    "operation": "archive",
                    "item_id": item_id,
                    "archive_month": archive_month,
                    "metadata": entry,
                },
            )
            dst.parent.mkdir(parents=True, exist_ok=True)
            os.replace(src, dst)
            month_metadata = _load_metadata_file(metadata_path)
            month_metadata[item_id] = entry
            _publish_metadata_at(paths, month_metadata, metadata_path)
            _clear_transaction(paths)
            metadata[item_id] = entry
            archived_ids.append(item_id)
        return archived_ids


def migrate_all_eligible(paths: WorkspacePaths, now: str | None = None) -> list[str]:
    """Scan all eligible items (including those still in ``items/``) and
    archive them. Returns the list of archived item IDs.
    """
    eligible = scan_eligible_items(paths, now)
    item_ids = [item.id for item in eligible]
    return archive_items(paths, item_ids, now)


def migrate_legacy_archives(paths: WorkspacePaths) -> list[str]:
    """Idempotently move compatible root-level archive data into month shards.

    Root metadata remains authoritative for a legacy entry until both the YAML file
    and the destination month metadata have been published. This makes a retry safe
    after either interruption point without rewriting YAML bytes.
    """
    with _archive_lock(paths):
        _recover_transaction_locked(paths)
        legacy_path = _metadata_file(paths)
        legacy_metadata = _load_metadata_file(legacy_path)
        migrated_ids: list[str] = []
        for item_id in sorted(legacy_metadata):
            entry = legacy_metadata[item_id]
            if not isinstance(entry, dict) or entry.get("original_id") != item_id:
                raise ValidationFailed("Legacy archive metadata has invalid content")
            metadata_path = _metadata_path_for_entry(paths, entry)
            dst = metadata_path.parent / f"{item_id}.yaml"
            src = _archived_dir(paths) / f"{item_id}.yaml"
            month_metadata = _load_metadata_file(metadata_path)
            existing_entry = month_metadata.get(item_id)
            if existing_entry is not None and existing_entry != entry:
                raise ConflictError(
                    f"Cannot migrate {item_id!r}: month metadata conflicts with legacy metadata"
                )
            if src.exists() and dst.exists():
                if src.read_bytes() != dst.read_bytes():
                    raise ConflictError(
                        f"Cannot migrate {item_id!r}: legacy and month files conflict"
                    )
                src.unlink()
            elif src.exists():
                dst.parent.mkdir(parents=True, exist_ok=True)
                os.replace(src, dst)
            elif not dst.exists():
                raise NotFound(f"Legacy archived file for {item_id!r} not found")
            month_metadata[item_id] = entry
            _write_metadata_file(metadata_path, month_metadata)
            del legacy_metadata[item_id]
            migrated_ids.append(item_id)
        if legacy_metadata:
            _write_metadata_file(legacy_path, legacy_metadata)
        else:
            legacy_path.unlink(missing_ok=True)
        return migrated_ids


def unarchive_item(paths: WorkspacePaths, item_id: str, now: str | None = None) -> Item:
    """Move an archived item from ``.taskpilot/archived/`` back to
    ``.taskpilot/items/``, update ``metadata.json``, and return the
    restored item.

    Raises :class:`NotFound` when the item is not archived and
    :class:`ConflictError` when the active item file already exists.
    """
    with _archive_lock(paths):
        _recover_transaction_locked(paths)
        records = _metadata_records(paths)
        record = records.get(item_id)
        if record is None:
            raise NotFound(f"Item {item_id!r} is not archived")
        entry, metadata_path = record
        src = _archive_file(paths, item_id, entry, metadata_path)
        if not src.exists():
            raise NotFound(f"Archived file for {item_id!r} not found")
        dst = paths.item_file(item_id)
        if dst.exists():
            raise ConflictError(
                f"Cannot unarchive {item_id!r}: active item file already exists"
            )
        _save_transaction(
            paths,
            {
                "operation": "unarchive",
                "item_id": item_id,
                "archive_month": (
                    None
                    if metadata_path == _metadata_file(paths)
                    else metadata_path.parent.name
                ),
                "metadata": entry,
            },
        )
        dst.parent.mkdir(parents=True, exist_ok=True)
        os.replace(src, dst)
        metadata = _load_metadata_file(metadata_path)
        metadata.pop(item_id, None)
        _publish_metadata_at(paths, metadata, metadata_path)
        _clear_transaction(paths)
        return read_item(paths, item_id)


def archived_item_file(paths: WorkspacePaths, item_id: str) -> Path:
    """Return an archived item's metadata-backed canonical YAML path."""
    record = _metadata_records(paths).get(item_id)
    if record is None:
        raise NotFound(f"Item {item_id!r} is not archived")
    entry, metadata_path = record
    src = _archive_file(paths, item_id, entry, metadata_path)
    if not src.is_file():
        raise NotFound(f"Archived file for {item_id!r} not found")
    return src


def read_archived_item(paths: WorkspacePaths, item_id: str) -> Item:
    """Read one archived item, preserving malformed canonical data as an error."""
    src = archived_item_file(paths, item_id)
    try:
        return parse_item_file(src)
    except (ItemParseError, ValidationError, UnicodeDecodeError, OSError) as exc:
        raise ValidationFailed(
            f"Invalid archived item file for {item_id!r}: {exc}"
        ) from exc


def list_archived_items(paths: WorkspacePaths) -> list[Item]:
    """Load valid archived items from every metadata location in ID order."""
    items: list[Item] = []
    for item_id in archived_item_ids(paths):
        try:
            items.append(read_archived_item(paths, item_id))
        except (NotFound, ValidationFailed):
            continue
    return items


def list_invalid_archived_item_stubs(
    paths: WorkspacePaths, *, project: str | None = None
) -> list[tuple[str, str, str]]:
    """Return metadata-backed archived items that cannot be parsed for API visibility."""
    result: list[tuple[str, str, str]] = []
    for item_id in archived_item_ids(paths):
        if project is not None and not item_id.startswith(f"{project}-"):
            continue
        try:
            read_archived_item(paths, item_id)
        except ValidationFailed as exc:
            try:
                rel = paths.relative_posix(archived_item_file(paths, item_id))
            except NotFound:
                continue
            result.append((item_id, rel, str(exc)))
        except NotFound:
            continue
    return result


def archived_item_ids(paths: WorkspacePaths) -> list[str]:
    """Return every item ID reserved by archive metadata in stable order.

    This deliberately does not parse archived YAML files: even an invalid archived
    file reserves its ID and must not allow a later allocation to reuse it.
    """
    return sorted(_load_metadata(paths))


def is_archived(paths: WorkspacePaths, item_id: str) -> bool:
    """Check ``metadata.json`` for the item ID."""
    metadata = _load_metadata(paths)
    return item_id in metadata
