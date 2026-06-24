---
name: test-change
description: Designs, writes, or reviews TaskPilot tests for changed behavior across unit, contract, integration, CLI, API, component, and browser levels.
---

# Test Change

Read `references/test-strategy.md` and `.claude/conventions/testing.md`.

1. State the test phase: tests-first, characterization, post-implementation execution, or review.
2. Map requirements, bug behavior, or preserved refactor behavior to observable assertions.
3. Select the lowest-cost level that proves each behavior using `.claude/conventions/testing.md`.
4. Add boundary tests where data crosses files, services, CLI, REST, or browser boundaries.
5. Cover success plus relevant invalid input, missing references, conflict/error behavior, and
   deterministic output.
6. Use red-green-refactor for behavior changes unless the active route explicitly permits a
   different order. For refactors, add characterization tests first when existing coverage is weak.
7. For UI changes, apply `.claude/conventions/testing.md` for component, Playwright TypeScript, and
   E2E scope.
8. Run narrow tests, then the affected suite.
9. Inspect for false positives, brittle mocks, timing assumptions, over-broad E2E coverage, and
   redundant coverage.

Do not change production behavior unless the active route assigns that scope.

The artifact begins with `Skill: test-change - output below` and reports status, requirements,
phase, selected levels, test files, commands and results, pyramid justification, gaps, flakiness
risks, and blockers.
