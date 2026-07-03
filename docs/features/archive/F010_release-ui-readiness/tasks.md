# F010 Release UI Readiness — Tasks

| ID | Task | Implements | Status | Depends on |
| --- | --- | --- | --- | --- |
| F010-T1 | Extract or extend shared filter controls/options so Board and List can share dropdown behavior and date-range semantics | F010-R1, F010-R2, F010-R3 | ✅ done | — |
| F010-T2 | Add Board filters for type, priority, updated range, and created range with Clear behavior and filtered-empty column handling | F010-R1, F010-R3 | ✅ done | F010-T1 |
| F010-T3 | Add List created time range filtering and update combined filter/reset behavior | F010-R2, F010-R3 | ✅ done | F010-T1 |
| F010-T4 | Hide the Tree tab from release-facing navigation and update release-facing tests/docs while keeping Tree code importable | F010-R4 | ✅ done | — |
| F010-T5 | Implement local UI-state service/model for `ui-state.yaml` in the existing TaskPilot system directory with `TASKPILOT_HOME` support | F010-R5, F010-R6 | ✅ done | — |
| F010-T6 | Add `GET /api/ui-state` and `PATCH /api/ui-state` with partial-update validation, null clearing, unknown-field rejection, and active-project validation | F010-R6 | ✅ done | F010-T5 |
| F010-T7 | Wire WebUI startup to fetch UI state first, then projects, and silently restore or fall back according to active project availability | F010-R7 | ✅ done | F010-T6 |
| F010-T8 | Save last opened project on explicit user selection while keeping current-session selection usable if persistence fails | F010-R8 | ✅ done | F010-T7 |
| F010-T9 | Configure WebUI item/project validation queries to refetch every 5 seconds and on focus/visibility return for Board, List, item detail, and validation status | F010-R9 | ✅ done | F010-T7 |
| F010-T10 | Protect dirty item detail edit fields from background refresh overwrites while allowing clean data to refresh | F010-R10 | ✅ done | F010-T9 |
| F010-T11 | Add `validation-success-muted` token and apply it to the all-valid validation success state | F010-R11 | ✅ done | — |
| F010-T12 | Add component, API, functional E2E, and browser-contract coverage for filters, Tree hiding, UI-state restore/save, refresh behavior, dirty edit protection, and validation contrast | F010-R1, F010-R2, F010-R3, F010-R4, F010-R5, F010-R6, F010-R7, F010-R8, F010-R9, F010-R10, F010-R11 | ✅ done | F010-T2, F010-T3, F010-T4, F010-T6, F010-T8, F010-T10, F010-T11 |
| F010-T13 | Hold and document the task detail redesign discussion before any implementation work starts | F010-R12 | ✅ done | — |

## Notes

- Board status filtering is intentionally not included because Board columns already represent
  status.
- Date filters should reuse one deterministic date-range helper instead of duplicating range logic
  per view.
- UI-state persistence belongs beside the existing registry infrastructure but should not change
  `registry.yaml` or the registry schema.
- Polling is the accepted Beta approach for external update visibility; do not introduce push
  channels for F010.
- If task detail redesign is implemented later, route it as a separate UI discussion/spec slice
  before production code changes.
