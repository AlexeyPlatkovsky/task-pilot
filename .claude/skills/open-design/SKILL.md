---
name: open-design
description: Creates, edits, and verifies TaskPilot UI designs in Open Design via the Open Design MCP server. Use for design-only OD requests. Do not implement application code for design-only tasks.
applies_when: creating or modifying TaskPilot design artifacts in Open Design projects through OD MCP
---

# open-design

## Purpose

Execute TaskPilot design work in Open Design (OD) through the OD MCP server. This skill works with
OD projects, generated artifacts, source files, design-system resources, and browser-viewable
previews. It does not implement application code, choose product direction, or report final closure.

## What Is Open Design

Open Design is a local-first design workspace exposed through MCP. Each OD project contains a
rendered artifact such as HTML, JSX, CSS, SVG, or related assets plus the source files used to
produce it. OD projects are outside the TaskPilot production source tree unless the user explicitly
asks to translate an accepted OD artifact into code through `od-to-code`.

OD is the default MCP-backed design path for new TaskPilot design artifact work. Pencil remains
available for explicit `.pen` file work.

## Prerequisites

The Open Design MCP server must be installed, configured, and running. Verify availability with
`mcp__open_design__get_active_context` or `mcp__open_design__list_projects`. If OD tools are
unavailable, stop and ask the user to configure or open Open Design.

## Best-Practice Constraints

These constraints adapt current MCP and OD guidance:

1. **Resources before tools for reference material.** OD design-system specs are MCP resources
   (`od://design-systems/<id>/DESIGN.md`). Read the relevant resource before generation or edits
   when a project has one attached or the user names one.

2. **Explicit tool consent for mutation.** Treat OD write operations, run creation, cancellation,
   and deletion as state-changing tool calls. Never delete an OD project unless the user explicitly
   requested the named project deletion.

3. **Commission generation; do not impersonate OD internals.** Use `list_skills` and
   `list_plugins` when needed, then `start_run`. If the OD MCP exposes `list_agents`, call it before
   passing `start_run.agent`; otherwise omit the agent override and use the user's configured OD
   default. OD spawns its own agent; poll `get_run` until terminal. Do not cancel a running OD
   generation unless the user asks.

4. **Pull full design context before judging or translating.** Use `get_artifact()` for entry files
   plus referenced siblings. Prefer it over repeated `get_file` calls when understanding,
   reviewing, or extending a design.

5. **Preserve local-first boundaries.** OD artifacts are design evidence. Do not add cloud
   services, accounts, synchronization, or production dependencies to TaskPilot from OD output.

6. **Avoid ambiguous artifact formats.** OD natively produces browser-viewable artifacts, not
   binary `.pptx`, `.docx`, or `.pdf` files. Ask before starting when the requested format is
   ambiguous.

## Execution Rules

### 1. Load Required Context

- Read `.claude/docs/design-book.md` and `docs/design.md` before creating, generating, or editing
  an OD artifact.
- Search `docs/specs/` for an accepted spec related to the work; read it when present.
- If the OD project has an attached design system or the user names one, read the relevant
  `od://design-systems/<id>/DESIGN.md` resource before starting.
- Enumerate the active "Do not" constraints from `.claude/docs/design-book.md` Principles or
  Visual Direction before changing a design.

Stop and present 2-3 options with trade-offs when:

- a token, component, spacing value, or layout rule needed for the task is not in the design book
  or attached OD design system;
- a hardcoded value is about to be introduced where a documented token exists;
- a new component duplicates an existing reusable component or OD source module;
- a frame/page requires a new interaction state, breakpoint behavior, or layout pattern not covered
  by the design book.

For ambiguous decisions within the documented system, pick the nearest match, record it as an
inferred decision, and continue.

### 2. Resolve Project Context

- For existing-design work, prefer active OD context. Call `get_active_context()` only when the
  target project is unclear or the active context needs confirmation.
- If no active project exists for an existing-design request, ask the user to open the intended OD
  project and stop.
- For new design work, create a new OD project with a kebab-case id derived from the requested
  artifact name when the user did not supply a target project.
- When OD resolves a project by substring, confirm the resolved project id/name in the output. If
  the match is unexpected, stop and ask the user to choose the project.

### 3. Inspect Before Editing

For existing OD projects:

