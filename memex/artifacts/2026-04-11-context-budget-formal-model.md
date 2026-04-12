---
date: 2026-04-11
depth: deep
tags: [context-window, token-economics, architecture, formal-model, compaction]
source-thread: ../active-threads/context-budget-economics.md
source: agent
summary: Formal model of context economics for agentic systems. Defines budget partitions (pinned, discretionary, conversation, working), compaction triggers, and the token ROI concept. Mental model, not a runtime optimizer.
---

# Context Budget Formal Model

## Budget Partitions

The context window is a finite resource. Understanding how it decomposes is prerequisite to managing it.

```
B_total = model context window (e.g., 200K tokens)

B_total = B_reserve + B_pinned + B_discretionary

Where:
  B_reserve       = output token reservation (e.g., 16K tokens)
  B_pinned        = system prompt + tool schemas (measured, stable)
  B_discretionary = B_total - B_reserve - B_pinned

B_discretionary = B_conversation + B_working

Where:
  B_conversation  = message history (user + assistant turns)
  B_working       = file contents, search results, tool outputs
```

## Measuring the Partitions

| Partition | How to measure | Typical range |
|-----------|---------------|---------------|
| B_reserve | Fixed per request (max_tokens) | 4K-16K |
| B_pinned | Count system prompt + all tool schemas once at startup | 2K-8K depending on tool count |
| B_conversation | Accumulates with each turn; dominates in long sessions | 0 to B_discretionary |
| B_working | Spikes when files are read or search results returned; decays as results age out | Highly variable |

**Key insight**: B_pinned is a tax paid on every request. Each tool schema added to the system costs tokens on every single API call. This is the "schema tax" — see -> [agentic-design-vocabulary.md](../reference-notes/agentic-design-vocabulary.md).

## Compaction

### Trigger Condition

```
Compact when: B_conversation + B_working > B_discretionary * 0.9
```

The 0.9 threshold leaves a 10% buffer for the next tool call's output. Hitting this threshold without compaction risks truncation or failed requests.

### Compaction Strategy (ordered by aggression)

1. **Drop stale tool results**: Tool outputs older than M turns are replaced with a one-line summary ("read_file returned 150 lines of foo.py")
2. **Truncate large file reads**: Files over T tokens are replaced with first/last N lines plus a summary
3. **Summarize old conversation**: Messages older than N turns are compressed into a running summary block
4. **Drop assistant reasoning**: Internal chain-of-thought from old turns can be stripped entirely

Each level is applied only if the previous level didn't bring the budget below threshold.

## Token ROI

Not all tokens contribute equally to task completion. The **token ROI** concept:

> Each token loaded into context should contribute more to task completion than the next-best alternative token that could occupy that slot.

This is a mental model for making loading decisions, not a computable metric. Practical implications:

- A 500-line file where you need 3 lines has terrible token ROI. Use search or targeted reads.
- A system prompt paragraph that prevents a common error class has excellent token ROI even if never "used."
- Old conversation turns have declining ROI as they become less relevant to the current step.
- Tool schemas for unused tools have zero ROI but nonzero cost (schema tax).

## Relationship to Implementation

The actual implementation in `tinyagent/context.py` uses simpler heuristics than this model describes:

- Turn counting rather than token counting for compaction triggers
- Fixed truncation limits rather than adaptive thresholds
- No token ROI scoring — the developer makes loading decisions at design time

This formal model is a **reasoning framework**, not a specification. It helps explain *why* the heuristics work and *when* they'll break down. A future version could implement token-level budget tracking, but the current turn-based heuristics are sufficient for sessions under ~30 turns.

## Cross-References

- Context exhaustion failure mode: -> [failure-mode-taxonomy.md](../reference-notes/failure-mode-taxonomy.md)
- React loop context overhead that motivated this model: -> [2026-04-11-pivot-react-loop-to-plan-execute.md](2026-04-11-pivot-react-loop-to-plan-execute.md)
- Schema tax concept: -> [agentic-design-vocabulary.md](../reference-notes/agentic-design-vocabulary.md)
