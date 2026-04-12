---
last-touched: 2026-04-11
category: design
hits: 3
tags: [errors, recovery, design, reliability]
---

# Error Recovery as Design

## Summary

Most agent frameworks treat errors as exceptions to catch and suppress. This is backwards. An error is information — often the most useful signal the agent receives in a turn. What the agent does *after* an error matters far more than whether it caught the error cleanly. Error recovery is not exception handling; it's a design discipline.

## The Anti-Pattern

```python
try:
    result = tool.execute(args)
except Exception:
    return "Something went wrong. Please try again."
```

This is the worst possible response. The agent has thrown away the signal (what went wrong), defaulted to a generic message (no actionable info for the human), and implicitly suggested retrying (which may fail identically). Three mistakes in three lines.

## Error Taxonomy for Agentic Tools

Not all errors are equal. The agent's response should depend on the *category*, not just the presence of failure:

**Retryable** — rate limit, network timeout, transient server error. Backoff and retry with exponential delay. Cap retries (3 is usually right). Don't retry silently forever — that's the brute-force failure mode.

**Informational** — file not found, permission denied, invalid path. These aren't failures; they're facts about the world. The agent should adjust its plan: try a different path, ask for the correct filename, check permissions.

**Fatal** — invalid API key, model unavailable, quota exhausted. No amount of retrying helps. Stop, explain clearly, suggest a concrete fix ("check your ANTHROPIC_API_KEY environment variable").

**Ambiguous** — partial output, truncated response, tool returned success but the content looks wrong. This is the hardest category. The agent must detect the ambiguity and decide: retry? ask the human? attempt to validate the partial result?

## The Ambiguous Error Problem

A model generates a `write_file` tool call. The tool returns `success`, but only wrote 30% of the intended content (disk full, buffer issue, truncation). The agent sees "success" and moves on. The file is now silently corrupted. This class of error — where the signal says OK but the outcome is wrong — requires validation steps baked into the tool execution path, not just error handling.

## Open Questions

- How should the agent communicate its error-recovery reasoning to the human? Silently retry feels opaque; narrating every retry feels noisy.
- At what retry count does a "retryable" error become effectively fatal?

## Connections

-> [Failure Modes](./agentic-loop-failure-modes.md) — brute-force retry as a named failure mode; error recovery is the countermeasure
-> [Client](../../tinyagent/client.py) — retry logic with exponential backoff lives here
-> [Streaming vs Batched](../threads/streaming-vs-batched-output.md) — streaming complicates error detection for partial responses
