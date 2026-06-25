"""Deterministic CLI exit codes (feature F003).

The CLI contract (``docs/features/F003_cli-interface/requirements.md``) fixes
three exit codes so scripts and AI agents can branch on them reliably:

- ``0`` success;
- ``1`` user error (bad input, not found, conflict — the caller can fix it);
- ``2`` system error (an unexpected failure the caller cannot fix).
"""

from __future__ import annotations

__all__ = ["EXIT_OK", "EXIT_USER_ERROR", "EXIT_SYSTEM_ERROR"]

#: Command completed successfully.
EXIT_OK = 0
#: Caller-correctable error: invalid input, missing item/project, conflict.
EXIT_USER_ERROR = 1
#: Unexpected failure the caller cannot correct (I/O, internal error).
EXIT_SYSTEM_ERROR = 2
