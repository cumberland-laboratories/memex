# Memex

A persistence architecture that gives stateless LLMs continuous intelligence.

Instead of storing project memory in opaque model features or vector databases, Memex maintains a transparent, governed knowledge graph in markdown: threads, artifacts, cross-references, and constitutions that tell the AI how to maintain it all. The result is a working memory layer that can continue across sessions without fine-tuning, proprietary infrastructure, or giant context windows.

## Getting Started

Clone the repo and open it with your AI agent of choice:

```bash
git clone https://github.com/cumberland-laboratories/memex.git
cd memex
```

The agent reads its model entrypoint, finds the constitutions, detects a fresh instance, and starts the concierge bootstrap: a conversation that populates your Memex.

Typical first-session questions:

1. Who are you? -> `memex/identity.md`
2. What are you building? -> `memex/mission.md`, `memex/roadmap.md`
3. If you have code, should we bootstrap charters? -> `memex/charters/`
4. What is already in flight? -> threads, inbox, issues

The Memex grows by being used, not by being configured. A half-populated Memex that reflects reality is better than a fully populated one that the PI did not verify.

## What It Installs

```text
constitution-core.md         <- Portable governance (roles, lifecycle, conventions)
constitution.md              <- Domain rules for this instance
.memex/                      <- Portable machinery (scripts, procedures, policies)
memex/                       <- The knowledge graph (yours to populate)
  identity.md                <- Who you are
  mission.md                 <- What you're building and why
  roadmap.md                 <- Priorities
  inbox.md                   <- Zero-friction capture
  issues.md                  <- Bugs and blockers
  patterns.md                <- Recurring rhythms
  commit_draft.md            <- Session change log
  memex-start-up.md          <- Concierge bootstrap guide
  active-threads/            <- Current topics
  threads/                   <- Reference threads
  artifacts/                 <- Deep records
  charters/                  <- Code module maps (for coding projects)
  procedures/                <- Project-specific workflows
  reference-notes/           <- Design rationale and cognitive aids
CLAUDE.md                    <- Claude Code entry point
AGENTS.md                    <- Codex entry point
GEMINI.md                    <- Gemini entry point
```

## How It Works

### The knowledge layer maintains itself

Threads update as a side effect of conversation. The AI captures ideas, decisions, and context because the constitutions tell it to.

### Orientation is pre-loaded, not rediscovered

The AI loads your active working set before you say anything. It already knows what you were working on yesterday. The constitutions are the boot sequence.

### Governance is machine-readable

The rules are in files: what to capture, what to ignore, when to compress, when to archive, who can do what. Any model that can read markdown and follow instructions can operate the system.

### A hard budget prevents uncontrolled growth

Active threads stay on the desk. Cold topics move to the filing cabinet. Nothing is deleted; it just costs less to carry.

## For Coding Projects

If your project has a codebase, the Memex includes **charters**: maintained maps of code modules, boundaries, access patterns, and tripwires. The agent reads charters before changing code and updates them after.

Charter notation, philosophy, and format:
-> [memex/charters/README.md](memex/charters/README.md)

## Multi-Model Architecture

The constitutions are the interface contract. Any model that can read markdown and follow instructions can operate the Memex.

- Claude Code / Codex / Gemini can all be primary agents
- a different model can act as enforcer
- the enforcer is different by design: different training, different blind spots, independent verification

The architecture outlives any individual model. The governance is in the files.

## The Enforcer

The writer never reviews its own work. A different model audits the Memex read-only and reports findings. It checks for contradictions, missing cross-references, structural drift, and charter violations. It does not edit. It reports. The PI reviews and decides.

For coding projects, the enforcer review script adds mechanical lint (hardcoded secrets, SQL dangers, injection vectors) alongside charter-grounded review.

## See a Populated Example

A fully populated Memex instance is preserved at git tag `v1-tinyagent-example`:

```bash
git checkout v1-tinyagent-example
```

This shows the complete architecture in action: active threads, module charters with TRIPWIREs, artifacts, enforcer reports, and a working Python project the charters describe. See [memex/reference-notes/example-tinyagent-instance.md](memex/reference-notes/example-tinyagent-instance.md) for details.

```bash
git checkout dev   # return to clean state
```

## License

MIT. See [LICENSE](LICENSE).

## Origin

[Cumberland Laboratories](https://github.com/cumberland-laboratories). For a lightweight code-only version without the full thread graph, see [Gator](https://github.com/cumberland-laboratories/gator).
