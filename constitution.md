# Memex Public Reference Instance — Domain Constitution

Project-specific rules for this particular Memex. The core Memex governance lives in → [constitution-core.md](constitution-core.md).

## What This Repo Is

This is the **public reference instance** of the Memex architecture, released under MIT license. It is not a starter kit or a template — it is a *populated, working Memex* that a reader can browse on GitHub and absorb the ideas from without cloning anything.

The repo currently carries a small illustrative project (`tinyagent` — a minimal Claude-API coding assistant in pure Python) as the vehicle for demonstrating the Memex managing both project planning and code development. The code is secondary; the **structure, the threads, the cross-references, the reports, and the wiki** are the thing.

A second layer of content — `memex/reference-notes/essay-*.md` — preserves earlier architectural thinking about the Memex itself. These are the "Memex architecture essays" and are distinct from the project threads.

## PI

The PI in this reference instance is a fictional persona ("Ren"). A real cloner replaces the content with their own mission, identity, and project.

## Operating Mode

`operating-mode: user` — the default session level is content (using the Memex as infrastructure). Architectural discussions about the Memex itself use the `*m` prefix to switch to meta-level.

## Charter Lookup Rule

**Before modifying code**, consult the relevant charters. This is not optional. Charters are the ground-truth API reference — they document what every function reads, writes, and depends on, including patterns that cannot be inferred from the code alone (tripwires, rendering dualities, session state flows).

Full procedure: → [Charter Lookup](memex/procedures/charter-lookup.md)
Charter philosophy and formats: → [Why Charters](memex/reference-notes/charter-philosophy.md)

## Domain Conventions

This reference instance deliberately omits the heavier conventions that a long-running production Memex might adopt:

- No `friction.md` ��� the public repo is small and short-lived; friction logging has no audience here.
- No `whiteboard.md` — no multi-operator concurrent work happens in a reference instance.
- No `audit-tracker.md` — enforcer reports live in `docs/reports/` and are read directly.

Project-specific procedures live in `memex/procedures/` and grow organically as the project needs them.

## Reference-Note Essays

`memex/reference-notes/essay-*.md` are long-form essays on the Memex architecture — adversarial review methods, knowledge-systems comparison, agent performance, the role of git, etc. They are not part of the `tinyagent` project's working threads, and they should not be treated as active-threads even if they're long or substantive. They are **reference material about the Memex itself**, preserved as part of the repo's intellectual history.

## API Keys and External Dependencies

The `tinyagent` project requires a Claude API key to actually run. The public repo ships with a `.env.example`; instructions for wiring it up live in `docs/systems/tinyagent-architecture.md`. A reader browsing the repo on GitHub does not need any keys to read the Memex and understand the architecture — only to *run* `tinyagent`.
