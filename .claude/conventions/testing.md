# Testing Standard

- Name tests by observable behavior and condition.
- Prefer behavior assertions over implementation details.
- Use minimal explicit fixtures and deterministic temporary workspaces.
- Do not use external networks, user home directories, arbitrary sleeps, or hidden shared state.
- Contract tests verify success and error shapes.
- UI tests use accessible roles, labels, and visible text.
- E2E tests cover critical journeys not already proved at lower levels.
- Do not weaken assertions or update snapshots without inspecting the semantic change.
