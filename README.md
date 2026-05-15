# Memex

A persistence architecture that gives stateless LLMs continuous intelligence.

Instead of storing memories in opaque model features or vector databases, the Memex maintains a transparent, governed knowledge graph in markdown — threads, artifacts, cross-references, and a constitution that tells the AI how to maintain it all. The result: conversations that continue across sessions without fine-tuning, proprietary infrastructure, or large context windows.

## Getting Started

Clone the repo and open it with an AI agent (Claude Code, Codex CLI, Gemini CLI):

```bash
git clone https://github.com/cumberland-laboratories/memex.git
cd memex
```

The agent reads `CLAUDE.md`, finds the constitution, detects a fresh instance, and starts the **concierge bootstrap** — a conversation that populates your Memex:

1. Who are you? (→ identity.md)
2. What are you building? (→ mission.md, roadmap.md)
3. If you have code: bootstrap charters (→ the 2% intelligent map of your codebase)
4. What's already in flight? (→ threads, inbox)

The Memex grows by being used, not by being configured. A half-populated Memex that reflects reality is better than a fully-populated one you didn't verify.

## What's Inside

```
constitution-core.md         ← Portable governance (roles, lifecycle, conventions)
constitution.md              ← Domain rules for this instance
.memex/                      ← Portable machinery (scripts, procedures, policies)
memex/                       ← The knowledge graph (yours to populate)
  identity.md                ← Who you are
  mission.md                 ← What you're building and why
  roadmap.md                 ← Priorities
  inbox.md                   ← Zero-friction capture
  issues.md                  ← Bugs and blockers
  patterns.md                ← Recurring rhythms
  commit_draft.md            ← Session change log
  memex-start-up.md          ← Concierge bootstrap guide
  active-threads/            ← Current topics (loaded every session, 5-8 files)
  threads/                   ← Reference threads (loaded on demand)
  artifacts/                 ← Deep records (loaded on demand)
  charters/                  ← Code module maps (for coding projects)
  procedures/                ← Project-specific workflows
  reference-notes/           ← Design rationale and cognitive aids
CLAUDE.md                    ← Claude Code entry point
AGENTS.md                    ← Enforcer entry point
GEMINI.md                    ← Alternate model entry point
```

## How It Works

### The knowledge layer maintains itself

Threads update as a side effect of conversation. The AI captures ideas, decisions, and context because the constitution tells it to. Documentation nobody has to write.

### Orientation is pre-loaded, not searched

The AI loads your active working set before you say anything. It already knows what you were working on yesterday. The constitution is the boot sequence.

### Governance is machine-readable

An executable constitution — what to capture, what to ignore, when to compress, when to archive, who can do what. Encode the rules once, and any model that reads markdown can operate the system.

### A hard budget prevents infinite growth

Active threads stay on the desk (~400 lines, ~8K tokens). Cold topics move to the filing cabinet. Nothing is deleted — it just costs less to carry.

### Importance is behavioral, not declared

Hit counts track what you actually return to. The system self-organizes around real attention, not stated priorities.

## For Coding Projects

If your project has a codebase, the Memex includes **charters** — a 2% intelligent map of your code. Each module gets a charter documenting what functions do, what they read/write, who calls them, and the tripwires that must be preserved. The agent reads charters before changing code and updates them after. CI/CD for the knowledge layer.

Charter notation, philosophy, and format: → [memex/charters/README.md](memex/charters/README.md)

## Multi-Model Architecture

The constitution is the interface contract. Any model that can read markdown and follow instructions can operate the Memex:

- **Claude Code** as primary agent — reads constitution, maintains threads, writes code, updates charters
- **Codex / Gemini** as enforcer — audits the Memex read-only, produces reports, catches what the primary agent misses
- The enforcer is a **different model** by design — different training, different blind spots, independent verification

The architecture outlives any individual model. The governance is in the files.

## The Enforcer

The writer never reviews its own work. A different model audits the Memex read-only and reports findings. It checks for contradictions, missing cross-references, structural drift, and charter violations. It does not edit. It reports. The PI reviews and decides.

For coding projects, the enforcer review script (`memex/scripts/enforcer-review.py`) adds mechanical lint (hardcoded secrets, SQL dangers, injection vectors) alongside charter-grounded review.

## See a Populated Example

A fully populated Memex instance is preserved at git tag `v1-tinyagent-example`:

```bash
git checkout v1-tinyagent-example
```

This shows the complete architecture in action: 7 active threads, 5 module charters with TRIPWIREs, 15 artifacts, enforcer reports, a rendered wiki, and a working Python project the charters describe. See [reference-notes/example-tinyagent-instance.md](memex/reference-notes/example-tinyagent-instance.md) for details.

```bash
git checkout dev   # return to clean state
```

## Repo Structure

```
.memex/                      ← Portable machinery (don't modify)
  scripts/                   ← CLI, lint, wiki generation, graph health
  procedures/                ← Session lifecycle, thread lifecycle, audits
  policies/                  ← Concierge decision trees
  roles.yaml                 ← Role definitions (PI, agent, enforcer, crawler)
memex/                       ← The knowledge graph (yours)
  active-threads/            ← Current topics (5-8, loaded every session)
  threads/                   ← Reference threads (loaded on demand)
  artifacts/                 ← Deep records (loaded on demand)
  charters/                  ← Code module maps (notation + templates)
  reference-notes/           ← Essays and cognitive aids
```

## License

MIT. See [LICENSE](LICENSE).

## Origin

[Cumberland Laboratories](https://github.com/cumberland-laboratories). For a lightweight code-only version without the full thread graph, see [Gator](https://github.com/cumberland-laboratories/gator) — same loop, minimal ceremony.
