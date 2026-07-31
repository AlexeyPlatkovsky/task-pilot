# Daemon Lifecycle Commands

Status: accepted

## Outcome

A user can run the TaskPilot local server as a background process instead of holding a foreground
terminal open, and can check on, stop, restart, or tail the logs of that background process from
another shell.

## Context

`taskpilot serve` (`src/taskpilot/cli/commands/serve.py`) already starts the WebUI/API server, but it
blocks the calling terminal (`uvicorn.run(...)` runs in the foreground) and has no PID tracking, no
log file, and no stop/status mechanism. TP-122 asks for `start` / `stop` / `restart` / `status` /
`logs` subcommands that manage that same server as a background daemon.

The registry module (`src/taskpilot/services/registry.py`) already resolves a per-OS,
`TASKPILOT_HOME`-overridable application-data directory (`default_registry_dir()`) and already
branches on `os.name == "nt"` for file locking (`msvcrt` vs `fcntl`). This spec follows that existing
precedent for OS-specific behavior rather than introducing a new convention.

## Scope

In scope: five new CLI subcommands (`start`, `stop`, `restart`, `status`, `logs`) and a new
`services/daemon.py` module that owns PID file, log file, process spawn, and liveness/stop logic.
`start` reuses the existing `serve` bootstrap (`taskpilot.server.app:create_app_from_env` via
uvicorn) as a detached child process; it does not duplicate server bootstrap logic.

Out of scope: changing `taskpilot serve`'s existing foreground behavior or its flags; multi-instance
daemon support (only one daemon per machine, matching the existing single-registry-dir model);
automatic daemon restart/supervision (e.g. crash recovery, systemd/launchd integration); log
rotation (append-only log is sufficient for this slice — flagged as an open question below).

## Requirements

### Functional

- `taskpilot start [--host HOST] [--port PORT] [--workspace PATH]`: spawns the server as a detached
  background process using the same host/port/workspace validation and registry-dir resolution as
  `serve` today. Writes a PID file recording the child PID, host, and port. Returns to the shell
  immediately once the child process is confirmed launched, printing the PID, host, and port.
  If a daemon is already running (live PID file), does not spawn a second one; reports the existing
  PID and exits `EXIT_USER_ERROR` (1).
- `taskpilot stop`: reads the PID file, sends a graceful termination signal (`SIGTERM` on POSIX,
  `TerminateProcess` via `taskpilot.exe` semantics through Python's `Process.terminate()` on
  Windows) to the recorded PID, waits (bounded) for exit, then removes the PID file. If no PID file
  exists, or the recorded process is not alive (stale PID file), reports "not running", removes any
  stale PID file, and exits `EXIT_USER_ERROR` (1) — `stop` on an already-stopped daemon is a
  caller-correctable condition, not a system failure.
- `taskpilot restart`: runs the `stop` behavior (tolerating "not running") followed by the `start`
  behavior, reusing both code paths rather than re-implementing them.
- `taskpilot status`: reports whether the daemon is running. When running: PID, host, port, and how
  long it has been up. When not running (no PID file, or stale PID file): reports "not running" and
  exits `EXIT_OK` (0) — status is a query, not an error, on either outcome. `--json` (existing global
  flag) emits a machine-readable equivalent.
- `taskpilot logs [--follow/-f] [--lines N]`: prints the daemon's log file. Without `--follow`,
  prints the last `N` lines (default matches a reasonable tail default, e.g. 100) and exits. With
  `--follow`, tails the file as it grows (like `tail -f`) until interrupted (Ctrl-C). If no log file
  exists yet, reports that and exits `EXIT_USER_ERROR` (1).

### Quality

- Cross-platform: POSIX (macOS/Linux) and Windows (`os.name == "nt"`) both supported, matching the
  precedent in `registry.py`. Detached-process creation and liveness/termination checks are the two
  behaviors that differ by platform; both are isolated behind small functions in the new
  `services/daemon.py` module so the CLI layer stays platform-agnostic.
- PID and log files live under `default_registry_dir()` (the existing per-OS application-data
  directory), not under the project workspace's `.taskpilot/` — the daemon is machine-level state
  (one daemon per machine), matching the registry's own "machine-specific state" framing, not
  project-canonical data. Filenames: `daemon.pid` and `daemon.log` inside that directory.
- No canonical task file or persistence-schema change. PID/log files are disposable runtime state,
  not canonical data — consistent with the product invariant that SQLite/index-like data is never
  the source of truth.
