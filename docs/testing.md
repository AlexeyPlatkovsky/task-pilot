# Testing

## Strategy

TaskPilot tests at the lowest level that proves behavior and at boundaries where contracts
cross. Core domain logic is covered by unit tests. File parsing, serialization, and CLI
contracts are covered by integration tests. The REST API is validated through API tests.
The WebUI is tested through component tests.

Failure paths, invalid inputs, cross-platform path behavior, and deterministic output are
treated as first-class test concerns alongside happy paths.

## Test Levels

| Level | Scope | Tooling |
| --- | --- | --- |
| Unit | Individual functions and classes in the Python core: parsers, validators, domain services, link derivation | pytest |
| Integration | File read/write round-trips, CLI command execution with real filesystem, index rebuild from canonical files | pytest |
| API | FastAPI endpoints: request/response contracts, error handling, JSON determinism | pytest + FastAPI TestClient |
| Component | React components: Kanban board, item modal, project selector, form validation | Vitest + React Testing Library |
| End-to-end | Full workflow: init -> create items -> WebUI display -> CLI query -> git diff readability | Manual checklist (Alpha), automated later |

## Running Feature Scenarios

Per-feature `scenarios.md` files contain Gherkin `Given/When/Then` scenarios linked to
requirement IDs. Automated scenarios are run through pytest with a Gherkin-compatible runner
(e.g. pytest-bdd). A manual verification checklist accompanies each feature and runs at least
once before the feature is marked done.

## Coverage Expectations

Before a feature is considered done:
- every requirement has at least one scenario covering its happy path;
- every requirement has at least one scenario covering a failure or edge case;
- the feature's manual checklist has been executed and passed;
- no assertions have been weakened or tests deleted to force a pass.

Shared infrastructure (file parser, validation, link derivation, JSON serialization) must have
dedicated coverage above 80% before Beta.

## Environments

- **Local**: primary test environment. All tests must pass on a developer's machine without
  network access.
- **CI**: future. Runs the same suite on push. Not required for Alpha.

## Quality Gates

- All unit, integration, and API tests pass before merging.
- Component tests pass for any WebUI change.
- `taskpilot validate` reports no errors in test fixture data.
- No critical scenarios are failing.
- Formatting, type checks, and lints pass across Python and TypeScript.
