# UI Quality Retrospective — Advanced Views

Date: 2026-06-29

## Summary

Several F006 UI fixes were discovered after implementation: drag/drop card blink, incomplete list
filter behavior, native dropdown placement inconsistency, missing Clear behavior, inconsistent
project/theme/list selector styling, and text sort labels where canonical arrows were expected.

The primary cause was not a single implementation defect. The specifications and AI instructions
captured feature presence but did not require explicit UI interaction contracts, full finite-state
coverage, reusable control consistency, or transient optimistic-state validation.

## Root Causes

- F006 acceptance criteria described sortable/filterable behavior but not visible indicators,
  reset behavior, dropdown placement, selected-state styling, or all option states.
- UI instructions required design-system alignment, but did not force a component-pattern inventory
  before adding or changing controls.
- Tests proved representative happy paths rather than every enum/filter option, reset/default
  state, filtered-empty state, and re-render/time-sensitive behavior.
- Drag/drop validation proved final status, but not the transient state between drop and cache/API
  settlement.
- Native browser controls were used where product behavior required deterministic placement and
  shared option styling.

## Instruction And Documentation Updates

- `.claude/skills/manager/SKILL.md` now routes shared controls, native-control replacement,
  drag/drop, and optimistic/cache-visible UI as at least medium risk.
- `.claude/conventions/ui-component-library.md` now requires a UI pattern inventory and explicit
  interaction contracts for reusable controls.
- `.claude/conventions/testing.md` now requires finite option coverage, reset/default/filter-empty
  coverage, canonical sort indicator assertions, custom dropdown contracts, and transient
  drag/drop/optimistic-state tests.
- `.claude/skills/design-ui/SKILL.md`, `.claude/skills/test-change/SKILL.md`, and
  `.claude/skills/validate-change/SKILL.md` now require those contracts to be planned, tested, and
  validated.
- `designs/design.md`, `docs/design.md`, `docs/testing.md` and F006 now document the
  dropdown selector, sorting indicator, filter reset, and optimistic UI contracts.

## Expected Future Behavior

Future UI work should define the full visible interaction contract before implementation, reuse or
extract local component patterns when a control appears in multiple places, and validate both
settled behavior and user-visible transient states.
