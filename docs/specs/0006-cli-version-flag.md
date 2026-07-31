# CLI Version Flag

Status: implemented

## Outcome

`taskpilot --version` and `taskpilot -v` print the installed TaskPilot version and exit
successfully, regardless of how the Python CLI is invoked — a venv install (`taskpilot --version`),
direct module invocation (`python -m taskpilot.cli.app --version`), or an editable/dev checkout.
The printed value matches what the npm wrapper (`bin/taskpilot`) already reports for `--version`.

## Context

`bin/taskpilot` (the npm entry point) already special-cases `--version` inline — it prints
`packageJson.version` and exits 0 without delegating to Python (lines 365-368, implemented under
TP-80, done). That handling only fires for the exact single-argument invocation `taskpilot
--version` before the wrapper hands off to the Python process; it does not cover `-v`, and it does
not run at all for anyone invoking the Python CLI directly (raw venv install, `python -m
taskpilot.cli.app`, or any future non-npm packaging).

The root Typer callback (`src/taskpilot/cli/app.py`, `main()`) currently defines only `--json`
(F003-R8). Neither `--version` nor `-v` is defined anywhere in the Python CLI, so both invocations
below exit 2 ("No such option"):

```
.venv/bin/taskpilot --version
python -m taskpilot.cli.app --version
```

The version string's source of truth is the `version` field in `pyproject.toml` (currently
`1.2.0`), mirrored in `package.json` for the npm wrapper — the same value both entry points must
report.

Observed local-environment note: the `.venv` in this checkout currently has `taskpilot` installed
at metadata version `1.1.0` (`importlib.metadata.version("taskpilot")`) while `pyproject.toml`
already reads `1.2.0` — the editable install is stale relative to the source tree. This is not a
defect this spec introduces; it is the same class of drift the npm wrapper already has (a bumped
`package.json` needs a fresh install/build for `bin/taskpilot` to reflect it too). See Risks.

## Scope

In scope: one new eager `--version`/`-v` option on the root Typer callback in
`src/taskpilot/cli/app.py`, resolving the installed package version via `importlib.metadata` and
printing it, short-circuiting before any subcommand runs.

Out of scope: changing `bin/taskpilot`'s existing inline `--version` handling (already correct for
npm-installed end users); `taskpilot doctor --rebuild-runtime` or any other wrapper-only command;
changing the existing `--json` option or `CLIState` contract; a `version` subcommand (an option on
the root callback is the requested shape, matching Typer's eager-option idiom and the wrapper's
existing `--version` surface).

## Requirements

### Functional

- `taskpilot --version` and `taskpilot -v` print the installed version string followed by a
  newline to stdout and exit `0` (`EXIT_OK`), without dispatching to any subcommand — even when
  invoked as `taskpilot --version <anything-else>` (eager option fires during parsing, before
  subcommand resolution).
- The same behavior is reachable via `python -m taskpilot.cli.app --version` / `-v`, since the
  option lives on the root Typer callback rather than in wrapper-only code.
- Output is plain text (`{version}\n`), not affected by `--json` — `--version` short-circuits
  before `CLIState` is constructed, matching the npm wrapper's plain-text `--version` output today.
- The printed value is resolved via `importlib.metadata.version("taskpilot")` (the installed
  distribution's own metadata, populated from `pyproject.toml`'s `version` field at build/install
  time) — no separate copy of the version string is hardcoded in `app.py`.
- `taskpilot` with no arguments continues to show help (`no_args_is_help=True`, unchanged); adding
  `--version`/`-v` does not alter that default.

### Quality

