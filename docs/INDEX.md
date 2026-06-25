# Documentation Index

**Tier:** Standard
**Docs root:** `docs/`

## Documents

| Document | Owns | Read when |
| --- | --- | --- |
| `idea.md` | Problem, users, scope, principles | You need project intent or scope boundaries |
| `architecture.md` | Technical structure, components, data model, tech stack, constraints | You need system design or stack details |
| `design.md` | Product/UX design: user flows, screens, states, UX principles, accessibility | You need UI design or interaction patterns |
| `testing.md` | Test strategy, levels, tooling, environments, quality gates | You need how quality is verified |
| `roadmap.md` | Phases, milestones, release levels, sequencing, implementation phases | You need release plan or priorities |
| `specs/` | Accepted product contracts, behavior, public interfaces, persistence decisions | You need governing product requirements |
| `decisions/` | Architectural decision records | You need the rationale behind a choice |

### Legacy Documents

These documents predate the SDD structure and are retained for reference. Accepted specifications
under `docs/specs/` supersede them where they conflict.

| Document | Owns | Read when |
| --- | --- | --- |
| `taskpilot_concept.md` | Original product concept (superseded by accepted specs where they differ) | Historical reference only |

## Feature Registry

| ID | Feature | Status | Requirements | Tasks | Scenarios | Serves |
| --- | --- | --- | --- | --- | --- | --- |
| F001 | task-file-storage | planned | 7 | 8 | 7 | Phase 1 — File model and parser |
| F002 | domain-services | implemented | 8 | 8 | 8 | Phase 2 — Domain/service layer |
| F003 | cli-interface | in progress | 8 | 8 | 9 | Phase 3 — CLI |
| F004 | webui-workspace | implemented | 9 | 9 | 9 | Phase 4 — Local WebUI |
| F006 | advanced-views | planned | 5 | 6 | 5 | Phase 5 — Better views |
| F007 | git-helpers | planned | 5 | 5 | 5 | Phase 6 — Git helpers |
| F008 | mcp-adapter | planned | 6 | 7 | 5 | Phase 7 — MCP adapter |

## Decision Log

| ADR | Title | Status |
| --- | --- | --- |
| ADR-001 | Markdown/YAML Files as Canonical Source of Truth | accepted |
| ADR-002 | Python Fast MVP Stack | accepted |
| ADR-003 | Pure YAML Item Files | accepted |
| ADR-004 | Separate Append-Only Comment Files | accepted |
| ADR-005 | Kanban Board as Primary Workspace Page | accepted |
| ADR-006 | System Registry in the CLI Adapter for Alpha | accepted |
