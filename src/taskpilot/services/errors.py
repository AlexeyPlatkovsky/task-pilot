"""Domain-service error types (feature F002).

Services raise these instead of leaking pydantic ``ValidationError``, ``OSError``,
or other low-level exceptions to adapters. Each error carries a human-readable
message so CLI/API adapters can render a descriptive response (F002-R8).
"""

from __future__ import annotations

__all__ = ["ServiceError", "ValidationFailed", "NotFound", "ConflictError"]


class ServiceError(Exception):
    """Base class for all domain-service errors."""


class ValidationFailed(ServiceError):
    """Operation input failed validation before any file was written (F002-R8)."""


class NotFound(ServiceError):
    """A requested project or item does not exist."""


class ConflictError(ServiceError):
    """The operation conflicts with existing canonical state (e.g. create over an existing project)."""
