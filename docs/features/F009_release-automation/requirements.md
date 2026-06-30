# F009 Release Automation — Requirements

## Summary

Create the first TaskPilot release path as an npm-distributed CLI package named `taskpilot`. The
npm package bundles the Python implementation and built WebUI assets, performs lazy first-run
Python dependency setup in a user cache, and publishes only after a required dry-run and manual
approval. The package remains local-first at runtime; network access may be required only for
first-run dependency setup unless the runtime cache is already present.

## Serves

- `roadmap.md` Next Release Roadmap — Release Automation

## Functional Requirements

| ID | Requirement | Priority |
| --- | --- | --- |
| F009-R1 | The release shall publish an unscoped npm CLI package named `taskpilot` that exposes the `taskpilot` command and blocks release if the name is unavailable | must |
| F009-R2 | The npm package shall be assembled from a clean staging directory containing the Python source and built WebUI assets | must |
| F009-R3 | The npm wrapper shall discover Python `>=3.11` with `venv` and `pip`, using `TASKPILOT_PYTHON` as an override before common command discovery | must |
| F009-R4 | The npm wrapper shall lazily create a user-cache runtime environment keyed by TaskPilot npm version and Python major/minor version | must |
| F009-R5 | Runtime setup shall install Python dependencies from a bundled `requirements.lock` using `pip`, delete partial caches on failure, and report offline/setup failures clearly | must |
| F009-R6 | The npm wrapper shall handle `taskpilot --version` without runtime setup and handle `taskpilot doctor --rebuild-runtime` by deleting, rebuilding, and exiting before Python delegation | must |
| F009-R7 | The npm wrapper shall delegate normal commands to Python with `TASKPILOT_WEB_DIST` pointing at the staged WebUI assets | must |
| F009-R8 | If packaged WebUI assets are missing or unreadable, the API shall start and the WebUI route shall show a clear packaging error | must |
| F009-R9 | Release validation shall require matching versions in `package.json` and `pyproject.toml`, a committed `CHANGELOG.md` entry for the target version, and the full current quality suite before publish | must |
| F009-R10 | The release workflow shall run a two-stage npm publish: dry-run first, then manual approval before real npm publish | must |
| F009-R11 | Release validation shall support macOS, Linux, and Windows with full checks on macOS and CLI plus WebUI asset smoke checks on Windows and Ubuntu | must |
| F009-R12 | Release documentation shall cover global npm install, npm-only package-manager support, setup logs, offline failure recovery, cache rebuild, credentials, approval, and npm rollback by deprecating bad versions and publishing corrected versions | must |

## Acceptance Criteria

- **F009-R1:** The release workflow verifies the npm package name `taskpilot` before publish. If
  the name is unavailable or the package metadata would publish under another name, the release
  fails before publish.
- **F009-R2:** The package build creates a staging directory from clean inputs and includes Python
  source plus production WebUI assets without requiring generated assets to be committed under the
  Python source tree.
- **F009-R3:** The wrapper accepts `TASKPILOT_PYTHON` when it points to compatible Python, otherwise
  searches common Python commands and rejects missing Python, Python `<3.11`, missing `venv`, or
  missing `pip` with specific errors.
- **F009-R4:** First run creates a runtime cache outside the project workspace and npm package
  directory. Different TaskPilot npm versions or Python major/minor versions use separate caches.
- **F009-R5:** If dependency setup fails, the wrapper deletes the partial cache, prints a concise
  error, prints the setup log path, prints the last 20-50 lines of `pip` output, and gives exact
  offline/setup instructions.
- **F009-R6:** `taskpilot --version` returns the npm package version without creating the runtime
  cache. `taskpilot doctor --rebuild-runtime` deletes the matching runtime cache, rebuilds it
  immediately, reports concise progress to stderr, and exits.
- **F009-R7:** Normal CLI commands run through the bundled Python implementation, and Python receives
  `TASKPILOT_WEB_DIST` pointing at the staged WebUI assets.
- **F009-R8:** With missing packaged WebUI assets, API routes still start, and the WebUI route
  returns a clear packaging error instead of a blank page or generic server failure.
- **F009-R9:** A release with mismatched `package.json` and `pyproject.toml` versions, missing
  `CHANGELOG.md` target-version entry, failing test/lint/format/browser/build gate, or failing
  package build fails before publish.
- **F009-R10:** Real npm publish cannot run until a successful dry-run has completed and a maintainer
  manually approves the publish stage.
- **F009-R11:** macOS runs the full release quality suite. Windows and Ubuntu run npm global install,
  first-run runtime setup, `taskpilot --version`, a CLI command, and WebUI asset smoke validation.
- **F009-R12:** Release documentation explains `npm install -g taskpilot`, npm-only support for the
  first release, `TASKPILOT_PYTHON`, setup log locations, offline/setup failures,
  `taskpilot doctor --rebuild-runtime`, publish credentials and approval, and rollback by
  `npm deprecate` plus a corrected follow-up version.

## Constraints

- The first release supports npm global install only: `npm install -g taskpilot`.
- The first release does not promise pnpm, yarn, `npx`, or non-npm package-manager support.
- The npm package remains a wrapper around the existing Python implementation; it must not duplicate
  TaskPilot domain rules in JavaScript.
- First-run setup may require network access to install Python dependencies from the bundled
  `requirements.lock`; normal TaskPilot runtime remains local-first after setup.
- Cache data belongs in the user cache directory, not in `.taskpilot/`, the project repository, or
  the installed npm package directory.
- A bad npm release is corrected by deprecating the bad version and publishing a corrected version.
  Unpublish is reserved for exceptional secret, legal, or security incidents.

## Out of Scope

- Python-package-first release automation.
- Publishing to PyPI.
- `npx` support as a guaranteed release path.
- pnpm or yarn support.
- Managed Python runtime download.
- Vendored wheels or fully offline fresh install.
- Automatic publish on every push, merge, tag, or GitHub Release creation.
- Rewriting the TaskPilot CLI/domain implementation in JavaScript or TypeScript.
