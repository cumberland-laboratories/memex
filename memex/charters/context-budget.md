---
date: 2026-04-27
depth: full
tags: [charter, tinyagent, architecture, context-budget]
source-thread: context-budget-economics
source: claude
summary: Function-level charter for tinyagent's context budget manager — priority tiers, token tracking, compaction, and the snapshot API that feeds the agentic loop.
---

# Context Budget — priority tiers, token tracking, compaction, snapshot

Last verified: 2026-04-27
Files covered: tinyagent/context.py (132 lines)

---

## Constants

- `MODEL_MAX_TOKENS` — dict mapping model names to max context. Currently only claude-sonnet-4-20250514 and claude-haiku-4-20250414 at 200K.
- `DEFAULT_MAX_TOKENS` — 200,000. Fallback if model not in dict.
- `OUTPUT_RESERVE` — 8,192 tokens reserved for model output. Subtracted from budget.
- `RECENT_TURN_COUNT` — 6 turns kept as RECENT before demotion to HISTORICAL.

## Priority (IntEnum)
Three tiers: PINNED (0), RECENT (1), HISTORICAL (2). IntEnum so tiers sort naturally.
← agent.py uses Priority.PINNED and Priority.RECENT when adding messages
! PINNED messages are never evicted. If the system prompt + tool schemas exceed the budget, the system is broken — no runtime check for this.

## TrackedMessage (dataclass)
Fields: role, content, priority, token_estimate (default 0), turn_index (default 0).
! token_estimate uses chars/4 heuristic — see _estimate_tokens(). Production needs anthropic.count_tokens(). → [Context Budget Economics](../active-threads/context-budget-economics.md)

---

## ContextManager class

### __init__(model="claude-sonnet-4-20250514")
Sets budget = model max tokens minus output reserve. Initializes empty message list and turn counter.
← __main__.main()
! Budget is calculated once at init. No mid-session adjustment if model changes.

### add(role, content, priority=RECENT)
Appends a TrackedMessage. Auto-triggers compact() if total tokens exceed budget.
← Agent.run(W), Agent.resume(W), Agent._step(W)
→ _estimate_tokens(R), compact()
! Every add() checks budget — compaction can happen on any message insertion, not just at explicit checkpoints. This means a large tool result can trigger compaction mid-step.

### compact()
Summarizes HISTORICAL messages to free budget. Reassigns priorities first, collects all HISTORICAL messages, replaces them with a summary stub, inserts summary after PINNED messages.
← add() (auto-triggered)
→ _reassign_priorities(), _build_summary_stub()
! STUB — _build_summary_stub() returns a placeholder string, not an actual Claude-powered summary. A real implementation calls Claude to summarize, preserving key decisions, file paths, and user constraints. → [Context Budget Economics](../active-threads/context-budget-economics.md)
! Summary is inserted at position after all PINNED messages. If PINNED order matters, this preserves it.
! After compaction, the summary itself is marked HISTORICAL — meaning it can be re-compacted on the next cycle. This is intentional (summaries of summaries) but lossy.

### snapshot()
Returns messages formatted for Anthropic API — list of {role, content} dicts, excluding system messages. Calls _reassign_priorities() first to ensure correct tier classification.
← Agent._step(R)
! Excludes role="system" — system prompt is passed separately via system_prompt(). If a non-system PINNED message existed, it would be included here.

### system_prompt()
Extracts content from PINNED system messages, joins with double newline.
← Agent._step(R)
! Returns None if no system messages — Client._build_kwargs() will omit the system parameter entirely.

### total_tokens_used()
Public accessor for _total_tokens(). No side effects.

### _reassign_priorities()
Reclassifies non-PINNED messages: last RECENT_TURN_COUNT stay RECENT, everything older becomes HISTORICAL.
← compact(), snapshot()
! Called on both compact() and snapshot() — double-called on the compact path (compact calls it, then add's next snapshot call will call it again). Idempotent, so this is safe but wasteful.
! Operates on count of non-PINNED messages, not on turn_index. This means PINNED messages don't affect the recency window.

### _estimate_tokens(content)
Static method. Returns len(str(content)) // 4.
! chars/4 is crude — overestimates for code (short tokens), underestimates for natural language with long words. Production needs anthropic.count_tokens(). → [Context Budget Economics](../active-threads/context-budget-economics.md)

### _build_summary_stub(messages)
Static method. Placeholder: returns "[Compacted: N messages (role counts) summarized...]".
← compact()
! This is the most important stub in the codebase. The quality of compaction determines whether the agent loses context or preserves it. Replacing this with a real Claude call is the single highest-impact improvement. → [Context Budget Economics](../active-threads/context-budget-economics.md)
