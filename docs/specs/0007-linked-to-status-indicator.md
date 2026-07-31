# Linked To Status Indicator

Status: implemented

## Outcome

A reader scanning the item modal's Linked to section can see each linked item's status without
opening it — status renders ahead of the title in every relationship row, using the same visual
treatment as the item's own Status field in the summary above.

## Context

`docs/specs/0004-beta-item-detail-redesign.md` F6 defines each Linked to row as "the relationship
label followed by a link containing item ID and title," rendered by `RelationshipItem` in
`web/src/components/ItemModal.tsx` (line ~487). That row currently shows only ID and title; a
reader has to open the linked item to learn its status. The REST `relationships` payload (same
spec, CLI/API contracts section) already returns `status` on every relationship summary
(`ItemRelationshipSummary.status`, `web/src/types/index.ts:60`), including the `"unknown"`
placeholder value used for missing/invalid targets — no API or service change is needed, this is a
rendering-only change.

The item summary's own Status field (`ItemModal.tsx` line ~257-263) already renders status as a
`.badge .statusBadge .status-{status}` pill using `STATUS_LABELS`. TP-111 asks the Linked to rows
to reuse that same treatment rather than invent a new one.

This amends 0004 F6's row-content sentence. The rest of F6 (ordering, empty state, broken-link
visibility, one-row-per-relationship, ID bold) is unchanged and remains authoritative there; this
spec is additive to it, not a replacement. `docs/specs/0004-beta-item-detail-redesign.md` F6's
row-content sentence is `[superseded: 0007]` for the specific claim that a row contains only "the
relationship label followed by a link" — it now also contains a status indicator, defined here.

## Scope

In scope: render a status badge, visually matching the existing item-summary Status badge, in each
valid Linked to row, positioned after the relationship label and before the ID/title link (label,
then status, then the ID+title link — status sits ahead of the title as requested; the badge is a
separate row element rather than embedded inside the truncating link, see Design for why). Handle
the missing/invalid-target case explicitly (see Design).

Out of scope: any REST/API/service change (the data already exists); changing relationship
ordering, empty-state text, or the existing "missing or invalid" indicator's own text; editing
behavior anywhere else in the modal.

