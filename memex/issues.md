# Known Issues & Fragilities

## 1. Context explosion on large file reads

When a tool returns a large file (>500 lines), it gets stuffed into context verbatim. No truncation, no summarization. One careless `read_file("package-lock.json")` and the budget is gone. Need a content-aware truncation strategy that preserves the useful parts — but "useful" is task-dependent, which makes this hard.

## ~~2. No retry or backoff for rate limits~~ (resolved)

~~The Anthropic SDK throws on 429s and tinyagent just... stops.~~ Fixed in `client.py`: `_call_with_retry` implements exponential backoff with jitter, 3 retries on `RateLimitError`. Resolved 2026-04-11.

## 3. No graceful degradation when context budget exceeded mid-turn

If the agent exceeds its context budget in the middle of a multi-step plan, it has no mechanism to compress and continue. It either truncates brutally (losing plan state) or errors out. The right answer is probably a checkpoint-and-compress cycle, but that introduces its own complexity around what state to preserve.

## 4. Tool dispatch is not concurrent-safe

If two tool calls reference the same file (e.g., read then write in a batch), there's no ordering guarantee and no lock. In practice the API returns tool calls sequentially, but nothing in the protocol enforces that, and if we ever batch tool execution this becomes a real race condition.
