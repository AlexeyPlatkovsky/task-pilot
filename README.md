# TaskPilot

Local-first, file-based task management. Markdown/YAML files under `.taskpilot/` are the canonical
source of truth; everything else (indexes, UI state) is disposable. TaskPilot works offline with no
accounts or hidden synchronization.

See [`docs/`](docs/) for the product concept, specifications, and architecture decisions.

## Workspace layout

A TaskPilot project lives inside its repository under `.taskpilot/`:

```text
repo-root/
  .taskpilot/
    project.yaml          # canonical project identity
    items/
      TP-1.yaml           # one YAML file per item
    comments/
      TP-1/
        2026-06-23T10-00-00Z.md   # append-only Markdown comments per item
```

## Development

This is a Python project managed with [`uv`](https://docs.astral.sh/uv/).

```bash
uv sync          # create the environment and install dev dependencies
uv run pytest    # run the test suite
```

Source lives under `src/taskpilot/` (core domain layer); tests live under `tests/`.

## Installation

TaskPilot is distributed as an npm package. The first release supports **npm global install only**.

**Prerequisites:**
- Node.js >= 18 (required by npm)
- Python >= 3.11 with `venv` and `pip` (discovered automatically at runtime)

```bash
npm install -g taskpilot
```

The first run sets up a Python runtime environment in your user cache directory
(keyed by TaskPilot npm version and Python major.minor version). Subsequent runs
reuse the cached environment and are fast. During setup, logs are written to
`<cache>/runtimes/npm-<version>/py<major.minor>/setup.log`.

**Specifying a Python interpreter:**

Set `TASKPILOT_PYTHON` to the full path of a compatible Python executable:

```bash
TASKPILOT_PYTHON=/opt/homebrew/bin/python3.11 taskpilot --help
```

**Cache location by platform:**

| Platform | Cache directory |
| --- | --- |
| macOS | `~/Library/Caches/taskpilot/` |
| Linux | `~/.cache/taskpilot/` (XDG) |
| Windows | `%LOCALAPPDATA%/taskpilot/Cache/` |

## Offline and Setup Failures

Normal TaskPilot runtime works offline after the first-run setup. First-run
setup requires network access to install Python dependencies from the bundled
`requirements.lock`.

If setup fails:
- The partial cache is deleted automatically.
- The setup log is preserved at
  `<cache>/runtimes/npm-<version>/py<major.minor>.setup.log`.
- The setup log path and last 20-40 lines of `pip` output are printed.
- For network failures, the error includes instructions to connect and retry.
- For other failures, run `taskpilot doctor --rebuild-runtime` to retry.

## Cache Rebuild

```bash
taskpilot doctor --rebuild-runtime
```

Deletes the matching runtime cache for the current npm version and Python
version, then rebuilds it immediately. Exits after rebuild without delegating
to Python.

## Releasing

### Publishing a Beta version

1. Update `version` in both `package.json` and `pyproject.toml`.
2. Add a `## [x.y.z]` section to `CHANGELOG.md`.
3. Merge the version/changelog change.
4. In GitHub Actions, run the **Release** workflow manually.
5. Enter the exact version.

The manual workflow runs the full release gate, Ubuntu and Windows package
smoke checks, rebuilds the staging package, runs `npm publish --dry-run`, then
publishes to npm with the `beta` dist-tag.

Beta publishing uses npm Trusted Publishing from GitHub Actions. Before the
first publish, configure the npm package trusted publisher for this repository,
workflow `.github/workflows/release.yml`, and environment `npm-beta`. The
publish job requests GitHub's OIDC token through `id-token: write` and does not
require a long-lived `NPM_TOKEN` secret.

Local publish scripts remain available for emergency/manual verification:

```bash
npm run quality-gates
npm run release:dry-run
npm run release:publish
```

Local publish scripts also default to the `beta` dist-tag. Set
`NPM_DIST_TAG=latest` only when intentionally promoting a stable release.

### Rolling back a bad release

Do **not** use `npm unpublish` except for exceptional secret, legal, or
security incidents. Instead:

1. Deprecate the bad version:
   ```bash
   npm deprecate taskpilot@x.y.z "This version has a defect. Use taskpilot@x.y.z+1 instead."
   ```
2. Publish a corrected follow-up version with an incremented version number.

This keeps the npm registry history intact and prevents breaking existing
installations that have pinned or cached the bad version.

### Package manager support

The first release supports **npm only**. `pnpm`, `yarn`, `npx`, and other
package managers are not guaranteed to work and are out of scope for the
initial release.
