# CLI Update Command

Status: implemented

Backlog: TP-140.

## Outcome

`taskpilot update` upgrades an npm-installed TaskPilot to the latest version published on npmjs,
and `taskpilot update --check` reports whether a newer version exists without changing anything.

## Context

The npm entry point `bin/taskpilot` already handles `--version` and `doctor --rebuild-runtime`
itself, before discovering Python. Everything else is delegated to the Python CLI. Nothing upgrades
an installed package today; users must know the scoped package name and run `npm install -g`
themselves.

TaskPilot is offline-first: no command reaches the network unless the user runs it explicitly.
`update` is such an explicit command and is the only one that contacts the registry.

## Scope

In scope: `update` and `update --check` in `bin/taskpilot`; a Python CLI `update` command for
installs without the npm wrapper.

Out of scope: automatic or background update checks; downgrades; choosing a version or dist-tag;
updating pip or source installs.

## Requirements

- R1 The wrapper handles `taskpilot update [--check]` itself, before Python discovery, so it works
  even when the Python runtime is missing or broken. A leading global `--json` is accepted and
  ignored.
- R2 The latest version comes from `npm view @alexey_platkovsky/taskpilot version`, so the user's
  npm registry, proxy, and auth configuration apply. On failure (npm missing, offline, registry
  error, unparseable output) it prints
  `taskpilot: could not check for updates: <reason>` (npm's error code and first error line, never
  its log-file path) and
  `taskpilot: update manually with: npm install -g @alexey_platkovsky/taskpilot@latest` to stderr
  and exits `1`.
- R3 When the latest version is not newer than the installed one (numeric `major.minor.patch`
  comparison), it prints `taskpilot is up to date (<installed>)` to stdout and exits `0` without
  installing.
- R4 `--check` with a newer version prints
  `Update available: <installed> -> <latest>. Run: taskpilot update` to stdout and exits `0`
  without installing.
- R5 Without `--check` and with a newer version, it prints
  `taskpilot: updating <installed> -> <latest>...` to stderr, runs
  `npm install -g @alexey_platkovsky/taskpilot@<latest>` with inherited stdio, and on success prints
  `taskpilot: updated to <latest>` to stderr and exits `0`. A non-zero npm exit prints
  `taskpilot: npm install failed (exit <code>)` (or `(signal <name>)` / the spawn error) and the manual command hint to stderr and exits `1`.
  The Python runtime for the new version is built on its first run, as for any fresh install.
- R6 Any argument other than a single optional `--check` prints
  `taskpilot: usage: taskpilot update [--check]` to stderr and exits `1` without contacting npm.
- R7 The Python CLI `taskpilot update` (reached only without the npm wrapper) prints to stderr
  that self-update is provided by the npm package, with the command
  `npm install -g @alexey_platkovsky/taskpilot@latest`, and exits `1`. It never touches the network.

## Acceptance Criteria

- AC1 Given npm reports a newer version, `update --check` prints the update-available line, exits
  `0`, and npm install is never called.
- AC2 Given npm reports a newer version, `update` runs `npm install -g <pkg>@<latest>` once, prints
  the updated line, and exits `0`.
- AC3 Given npm reports the same or an older version, `update` prints the up-to-date line, exits
  `0`, and does not install.
- AC4 Given `npm view` fails or prints a non-version, `update` exits `1` with both stderr lines and
  does not install.
- AC5 Given npm install fails, `update` exits `1` with the failure line and the manual hint.
- AC6 Given an unknown argument, `update` exits `1` with the usage line and npm is never called.
- AC7 Python `taskpilot update` exits `1` with the npm instruction and no network access.

## Test Strategy

| Behavior | Level |
| --- | --- |
| Wrapper update flows (AC1–AC6) | Integration: run `node bin/taskpilot` with a stub `npm` on `PATH` that records calls (POSIX only; skipped on Windows) |
| Version comparison | Covered through AC1/AC3 (newer, equal, older, prerelease-free) |
| Python `update` (AC7) | CLI (Typer runner) |

## Risks

- Global npm installs may need elevated permissions; the failure path prints the manual command
  instead of retrying with `sudo`.
- `npm view` uses the user's npm configuration; a private registry mirror that lags npmjs reports
  its own latest version.

## Acceptance Evidence

| Criteria | Evidence |
| --- | --- |
| AC1–AC6, R1 (`--json` prefix), version ordering | `tests/release/test_wrapper_update.py` |
| AC7 | `tests/cli/test_cli_scaffold.py::test_python_update_explains_npm_path_and_exits_1` |

Known limitation: the Windows path (`npm.cmd` through a shell) is not covered by automated tests;
the Python `update --check` (no wrapper) is rejected by the CLI parser with exit `2`.

