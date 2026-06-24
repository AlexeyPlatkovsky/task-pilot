# TaskPilot

Local-first, file-based task management. Markdown/YAML files under `.taskpilot/` are the canonical
source of truth; everything else (indexes, UI state) is disposable. TaskPilot works offline with no
accounts or hidden synchronization.

See [`docs/`](docs/) for the product concept, specifications, and architecture decisions.

## Workspace layout

A TaskPilot project lives inside its repository under `.taskpilot/`:

```text
repo-root/
  .taskpilot/
    project.yaml          # canonical project identity
    items/
      TP-1.yaml           # one YAML file per item
    comments/
      TP-1/
        2026-06-23T10-00-00Z.md   # append-only Markdown comments per item
```

## Development

This is a Python project managed with [`uv`](https://docs.astral.sh/uv/).

```bash
uv sync          # create the environment and install dev dependencies
uv run pytest    # run the test suite
```

Source lives under `src/taskpilot/` (core domain layer); tests live under `tests/`.
