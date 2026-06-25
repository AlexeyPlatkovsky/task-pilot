"""UTC timestamp helpers for canonical TaskPilot data.

Canonical timestamps are UTC ISO 8601 with seconds and a ``Z`` suffix, e.g.
``2026-06-24T10:00:00Z`` (see ``docs/specs/0002``). Comment filenames use the
same instant with ``:`` replaced by ``-`` so they are filesystem-safe and sort
chronologically.
"""

from __future__ import annotations

from datetime import datetime, timezone

__all__ = [
    "utc_now_iso",
    "is_canonical_iso",
    "iso_to_filename_stamp",
    "filename_stamp_to_iso",
]

_ISO_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


def utc_now_iso() -> str:
    """Return the current UTC time as ``YYYY-MM-DDTHH:MM:SSZ`` (seconds precision)."""
    return datetime.now(timezone.utc).strftime(_ISO_FORMAT)


def is_canonical_iso(value: str) -> bool:
    """True when ``value`` is a canonical UTC ISO 8601 timestamp (``...Z``, seconds)."""
    try:
        datetime.strptime(value, _ISO_FORMAT)
    except (ValueError, TypeError):
        return False
    return True


def iso_to_filename_stamp(iso: str) -> str:
    """Convert a canonical ISO timestamp to a filesystem-safe stamp.

    ``2026-06-24T10:00:00Z`` -> ``2026-06-24T10-00-00Z``.
    """
    datetime.strptime(iso, _ISO_FORMAT)  # validate shape
    return iso.replace(":", "-")


def filename_stamp_to_iso(stamp: str) -> str:
    """Inverse of :func:`iso_to_filename_stamp`.

    ``2026-06-24T10-00-00Z`` -> ``2026-06-24T10:00:00Z``.
    """
    date_part, _, time_part = stamp.partition("T")
    iso = f"{date_part}T{time_part.replace('-', ':')}"
    datetime.strptime(iso, _ISO_FORMAT)  # validate shape
    return iso
