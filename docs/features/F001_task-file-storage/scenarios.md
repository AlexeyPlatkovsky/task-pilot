# F001 Task File Storage — Scenarios

## Scenarios

### F001-S1: Initialize workspace in empty directory

Covers: F001-R1

```gherkin
Scenario: Initialize workspace in empty directory
  Given the current directory does not contain a .taskpilot/ folder
  When the user runs "taskpilot init ."
  Then a .taskpilot/ directory is created
    And it contains project.yaml with default schema_version
    And it contains items/ directory
    And it contains comments/ directory
    And project.yaml has the configured project identity
```

### F001-S2: Parse valid item YAML file

Covers: F001-R2

```gherkin
Scenario: Parse valid item YAML file
  Given .taskpilot/items/TP-1.yaml with all mandatory fields and title "Benchmark task"
  When the parser reads the file
  Then an item model is returned with id "TP-1"
    And title is "Benchmark task"
    And type is the value from the file
    And status is the value from the file
    And created_at and updated_at are valid timestamps
```

### F001-S3: Deterministic write round-trip

Covers: F001-R3

```gherkin
Scenario: Deterministic write round-trip
  Given an item model with all fields populated
  When the writer serializes and writes the item to disk
    And the parser reads the written file back
    And the writer serializes the parsed model again
  Then the second output is byte-identical to the first output
```

### F001-S4: Parse comment file with YAML frontmatter

Covers: F001-R4

```gherkin
Scenario: Parse comment file with YAML frontmatter
  Given .taskpilot/comments/TP-1/2026-06-23T10-00-00Z.md with valid frontmatter and Markdown body
  When the comment parser reads the file
  Then the model has created_at matching the filename timestamp
    And created_by is the value from frontmatter
    And body contains the Markdown content
```

### F001-S5: Comment timestamp collision disambiguation

Covers: F001-R5

```gherkin
Scenario: Comment timestamp collision disambiguation
  Given .taskpilot/comments/TP-1/2026-06-23T10-00-00Z.md already exists
  When a new comment is created at the same second
  Then the filename is 2026-06-23T10-00-00Z-2.md
    And created_at in the frontmatter is 2026-06-23T10:00:00Z
```

### F001-S6: Validate item missing required field

Covers: F001-R6

```gherkin
Scenario: Validate item missing required field
  Given .taskpilot/items/TP-2.yaml with id "TP-2" but no title field
  When validation runs
  Then a validation error is reported for TP-2
    And the error message includes "title" and the file path
    And validation exits non-zero
```

### F001-S7: Load project with mixed valid and invalid items

Covers: F001-R7

```gherkin
Scenario: Load project with mixed valid and invalid items
  Given .taskpilot/items/ contains TP-1.yaml (valid), TP-2.yaml (valid), and TP-3.yaml (invalid YAML)
  When the project loads
  Then TP-1 and TP-2 are available as valid items
    And TP-3 is listed as a validation error with file path and error message
    And no exceptions crash the loader
```

## Manual Verification Checklist

- [ ] (F001-R1) `taskpilot init .` in a directory already containing a `.taskpilot/` produces a clear error message instead of overwriting.
- [ ] (F001-R3) Writing an item with only mandatory fields produces only those fields in the output (no `null` or empty optional fields).
- [ ] (F001-R6) An item with an ID that doesn't match its filename (e.g. `TP-1.yaml` contains `id: VP-5`) is flagged as a validation error.
- [ ] (F001-R6) An item with `status: imaginary_status` is flagged with a message listing valid statuses.
- [ ] (F001-R5) Comment filenames sort chronologically when listed by the filesystem.
