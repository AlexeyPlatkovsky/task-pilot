# Feature Change Pipeline

## Trigger

Use for a feature, refactor, or non-trivial bug fix that changes TaskPilot production behavior.

## Ordered Steps

1. Run `spec-driven-development` unless an accepted specification already covers the requested
   behavior. Require `Skill: spec-driven-development - output below`.
2. Run `implement-change`. Require `Skill: implement-change - output below`.
3. Run `test-change`. Require `Skill: test-change - output below`.
4. Run `validate-change`. Require `Skill: validate-change - output below`.
5. Run `code-reviewer` when the manager classified risk as medium, high, or system-level. Require
   `Agent: code-reviewer - output below`.

Stop on a blocked or failed step and return control to the manager. The manager owns documentation
maintenance and task-complete after this pipeline.

## Output Contract

Begin with `Pipeline: feature-change - output below` and report status, completed handoffs,
artifact labels, skipped steps with reasons, deviations, and blockers.
