# Classification Scans

## Purpose

Defines the three scans `.claude/skills/manager/SKILL.md` runs during classification, before
finalising a route. Each scan is self-contained procedure text; the manager decides when to run
them and what to do with a blocking result. This file is the sole owner of each scan's content —
no other artifact restates or forks these rules.

## Product-scope scan

Compare the request with accepted specs, roadmap, design docs, and recorded open questions before
finalising the route. If the request would expand or narrow release scope, change an accepted
editable/read-only field boundary, alter persistence or API contracts, turn an open question into
behavior, or interpret ambiguous polish language as product approval, stop and return a
scope-delta blocker instead of routing implementation. The blocker must state current accepted
behavior, requested or implied behavior, why it is a scope change, available options, and any
recommendation. Do not treat a new request as approval for the delta unless the user explicitly
acknowledges the scope change.

## Specification-materiality scan

Decide whether the change requires a specification before implementation, and record the decision
plus the clause that settled it. A specification is required when the change alters product
behavior visible to a user or API consumer; a public contract (CLI command or flag, REST request
or response shape, exit code, JSON envelope); persistence, canonical file format, or on-disk
layout; an accepted editable/read-only field boundary; architecture or a cross-layer boundary; or
the default behavior or default value of an already-accepted feature; a refactor that exposes a
new architecture decision, changes an import path, package name, or module location that code
outside the refactored package depends on, or has no explicit behavior-preservation boundary. A
specification is not required for a visual or cosmetic change that alters no value, rule, or
state stated normatively in `docs/` or `designs/design.md` — applying an existing documented
token for the purpose that document assigns it, at its documented value, is not such an
alteration; an internal refactor that preserves every contract and matches none of the refactor
triggers above; a test-only or documentation-only change; or a bug fix that restores behavior an
accepted specification already defines. Substituting a different token for a purpose the document
assigns to another token is such an alteration and requires a specification. The required list
wins on any overlap.

Changing a default is a behavior change even when the code is one line, and a visually cosmetic
change can still alter documented behavior — decide by what the change does, not by its diff
size. When neither list clearly applies, or both appear to, treat the change as requiring a
specification. This scan is the sole owner of the question; `docs/specs/README.md` points here
rather than restating it.

## Architecture-boundary scan

Before finalising the classification, read the diff to list every new cross-layer import the
change introduces and check each against the AGENTS.md Architecture Boundaries section. A "layer"
here means one of the project's top-level source directories: ``core``, ``services``, ``cli``,
``server``, ``web`` (the TypeScript frontend). In the AGENTS.md diagram, ``core`` + ``services``
together form "parser/validator → domain model and services". The adapters are ``cli``,
``server``, and future ``mcp`` — all fed by the same domain/service layer. Adapter→adapter
imports (``server``→``cli``, ``web``→``cli``, ``cli``→``server``, etc.) are mandatory violations.
Third-party library imports (fastapi, typer, etc.) are not in scope for this scan. If the scan
finds a violation and its severity is unclear, treat it as a blocker and return it to the user for
a routing decision rather than silently proceeding.
