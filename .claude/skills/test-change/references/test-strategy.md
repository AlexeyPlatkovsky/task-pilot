# TaskPilot Test Strategy

| Level | Use for |
| --- | --- |
| Unit | Pure domain rules, validation, graph operations, and deterministic serialization |
| Contract | Item frontmatter, CLI JSON, REST payloads, and error envelopes |
| Integration | Filesystem plus service, service plus index, and CLI plus workspace |
| API | HTTP adapters with real services |
| Component | React interaction and visible states |
| E2E | Critical browser journeys across real local layers |

Required mapping:

- Domain rule: unit.
- Canonical file format: unit + contract; add filesystem integration for reads/writes.
- Service operation: unit or integration according to real collaborators.
- CLI command: CLI integration + JSON contract.
- REST endpoint: API integration + contract.
- React interaction: component.
- Cross-surface critical workflow: one focused E2E.
- Bug fix: lowest-level regression test that reproduces the defect.

Use temporary workspaces, malformed and valid representative files, injected clocks and IDs, and
assert exact content/order when deterministic Git-friendly output is contractual.
