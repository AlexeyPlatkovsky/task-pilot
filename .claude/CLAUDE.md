# Claude Code Entry Point

Before any project analysis, planning, tool call, file read, or file change, Claude Code must import
and obey the complete canonical root contract:

@../AGENTS.md
@skills/manager/SKILL.md

Every rule in root `AGENTS.md` is mandatory. Root `AGENTS.md` always wins over this file and every
other artifact under `.claude/`. If `AGENTS.md` cannot be loaded, stop immediately and report that
the canonical contract is unavailable.
