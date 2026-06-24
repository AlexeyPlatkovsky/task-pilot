# TaskPilot Test Strategy

This reference applies `.claude/conventions/testing.md`; that convention owns the testing pyramid,
major UI path, critical cross-surface journey, and smallest sufficient validation definitions.

| Level | Use for |
| --- | --- |
| Unit | Pure domain rules, validation, graph operations, deterministic serialization, parsing, and link behavior |
| Contract | Item frontmatter, CLI JSON, REST payloads, error envelopes, and deterministic ordering |
| API | HTTP adapters with real services at the request/response boundary |
| Component | React interaction, visible states, validation, accessibility affordances, and local UI state |
| Integration | Filesystem plus service, service plus index/cache, and CLI plus workspace |
| E2E | Critical browser journeys and major UI paths not already proved at lower levels |

Required mapping:

- Domain rule: unit.
- Canonical file format: unit + contract; add filesystem integration for reads/writes.
- Service operation: unit or integration according to real collaborators.
- CLI command: CLI integration + JSON contract.
- REST endpoint: API integration + contract.
- React interaction: component.
- Cross-surface critical workflow or major browser path: one focused Playwright TypeScript E2E.
- Bug fix: lowest-level regression test that reproduces the defect.

Use temporary workspaces, malformed and valid representative files, injected clocks and IDs, and
assert exact content/order when deterministic Git-friendly output is contractual.

Preserve the pyramid defined by `.claude/conventions/testing.md`.
