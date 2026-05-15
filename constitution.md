# Memex — Domain Constitution

Project-specific rules for this Memex instance. The core governance lives in → [constitution-core.md](constitution-core.md).

## What This Repo Is

This is the **Memex** — an MIT-licensed knowledge persistence layer for AI-assisted research and development. It makes the AI feel like it was there yesterday. The architecture is designed to be cloned, populated by a PI (principal investigator) working with an AI agent, and grown over time.

If this is a **fresh instance** (identity.md still has bracket placeholders, active-threads/ is empty), the agent follows the concierge bootstrap in → [memex-start-up.md](memex/memex-start-up.md).

## Operating Mode

`operating-mode: user` — the default session level is content (using the Memex as infrastructure). Architectural discussions about the Memex itself use the `*m` prefix to switch to meta-level.

## Charter Lookup Rule

**Before modifying code**, consult the relevant charters. This is not optional. Charters are the ground-truth API reference — they document what every function reads, writes, and depends on, including patterns that cannot be inferred from the code alone (tripwires, rendering dualities, session state flows).

Full procedure: → [Charter Lookup](memex/procedures/charter-lookup.md)
Charter philosophy, notation, and formats: → [memex/charters/README.md](memex/charters/README.md)

## Domain Conventions

- **Charters** live in `memex/charters/`. Used for coding projects — the 2% intelligent map of the codebase. The README.md in that folder is self-contained: point an LLM at `memex/charters/` and it gets the philosophy, the notation, and the format.
- **Reference-note essays** (`memex/reference-notes/essay-*.md`) are long-form essays on the Memex architecture itself. They are reference material, not active threads.
- Project-specific procedures live in `memex/procedures/` and grow organically.
- `memex/whiteboard.md` is an ephemeral working surface — enforcer findings, coordination notes. Cleared after use.

## Concierge Principle

The agent's first job is to make the PI productive, not to demonstrate the architecture. On a fresh instance:
1. Establish ownership context (solo or team?) → [identity-and-ownership.md](memex/reference-notes/identity-and-ownership.md)
2. Ask what the PI is working on
3. Populate mission.md and identity.md from the conversation
4. Build the roadmap together
5. If the project has code, bootstrap charters (→ [memex-start-up.md](memex/memex-start-up.md))
6. Let threads emerge from conversation — don't force structure before there's content

The Memex grows by being used, not by being configured.

For common PI questions — "catch me up", "what should I work on?", "where does this go?" — see → [concierge-responses.md](memex/reference-notes/concierge-responses.md).

## Prior Example

A fully populated Memex instance (the "tinyagent" reference project) is preserved at git tag `v1-tinyagent-example`. Check it out to see what a mature Memex looks like with threads, charters, artifacts, wiki, and systems docs all working together. See → [reference-notes/example-tinyagent-instance.md](memex/reference-notes/example-tinyagent-instance.md).
