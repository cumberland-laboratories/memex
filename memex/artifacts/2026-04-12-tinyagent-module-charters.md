---
date: 2026-04-12
depth: medium
tags: [tinyagent, charters, architecture, onboarding, parachute-in]
source-thread: context-budget-economics
source: claude
summary: Module-level charters for tinyagent — ownership, responsibilities, boundaries, and entry points for each module. Designed as a "parachute in" document for someone encountering the codebase cold.
superseded-by: 2026-04-27-charter-*.md (function-level charters with notation)
---

# tinyagent Module Charters (Superseded)

**This artifact is superseded** by function-level charters with full notation (line anchors, access patterns, tripwires, cross-references):
- → [Agent Loop Charter](2026-04-27-charter-agent-loop.md)
- → [Context Budget Charter](2026-04-27-charter-context-budget.md)
- → [Infrastructure Charter](2026-04-27-charter-infrastructure.md)
- → [Tools Charter](2026-04-27-charter-tools.md)

This file is preserved as a historical example of the module-level five-question format. For active development, use the function-level charters above.

*"Parachute in" reference: read a module's charter before reading its code.*

Each charter answers five questions: What does this module own? What does it *not* own? What are its inputs and outputs? Where does it connect to the rest of the system? What should you know before changing it?

---

## `agent.py` — The Loop

**Owns**: the plan-act-observe-reflect cycle. Receives a task, drives it to completion (or escalation), and returns a final response. Owns the iteration counter and termination logic.

**Does not own**: API calls (delegates to `client`), budget decisions (delegates to `context`), tool execution logic (delegates to `tools` registry), or persistence (delegates to `session`).

**Inputs**: a task string (from `__main__`), plus injected `Client`, `ContextManager`, and `Session` instances.

**Outputs**: a final response string. Side effects: tool executions, session save.

**Connections**: imports `client`, `context`, `session`, `tools`. Nothing imports `agent` except `__main__`.

**Before changing**: understand the `_step` method — it's the inner loop. Every iteration goes: snapshot context → call Claude → parse tool_use blocks → execute tools → feed results back → check for loops. The reflect step (loop detection, escalation) is the most stubbed part. Changes here ripple into context budget behavior.

---

## `context.py` — The Budget

**Owns**: what stays in context and what gets evicted. Tracks every message with a priority tier (PINNED / RECENT / HISTORICAL), estimates token counts, triggers compaction when the budget is exceeded. This is the hardest module in the system.

**Does not own**: the content of messages (just tracks them), API formatting (snapshot returns raw dicts), or the decision of *what to say* (that's the agent's job).

**Inputs**: messages via `add(role, content, priority)`. Configuration: model name → budget ceiling.

**Outputs**: `snapshot()` returns an API-ready message list. `system_prompt()` extracts pinned system content.

**Connections**: imported by `agent`. Imports nothing from tinyagent.

**Before changing**: the `_reassign_priorities()` method is called on every `add()` and `snapshot()`. It reclassifies messages: the last N turns stay RECENT, everything older becomes HISTORICAL and is eligible for compaction. The compaction stub (`_build_summary_stub`) is a placeholder — a real implementation calls Claude to summarize. Token estimation (`len // 4`) is crude. See the context-budget-economics thread for the design reasoning.

---

## `client.py` — The Wire

**Owns**: exactly one thing — sending messages to Claude and getting responses back. Handles rate-limit retry with exponential backoff (3 attempts, doubling delay).

**Does not own**: message construction (receives pre-formatted messages), response parsing (returns raw `anthropic.types.Message`), or any application logic.

**Inputs**: messages, tool schemas, system prompt, max_tokens.

**Outputs**: an `anthropic.types.Message` (for `chat`) or an iterator (for `stream_chat`).

**Connections**: imported by `agent`. Imports only the `anthropic` SDK.

**Before changing**: this is intentionally thin. If you're adding logic here, ask whether it belongs in `agent` instead. The only legitimate additions: caching, token counting, request logging, or new API features (e.g., prompt caching headers).

---

## `session.py` — The Tape

**Owns**: session state persistence. Writes JSON files to `.tinyagent-sessions/`. Tracks the message log and tool result history. Provides `save()`, `load()`, `list_sessions()`.

**Does not own**: what goes into messages (the agent decides that), context management (that's `context.py`), or session *strategy* (whether to resume, start fresh, etc. — that's `__main__`).

**Inputs**: messages and tool results appended via `record_message()` and `record_tool_result()`.

**Outputs**: JSON files on disk. `load()` reconstructs a Session from a file.

**Connections**: imported by `agent`. Imports nothing from tinyagent.

**Before changing**: session files are designed to be inspectable with `cat` and `jq`. Don't add binary formats. If you need richer queries, consider JSONL (one line per turn) — there's an inbox item about this.

---

## `tools/__init__.py` — The Registry

**Owns**: the mapping from tool names to handlers and schemas. Tools self-register on import. The registry exports schemas in Anthropic API format and dispatches execution by name.

**Does not own**: tool implementations (each lives in its own file), tool selection (the model chooses), or tool result handling (the agent manages that).

**Inputs**: `register(name, description, parameters, handler)` called at import time by each tool module.

**Outputs**: `get_schemas()` returns a list of tool definitions. `execute(name, args)` calls the handler and returns a string.

**Connections**: imported by `agent` (for schemas and execution). Each tool file imports `registry` to self-register.

**Before changing**: adding a tool means creating a new file in `tools/` that calls `registry.register(...)` at module level, then adding an import line to `load_all_tools()`. That's it. Remember the schema tax — each tool costs ~100-200 tokens of context on every turn.

---

## `__main__.py` — The Wiring Harness

**Owns**: CLI parsing, environment loading, and wiring the other modules together. Creates the `Client`, `ContextManager`, `Session`, and `Agent`, then calls `agent.run()` or `agent.resume()`.

**Does not own**: any application logic. If you're adding behavior here, it probably belongs in `agent`.

**Inputs**: command-line arguments and environment variables (ANTHROPIC_API_KEY).

**Outputs**: prints the agent's final response to stdout.

**Before changing**: this is the only module that imports everything. Keep it thin — it's a composition root, not a controller.

---

## Individual Tools (`tools/read_file.py`, `write_file.py`, `run_command.py`, `list_files.py`)

Each tool file owns one capability boundary crossing:

| Tool | Boundary | Safety | Key constraint |
|------|----------|--------|----------------|
| `read_file` | disk → context | Truncates at 50K chars | Large files blow the budget |
| `write_file` | context → disk | cwd containment check | Refuses paths outside working dir |
| `run_command` | context → shell | Timeout (30s default) | No sandboxing — see subprocess-sandboxing thread |
| `list_files` | disk → context | None | Glob patterns only, no recursion guard |

**Before changing any tool**: each tool returns a *string*. The model parses what it needs. Don't return structured data — it complicates the protocol for no gain.