- No production dependency added: `importlib.metadata` is stdlib (Python >=3.11, matching
  `pyproject.toml`'s `requires-python`).
- Architecture boundary: the option and its resolution live entirely in `cli/app.py` (or a small
  helper it calls within the `cli` layer) — no `core`/`services` change, no persistence or
  canonical-file effect.
- Deterministic output: exit code and stdout content do not depend on workspace state, `--json`, or
  any other flag.

## Design

### Domain and invariants

None — this is a CLI-presentation-only concern; no domain concept is introduced or changed.

### Canonical file effects

None. No `.taskpilot/items/` or other canonical file is read or written.

### Service operations

None. No new `core`/`services` function — version resolution is a one-line
`importlib.metadata.version("taskpilot")` call kept in the `cli` layer.

### CLI / API contracts

`src/taskpilot/cli/app.py`, root `@app.callback()` (`main()`), gains:

```python
def _version_callback(value: bool) -> None:
    if value:
        typer.echo(importlib.metadata.version("taskpilot"))
        raise typer.Exit(code=EXIT_OK)

version: bool = typer.Option(
    False,
    "--version",
    "-v",
    help="Print the installed TaskPilot version and exit.",
    is_eager=True,
    callback=_version_callback,
)
```

(Exact parameter ordering/placement decided during implementation; behavior above is normative.)
No REST/API contract change — this is CLI-only.

### UI states

None — no WebUI surface.

## Acceptance Criteria

- Given a working `taskpilot` install, when the user runs `taskpilot --version`, then the CLI
  prints the installed version string and a trailing newline to stdout and exits `0`.
- Given a working `taskpilot` install, when the user runs `taskpilot -v`, then the behavior is
  identical to `--version`.
- Given a working `taskpilot` install, when the user runs `python -m taskpilot.cli.app --version`,
  then the behavior is identical to the console-script entry point.
- Given `--version` is combined with other arguments (e.g. `taskpilot --version item list`), when
  the user runs it, then the CLI still prints the version and exits `0` without running `item
  list`.
- Given no `--version`/`-v` flag is passed, when the user runs any existing command, then behavior
  is unchanged (regression check for `--json` and all existing subcommands).
- Given the user runs `taskpilot` with no arguments, when the command executes, then help is shown
  as before (`no_args_is_help=True` unaffected).

## Test Strategy

Per `.claude/skills/test-change/references/test-strategy.md` categories:

- CLI-contract tests (Typer `CliRunner`, following the existing pattern in `tests/cli/`) for:
  `--version`, `-v`, combined with a trailing subcommand/args, and a regression check that
  `--json` and an existing subcommand (e.g. `taskpilot item list --json`) still work unchanged.
  Assert against `importlib.metadata.version("taskpilot")` read live in the test (not a hardcoded
  literal), so the test stays correct regardless of the installed/dev version and doesn't
  reproduce the local `pyproject.toml`/installed-metadata drift noted in Context.
- No unit-level test needed beyond the CLI-contract level — there is no service/domain logic to
  isolate.
- No E2E/browser-level test — no UI surface.

## Implementation Slices

1. Add the `--version`/`-v` eager option and callback to `src/taskpilot/cli/app.py`; CLI-contract
   tests covering the acceptance criteria above.
2. Documentation sync (`docs/api.md` or equivalent CLI reference, wherever the existing `--json`
   global option is documented) — via `maintain-docs`.

## Risks and Compatibility

- Purely additive: no existing flag, command, exit code, or output shape changes. `--json` and
  every existing subcommand are unaffected.
- Version-drift risk (not introduced by this change, but relevant to testing/verification): the
  printed value comes from the installed distribution's metadata, which only matches
  `pyproject.toml` after a fresh `pip install`/editable-install refresh. A stale dev venv (as
  currently observed locally: `1.1.0` installed vs. `1.2.0` in `pyproject.toml`) will print the
  stale value — this mirrors the npm wrapper's existing dependence on `package.json` being current
  at packaging time, not a new invariant. Tests must read the expected value live via
  `importlib.metadata` rather than asserting a hardcoded version literal, so this drift cannot
  cause a false test failure or a false pass.

## Assumptions

- An option on the root callback (not a `version` subcommand) is the correct shape, matching both
  Typer's eager-option idiom and the existing `bin/taskpilot --version` surface end users already
  expect.
- `importlib.metadata.version("taskpilot")` is an acceptable resolution mechanism (stdlib, no new
  dependency) rather than parsing `pyproject.toml` directly at runtime (which would require either
  a new TOML-parsing dependency on Python <3.11 or bundling `pyproject.toml` into the installed
  package — neither is necessary since `importlib.metadata` is the standard mechanism for this).

## Open Questions

None blocking.
