# F006 Advanced Views — Scenarios

## Scenarios

### F006-S1: Sort list view by column

Covers: F006-R1

```gherkin
Scenario: Sort list view by column
  Given the list view is displayed with items VP-1 (bug), VP-2 (epic), VP-3 (task)
  When the user clicks the "Type" column header
  Then rows are sorted by type alphabetically
  When the user clicks "Type" again
  Then rows are sorted in reverse order
```

### F006-S2: Filter list view

Covers: F006-R2

```gherkin
Scenario: Filter list view
  Given items include VP-1 (task, done) and VP-2 (bug, backlog)
  When the user selects "type=bug" filter
  Then only VP-2 is shown
  When the user adds "status=backlog" filter
  Then VP-2 remains visible (both filters match)
```

### F006-S3: Expand tree view hierarchy

Covers: F006-R3

```gherkin
Scenario: Expand tree view hierarchy
  Given VP-1 (epic) has child VP-2 (feature)
    And VP-2 has child VP-3 (task)
  When the tree view loads
  Then VP-1 is shown at the root with an expand arrow
  When the user clicks the expand arrow on VP-1
  Then VP-2 is shown as a child of VP-1 with its own expand arrow
  When the user clicks the expand arrow on VP-2
  Then VP-3 is shown as a child of VP-2
```

### F006-S4: Validation panel shows errors

Covers: F006-R4

```gherkin
Scenario: Validation panel shows errors
  Given item VP-3.yaml is missing the title field
  When the user opens the validation panel
  Then a list entry shows "VP-3: missing required field 'title'"
    And the file path is displayed
    And clicking the entry opens VP-3 in the item modal (with partial data)
```

### F006-S5: Switch between views

Covers: F006-R5

```gherkin
Scenario: Switch between views
  Given the user is viewing the Kanban board for project VP
  When the user clicks the "List" tab
  Then the list view is displayed with VP's items
  When the user clicks the "Tree" tab
  Then the tree view is displayed
  When the user clicks the "Board" tab
  Then the Kanban board is displayed again
```

## Manual Verification Checklist

- [ ] (F006-R3) An item without parent_id appears at the root level of the tree.
- [ ] (F006-R3) Circular parent_id relationships (detected by validation) do not cause infinite recursion in tree view.
- [ ] (F006-R4) Validation panel with zero errors shows "All items valid" message.
