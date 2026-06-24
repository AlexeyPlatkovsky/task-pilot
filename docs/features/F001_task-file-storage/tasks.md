# F001 Task File Storage — Tasks

| ID | Task | Implements | Status | Depends on |
| --- | --- | --- | --- | --- |
| F001-T1 | Define `.taskpilot/` folder layout constants and path resolution helpers | F001-R1 | done | — |
| F001-T2 | Implement `taskpilot init` workspace creation | F001-R1 | done | F001-T1 |
| F001-T3 | Implement item YAML parser with Pydantic models for all mandatory and optional fields | F001-R2 | done | F001-T1 |
| F001-T4 | Implement deterministic item YAML writer with stable field ordering | F001-R3 | done | F001-T3 |
| F001-T5 | Implement comment Markdown parser with YAML frontmatter extraction | F001-R4 | todo | F001-T1 |
| F001-T6 | Implement comment file writer with timestamp-based naming and collision disambiguation | F001-R5 | todo | F001-T5 |
| F001-T7 | Implement item validation: required fields, valid enums, unique IDs, valid references | F001-R6 | todo | F001-T3 |
| F001-T8 | Implement project loader that separates valid items from validation errors | F001-R7 | todo | F001-T3, F001-T7 |

## Notes

- Item YAML field order should match `docs/specs/0002-alpha-product-and-stack-decisions.md`: `schema_version`, `id`, `title`, `priority`, `type`, `status`, `created_at`, `updated_at`, then known optional fields in the accepted order, followed by preserved unknown fields in deterministic key order.
- Comment filename format: `YYYY-MM-DDTHH-MM-SSZ.md`. Collision suffix: `-2`, `-3`, etc.
- Parser should handle and report YAML syntax errors, not crash.
