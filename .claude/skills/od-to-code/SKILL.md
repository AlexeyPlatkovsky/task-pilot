---
name: od-to-code
description: Reads an Open Design artifact bundle and produces a component specification for test-first React implementation. Does not write code or tests.
applies_when: translating an accepted Open Design artifact into a React component specification
---

# OD-to-Code Translation Skill

## Purpose

Extract the component contract from an Open Design (OD) artifact and emit a specification that the
`test-change` and `implement-change` skills can execute without further design interpretation.
This skill reads OD artifacts; it never writes production code, test files, or CSS.

## Visible-Artifact Trace

Emit before the first tool call:

`Trace: skill od-to-code - output below`

## Prerequisites

Before executing:

1. Confirm the target OD project and entry artifact are available through Open Design MCP. Stop if
   absent.
2. Confirm an accepted spec or explicit acceptance criteria is present for the work. Stop if
   absent.
3. Confirm the Open Design MCP server is available. Stop if unavailable.

## Execution Steps

1. **Load design context.** Read `designs/design.md` (Required States, Accessibility
   Baseline, Visual Direction, Color Tokens, Icon Library sections) and `docs/design.md`.
   Read a relevant OD design-system resource when attached or supplied.

2. **Read the OD artifact.** Call in order:
   - `mcp__open_design__get_project()` to capture project metadata, entry file, design-system id,
     and preview URL;
   - `mcp__open_design__get_artifact(include: "auto")` for the entry artifact and referenced
     siblings;
   - `mcp__open_design__list_files()` only when inventory is needed beyond the pulled artifact;
   - `mcp__open_design__search_files()` for specific components, text, or token references.

   Stop if the artifact bundle is truncated or the entry artifact is missing. Ask whether to narrow
   the entry or pull a larger bundle before continuing.

3. **Extract component inventory.** For each visible component and sub-component:
   - Name: PascalCase React component and kebab-case CSS class names.
   - Inferred TypeScript props interface.
   - States visible in the artifact (loading, empty, error, populated, hover, disabled, invalid,
     conflict, success, narrow-screen, etc.).
   - Layout description using token references from `web/src/tokens.css`.
   - Color mapping: each fill/stroke/text color -> the corresponding token.
   - Interactive affordances: click targets, keyboard behavior, focus order.
   - Required Lucide icons through `web/src/components/ui/Icon.tsx` with `aria-label` strategy.

4. **Gap analysis.** Compare visible states against the Required States list from
   `designs/design.md`. List every required state absent from the OD artifact.
   Also report any token gap (a visual value that has no mapping in `web/src/tokens.css`) with a
   proposed token name and value range.
   Stop and present both gap lists to the user before emitting the component specification. Await
   user decision: confirmed gaps (states intentionally out of scope, approved token proposals)
   allow continuation; unresolved gaps remain blockers.

5. **Emit component specification.** For each component in scope:

   ```text
   Component: <ComponentName>
   File: web/src/components/<ComponentName>.tsx
   CSS module: web/src/components/<ComponentName>.module.css

   OD source:
   - Project: <project id/name>
   - Entry artifact: <path>
   - Source files: <paths>

   Props interface (TypeScript):
   <interface block>

   Accessibility contract:
   - ARIA role: <role>
   - Keyboard behavior: <description>
   - Accessible name source: <prop or aria-label strategy>

   Required states:
   - <state>: <rendering description>
   - ...

   CSS classes and token assignments:
   - .<className>: background var(--token), color var(--token), ...
   - ...

   Test coverage targets:
   - renders in <state> state: <assertion>
   - accessible name is <value>: <assertion>
   - ...
   ```

## Stop Conditions

- Target OD project or entry artifact unavailable -> stop, report the attempted project/entry.
- Open Design MCP unavailable -> stop.
- Accepted spec or acceptance criteria absent -> stop.
- `get_artifact` result is truncated -> stop and ask whether to narrow or enlarge the pull.
- Required states absent from artifact or token gaps identified -> stop and present the gap list
  to the user before proceeding. Await user decision. Confirmed gaps (intentionally out of scope or
  approved token proposals) allow continuation; unresolved gaps remain blockers.

## Output Contract

Begin with: `Skill: od-to-code - output below`

Include:

- status (`completed`, `skipped`, or `blocked`);
- OD project id/name, entry artifact, preview URL or N/A reason, and source files used;
- component count;
- full specification for each component;
- gap list (missing required states, token gaps) - empty if none;
- blockers.
