---
last-touched: 2026-04-12
category: design
hits: 4
tags: [context, budget, token-economics, design]
---

# Context Budget Economics

## Summary

Every token loaded into context has an opportunity cost — it displaces something else you could have loaded. The context-budget model decomposes the window into reserves, pinned content, and a discretionary budget that the agent must allocate wisely. Tinyagent's `context.py` implements this decomposition and uses a recency-weighted relevance heuristic to make allocation decisions. This thread captures the core tradeoff and the open questions around compaction strategy.

## The Budget Model

The usable context window is not `max_tokens`. It decomposes:

    effective_budget = max_tokens - output_reserve - pinned_cost
    pinned_cost      = system_prompt + tool_schemas + session_header

Everything left is **discretionary budget** — the space the agent can fill with conversation history, file contents, and retrieved context. On Claude with 200k tokens, pinned cost runs ~3-5k, output reserve ~4k. That leaves ~190k discretionary. Sounds generous. It isn't.

## Discretionary Allocation

Three consumers compete for discretionary tokens:

1. **Recent conversation** — the last N turns. Dropping these breaks coherence.
2. **File contents** — tool results from `read_file`. A single large file can eat 20k tokens.
3. **Retrieved context** — Memex threads, docs, anything the agent pulls in for reference.

The naive approach (keep everything) works until it doesn't — and when it fails, it fails mid-task with no graceful recovery. You need a policy.

## The Heuristic: Recency-Weighted Relevance

**Recent tokens are worth more than old tokens of equal relevance.** A file read from 2 turns ago matters more than one from 15 turns ago, even if both are "relevant." The weighting is exponential decay — each turn halves the retention priority of old content.

This isn't perfect. Sometimes the first file read is the most important one. But as a default policy it prevents context exhaustion on long sessions, which is the more common failure mode.

## The Compaction Decision

When budget pressure hits, three options:

- **Summarize** — compress old messages into a synopsis. Lossy but retains signal.
- **Drop** — remove low-priority items entirely. Lossless for what remains.
- **Page out** — write to disk, load back on demand. Zero loss but adds a tool call.

## Open Questions

- Is it better to summarize 10 old messages or drop the 3 least-relevant tool results? The answer probably depends on task type, but we don't have a classifier for that yet.

## Connections

→ [Formal Model](../artifacts/2026-04-11-context-budget-formal-model.md) — the math behind the decay curves and allocation policy
→ [Implementation](../../tinyagent/context.py) — where this lives in code
→ [Session Continuity](session-continuity-without-memory.md) — context loading is the mechanism for continuity
→ [History Compaction](../threads/history-compaction-strategies.md) — detailed compaction strategies
