---
last-touched: 2026-04-12
category: design
hits: 1
tags: [tools, schema, ergonomics, dx]
---

# Tool Schema Ergonomics

## Summary

A tool definition isn't just an API contract — it's a prompt. The model reads every tool schema on every turn, and the quality of that schema directly determines whether the model calls the tool correctly. Bad names, vague descriptions, and over-complex parameter types cause hallucinated arguments and wasted turns. Tool ergonomics is a first-class design concern.

## Naming Conventions

Good: `verb_noun` — `read_file`, `run_command`, `list_directory`. The model can infer behavior from the name alone.

Bad: `do_thing`, `helper`, `process`, `handle_request`. These force the model to rely entirely on the description, which it may misread or skip under token pressure.

Worse: `util_v2_final`, `_internal_exec`. The model will still try to call these. Naming debt is immediate, not deferred.

## Descriptions Are Load-Bearing

The description field is read every single turn. It's not documentation for humans — it's an instruction for the model. Be precise. Mention edge cases. State what the tool does NOT do. A description like "Reads a file" is worse than "Reads a file from the local filesystem. Returns the file contents as a string. Returns an error if the file does not exist or is not readable. Binary files are not supported."

## Parameter Design

- **Prefer flat schemas.** Strings, numbers, booleans, simple arrays. The model handles these reliably.
- **Avoid deep nesting.** `{"options": {"format": {"type": "json", "indent": 2}}}` — models hallucinate structure at depth > 2.
- **Required vs optional matters.** If a param has a sensible default, mark it optional and state the default in the description. Don't make the model guess.
- **Examples in descriptions** dramatically improve first-call accuracy. `"pattern: a glob pattern (e.g., '*.py', 'src/**/*.ts')"` is worth more than a paragraph of explanation.

## The Schema Tax

Every tool definition consumes tokens on every turn. Ten tools with rich schemas can eat 2,000+ tokens before the conversation even starts. This is the schema tax — it's permanent, it compounds, and it trades directly against context available for actual work. This is why tool grain size matters: each tool you add has a recurring cost, not a one-time cost.

With tinyagent's three tools (`read_file`, `write_file`, `run_command`), the schema tax is ~400 tokens. Manageable. But a system with 30 tools can lose 10-15% of its context window to schema alone — before a single message.

## Open Questions

- Should tool descriptions be dynamically shortened after the first few turns (the model has "learned" them)?
- Is there a sweet spot for description length — detailed enough to prevent errors, short enough to minimize tax?

## Connections

-> [Grain Size](./tool-grain-size.md) — schema tax as the economic argument for fewer, coarser tools
-> [Tool Protocol Decision Record](../artifacts/2026-04-11-tool-protocol-decision-record.md) — formal rationale for the schema choices
-> [Tool Registry](../../tinyagent/tools/__init__.py) — where tool schemas are defined in code
