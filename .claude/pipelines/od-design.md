# Open Design Pipeline

## Trigger

Use for design-only work in Open Design (OD) through the Open Design MCP server with no production
code change. OD is the default MCP-backed design route for new TaskPilot design artifact work unless
the user explicitly asks for a `.pen` file or Pencil.

When a single request names both an OD design goal and a code-change goal, route through
`od-to-code.md` instead. If this situation is discovered after this pipeline is already loaded,
emit `Pipeline: od-design - output below` with status `blocked`, reason, scope, and reroute target
`od-to-code.md`, then return control to the manager.

## Prerequisites

Before stage 1:

- Confirm the Open Design MCP server is available (`mcp__open_design__get_active_context` or
  `mcp__open_design__list_projects`). Stop if unavailable.
- Confirm `designs/design.md` is readable. Stop if unavailable.
- For existing-design requests, confirm an active OD project exists. If none exists, ask the user to
  open the intended OD project and stop. For new design artifact requests, record that
  `open-design` must create the OD project; do not create it in this prerequisite gate.
- For ambiguous document-format requests such as "deck", "slides", "PDF", or "doc", ask whether
  the desired output is browser-viewable OD HTML/SVG or a real binary export before starting OD.

## Ordered Steps

1. **Context load.** Read `designs/design.md` and `docs/design.md`. Search `docs/specs/`
   for a spec related to the work; if one exists, read it. Confirm whether a relevant OD design
   system resource (`od://design-systems/<id>/DESIGN.md`) is attached or supplied. Emit:
   `Pipeline: od-design - output below` with status, stage `context-loaded`, scope, assumptions,
   context checks, design-system resource status, and blockers.

2. **Design.** Run `open-design` skill. The skill governs all OD MCP operations including
   active-context handling, project creation, run commissioning, artifact pulls, direct file edits,
   design-system resource use, and preview evidence.
   Require: `Skill: open-design - output below`. Stop if the skill reports blocked.

3. **Design review.** Run `design-reviewer` agent in an isolated fresh context. Pass OD preview
   evidence, pulled artifact inventory, the `open-design` verification field, and screenshots or
   browser evidence. If preview/browser evidence is unavailable, pass the explicit blocked or N/A
   visual-verification report from `open-design`; stop if neither evidence nor an explicit report is
   present.
   Require: `Agent: design-reviewer - output below`.
   - If `design-reviewer` reports blocked, stop and return control to the manager.
   - Critical or High findings -> return to stage 2 (`open-design`), fix, re-pull artifacts, re-run
     `design-reviewer`. Up to 3 loops total. Record loop count and repeat artifact labels.
   - If Critical or High findings remain after 3 loops, stop with blockers.

4. **Snapshot and verify.** Confirm the final OD artifact can be pulled with
   `mcp__open_design__get_artifact(include: "auto")`, record the project id/name, entry file,
   preview URL when present, and whether any generated or edited files were truncated by MCP caps.
   For major paths, verify the preview with browser evidence or report why browser verification is
   blocked or not applicable.

Stop on a blocked or failed step and return control to the manager. The manager owns documentation
maintenance and task-complete after this pipeline.

## Output Contract

Begin with `Pipeline: od-design - output below` and report:

- status;
- OD project id/name and entry file;
- completed stage labels;
- design-reviewer verdict and loop count;
- artifact pull confirmation and preview URL or N/A reason;
- design-system resource used or N/A;
- blockers.
