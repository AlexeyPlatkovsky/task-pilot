# Testing Instruction Gap Review

**Date:** 2026-06-28
**Scope:** TaskPilot testing instructions, current WebUI test layout, and F006 execution gap.

## Summary

The testing strategy already describes a reasonable pyramid, but enforcement was too implicit. The
F006 implementation added component tests and live Playwright browser evidence, but missed committed
functional E2E tests for the new major UI paths. The existing Playwright E2E suite also contains a
token/theme computed-style test, which is a browser contract test rather than a functional E2E
journey.

## Findings

| Severity | Area | Gap | Recommended fix | Status |
| --- | --- | --- | --- | --- |
| High | Functional E2E | Major UI paths can pass validation with Playwright CLI evidence but no committed Playwright test. | Require a test-level matrix and persistent functional E2E tests for major UI paths. | ✅ done; `npm run test:e2e:functional` passes |
| High | Test classification | `web/e2e/tokens.spec.ts` checks CSS token/theme computed values inside the functional E2E directory. | Move token/theme checks to a separate browser contract level. | ✅ done; `npm run test:browser-contract` passes |
| Medium | Instruction enforcement | Existing instructions say Playwright CLI is not a substitute, but validation did not explicitly fail that case. | Make `validate-change` verify committed tests and command results for selected levels. | ✅ done; instruction validation accepted |
| Medium | Component visibility | Component tests exist under `web/src/components/__tests__/`, but there is no separate component-test command or reporting label. | Add a discoverable `test:component` script and require artifacts to list component tests separately from pure unit tests. | ✅ done; `npm run test:component` passes |
| Medium | Test planning | The old test-change artifact could report selected levels without proving every requirement was classified. | Require a requirement-to-assertion test matrix with explicit skip reasons. | ✅ done; instruction validation accepted |
| Medium | Review gate | Instruction review could accept artifacts that were structurally valid while missing implied enforcement details. | Add an implicit-instruction audit to `instruction-evaluator`. | ✅ done; instruction validation accepted |
| Low | Package scripts | `npm run test:e2e` currently maps to all Playwright specs under one directory. | Split Playwright configs or projects into functional E2E and browser contract suites. | ✅ done; `npm run test:e2e` now runs functional e2e only |
| Low | Historical coverage | F006 component tests cover list/tree/validation behavior, but there is no functional cross-surface regression. | Add F006 Playwright functional specs in a follow-up change. | ✅ done; F006 functional spec added |

## Updated Instruction Direction

- Component tests remain the primary proof for React rendering, local state, accessibility, and
  component interactions.
- Functional E2E tests cover user journeys only: project loading, view switching, list filtering,
  tree navigation, item opening, editing, invalid-file recovery, and other REST-backed workflows.
- Browser contract tests cover real-browser style concerns: tokens, themes, responsive contracts,
  focus rings, viewport behavior, and visual-regression checks.
- Playwright CLI is investigation and validation evidence only. It may inform test authoring but
  does not replace committed Playwright TypeScript tests when a functional E2E or browser contract
  gate is selected.

## Follow-up Work

1. ✅ Add a `web/e2e/functional/` suite for user journeys and move current token checks out of the
   functional E2E layer.
2. ✅ Add a browser contract suite, for example `web/browser-contract/`, with its own Playwright
   config or project.
3. ✅ Add `test:component`, `test:e2e:functional`, and `test:browser-contract` scripts so CI and
   agent artifacts can report the levels separately.
4. ✅ Add F006 functional E2E coverage for Board/List/Tree tabs, list sort/filter, tree item
   opening, and validation panel rendering.
5. ✅ Decision: do not add mandatory independent test-scope review for every UI feature. The new
   required test-level matrix plus validation gate closes the observed gap; independent pre-change
   test-scope review remains reserved for major/high-risk feature work.

## Remediation Evidence

| Check | Result |
| --- | --- |
| `npm run test` | ✅ 13 files, 85 tests passed |
| `npm run test:component` | ✅ 12 files, 67 tests passed |
| `npm run test:e2e:functional` | ✅ 1 functional F006 Playwright test passed |
| `npm run test:e2e` | ✅ alias runs functional E2E only and passed |
| `npm run test:browser-contract` | ✅ 4 browser contract Playwright tests passed |
| `npm run lint` | ✅ passed |
| `npm run build` | ✅ passed with existing Vite chunk-size warning |
