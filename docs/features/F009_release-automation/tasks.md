# F009 Release Automation — Tasks

| ID | Task | Implements | Status | Depends on |
| --- | --- | --- | --- | --- |
| F009-T1 | Define npm package metadata for unscoped `taskpilot`, `taskpilot` bin, included files, and package-name preflight | F009-R1, F009-R2 | ✅ done | — |
| F009-T2 | Build clean npm staging that copies Python source, release metadata, `requirements.lock`, wrapper files, and production WebUI assets | F009-R2, F009-R7 | ✅ done | F009-T1 |
| F009-T3 | Implement Python discovery with `TASKPILOT_PYTHON` override, common command fallback, and `>=3.11`/`venv`/`pip` validation | F009-R3 | ✅ done | F009-T1 |
| F009-T4 | Implement lazy user-cache runtime setup keyed by npm version and Python major/minor version | F009-R4 | ✅ done | F009-T3 |
| F009-T5 | Install dependencies from bundled `requirements.lock`, handle partial-cache deletion, setup progress, setup logs, pip output tail, and offline/setup errors | F009-R5 | ✅ done | F009-T4 |
| F009-T6 | Implement wrapper command handling for `--version` and `doctor --rebuild-runtime` | F009-R6 | ✅ done | F009-T4 |
| F009-T7 | Delegate normal commands to Python with `TASKPILOT_WEB_DIST` set to staged WebUI assets | F009-R7 | ✅ done | F009-T2, F009-T5 |
| F009-T8 | Add server behavior for missing or unreadable packaged WebUI assets: API continues and WebUI route reports packaging error | F009-R8 | ✅ done | F009-T7 |
| F009-T9 | Add release preflight for matching `package.json`/`pyproject.toml` versions and target-version `CHANGELOG.md` entry | F009-R9 | ✅ done | F009-T1 |
| F009-T10 | Wire full release quality gates: Python tests/lint/format, WebUI tests, browser contract, functional E2E, WebUI build, package build, and npm dry-run | F009-R9, F009-R10 | ✅ done | F009-T2, F009-T9 |
| F009-T11 | Add two-stage release workflow with required dry-run, manual approval, credentials check, and real npm publish | F009-R10 | ✅ done | F009-T10 |
| F009-T12 | Add macOS full-check release validation and Windows/Ubuntu npm global install plus CLI/WebUI smoke checks | F009-R11 | ✅ done | F009-T10 |
| F009-T13 | Document install path, npm-only support, Python prerequisite, cache/log locations, offline recovery, rebuild command, approval, credentials, and npm deprecate rollback | F009-R12 | ⏳ todo | F009-T11, F009-T12 |

## Notes

- The wrapper should keep stdout clean for delegated command output and use concise stderr progress
  only during first-run setup or rebuild.
- Cache cleanup should be conservative: delete the matching partial cache on setup failure, but do
  not remove unrelated TaskPilot/Python-version caches.
- Windows and Ubuntu smoke checks must prove the npm package can install globally, set up the
  Python runtime, run at least one delegated CLI command, and serve or fetch packaged WebUI assets.
- If npm package name `taskpilot` is unavailable, stop and return to product naming; do not
  silently publish under a scoped or alternate package name.
