---
last-touched: 2026-04-12
category: design
hits: 2
tags: [agentic-loop, failure-modes, reliability]
---

# Agentic Loop Failure Modes

## Summary

An agentic loop (plan-act-observe-reflect) has characteristic failure modes that recur across implementations. Naming them makes them designable. This thread catalogs five failure modes observed during tinyagent development, each with a concrete countermeasure. The goal is not perfection — it's making failures shallow and recoverable.

## The Catalog

### 1. Brute-Force Retry

The agent repeats a failing action verbatim, expecting different results. Common with file writes that fail on permissions or shell commands with wrong syntax.

**Countermeasure:** Track the last N actions. If the same tool call appears twice with identical parameters, force an alternative — escalate to the user, try a different approach, or surface the error as a planning input.

### 2. Plan Drift

The agent forgets the original goal mid-execution. Happens when the conversation grows long and the task description scrolls out of the context window.

**Countermeasure:** Pin the task description in context. Tinyagent's session header includes the original task, and the compaction logic never summarizes it away. Periodic re-grounding: every N turns, re-read the task.

### 3. Context Exhaustion

The discretionary budget runs out mid-task. The agent has loaded too many file reads or the conversation has grown too long. Symptoms: truncated responses, incoherent planning, dropped tool results.

**Countermeasure:** Compaction triggers at 70% budget usage. Graceful degradation: summarize old turns, drop low-priority tool results, warn the user that context is tight. Never let it hit 100%.

### 4. Tool Hallucination

The agent invents tool names or parameters that don't exist. Happens more often when many tools are registered or tool names are ambiguous.

**Countermeasure:** Strict schema validation on every tool call. Unknown tool names get a clear error message, not a silent failure. Keep tool count low (see grain-size thread).

### 5. Infinite Delegation

The agent asks the user instead of acting. "Should I read the file?" — just read it. This is the conservative failure mode, less dangerous but corrosive to usefulness.

**Countermeasure:** Bias toward action for reversible operations. Reading is always safe. Writing to a new file is safe. Overwriting or deleting requires confirmation. The threshold is blast radius, not uncertainty.

## Connections

→ [Error Recovery as Design](error-recovery-as-design.md) — what the agent does after catching a failure
→ [Ask vs Act Thresholds](ask-vs-act-thresholds.md) — the reversibility framework behind countermeasure #5
→ [Failure Mode Taxonomy](../reference-notes/failure-mode-taxonomy.md) — expanded version of this catalog
→ [Context Budget Economics](context-budget-economics.md) — the budget model behind countermeasure #3
