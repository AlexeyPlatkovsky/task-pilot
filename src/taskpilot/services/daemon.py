"""Background daemon lifecycle for the local server (task TP-122, spec ``0005``).

Tracks a single background server process per machine via a PID file under the
registry directory (:func:`taskpilot.services.registry.default_registry_dir`),
mirroring that module's framing of daemon state as disposable, machine-local
data rather than canonical project data. Process spawn/liveness/termination is
stdlib-only and branches on ``os.name`` (no ``psutil`` dependency), matching the
precedent already set by ``services/registry.py``'s file-locking code.
"""

from __future__ import annotations

import os
import signal
import subprocess
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Sequence

import yaml
from pydantic import BaseModel, ConfigDict, ValidationError

from taskpilot.core.timestamps import utc_now_iso
from taskpilot.core.yaml_io import dump_yaml, load_yaml
from taskpilot.services.errors import ConflictError, NotFound

__all__ = [
    "PID_FILENAME",
    "LOG_FILENAME",
    "DaemonState",
    "pid_file",
    "log_file",
    "write_state",
    "read_state",
    "is_alive",
    "start_daemon",
    "stop_daemon",
]

#: PID file name inside the registry directory.
PID_FILENAME = "daemon.pid"
#: Log file name inside the registry directory.
LOG_FILENAME = "daemon.log"
_LOCK_FILENAME = ".daemon.lock"

#: How long to wait for a terminated process to actually exit before giving up.
_STOP_TIMEOUT_SECONDS = 5.0
_STOP_POLL_INTERVAL_SECONDS = 0.05


class DaemonState(BaseModel):
    """Recorded state of the running background daemon."""

    model_config = ConfigDict(extra="forbid")

    pid: int
    host: str
    port: int
    started_at: str


def pid_file(registry_dir: Path) -> Path:
    """Path to the daemon PID file inside ``registry_dir``."""
    return registry_dir / PID_FILENAME


def log_file(registry_dir: Path) -> Path:
    """Path to the daemon log file inside ``registry_dir``."""
    return registry_dir / LOG_FILENAME


@contextmanager
def _daemon_lock(registry_dir: Path) -> Iterator[None]:
    """Serialize start/stop across processes (mirrors ``services/registry.py``).

    Closes the read-check-then-spawn window in :func:`start_daemon`: without
    this, two concurrent ``taskpilot start`` invocations could both observe no
    existing daemon and both spawn one, orphaning the first.
    """
    registry_dir.mkdir(parents=True, exist_ok=True)
    lock_path = registry_dir / _LOCK_FILENAME
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


def write_state(registry_dir: Path, state: DaemonState) -> None:
    """Write ``state`` to the PID file atomically, creating ``registry_dir`` if needed.

    Serializes first, then publishes via ``os.replace`` so a crash mid-write
    cannot leave a partial file that a later read would fail to parse.
    """
    registry_dir.mkdir(parents=True, exist_ok=True)
    content = dump_yaml(state.model_dump()).encode("utf-8")
    fd, tmp = tempfile.mkstemp(dir=str(registry_dir), prefix=".daemon_", suffix=".tmp")
    try:
        os.write(fd, content)
    except BaseException:
        os.close(fd)
        os.unlink(tmp)
        raise
    os.close(fd)
    try:
        os.replace(tmp, str(pid_file(registry_dir)))
    except BaseException:
        os.unlink(tmp)
        raise


def read_state(registry_dir: Path) -> DaemonState | None:
    """Return the recorded daemon state, or ``None`` when not running.

    A PID file that is missing, unparseable/corrupt, or whose recorded process
    is no longer alive is all treated as "not running" — stale in every case —
    and cleaned up here so every caller sees one consistent answer instead of
    re-deriving the stale check itself.
    """
    path = pid_file(registry_dir)
    if not path.is_file():
        return None

    try:
        data = load_yaml(path.read_text(encoding="utf-8"))
        state = DaemonState.model_validate(data) if data is not None else None
    except (OSError, yaml.YAMLError, ValidationError):
        # OSError also covers the file being removed between is_file() and
        # read_text() by a concurrent stop_daemon — treat that as "not running"
        # rather than letting FileNotFoundError propagate.
        state = None

    if state is None:
        path.unlink(missing_ok=True)
        return None

    if not is_alive(state.pid):
        path.unlink(missing_ok=True)
        return None
    return state


def is_alive(pid: int) -> bool:
    """Return whether ``pid`` refers to a currently running process."""
    if pid <= 0:
        return False
    if os.name == "nt":
        return _is_alive_windows(pid)
    return _is_alive_posix(pid)


