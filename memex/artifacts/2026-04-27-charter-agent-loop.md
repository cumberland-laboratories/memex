---
date: 2026-04-27
depth: full
tags: [charter, tinyagent, architecture, agent-loop]
source-thread: context-budget-economics
source: claude
summary: Function-level charter for tinyagent's agentic loop — the plan-act-observe-reflect cycle, iteration control, tool dispatch, and loop detection.
---

# Agent Loop — plan-act-observe-reflect cycle, iteration control, tool dispatch

Last verified: 2026-04-27
Files covered: tinyagent/agent.py (126 lines)

---

## Constants

- `SYSTEM_PROMPT` [L16] — hardcoded system prompt injected as PINNED. Instructs the model to work step by step and not call tools in its final response.

## IterationOutcome [L24]
Enum-like class. Three states: `CONTINUE`, `DONE`, `ESCALATE`.
! No actual enum — just string constants on a plain class. Works but has no type safety.

---

## Agent class [L30]

### __init__(client, context, session, max_iterations=20) [L33]
Wires injected dependencies. No logic.
← __main__.main()
→ stores Client, ContextManager, Session, max_iterations

### run(task) [L40]
Starts a new task. Injects system prompt as PINNED, user task as RECENT, records to session, enters loop.
← __main__.main()
→ ContextManager.add(R/W), Session.record_message(W), _loop()
! System prompt is PINNED — never evicted by context budget. User task is RECENT — eligible for compaction after enough turns.

### resume() [L47]
Resumes from saved session. Re-injects system prompt and replays all saved messages into context.
← __main__.main()
→ ContextManager.add(R/W), Session.messages(R), _loop()
! Replays messages without priority — they get default RECENT, then _reassign_priorities() demotes old ones to HISTORICAL. This means a long resumed session may immediately trigger compaction.

### _loop() [L54]
Core iteration loop. Calls _step() up to max_iterations times. Returns on DONE or ESCALATE. Saves session on every exit path.
← run(), resume()
→ _step(), Session.save(W)
! Escalation is stubbed — returns a string, doesn't actually ask the user. See → [Ask vs Act Thresholds](../../memex/active-threads/ask-vs-act-thresholds.md)
! Session.save() called on DONE, ESCALATE, and max-iterations. Three exit paths, all save.

### _step(iteration) [L69]
One plan-act-observe-reflect cycle. Snapshots context, calls Claude, parses response into text and tool_use blocks, executes tools, feeds results back, checks for loops.
← _loop()
→ ContextManager.snapshot(R), Client.chat(external API), registry.get_schemas(R), ContextManager.system_prompt(R), ContextManager.add(W), Session.record_message(W), _execute_tool_calls(), _detect_loop()
! Response parsing assumes block.type is either "text" or "tool_use" — no handling for other block types (e.g., thinking blocks if extended thinking were enabled).
! If no tool_calls → DONE. This is the termination signal: the model's decision to stop calling tools ends the loop.

### _execute_tool_calls(tool_calls) [L107]
Executes each tool call through the registry. Catches exceptions per-tool and converts to error strings.
← _step()
→ registry.execute(R), Session.record_tool_result(W)
! Errors become strings, not exceptions — the model sees the error in its next turn and can react. This is intentional: → [Error Recovery as Design](../../memex/active-threads/error-recovery-as-design.md)
! Tool results are recorded to session individually, not batched.

### _detect_loop() [L119]
Stub loop detection: if last 3 tool calls match the previous 3 (by name + serialized input), flags escalation.
← _step()
→ Session.tool_results(R)
! This is deliberately naive — a real implementation needs semantic comparison, not exact match. See → [Agentic Loop Failure Modes](../../memex/active-threads/agentic-loop-failure-modes.md)
! Uses lambda inside method body for signature comparison — works but not testable in isolation.
