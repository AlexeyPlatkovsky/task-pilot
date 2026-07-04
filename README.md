# TaskPilot

TaskPilot is local-first task management for software projects. It keeps project work in
Git-friendly files inside your repository, so humans and coding agents can share the same durable,
inspectable task state without accounts, hosted services, or hidden synchronization.

TaskPilot is published as the `taskpilot` npm package.

## Why TaskPilot

- Local-first: task data lives in your repo under `.taskpilot/`.
- File-based: YAML items and Markdown comments are the canonical source of truth.
- Agent-friendly: CLI output can be human-readable or deterministic JSON.
- Offline by default: normal usage works after the first runtime setup.
- Git-friendly: one file per item and append-style comments reduce merge conflicts.

## Install

TaskPilot is distributed through npm. The stable release supports global npm installation.

```bash
npm install -g taskpilot
```

Prerequisites:

- Node.js 18 or newer.
- Python 3.11 or newer with `venv` and `pip`.

TaskPilot finds Python automatically on first run. To use a specific interpreter:

```bash
TASKPILOT_PYTHON=/opt/homebrew/bin/python3.11 taskpilot --help
```

## Quick Start

Initialize TaskPilot in a project repository:

```bash
cd my-project
taskpilot init .
```

Create and inspect work items:

```bash
taskpilot item create --title "Add login form" --type task
taskpilot item list
taskpilot item show MP-1
```

Update workflow state:

```bash
taskpilot item update MP-1 --status in_progress
taskpilot item comment MP-1 "Started implementation."
```

Use JSON output for scripts and AI agents:

```bash
taskpilot --json item list
taskpilot --json validate
```

Start the local WebUI:

```bash
taskpilot serve
```

Then open `http://127.0.0.1:7152/`. The WebUI can be started from any directory; it loads
registered projects from your local TaskPilot registry and restores the last valid project when
available.

## Data Layout

A TaskPilot workspace is stored inside the repository:

```text
repo-root/
  .taskpilot/
    project.yaml
    items/
      MP-1.yaml
    comments/
      MP-1/
        2026-06-23T10-00-00Z.md
```

The files under `.taskpilot/` are the product data. Indexes, caches, local server state, and UI
state are disposable.

## CLI

Common commands:

```bash
taskpilot init .
taskpilot project list
taskpilot item list
taskpilot item show MP-1
taskpilot item create --title "Write docs" --type task
taskpilot item update MP-1 --status done
taskpilot item parent CHILD-1 PARENT-1
taskpilot item blocks BLOCKER-1 TARGET-1
taskpilot item relates ITEM-1 ITEM-2
taskpilot item comment MP-1 "Context for the next pass."
taskpilot validate
taskpilot serve
```

Run `taskpilot --help` or any subcommand with `--help` for the complete option list.

## WebUI and Local API

`taskpilot serve` starts the local WebUI and REST API server. It can be run from any directory and
uses the local TaskPilot registry to list initialized projects.

```bash
taskpilot serve
```

By default TaskPilot binds to `127.0.0.1:7152`.

- WebUI: `http://127.0.0.1:7152/`
- REST API: `http://127.0.0.1:7152/api`
- OpenAPI docs: `http://127.0.0.1:7152/docs`

If the packaged WebUI assets are missing, the root URL shows a packaging error page and the REST
API remains available.

To validate a specific workspace before starting the server, pass `--workspace`:

```bash
taskpilot serve --workspace /path/to/repo
```

## Offline Use and Runtime Cache

The first TaskPilot run creates a Python runtime environment in your user cache directory. This
setup may need network access to install the locked Python dependencies. After setup, normal
TaskPilot commands work offline and reuse the cached runtime.

Default cache locations:

| Platform | Cache directory |
| --- | --- |
| macOS | `~/Library/Caches/taskpilot/` |
| Linux | `~/.cache/taskpilot/` |
| Windows | `%LOCALAPPDATA%/taskpilot/Cache/` |

If setup fails, TaskPilot removes the partial runtime and preserves a setup log. Rebuild the runtime
with:

```bash
taskpilot doctor --rebuild-runtime
```

## Package Support

The stable release supports global npm installation. `pnpm`, `yarn`, `npx`, and other package
managers are not guaranteed to work yet.

## Development

This repository uses Python and `uv` for local development.

```bash
uv sync
uv run pytest
```

Project documentation lives under [`docs/`](docs/), including the product concept, accepted specs,
architecture notes, and roadmap.

Release helpers are available as npm scripts for maintainers:

```bash
npm run quality-gates
npm run release:dry-run
```
