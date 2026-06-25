"""Translate domain errors into CLI stderr output and exit codes (task F003-T1).

Domain services raise :class:`~taskpilot.services.errors.ServiceError` subtypes.
The CLI adapter turns those into an actionable stderr message and the
deterministic exit code from :mod:`taskpilot.cli.exit_codes`:

- :class:`ValidationFailed`, :class:`NotFound`, :class:`ConflictError` are
  caller-correctable -> exit ``1`` (user error);
- any other :class:`ServiceError` is treated as an unexpected internal failure
  -> exit ``2`` (system error).

JSON-mode error envelopes are intentionally out of scope for Alpha (see
``requirements.md`` "Out of Scope"); errors are plain text on stderr in every
mode so the message is never swallowed.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

import typer

from taskpilot.cli import exit_codes
from taskpilot.services.errors import (
    ConflictError,
    NotFound,
    ServiceError,
    ValidationFailed,
)

__all__ = ["service_errors"]

#: Service errors the caller can correct -> user error exit code.
_USER_ERRORS = (ValidationFailed, NotFound, ConflictError)


@contextmanager
def service_errors() -> Iterator[None]:
    """Run a command body, converting service errors to stderr + ``typer.Exit``.

    Wrap the service calls of a command in this context manager. Known
    caller-correctable errors exit ``1``; any other :class:`ServiceError` exits
    ``2``. Non-``ServiceError`` exceptions propagate unchanged.
    """
    try:
        yield
    except _USER_ERRORS as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(exit_codes.EXIT_USER_ERROR) from exc
    except ServiceError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(exit_codes.EXIT_SYSTEM_ERROR) from exc
