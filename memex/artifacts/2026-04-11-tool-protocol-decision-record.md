---
date: 2026-04-11
depth: deep
tags: [tool-use, architecture, decision-record, json-schema, protocol]
source-thread: ../active-threads/tool-schema-ergonomics.md
source: agent
summary: Formal decision record for tinyagent's tool protocol. JSON Schema definitions, one file per tool, string returns, no protocol-level composition. Documents alternatives considered and rejected.
---

# Tool Protocol Decision Record

## Context

tinyagent needs a tool protocol that balances three concerns: compatibility with the Claude API's native tool format, developer ergonomics for adding new tools, and runtime simplicity in the agentic loop.

## Decisions

### 1. JSON Schema for Parameter Definitions

Tool parameters are defined using JSON Schema, matching the Claude API's native `input_schema` format exactly. No translation layer, no custom DSL.

**Rationale**: The Claude API already speaks JSON Schema. Any abstraction on top would be a schema tax (see -> [agentic-design-vocabulary.md](../reference-notes/agentic-design-vocabulary.md)) — an additional layer the developer must learn and the runtime must translate, with no added expressiveness.

### 2. One File Per Tool

Each tool lives in its own Python file under `tinyagent/tools/`. The file exports a function and a schema dict. Tool discovery is automatic via directory scanning.

**Rationale**: Monolithic registries create merge conflicts and cognitive overhead. A new tool is a new file — no existing files need modification. The grain size is right: one concept, one file, one test.

### 3. Tool Functions Return Strings

All tool functions return `str`. The model receives the string as a `tool_result` content block and parses what it needs.

**Rationale**: Structured return types (dicts, dataclasses) create a contract the model cannot reliably consume. The model already parses natural language; giving it a formatted string ("File contents of foo.py:\n```...```") is both simpler and more robust than JSON serialization of structured results.

### 4. No Protocol-Level Tool Composition

Tools do not chain or compose at the protocol level. There are no pipelines, no tool-output-as-tool-input wiring. The model composes tools by calling them sequentially through the agentic loop.

**Rationale**: Tool pipelines are premature abstraction. The model is already an excellent compositor — it reads one tool's output and decides what to call next. Hard-wiring composition at the protocol level removes the model's ability to adapt mid-sequence and adds machinery that must be maintained.

## Alternatives Considered

| Alternative | Why rejected |
|------------|-------------|
| **Pydantic models for parameters** | Adds a heavy dependency, requires model → schema compilation, and the Claude API already defines the schema format. Schema tax without payoff. |
| **XML tool definitions** | Non-standard, no ecosystem tooling, would require a custom parser. JSON Schema is the industry default. |
| **Tool pipelines / DAGs** | Premature abstraction. Real-world tool composition patterns weren't known yet. Building pipeline infrastructure before knowing the patterns would cement the wrong abstractions. |
| **Tool result objects with metadata** | Added complexity (latency fields, error codes, pagination) for information the model either doesn't need or can infer from the string result. |

## Consequences

- Adding a new tool requires exactly one new file and zero modifications to existing code
- Tool schemas are directly pasteable into Claude API calls without transformation
- The agentic loop's tool dispatch is a simple function call + string return
- Debugging tool behavior means reading one file, not tracing through a registry

See also: the tool loading implementation in `tinyagent/tools/` and the dispatch logic in `tinyagent/loop.py`.
