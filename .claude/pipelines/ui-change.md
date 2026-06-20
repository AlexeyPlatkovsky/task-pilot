# UI Change Pipeline

## Trigger

Use for TaskPilot product UI design or implementation, including list/detail, forms, validation
states, Kanban, tree, accessibility, responsive behavior, and visual-system changes.

## Ordered Steps

1. Run `spec-driven-development` unless an accepted specification already covers the requested
   behavior. Require `Skill: spec-driven-development - output below`.
2. Run `design-ui`; create or update `.claude/docs/design-book.md`. Require
   `Skill: design-ui - output below`.
3. When implementation is requested, run `implement-change`. Require
   `Skill: implement-change - output below`.
4. When implementation is requested, run `test-change`. Require
   `Skill: test-change - output below`.
5. Run `validate-change`, including visual evidence at desktop and narrow widths when a runnable UI
   exists. Require `Skill: validate-change - output below`.
6. Run `design-reviewer` in isolated fresh context. Require
   `Agent: design-reviewer - output below`.

Stop on a blocked or failed step and return control to the manager. The manager owns documentation
maintenance and task-complete.

## Output Contract

Begin with `Pipeline: ui-change - output below` and report status, design-book path, completed
handoffs, artifact labels, visual evidence, skipped implementation steps, and blockers.
