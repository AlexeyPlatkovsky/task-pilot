# ADR-001: Markdown/YAML Files as Canonical Source of Truth

- **Status:** accepted
- **Date:** 2026-06-19
- **Deciders:** TaskPilot project

## Context

TaskPilot needs a storage format for task data that is human-readable, AI-friendly,
Git-compatible, and local-first. The format must produce clean diffs, avoid merge conflicts
where possible, and not require a running server to inspect.

A binary database (SQLite) as the source of truth would make Git diffs unreadable and
merges painful. A single JSON or YAML file for all items would cause frequent merge conflicts
when multiple agents work on different tasks. A cloud-hosted database contradicts the
local-first principle.

## Decision

YAML and Markdown files are the canonical source of truth. One file per item minimizes Git
conflicts. Comments are separate append-only Markdown files to further reduce merge pressure.
SQLite, if introduced later, is a disposable local index/cache, never the source of truth.

## Consequences

- Task files produce readable Git diffs.
- Merge conflicts are limited to items actually edited by multiple parties.
- Developers can inspect task state without TaskPilot running.
- Validation becomes critical — manually edited files can introduce errors.
- The system must handle file parsing, serialization, and an index layer on top of files.
- Rebuilding the index from files must be fast and reliable.

## Alternatives Considered

- **SQLite as source of truth** — rejected because binary databases are opaque in Git,
  merges are painful, and diffs are unreadable.
- **Single items.json file** — rejected because multi-agent edits would produce frequent
  merge conflicts.
- **Cloud-hosted database** — rejected because it contradicts local-first and offline
  requirements.
- **Markdown with YAML frontmatter per item** — rejected because spec 0002 selected pure
  YAML for deterministic machine parsing (see ADR-003).
