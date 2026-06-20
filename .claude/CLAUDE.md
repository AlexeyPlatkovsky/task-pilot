# Claude Code Entry Point

This file is the Claude Code entry point for TaskPilot. It does not define independent policy.

Before any project analysis, planning, tool call, file read, or file change, Claude Code must import
and obey the complete canonical root contract:

@../AGENTS.md

Every rule in root `AGENTS.md` is mandatory. Root `AGENTS.md` always wins over this file and every
other artifact under `.claude/`. If `AGENTS.md` cannot be loaded, stop immediately and report that
the canonical contract is unavailable.

All additional TaskPilot AI staff, skills, pipelines, conventions, and AI reference documents are
located under `.claude/` and must be loaded only as routed by `AGENTS.md`.
