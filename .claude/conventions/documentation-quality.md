# Documentation Quality

## Purpose

Define shared quality standards for project documents and canonical task content.

This convention applies when creating, updating, or reviewing Markdown documents in the project,
including `docs/`, `.claude/`, root documentation files, and feature/specification documents, and
the title and description content of canonical TaskPilot items under `.taskpilot/`. Items are YAML
rather than Markdown but carry the same claims about project state.

For item content, `.claude/skills/ground-request/SKILL.md` is the capability that applies these
standards. That pointer is for discoverability; the gate itself belongs to the skill and the pipeline,
not to this convention.

## Gap Disclosure

Do not present a document as ready when known gaps remain unstated. If the document introduces,
changes, or summarizes project direction, behavior, implementation plans, operations, release
processes, design, architecture, specifications, or instructions, it must explicitly surface
material gaps that are known from the user request, existing docs, code, tests, or repository
structure.

Material gaps include:
- unresolved product, design, architecture, operational, or instruction decisions;
- missing or ambiguous contracts, owners, inputs, outputs, triggers, credentials, or publish
  targets;
- sequencing dependencies or prerequisites that must be settled before implementation or release;
- consistency conflicts with existing docs, accepted specs, decisions, code, tests, or package
  metadata;
- validation, migration, compatibility, security, release, rollback, or support risks;
- assumptions that affect scope, acceptance, or delivery.

Place gaps where a future reader will see them before acting on the document: in the affected
section, a dedicated `Gaps`, `Open Questions`, `Risks`, or `Prerequisites` section, or the artifact
summary. Do not wait for a separate review request to reveal obvious gaps.

Discussion of gaps may be deferred by an explicit instruction; recording them in the document is
not waivable. A general approval such as "looks fine" or "just add them" defers nothing; record the
gaps regardless.

## Evidence Boundary

Separate confirmed facts from assumptions. When a fact cannot be verified from user input,
repository evidence, accepted specs, or existing documents — except as narrowed below — mark it as
an assumption or blocker instead of writing it as settled project state.

A user assertion about current repository state is not verification. Claims that the repository
contains, supports, or behaves in some way must be confirmed against source, tests, configuration,
an accepted specification, or authoritative project documentation before being written as settled
state.

Authoritative project documentation is the subset of `docs/` that records delivered state:

| Source | Evidence for |
| --- | --- |
| `architecture.md`, `api.md` | Structure and contract surface as delivered |
| `specs/`, `decisions/` | Accepted behavior and decisions, subject to the marker rule below |
| `features/F<NNN>_*` | Only when that feature's `docs/INDEX.md` registry row reads `✅ implemented` |
| `design.md` | Shipped screens, states, and interaction patterns — not its UX principles |
| `testing.md` | The tooling and CI gates it describes — not coverage aspirations |
| `designs/design.md` | Delivered design-system tokens, icons, and component rules |

`docs/roadmap.md`, `docs/idea.md`, `docs/taskpilot_concept.md`, and everything under `.claude/docs/`
record intent and direction, so they are never evidence that something exists. `docs/INDEX.md` and
`.claude/docs/README.md` are lookup indexes, not evidence. `.claude/conventions/` states standards the
project holds itself to, which is not the same as behavior it has delivered; it is never evidence
either.

Even inside the recording set, a statement is evidence only when it is unqualified:

- a statement carrying `[planned]`, `[not implemented]`, or `[superseded: <ref>]` is not evidence of
  shipped behavior, and neither is one qualified by an equivalent in-use marker — `(future)`, `⏳`,
  `planned`, `directional`, `candidate`, or any wording that defers the behavior;
- a statement in the requirement or aspiration register — "shall", "should", "could" — states intent
  rather than delivery, whatever document it sits in;
- silence in a document is not evidence that something is absent;
- where documentation and source disagree, source is the fact and the document is defective — report
  the defect rather than propagating it.
