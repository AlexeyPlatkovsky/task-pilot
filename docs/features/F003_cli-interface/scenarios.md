# F003 CLI Interface — Scenarios

## Scenarios

### F003-S1: Initialize workspace via CLI

Covers: F003-R1

```gherkin
Scenario: Initialize workspace via CLI
  Given the current directory has no .taskpilot/
  When the user runs "taskpilot init ."
  Then .taskpilot/ is created
    And stdout confirms the workspace was initialized
    And exit code is 0
```

### F003-S2: List projects in JSON format

Covers: F003-R3, F003-R8

```gherkin
Scenario: List projects in JSON format
  Given a registered project VP
  When the user runs "taskpilot project list --json"
  Then stdout contains a JSON array with one object
    And the object has keys "name" and "key" in deterministic order
    And exit code is 0
```

### F003-S3: Create item with all required fields

Covers: F003-R4

```gherkin
Scenario: Create item with all required fields
  Given project VP exists
  When the user runs "taskpilot item create --project VP --title 'Benchmark task' --type task --priority high"
  Then a new item is created with the next available ID
    And stdout prints the item ID
    And exit code is 0
```

### F003-S4: Show item with JSON output

Covers: F003-R4, F003-R8

```gherkin
Scenario: Show item with JSON output
  Given item VP-1 exists with title "Benchmark task"
  When the user runs "taskpilot item show VP-1 --json"
  Then stdout contains a JSON object with id "VP-1" and title "Benchmark task"
    And running the command again produces identical output
```

### F003-S5: Add link between items

Covers: F003-R5

```gherkin
Scenario: Add link between items
  Given items VP-1 and VP-2 exist
  When the user runs "taskpilot item link VP-1 blocks VP-2"
  Then stdout confirms the link was added
    And running the same command again succeeds (idempotent)
    And exit code is 0
```

### F003-S6: Add comment to item

Covers: F003-R6

```gherkin
Scenario: Add comment to item
  Given item VP-1 exists
  When the user runs "taskpilot item comment VP-1 'Reviewed implementation'"
  Then a comment file is created under comments/VP-1/
    And stdout prints the comment filename
    And exit code is 0
```

### F003-S7: Validate clean workspace

Covers: F003-R7

```gherkin
Scenario: Validate clean workspace
  Given a workspace with all valid item files
  When the user runs "taskpilot validate"
  Then stderr is empty
    And exit code is 0
```

### F003-S8: Validate workspace with errors

Covers: F003-R7

```gherkin
Scenario: Validate workspace with errors
  Given a workspace where TP-2.yaml is missing a title
  When the user runs "taskpilot validate"
  Then stderr lists the error with file path and missing field
    And exit code is non-zero
```

### F003-S9: Start REST API server

Covers: F003-R2

```gherkin
Scenario: Start REST API server
  Given a registered project VP exists
  When the user runs "taskpilot serve --port 8080"
  Then stdout confirms the server is listening on port 8080
    And the process runs until interrupted
  When the user sends SIGINT
  Then the server shuts down cleanly
    And exit code is 0
```

## Manual Verification Checklist

- [ ] (F003-R1) `taskpilot init .` in a non-empty directory with existing files succeeds and does not delete existing files.
- [ ] (F003-R4) `taskpilot item create` with missing required fields prints usage error to stderr and exits non-zero.
- [ ] (F003-R4) `taskpilot item update VP-NONEXISTENT` prints error and exits non-zero.
- [ ] (F003-R5) `taskpilot item link VP-1 blocks VP-NONEXISTENT` prints error about target not found.
- [ ] (F003-R2) `taskpilot serve` without `--port` uses a default port and prints the listening URL.
- [ ] (F003-R8) JSON output across multiple calls with no state changes is byte-identical.
