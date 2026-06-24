# F007 Git Helpers — Scenarios

## Scenarios

### F007-S1: Show sync status

Covers: F007-R1

```gherkin
Scenario: Show sync status
  Given a Git repository with a TaskPilot workspace
    And VP-1.yaml has been modified but not staged
  When "taskpilot sync status" runs
  Then stdout lists "items/VP-1.yaml" as modified
    And exit code is 0
```

### F007-S2: Validate blocks commit

Covers: F007-R2

```gherkin
Scenario: Validate blocks commit
  Given item VP-3.yaml has a validation error (missing title)
  When "taskpilot sync validate" runs
  Then stderr lists the validation error
    And exit code is non-zero
```

### F007-S3: Pull rebases and validates files

Covers: F007-R3

```gherkin
Scenario: Pull rebases and validates files
  Given a clean Git repository with a valid TaskPilot workspace
    And a remote has new commits modifying VP-5.yaml
  When "taskpilot sync pull" runs
  Then "git pull --rebase" is executed and printed
    And "taskpilot validate" runs automatically
    And validation includes VP-5's updated content
```

### F007-S4: Push stages, commits, and pushes

Covers: F007-R4

```gherkin
Scenario: Push stages, commits, and pushes
  Given a Git repository with modified VP-1.yaml and a new comment file
  When "taskpilot sync push --yes" runs
  Then "git add .taskpilot/" stages the files
    And "git commit -m 'Update TaskPilot tasks'" creates a commit
    And "git push" pushes to the remote
```

### F007-S5: Export changes since ref

Covers: F007-R5

```gherkin
Scenario: Export changes since ref
  Given the last 2 commits modified VP-1.yaml and VP-3.yaml
  When "taskpilot sync export --since HEAD~2" runs
  Then stdout lists VP-1 and VP-3 as changed items
    And includes the change type (modified, added, deleted) for each
```

## Manual Verification Checklist

- [ ] (F007-R4) `sync push` without `--yes` prompts for confirmation before staging and pushing.
- [ ] (F007-R3) `sync pull` with a dirty working tree warns and exits non-zero without `--force`.
- [ ] (F007-R1) `sync status` in a directory that is not a Git repository prints an error.
- [ ] (F007-R5) `sync export` with no changes since ref prints a "no changes" message.
