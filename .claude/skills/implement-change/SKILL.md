---
name: implement-change
description: Implements production behavior from an accepted TaskPilot specification or explicit low-risk request. Does not own independent review or final closure.
---

# Implement Change

Prerequisites: an accepted specification or explicit behavior, known success criteria, and a
planned validation route.

1. Read affected code, tests, conventions, and decisions.
   For WebUI component-library or existing-page UI work, include
   `.claude/conventions/ui-component-library.md`.
2. Verify the implementation scope still matches accepted specs, roadmap, design docs, and recorded
   open questions. If implementation would expand or narrow release scope, change an accepted
   editable/read-only field boundary, alter persistence or API contracts, or resolve an open product
   question without explicit approval, stop and report a scope-delta blocker. Do not convert an
   ambiguous request into implemented behavior.
3. For every requirement in scope, enumerate boundary conditions:
   - null / empty / missing / unrecognized inputs (in PATCH semantics
     ``null`` = explicitly cleared field, ``missing`` = not sent — distinct);
   - conflicting or duplicate state (existing project, repeated id, etc.);
   - silent-failure paths (files that can't be parsed, unreadable, wrong format);
   - error-envelope overlap with framework defaults (same status code,
     different body shape from the framework's own error handler).

   Map each boundary to an observable assertion or to a documented limitation.
   Report the resulting table as part of the artifact. The boundary-condition
   table complements the test plan produced by ``test-change`` step 3 — it is
   not a replacement. When the pipeline deferred tests (mapping-only mode),
   this step must check that the existing mapping is complete and add any
   boundaries discovered during implementation.
4. Implement the smallest complete vertical slice.
5. Keep domain rules in services and translation in adapters.
6. Preserve canonical-file-first writes and deterministic outputs.
7. Add only production and directly required support changes; test implementation belongs to
   `test-change`.
8. Run narrow compile or static checks needed to catch implementation errors
   and code-quality issues — including unused parameters, unused imports,
   and dead code. Use the project's configured linter for the language
   (ruff for Python, ESLint for TypeScript). If no linter is configured,
   propose installing one; add it only with user approval, or document
   the gap as a blocker.
9. Inspect the implementation diff for unrelated churn, leaked abstractions, and missing errors.

Stop for an unapproved breaking contract, canonical migration, production dependency, destructive
operation, security model, or architecture choice.

The artifact begins with `Skill: implement-change - output below` and reports status,
scope-delta result, behavior, changed files, assumptions, narrow checks, deviations, and blockers.
