---
name: manager
description: Classifies and routes every non-trivial TaskPilot task to the correct pipeline, skill, or agent before execution.
user-invocable: false
---

# TaskPilot Work Manager

## Responsibility

Route non-trivial work only. Do not implement, review, test, or document changes in this file.

## Classification

Classify before edits:

- Complexity: trivial or non-trivial.
- Size: small, standard, or major.
- Risk: low, medium, high, or system-level.
- Reach: single area or cross-layer.
- Change type: feature, bug fix, refactor, UI, documentation, review, instruction, or brainstorm.
- Task backing: task-backed when the user supplies a task ID, a canonical TaskPilot item exists for
  the work, or the requested work clearly implements a tracked feature task; otherwise untracked.

Treat the task as non-trivial when it changes behavior, contracts, persistence, architecture,
production dependencies, or requires more than one coordinated capability.

Size definitions:

- Small: localized, low-risk, expected behavior already explicit, and no public contract,
  persistence, canonical format, cross-layer, or multi-step workflow change.
- Standard: non-trivial production change with bounded scope, one primary task or behavior, and
  no high-risk architecture, persistence, or canonical-format decision.
- Major: cross-layer, multi-feature, high-risk, contract/persistence/canonical-format, broad UI
  workflow, or work that needs multiple independent review gates.

## Route Selection

- Feature or non-trivial behavior-changing bug fix: `.claude/pipelines/feature-change.md`.
- Behavior-preserving refactor: `.claude/pipelines/refactor-change.md`.
- Product UI design or implementation: `.claude/pipelines/ui-change.md`.
- Read-only instruction-system review: `.claude/agents/instruction-evaluator.md`.
- Other read-only review request: `.claude/pipelines/code-review.md`.
- Open high-impact choice with materially different outcomes: `.claude/skills/brainstorm/SKILL.md`.
- Documentation-only work: `.claude/skills/maintain-docs/SKILL.md`, then validation and completion.
- Project instruction-system creation or material change: `.claude/pipelines/instruction-change.md`.

Framework stages under `.claude/manifesto/`, including `02_review.md`, are invoked explicitly by
the user. They are framework workflows, not project routing targets.

Use conditional rigor:

- Small low-risk changes may stay on the current branch, skip task movement, skip a new
  specification when behavior is already explicit, and validate with focused tests and checks.
- Standard or major task-backed feature work requires a fresh branch through `work-with-git` before
  implementation, unless the user explicitly overrides it or branch creation is blocked. The manager
  must state the branch source, branch name, and whether task-state hygiene is required before
  `work-with-git` runs.
- Major or high-risk feature work requires tests before implementation and independent review of
  the test scope before production changes.
- Refactors require characterization tests first when existing coverage does not prove preserved
  behavior.
- UI work requires component coverage and browser evidence for major paths when a runnable UI
  exists, as defined in `.claude/conventions/testing.md`.

For high-risk or system-level work, require independent review after validation. For medium-risk
production work, require independent review unless the change is documentation-only. For
`code-reviewer` and `design-reviewer` findings with Critical, High, or Major severity, require
fixes and re-review for up to three loops or stop with blockers. Severity definitions are owned by
`.claude/conventions/review-severity.md`. Agents with canonical verdict contracts, such as
instruction-system review agents, keep their own stop and retry rules. Each code/design review loop
returns to the responsible previous capability, reruns required validation, reruns the same
reviewer, and records the attempt count plus repeated artifact labels.

## Handoff Gate

Name every selected capability and expected artifact before execution. Do not advance when an
expected artifact is absent or reports blocked/failed status. Raw tool output is not a substitute.

When the manager selects a pipeline, that pipeline must be loaded and its first artifact emitted
before any implementation begins. Do not proceed directly to implementation even when tasks are
clearly defined.

When implementation changes behavior, interfaces, commands, architecture, domain facts, project
structure, or known failure modes, append documentation maintenance after substantive work.

Append task-complete to every non-trivial route. Before invoking it, verify every planned artifact
is present.

## Output Contract

Begin with:

`Manager: taskpilot-manager - output below`

Include:

- status;
- complexity, risk, and reach;
- size and change type;
- task backing;
- branch decision: fresh branch required or skipped, branch source and branch name or `N/A` when
  skipped, and reason;
- task-state decision: required or skipped, target task item when known, sanctioned update path,
  verification evidence required, and reason;
- selected pipeline or immediate capability;
- ordered handoffs and exact expected artifact labels;
- validation and independent-review requirements;
- documentation-maintenance decision;
- final task-complete step;
- assumptions and blockers.
