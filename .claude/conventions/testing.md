# Testing Standard

- Follow the testing pyramid: many unit tests, fewer contract/API/component/integration tests, and
  E2E tests only for major paths that lower levels cannot prove.
- Unit tests own pure domain rules, parsing, validation, graph/link behavior, deterministic
  serialization, and other logic that can run without adapters.
- Contract tests own canonical file shapes, CLI JSON, REST payloads, error envelopes, and stable
  ordering.
- API tests own FastAPI route behavior over real services at the request/response boundary.
- Component tests own React rendering, state, validation, accessibility affordances, and user
  interactions inside a component or small component group.
- Integration tests own real boundaries such as filesystem plus service, CLI plus workspace, and
  service plus index/cache.
- Browser E2E tests own only critical cross-surface journeys and major UI paths. Use Playwright
  with TypeScript and the repository's Playwright CLI/script when browser automation is required.
- A major UI path is a workflow that crosses screens or browser state, depends on the REST API,
  exercises drag/drop or keyboard alternatives, verifies responsive behavior, or represents a
  primary user journey such as project selection, board navigation, item editing, or invalid-file
  recovery.
- A critical cross-surface journey is a user-visible workflow that crosses at least two adapters or
  process boundaries, such as CLI-created data appearing in the WebUI through the REST API.
- Smallest sufficient validation means the lowest-level checks that prove each requirement plus the
  boundary checks for changed contracts; it must not replace missing lower-level evidence with broad
  E2E coverage.
- Name tests by observable behavior and condition.
- Prefer behavior assertions over implementation details.
- Use minimal explicit fixtures and deterministic temporary workspaces.
- Do not use external networks, user home directories, arbitrary sleeps, or hidden shared state.
- Contract tests verify success and error shapes.
- UI tests use accessible roles, labels, and visible text.
- UI implementation should be proven primarily by component tests, with Playwright evidence for
  major browser paths, responsive behavior, drag/drop, keyboard navigation, and API-backed flows.
- Do not weaken assertions or update snapshots without inspecting the semantic change.
