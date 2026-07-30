# TaskPilot Specifications

This folder holds the accepted product contracts.

Each specification records outcome, scope, requirements, design effects, acceptance criteria, test
strategy, implementation slices, risks, assumptions, and open questions.

Specifications use one of these states: `draft`, `accepted`, or `implemented`.

A state applies to the specification as a whole, not to every statement inside it. A behavioral
statement that does not describe shipped behavior carries an inline marker — `[planned]`,
`[not implemented]`, or `[superseded: <ref>]`. The marker vocabulary is defined under "Statement
status markers" in [0002](0002-alpha-product-and-stack-decisions.md) and applies to every
specification here. A marked statement is not evidence of shipped behavior, and neither is a
requirement-register statement ("shall", "should", "could") in a specification that is `accepted` but
not yet `implemented` — it states what was agreed, not what ships.

Whether a given change requires a specification is decided by the specification-materiality scan in
`.claude/skills/manager/SKILL.md`, which is where routing gates live. It is deliberately not restated
here: a normative gate sitting in `docs/` would be editable through documentation-only routing.

## Index

| Spec | Status | Purpose |
| --- | --- | --- |
| [0001: Product Foundation](0001-product-foundation.md) | ✅ accepted | Establishes the initial product contract, vocabulary, architecture boundaries, and unresolved follow-up specs. |
| [0002: Alpha Product and Stack Decisions](0002-alpha-product-and-stack-decisions.md) | ✅ accepted | Captures current Alpha/Beta/Release decisions for storage, registry, item model, comments, WebUI, and tech stack. |
| [0003: CSS Design Token System and Icon Library](0003-design-token-system.md) | ✅ accepted | Introduces 55 semantic CSS custom properties, light/dark themes, and lucide-react icon library. |
| [0004: Beta Item Detail Redesign](0004-beta-item-detail-redesign.md) | ✅ implemented | Settles and implements the Beta item modal information architecture without changing canonical files or API contracts. |
