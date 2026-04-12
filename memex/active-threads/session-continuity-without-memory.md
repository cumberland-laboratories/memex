---
last-touched: 2026-04-12
category: design
hits: 3
tags: [continuity, session, memex-thesis, statelessness]
---

# Session Continuity Without Memory

## Summary

Language models are stateless — every session starts cold. There is no persistent memory API, no fine-tuning between runs. Yet a well-built agent can feel continuous across sessions: picking up where it left off, knowing the project's state, recalling past decisions. This thread explores how tinyagent achieves that illusion through three layers of external state, and why this connects directly to the Memex architecture.

## The Problem

Session 1 ends. Session 2 begins. The model has zero recollection of session 1. Not degraded recollection — *zero*. Every warm feeling of "the agent remembers me" is actually the agent being handed good notes at startup.

This is not a limitation to work around. It's the fundamental constraint that shapes the entire architecture.

## Three Layers of Continuity

### Layer 1: Session Files on Disk

`tinyagent/session.py` persists session state as JSON: the task, key decisions, files touched, errors encountered. On next launch, the agent loads the last session file and gets a structured summary of what happened. Cheap, local, always available.

### Layer 2: The Memex as External Memory

Active threads, artifacts, and the commit draft are the project's long-term memory. They're not conversation logs — they're curated, compressed knowledge. When the agent opens a session, the Memex threads tell it what the project *is*, not just what happened last time.

### Layer 3: Context Preloading at Session Open

The session-opening procedure loads a specific set of files: constitution, mission, active threads, commit draft. This is the "always-loaded" set — the minimum context for coherent operation. Everything else is navigable on demand.

## The Key Insight

Continuity is not about remembering everything. It's about loading the **right context at the right time**. A model with perfect recall of 1000 sessions but no ability to prioritize would drown in noise. A model with recall of zero sessions but excellent context loading feels smarter.

The Memex's distinction between "always-loaded" and "navigable" content maps directly to the context budget. Always-loaded content is pinned cost. Navigable content is discretionary — pulled in when relevant, dropped when not.

## Open Questions

- Should session files include a "continuation prompt" — a sentence written by the agent at end-of-session, addressed to the next session's agent? Feels useful. Also feels like it could drift into incoherence over many sessions.

## Connections

→ [Context Budget Economics](context-budget-economics.md) — the budget model that governs what gets loaded
→ [Session Implementation](../../tinyagent/session.py) — where layer 1 lives in code
→ [Session Lifecycle Procedure](../../.memex/procedures/session-lifecycle.md) — the procedure that governs context preloading
→ [Prompt Caching Tradeoffs](../threads/prompt-caching-tradeoffs.md) — caching interacts with what stays pinned
→ [Error Recovery as Design](error-recovery-as-design.md) — session files are also a recovery mechanism; if the agent crashes, the session can be resumed
