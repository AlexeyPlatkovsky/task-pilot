# Beta Item Detail Redesign

Status: implemented

## Outcome

The WebUI item modal becomes a release-quality task view for the core item-management loop. It
keeps users in Board or List context, makes the item identity and editable fields obvious, and
groups read-only task context so priority, status, readiness, completion, attachments, references,
comments, validation issues, and timestamps are scan-friendly before Beta.

## Context

`docs/roadmap.md` marks the task detail view redesign as a release blocker because the current
modal exposes many fields without a clear information hierarchy. `docs/design.md` already defines
modal editing as the workspace pattern, and `docs/specs/0002-alpha-product-and-stack-decisions.md`
keeps the modal on the current page with Alpha editing limited to title, description, priority,
and status.

This specification settles the information architecture for the Beta polish pass without changing
canonical task data. It adds a REST detail contract for derived relationship context while keeping
reverse links derived rather than persisted.

## Scope

In scope:

- restructure the existing item modal view mode into a header, two-column summary, Info section,
  comments section, and validation area;
- keep title, status, priority, and description as the only editable WebUI fields;
- keep the requested read-only context visible when present: priority, status, timestamps,
  description, readiness, resources, linked items, comments, and validation findings;
- show absent checklist, resource, and comment groups as explicit empty states where
  that absence is useful for day-to-day task review;
- preserve the existing soft-delete confirmation behavior;
- preserve invalid item visibility and show validation findings inside the modal;
- keep the modal usable in the supported desktop viewport range.

Out of scope:

- new canonical item fields or serialization rules;
- REST API additions for comment mutation or hard delete;
- editing DOR, DOD, tags, attachments, external references, parent, or non-parent links;
- WebUI item creation;
- project-configured workflow statuses;
- permanent item delete safeguards;
- mobile or tablet layouts.

## Requirements

### Functional

F1. The modal header shall show item type, item ID, and title in that order. Item type shall use a
compact icon label with shared item-type colors: Epic purple, Feature dark blue, Task light blue,
and Bug red. Item ID shall be visually stronger than the type label.

F2. The item summary shall render under `aria-label="Item summary"` as two metadata columns: the
left column contains Priority and Status, and the right column contains Created and Updated.

F3. The view mode shall group Description, Readiness, and Resources under an Info section and shall
show a clear empty state when the item has no description.

F4. The view mode shall group DOR and DOD checklists together, preserving item order and showing
empty checklist states when either list is absent.

F5. The view mode shall group tags, attachments, and external references together, preserving item
order and showing an explicit no-resources state when all are absent.

F6. The modal shall show a Linked to section between Info and Comments. It shall render direct
parent, direct children, stored forward links, and derived reverse links when present. Each linked
item shall render as one row in a one-column list with the relationship label followed by a link
containing item ID and title, for example `Parent: TP-5 Base Epic for test`. The item ID and title
shall use one font and size, with the ID bold. Relationship links shall open the target item in the
same modal. Long titles shall be trimmed for stable layout. Rows shall preserve deterministic order:
Parent, Children, Blocks, Blocked by, and Related to. Stored `relates_to` and derived `related_to`
rows shall both appear under Related to. The section shall use an empty state when the item has no
relationships. Broken relationship targets shall remain visible by item ID with a missing or
invalid state instead of disappearing from the section.

F7. Comments shall remain read-only and chronological through the existing comment thread.

F8. Invalid item findings shall remain visible in the modal and shall include severity, message,
and field when available.

F9. Edit mode shall continue to edit only title, description, priority, and status. Cancel shall
return to view mode without committing changes.

F10. Edit and Delete shall be icon-only buttons in the upper-right action group near Close. Delete
shall continue to use the existing confirmation dialog and soft-delete behavior.

F11. The modal shall not fetch relationship details independently. It shall render relationships
from the current item detail response.

### Quality

Q1. The modal shall use local WebUI tokens and existing components rather than introducing a new
visual system.

Q2. The modal shall preserve Radix Dialog accessibility behavior, visible close control, keyboard
focus, and accessible title/description.

Q3. The modal shall avoid nested cards; section grouping may use borders, grids, lists, chips, and
muted surfaces.

Q4. The modal shall avoid hardcoded token-owned colors, shadows, radii, and typography values.

Q5. The modal shall remain readable and stable at the supported desktop minimum width.

## Design

### Domain and invariants

No canonical file format rules change. Markdown/YAML item files remain canonical. Reverse links and
children remain derived by services and are not stored twice. Invalid files remain visible and
actionable.

### Canonical file effects

None. The redesign and relationship section are read-only except for the existing edit and
soft-delete paths.

### Service operations

No write service operation is required. The REST adapter derives relationship context from existing
item, hierarchy, and reverse-link services.

### CLI / API contracts

`ItemDetail` adds a read-only `relationships` object containing:

- `parent`: the direct parent item summary, or null;
- `children`: direct child item summaries;
- `blocks` and `relates_to`: stored forward link target summaries;
- `blocked_by` and `related_to`: derived reverse link source summaries.

Relationship summaries include item ID, title, type, status, and priority. CLI contracts do not
change. Missing or invalid relationship targets are returned with `valid: false`, the requested
item ID, and placeholder title/status/type/priority values so the UI can surface the broken link.

