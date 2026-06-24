# F005 SQLite Index — Scenarios

## Scenarios

### F005-S1: Rebuild index from files

Covers: F005-R1

```gherkin
Scenario: Rebuild index from files
  Given a workspace with 10 item YAML files and 5 comment files
    And index.db does not exist
  When index rebuild runs
  Then index.db contains 10 item rows and 5 comment rows
    And all item fields match their YAML file values
```

### F005-S2: Rebuild after deletion

Covers: F005-R2

```gherkin
Scenario: Rebuild after deletion
  Given index.db exists with 10 items indexed
  When index.db is deleted
    And "taskpilot index rebuild" runs
  Then index.db is recreated with the same 10 items
```

### F005-S3: Index status shows staleness

Covers: F005-R3

```gherkin
Scenario: Index status shows staleness
  Given index.db was rebuilt at 10:00
    And an item file was modified at 10:05
  When "taskpilot index status" runs
  Then the output indicates the index is stale
    And reports the item count and last rebuild time
```

### F005-S4: Filtered query matches file scan

Covers: F005-R4

```gherkin
Scenario: Filtered query matches file scan
  Given items with various statuses and types
  When querying the index for status=ready AND type=task
  Then the result set matches scanning all item YAML files with the same filter
```

### F005-S5: Reverse links available in index

Covers: F005-R5

```gherkin
Scenario: Reverse links available in index
  Given VP-1 has links.blocks containing VP-2
    And index was rebuilt
  When querying the index for items blocking VP-2
  Then VP-1 is returned
    And blocked_by is derived, not read from VP-2's file
```

### F005-S6: Cache directory git-ignored

Covers: F005-R6

```gherkin
Scenario: Cache directory git-ignored
  Given a workspace initialized with "taskpilot init ."
  When index.db is created under .taskpilot/cache/
  Then "git status" does not show index.db as untracked
```

### F005-S7: File written before index updated

Covers: F005-R7

```gherkin
Scenario: File written before index updated
  Given a workspace with a running index
  When an item is created through the domain layer
  Then the YAML file is written to disk first
    And the item is immediately queryable through the index
```

## Manual Verification Checklist

- [ ] (F005-R1) Index rebuild with 0 items produces an empty but valid index.db (no crash).
- [ ] (F005-R2) Running `index rebuild` twice in a row produces identical index.db content.
- [ ] (F005-R7) If the index update fails after a successful file write, the canonical file is still correct and a subsequent rebuild fixes the index.
- [ ] (F005-R6) `.taskpilot/cache/` is in the workspace's `.gitignore`, not the repo root's `.gitignore`.
