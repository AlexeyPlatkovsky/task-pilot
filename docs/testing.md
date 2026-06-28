# Testing

## Strategy

TaskPilot tests at the lowest level that proves behavior and at boundaries where contracts
cross. Core domain logic is covered by unit tests. File parsing, serialization, and CLI
contracts are covered by integration tests. The REST API is validated through API tests.
The WebUI is tested through component tests, focused functional Playwright E2E tests for major
browser journeys, and separate browser contract tests for style or browser-only behavior.

Failure paths, invalid inputs, cross-platform path behavior, and deterministic output are
treated as first-class test concerns alongside happy paths.

## Test Levels

| Level | Scope | Tooling |
| --- | --- | --- |
| Unit | Individual functions and classes in the Python core: parsers, validators, domain services, link derivation | pytest |
| Integration | File read/write round-trips and CLI command execution with real filesystem | pytest |
| API | FastAPI endpoints: request/response contracts, error handling, JSON determinism | pytest + FastAPI TestClient |
| Component | React components: Kanban board, item modal, project selector, form validation | Vitest + React Testing Library |
| Functional E2E | User-visible browser workflows that cross screens, REST state, or browser behavior | Playwright |
| Browser contract | Browser-only style, token, theme, viewport, responsive, focus-ring, and visual-regression contracts | Playwright |

## Running Feature Scenarios

Per-feature `scenarios.md` files contain Gherkin `Given/When/Then` scenarios linked to
requirement IDs. Automated scenarios are run through pytest with a Gherkin-compatible runner
(e.g. pytest-bdd). A manual verification checklist accompanies each feature and runs at least
once before the feature is marked done.

## Web Test Commands

Run these from `web/`:

| Command | Scope |
| --- | --- |
| `npm run test` | All Vitest unit/component tests |
| `npm run test:component` | React component tests only |
| `npm run test:e2e` | Functional E2E suite |
| `npm run test:e2e:functional` | Functional E2E suite explicitly |
| `npm run test:browser-contract` | Browser-only token/theme/visual contract suite |

## Coverage Expectations

Before a feature is considered done:
- every requirement has at least one scenario covering its happy path;
- every requirement has at least one scenario covering a failure or edge case;
- the feature's manual checklist has been executed and passed;
- every UI requirement has an explicit test-level decision for component, API/contract,
  functional E2E, browser contract, or not applicable with a concrete reason;
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
- Functional E2E tests pass for any changed major UI path.
- Browser contract tests pass for changed token, theme, viewport, or visual browser contracts.
- `taskpilot validate` reports no errors in test fixture data.
- No critical scenarios are failing.
- Formatting, type checks, and lints pass across Python and TypeScript.
