# Mission

## What tinyagent is

A minimal coding assistant that demonstrates agentic design patterns in pure Python. No frameworks, no dependencies beyond the Anthropic SDK and stdlib. One file you can read top to bottom in twenty minutes.

## Why it exists

Most agentic coding tools hide their architecture behind layers of abstraction. tinyagent exists to make architectural decisions visible and debatable. Every design choice — context management, tool dispatch, error recovery — is surface-level, not buried in a framework.

It is a **design artifact and teaching vehicle**, not a production tool. If you're using it to ship code, you've missed the point. If you're using it to argue about how agents should work, you're in the right place.

## Scope boundaries

**In scope:**
- Single-session task execution
- File operations (read, write, patch)
- Shell command execution with confirmation
- Context budget tracking and compression
- Tool protocol design (schema, dispatch, error shapes)

**Out of scope:**
- Multi-agent orchestration
- Persistence across tasks (the Memex handles that layer)
- Retrieval-augmented generation or vector search
- Production reliability guarantees (retry, circuit-breaking)
- GUI or web interface

The boundary is intentional: tinyagent handles one task in one session. Everything that persists across sessions lives in the Memex, not in tinyagent.
