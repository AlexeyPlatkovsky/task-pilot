# Plan: Fix batch-task and agent-delegation instruction gaps

## Pipeline

Route: `instruction-change.md` (non-trivial, low risk, instruction-only)

Ordered steps:
1. `maintain-instruction-system` → implement changes
2. `instruction-evaluator` agent → isolated review
3. `artifact-acceptance-tester` agent → 9 scenarios per target
4. `validate-change` → check references, paths, diff scope

---

## Changes

### AGENTS.md — add batch-task routing clause

**After line 45** (after `"A user saying 'implement,' 'fix,' or equivalent triggers this gate again."`):

```
When a user requests multiple tasks in a single instruction (for example "implement the rest of
the tasks" or "do T5 through T10"), re-enter the routing gate for each task that changes behavior
in a distinct area. At minimum, produce one manager artifact that names every requested task,
classifies each one individually, and lists the ordered per-task handoffs. Do not treat a batch
of tasks as a single classification.
```

### feature-change.md — clarify agent delegation for code-reviewer steps

**Replace lines 43–44** (step 4 description):

Old:
```
4. Run `code-reviewer` on the test scope when the conditional gates require it. Require
   `Agent: code-reviewer - output below`.
```

New:
```
4. Delegate to the `.claude/agents/code-reviewer.md` agent in an isolated read-only
   context when the conditional gates require test-scope review. Pass the full diff
   scope, governing specification, and acceptance criteria. Require
   `Agent: code-reviewer - output below`. Do not write review conclusions inline as a
   substitute for the agent output.
```

**Replace lines 49–50** (step 8 description):

Old:
```
8. Run `code-reviewer` when the manager classified risk as medium, high, or system-level. Require
   `Agent: code-reviewer - output below`.
```

New:
```
8. Delegate to the `.claude/agents/code-reviewer.md` agent in an isolated read-only
   context when the manager classified risk as medium, high, or system-level. Pass the
   full diff scope, governing specification, and acceptance criteria. Require
   `Agent: code-reviewer - output below`. Do not write review conclusions inline as a
   substitute for the agent output.
```

## Impact

- 2 files changed, no files created/deleted, no path renames
- AGENTS.md capability registry already lists code-reviewer agent — no sync needed
- No `.manifesto/` files touched
- Both edits stay in correct layers (root contract + pipeline)

## Verification

After edits:
1. `git diff` — confirm only 2 files, only targeted sections changed
2. Check no stale references
3. instruction-evaluator agent review
4. artifact-acceptance-tester agent (9 scenarios/target)
