# Context-Budget Manager

How `context.py` manages the finite context window across an unbounded agentic loop.

## The Problem

Claude's context window is large (200K tokens) but not infinite. An agentic loop accumulates messages without bound: every tool call adds input and output, every file read dumps content into the conversation. A 10-iteration session can easily consume 50K+ tokens. A 50-iteration session will blow the budget.

The context manager is the most important module in tinyagent. Everything else is plumbing.

## Three Priority Tiers

Every message tracked by the `ContextManager` belongs to one of three tiers:

| Tier | Contents | Policy |
|------|----------|--------|
| **PINNED** | System prompt, tool schemas | Always loaded, never evicted |
| **RECENT** | Last N turns (default: 6) | Kept verbatim — high value, recent decisions |
| **HISTORICAL** | Older turns | Compressible — can be summarized or dropped |

Priority is dynamic. A RECENT message becomes HISTORICAL once enough newer turns push it past the sliding window. The `_reassign_priorities()` method handles reclassification on every `add()` and `snapshot()` call.

## Budget Tracking

The total budget is `MODEL_MAX_TOKENS - OUTPUT_RESERVE` (200K - 8192 = ~192K tokens).

Token estimation is currently `len(content) // 4` — a crude heuristic. A production system would use `anthropic.count_tokens()` or a local tokenizer. This is noted as a TODO in the source.

Every call to `add()` checks `_total_tokens() > budget`. If over budget, `compact()` fires automatically.

## Compaction

When the budget is exceeded:

1. **Reassign priorities** — slide the RECENT window so only the last N turns stay RECENT
2. **Collect HISTORICAL messages** — everything older than the RECENT window
3. **Summarize** — build a summary of the historical messages (currently a stub; a real implementation calls Claude to preserve key decisions, file paths, and constraints)
4. **Replace** — drop all HISTORICAL messages, insert the summary message after the PINNED block

This is the summarize-and-drop strategy. Tool results in HISTORICAL messages are the first to lose detail — assistant reasoning about those results is more valuable than the raw output.

## Key Methods

- `add(role, content, priority)` — append a message, auto-compact if over budget
- `snapshot()` — return the current message list formatted for the Anthropic API, already fitted to budget
- `system_prompt()` — extract PINNED system messages (sent separately via the API's `system` parameter)
- `compact()` — manually trigger compaction
- `total_tokens_used()` — current estimated token count

## What the Stub Misses

The current implementation stubs the summarization step — it produces a placeholder string instead of calling Claude. A real system needs to weigh:

- Cost of re-summarization (an API call per compaction) vs. lost detail
- Which tool results are "load-bearing" (the test output that proved the fix works)
- Whether the user's goal has shifted mid-session
- Graceful degradation when even the summary exceeds budget

These tradeoffs are tracked in -> [history-compaction-strategies](../../memex/threads/history-compaction-strategies.md).
