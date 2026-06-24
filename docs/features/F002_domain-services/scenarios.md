# F002 Domain Services — Scenarios

## Scenarios

### F002-S1: Create and read project

Covers: F002-R1

```gherkin
Scenario: Create and read project
  Given an initialized workspace
  When a project "VoicePilot" is created with key "VP"
  Then project.yaml contains name "VoicePilot" and key "VP"
    And reading the project returns those values
```

### F002-S2: Create and update item

Covers: F002-R2

```gherkin
Scenario: Create and update item
  Given project VP exists
  When an item is created with title "Add benchmark", type "task", priority "normal"
  Then the item file VP-1.yaml is written
    And reading VP-1 returns the title, type, and priority
  When VP-1 status is updated to "in_progress"
  Then VP-1.yaml shows status "in_progress"
    And updated_at is newer than created_at
```

### F002-S3: Enforce parent/child hierarchy rules

Covers: F002-R3

```gherkin
Scenario: Enforce parent/child hierarchy rules
  Given an epic VP-1 and a bug VP-2
  When setting VP-2's parent_id to VP-1
  Then the operation fails because a bug cannot be a child of an epic
  When creating a task VP-3 with parent_id VP-1
  Then VP-3.yaml shows parent_id "VP-1"
```

### F002-S4: Add and query link

Covers: F002-R4

```gherkin
Scenario: Add and query link
  Given items VP-1 and VP-2
  When a "blocks" link is added from VP-1 to VP-2
  Then VP-1.yaml shows links.blocks containing "VP-2"
    And VP-2.yaml is unchanged
    And querying links for VP-1 includes "blocks" -> ["VP-2"]
```

### F002-S5: Derive reverse links

Covers: F002-R5

```gherkin
Scenario: Derive reverse links
  Given VP-1 blocks VP-2
    And VP-3 blocks VP-2
  When querying all items and deriving reverse links
  Then VP-2's derived blocked_by list contains VP-1 and VP-3
    And no file stores "blocked_by" — it is computed
```

### F002-S6: Add comment without updating item

Covers: F002-R6

```gherkin
Scenario: Add comment without updating item
  Given item VP-1 with updated_at "2026-06-20T10:00:00Z"
  When a comment "Investigated parser" is added to VP-1
  Then comments/VP-1/ contains a new .md file
    And VP-1.yaml updated_at is unchanged
    And listing comments for VP-1 returns the new comment sorted by timestamp
```

### F002-S7: Soft delete item

Covers: F002-R7

```gherkin
Scenario: Soft delete item
  Given item VP-5 with status "backlog"
  When VP-5 is deleted
  Then VP-5.yaml shows status "deleted"
    And VP-5.yaml still exists on disk
    And listing items with default filter excludes VP-5
    And directly reading VP-5 by ID still returns the item
```

### F002-S8: Reject invalid status on create

Covers: F002-R8

```gherkin
Scenario: Reject invalid status on create
  Given project VP exists
  When creating an item with status "imaginary_status"
  Then the operation returns a validation error
    And no file is written to items/
```

## Manual Verification Checklist

- [ ] (F002-R3) Attempting to set parent_id to a non-existent item returns an error.
- [ ] (F002-R3) Setting an item's parent_id to itself returns an error (no cycles).
- [ ] (F002-R8) Attempting to update an item that doesn't exist returns a descriptive error.
- [ ] (F002-R7) Deleting an already-deleted item succeeds silently (idempotent).
