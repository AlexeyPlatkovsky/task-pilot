# F007 Git Helpers — Tasks

| ID | Task | Implements | Status | Depends on |
| --- | --- | --- | --- | --- |
| F007-T1 | Implement `sync status`: check `git status --porcelain` filtered to `.taskpilot/` files | F007-R1 | todo | F003-T1 |
| F007-T2 | Implement `sync validate`: run `taskpilot validate` with appropriate exit code | F007-R2 | todo | F003-T7 |
| F007-T3 | Implement `sync pull`: `git pull --rebase` + `taskpilot index rebuild`, print executed commands | F007-R3 | todo | F005-T3 |
| F007-T4 | Implement `sync push`: `git add .taskpilot/`, `git commit`, `git push` with confirmation | F007-R4 | todo | — |
| F007-T5 | Implement `sync export`: `git diff --name-only <ref>` filtered to `.taskpilot/`, summarize changed items | F007-R5 | todo | — |

## Notes

- `sync push` uses a standard commit message unless the user provides one via `--message`.
- `sync pull` should warn if the working tree is dirty before rebasing.
- All sync commands should handle the case where the current directory is not a Git repository.
