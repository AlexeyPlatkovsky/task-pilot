# Traceability Standard

Every non-trivial routed handoff must emit a visible artifact before a downstream step advances.

Use one stable label:

- `Manager: <name> - output below`
- `Pipeline: <name> - output below`
- `Skill: <name> - output below`
- `Agent: <name> - output below`

Each artifact states status (`completed`, `skipped`, or `blocked`), scope, assumptions, checks,
and blockers. A table is required when multiple gates or files are checked.

Raw commands and tool output are evidence only. Missing artifacts block downstream routing.
