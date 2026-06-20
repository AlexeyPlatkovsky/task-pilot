---
name: test-change
description: Designs, writes, or reviews TaskPilot tests for changed behavior across unit, contract, integration, CLI, API, component, and browser levels.
---

# Test Change

Read `references/test-strategy.md` and `.claude/conventions/testing.md`.

1. Map requirements or bug behavior to observable assertions.
2. Select the lowest-cost level that proves each behavior.
3. Add boundary tests where data crosses files, services, CLI, REST, or browser boundaries.
4. Cover success plus relevant invalid input, missing references, conflict/error behavior, and
   deterministic output.
5. Use red-green-refactor when behavior is not implemented and the route permits tests first.
6. Run narrow tests, then the affected suite.
7. Inspect for false positives, brittle mocks, timing assumptions, and redundant coverage.

Do not change production behavior unless the active route assigns that scope.

The artifact begins with `Skill: test-change - output below` and reports status, requirements,
selected levels, test files, commands and results, gaps, flakiness risks, and blockers.
