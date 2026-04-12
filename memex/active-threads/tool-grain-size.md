---
last-touched: 2026-04-11
category: design
hits: 3
tags: [tools, design, grain-size]
---

# Tool Grain Size

## Summary

Tool granularity is a design spectrum with real costs at both extremes. Too fine-grained and you pay call overhead plus schema bloat; too coarse and tools become brittle black boxes the model can't compose. Tinyagent adopts the heuristic: "a tool should do one thing the model cannot do itself." This thread works through the reasoning.

## The Spectrum

From fine to coarse:

- `read_line(file, line_num)` — too fine. Reading a file takes N calls. The model spends tokens on orchestration instead of thinking.
- `read_file(path)` — right. One capability boundary crossed (disk access), result returned whole.
- `read_and_analyze_file(path, question)` — too coarse. The analysis is something the model does *better* in-context than a tool can. You've hidden reasoning inside a tool call where the model can't inspect or redirect it.

The failure mode at each end is different. Too-fine tools cause **loop bloat** — the agent burns turns on mechanical orchestration. Too-coarse tools cause **opacity** — the agent can't see intermediate results, can't change strategy mid-read.

## The Schema Tax

Every tool definition eats ~100-200 tokens of context permanently. It's pinned cost — the model sees every tool schema on every turn. Ten tools: ~1500 tokens. Thirty tools: ~4500 tokens. That's discretionary budget you never get back.

This creates selection pressure: don't register tools you rarely use. Tinyagent ships five tools. That's not laziness; it's a budget decision.

## The Heuristic

**A tool should do one thing that the model cannot do itself.**

The model can: summarize, parse, decide, plan, format, compare, classify.
The model cannot: read files, write files, run shell commands, make HTTP calls.

If a proposed tool duplicates a capability the model already has, it's overhead. If it crosses an I/O boundary the model can't reach, it earns its schema tax.

## Open Questions

- Where does `search_files(pattern)` fall? The model can't search, but returning 50 results creates its own context pressure. Maybe the grain-size heuristic needs a corollary about result size.

## Connections

→ [Tool Protocol Decision Record](../artifacts/2026-04-11-tool-protocol-decision-record.md) — the formal decision on tool schema format
→ [Tool Schema Ergonomics](tool-schema-ergonomics.md) — the model's-eye view of what makes a tool usable
→ [Context Budget Economics](context-budget-economics.md) — schema tax is a budget concern
→ [Design Vocabulary](../reference-notes/agentic-design-vocabulary.md) — grain size as a named concept
→ [Agentic Loop Failure Modes](agentic-loop-failure-modes.md) — too-fine tools cause loop bloat, a cousin of brute-force retry
