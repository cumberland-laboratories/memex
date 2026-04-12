# tinyagent Architecture

A minimal Claude-API coding assistant in pure Python. This is a design artifact demonstrating one way to wire an agentic loop; some paths are stubbed with TODOs.

## Module Map

```
tinyagent/
  __main__.py   CLI entry point — arg parsing, env loading, wiring
  agent.py      The agentic loop: plan -> act -> observe -> reflect
  client.py     Thin Anthropic SDK wrapper with rate-limit retry
  context.py    Context-budget manager (the hard problem)
  session.py    Session persistence to JSON files
  tools/
    __init__.py     Tool registry — register, schema export, dispatch
    read_file.py    Read file contents (relative to cwd)
    write_file.py   Write file contents (cwd-contained)
    list_files.py   List directory contents
    run_command.py  Shell command execution with timeout
```

## Data Flow

1. **User task** arrives via CLI (`python -m tinyagent "your task"`)
2. `__main__.py` builds a `Client`, `ContextManager`, and `Session`, then hands them to an `Agent`
3. `Agent.run()` adds the system prompt (PINNED) and user task (RECENT) to context
4. **Loop** (`_step`): context snapshot goes to Claude via `Client.chat()`, response is parsed for text and `tool_use` blocks
5. **Tool execution**: `agent.py` dispatches each `tool_use` call through the registry, collects string outputs, feeds `tool_result` blocks back as a user message
6. **Reflection**: loop detects repeated tool-call patterns (stub — a real system evaluates progress and decides escalation)
7. **Termination**: loop ends when the model responds with text only (no tool calls) or `max_iterations` is hit
8. **Session save**: final state written to `.tinyagent-sessions/<uuid>.json`

## Design Philosophy

"Make the seams visible." Each module has one job, dependencies flow one direction:

- `__main__` depends on everything (it's the wiring harness)
- `agent` depends on `client`, `context`, `session`, and `tools`
- `client` depends only on the Anthropic SDK
- `context` depends on nothing external
- `session` depends on nothing external
- Each tool file depends only on the registry

No hidden singletons, no circular imports, no framework magic. You can read any module in isolation and understand what it does.

## Setup

- Python 3.10+ (uses `X | Y` union syntax)
- Install dependencies: `pip install -r requirements.txt`
- Copy `.env.example` to `.env` and set `ANTHROPIC_API_KEY`
- The only runtime dependency beyond the standard library is the `anthropic` SDK and `python-dotenv`

## Running

```bash
# New task (bare invocation)
python -m tinyagent "refactor the login module"

# New task (explicit subcommand)
python -m tinyagent run "add error handling to api.py" --model claude-sonnet-4-20250514

# Resume a previous session
python -m tinyagent resume <session-id>
```

Default model is `claude-sonnet-4-20250514`. Default max iterations is 20.

## Key Design Decisions

- **Batched responses** for tool-use turns, streaming for final text output. See -> [streaming-vs-batched-output](../../memex/threads/streaming-vs-batched-output.md).
- **Context budget** is the central constraint. See -> [context-manager](context-manager.md).
- **No tool chaining** — the model composes multi-step actions through the loop, not through tool-to-tool calls.
- **Session persistence** uses plain JSON files. No database, no binary formats. Inspectable with `cat` and `jq`.

## Status

This is a design artifact. The architecture is complete and the modules run, but several subsystems are stubbed:
- Loop detection is a simple 3-turn repetition check
- Context compaction uses a placeholder summary instead of calling Claude
- Token counting uses `len(text) // 4` instead of a proper tokenizer
- No prompt caching, no subprocess sandboxing, no command allowlists

These stubs are documented as TODOs in the source and tracked in Memex threads.
