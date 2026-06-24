# Review Severity Standard

Use this scale for `code-reviewer` and `design-reviewer` findings that gate feature, UI, and
refactor routes.

Instruction-system evaluators, artifact acceptance testers, and agents with canonical output
contracts keep their own verdicts, severities, and stop conditions.

| Severity | Use when | Routed gate |
| --- | --- | --- |
| Critical | The change can corrupt canonical task data, violate source-of-truth rules, break a public contract, create a destructive or security risk, or make a required workflow unusable. | Must fix and re-review. |
| High | The change misses an accepted requirement, causes a likely user-visible regression, breaks important error handling, or violates an architecture boundary. | Must fix and re-review. |
| Major | The change is materially incomplete, under-tested at a required boundary, creates a credible maintenance or compatibility risk, or leaves required validation evidence missing. | Must fix and re-review. |
| Low | The issue is real but does not block correctness, safety, required behavior, or required validation evidence. | May fix without re-review or report as residual risk. |

Do not report style-only preferences as review findings. When severity is uncertain, choose the
lower severity unless the impact plausibly blocks correctness, safety, contracts, or required
evidence.
