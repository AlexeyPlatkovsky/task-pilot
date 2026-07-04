# Beta Item Detail Redesign

Status: accepted

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

This specification settles the information architecture and inline editing behavior for the Beta
polish pass without changing canonical task data formats. The WebUI may expose existing item YAML
fields through the REST API, but canonical files remain the source of truth and comments remain
append-style Markdown files.

## Scope

In scope:

- restructure the existing item modal into a header, two-column summary, content groups, comments
  section, and validation area;
- keep users in the same modal when edit mode is active instead of replacing the detail view with a
  separate form;
- make title, description, DOR, DOD, resources, and new comments editable in edit mode;
- keep the requested read-only context visible when present: priority, status, timestamps,
  description, readiness, resources, comments, and validation findings;
- show absent checklist, resource, and comment groups as explicit empty states where
  that absence is useful for day-to-day task review;
- keep delete confirmation layered over the current modal instead of hiding the item detail;
- preserve invalid item visibility and show validation findings inside the modal;
- keep the modal usable in the supported desktop viewport range.

Out of scope:

- new canonical item fields or serialization rules;
- REST API additions for child items, reverse links, existing-comment mutation, or hard delete;
- editing tags, parent, or non-parent links;
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

F3. The modal shall show Description, Readiness, and Resources as adjacent content groups without an
extra "Info" section heading. It shall show a clear empty state when the item has no description.

F4. The view mode shall group DOR and DOD checklists together, preserving item order and showing
empty checklist states when either list is absent.

F5. The view mode shall group tags, attachments, and external references together, preserving item
order and showing an explicit no-resources state when all are absent.

F6. Existing comments shall remain chronological through the existing comment thread. Edit mode
shall allow adding a new comment through the append-only comment service without mutating or
deleting existing comment files.

F7. Invalid item findings shall remain visible in the modal and shall include severity, message,
and field when available.

F8. Edit mode shall keep the same modal layout and make title, Description, DOR, DOD, Resources,
and Comments editable. Priority and Status remain displayed in the summary unless a later accepted
scope explicitly changes them.

F9. Edit and Delete shall be icon-only buttons in the upper-right action group near Close. Delete
shall show the confirmation dialog over the existing modal and continue to use soft-delete
behavior.

F10. The modal shall not fetch or derive child items or reverse links beyond the current item
detail response.

F11. DOR and DOD shall render as checklist groups with checkboxes. In edit mode, each group shall
show a plus icon that inserts a new editable item. Checklist text is limited to 60 characters; an
item clicked in edit mode becomes an inline text field, blur commits the value, and the inline
delete icon removes the item without confirmation.

F12. Resources shall render attachments and links with edit-mode actions for Attach and Link.
Every resource row shall have an icon-only delete action in edit mode. Resource deletion shall ask
for confirmation over the current modal before updating the item.

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

No canonical format rules change. Markdown/YAML item files remain canonical. Reverse links remain
derived by services and are not stored twice. Invalid files remain visible and actionable. Comment
creation remains append-only through separate Markdown files.

### Canonical file effects

Title, description, DOR, DOD, attachments, and external references may be rewritten through the
validated item update path. Comment creation writes a new timestamped Markdown file and does not
rewrite the item YAML.

### Service operations

No new item service operation is required; existing validated `update_item` semantics handle
existing YAML fields. The existing comment service handles new comment creation.

### CLI / API contracts

The REST item patch contract exposes existing `ItemDetail` fields needed by edit mode:
`description`, `dor`, `dod`, `attachments`, and `external_refs`. A REST comment creation endpoint
may append a comment and return the refreshed item detail. CLI contracts do not change.

### UI states

- Loading: show the modal shell with the requested item ID and loading text.
- Load error: show failure text and retry action.
- View mode: show header, summary, Description, Readiness, Resources, Comments, and validation
  findings when applicable.
- Empty groups: show no-description, no-checklist, no-resources, and no-comments
  states where relevant.
- Edit mode: keep the detail layout in place, make scoped fields editable inline, and preserve
  mutation/error visibility.
- Delete confirm: show the existing destructive confirmation dialog over the still-visible modal.
- Resource delete confirm: show a scoped confirmation dialog over the still-visible modal.
- Invalid item: show validation findings without hiding parsed fields.

## Acceptance Criteria

