---
last-touched: 2026-04-12
category: reference
tags: [charters, onboarding, architecture, pattern, coding-projects]
---

# Codebase Charter Pattern

## Summary

A charter is a "parachute in" document that lets someone — human or LLM — orient in a codebase without reading every file. Each module gets a short block answering the same five questions. The result is a map you read *before* the code, not a reference you check *after*.

For the deeper argument — why charters exist, why boundaries matter more than descriptions, and how this connects to AI-assisted development — see -> [Why Charters](charter-philosophy.md).

## The Five Questions

Every module charter answers:

1. **What does this module own?** Its single responsibility, stated as a noun phrase ("session persistence", "rate-limit retry", "the agentic loop"). If you can't state it in one phrase, the module probably does too much.

2. **What does it NOT own?** Boundaries are more useful than descriptions. Saying "does not own API calls" prevents someone from adding API logic here. This is the line that prevents modules from growing.

3. **What are its inputs and outputs?** Concrete: method signatures, data formats, side effects. Not architectural hand-waving — what actually goes in and comes out.

4. **Where does it connect?** What imports it, what does it import. Dependency direction matters: if A imports B, changes to B can break A. A module that imports nothing is safe to change; a module imported by everything is dangerous to change.

5. **What should you know before changing it?** The non-obvious things: implicit contracts, performance-sensitive paths, known stubs, design decisions that look wrong but are intentional. This is where institutional knowledge lives.

## When to Write Charters

- **At project start**: write skeleton charters alongside skeleton code. They force you to articulate module boundaries before writing implementations.
- **Before onboarding**: when someone new (human or LLM) will parachute into the codebase. The charter is cheaper than a walkthrough and doesn't decay as fast.
- **After a refactor**: module boundaries shift. Update charters to match the new reality, or they become misleading.
- **When an LLM will modify the code**: the charter is the most efficient way to give an LLM the "what goes where" knowledge it needs. It's cheaper than loading every source file into context.

## Where They Live

In a Memex project, charters belong as a **dated artifact** (`memex/artifacts/YYYY-MM-DD-<project>-module-charters.md`) because they're a snapshot of architectural decisions. The systems doc (`docs/systems/<project>-architecture.md`) carries the module map; the charter artifact carries the ownership and boundary detail.

For non-Memex projects, a `ARCHITECTURE.md` or `docs/charters.md` at the repo root works. The format matters less than the discipline of answering all five questions for every module.

## Anti-Patterns

- **Charter as API docs**: charters are about ownership and boundaries, not method signatures. If it reads like a docstring, it's too low-level.
- **Charter without "does not own"**: the boundaries are the most valuable part. Without them, the charter is just a description.
- **Stale charters**: worse than no charters. If you refactor, update or delete the charter. A wrong map is more dangerous than no map.
- **One giant charter**: each module gets its own block. If you can't separate them, your modules aren't separate.

## Connections

-> [tinyagent Module Charters](../artifacts/2026-04-12-tinyagent-module-charters.md) — worked example of this pattern applied to a real (small) codebase
-> [Tool Grain Size](../active-threads/tool-grain-size.md) — the "one thing the model cannot do itself" heuristic applies to modules too: one thing the other modules cannot do themselves
