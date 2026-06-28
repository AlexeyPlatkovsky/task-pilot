---
name: test-change
description: Designs, writes, or reviews TaskPilot tests for changed behavior across unit, contract, integration, CLI, API, component, and browser levels.
---

# Test Change

Read `references/test-strategy.md` and `.claude/conventions/testing.md`.

1. State the test phase: tests-first, characterization, post-implementation execution, or review.
2. Map requirements, bug behavior, or preserved refactor behavior to observable assertions.
3. Select the lowest-cost level that proves each behavior using `.claude/conventions/testing.md`.
4. Produce a test-level matrix before editing tests. Each changed requirement must have one row with:
   requirement or behavior, assertion, selected level, test file path, tests-first status, and
   explicit skip reason when a level is not applicable. For UI work, include separate decisions for
   component, API/contract, functional E2E, and browser contract. A major UI path must name a
   committed functional Playwright TypeScript test path, unless an existing functional E2E test
   already covers it and is named in the row.
5. Add boundary tests where data crosses files, services, CLI, REST, or browser boundaries.
6. Cover success plus relevant invalid input, missing references, conflict/error behavior, and
   deterministic output.
7. Use red-green-refactor for behavior changes unless the active route explicitly permits a
   different order. For refactors, add characterization tests first when existing coverage is weak.
8. For UI changes, apply `.claude/conventions/testing.md` for component, functional Playwright E2E,
   and browser contract scope. Keep functional E2E user-journey assertions separate from CSS token,
   computed-style, screenshot-only, and visual contract assertions. When the element refs,
   accessible names, or DOM structure required for assertions cannot be determined from static
   repository source files such as TypeScript/JSX source — committed playwright-cli snapshot files
   satisfy this condition only when they were generated against the current component structure; if
   the component may have changed since the last committed snapshot, treat refs as unavailable and
   invoke `playwright-cli` per
   `.claude/conventions/testing.md`. Require `Skill: playwright-cli - output below` when this
   investigation step runs.
9. Run narrow tests, then the affected suite, including the required component, functional E2E, and
   browser contract commands when those levels are selected by the matrix.
10. Inspect for false positives, brittle mocks, timing assumptions, over-broad E2E coverage,
   misplaced style/token assertions in functional E2E, hidden shared state, over-engineered helper
   extraction, and redundant coverage.

Do not change production behavior unless the active route assigns that scope.

The artifact begins with `Skill: test-change - output below` and reports status, requirements,
phase, the test-level matrix, selected levels, test files, commands and results, pyramid
justification, gaps, flakiness risks, and blockers.
