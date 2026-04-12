---
last-touched: 2026-04-12
category: reference
hits: 0
tags: [optimization, tinyagent, client, anthropic-api]
---

# Prompt Caching Tradeoffs

## Summary

Anthropic's prompt caching allows the system prompt and tool schemas to be cached across turns, saving input tokens on every request. For tinyagent, this would save roughly 2K tokens per turn on the repetitive prefix. Not implemented; noted as a future optimization in `client.py`.

## How It Works

The Anthropic API supports `cache_control` markers on message blocks. Content before a cache breakpoint is hashed and reused across requests. On a cache hit, those tokens are billed at a reduced rate and skip reprocessing.

## Pro

- The system prompt + tool schemas are identical on every turn — a textbook caching candidate
- At ~2K tokens per turn over a 20-turn session, that is ~40K input tokens saved
- Reduces latency on the prefill phase (cached tokens process faster)

## Con

- Any change to cached content invalidates the cache — adding a tool, tweaking the system prompt, or changing schema descriptions forces a full re-send
- Adds complexity to `client.py`: the `_build_kwargs` method would need to inject `cache_control` blocks at the right positions
- Cache has a TTL (currently 5 minutes on Anthropic's side); long pauses between turns lose the benefit

## Current Status

Not implemented. The `client.py` wrapper sends the system prompt and tools fresh on every call. This is fine for a design artifact where API cost is not the bottleneck. A production deployment processing hundreds of sessions would want this.

Related: -> [context-manager](../../docs/systems/context-manager.md) (the budget tracker that would benefit most from reduced per-turn overhead).
