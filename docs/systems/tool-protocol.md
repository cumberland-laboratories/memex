# Tool Protocol

How tools work in tinyagent: definition, registration, execution, and safety.

## Tool Definition

A tool is four things: a name, a description, a JSON Schema for its parameters, and a handler function. No classes, no inheritance. The handler takes a `dict[str, Any]` and returns a `str`.

```python
def handle_read_file(args: dict[str, Any]) -> str:
    ...
    return file_contents
```

String-in, string-out. The model sees text, produces text. No structured output from tools.

## Schema Format

Tool schemas match the Claude API native `tool_use` format:

```json
{
  "name": "read_file",
  "description": "Read the contents of a file.",
  "input_schema": {
    "type": "object",
    "properties": {
      "path": {"type": "string", "description": "File path relative to cwd."}
    },
    "required": ["path"]
  }
}
```

The `input_schema` is standard JSON Schema. The registry's `get_schemas()` method returns these for every registered tool, and `agent.py` passes them directly to `Client.chat()`.

## Registration

`tools/__init__.py` holds a singleton `_ToolRegistry`. Each tool module calls `registry.register()` at import time — self-registration. The `load_all_tools()` function imports all built-in modules to trigger registration.

One file per tool. To add a tool: create `tools/my_tool.py`, define the handler, call `registry.register()`, and add the import to `load_all_tools()`.

## Execution

When Claude returns `tool_use` blocks in its response, `agent.py` handles them:

1. Parse each `tool_use` block for `id`, `name`, and `input`
2. Call `registry.execute(name, input)` which dispatches to the registered handler
3. Wrap the string output in a `tool_result` block with the matching `tool_use_id`
4. Feed the results back as a user message for the next turn

Errors in tool execution are caught and returned as error strings — the model sees the error and can adjust. Tools never raise into the loop.

## Built-in Tools

| Tool | File | Purpose |
|------|------|---------|
| `read_file` | `read_file.py` | Read file contents by path |
| `write_file` | `write_file.py` | Write content to a file |
| `list_files` | `list_files.py` | List directory contents |
| `run_command` | `run_command.py` | Execute shell commands |

## Safety

**write_file**: Resolves the target path and checks `target.relative_to(cwd)`. Refuses writes outside the working directory. Creates parent directories as needed.

**run_command**: Executes via `subprocess.run()` with `shell=True` and a configurable timeout (default 30s). Currently no sandboxing beyond the timeout — see -> [subprocess-sandboxing-notes](../../memex/threads/subprocess-sandboxing-notes.md) for the deferred plan.

## Design Decision: No Tool Chaining

Tools do not call other tools. The model composes multi-step workflows through the loop: read a file, think about it, write a modified version, run tests. This keeps each tool simple and makes the decision trace legible in the session log.
