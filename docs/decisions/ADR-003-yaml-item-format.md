# ADR-003: Pure YAML Item Files

- **Status:** ✅ accepted
- **Date:** 2026-06-23
- **Deciders:** TaskPilot project

## Context

The original concept document proposed item files as Markdown with YAML frontmatter — a
header block of structured YAML followed by a freeform Markdown body. This format is common
in static site generators and some note-taking tools.

However, for machine parsing and deterministic serialization, a hybrid format introduces
complexity: the parser must handle the boundary between YAML and Markdown, preserve or
normalize it on write, and decide how to round-trip edits. The `description` field can carry
Markdown content within a YAML string, achieving the same human readability without the
parsing ambiguity.

## Decision

Item files are pure YAML files (`.yaml` extension). All structured fields, including the
item description, live within the YAML document. The description field may contain Markdown
as a multiline YAML string.

Comment files remain Markdown with YAML frontmatter because comments are primarily human-written
prose that benefits from Markdown-first formatting.

## Consequences

- Parsing is unambiguous: a single YAML parser handles the entire file.
- Serialization is fully deterministic — no boundary between YAML and freeform Markdown.
- The description field supports Markdown through YAML multiline strings (`|` or `>`).
- The format is easily consumed by AI agents that already parse YAML.
- Comment files remain Markdown-first, which is their natural format.
- The earlier concept-doc examples showing Markdown+YAML format are superseded.

## Alternatives Considered

- **Markdown with YAML frontmatter** — rejected because parsing the boundary adds complexity
  and nondeterminism, and the same content fits cleanly in YAML multiline strings.
- **JSON files** — rejected because JSON lacks native multiline strings, comments, and is
  less human-friendly for hand-editing.
- **TOML files** — rejected because ecosystem support for TOML is narrower, and nested
  structures needed for links and fields are less ergonomic than YAML.
