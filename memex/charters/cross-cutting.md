---
date: 2026-04-27
depth: full
tags: [charter, tinyagent, architecture, cross-cutting]
source-thread: context-budget-economics
source: claude
summary: Cross-cutting charter for tinyagent — patterns, invariants, and tripwires that span multiple modules and must be preserved as a unit during any refactor.
---

# Cross-Cutting Concerns — patterns spanning multiple modules

Last verified: 2026-04-27
Files covered: (cross-cutting — spans all modules)

---

## Tool Result Flow (TRIPWIRE)

A tool call traverses four modules in sequence. Changing any link breaks the chain.

```
Agent._step()                    → parses response.content for tool_use blocks
Agent._execute_tool_calls()      → calls registry.execute(name, args) per tool
  registry.execute()             → dispatches to tool handler
  tool handler                   → returns string (ALWAYS a string)
  Agent._execute_tool_calls()    → catches exceptions, converts to error string
  Session.record_tool_result()   → appends to session.tool_results (in-memory)
Agent._step()                    → wraps results as tool_result blocks
ContextManager.add()             → adds as "user" message with Priority.RECENT
```

**What breaks:**
- If a tool handler returns non-string, _execute_tool_calls str()-coerces it [agent.py L115] — works but may produce unreadable output
- If registry.execute raises KeyError (unknown tool), the exception is caught and becomes an error string — the model sees "Error executing..." and can react
- Tool results go to BOTH session (permanent record) AND context (ephemeral, subject to compaction). After compaction, the session has tool results the context has forgotten.

→ see [Agent Loop Charter](agent-loop.md) _execute_tool_calls
→ see [Tools Charter](tools.md) registry.execute

---

## Budget Pressure from Tool Results (TRIPWIRE)

read_file can return up to 50,000 characters (~12,500 tokens). A single large file read can consume >6% of the 200K context window. ContextManager.add() checks budget after every insertion [context.py L58] — a large tool result can trigger compaction mid-step, before the agent has processed the result.

**The danger:** if the agent reads a large file, compaction fires, and the compaction stub (which is a placeholder, not a real summarizer) discards earlier context that the agent needs to complete the task. The agent doesn't know context was lost.

**Files involved:** tools/read_file.py (MAX_CHARS = 50,000), context.py (add, compact), agent.py (_step)

! No mid-turn budget recovery. If a tool result blows the budget, compaction happens but the agent has no signal that context was lost. It continues with degraded state. → [Context Budget Economics](../active-threads/context-budget-economics.md)

---

## Termination Signal

The agentic loop has no explicit "stop" command. Termination is an implicit contract:

1. The system prompt [agent.py L16-21] says: "When done, respond with a summary. Do not call tools in your final response."
2. Agent._step() [agent.py L90-91] checks: if no tool_calls in response → DONE.

**This means:** the model's decision to stop calling tools is the ONLY termination signal. If the system prompt is changed and this instruction is removed, the loop will run until max_iterations. If the model ignores the instruction and keeps calling tools, same result.

! There is no "task complete" tool, no explicit done signal, no progress assessment. The model just... stops calling tools. This works surprisingly well in practice but is fragile to prompt changes.

→ see [Agent Loop Charter](agent-loop.md) _step, SYSTEM_PROMPT
→ see [Agentic Loop Failure Modes](../active-threads/agentic-loop-failure-modes.md)

---

## Session Save Invariant

Agent._loop() [agent.py L54-67] saves the session on ALL three exit paths:
1. `IterationOutcome.DONE` — normal completion
2. `IterationOutcome.ESCALATE` — loop detected or escalation needed
3. Max iterations reached — safety stop

**This must be preserved.** Any refactor that adds a new exit path from _loop() must include session.save(). An unsaved session means lost work — the user cannot resume.

! session.save() writes to disk synchronously. If the process is killed during save(), the JSON file may be corrupt. No atomic write (write-to-temp-then-rename). Low risk in practice but worth noting.

---

## Stub Inventory

Stubs scattered across modules, each tracked by a different Memex thread. Listed here so a refactor doesn't accidentally "complete" a stub without the full design context.

| Stub | Location | Tracked by |
|------|----------|-----------|
| Context compaction | context.py `_build_summary_stub` | → [Context Budget Economics](../active-threads/context-budget-economics.md) |
| Token estimation | context.py `_estimate_tokens` | → [Context Budget Economics](../active-threads/context-budget-economics.md) |
| Loop detection | agent.py `_detect_loop` | → [Agentic Loop Failure Modes](../active-threads/agentic-loop-failure-modes.md) |
| Escalation handling | agent.py `_loop` | → [Ask vs Act Thresholds](../active-threads/ask-vs-act-thresholds.md) |
| Subprocess sandboxing | tools/run_command.py | → [Tool Grain Size](../active-threads/tool-grain-size.md) |

! Do NOT replace a stub with a full implementation without reading the linked thread first. The stub is intentional — the design hasn't been decided yet.