- Architecture boundary: `cli/commands/{start,stop,restart,status,logs}.py` (or one `daemon.py`
  command module registering all five) only parses args, calls into `services/daemon.py`, and
  formats output. All PID-file I/O, process spawn/liveness/termination, and log-file I/O live in
  `services/daemon.py`.

## Design

### Domain and invariants

- A "daemon" is identified by a single PID file at `<registry_dir>/daemon.pid`. Its presence plus a
  live process at the recorded PID is the sole source of truth for "is it running" — there is no
  separate state to fall out of sync, other than the ordinary stale-PID-file case (process died
  without cleanup), which every read path must detect and treat as "not running."
- Only one daemon per machine (mirrors the existing one-registry-per-machine model). `start` while
  already running is a no-op-with-error, not a queue or second instance.

### Canonical file effects

None. No `.taskpilot/items/` or other canonical file is touched by this feature.

### Service operations

New module `src/taskpilot/services/daemon.py`:

- `pid_file(registry_dir: Path) -> Path`, `log_file(registry_dir: Path) -> Path`
- `read_pid(registry_dir: Path) -> DaemonState | None` — parses the PID file (PID, host, port,
  started_at); returns `None` if absent or the recorded process is not alive (also cleans up the
  stale file).
- `start_daemon(registry_dir, *, host, port, workspace) -> DaemonState` — spawns the detached child
  process (POSIX: `subprocess.Popen(..., start_new_session=True)`; Windows:
  `subprocess.Popen(..., creationflags=CREATE_NEW_PROCESS_GROUP | DETACHED_PROCESS)`), redirects
  child stdout/stderr to the log file, writes the PID file, and returns the resulting state. Raises
  a typed error if already running.
- `stop_daemon(registry_dir) -> None` — signals the recorded PID (`SIGTERM` POSIX /
  `Process.terminate()` Windows), waits with a bounded timeout for exit, raises a typed
  "not running" error if there was nothing to stop.
- `is_alive(pid: int) -> bool` — cross-platform liveness check (`os.kill(pid, 0)` POSIX;
  `OpenProcess`/`psutil`-free equivalent on Windows — see Open Questions on whether a new dependency
  is acceptable here).

### CLI / API contracts

Five new subcommands on the root `taskpilot` Typer app (`src/taskpilot/cli/app.py` gains a
`daemon_cmd.register(app)` call, or five individual command modules — implementation slice below
decides): `start`, `stop`, `restart`, `status`, `logs`. Exit codes follow the existing convention in
`src/taskpilot/cli/exit_codes.py` (`EXIT_OK`, `EXIT_USER_ERROR`, `EXIT_SYSTEM_ERROR`) exactly as
`serve.py` already does. `status --json` follows the existing global `--json` flag pattern from
`CLIState`.

## Acceptance Criteria

- Given no daemon is running, when the user runs `taskpilot start`, then a background process is
  spawned, the shell returns immediately, and `taskpilot status` reports it running with a PID.
- Given a daemon is already running, when the user runs `taskpilot start` again, then no second
  process is spawned, an error naming the existing PID is printed, and the exit code is 1.
- Given a daemon is running, when the user runs `taskpilot stop`, then the process is terminated,
  the PID file is removed, and a subsequent `taskpilot status` reports "not running" with exit 0.
- Given no daemon is running (no PID file), when the user runs `taskpilot stop`, then the CLI
  reports "not running" and exits 1.
- Given a PID file exists but its process is no longer alive, when the user runs `taskpilot status`
  or `taskpilot stop`, then the CLI treats it as "not running," cleans up the stale PID file, and
  (for `status`) exits 0 / (for `stop`) exits 1.
- Given a daemon is running, when the user runs `taskpilot restart`, then the old process is
  stopped and a new process is started, and `taskpilot status` reports the new PID.
- Given the daemon has written log output, when the user runs `taskpilot logs`, then the last N
  lines print and the command exits; with `--follow`, new lines appear as they are written until
  interrupted.
- Given no log file exists yet, when the user runs `taskpilot logs`, then the CLI reports that
  clearly and exits 1.

## Test Strategy

Per `.claude/skills/test-change/references/test-strategy.md` categories:

