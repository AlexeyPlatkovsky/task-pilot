# F008 MCP Adapter — Tasks

| ID | Task | Implements | Status | Depends on |
| --- | --- | --- | --- | --- |
| F008-T1 | Scaffold MCP server module using Python MCP SDK (e.g. `mcp` package) with stdio transport | F008-R1 | ⏳ todo | — |
| F008-T2 | Implement `project_list` MCP tool calling F002 project service | F008-R1, F008-R5 | ⏳ todo | F008-T1, F002-T1 |
| F008-T3 | Implement `item_create` and `item_update` MCP tools | F008-R2, F008-R5 | ⏳ todo | F008-T1, F002-T2 |
| F008-T4 | Implement `item_search` MCP tool with filter parameters | F008-R2, F008-R5 | ⏳ todo | F008-T1, F002-T2 |
| F008-T5 | Implement `item_link` MCP tool | F008-R3, F008-R5 | ⏳ todo | F008-T1, F002-T4 |
| F008-T6 | Implement `item_ready` and `item_tree` MCP tools | F008-R4, F008-R5 | ⏳ todo | F008-T1, F002-T2 |
| F008-T7 | Ensure deterministic JSON output schema matches CLI JSON format | F008-R6 | ⏳ todo | F008-T2, F008-T3, F003-T1 |

## Notes

- Use MCP Python SDK for standard tool registration and JSON-RPC handling.
- Each tool function is a thin wrapper: parse arguments -> call domain service -> serialize response.
- Error responses should include descriptive messages matching CLI error patterns.
