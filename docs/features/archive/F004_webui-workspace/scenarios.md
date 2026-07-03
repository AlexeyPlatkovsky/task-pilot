# F004 WebUI Workspace — Scenarios

## Scenarios

### F004-S1: No registered projects

Covers: F004-R1, F004-R8

```gherkin
Scenario: No registered projects
  Given the system registry has no registered projects
  When the user opens the WebUI
  Then a message "No projects registered" is displayed
    And the message includes "taskpilot init ." as a hint
```

### F004-S2: Select project and see Kanban board

Covers: F004-R1, F004-R2

```gherkin
Scenario: Select project and see Kanban board
  Given the system registry has registered project "VoicePilot" (VP)
  When the user clicks "VoicePilot" in the project selector
  Then the Kanban board is displayed
    And columns "backlog", "ready", "in_progress", "done", "cancelled" are visible
```

### F004-S3: Cards sorted by type then ID

Covers: F004-R3

```gherkin
Scenario: Cards sorted by type then ID
  Given project VP has items: VP-1 (epic), VP-3 (task), VP-2 (feature), all in "backlog"
  When the Kanban board loads
  Then the backlog column shows cards in order: VP-1, VP-2, VP-3
```

### F004-S4: Open item detail modal in read mode

Covers: F004-R4

```gherkin
Scenario: Open item detail modal in read mode
  Given item VP-1 exists with title "Benchmark task" and status "backlog"
  When the user clicks the VP-1 card
  Then a modal opens showing title, type badge, status badge, priority label
    And the description (if any) is rendered as Markdown
    And linked items are listed
    And comments are shown chronologically
```

### F004-S5: Edit item in modal

Covers: F004-R5

```gherkin
Scenario: Edit item in modal
  Given the VP-1 detail modal is open in read mode
  When the user clicks "Edit"
  Then title becomes an editable text input
    And status becomes a dropdown
    And priority becomes a dropdown
  When the user changes status to "in_progress" and clicks "Save"
  Then the modal returns to read mode showing status "in_progress"
    And the VP-1 card moves to the "in_progress" column on the Kanban board
```

### F004-S6: Show read-only comments in modal

Covers: F004-R6

```gherkin
Scenario: Show read-only comments in modal
  Given the VP-1 detail modal is open
    And the comment thread shows existing comments
  Then no WebUI comment input is shown
    And comments are ordered chronologically
```

### F004-S7: Delete item with confirmation

Covers: F004-R7

```gherkin
Scenario: Delete item with confirmation
  Given the VP-5 detail modal is open
  When the user clicks "Delete"
  Then a confirmation dialog appears asking "Delete this item?"
  When the user confirms
  Then the modal closes
    And the VP-5 card disappears from the Kanban board
    And VP-5 is accessible via direct lookup with status "deleted"
```

### F004-S8: Empty board with prompt

Covers: F004-R8

```gherkin
Scenario: Empty board with prompt
  Given project VP has zero items
  When the Kanban board loads
  Then each column is empty
    And a message explains how to create the first item with the CLI
```

### F004-S9: Drag card to change status

Covers: F004-R9

```gherkin
Scenario: Drag card to change status
  Given VP-1 is a valid item in the "backlog" column
  When the user drags VP-1's card to the "in_progress" column
  Then VP-1's status updates to "in_progress" via API
    And the card appears in the "in_progress" column
    And the "backlog" column no longer shows VP-1
```

## Manual Verification Checklist

- [ ] (F004-R5) Editing an item and canceling reverts all field changes.
- [ ] (F004-R5) Saving with a blank title shows inline validation error near the title field.
- [ ] (F004-R6) The modal does not show comment add, edit, or delete controls.
- [ ] (F004-R8) If the API returns an error, an error message with retry button is displayed.
- [ ] (F004-R8) The modal shows a loading indicator while item data is being fetched.
- [ ] (F004-R9) Invalid item cards cannot be dragged.
- [ ] (F004-R9) Keyboard: focusing a card and pressing Right arrow moves it to the next status column.
