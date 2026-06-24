# F008 MCP Adapter — Scenarios

## Scenarios

### F008-S1: List projects via MCP

Covers: F008-R1, F008-R5

```gherkin
Scenario: List projects via MCP
  Given the system registry has project "VoicePilot" (VP) and "PlayForge" (PF)
  When an MCP client calls the "project_list" tool
  Then the response contains a JSON array with two project objects
    And each object has "name" and "key" fields
    And the same domain service is called as "taskpilot project list --json"
```

### F008-S2: Create item via MCP

Covers: F008-R2, F008-R6

```gherkin
Scenario: Create item via MCP
  Given project VP exists
  When an MCP client calls "item_create" with project=VP, title="Benchmark", type="task"
  Then the item is created via F002 domain services
    And the response JSON matches the schema of "taskpilot item show VP-N --json"
    And the item file VP-N.yaml is written to disk
```

### F008-S3: Add link via MCP

Covers: F008-R3

```gherkin
Scenario: Add link via MCP
  Given items VP-1 and VP-2 exist
  When an MCP client calls "item_link" with source="VP-1", link_type="blocks", target="VP-2"
  Then VP-1.yaml is updated with links.blocks containing "VP-2"
    And the response confirms the link was added
```

### F008-S4: List ready items via MCP

Covers: F008-R4

```gherkin
Scenario: List ready items via MCP
  Given project VP has VP-1 (ready, epic) and VP-2 (ready, task) and VP-3 (backlog, bug)
  When an MCP client calls "item_ready" with project=VP
  Then the response contains VP-1 and VP-2 sorted by type then ID
    And VP-3 is not included
```

### F008-S5: MCP and CLI produce identical output

Covers: F008-R6

```gherkin
Scenario: MCP and CLI produce identical output
  Given item VP-1 exists
  When item data is requested via MCP "item_show" for VP-1
    And the same data is requested via "taskpilot item show VP-1 --json"
  Then both responses have the same field names and value types for all fields
```

## Manual Verification Checklist

- [ ] (F008-R5) Creating an item through MCP and then reading it through CLI shows consistent data.
- [ ] (F008-R5) MCP tool error for invalid input matches CLI error message content.
- [ ] (F008-R6) MCP response field ordering is deterministic and stable across calls.
- [ ] (F008-R1) MCP tool list includes all defined tools with proper descriptions.
