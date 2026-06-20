---
name: brainstorm
description: Resolves an open TaskPilot design or setup decision with materially different options before execution. Do not use for factual questions or after a choice is confirmed.
---

# Brainstorm

Keep discussion separate from execution.

1. Ask exactly one decision question per turn.
2. Present two or three concrete options.
3. State what each option optimizes, sacrifices, and risks.
4. Include a free-form correction path for factual setup choices.
5. Stop and wait after each question.
6. Do not create or edit files during brainstorming.
7. When all decisions are made, emit a decision summary and wait for confirmation before execution.

Focus only on choices that materially affect routing, contracts, persistence, architecture,
validation, or reusable instruction structure.

The final artifact begins with `Skill: brainstorm - output below` and lists status, each decision,
selected option, constraints, assumptions, and unresolved blockers.