- Unit tests for `services/daemon.py`: PID file read/write/parse, stale-PID detection (mock a dead
  PID), `is_alive` on the current test process vs. an invalid PID, log-file path resolution — using
  `TASKPILOT_HOME` (already the test seam `registry.py` uses) to isolate from the real home
  directory.
- CLI-contract tests (Typer `CliRunner`, following the pattern used for `serve`/`item` commands)
  for each subcommand's exit code and stdout shape, using a real short-lived subprocess for `start`
  (spawn, assert PID file + status, then `stop` in teardown) rather than mocking the process spawn,
  so the detach behavior is actually exercised.
- Cross-platform: the POSIX path (`fcntl`-equivalent signal/spawn) is exercised directly in CI;
  the Windows-specific branch (`creationflags`, `TerminateProcess`) cannot be exercised on
  POSIX CI runners and is either covered by a Windows CI job if one exists, or unit-tested with the
  Windows branch monkeypatched/isolated — check current CI matrix before finalizing (see Open
  Questions).
- No E2E/browser-level tests — this is a CLI/process feature with no UI surface.

## Implementation Slices

1. `services/daemon.py`: PID file model + read/write/stale-detection + `is_alive` (POSIX first,
   Windows branch stubbed with a typed "not yet exercised on this platform" note if CI can't run
   Windows — flag as risk, not silently skip).
2. `start`/`status` commands wired to slice 1, with unit + CLI tests.
3. `stop`/`restart` commands, with unit + CLI tests (including the stale-PID and not-running
   paths).
4. `logs` command (tail + follow), with unit + CLI tests.
5. Documentation sync (`docs/api.md` or equivalent CLI command reference) — via `maintain-docs`.

## Risks and Compatibility

- Process-management bugs (orphaned children, zombie processes, port-already-in-use races between
  `stop` and `start` in `restart`) are the main correctness risk; the bounded-wait-then-verify
  pattern in `stop_daemon`/`start_daemon` and the CLI-level subprocess tests in the test strategy
  are the mitigation.
- Windows behavior is designed but not verified against a live Windows run as part of this spec —
  see Open Questions.
- `start_daemon` and `stop_daemon` both run their entire read-check/spawn-or-terminate/write-or-unlink
  sequence under the same cross-process lock (mirroring `services/registry.py`'s `fcntl`/`msvcrt`
  locking). This closes both the read-check-then-spawn race that would otherwise let two concurrent
  `taskpilot start` invocations both spawn a daemon, and the asymmetric race where an unlocked `stop`
  could delete a different, concurrently-started daemon's PID file. `stop_daemon` additionally only
  removes the PID file if it still records the PID just stopped, as defense in depth.
- PID-reuse is an accepted residual risk: liveness is PID-only (no start-time or command-line
  cross-check), so if the daemon process dies and the OS reissues its PID to an unrelated process
  before the next `status`/`stop` call, that unrelated process would be misread as the daemon and
  could receive a termination signal. Narrow window in practice for a single-user local tool;
  not mitigated further in this slice.
- No compatibility risk to existing `serve` command or canonical file formats; this is purely
  additive.

## Assumptions

- One daemon per machine (no `--name`/multi-instance support) is sufficient for this slice, matching
  the single-registry-dir precedent.
- PID/log files belong in `default_registry_dir()`, not the project workspace, because the daemon is
  a machine-level concern like the registry itself, not project-canonical data.
- A plain append-only log file (no rotation) is acceptable for this slice.

## Open Questions

- ~~Is a `psutil`-class dependency acceptable...~~ Resolved: stdlib-only (`os.kill`/`subprocess`/
  `ctypes` for Windows termination). No new production dependency. User-confirmed 2026-07-31.
- CI has no Windows job in `ci.yml` (Ubuntu-only); Windows is exercised only by the `windows-smoke`
  job in `.github/workflows/release.yml` (npm-global-install + CLI/WebUI smoke, not the pytest
  suite). The Windows-specific branch in `services/daemon.py` therefore ships without automated
  unit-test coverage on Windows; add a smoke check for `start`/`status`/`stop` to the existing
  `windows-smoke` job as this feature's Windows verification, and unit-test the branch selection
  logic (not actual Windows syscalls) on the Ubuntu CI runner via monkeypatching `os.name`.
- Is log rotation/size capping required now, or acceptable as a later follow-up (assumption above
  says later)? — carried forward as an assumption, not blocking.
- Exact default `--lines` count for `taskpilot logs` (spec assumes 100) — carried forward as an
  assumption, not blocking.
