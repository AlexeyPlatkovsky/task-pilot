---
name: track-with-taskpilot
description: Uses TaskPilot as the project task tracker — queries, creates, and updates items via CLI or direct file access to keep work visible and traceable.
user-invocable: true
---

# Track with TaskPilot

## Responsibility

Manage TaskPilot task items for development work during AI-assisted sessions. This skill is a
utility — it is called inline by other skills or on demand, not gated through the manager route.

## Layer boundary

This skill manages local TaskPilot task items only. Do not use it for:

- Routing or classifying work — use `.claude/skills/manager/SKILL.md`.
- Implementing production code — use `.claude/skills/implement-change/SKILL.md`.
- Code review or design review — use `.claude/agents/code-reviewer.md` or
  `.claude/agents/design-reviewer.md`.

## Context

This project stores its own tasks in `.taskpilot/items/*.yaml`. The structure:

- `.taskpilot/project.yaml` — project identity (id, key, name)
- `.taskpilot/items/<ITEM_ID>.yaml` — individual items
- `.taskpilot/comments/<ITEM_ID>/` — comment files per item

Each item is a flat YAML file with fields: `schema_version`, `id`, `title`, `priority`
(low|normal|high), `type` (epic|feature|task|bug), `status` (backlog|in_progress|done|cancelled),
`created_at`, `updated_at`, and optional `description`, `parent_id`, `tags`, `created_by`.

## Interactions

### Query tasks via CLI

```sh
# List all items
taskpilot item list

# List items filtered by status
taskpilot item list --status backlog

# List items filtered by type
taskpilot item list --type task

# Show a single item
taskpilot item show TP-3

# JSON output (for programmatic use)
taskpilot item list --json
taskpilot item show TP-3 --json
```

### Create a new task

```sh
taskpilot item create \
  --title "Brief title" \
  --type task \
  --priority normal \
  --status backlog \
  --description "Optional details"
```

Required fields: `--title`, `--type`. Returns the new item id (e.g. `TP-6`).

### Update a task

```sh
taskpilot item update TP-3 --status in_progress --priority high
```

Only passed fields are changed. The `updated_at` timestamp is refreshed automatically.

### Read tasks via direct file access

When `taskpilot` is not on PATH, returns exit code 127/not-found, or raw YAML is needed,
read files directly:

- `.taskpilot/items/<ID>.yaml` — single item
- `.taskpilot/items/` — all items

### Create/update tasks via direct file access (CLI fallback)

When the CLI is unavailable and you need to write, create or update a YAML file directly
following the schema at `.taskpilot/items/<existing-id>.yaml`:

```sh
# Write a new item file
cat > .taskpilot/items/<NEW_ID>.yaml << 'EOF'
schema_version: 1
id: <NEW_ID>
title: "Item title"
priority: normal
type: task
status: backlog
created_at: "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
updated_at: "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
EOF

# Update an existing item's status (in-place sed)
sed -i '' 's/^status: .*/status: done/' .taskpilot/items/TP-3.yaml
```

## Error handling

- **`taskpilot: command not found`** (exit code 127): fall back to direct file access.
- **`.taskpilot/` directory missing**: the workspace has not been initialized — run
  `taskpilot init` or create the directory structure manually per project spec.
- **CLI exit code non-zero**: parse stderr for the error; if it indicates a workspace
  issue, check `.taskpilot/project.yaml` and `.taskpilot/items/` existence.
- **Item file not found**: the item id does not exist — verify with `ls .taskpilot/items/`.

## When to use

- **Before starting work**: check what tasks exist, their statuses, priorities, and types to
  understand the current sprint or backlog context.
- **After completing a task**: update its status to `done`.
- **When starting new work**: create a task item first, then reference the task id in the branch
  name and commit messages.
- **During validation**: verify task-item assertions in the `.taskpilot/` tree match expected
  behavior.
- **When the manager routes work**: if the manager identifies a task-backed item, load this skill
  to verify the item exists, read its current state, and create sub-items if needed.

## Output Contract

The artifact begins with `Skill: track-with-taskpilot - output below` and reports:

- invoked operation(s);
- affected item ids;
- current item states before and after (if mutated);
- raw YAML snapshot of relevant items (if queried);
- blockers or errors.

Emit the artifact when:
- the caller explicitly includes a directive like "track-with-taskpilot artifact required";
- the operation is part of a routed handoff from the manager or a pipeline;
- the operation mutates item state (create, update).

Do not emit the artifact for trivial inline queries (e.g. a single `taskpilot item show` call)
unless the caller explicitly requests it.
