# ADR-004: Separate Append-Only Comment Files

- **Status:** accepted
- **Date:** 2026-06-19
- **Deciders:** TaskPilot project

## Context

Items have comments — threaded discussion or agent notes associated with a task. The simplest
storage approach is to embed comments inside the item file, but this creates merge conflicts
when multiple agents or users add comments to the same item simultaneously.

Since comments are frequently the most active part of an item (agents reporting progress,
users adding notes), embedding them in the item file would cause the item's `updated_at` to
change on every comment, producing false signals about substantive item changes.

## Decision

Comments are stored as separate append-only Markdown files, one per comment, under
`.taskpilot/comments/<ITEM_ID>/`. The filename is a UTC timestamp (`2026-06-23T10-00-00Z.md`)
which serves as the comment's identity. Comment content uses YAML frontmatter for metadata
(`created_at`, `created_by`) and Markdown body for the message.

Adding a comment does not update the parent item's `updated_at`. `updated_at` reflects changes
to the item YAML itself. A future `last_activity_at` can be derived from item timestamps and
comment timestamps.

Comment edit/delete is deferred until Beta.

## Consequences

- Multiple agents can add comments to the same item without merge conflicts.
- Item `updated_at` accurately reflects changes to the item's fields, not discussion activity.
- Comment files are individually addressable and can be inspected in Git history.
- Timestamp collisions (two comments in the same second) need a deterministic disambiguation
  suffix.
- Finding and listing comments requires scanning a directory rather than parsing a single file.
- Comment folders add directory entries to the repository, but the number remains manageable
  for local projects.

## Alternatives Considered

- **Embedded comments in item YAML** — rejected because it couples comment activity to item
  field changes, causing merge conflicts and timestamp noise.
- **Single comments file per item** — rejected because it still creates merge conflicts when
  multiple parties append.
- **Binary database for comments** — rejected because comments should be Git-visible and remain
  normal text files.
