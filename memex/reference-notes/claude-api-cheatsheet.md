---
last-touched: 2026-04-11
category: reference
tags: [claude-api, anthropic, tool-use, cheatsheet, quick-reference]
---

# Claude API Cheatsheet

Practical quick reference for the Anthropic Claude Messages API. Covers the patterns used in tinyagent and common gotchas.

## Basic Chat Completion

```python
import anthropic

client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=4096,
    system="You are a helpful assistant.",
    messages=[
        {"role": "user", "content": "Hello"}
    ]
)
print(response.content[0].text)
```

## Model Names

| Model | ID |
|-------|----|
| Claude Sonnet | `claude-sonnet-4-20250514` |
| Claude Opus | `claude-opus-4-20250514` |

## System Prompts

The `system` parameter is a top-level field, **not** a message role. Do not put `{"role": "system", ...}` in the messages array — the API will reject it.

## Tool Use

```python
tools = [{
    "name": "read_file",
    "description": "Read the contents of a file",
    "input_schema": {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "File path to read"}
        },
        "required": ["path"]
    }
}]

response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=4096,
    tools=tools,
    tool_choice={"type": "auto"},  # or "any" to force tool use, or {"type": "tool", "name": "read_file"}
    messages=[{"role": "user", "content": "Read foo.py"}]
)
```

When the response contains a `tool_use` content block, you **must** follow it with a `tool_result`:

```python
# response.content may contain: [TextBlock(...), ToolUseBlock(id="toolu_123", name="read_file", input={...})]
# After executing the tool:
messages.append({"role": "assistant", "content": response.content})
messages.append({"role": "user", "content": [
    {"type": "tool_result", "tool_use_id": "toolu_123", "content": "file contents here"}
]})
```

## Streaming

```python
with client.messages.stream(
    model="claude-sonnet-4-20250514",
    max_tokens=4096,
    messages=[{"role": "user", "content": "Hello"}]
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
```

## Token Counting

Available in the response's `usage` field:

```python
response.usage.input_tokens   # tokens consumed by messages + system + tools
response.usage.output_tokens  # tokens generated in the response
```

Use these to track B_conversation and implement compaction triggers. See -> [context-budget-formal-model.md](../artifacts/2026-04-11-context-budget-formal-model.md).

## Rate Limits and Retries

The SDK handles retries automatically for 429 (rate limit) and 529 (overloaded) responses. To customize:

```python
client = anthropic.Anthropic(max_retries=3)  # default is 2
```

For manual retry logic, check `response.status_code` and respect the `retry-after` header.

## Common Gotchas

1. **tool_use must be followed by tool_result** — if the assistant response contains a `tool_use` block, the next message must include a matching `tool_result`. Omitting it causes an API error.
2. **system is not a message role** — use the top-level `system` parameter, not a message with `role: "system"`.
3. **content is a list** — `response.content` is always a list of content blocks, even for simple text responses. Access `response.content[0].text` for the text.
4. **tool_use_id must match** — the `tool_use_id` in `tool_result` must exactly match the `id` from the `tool_use` block.
5. **max_tokens is required** — unlike some APIs, this field is mandatory.
6. **Messages must alternate roles** — user, assistant, user, assistant. Multiple consecutive messages of the same role must be consolidated.
