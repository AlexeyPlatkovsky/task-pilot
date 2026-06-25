# F005 REST API — Scenarios

## Scenarios

### F005-S1: List projects when projects are registered

Covers: F005-R2, F005-R7

```gherkin
Scenario: List registered projects
  Given a workspace with two registered projects "Alpha" (key VP) and "Beta" (key BT)
  When the client sends GET /api/projects
  Then the response status is 200
    And the response body is a JSON array with two elements
    And each element has fields id, key, name, and active
    And the element for "Alpha" has key "VP" and active true
```

### F005-S2: List projects when no projects are registered

Covers: F005-R2

```gherkin
Scenario: List projects with empty registry
  Given a workspace with no registered projects
  When the client sends GET /api/projects
  Then the response status is 200
    And the response body is an empty JSON array
```

### F005-S3: List items for a project excludes deleted items

Covers: F005-R3, F005-R7

```gherkin
Scenario: List items excludes deleted
  Given a project "Alpha" with items VP-1 (status backlog) and VP-2 (status deleted)
  When the client sends GET /api/projects/alpha/items
  Then the response status is 200
    And the response body contains VP-1
    And the response body does not contain VP-2
    And each item has fields id, title, type, status, priority, and valid
```

### F005-S4: Get item detail with comments

Covers: F005-R4, F005-R7

```gherkin
Scenario: Get item detail including comments
  Given a project "Alpha" with item VP-1 that has one comment
  When the client sends GET /api/projects/alpha/items/VP-1
  Then the response status is 200
    And the response body has field comments as a list with one element
    And the comment has fields schema_version, created_at, and body
    And all ItemDetail fields defined in web/src/types/index.ts are present
```

### F005-S5: Patch item status

Covers: F005-R5, F005-R7

```gherkin
Scenario: Update item status via PATCH
  Given a project "Alpha" with item VP-1 (status backlog)
  When the client sends PATCH /api/projects/alpha/items/VP-1 with body {"status": "in_progress"}
  Then the response status is 200
    And the response body has status "in_progress"
    And the canonical YAML file for VP-1 has status: in_progress
```

### F005-S6: Patch item with invalid status returns 422

Covers: F005-R8

```gherkin
Scenario: Update item with invalid status
  Given a project "Alpha" with item VP-1
  When the client sends PATCH /api/projects/alpha/items/VP-1 with body {"status": "flying"}
  Then the response status is 422
    And the response body has field detail
```

### F005-S7: Get items for unknown project returns 404

Covers: F005-R8

```gherkin
Scenario: List items for unknown project
  Given a workspace with no project keyed "ghost"
  When the client sends GET /api/projects/ghost/items
  Then the response status is 404
    And the response body is {"detail": "Project not found: ghost"}
```

### F005-S8: Get unknown item returns 404

Covers: F005-R8

```gherkin
Scenario: Get detail for unknown item
  Given a project "Alpha" with no item "VP-999"
  When the client sends GET /api/projects/alpha/items/VP-999
  Then the response status is 404
    And the response body has field detail
```

### F005-S9: Start server via CLI

Covers: F005-R6

```gherkin
Scenario: Start server with custom port
  Given a valid workspace
  When the user runs "taskpilot serve --port 9000"
  Then the server starts and listens on port 9000
    And GET http://localhost:9000/docs returns HTTP 200
```

### F005-S10: JSON response is deterministic

Covers: F005-R7

```gherkin
Scenario: Repeated GET returns identical JSON
  Given a project "Alpha" with item VP-1
  When the client sends GET /api/projects/alpha/items/VP-1 twice without any writes between requests
  Then both responses have identical JSON bodies
```

## Manual Verification Checklist

- [ ] (F005-R1) `GET /docs` returns the FastAPI OpenAPI UI listing all nine routes (health, projects, items list, item detail, item patch).
- [ ] (F005-R2) `GET /api/projects` with two registered projects returns both with correct `key` and `name` values.
- [ ] (F005-R3) Creating an item via CLI, then calling `GET /api/projects/{id}/items`, returns the new item in the list.
- [ ] (F005-R3) Deleting an item via CLI (status → deleted), then calling the items list endpoint, does not include the deleted item.
- [ ] (F005-R4) `GET /api/projects/{id}/items/{item_id}` for an item with comments returns them in chronological order.
- [ ] (F005-R5) `PATCH` with `{"status": "in_progress"}` updates the YAML file on disk and returns the new status in the response.
- [ ] (F005-R6) `taskpilot serve --host 127.0.0.1 --port 8080` starts and accepts connections on that address and port.
- [ ] (F005-R6) Stopping the server with Ctrl-C exits cleanly without a traceback.
- [ ] (F005-R8) `GET /api/projects/does-not-exist/items` returns HTTP 404 with a `detail` field.
- [ ] (F005-R9) With `npm run dev` running and `taskpilot serve` running, the project selector in the browser loads real project data without CORS errors in the browser console.