- call `get_project()` to record name, id, entry file, design-system id, and preview URL;
- call `get_artifact(include: "auto")` for the entry artifact and referenced siblings;
- use `list_files()` for inventory and `search_files()` for specific components/copy;
- use `get_file()` only for a known single file or paginated follow-up after `get_artifact`.

If `get_artifact` reports truncation, stop before review or translation and either narrow the entry
file or ask the user to approve an `include: "all"` or larger `maxBytes` pull.

### 4. Generate or Edit

For generation or broad refinement:

1. Call `list_skills()` and `list_plugins()` when the task calls for a recipe or packaged workflow.
2. When selecting an OD agent is required and the OD MCP exposes `list_agents()`, call it before
   setting `start_run.agent`; when it is unavailable, omit the agent override.
3. Call `start_run()` with the selected project, skill/plugin, and a prompt that includes:
   - TaskPilot product context;
   - relevant design-book constraints;
   - required states;
   - accessibility baseline;
   - token and icon-library rules;
   - explicit non-goals.
4. Poll `get_run()` every 30-60 seconds until `succeeded`, `failed`, or `canceled`.
5. On success, pull the result with `get_artifact()` and record the preview URL.

For small, direct file edits inside an OD project:

- use `create_artifact()` only for a new normal artifact entry file;
- use `write_file()` for iterating an existing OD file;
- keep edits narrow and preserve artifact manifests;
- after editing, pull with `get_artifact()` and verify the preview when available.

### 5. Design-System Discipline

- Use TaskPilot tokens and existing component/module patterns as the source of truth for colors,
  spacing, radius, shadows, typography, statuses, priorities, and icons.
- Preserve TaskPilot's developer-tool density and avoid marketing-page structure for product UI.
- Cover all applicable required states: loading, empty, recoverable error, invalid canonical file,
  missing or broken relation, unsaved or conflicting change, completed success, and narrow-screen
  layout.
- Keep domain rules, filesystem behavior, and persistence details out of OD visual artifacts.
- Use browser-viewable preview evidence for final review when possible.

### 6. Hand Off Cleanly

Before returning control to the pipeline, verify:

- OD project id/name, entry file, and preview URL or N/A reason;
- pulled artifact inventory and truncation status;
- design-system resource used or N/A;
- generated/edited files;
- required states and accessibility coverage;
- browser or screenshot evidence, or blocked/N/A reason.

This skill does not run pipeline validation or report closure.

## Open Design MCP Tool Reference

| Tool | What it does |
| --- | --- |
| `get_active_context()` | Reports the active OD project/file when available |
| `list_projects()` / `get_project()` | Lists or reads OD project metadata and preview URL |
| `list_files()` / `search_files()` / `get_file()` | Inspects project files |
| `get_artifact()` | Pulls the entry artifact plus referenced sibling files; preferred for design context |
| `create_project()` | Creates a new OD project, optionally with a design system or skill |
| `list_skills()` / `list_plugins()` | Discovers available OD generation capabilities |
| `list_agents()` | Discovers OD agents when this optional tool is exposed |
| `start_run()` / `get_run()` / `cancel_run()` | Commissions, polls, or explicitly cancels an OD generation/refinement run |
| `create_artifact()` / `write_file()` / `delete_file()` | Creates, updates, or deletes OD project files |
| `delete_project(project, confirm: true)` | Irreversibly deletes a named OD project; requires explicit user request |

## Output Contract

Before this skill's first tool call on its turn, emit one line:

`Trace: skill open-design - output below`

At the end of execution, emit:

`Skill: open-design - output below`

Then include:

| Field | Content |
| --- | --- |
| Status | `completed`, `skipped`, or `blocked` |
| Target | OD project, page, artifact, component, or file area changed |
| OD project | Project id/name, entry file, active context source, and preview URL or N/A |
| Files changed | OD project files created, generated, modified, or deleted |
| Changes made | Design elements, artifact structure, or source files created/updated/deleted |
| Design systems used | TaskPilot design book, `docs/design.md`, OD design-system resource, or N/A |
| Verification | `get_artifact` result, preview/browser evidence, screenshot path, or reason not run |
| Assumptions / inferred decisions | Material assumptions or inferred design decisions, or `none` |
| Warnings / Errors | Tool warnings, truncation, failed runs, or `none` |
| Open questions | Clarifications needed, or `none` |
