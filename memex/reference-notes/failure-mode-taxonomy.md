---
last-touched: 2026-04-11
category: reference
tags: [failure-modes, agentic-loop, taxonomy, debugging, reliability]
---

# Failure Mode Taxonomy

Catalog of known agentic failure modes for tinyagent. Referenced by -> [agentic-loop-failure-modes thread](../active-threads/agentic-loop-failure-modes.md). Each entry includes detection signals and recovery strategies. Vocabulary definitions in -> [agentic-design-vocabulary.md](agentic-design-vocabulary.md).

## Taxonomy

### Brute-Force Retry
- **Description**: The agent repeats the same failing action without changing approach. Typically re-runs a tool call that returned an error, expecting a different result.
- **Detection signal**: Two or more identical (or near-identical) tool calls in sequence with the same error.
- **Recovery strategy**: Detect at the loop level. After 2 identical failures, force the agent to articulate an alternative approach before retrying. Escalation ladder: retry -> alternate approach -> re-plan -> ask human.
- **Severity**: Medium. Wastes context budget but usually self-limiting (the model eventually tries something else).

### Plan Drift
- **Description**: Gradual divergence between the agent's stated plan and its actual execution. Each step seems locally reasonable, but the aggregate trajectory has shifted from the original goal.
- **Detection signal**: Compare current action rationale against the original plan. If the agent is justifying steps not in the plan without explicitly re-planning, drift is occurring.
- **Recovery strategy**: Persistent plans with numbered steps. The loop checks: "which plan step are we on?" If the agent acts outside the plan, require explicit re-planning. See -> [pivot to plan-execute](../artifacts/2026-04-11-pivot-react-loop-to-plan-execute.md).
- **Severity**: High. Produces plausible but wrong results. The output looks complete but doesn't match the original intent.

### Context Exhaustion
- **Description**: The conversation has consumed enough context that the agent can no longer load information needed for the current task. Quality degrades as the model loses access to earlier instructions or file contents.
- **Detection signal**: Token usage approaching B_discretionary limit. Qualitative: agent starts asking for information it was already given, or produces shallow/generic responses.
- **Recovery strategy**: Compaction triggers at 90% of B_discretionary. Proactive: estimate task size before starting and warn if it may exceed budget. See -> [context-budget-formal-model.md](../artifacts/2026-04-11-context-budget-formal-model.md).
- **Severity**: High. Degrades silently — the model doesn't announce it's losing context.

### Tool Hallucination
- **Description**: The model invents a tool that doesn't exist, or calls a real tool with fabricated parameter names or impossible values.
- **Detection signal**: Tool dispatch fails with "unknown tool" or "unknown parameter" error. More subtle: syntactically valid calls with semantically impossible inputs (e.g., reading a file path that was never mentioned).
- **Recovery strategy**: Strict schema validation before dispatch. Return clear error messages naming the available tools. Keep tool schemas unambiguous — vague descriptions increase hallucination rate.
- **Severity**: Medium. Caught by validation, but wastes a turn. Frequent hallucination may signal the tool set is too large or too ambiguous (schema tax problem).

### Infinite Delegation
- **Description**: In multi-agent systems, agents delegate tasks to each other in a cycle, with no agent actually performing the work. Can also manifest as a single agent repeatedly deferring ("I'll need to check that") without ever checking.
- **Detection signal**: Turn count increasing without tool calls or concrete output. Agent responses contain hedging language but no actions.
- **Recovery strategy**: Maximum turn limit per task. Require at least one tool call or concrete output per N turns. For multi-agent: acyclic delegation graph enforced at the orchestrator level.
- **Severity**: Medium. Obvious once detected but can burn significant context before detection.

### Partial Completion
- **Description**: The agent declares the task complete, but some steps were skipped or some outputs are missing. The "done" signal is premature.
- **Detection signal**: Compare the declared output against the original plan's success criteria. Automated: check that all planned deliverables exist. Manual: review before accepting.
- **Recovery strategy**: Explicit completion checklist derived from the plan. The loop verifies each item before allowing the agent to declare done. Don't trust "I've completed all the steps" — verify.
- **Severity**: High. The most dangerous failure mode because it terminates the loop. Everything downstream proceeds on the assumption the task is done.

### Scope Creep
- **Description**: The agent does more than asked — refactoring code that should be left alone, adding features not requested, "improving" things outside the task boundary.
- **Detection signal**: Diff review shows changes to files or functions not mentioned in the task. Agent explains changes with "while I was here, I also..." language.
- **Recovery strategy**: Explicit scope boundaries in the plan. The ask-vs-act threshold applies: unasked-for changes with high blast radius should be proposed, not applied. Tool-level guardrails: restrict which files/directories the agent can modify.
- **Severity**: Low to medium. Sometimes helpful, but breaks trust. The human can't rely on the agent staying in its lane.

### Silent Failure
- **Description**: An error occurs but is swallowed — the agent produces output as if the operation succeeded. Includes: tool errors ignored, wrong results accepted without validation, exceptions caught and discarded.
- **Detection signal**: Hardest to detect. Requires output validation against ground truth. Signals: agent's summary doesn't mention errors that appeared in tool results; output is suspiciously generic.
- **Recovery strategy**: Never suppress tool errors in the loop. Surface all non-zero exit codes and error messages to the model. Build validation steps into plans: after writing code, run it; after editing a file, read it back.
- **Severity**: Critical. The failure is invisible. Downstream work builds on a wrong foundation. The later it's caught, the more expensive the rework.
