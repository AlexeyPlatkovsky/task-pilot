---
name: design-ui
description: Designs accessible TaskPilot product UI flows and records accepted design decisions. Use before UI implementation; not for marketing pages or production code.
---

# Design TaskPilot UI

Read `designs/design.md`. For WebUI component-library or existing-page work, also read
`.claude/conventions/ui-component-library.md`. This skill designs UI behavior and updates design
docs; production implementation belongs to `implement-change`.

1. Identify the user job, displayed data, primary action, and loading/empty/error/invalid states.
2. Reuse existing components and tokens. Without them, use neutral surfaces, one accent, explicit
   hierarchy, and consistent spacing.
3. Choose the simplest fitting pattern: table/list for scanning, panel/page for detail, inline
   validation, and explicit status/relation labels.
4. Define keyboard behavior, focus order, accessible names, and narrow-screen behavior.
5. Keep domain and persistence rules out of UI components.
6. Define the component-test and critical E2E coverage required by the design.
7. Create or update `designs/design.md` with accepted flows, patterns, states,
   accessibility behavior, responsive behavior, and unresolved design debt.
8. When a runnable UI already exists, render and inspect desktop and narrow widths to ground the
   design update in observed behavior.

Do not hide validation, file conflicts, sync state, or destructive effects. Do not use color alone
for status or default to decorative dashboards, glass effects, gradients, or gratuitous motion.
If required product behavior, data contracts, or the runnable UI are unavailable, report the
missing context and mark affected design or visual checks blocked rather than inventing them.

Do not modify production UI code while acting in this skill.

The artifact begins with `Skill: design-ui - output below` and reports status, flow, layout, states,
accessibility, design-system changes, visual evidence, assumptions, and blockers.
