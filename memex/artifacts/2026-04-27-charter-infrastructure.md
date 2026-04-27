---
date: 2026-04-27
depth: full
tags: [charter, tinyagent, architecture, infrastructure]
source-thread: context-budget-economics
source: claude
summary: Function-level charter for tinyagent's infrastructure — the API client, session persistence, and CLI wiring harness.
---

# Infrastructure — API client, session persistence, CLI entry point

Last verified: 2026-04-27
Files covered: tinyagent/client.py (63 lines), tinyagent/session.py (78 lines), tinyagent/__main__.py (72 lines)

---

## client.py — The Wire

### Constants
- `MAX_RETRIES` [L8] — 3 retry attempts on rate limit.
- `INITIAL_BACKOFF_S` [L9] — 1.0 second initial backoff, doubles each retry.

### Client class [L12]

#### __init__(api_key, model="claude-sonnet-4-20250514") [L15]
Creates anthropic.Anthropic client instance.
← __main__.main()

#### chat(messages, tools=None, system=None, max_tokens=4096) [L19]
Sends a chat request. Returns anthropic.types.Message. Retries on rate limit.
← Agent._step(external API call)
→ _build_kwargs(), _call_with_retry(), anthropic.Anthropic.messages.create(external)
! Returns raw Message object — no parsing. The agent is responsible for interpreting response.content blocks.
! max_tokens=4096 is the output cap, not the context window. Separate from ContextManager's budget.

#### stream_chat(messages, tools=None, system=None, max_tokens=4096) [L31]
Streaming variant. Returns an iterator. Same retry on initial connection.
← (not currently called — reserved for final text output streaming)
→ _build_kwargs(), _call_with_retry(), anthropic.Anthropic.messages.create(external, stream=True)
! Not used in the current agent loop. The loop uses chat() for all turns including the final one.

#### _build_kwargs(messages, tools, system, max_tokens) [L44]
Builds the kwargs dict for messages.create(). Omits tools and system if None.
← chat(), stream_chat()
! Intentionally thin — no prompt caching headers, no token counting, no request logging. These are the legitimate additions if you need to extend this module.

#### _call_with_retry(fn) [L54]
Exponential backoff retry on anthropic.RateLimitError only. Re-raises after MAX_RETRIES.
← chat(), stream_chat()
! Only catches RateLimitError — all other exceptions propagate immediately. This is intentional: API errors (invalid request, auth failure) should not be retried.
! Uses time.sleep() — blocks the thread. Fine for single-agent use; problematic if you ever run multiple agents concurrently.

---

## session.py — The Tape

### Constants
- `SESSIONS_DIR` [L12] — Path(".tinyagent-sessions"). Created on first save.

### Session class [L15]

#### __init__(session_id, messages=None, tool_results=None, metadata=None) [L18]
Initializes with ID, empty message/tool_results lists, and metadata with timestamps.
← Session.new(), Session.load()

#### new() [L31]
Classmethod. Creates a new session with a UUID4 ID.
← __main__.main() for "run" command

#### load(session_id) [L35]
Classmethod. Reads JSON from .tinyagent-sessions/{session_id}.json. Raises FileNotFoundError if missing.
← __main__.main() for "resume" command
→ Filesystem(R)
! No schema validation — trusts the JSON structure. Corrupt files will produce KeyError or TypeError.

#### save() [L43]
Writes session state to JSON file. Creates SESSIONS_DIR if needed. Updates metadata.updated_at.
← Agent._loop(W) on every exit path (DONE, ESCALATE, max iterations)
→ Filesystem(W)
! Uses json.dump with indent=2 and default=str — human-readable, inspectable with cat and jq. No binary formats.
! mkdir(parents=True, exist_ok=True) — safe to call repeatedly.

#### list_sessions() [L55]
Staticmethod. Returns list of {session_id, created_at, message_count} for all .json files in SESSIONS_DIR.
← (not currently called in main flow — available for future session browser)
→ Filesystem(R)
! Silently skips corrupt JSON files (JSONDecodeError, KeyError).

#### record_message(role, content) [L70]
Appends {role, content, timestamp} to messages list. In-memory only until save().
← Agent.run(W), Agent._step(W)

#### record_tool_result(tool_use_id, name, input_args, output) [L74]
Appends {id, name, input, output, timestamp} to tool_results list. In-memory only until save().
← Agent._execute_tool_calls(W)
! output is str()-coerced. Tool handlers already return strings, so this is a safety belt.

---

## __main__.py — The Wiring Harness

### build_parser() [L9]
Creates argparse parser with "run" and "resume" subcommands. Default model: claude-sonnet-4-20250514. Default max_iterations: 20.

### main() [L29]
Entry point. Loads .env, checks ANTHROPIC_API_KEY, parses args, wires Client + ContextManager + Session + Agent, calls run() or resume().
← `python -m tinyagent`
→ Client(W), ContextManager(W), Session.new(W) or Session.load(R), Agent(W), Agent.run() or Agent.resume()
! Bare invocation (no subcommand) is handled: `python -m tinyagent "task"` works the same as `python -m tinyagent run "task"`.
! Imports of tinyagent modules are deferred to after env validation [L51-54] — fail fast on missing API key before loading the SDK.
! This is the only module that imports everything. Keep it thin — it's a composition root, not a controller.
