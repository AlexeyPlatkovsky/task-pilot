# Testing Standard

- Follow the testing pyramid: many unit tests, fewer contract/API/component/integration tests, and
  E2E tests only for major paths that lower levels cannot prove.
- Unit tests own pure domain rules, parsing, validation, graph/link behavior, deterministic
  serialization, and other logic that can run without adapters.
- Contract tests own canonical file shapes, CLI JSON, REST payloads, error envelopes, and stable
  ordering.
- API tests own FastAPI route behavior over real services at the request/response boundary.
- Component tests own React rendering, state, validation, accessibility affordances, and user
  interactions inside a component or small component group. Component tests are React tests run with
  Vitest and Testing Library; they must be listed separately from pure unit tests in test artifacts
  even when both run through the same command.
- Integration tests own real boundaries such as filesystem plus service, CLI plus workspace, and
  service plus index/cache.
- Functional browser E2E tests own only critical cross-surface journeys and major UI paths. They
  must assert user-observable workflow behavior through accessible UI interactions and REST-backed
  state, not CSS token values, computed style contracts, screenshot-only checks, implementation
  selectors, or component-internal state.
- Browser contract tests own browser-only style, token, theme, viewport, responsive, focus-ring, and
  visual-regression contracts. Keep these separate from functional E2E files and report them as a
  distinct test level.
- Use persistent Playwright TypeScript tests for required functional E2E and browser contract
  coverage. Use the repository's Playwright script/config for execution.
- `playwright-cli` is the AI investigation tool for live browser interaction. Use it to discover
  accessible names, stable element refs, and DOM structure before writing static Playwright
  TypeScript test files, and to gather browser evidence during validation. Prefer refs from the
  current accessibility snapshot over CSS selectors; re-snapshot after any action that adds,
  removes, or repositions DOM elements (navigation, form submission, modal open/close, list item added, removed, or reordered).
  `playwright-cli` findings are evidence that informs test authoring; they are not a substitute for
  persistent Playwright TypeScript test files in the repository.
- A major UI path is a workflow that crosses screens or browser state, depends on the REST API,
  exercises drag/drop or keyboard alternatives, verifies responsive behavior, or represents a
  primary user journey such as project selection, board navigation, item editing, or invalid-file
  recovery.
- A critical cross-surface journey is a user-visible workflow that crosses at least two adapters or
  process boundaries, such as CLI-created data appearing in the WebUI through the REST API.
- Smallest sufficient validation means the lowest-level checks that prove each requirement plus the
  boundary checks for changed contracts; it must not replace missing lower-level evidence with broad
  E2E coverage.
- UI test planning must classify every changed UI requirement into one of: component, API/contract,
  functional E2E, browser contract, or not applicable with a concrete reason. A major UI path
  requires committed functional E2E unless the requirement is already covered by an existing
  functional E2E test named in the test artifact.
- Name tests by observable behavior and condition.
- Prefer behavior assertions over implementation details.
- Use minimal explicit fixtures and deterministic temporary workspaces.
- Do not use external networks, user home directories, arbitrary sleeps, or hidden shared state.
- Contract tests verify success and error shapes.
- UI tests use accessible roles, labels, and visible text.
- UI implementation should be proven primarily by component tests, with Playwright evidence for
  major browser paths, responsive behavior, drag/drop, keyboard navigation, and API-backed flows.
- UI controls with finite option sets must cover every meaningful option or every enum member,
  not only one representative value, unless the test artifact explains why the remaining values are
  mechanically equivalent. Filter controls must also cover the default state, reset/clear behavior,
  filtered-empty behavior, and at least one combined-filter case.
- Sorting controls must cover the default, ascending, and descending visible indicators plus the
  accessible sort state. If product docs define canonical icons or glyphs, tests must assert those
  indicators directly rather than accepting arbitrary text labels.
- Custom dropdowns, menus, and popovers must have component coverage for trigger labeling,
  selected option display, selected/hover/focus state contract, below/anchored placement when
  required, close behavior, and parity with any existing selector pattern they replace.
- Drag/drop, optimistic updates, and local cache updates must cover the transient user-visible
  state between the user action and the confirmed server/cache result. A passing final-state test
  is insufficient when stale cached data could briefly reappear.
- UI logic that depends on current time, cache contents, or parent re-renders must include a
  deterministic regression test for those changing inputs when the behavior would be visible to
  users.
- Functional E2E authoring should stay TaskPilot-native. Start with small helpers under
  `web/e2e/support` for deterministic workspaces, project opening, and repeated domain locators.
  Do not introduce a copied browser framework, custom locator proxy, page-object DSL, reporting
  stack, or lint plugin until the same setup, navigation, or assertion pattern appears in at least
  three committed functional specs, or validation records a flaky or false-positive failure caused
  by missing helper structure.
- Functional E2E helpers may expose stable domain selectors such as item IDs and workflow statuses
  when no accessible role cleanly scopes a board region. When a test uses a domain selector, it
  must also include a user-visible role, label, text, or REST-backed assertion for the same workflow,
  or record why the UI exposes no accessible control for that interaction.
- Functional E2E uses Page Objects under `web/e2e/pages`. Functional specs under
  `web/e2e/functional` must not construct Playwright locators; specs call Page Object methods for
  browser actions and assertions.
- Page Objects use `data-test-id` as the primary selector. The attribute value must be stable,
  kebab-case, and domain-oriented. Role, label, or text locators are allowed inside Page Objects
  only as secondary user-visible assertions or when adding a stable `data-test-id` is impossible;
  the exception must be reported in the E2E artifact.
- E2E is part of TDD for UI work. Each selected functional E2E row must state why unit, component,
  or API coverage cannot fully prove the workflow. Every UI implementation change runs the affected
  functional E2E scope after implementation, or records why no functional E2E scope applies.
- Review functional E2E additions for flakiness, hidden shared state, over-broad coverage,
  implementation-only selectors, sleeps, false positives, and over-engineered helper extraction.
- CSS token and theme correctness should be tested as unit/component CSS-contract checks when the
  runtime can prove them, or browser contract tests when a real browser is required. Do not place
  token-only or computed-style-only checks in functional E2E.
- Do not weaken assertions or update snapshots without inspecting the semantic change.
