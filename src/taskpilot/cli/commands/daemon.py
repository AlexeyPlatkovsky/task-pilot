"""``taskpilot start|stop|restart|status|logs`` — background daemon lifecycle
(task TP-122, spec ``docs/specs/0005-daemon-lifecycle-commands.md``).

Wraps :mod:`taskpilot.services.daemon` with CLI argument parsing and output
formatting only; process/PID/log logic stays in the service layer (TP-4).
``start`` re-invokes ``taskpilot serve`` as a detached subprocess rather than
duplicating its uvicorn bootstrap.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import typer

from taskpilot.cli import output
from taskpilot.cli.context import get_state
from taskpilot.cli.exit_codes import EXIT_USER_ERROR
from taskpilot.services import daemon
from taskpilot.services.errors import ConflictError, NotFound
from taskpilot.services.registry import default_registry_dir

__all__ = ["register"]

#: Base argv used to launch the server in the background. The trailing
#: ``serve`` subcommand and its options are appended by :func:`start_command`.
#: A module-level list so tests can substitute a lightweight stand-in process.
_SERVER_COMMAND = [sys.executable, "-m", "taskpilot.cli.app"]

_DEFAULT_LOG_LINES = 100


def start_command(
    host: str = typer.Option("127.0.0.1", "--host", help="Host interface to bind."),
    port: int = typer.Option(7152, "--port", help="Port to listen on."),
    workspace: str | None = typer.Option(
        None, "--workspace", help="Validate this workspace root before startup."
    ),
) -> None:
    """Start the server as a background daemon."""
    registry_dir = default_registry_dir()
    command = [*_SERVER_COMMAND, "serve", "--host", host, "--port", str(port)]
    if workspace is not None:
        command.extend(["--workspace", workspace])

    try:
        state = daemon.start_daemon(
            registry_dir, host=host, port=port, workspace=workspace, command=command
        )
    except ConflictError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(EXIT_USER_ERROR)

    typer.echo(f"TaskPilot daemon started (pid {state.pid}) on http://{host}:{port}")


def stop_command() -> None:
    """Stop the running daemon."""
    registry_dir = default_registry_dir()
    try:
        daemon.stop_daemon(registry_dir)
    except NotFound as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(EXIT_USER_ERROR)
    typer.echo("TaskPilot daemon stopped")


def restart_command(
    host: str = typer.Option("127.0.0.1", "--host", help="Host interface to bind."),
    port: int = typer.Option(7152, "--port", help="Port to listen on."),
    workspace: str | None = typer.Option(
        None, "--workspace", help="Validate this workspace root before startup."
    ),
) -> None:
    """Stop the running daemon (if any) and start a new one."""
    registry_dir = default_registry_dir()
    try:
        daemon.stop_daemon(registry_dir)
    except NotFound:
        pass

    command = [*_SERVER_COMMAND, "serve", "--host", host, "--port", str(port)]
    if workspace is not None:
        command.extend(["--workspace", workspace])
    try:
        state = daemon.start_daemon(
            registry_dir, host=host, port=port, workspace=workspace, command=command
        )
    except ConflictError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(EXIT_USER_ERROR)

    typer.echo(f"TaskPilot daemon restarted (pid {state.pid}) on http://{host}:{port}")


def status_command(ctx: typer.Context) -> None:
    """Report whether the daemon is currently running."""
    state_obj = get_state(ctx)
    registry_dir = default_registry_dir()
    state = daemon.read_state(registry_dir)

    if state is None:
        if state_obj.json:
            output.print_json({"running": False})
        else:
            typer.echo("TaskPilot daemon is not running")
        return

    if state_obj.json:
        output.print_json(
            {
                "running": True,
                "pid": state.pid,
                "host": state.host,
                "port": state.port,
                "started_at": state.started_at,
            }
        )
    else:
        typer.echo(
            f"TaskPilot daemon is running (pid {state.pid}) on "
            f"http://{state.host}:{state.port}, started at {state.started_at}"
        )


def logs_command(
    lines: int = typer.Option(
        _DEFAULT_LOG_LINES, "--lines", "-n", help="Number of trailing lines to print."
    ),
    follow: bool = typer.Option(
        False, "--follow", "-f", help="Tail the log file as it grows."
    ),
) -> None:
    """Print the daemon's log output."""
    registry_dir = default_registry_dir()
    path = daemon.log_file(registry_dir)
    if not path.is_file():
        typer.echo("Error: no daemon log file found", err=True)
        raise typer.Exit(EXIT_USER_ERROR)

    _print_tail(path, lines)
    if follow:
        _follow(path)


def _print_tail(path: Path, lines: int) -> None:
    content = path.read_text(encoding="utf-8", errors="replace")
    all_lines = content.splitlines()
    tail = all_lines[-lines:] if lines > 0 else []
    for line in tail:
        typer.echo(line)


def _follow(path: Path) -> None:
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        handle.seek(0, 2)
        try:
            while True:
                line = handle.readline()
                if line:
                    typer.echo(line.rstrip("\n"))
                else:
                    time.sleep(0.5)
        except KeyboardInterrupt:
            pass


def register(app: typer.Typer) -> None:
    """Attach the daemon lifecycle commands to ``app``."""
    app.command("start")(start_command)
    app.command("stop")(stop_command)
    app.command("restart")(restart_command)
    app.command("status")(status_command)
    app.command("logs")(logs_command)
