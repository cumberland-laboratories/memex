---
last-touched: 2026-04-12
category: reference
hits: 1
tags: [ux, tinyagent, client, design-decision]
---

# Streaming vs Batched Output

## Summary

Should tinyagent stream tokens to the user as they arrive, or wait for complete responses? The current decision is a hybrid: batch tool-use turns (where we need the complete response to parse tool calls), stream final text output (where the user benefits from seeing progress). `client.py` already exposes both `chat()` and `stream_chat()` methods to support this.

## Tradeoffs

**Streaming** (token-by-token to stdout):
- Better UX — the user sees progress immediately, the tool feels responsive
- Harder to implement correctly for tool-use turns: tool_use blocks arrive incrementally, and parsing a half-formed JSON `input` field mid-stream is fragile
- Requires event-based processing or chunked accumulation

**Batched** (wait for complete response):
- Simpler implementation — one API call, one parsed response object
- Easier error handling — the full response is available before any action is taken
- Feels sluggish on long responses; the user stares at a blank terminal

## Current Decision

Batch for tool-use turns, stream for final text output. The agent loop in `agent.py` uses `client.chat()` (batched) for all turns. A future pass would switch the final-response turn to `client.stream_chat()` once the loop detects no tool calls will be needed.

This is good enough for a design artifact. A production agent would likely stream everything and accumulate tool_use blocks with a state machine.

## Connections

-> [Error Recovery](../active-threads/error-recovery-as-design.md) — streaming complicates error detection; partial responses are harder to validate mid-stream
-> [Context Budget](../active-threads/context-budget-economics.md) — streaming doesn't change the budget math, but affects when the agent commits tokens to context
