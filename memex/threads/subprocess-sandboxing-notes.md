---
last-touched: 2026-04-12
category: reference
hits: 0
tags: [security, tinyagent, tools, run-command]
---

# Subprocess Sandboxing Notes

## Summary

The `run_command` tool executes shell commands via `subprocess.run()` with `shell=True` and a timeout, but no sandboxing. This is the most dangerous tool in the system. Several sandboxing options were evaluated; the decision is to defer proper sandboxing to v2 and rely on working-directory containment plus human approval for now.

## Current State

- Commands run with the full privileges of the tinyagent process
- A configurable timeout (default 30s) prevents infinite hangs
- No filesystem isolation, no network restriction, no resource limits
- The `write_file` tool has cwd containment, but `run_command` does not — a model-generated `rm -rf /` would execute if no human is in the loop

## Options Considered

**Docker container per command**: Spin up a lightweight container for each shell invocation. Strong isolation, but adds ~200ms latency per command and requires Docker on the host. Overkill for a single-user local tool.

**nsjail / bubblewrap**: Linux-only user-namespace sandboxes. Low overhead, good filesystem and network isolation. Not portable to macOS or Windows.

**seccomp profiles**: Restrict system calls at the kernel level. Very fine-grained but complex to configure correctly, and Linux-only.

**Simple allowlist**: Maintain a list of permitted commands (e.g., `cat`, `ls`, `python`, `grep`). Reject anything not on the list. Portable and simple, but brittle — a model can achieve most goals through creative use of allowed commands, and the allowlist grows until it's meaningless.

## Decision

Defer to v2. For now, rely on two mitigations:

1. **Working-directory containment**: the agent operates in a known project directory. Damage is bounded to that directory (though `run_command` does not enforce this — only `write_file` does).
2. **Ask-vs-act threshold**: destructive or ambiguous commands should trigger a confirmation prompt before execution. This is tracked as a TODO in the agent loop — see the ask-vs-act active thread.

## Risk Assessment

A malicious prompt injection or a confused model could generate destructive commands. The timeout prevents infinite resource consumption but not fast destructive actions. The realistic mitigation for a local dev tool is human-in-the-loop approval for all shell commands, which the current stub does not implement.

## Connections

-> [Ask vs Act Thresholds](../active-threads/ask-vs-act-thresholds.md) — human approval is the current sandboxing substitute for destructive commands
-> [Tool Protocol](../../docs/systems/tool-protocol.md) — tool execution model and safety checks
