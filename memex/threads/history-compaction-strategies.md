---
last-touched: 2026-04-12
category: reference
hits: 1
tags: [context-management, tinyagent, design-decision]
---

# History Compaction Strategies

## Summary

When the context budget is exceeded, tinyagent must reduce the conversation history to fit. Three strategies were considered; the current implementation uses a combination of summarize-and-drop with selective pruning of tool results. The summarization step itself is currently stubbed — it produces a placeholder rather than calling Claude.

## Strategies Considered

### Sliding Window
Drop the oldest N messages until the budget fits.
- **Pro**: trivial to implement, zero cost (no API call)
- **Con**: loses early context entirely — the original task description, initial constraints, and early reasoning vanish. The model may repeat mistakes or contradict earlier decisions.

### Summarize-and-Drop
Call Claude to summarize the old messages into a single condensed message, then replace the originals.
- **Pro**: preserves meaning — key decisions, file paths, and user constraints survive in compressed form
- **Con**: expensive (an extra API call per compaction), and the summary itself may be lossy. Recursive summarization degrades further.

### Selective Pruning
Drop tool results (raw file contents, command output) but keep assistant reasoning about those results.
- **Pro**: preserves the decision chain — why the model chose a particular approach, what it learned from an error. The reasoning is more valuable than the raw data.
- **Con**: if the model needs to re-read a file, it has lost the content and must call the tool again (costing a turn).

## Current Approach

`context.py` uses **summarize-and-drop** as the primary strategy, with **selective pruning** as a refinement: tool results in HISTORICAL messages are the first candidates for compression. The summary stub currently produces a placeholder string; a real implementation would call Claude with instructions to preserve file paths, key decisions, and user-stated constraints.

## Open Questions

- Should compaction be triggered at 90% budget, or wait until 100%? Early compaction wastes less but runs more often.
- Can we detect "load-bearing" tool results (e.g., test output that proves a fix works) and exempt them from pruning?
- Would a two-tier summary (detailed for recent history, terse for older) balance cost and fidelity?

Related: -> [context-manager](../../docs/systems/context-manager.md) (implementation details).
