"""Per-invocation CLI state carried through Typer's context (task F003-T1).

The root callback stores a :class:`CLIState` on ``ctx.obj`` so every subcommand
can read global options — currently the ``--json`` switch — without re-declaring
them. Subcommands fetch it with :func:`get_state`.
"""

from __future__ import annotations

from dataclasses import dataclass

import typer

__all__ = ["CLIState", "get_state"]


@dataclass
class CLIState:
    """Global options resolved once by the root callback.

    ``json`` selects machine-readable output (F003-R8); ``False`` means
    human-readable output.
    """

    json: bool = False


def get_state(ctx: typer.Context) -> CLIState:
    """Return the :class:`CLIState` for this invocation, creating a default if absent.

    A default is created when a command is exercised without the root callback
    (e.g. some test harnesses), so subcommands never see ``None``.
    """
    if not isinstance(ctx.obj, CLIState):
        ctx.obj = CLIState()
    return ctx.obj