def _is_alive_posix(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        # Exists but owned by another user — still alive from our perspective.
        return True
    return True


def _configure_kernel32():
    """Declare ``restype``/``argtypes`` for the kernel32 calls used here.

    ``ctypes`` defaults an undeclared foreign-function return type to 32-bit
    ``c_int``. ``HANDLE`` is pointer-sized (64-bit on Win64), so an
    ``OpenProcess`` handle used without this declaration gets truncated before
    it is ever passed back into ``GetExitCodeProcess``/``TerminateProcess``/
    ``CloseHandle`` — a well-known ctypes pitfall for exactly these APIs.
    """
    import ctypes
    from ctypes import wintypes

    kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.GetExitCodeProcess.restype = wintypes.BOOL
    kernel32.GetExitCodeProcess.argtypes = [
        wintypes.HANDLE,
        ctypes.POINTER(wintypes.DWORD),
    ]
    kernel32.TerminateProcess.restype = wintypes.BOOL
    kernel32.TerminateProcess.argtypes = [wintypes.HANDLE, wintypes.UINT]
    kernel32.CloseHandle.restype = wintypes.BOOL
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    return kernel32


def _is_alive_windows(pid: int) -> bool:
    import ctypes
    from ctypes import wintypes

    kernel32 = _configure_kernel32()
    process_query_limited_information = 0x1000
    handle = kernel32.OpenProcess(process_query_limited_information, False, pid)
    if not handle:
        return False
    try:
        exit_code = wintypes.DWORD()
        still_active = 259  # STILL_ACTIVE
        if not kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
            return False
        return exit_code.value == still_active
    finally:
        kernel32.CloseHandle(handle)


def start_daemon(
    registry_dir: Path,
    *,
    host: str,
    port: int,
    workspace: str | None,
    command: Sequence[str] | None = None,
) -> DaemonState:
    """Spawn ``command`` as a detached background process and record its PID.

    Raises :class:`ConflictError` when a daemon is already running — checked
    before ``command`` is required, so callers only need to build the argv (the
    CLI layer owns that, e.g. re-invoking ``taskpilot serve`` as a subprocess)
    once they know a spawn will actually happen. The existing-check and spawn
    run under a cross-process lock so two concurrent ``start`` calls cannot
    both pass the check and both spawn a daemon.
    """
    with _daemon_lock(registry_dir):
        existing = read_state(registry_dir)
        if existing is not None:
            raise ConflictError(
                f"Daemon already running (pid {existing.pid}, "
                f"http://{existing.host}:{existing.port})"
            )
        if command is None:
            raise ValueError("command is required to start a new daemon")

        registry_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_file(registry_dir)
        spawn_kwargs: dict[str, object] = {}
        if os.name == "nt":
            spawn_kwargs["creationflags"] = (
                subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
            )
        else:
            spawn_kwargs["start_new_session"] = True

        with log_path.open("ab") as log:
            process = subprocess.Popen(
                list(command),
                stdout=log,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                **spawn_kwargs,
            )

        state = DaemonState(
            pid=process.pid,
            host=host,
            port=port,
            started_at=utc_now_iso(),
        )
        write_state(registry_dir, state)
        return state


def stop_daemon(registry_dir: Path) -> None:
    """Stop the running daemon, or raise :class:`NotFound` when none is running.

    Runs under the same cross-process lock as :func:`start_daemon` so a
    concurrent ``start`` cannot write a new daemon's PID file in the window
    between this function's liveness check and its final unlink — which would
    otherwise let this function delete an unrelated, freshly-started daemon's
    record instead of the one it actually stopped.
    """
    with _daemon_lock(registry_dir):
        state = read_state(registry_dir)
        if state is None:
            raise NotFound("Daemon is not running")

        _terminate(state.pid)

        deadline = time.monotonic() + _STOP_TIMEOUT_SECONDS
        while time.monotonic() < deadline and is_alive(state.pid):
            _reap_if_our_child(state.pid)
            time.sleep(_STOP_POLL_INTERVAL_SECONDS)

        # Defense in depth: only remove the PID file if it still records the
        # PID we just stopped, even though holding the lock for the whole
        # function already rules out a concurrent start_daemon replacing it.
        current = _read_raw_pid(registry_dir)
        if current is None or current == state.pid:
            pid_file(registry_dir).unlink(missing_ok=True)


def _read_raw_pid(registry_dir: Path) -> int | None:
    """Return the PID recorded in the PID file without stale-cleanup side effects."""
    path = pid_file(registry_dir)
    try:
        data = load_yaml(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return None
    if data is None:
        return None
    try:
        return DaemonState.model_validate(data).pid
    except ValidationError:
        return None


def _reap_if_our_child(pid: int) -> None:
    """Best-effort non-blocking reap for the case where the calling process
    happens to be the daemon's direct parent (true only when ``start`` and
    ``stop`` run in the same process, e.g. tests exercising the service layer
    directly). In real CLI usage the daemon is reparented to init once the
    ``start`` process exits, so this is a no-op there.
    """
    if os.name == "nt":
        return
    try:
        os.waitpid(pid, os.WNOHANG)
    except ChildProcessError:
        pass


def _terminate(pid: int) -> None:
    if os.name == "nt":
        _terminate_windows(pid)
    else:
        _terminate_posix(pid)


def _terminate_posix(pid: int) -> None:
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        pass


def _terminate_windows(pid: int) -> None:
    kernel32 = _configure_kernel32()
    process_terminate = 0x0001
    handle = kernel32.OpenProcess(process_terminate, False, pid)
    if not handle:
        return
    try:
        kernel32.TerminateProcess(handle, 1)
    finally:
        kernel32.CloseHandle(handle)
