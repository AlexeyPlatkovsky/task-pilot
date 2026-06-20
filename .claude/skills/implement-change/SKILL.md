---
name: implement-change
description: Implements production behavior from an accepted TaskPilot specification or explicit low-risk request. Does not own independent review or final closure.
---

# Implement Change

Prerequisites: an accepted specification or explicit behavior, known success criteria, and a
planned validation route.

1. Read affected code, tests, conventions, and decisions.
2. State intended behavior, affected layers, and assumptions.
3. Implement the smallest complete vertical slice.
4. Keep domain rules in services and translation in adapters.
5. Preserve canonical-file-first writes and deterministic outputs.
6. Add only production and directly required support changes; test implementation belongs to
   `test-change`.
7. Run narrow compile or static checks needed to catch implementation errors.
8. Inspect the implementation diff for unrelated churn, leaked abstractions, and missing errors.

Stop for an unapproved breaking contract, canonical migration, production dependency, destructive
operation, security model, or architecture choice.

The artifact begins with `Skill: implement-change - output below` and reports status, behavior,
changed files, assumptions, narrow checks, deviations, and blockers.
