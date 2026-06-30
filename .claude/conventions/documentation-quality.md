# Documentation Quality

## Purpose

Define shared quality standards for project documents.

This convention applies when creating, updating, or reviewing Markdown documents in the project,
including `docs/`, `.claude/`, root documentation files, and feature/specification documents.

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

## Evidence Boundary

Separate confirmed facts from assumptions. When a fact cannot be verified from user input,
repository evidence, accepted specs, or existing documents, mark it as an assumption or blocker
instead of writing it as settled project state.
