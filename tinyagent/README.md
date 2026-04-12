# tinyagent

A minimal Claude-API coding assistant — a design-quality teaching artifact.

**This is not production code.** It is a skeleton that illustrates the
architecture of an agentic coding loop: context management, tool dispatch,
session persistence, and the plan-act-observe-reflect cycle.

## Setup

```bash
# 1. Set your API key
export ANTHROPIC_API_KEY=sk-ant-...
# or create a .env file in the repo root

# 2. Install dependencies
pip install anthropic python-dotenv

# 3. Run
python -m tinyagent run "create a hello world script"

# 4. Resume a session
python -m tinyagent resume <session-id>
```

## Architecture

```
tinyagent/
  __main__.py    CLI entry point (argparse, env loading)
  client.py      Thin Anthropic SDK wrapper (retry on rate-limit)
  context.py     Context-budget manager (the hard problem)
  agent.py       Agentic loop: plan → act → observe → reflect
  session.py     JSON-file session persistence
  tools/
    __init__.py   Tool registry
    read_file.py  Read a file (with truncation)
    write_file.py Write a file (with safety bounds)
    run_command.py Shell commands (with timeout)
    list_files.py  Glob-based file listing
```

## Design notes

- **Context budget** is the headline concern. See `context.py` for the
  priority-tier approach (pinned > recent > historical/compressible).
- **Tools** are plain functions with JSON Schema metadata. No framework.
- **Sessions** are plain JSON files in `.tinyagent-sessions/`.
- **TODO stubs** point to Memex design threads for open questions.

## Open questions (marked as TODOs in code)

- Token counting: chars/4 heuristic vs. proper tokenizer
- Context compaction: when and how to summarize old messages
- Ask-vs-act threshold: when should the agent ask for clarification?
- Subprocess sandboxing: how to safely run user commands
- Cost model: how to weigh re-summarization cost vs. lost detail
