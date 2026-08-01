# Default Updated Filter

Status: implemented

## Outcome

When a user opens the Board view or the List view, items that have not been updated in the last 7
days are hidden by default — the Updated filter starts at `Last 7 days` instead of `Any time`. The
filter remains the same first-class, visible, user-clearable control it already is: its trigger
always shows the active value (`Updated: Last 7 days`), and Clear restores every filter, including
Updated, to its default.

## Context

`docs/roadmap.md` ("Board and List Filter Readiness") and its implementation
(`web/src/components/filters.ts` `DEFAULT_BOARD_FILTERS.updatedRange`,
`web/src/components/ItemListView.tsx` `DEFAULT_FILTERS.timeRange`) currently default the Updated
filter to `all` (`Any time`) on both views. TP-109 asks for that default to become `last_7_days`
("Last 7 days") on every board on load, so stale items don't clutter the default view.

TP-109's description flagged two open questions before this could be specified. Both are settled
here, by explicit user decision (not inferred):

1. **Scope — which boards?** "on all boards" means both the Kanban Board view and the List view.
   They already share the same `Updated` filter component (`UPDATED_FILTER_OPTIONS` in
   `filters.ts`) and options, and the roadmap treats Board/List filters as a matched pair — there is
   no reason for the default to diverge between them.
2. **Does the user's last-used filter override the default on return visits?** No. The filter always
   resets to `Last 7 days` on every fresh mount of Board or List, matching the literal "on load"
   wording in TP-109. No local-storage or other persistence of a previously chosen Updated value is
   added by this change; filter state remains component-local `useState`, as it is today.

A third question — "how does the default interact with items that have never been updated since
creation?" — turned out not to need a design decision: `updated_at` is always populated at item
creation, set equal to `created_at`
(`src/taskpilot/services/item_service.py` `create_item`; `Item.updated_at` is a mandatory,
non-Optional field in `src/taskpilot/core/models.py`). There is no "never updated" state to special-
case. A never-touched item simply ages out of the default `Last 7 days` view once more than 7 days
have passed since its creation, exactly as an item that was updated 8+ days ago and never touched
again would. This is expected, visible behavior (see Requirements), not a defect or an edge case
requiring extra handling.

Because this changes a default that `docs/roadmap.md` documents as already implemented/release-
ready, it is a default-behavior change to an already-accepted feature and requires a specification
(`.claude/conventions/classification-scans.md`, specification-materiality scan).

## Scope

In scope:
- Change `DEFAULT_BOARD_FILTERS.updatedRange` (Board view) and `DEFAULT_FILTERS.timeRange` (List
  view) from `"all"` to `"last_7_days"`.
- `docs/roadmap.md`'s "Board and List Filter Readiness" section updated to state the new default.

Out of scope:
- The `Created` time-range filter's default (`createdRange`) — stays `Any time`. TP-109 only asks
  about the `Updated` filter.
- Tree view — filters remain out of release scope there per the roadmap.
- Any persistence of user filter choices across sessions (explicitly declined, see Context).
- Any change to the `UPDATED_FILTER_OPTIONS` option list, filter component markup, `FilterBar`,
  `DropdownSelect`, or the time-range matching logic (`isWithinTimeRange`) — the existing visible-
  trigger-label and Clear-restores-defaults behavior already satisfies TP-109's "visible and
  overridable, not hidden" requirement without any component change.
- Any API/service/CLI/canonical-file change — this is pure frontend default-state.

## Requirements

### Functional

- On first render of the Board view, `boardFilters.updatedRange` is `"last_7_days"`; items whose
  `updated_at` falls outside the last 7 days (relative to the existing `filterReferenceTimeForItems`
  reference time) are excluded from every column, same as if the user had selected `Last 7 days`
  manually today.
- On first render of the List view, `filters.timeRange` is `"last_7_days"`, with the equivalent
  effect on the table's rows.
