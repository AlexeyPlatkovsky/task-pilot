---
name: design-ui
description: Designs or implements simple accessible TaskPilot product UI flows. Use for list/detail, forms, validation, Kanban, tree, and local workflow states; not marketing pages.
---

# Design TaskPilot UI

1. Identify the user job, displayed data, primary action, and loading/empty/error/invalid states.
2. Reuse existing components and tokens. Without them, use neutral surfaces, one accent, explicit
   hierarchy, and consistent spacing.
3. Choose the simplest fitting pattern: table/list for scanning, panel/page for detail, inline
   validation, and explicit status/relation labels.
4. Define keyboard behavior, focus order, accessible names, and narrow-screen behavior.
5. Keep domain and persistence rules out of UI components.
6. Add component tests for interactions and E2E only for critical journeys.
7. Render and inspect desktop and narrow widths when a runnable UI exists.

Do not hide validation, file conflicts, sync state, or destructive effects. Do not use color alone
for status or default to decorative dashboards, glass effects, gradients, or gratuitous motion.
If required product behavior, data contracts, or the runnable UI are unavailable, report the
missing context and mark affected design or visual checks blocked rather than inventing them.

The artifact begins with `Skill: design-ui - output below` and reports status, flow, layout, states,
accessibility, changed files, visual verification, assumptions, and blockers.
