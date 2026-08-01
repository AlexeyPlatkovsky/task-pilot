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
`.claude/conventions/classification-scans.md`, invoked during classification by
`.claude/skills/manager/SKILL.md`, where routing gates live. It is deliberately not restated here: a
normative gate sitting in `docs/` would be editable through documentation-only routing.

## Index

| Spec | Status | Purpose |
| --- | --- | --- |
| [0001: Product Foundation](0001-product-foundation.md) | ✅ accepted | Establishes the initial product contract, vocabulary, architecture boundaries, and unresolved follow-up specs. |
| [0002: Alpha Product and Stack Decisions](0002-alpha-product-and-stack-decisions.md) | ✅ accepted | Captures current Alpha/Beta/Release decisions for storage, registry, item model, comments, WebUI, and tech stack. |
| [0003: CSS Design Token System and Icon Library](0003-design-token-system.md) | ✅ accepted | Introduces 55 semantic CSS custom properties, light/dark themes, and lucide-react icon library. |
| [0004: Beta Item Detail Redesign](0004-beta-item-detail-redesign.md) | ✅ implemented | Settles and implements the Beta item modal information architecture without changing canonical files or API contracts. |
| [0005: Daemon Lifecycle Commands](0005-daemon-lifecycle-commands.md) | ✅ accepted | Adds `start`/`stop`/`restart`/`status`/`logs` CLI commands to run and manage the server as a background daemon. |
| [0006: CLI Version Flag](0006-cli-version-flag.md) | ✅ implemented | Adds a `--version`/`-v` eager option to the root Typer callback so the raw Python CLI reports its version like the npm wrapper already does. |
| [0007: Linked To Status Indicator](0007-linked-to-status-indicator.md) | ✅ implemented | Amends 0004 F6: adds a status badge ahead of the ID/title link in each valid Linked to row; missing/invalid targets keep their existing state text instead. |
| [0008: Default Updated Filter](0008-default-updated-filter.md) | ✅ implemented | Changes the Board and List Updated filter's default from `Any time` to `Last 7 days`, always reapplied on load with no persistence. |