- The Updated dropdown's visible trigger label reflects the default on load (`Updated: Last 7
  days`), with no extra "active filter" indicator needed beyond the existing label.
- Clicking Clear on either view resets Updated (and every other filter) back to its default —
  `Last 7 days` for Updated, unchanged defaults for Type/Priority/Created.
- The user can change Updated to any other option (`Any time`, `Last 14 days`, `Last 30 days`) at
  any time, same as today; nothing about the filter's overridability changes.
- Reloading/remounting Board or List (e.g. navigating away and back, or a page refresh) re-applies
  the `Last 7 days` default — no prior in-session or cross-session selection is remembered.

### Quality

- No new persistence mechanism (local storage, query params, server-side preference) is introduced.
- No visual/component changes beyond the default value — this reuses the existing `DropdownSelect` /
  `FilterBar` pattern exactly as implemented for the Board/List Filter Readiness roadmap item.

## Design

### Domain and invariants

None new. No domain model change; `updated_at` semantics are unchanged (already always populated at
creation, per Context).

### Canonical file effects

None. No canonical task file, schema, or persistence change.

### Service operations

None. No service/REST change — this is client-side initial state only.

### CLI / API contracts

No change.

### UI states

- **Board view, initial load**: `Updated: Last 7 days` shown in the filter trigger; columns show
  only items updated within the last 7 days; `hasActiveBoardFilters` is `false` (the applied value
  equals the default), so the Clear button's visibility behavior is unchanged from today's pattern —
  only the value it now represents is different.
- **List view, initial load**: same as Board, mirrored in `ItemListView`'s own `Filters`/
  `DEFAULT_FILTERS`.
- **Filtered-empty state**: if every item on a project falls outside the last 7 days, the existing
  "No items match the selected filters" (Board) / equivalent List empty state now can appear on a
  cold load for older, otherwise-untouched projects — this is expected per Requirements, not a new
  empty-state variant to build; the existing filtered-empty UI already renders it.
- **User changes/clears Updated**: unchanged from today's implemented behavior.

## Acceptance Criteria

1. Given a project with items updated both within and beyond the last 7 days, when the Board view
   first mounts, then only items updated within the last 7 days appear in the columns, and the
   Updated filter trigger reads `Updated: Last 7 days`.
2. Given the same setup, when the List view first mounts, then only items updated within the last 7
   days appear in the table, and the Updated filter trigger reads `Updated: Last 7 days`.
3. Given the Board or List view with the default Updated filter applied, when the user selects `Any
   time` (or `Last 14/30 days`), then the item set updates accordingly, exactly as it does today for
   any manual filter change.
4. Given the Board or List view with any filters changed from default, when the user clicks Clear,
   then every filter — including Updated — returns to its default (`Last 7 days` for Updated), and
   the previously hidden items reappear if they fall within the new default range.
5. Given a Board or List view is unmounted and remounted (e.g. simulating navigation away and back),
   when it mounts again, then Updated is `Last 7 days` again, regardless of what the user last
   selected in the prior mount.
6. Given a project where every item's `updated_at` is older than 7 days (including items never
   updated since creation, which use their `created_at` as `updated_at`), when Board or List first
   mounts, then the existing filtered-empty state is shown and the Updated trigger still reads
   `Updated: Last 7 days`, making the applied filter visible rather than presenting a silent/empty
   board.

## Test Strategy

Per `.claude/skills/test-change/references/test-strategy.md`:

- Component tests (`web/src/components/__tests__/KanbanBoard.test.tsx`,
  `web/src/components/__tests__/ItemListView.test.tsx`): assert the default trigger label and
  filtered item set on initial render (AC1, AC2, AC6); assert Clear restores `Last 7 days`, not `Any
  time` (AC4) — the two existing assertions at `KanbanBoard.test.tsx:298` and
  `ItemListView.test.tsx:519,545` (`"Updated: Any time"` after Clear) are expected to change to
  `"Updated: Last 7 days"` as part of this change, not a regression to work around.
- No new API/service/unit-level test — no backend change.
- Functional E2E: check whether an existing `web/e2e/functional` spec asserts an unfiltered
  Board/List item count or relies on the current `Any time` default surfacing older fixture items;
  update or add a case per AC1/AC2/AC5 if the fixture set requires it.
- Browser contract: not expected to be needed — no new visual state, class, or token; N/A unless
  investigation during `test-change`/`implement-change` finds otherwise.

## Implementation Slices

1. Flip `DEFAULT_BOARD_FILTERS.updatedRange` and `ItemListView`'s `DEFAULT_FILTERS.timeRange` to
   `"last_7_days"` in `web/src/components/filters.ts` and `web/src/components/ItemListView.tsx`.
2. Update the two existing Clear-restores-default assertions (`KanbanBoard.test.tsx`,
   `ItemListView.test.tsx`) and any other test whose expectations assumed the `Any time` default,
   and add the new default-on-load assertions (AC1, AC2, AC6).
3. Run `npm run test`, `npm run lint`, `npm run build`.
4. Run `npm run test:e2e:functional`; fix or extend any spec whose fixtures/assertions assumed the
   old default.
5. Update `docs/roadmap.md`'s "Board and List Filter Readiness" section to state the new Updated
   default.

## Implementation Evidence

- Production default flip: `web/src/components/filters.ts` (`DEFAULT_BOARD_FILTERS.updatedRange`)
  and `web/src/components/ItemListView.tsx` (`DEFAULT_FILTERS.timeRange`), both `"all"` →
  `"last_7_days"`. No other production markup/behavior changed.
- **Correction against the initial plan, found while running the suites rather than assumed:** the
  plan ("no new UI affordance needed... existing filtered-empty UI already renders it") undersold
  one real gap. `KanbanBoard.tsx`'s `showEmptyPrompt`/`showFilteredEmpty` split compared
  `boardFilters` against `DEFAULT_BOARD_FILTERS` to decide "is a filter active." Once the default
  itself narrows by `updatedRange`, an all-stale project at the *default* state is indistinguishable
  from "no filters ever touched," so it rendered the plain "No items yet." empty prompt instead of
  "No items match the selected filters." — directly contradicting AC6 ("the applied filter visible
  rather than presenting a silent/empty board"). Fixed by comparing against an unfiltered
  `groupByStatus(items)` instead of `DEFAULT_BOARD_FILTERS` to decide which empty state applies,
  while leaving `hasActiveBoardFilters`'s original default-comparison semantics untouched for the
  Clear button's `disabled` state (still correct: Clear is a no-op exactly when nothing differs from
  default). `ItemListView.tsx` needed no equivalent fix — its filtered-empty/plain-empty split
  already keys off raw `items.length` vs. `filteredItems.length`, not a default comparison.
- **Test-fixture blast radius larger than anticipated:** flipping the default broke far more than
  the two Clear-restores-default assertions named in the plan, because `isWithinTimeRange` excludes
  any item with a missing or out-of-range `updated_at` once the *default* filter is a real range,
  not just after an explicit user selection. Fixed:
  - `KanbanBoard.test.tsx`'s `makeItem` had no default `created_at`/`updated_at` at all (~30 call
    sites relied on this); `ItemListView.test.tsx`'s and `ProjectWorkspace.test.tsx`'s `makeItem`
    defaulted to a fixed past date. All three now default to call-time `new Date().toISOString()`,
    which also correctly resolves under `vi.setSystemTime` fake-timer tests since it evaluates at
    call time, not module load.
  - Four component tests that explicitly set a fixed past `updated_at`/`created_at` with no `now`
    prop (comparing against real `Date.now()`) had those irrelevant date overrides removed so they
    fall back to the recent default, since they weren't testing date behavior.
  - One test (`ItemListView.test.tsx`, "clears all active filters...") passed a fixed `now` prop but
    left `created_at` on its default (real-clock) value, which is chronologically *after* the fixed
    `now` and so always fails `isWithinTimeRange`'s `<= now` check once a real range is selected;
    fixed by making both timestamp fields explicit and consistent with the fixed `now`.
  - `web/e2e/support/start-taskpilot-api.mjs` now restamps the committed fixture workspace's item
    `created_at`/`updated_at` to the current run time (stripped to canonical
    `YYYY-MM-DDTHH:MM:SSZ`, no fractional seconds, per `src/taskpilot/core/models.py`
    `_check_timestamp`) immediately after copying it to the Playwright scratch workspace, so
    `openFixtureProject()` journeys in `f004`/`f006` keep seeing their items under the new default.
  - `f004-core-workspace.spec.ts`'s `mockItemSummary` and both `browser-contract` fixtures
    (`kanban-card-layout.spec.ts`'s `items`, `item-modal-layout.spec.ts`'s `itemSummary`) had no
    dates at all and needed a recent `created_at`/`updated_at` added.
- `docs/roadmap.md` "Board and List Filter Readiness" updated to state the new Updated default.
- Validation commands run: `npm run test` (185/185), `npm run lint`, `npm run build`,
  `npm run test:e2e:functional` (7/7), `npm run test:browser-contract` (7/7). No Python file
  changed; confirmed no backend code or test references these frontend filter defaults.

## Risks and Compatibility

- Existing tests that render Board/List with older mock items and no explicit non-default Updated
  selection may now unexpectedly filter those items out, because `filterReferenceTimeForItems`
  derives "now" from the latest item timestamp (or real `Date.now()`) when no `now` prop is passed —
  older items relative to that reference can fall outside 7 days. Expected, intentional test updates
  once identified by running the suite, not silent breakage to paper over.
- Any Board/List screenshot, story, or manual-QA workflow that assumed all seeded items are visible
  by default will now need `Updated: Any time` selected explicitly, or fixture dates within 7 days
  of the reference time, to see the full set — a real, intended behavior change per TP-109, not a
  bug.
- No compatibility risk to any API/service/canonical-file contract — purely client-side default
  state.

## Assumptions

- "On load" means on every fresh component mount of Board/List, not merely the very first visit to
  the app — confirmed with the user (Persistence decision, Context).
- Both Board and List views get the new default, not Board alone — confirmed with the user (Scope
  decision, Context).
- No new UI affordance is needed to make the default "visible" beyond the existing
  `aria-label={`${label}: ${selectedLabel}`}` trigger pattern already implemented for every filter
  dropdown — it already always shows the active value, satisfying TP-109's "visible... not hidden
  behavior" requirement.

## Open Questions

None blocking — both open questions raised in TP-109's description are resolved above.