In scope (corrected during design review against `.claude/conventions/ui-component-library.md`):
extracting a small local `StatusBadge` presentational component. The badge markup/classes
(`.badge .statusBadge .status-{status}` + `STATUS_LABELS`) currently exist at exactly one
production call site (the item summary's Status field). This change adds a second call site
(relationship rows), which is the convention's own trigger for extraction ("Extract a reusable
component when the same UI pattern appears in two or more production places") — so the two call
sites are unified into one component rather than duplicated inline markup.

## Requirements

### Functional

- Each Linked to row for a **valid** relationship target renders, in this order: relationship label,
  a status badge (same visual treatment as the item summary's Status field: `STATUS_LABELS[status]`
  text inside a `.badge .statusBadge .status-{status}` pill), then the link containing bold item ID
  and (possibly trimmed) title. Status is visually and in reading order ahead of the title,
  satisfying "status before title."
- Each Linked to row for an **invalid/missing** relationship target (`valid: false`, placeholder
  `status: "unknown"`) does **not** render a status badge — `"unknown"` is not a real workflow
  status and duplicating it next to the existing "missing or invalid" state text would be
  confusing/redundant. The existing "missing or invalid" text (0004 F6) remains the sole,
  sufficient state signal for that row.
- All other row content and behavior (relationship label, link target/click-to-navigate, long-title
  trimming, deterministic Parent/Children/Blocks/Blocked by/Related to ordering, empty state) is
  unchanged from 0004 F6.

### Quality

- Reuses existing local WebUI tokens/classes only (`.badge`, `.statusBadge`, `.status-<status>`,
  `STATUS_LABELS`) — no new visual system, no hardcoded colors (consistent with 0004 Q1/Q4).
  \[quality-scope: layout-only follow-on to 0004; inherits 0004's Q1-Q5 rather than restating them]
- No new accessible name is required beyond the existing plain-text badge content (the item summary
  Status badge has no `aria-label` either — same pattern, no regression in accessibility surface).
- Row layout (CSS grid on `.relationshipItem`) accommodates the new element as its own grid column,
  outside the ID/title link, so the link's existing `white-space: nowrap` /
  `text-overflow: ellipsis` single-line truncation continues to apply only to ID+title text and
  cannot clip mid-badge — without this separation, a padded/uppercase badge sharing the same
  ellipsis box as long, truncated title text risks the ellipsis rendering across the badge instead
  of the text. No overlap at the supported desktop minimum width (0004 Q5).

## Design

### Domain and invariants

None new. No domain concept changes; `status` is already part of `ItemRelationshipSummary`.

### Canonical file effects

None. Read-only rendering change.

### Service operations

None. No service or REST change — `relationships[...].status` is already returned by the existing
endpoint (0004 CLI/API contracts).

### CLI / API contracts

No change. CLI contracts are unaffected (WebUI-only); the existing `ItemDetail.relationships`
payload shape from 0004 is unchanged.

### UI states

- Valid relationship row: label, then status badge (own grid cell, not part of the clickable link),
  then the existing ID (bold) + title link.
- Invalid/missing relationship row: label, then the ID + title link as today with no status badge,
  existing "missing or invalid" text unchanged.
- All other UI states (loading, load error, empty Linked to, edit mode, delete confirm, invalid
  item findings) are unchanged from 0004.

## Acceptance Criteria

1. Given an item with a valid parent/child/blocks/blocked-by/related-to relationship, when the
   modal opens, then each corresponding row shows the linked item's status (via
   `STATUS_LABELS[status]`) ahead of its ID/title link, using the same badge classes as the item
   summary's Status field.
2. Given an item with a relationship pointing at a missing or invalid target, when the modal opens,
   then that row shows no status badge and the existing "missing or invalid" text is still present.
3. Given a relationship row with a long title, when the modal opens, then the title is still
   trimmed for stable layout and the status badge does not push the row into overflow at the
   supported desktop minimum width.
4. Given the existing 0004 acceptance criteria for Linked to ordering, empty state, and same-modal
   navigation, when this change ships, then all of them continue to pass unchanged (regression).

## Test Strategy

Per `.claude/skills/test-change/references/test-strategy.md`:

- Component tests (`web/src/components/__tests__/ItemModal.test.tsx`, extending the existing Linked
  to coverage) for: status badge present with correct label/class for a valid row; status badge
  absent for an invalid/missing row (existing "missing or invalid" text still asserted); long-title
  trim still holds with the badge present; new `.relationshipItem` grid-column CSS assertion.
- No new API/service/unit-level test — no server-side change.
- **Correction against initial plan, confirmed by actually running the suites rather than assuming:**
  0004's existing `f004-core-workspace.spec.ts` functional E2E test asserts exact `toContainText`
  substrings per relationship row (e.g. `"Child: TP-2 Build list filtering"`). Running it after
  implementation showed it fails, because the inserted status badge text lands inside that
  substring (actual: `"Child: In ProgressTP-2 Build list filtering"`). Fixed by updating the
  expected strings in that spec to include the badge text — this is the same class of assumption
  failure as the component `textContent` equality check, just one level up; not a new E2E test, but
  the existing one is not "unaffected" as originally planned here.
- Browser contract: added a `relationships` fixture (with a long title + status) to
  `browser-contract/item-modal-layout.spec.ts` and a real-browser assertion that the relationship
  row does not overflow the modal's right edge at the 1280px minimum width. The original plan
  ("component-level evidence is expected to suffice, N/A otherwise") was written before checking
  whether the existing browser-contract fixture exercised the Linked-to section at all — it didn't
  (no `relationships` field), so an unverified N/A would have shipped the one visual-overflow claim
  in this spec's acceptance criteria (AC3) without real evidence. Added rather than asserted N/A.

## Implementation Slices

1. Extract a local `StatusBadge` component from the existing item-summary Status field markup
   (no behavior change at that call site); use it from both the summary Status field and the new
   `RelationshipItem` badge (rendered as its own grid cell before the ID/title link, guarded on
   `item.valid`). Extend `ItemModal.module.css` `.relationshipItem`'s grid-template-columns to add
   the badge column.
2. Update/add component tests (valid-row badge, invalid-row no-badge, long-title-with-badge
   regression, summary Status field unchanged after the extraction); update the one existing test
   whose exact row `textContent` assertion (`"Parent: VP-0 Beta release"`) will change once the
   badge is inserted.
3. Run focused component tests, full `npm run test`, `npm run lint`, `npm run build`.
4. Run `npm run test:e2e:functional` and fix any existing functional E2E assertion broken by the
   badge insertion (see Test Strategy correction above — this was required, not hypothetical).
5. Run `npm run test:browser-contract`, adding relationship-row coverage to
   `browser-contract/item-modal-layout.spec.ts` if the existing fixture doesn't already exercise
   the Linked-to section with a long title (it didn't).

## Implementation Evidence

- Implemented in `web/src/components/ItemModal.tsx` (`StatusBadge` extraction, `RelationshipItem`
  badge cell) and `web/src/components/ItemModal.module.css` (`.relationshipItem` grid column).
- Component coverage in `web/src/components/__tests__/ItemModal.test.tsx`.
- Functional E2E coverage updated in `web/e2e/functional/f004-core-workspace.spec.ts`.
- Browser contract coverage added to `web/browser-contract/item-modal-layout.spec.ts`.
- Validation commands passed for this slice: `npm run test:component -- ItemModal.test.tsx`,
  `npm run test`, `npm run lint`, `npm run build`, `npm run test:e2e:functional`, and
  `npm run test:browser-contract`.

## Risks and Compatibility

- The existing component test asserting exact row `textContent` (e.g. `"Parent: VP-0 Beta
  release"`) and the existing functional E2E test asserting exact `toContainText` substrings per
  row both broke once the status badge was inserted — expected, intentional updates confirmed by
  running the suites, not regressions to work around; both were fixed as part of this change's
  tests rather than loosened.
- A CSS-grid-only implementation of the badge would have misaligned invalid/missing rows (fewer
  DOM children than the row's declared grid columns, shifting the link and state text into the
  wrong track) — avoided by always rendering the badge's grid cell, even empty, for every row
  regardless of validity.
- Visual density: adding a badge to every relationship row increases row height/complexity
  slightly; mitigated by reusing the existing compact badge treatment already proven at the
  standard desktop width in the summary section.
- No compatibility risk to 0004's REST contract, canonical files, or any non-Linked-to modal area.

## Assumptions

- Status sits before the ID/title link, as its own row element, rather than embedded inside the
  link's text — avoids the link's single-line ellipsis truncation potentially clipping across a
  padded badge, and still places status ahead of the title as TP-111 asks. The ID remains the
  leading bold element *within the link*; the badge is simply outside that link, not competing with
  it for "leading identifier" status.
- No status badge for invalid/missing targets is the correct handling of "cover the case where a
  linked item is missing or unreadable," rather than inventing a visual treatment for the
  placeholder `"unknown"` status.
- A small local `StatusBadge` component (props: `status`, rendered inline in `ItemModal.tsx` or a
  colocated file) is the right size of extraction — it wraps only the existing markup/classes/label
  lookup, adds no new behavior, and is justified by the two-call-site rule rather than speculative
  reuse.

## Open Questions

None blocking.
