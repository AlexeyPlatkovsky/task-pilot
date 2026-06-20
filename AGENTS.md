# TaskPilot Agent Contract

## Role and Authority

This is the canonical operational contract for every AI coding tool in this repository.
Tool-specific entry files are adapters only and must stop if this file is unavailable.

Authority order:

1. User instructions in the active conversation.
2. This file.
3. Accepted specifications under `docs/specs/`.
4. `docs/taskpilot_concept.md`.
5. Architecture decisions under `docs/decisions/`.
6. Existing code, tests, and project conventions.

Do not silently resolve conflicts that change product behavior, public contracts, persistence, or
architecture. Report the conflict and obtain a decision.

## Product Invariants

- TaskPilot works offline and remains local-first.
- Markdown/YAML files are canonical task data.
- SQLite, when introduced, is disposable index/cache data and never the source of truth.
- Canonical files are written before indexes refresh.
- CLI, REST API, WebUI, and future MCP adapters use one domain/service layer.
- One file per item and separate append-style comments minimize Git conflicts.
- Reverse links are derived rather than stored twice.
- Serialization and JSON contracts are deterministic.
- Invalid files remain visible and actionable.
- Avoid cloud dependencies, accounts, hidden synchronization, and speculative enterprise scope.

## Mandatory Routing Gate

Before creating, editing, moving, or deleting files, state the task classification.

- Trivial and low risk: proceed directly and state why no pipeline is required.
- Non-trivial, or uncertain: load `.claude/skills/manager/SKILL.md`, emit its required manager
  artifact, and do not implement until the route is explicit.

The required manager artifact is `Manager: taskpilot-manager - output below`.

Non-trivial includes behavior changes, public contracts, persistence, cross-layer work,
architecture, production dependencies, multi-file workflows, and changes requiring coordinated
validation. A user saying "implement," "fix," or equivalent triggers this gate again.

Do not advance between routed steps without the visible output artifact required by the manager or
pipeline. Raw command output is evidence, not a routed artifact.

## Working Method

Use specification-driven development for non-trivial product work:

1. Discover relevant docs, code, tests, and constraints.
2. Create or update an accepted specification under `docs/specs/`.
3. Define acceptance criteria and test levels.
4. Implement the smallest complete vertical slice.
5. Validate with the smallest sufficient test matrix.
6. Obtain an independent review when the route requires it.
7. Synchronize affected documentation.
8. Close through `task-complete`.

Small local fixes may skip a new specification only when expected behavior is already explicit.

Ask before breaking APIs, changing canonical formats or source-of-truth rules, adding production
dependencies, destructive data operations, or unapproved architecture changes.

## Architecture Boundaries

```text
canonical task files
  -> parser / validator
  -> domain model and services
  -> CLI | REST API | future MCP
  -> WebUI through REST API
```

- UI and adapters translate inputs and outputs; they do not own domain rules.
- Filesystem and SQLite details do not leak into the domain model.
- Prefer direct file access until measured needs justify indexing.

## Capability Registry

Routing:

- Manager: `.claude/skills/manager/SKILL.md`
- Feature/change pipeline: `.claude/pipelines/feature-change.md`
- UI change pipeline: `.claude/pipelines/ui-change.md`
- Review pipeline: `.claude/pipelines/code-review.md`
- Instruction change pipeline: `.claude/pipelines/instruction-change.md`

Skills:

- Brainstorming: `.claude/skills/brainstorm/SKILL.md`
- Specification: `.claude/skills/spec-driven-development/SKILL.md`
- Implementation: `.claude/skills/implement-change/SKILL.md`
- Testing: `.claude/skills/test-change/SKILL.md`
- UI design: `.claude/skills/design-ui/SKILL.md`
- Validation: `.claude/skills/validate-change/SKILL.md`
- Documentation maintenance: `.claude/skills/maintain-docs/SKILL.md`
- Instruction maintenance: `.claude/skills/maintain-instruction-system/SKILL.md`
- Completion: `.claude/skills/task-complete/SKILL.md`

Agents:

- Independent code review: `.claude/agents/code-reviewer.md`
- Independent design review: `.claude/agents/design-reviewer.md`
- Instruction review: `.claude/agents/instruction-evaluator.md`
- Instruction scenario acceptance: `.claude/agents/artifact-acceptance-tester.md`

All runtime AI staff and supporting instruction artifacts live under `.claude/`. Load only the
capability required by the active route. Shared standards are under `.claude/conventions/`;
reusable project facts are indexed by `.claude/docs/README.md`.

## Quality and Safety

- Map each non-trivial change to explicit acceptance criteria.
- Test at the lowest level that proves behavior and at boundaries where contracts cross.
- Cover failure paths, invalid files, deterministic output, and relevant cross-platform paths.
- Do not weaken assertions, delete tests, or broadly update snapshots to force a pass.
- Run relevant formatting, types, tests, builds, CLI/API, and browser checks available in the repo.
- Report every skipped or blocked check and residual risk.
- Preserve unrelated changes and keep diffs narrow.
- Never commit, push, rewrite history, discard changes, or run destructive commands unless the user
  explicitly requests it.
- Do not claim completion without inspecting the final diff and emitting required validation,
  review, documentation, and completion artifacts.
