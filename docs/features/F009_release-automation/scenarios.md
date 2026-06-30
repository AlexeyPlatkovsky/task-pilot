# F009 Release Automation — Scenarios

## Scenarios

### F009-S1: Block release when npm package identity is wrong

Covers: F009-R1

```gherkin
Scenario: Block release when npm package identity is wrong
  Given the release workflow is preparing package metadata
    And the package name is not "taskpilot"
  When release preflight runs
  Then the workflow fails before publish
    And the failure explains that the first release requires the unscoped npm package "taskpilot"
```

### F009-S2: Assemble npm package from clean staging

Covers: F009-R2, F009-R7

```gherkin
Scenario: Assemble npm package from clean staging
  Given the WebUI production build has completed
    And the Python source and requirements.lock are present
  When the npm package staging task runs
  Then the staging directory contains the Python source
    And the staging directory contains built WebUI assets
    And the Python source tree is not modified by generated WebUI assets
```

### F009-S3: Discover compatible Python

Covers: F009-R3

```gherkin
Scenario: Discover compatible Python
  Given TASKPILOT_PYTHON is unset
    And python3 resolves to Python 3.10
    And python resolves to Python 3.12 with venv and pip
  When the npm wrapper starts a command that needs runtime setup
  Then it rejects Python 3.10
    And it selects Python 3.12
```

### F009-S4: Create versioned user-cache runtime

Covers: F009-R4, F009-R5

```gherkin
Scenario: Create versioned user-cache runtime
  Given TaskPilot npm version is "0.1.0"
    And the selected Python version is "3.12"
    And no matching runtime cache exists
  When the first delegated command runs
  Then the wrapper creates a user-cache runtime for "0.1.0" and Python 3.12
    And installs dependencies from the bundled requirements.lock with pip
    And reports concise setup progress to stderr
```

### F009-S5: Fail cleanly after interrupted setup

Covers: F009-R5

```gherkin
Scenario: Fail cleanly after interrupted setup
  Given first-run dependency installation is in progress
  When pip fails because the network is unavailable
  Then the wrapper deletes the partial runtime cache
    And prints a concise setup failure
    And prints the setup log path
    And prints the last 20-50 lines of pip output
    And prints exact offline/setup instructions
```

### F009-S6: Rebuild runtime with doctor command

Covers: F009-R6

```gherkin
Scenario: Rebuild runtime with doctor command
  Given a matching runtime cache exists
  When "taskpilot doctor --rebuild-runtime" runs
  Then the npm wrapper deletes the matching runtime cache
    And rebuilds the runtime immediately
    And exits without delegating the doctor command to Python
```

### F009-S7: Delegate normal command with WebUI asset path

Covers: F009-R7, F009-R8

```gherkin
Scenario: Delegate normal command with WebUI asset path
  Given the runtime cache is ready
    And the staged WebUI assets exist
  When "taskpilot serve" runs from the npm package
  Then the wrapper delegates to the bundled Python implementation
    And TASKPILOT_WEB_DIST points to the staged WebUI assets
    And the WebUI route serves the packaged asset shell
```

### F009-S8: Show packaging error when WebUI assets are missing

Covers: F009-R8

```gherkin
Scenario: Show packaging error when WebUI assets are missing
  Given the runtime cache is ready
    And TASKPILOT_WEB_DIST points to a missing directory
  When "taskpilot serve" runs
  Then API routes start
    And the WebUI route shows a clear packaging error
    And the server does not return a blank page for the WebUI route
```

### F009-S9: Block publish on release preflight failure

Covers: F009-R9, F009-R10

```gherkin
Scenario: Block publish on release preflight failure
  Given package.json version is "0.1.0"
    And pyproject.toml version is "0.1.1"
  When the release workflow runs
  Then the workflow fails before npm dry-run or publish
    And the failure states that package.json and pyproject.toml versions must match
```

### F009-S10: Publish only after dry-run and approval

Covers: F009-R10

```gherkin
Scenario: Publish only after dry-run and approval
  Given all release quality gates pass
    And npm publish dry-run succeeds
  When a maintainer approves the publish environment
  Then real npm publish runs
    And publish logs do not expose credentials
```

### F009-S11: Validate supported OS matrix

Covers: F009-R11

```gherkin
Scenario: Validate supported OS matrix
  Given the release validation matrix starts
  When macOS, Windows, and Ubuntu jobs run
  Then macOS runs the full release quality suite
    And Windows runs npm global install plus CLI and WebUI asset smoke checks
    And Ubuntu runs npm global install plus CLI and WebUI asset smoke checks
```

### F009-S12: Document npm rollback by deprecation and correction

Covers: F009-R12

```gherkin
Scenario: Document npm rollback by deprecation and correction
  Given version "0.1.0" has been published with a release defect
  When a maintainer reads the release documentation
  Then the documented recovery path deprecates "taskpilot@0.1.0"
    And publishes a corrected follow-up version
    And does not rely on unpublish except for exceptional secret, legal, or security incidents
```

## Manual Verification Checklist

- [ ] (F009-R1) Confirm npm package metadata uses unscoped `taskpilot` and exposes `taskpilot`.
- [ ] (F009-R2) Confirm staging can be removed and recreated without dirtying source trees.
- [ ] (F009-R3) Confirm Python discovery errors distinguish missing Python, old Python, missing
      `venv`, and missing `pip`.
- [ ] (F009-R4) Confirm runtime cache location is outside the project repository and installed npm
      package.
- [ ] (F009-R5) Confirm failed setup removes only the matching partial cache and prints the setup
      log path.
- [ ] (F009-R6) Confirm `taskpilot --version` does not create the runtime cache.
- [ ] (F009-R7) Confirm delegated Python commands receive `TASKPILOT_WEB_DIST`.
- [ ] (F009-R8) Confirm missing WebUI assets leave API routes usable.
- [ ] (F009-R9) Confirm missing target-version `CHANGELOG.md` entry blocks publish.
- [ ] (F009-R10) Confirm real publish cannot start before a successful dry-run and approval.
- [ ] (F009-R11) Confirm macOS full checks and Windows/Ubuntu smoke checks run in CI.
- [ ] (F009-R12) Confirm release docs describe `npm deprecate` plus corrected follow-up version.
