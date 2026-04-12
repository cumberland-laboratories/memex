---
date: 2026-04-11
depth: deep
tags: [agentic-loop, architecture, decision-record, plan-execute, ooda]
source-thread: ../active-threads/agentic-loop-failure-modes.md
source: agent
summary: Decision record reversing the original OODA-style react loop in favor of plan-then-execute. The react pattern burned context on redundant re-analysis and produced worse plan stability.
---

# Pivot: React Loop to Plan-Execute

## The Original Design

The first agentic loop implementation used a React-style observe-orient-decide-act (OODA) loop. Every iteration:

1. **Observe** the full current state (conversation, file contents, tool results)
2. **Orient** by analyzing what had changed since the last iteration
3. **Decide** the next action based on re-evaluation
4. **Act** by calling a tool or producing output

This was elegant in theory. The model always had fresh situational awareness. It could adapt mid-task if circumstances changed. No stale plans to go wrong.

## Why It Failed

Three problems surfaced during testing:

**Redundant analysis burned context budget.** Every turn included a full re-evaluation preamble. For a 10-step task, the model spent ~30% of its discretionary context re-deriving the same situational picture it had already established. This is the context economics problem described in -> [context-budget-formal-model.md](2026-04-11-context-budget-formal-model.md).

**The model kept "re-discovering" the same plan.** Without a persistent plan artifact, the orient step would independently converge on the same sequence of actions each iteration — but burn tokens doing so. Worse, slight prompt variations caused the re-derived plan to wobble, introducing gratuitous inconsistency.

**Plan drift was worse, not better.** Counter-intuitively, the absence of a persistent plan made drift *harder* to detect. There was no baseline to drift *from*. Each iteration's "plan" was ephemeral, so there was no way to notice that step 7's plan diverged from step 3's plan. The failure mode taxonomy covers this: -> [failure-mode-taxonomy.md](../reference-notes/failure-mode-taxonomy.md).

## The Pivot

Switched to **plan-then-execute**:

1. Generate a numbered plan up front (stored as a message or artifact)
2. Execute steps sequentially, checking off each one
3. Re-plan only on: step failure, unexpected state, or plan completion
4. Re-planning is explicit and produces a new numbered plan

## Tradeoffs

| Property | React loop | Plan-execute |
|----------|-----------|-------------|
| Adaptiveness | High (re-evaluates constantly) | Lower (follows plan until failure) |
| Predictability | Low (plan wobbles each turn) | High (plan is stable artifact) |
| Context cost | High (~30% overhead) | Low (plan generated once) |
| Debuggability | Poor (no persistent plan to inspect) | Good (plan is inspectable) |
| Drift detection | Hard (no baseline) | Easy (compare execution to plan) |

## Lessons

The react loop is the right choice when the environment is genuinely adversarial or rapidly changing (game-playing, real-time systems). For the kind of work tinyagent does — multi-step coding tasks in a relatively stable filesystem — the plan-execute pattern is strictly better. The key insight: **predictability is a feature, not a limitation**, when your environment changes slower than your planning cycle.
