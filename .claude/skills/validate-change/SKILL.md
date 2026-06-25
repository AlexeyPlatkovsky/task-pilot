---
name: validate-change
description: Performs final read-only validation that a TaskPilot change or review scope satisfies declared requirements without regressions.
---

# Validate Change

Validation is read-only.

1. Read the request, accepted specification, acceptance criteria, diff, and changed tests.
2. Map each requirement and planned gate to concrete evidence.
3. Run the smallest sufficient formatting, type, unit, contract, integration, component, API, E2E,
   build, and manual checks. For changes that touch Python files (`.py`, `.pyi`), always run
   `ruff format --check .` as a formatting gate. If ruff is unavailable, install it with
   `uv pip install ruff -q` and retry. Mark the formatting gate `pass` when zero files would be
   reformatted, `fail` when files would be reformatted (report the files), or `blocked` when the
   tool cannot be installed.
4. Apply `.claude/conventions/testing.md`; do not substitute broad E2E checks for missing
   lower-level evidence.
5. For runnable UI changes, include Playwright TypeScript evidence when that convention requires
   browser validation.
6. Distinguish implementation defects from environment blockers.
7. Check affected documentation and public contracts for drift.
8. Inspect the final diff for scope and regression risk.

Overall status is completed only when every required gate passes. Mark every gate `pass`, `fail`,
`skipped`, or `blocked`; skipped checks require a reason and residual risk.

The artifact begins with `Skill: validate-change - output below` and includes a table with gate,
evidence, result, and notes, followed by overall status, issues, assumptions, and blockers.
