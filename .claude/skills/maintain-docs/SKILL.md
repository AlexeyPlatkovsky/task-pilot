---
name: maintain-docs
description: Synchronizes TaskPilot specifications, decisions, guides, commands, APIs, architecture, and domain facts after a change affects them.
---

# Maintain Documentation

Read `.claude/conventions/reference-docs.md`.

1. Inspect the actual diff and completed behavior.
2. Find authoritative documentation roots through `.claude/docs/README.md`.
3. Determine whether behavior, workflows, commands, setup, architecture, contracts, vocabulary, or
   known failure modes changed.
4. Update only affected authoritative sections and their indexes or links.
5. Update specification status and acceptance evidence when implementation completed.
6. Create an ADR only for a durable architecture decision with meaningful alternatives and
   consequences.
7. Verify commands, paths, examples, names, and links against repository facts.

Do not modify production code or tests. Report rather than guess when documentation should change
but the correct contract is unclear or outside scope.
If the diff, authoritative source, or implemented behavior cannot be inspected, stop and report the
missing context as blocked.

The artifact begins with `Skill: maintain-docs - output below` and reports status as documentation
updated, checked/no update needed, or blocked, plus sources, files, conflicts, assumptions, and
blockers.
