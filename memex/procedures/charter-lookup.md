# Procedure: Charter Lookup

**When to use**: Before modifying application code. This is not optional — it's a constitutional requirement.

## Dispatch Table

Find the code you're about to change. Read the charter(s) listed. **Always** read cross-cutting if one exists.

### tinyagent

**Always read first:** [Cross-Cutting](../charters/cross-cutting.md) — patterns spanning multiple modules, TRIPWIRE labels, stub inventory.

| If you're changing... | Read these charters |
|---|---|
| `tinyagent/agent.py` | [Agent Loop](../charters/agent-loop.md) + [Cross-Cutting](../charters/cross-cutting.md) |
| `tinyagent/context.py` | [Context Budget](../charters/context-budget.md) + [Cross-Cutting](../charters/cross-cutting.md) |
| `tinyagent/client.py` | [Infrastructure](../charters/infrastructure.md) |
| `tinyagent/session.py` | [Infrastructure](../charters/infrastructure.md) + [Cross-Cutting](../charters/cross-cutting.md) |
| `tinyagent/__main__.py` | [Infrastructure](../charters/infrastructure.md) |
| `tinyagent/tools/__init__.py` | [Tools](../charters/tools.md) + [Cross-Cutting](../charters/cross-cutting.md) |
| `tinyagent/tools/*.py` (any tool) | [Tools](../charters/tools.md) + [Cross-Cutting](../charters/cross-cutting.md) |

*For a larger project, this table would have 15-20 rows mapping code paths to specific charter files. The dispatch table tells the agent exactly which charters to load instead of guessing.*

## How to Read a Charter

### Function-level charters (large codebases)

For each function you're about to change, find its entry and check:

1. **Line anchor `[Lnnn]`** — verify it's roughly current. If the function has moved far from the documented line, the charter may be stale. Proceed with caution.
2. **Access patterns `(R)/(W)/(RW)`** — what models, session keys, caches, and external APIs does this function read and write? Your change must preserve or intentionally modify these.
3. **Tripwires `!`** — non-obvious patterns that must be preserved. Read every tripwire before changing the function.
4. **Cross-references `→` / `←`** — what calls this function (`←`) and what does it call (`→`)? These are your blast radius.
5. **`TRIPWIRE` sections in cross-cutting** — architectural patterns spanning multiple functions. If your change touches any function involved in a cross-cutting pattern, read the full TRIPWIRE section.

### Module-level charters (small codebases)

1. **"Does not own"** — verify your change belongs in this module, not somewhere else.
2. **"Before changing"** — institutional knowledge: implicit contracts, stubs, intentional design decisions.
3. **"Connections"** — what imports this module? That's your blast radius.

## After Changing Code

If you changed a function's signature, access patterns, cross-references, or behavior, **update the charter in the same operation**:

- Update line anchors `[Lnnn]` if functions moved
- Update access patterns if you added or removed model/session/cache reads or writes
- Add or update tripwires if your change introduces non-obvious behavior
- Add cross-references if your change creates new dependencies
- Mark deleted functions as `**DELETED**` with date and reason — don't silently remove entries
- Update cross-cutting documentation if your change affects a pattern that spans modules

## When to Create Charters

If you're working in a codebase with no charters and the codebase exceeds ~10K lines, or if you're about to do a significant refactor, consider creating charters *before* starting the work. Charters created before a refactor serve as navigation map, dependency graph, tripwire documentation, and invariant checklist.

For charter format guidance: -> [memex/charters/README.md](../charters/README.md) (philosophy, notation, anti-patterns, and how to implement in another repo).