### UI states

- Loading: show the modal shell with the requested item ID and loading text.
- Load error: show failure text and retry action.
- View mode: show header, summary, Info, Linked to, comments, and
  validation findings when applicable. Linked to rows are one-column links that switch the modal to
  the linked item.
- Empty groups: show no-description, no-checklist, no-resources, and no-comments
  states where relevant.
- Edit mode: show the existing edit form and preserve current mutation/error behavior.
- Delete confirm: show the existing destructive confirmation dialog.
- Invalid item: show validation findings without hiding parsed fields.

## Acceptance Criteria

1. Given an item with type, status, priority, description, tags, DOR, DOD, attachments, external
   references, relationships, comments, and timestamps, when the modal opens, then each field
   appears in the correct grouped area with readable labels.
2. Given an item with no description, checklist content, resources, or comments,
   when the modal opens, then the modal shows explicit empty states for those groups.
3. Given an invalid item with validation findings, when the modal opens, then validation findings
   remain visible with severity, message, and field where available.
4. Given an item with a parent, children, forward links, and reverse links, when the modal opens,
   then the Linked to section lists one row per relationship in Parent, Children, Blocks,
   Blocked by, Related to order, and each row exposes a link containing the linked item ID and
   title.
5. Given an item with no relationships, when the modal opens, then the Linked to section shows a
   no-linked-items empty state.
6. Given an item has a relationship pointing at a missing or invalid item, when the modal opens,
   then the Linked to section still shows the linked item ID and a missing/invalid state.
7. Given a user activates a Linked to row link, when the target item can be loaded, then the same
   modal shows the target item detail without closing the board context.
8. Given a user enters edit mode, when they inspect the form, then only title, description,
   priority, and status are editable.
9. Given a user cancels edit mode, when the view returns, then no mutation is submitted.
10. Given a user opens the delete action, when the confirmation appears, then the existing
   soft-delete confirmation path is used.
11. Given the modal is rendered at the supported desktop minimum width, then header, actions,
   summary columns, sections, and long item IDs do not overlap.

## Test Strategy

- API tests cover the read-only relationship payload for parent, children, forward links, and
  reverse links, including missing relationship targets.
- Component tests cover grouped rendering, ordered relationship links, same-modal relationship
  navigation, empty relationship state, invalid relationship state, invalid findings, edit-mode
  scope, and delete confirmation continuity.
- Existing `ItemEditForm` tests continue to cover field validation, save behavior, and dirty-field
  preservation.
- Functional E2E coverage opens an item with relationship data and verifies the Linked to section
  is visible from the board modal.
- Browser contract evidence is required for layout only if component tests cannot prove the
  supported desktop minimum-width behavior.

## Implementation Evidence

- Implemented in `web/src/components/ItemModal.tsx` and
  `web/src/components/ItemModal.module.css`.
- Component coverage lives in `web/src/components/__tests__/ItemModal.test.tsx`.
- Existing modal journey coverage remains in `web/e2e/functional/f004-core-workspace.spec.ts`
  through `web/e2e/pages/taskpilot-page.ts`.
- Validation commands passed for the implementation slice: `npm run test:component --
  ItemModal.test.tsx`, `npm run test`, `npm run lint`, `npm run build`, and
  `npm run test:e2e:functional -- f004-core-workspace.spec.ts`.
- Browser contract evidence for the 1280px long-ID no-overlap layout passes through
  `npm run test:browser-contract`.
- Full relationship section implemented through the REST `relationships` payload and WebUI
  `Linked to` section.
- Relationship validation commands passed for this slice: `uv run pytest tests/server/test_api.py`,
  `npm run test`, `npm run lint`, `npm run build`, `npm run test:e2e:functional --
  f004-core-workspace.spec.ts`, `npm run test:browser-contract`, `ruff format --check .`, and
  `uv run taskpilot validate`.

## Implementation Slices

1. Add or update component tests for the accepted grouped modal contract.
2. Refactor `ItemModal` view-mode rendering into small local helpers without changing API calls.
3. Update modal CSS to support the summary/header and grouped body layout using existing tokens.
4. Run focused component tests, then WebUI build and relevant validation.
5. Update design and roadmap documentation to record the accepted contract and remaining Beta gaps.

## Risks and Compatibility

- Rendering empty states may add visible text in areas that previously disappeared. This is
  intentional for release readiness and does not change data.
- The relationship payload duplicates item summary facts in a detail response. Tests must guard the
  REST contract so future item-summary field changes do not silently drift.
- Full field editing and comment mutation are deferred from 1.0.0 unless a later
  accepted scope explicitly pulls them back in.

## Assumptions

- This user request is the explicit route that satisfies the roadmap's task-detail redesign
  discovery gate.
- The Beta polish pass should improve the existing local WebUI, not introduce OD or Pencil design
  artifacts.
- Child item visibility and reverse-link visibility are approved for this full relationship slice.

## Post-Beta Questions

- Should comment add/edit/delete ship in a later Beta, or remain a post-Beta workflow?
- Should full item field editing be split into separate post-modal slices for checklist, resource,
  and relationship editors?
