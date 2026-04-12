---
last-touched: 2026-04-11
category: reference
tags: [glossary, agentic-loop, vocabulary, design-concepts]
---

# Agentic Design Vocabulary

Named concepts used across tinyagent threads and artifacts. Each definition is canonical — use these terms precisely in threads to avoid reinventing vocabulary.

## Concepts

**Blast radius** — The scope of damage when an agent action goes wrong. A tool that writes one file has small blast radius; a tool that runs arbitrary shell commands has large blast radius. Design tools to minimize blast radius by default. Developed in: -> [tool-schema-ergonomics thread](../active-threads/tool-schema-ergonomics.md).

**Grain size** — The granularity of a tool's operation. "Edit file" is finer-grained than "refactor module." Finer grain gives the model more control but requires more steps. The right grain matches the model's reliable decision-making unit. Developed in: -> [tool-schema-ergonomics thread](../active-threads/tool-schema-ergonomics.md).

**Plan drift** — Gradual divergence between the agent's intended plan and its actual execution. Insidious because each individual step seems reasonable — the drift is only visible in aggregate. Worse in react loops where no persistent plan exists to drift from. Developed in: -> [agentic-loop-failure-modes thread](../active-threads/agentic-loop-failure-modes.md).

**Context exhaustion** — The condition where the conversation has consumed enough of B_discretionary that the agent can no longer load the information it needs to complete the current task. Leads to degraded output quality or outright failure. Developed in: -> [context-budget-economics thread](../active-threads/context-budget-economics.md).

**Tool hallucination** — The model invents a tool that doesn't exist or calls a real tool with fabricated parameters. More common when tool schemas are ambiguous or when the model is under context pressure. Developed in: -> [agentic-loop-failure-modes thread](../active-threads/agentic-loop-failure-modes.md).

**Brute-force retry** — Repeating the same failing action without changing approach. The agent re-runs a command that errored, hoping for a different result. A degenerate loop that wastes context budget. Developed in: -> [agentic-loop-failure-modes thread](../active-threads/agentic-loop-failure-modes.md).

**Recency-weighted relevance** — The heuristic that recent conversation turns are more relevant than older ones. Underpins compaction strategy: older turns are summarized first. Not always true (a requirement stated in turn 1 may be critical in turn 30), but a useful default. Developed in: -> [context-budget-economics thread](../active-threads/context-budget-economics.md).

**Schema tax** — The fixed token cost paid on every API call for tool definitions loaded into the system prompt. Each tool added to the system makes every request more expensive, regardless of whether the tool is used. Motivates keeping the tool set minimal. Developed in: -> [tool-schema-ergonomics thread](../active-threads/tool-schema-ergonomics.md).

**Escalation ladder** — A predefined sequence of increasingly aggressive recovery strategies. When a step fails: retry once, try an alternative approach, re-plan, ask the human. Each rung costs more but handles harder failures. Developed in: -> [agentic-loop-failure-modes thread](../active-threads/agentic-loop-failure-modes.md).

**Token ROI** — The contribution of a token in context toward task completion, relative to the next-best alternative token. A mental model for loading decisions: prefer high-ROI tokens (relevant code, clear instructions) over low-ROI tokens (stale tool results, verbose file contents). Developed in: -> [context-budget-economics thread](../active-threads/context-budget-economics.md). Formalized in: -> [context-budget-formal-model.md](../artifacts/2026-04-11-context-budget-formal-model.md).

**Ask-vs-act threshold** — The judgment call: should the agent act autonomously or ask the human for guidance? Depends on blast radius, confidence, and reversibility. Low blast radius + high confidence = act. High blast radius + low confidence = ask. Developed in: -> [agentic-loop-failure-modes thread](../active-threads/agentic-loop-failure-modes.md).

**Compaction trigger** — The condition (typically B_conversation + B_working > 0.9 * B_discretionary) that initiates context compression. Crossing this threshold means the agent must shed tokens or risk exhaustion. Developed in: -> [context-budget-economics thread](../active-threads/context-budget-economics.md).

**Session continuity** — The property that a new session can resume work as if the previous session never ended. Achieved through persistent plans, thread state, and commit messages. The Memex's core value proposition. Developed across all threads.

**Pinned context** — Content that occupies B_pinned: system prompt, tool schemas, and any always-loaded instructions. Cannot be compacted because it's needed on every request. Must be kept minimal. Developed in: -> [context-budget-economics thread](../active-threads/context-budget-economics.md).

**Discretionary budget** — B_discretionary = B_total - B_reserve - B_pinned. The context space the agent actually gets to use for conversation and working memory. The number that matters for session planning. Developed in: -> [context-budget-economics thread](../active-threads/context-budget-economics.md). Formalized in: -> [context-budget-formal-model.md](../artifacts/2026-04-11-context-budget-formal-model.md).
