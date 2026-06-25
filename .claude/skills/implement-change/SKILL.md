---
name: implement-change
description: Implements production behavior from an accepted TaskPilot specification or explicit low-risk request. Does not own independent review or final closure.
---

# Implement Change

Prerequisites: an accepted specification or explicit behavior, known success criteria, and a
planned validation route.

1. Read affected code, tests, conventions, and decisions.
2. For every requirement in scope, enumerate boundary conditions:
   - null / empty / missing / unrecognized inputs;
   - conflicting or duplicate state (existing project, repeated id, etc.);
   - silent-failure paths (files that can't be parsed, unreadable, wrong format);
   - error-envelope overlap with framework defaults (same status code,
     different body shape from the framework's own error handler).
   Map each boundary to an observable assertion or to a documented limitation.
   Report the resulting table as part of the artifact.
3. Implement the smallest complete vertical slice.
4. Keep domain rules in services and translation in adapters.
5. Preserve canonical-file-first writes and deterministic outputs.
6. Add only production and directly required support changes; test implementation belongs to
   `test-change`.
7. Run narrow compile or static checks needed to catch implementation errors
   and code-quality issues — including unused parameters, unused imports,
   and dead code. Use the project's configured linter for the language
   (ruff for Python, ESLint for TypeScript). If no linter is configured,
   install one and add it to the project's dev dependencies, or document
   the gap as a blocker.
8. Inspect the implementation diff for unrelated churn, leaked abstractions, and missing errors.

Stop for an unapproved breaking contract, canonical migration, production dependency, destructive
operation, security model, or architecture choice.

The artifact begins with `Skill: implement-change - output below` and reports status, behavior,
changed files, assumptions, narrow checks, deviations, and blockers.
