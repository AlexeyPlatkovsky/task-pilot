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
| `decisions/` | Architectural decision records | You need the rationale behind a choice |

### Legacy Documents

These documents predate the SDD structure and are retained for reference. SDD documents
supersede them where they conflict.

| Document | Owns | Read when |
| --- | --- | --- |
| `taskpilot_concept.md` | Original product concept (superseded) | Historical reference only |
| `specs/` | Original specifications 0001, 0002 (superseded) | Historical reference; content migrated to SDD docs |

## Feature Registry

| ID | Feature | Status | Requirements | Tasks | Scenarios | Serves |
| --- | --- | --- | --- | --- | --- | --- |
| F001 | task-file-storage | planned | 7 | 8 | 7 | Phase 1 — File model and parser |
| F002 | domain-services | planned | 8 | 8 | 8 | Phase 2 — Domain/service layer |
| F003 | cli-interface | planned | 8 | 8 | 9 | Phase 3 — CLI |
| F004 | webui-workspace | planned | 8 | 8 | 8 | Phase 4 — Local WebUI |
| F005 | sqlite-index | planned | 7 | 8 | 7 | Phase 5 — SQLite index/cache |
| F006 | advanced-views | planned | 6 | 7 | 6 | Phase 6 — Better views |
| F007 | git-helpers | planned | 5 | 5 | 5 | Phase 7 — Git helpers |
| F008 | mcp-adapter | planned | 6 | 7 | 5 | Phase 8 — MCP adapter |

## Decision Log

| ADR | Title | Status |
| --- | --- | --- |
| ADR-001 | Markdown/YAML Files as Canonical Source of Truth | accepted |
| ADR-002 | Python Fast MVP Stack | accepted |
| ADR-003 | Pure YAML Item Files | accepted |
| ADR-004 | Separate Append-Only Comment Files | accepted |
| ADR-005 | Kanban Board as Primary Workspace Page | accepted |