1. Given an item with type, status, priority, description, tags, DOR, DOD, attachments, external
   references, comments, and timestamps, when the modal opens, then each field appears in the
   correct grouped area with readable labels.
2. Given an item with no description, checklist content, resources, or comments,
   when the modal opens, then the modal shows explicit empty states for those groups.
3. Given an invalid item with validation findings, when the modal opens, then validation findings
   remain visible with severity, message, and field where available.
4. Given a user enters edit mode, when they inspect the modal, then the same modal remains visible
   and title, description, DOR, DOD, resources, and new-comment input are editable in place.
5. Given a user edits a DOR or DOD item, when the inline field blurs, then the item is saved through
   the item patch path and remains in list order.
6. Given a user adds a DOR or DOD item, when they type more than 60 characters, then the UI prevents
   or rejects the excess before saving.
7. Given a user deletes a DOR or DOD item in edit mode, when they click the row delete icon, then
   the item is removed without a confirmation dialog.
8. Given a user adds or removes a link or attachment resource, when the action is confirmed where
   required, then the corresponding `external_refs` or `attachments` field is updated without
   changing unrelated fields.
9. Given a user adds a comment in edit mode, when the comment is submitted, then a new append-only
   comment appears in chronological order and the item YAML is not rewritten for the comment.
10. Given a user opens the item delete action, when the confirmation appears, then the item modal
    remains visible behind it and the existing soft-delete confirmation path is used.
11. Given the modal is rendered at the supported desktop minimum width, then header, actions,
    summary columns, sections, and long item IDs do not overlap.

## Test Strategy

- Component tests cover grouped rendering, empty states, invalid findings, inline edit-mode scope,
  checklist editing, resource deletion confirmation, comment append affordance, and delete
  confirmation continuity.
- API tests cover item patch fields for DOR, DOD, attachments, and external references plus the
  comment append endpoint when introduced.
- Functional E2E coverage exercises the major modal edit workflow through the page object.
- Browser contract evidence covers layout and stacked confirmation behavior where component tests
  cannot prove browser placement.

## Implementation Evidence

- Previous view-mode polish was implemented in `web/src/components/ItemModal.tsx` and
  `web/src/components/ItemModal.module.css`.
- Component coverage lives in `web/src/components/__tests__/ItemModal.test.tsx`.
- Existing modal journey coverage remains in `web/e2e/functional/f004-core-workspace.spec.ts`
  through `web/e2e/pages/taskpilot-page.ts`.
- Validation commands passed for the implementation slice: `npm run test:component --
  ItemModal.test.tsx`, `npm run test`, `npm run lint`, `npm run build`, and
  `npm run test:e2e:functional -- f004-core-workspace.spec.ts`.
- Browser contract evidence for the 1280px long-ID no-overlap layout passes through
  `npm run test:browser-contract`.

## Implementation Slices

1. Add or update component tests for the accepted grouped modal contract.
2. Refactor `ItemModal` view-mode rendering into small local helpers without changing API calls.
3. Update modal CSS to support the summary/header and grouped body layout using existing tokens.
4. Run focused component tests, then WebUI build and relevant validation.
5. Update design and roadmap documentation to record the accepted contract and remaining Beta gaps.

## Risks and Compatibility

- Rendering empty states may add visible text in areas that previously disappeared. This is
  intentional for release readiness and does not change data.
- The current API does not expose child items or reverse links. The modal must not imply those are
  complete until an API/domain contract adds them.
- Existing comment edit/delete remains out of scope to preserve append-only comment behavior.
- Inline blur-save can produce multiple small canonical item rewrites; tests must prove unrelated
  fields are preserved and failed saves are visible.

## Assumptions

- This user request is the explicit route that satisfies the roadmap's task-detail redesign
  discovery gate.
- The Beta polish pass should improve the existing local WebUI, not introduce OD or Pencil design
  artifacts.
- Child item visibility and reverse-link visibility require API/domain work and are therefore
  outside this modal-only slice.

## Open Questions

- Should a later Beta slice add child item and reverse-link fields to `ItemDetail`, or should the
  modal derive that context from the already loaded item list?
- Should comment add/edit/delete ship in Beta, or should release scope narrow Beta to read-only
  comments for the first npm beta?
- Should full item field editing remain in Beta, or be split into separate post-modal slices for
  checklist, resource, and relationship editors?
