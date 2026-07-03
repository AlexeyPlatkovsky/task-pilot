# Routed Handoff Convention

When a pipeline or skill step includes "Run `<agent>`" (e.g. "Run `code-reviewer`"),
the executing AI must delegate to the named subagent in an isolated read-only context
through the agent launch mechanism. The agent's output is the required artifact for that
step. Do not write conclusions inline as a substitute for the agent output.

Agent invocation details — required inputs, execution mode, context requirements, output
shape — belong in the agent body (under `.claude/agents/`), not in the pipeline or skill
that delegates to it. Pipelines and skills reference agents by capability name only; they
do not duplicate how the agent works.

Every pipeline step that invokes an agent must verify the agent output artifact is present
before advancing. A missing, blocked, or failed agent artifact stops the pipeline at that
step.
