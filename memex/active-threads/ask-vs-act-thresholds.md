---
last-touched: 2026-04-12
category: design
hits: 2
tags: [autonomy, thresholds, safety, ux]
---

# Ask vs Act Thresholds

## Summary

When should an agentic tool act on its own, and when should it stop and ask? The answer isn't a binary — it's a gradient shaped by reversibility, blast radius, and authorization scope. Getting this wrong in either direction kills the tool: too cautious and it's a chatbot with extra steps; too autonomous and it's a liability.

## The Reversibility Principle

If an action is easily undone, bias toward acting. If it's hard or impossible to reverse, ask. This is the single strongest heuristic. A local file edit is trivially reversible (undo, git checkout). A `git push --force` to main is not. Deleting files outside the working tree might be unrecoverable.

## Blast Radius

Think in concentric circles of impact:

- **Local file in working dir** — low blast radius. Act.
- **File outside working dir** — medium. Confirm first.
- **Git commit** — medium (revertable, but touches shared history). Act and report.
- **Git push** — high. Propose and wait.
- **Delete / overwrite without backup** — very high. Refuse without explicit instruction.

## Authorization Scope

Approval for one action does not generalize. "Push this branch" does not mean "push any branch anytime." Each grant of authority is scoped to the specific action requested. The agent must not cache permissions across turns or across sessions. This is where most autonomy bugs live — the agent infers a standing order from a one-time instruction.

## The Escalation Ladder

1. **Act silently** — trivial, reversible, within scope (e.g., reading a file)
2. **Act and report** — low-risk but the human should know (e.g., writing a file in the working dir)
3. **Propose and wait** — meaningful consequences, needs explicit approval
4. **Refuse and explain** — destructive, out of scope, or ambiguous intent

## Concrete Example in tinyagent

- `read_file` — always act (step 1). No side effects.
- `write_file` — act if path is inside the working directory (step 2). Ask if outside it (step 3).
- `run_command` — act for read-only commands like `ls`, `cat` (step 1-2). Ask for anything that modifies state: `rm`, `mv`, `git push` (step 3). Refuse `rm -rf /` (step 4).

The reflect step in the agent loop is where this decision actually lives. Before executing a tool call, the agent checks the action against the escalation ladder. This is not a filter bolted on after — it's part of the loop's core logic.

## Open Questions

- Should the agent remember per-session grants? ("You said I could push to `dev`" — valid for this session only, or just that one push?)
- How do you handle compound actions where individual steps are safe but the sequence is dangerous?

## Connections

-> [Agent Loop](./agentic-loop-failure-modes.md) — infinite delegation as a failure mode when ask/act boundary is unclear
-> [Implementation](../../tinyagent/agent.py) — the reflect step where escalation decisions are made
-> [Subprocess Sandboxing](../threads/subprocess-sandboxing-notes.md) — sandboxing deferred; ask-vs-act is the interim mitigation
