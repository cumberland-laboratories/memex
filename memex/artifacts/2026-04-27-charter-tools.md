---
date: 2026-04-27
depth: full
tags: [charter, tinyagent, architecture, tools]
source-thread: context-budget-economics
source: claude
summary: Function-level charter for tinyagent's tool system — registry, schema export, dispatch, and all four built-in tools with their boundary crossings and safety constraints.
---

# Tools — registry, schema export, dispatch, built-in tools

Last verified: 2026-04-27
Files covered: tinyagent/tools/__init__.py (43 lines), tinyagent/tools/read_file.py (40 lines), tinyagent/tools/write_file.py (42 lines), tinyagent/tools/run_command.py (50 lines), tinyagent/tools/list_files.py (50 lines)

---

## tools/__init__.py — The Registry

### _ToolRegistry class [L10]

#### register(name, description, parameters, handler) [L14]
Registers a tool. Raises ValueError on duplicate name.
← Each tool module at import time (self-registration)
! Registration happens at module import, triggered by load_all_tools() [L39]. Adding a tool means: create file, call registry.register(), add import to load_all_tools().

#### get_schemas() [L22]
Returns tool definitions in Anthropic API format: [{name, description, input_schema}].
← Agent._step(R) — called every iteration to pass schemas to Claude
! Schema tax: each tool costs ~100-200 tokens of context on every turn. 4 tools ≈ 400-800 tokens per iteration. → [Tool Schema Ergonomics](../../memex/active-threads/tool-schema-ergonomics.md)

#### execute(name, args) [L27]
Dispatches to handler by name. Raises KeyError on unknown tool.
← Agent._execute_tool_calls(R)
! The handler must return a string. All built-in tools do. If a handler raises, the caller (Agent._execute_tool_calls) catches and converts to error string.

#### list_tools() [L32]
Returns list of registered tool names.
← (not currently called in main flow — available for introspection)

### registry [L36]
Module-level singleton instance of _ToolRegistry. All tool modules import this.

### load_all_tools() [L39]
Imports all built-in tool modules to trigger self-registration. Called at module load time [L43].
! Adding a new tool requires adding its import here. This is the only place that needs to change besides the new tool file itself. → [Adding a Tool](../../memex/procedures/adding-a-tool.md)
! Called at import time — not lazy. All tools are registered when tinyagent.tools is first imported.

---

## Built-in Tools — Boundary Crossings

Each tool crosses exactly one I/O boundary the model cannot reach on its own.

| Tool | File | Boundary | Safety | Key constraint |
|------|------|----------|--------|----------------|
| `read_file` | read_file.py | disk → context | Truncates at 50K chars | Large files blow the context budget |
| `write_file` | write_file.py | context → disk | cwd containment check | Refuses paths outside working directory |
| `run_command` | run_command.py | context → shell | Timeout (30s default) | No sandboxing — most dangerous tool |
| `list_files` | list_files.py | disk → context | Truncates at 200 results | No recursion guard on deep trees |

! All tools return strings. The model parses what it needs. Don't return structured data — it complicates the protocol for no gain. → [Tool Grain Size](../../memex/active-threads/tool-grain-size.md)

---

### handle_read_file(args) [L10]
File: tinyagent/tools/read_file.py
Reads file contents. Truncates at MAX_CHARS (50,000 ≈ 12,500 tokens) with truncation notice.
→ Filesystem(R)
! Truncation is hard — no "read from offset" or "read lines N-M". A 100K file returns the first 50K chars and a notice. The model cannot request the rest.
! Uses errors="replace" for encoding — won't crash on binary files but output will be garbage.

### handle_write_file(args) [L9]
File: tinyagent/tools/write_file.py
Writes content to file. Creates parent directories. Refuses paths that resolve outside cwd.
→ Filesystem(W)
! cwd containment: target.relative_to(cwd) raises ValueError for paths outside working directory. This is the only write safety mechanism.
! No backup, no diff, no confirmation. Overwrites silently. → [Ask vs Act Thresholds](../../memex/active-threads/ask-vs-act-thresholds.md) — this is the incident that prompted the ask-vs-act thread.

### handle_run_command(args) [L15]
File: tinyagent/tools/run_command.py
Runs shell command via subprocess. Returns stdout + stderr + exit code.
→ Shell(RW — arbitrary system access)
! MOST DANGEROUS TOOL. shell=True with no sandboxing, no allowlist, no filesystem restrictions, no network controls. Production needs all of these.
! Timeout default 30s. TimeoutExpired returns error string, does not kill child processes (subprocess.run handles SIGTERM but not cleanup of grandchildren).
! stderr is included in output with [stderr] prefix — model sees both streams.

### handle_list_files(args) [L11]
File: tinyagent/tools/list_files.py
Lists files matching glob pattern. Defaults to "**/*" in current directory. Truncates at MAX_RESULTS (200).
→ Filesystem(R)
! Default pattern "**/*" recurses the entire tree. On a large repo this is slow and hits the 200 result cap. The model should use targeted patterns.
! Returns paths relative to cwd when possible. Falls back to absolute paths for files outside cwd (shouldn't happen with normal usage).
