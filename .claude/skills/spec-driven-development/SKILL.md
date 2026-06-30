---
name: spec-driven-development
description: Creates or refines an implementation-ready TaskPilot specification before non-trivial behavior, contract, persistence, API, or cross-layer work. Does not implement production code.
---

# Specification-Driven Development

Read `references/spec-template.md`, `.claude/conventions/documentation-quality.md`, and the
relevant sections of `.claude/docs/README.md`.

1. Inspect the concept, related specs and decisions, affected code, and tests.
2. State the user outcome, current behavior, boundaries, and non-goals.
3. Convert requirements into observable behavior; mark unsupported inferences as assumptions.
4. Define only affected domain concepts, canonical files, services, CLI/API contracts, and UI
   states.
5. Write independently testable Given/When/Then acceptance criteria.
6. Select test levels using `.claude/skills/test-change/references/test-strategy.md`.
7. Identify migration, compatibility, data-loss, concurrency, and cross-platform risks.
8. Split implementation into small vertical slices with observable completion.
9. Create or update `docs/specs/<descriptive-slug>.md`.

Stop before choosing between materially different product contracts without user authority.

The artifact begins with `Skill: spec-driven-development - output below` and reports status,
specification path, decisions, assumptions, acceptance criteria coverage, slices, planned
validation, and blockers.
