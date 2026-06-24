# F008 MCP Adapter — Requirements

## Summary

Expose TaskPilot domain operations as MCP (Model Context Protocol) tools so MCP-native AI
clients can interact with tasks directly. The adapter is a thin layer that calls the shared
domain service layer (F002) — no separate business logic, no duplicated validation.

## Serves

- `roadmap.md` Phase 8 — MCP adapter
- `idea.md` — optional MCP adapter for MCP-native clients

## Functional Requirements

| ID | Requirement | Priority |
| --- | --- | --- |
| F008-R1 | The system shall expose project operations as MCP tools: `project_list` | should |
| F008-R2 | The system shall expose item operations as MCP tools: `item_create`, `item_update`, `item_search` | should |
| F008-R3 | The system shall expose link operations as MCP tools: `item_link` | could |
| F008-R4 | The system shall expose read operations as MCP tools: `item_ready` (list ready items), `item_tree` (hierarchy view) | could |
| F008-R5 | All MCP tools shall call the same F002 domain services used by CLI and REST API | must |
| F008-R6 | The MCP adapter shall produce deterministic JSON responses matching the same schemas as CLI JSON output | must |

## Acceptance Criteria

- **F008-R1:** An MCP client calling `project_list` receives a JSON array of registered projects.
- **F008-R2:** An MCP client calling `item_create` with title and type creates an item and returns the item ID and model.
- **F008-R3:** An MCP client calling `item_link` with source, link type, and target adds the link and returns confirmation.
- **F008-R4:** Calling `item_ready` for project VP returns items with status "ready", sorted by type and ID.
- **F008-R5:** Creating an item through MCP produces the same file output as creating it through CLI.
- **F008-R6:** JSON output for `item_show` through MCP matches the output of `taskpilot item show --json` field-for-field.

## Constraints

- MCP adapter is a Python module in `src/taskpilot/mcp/` (or similar).
- MCP adapter imports from `src/taskpilot/core/` — no code duplication.
- MCP protocol messages follow the standard MCP JSON-RPC format.
- MCP adapter only loads when explicitly started (e.g., `taskpilot mcp serve`).

## Out of Scope

- MCP transport negotiation (assumes stdio).
- MCP resource or prompt capabilities — tools only.
- Authentication or authorization for MCP connections.
- MCP server discovery or registration.
