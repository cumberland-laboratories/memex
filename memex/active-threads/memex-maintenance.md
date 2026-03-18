---
last-touched: 2026-03-18
category: systems
hits: 1
tags: [memex-infrastructure, tooling, maintenance, wiki, graph-health]
---

# Memex Maintenance

## Summary

Operational commands for maintaining the Memex: generating the wiki render, running the lint checker, and producing graph-health reports with visualization. These are the tools that keep the system honest — mechanical checks that don't depend on any model's judgment.

## Wiki Generation

Renders the thread graph into human-readable documentation. The wiki is a presentation layer, not the source of truth.

```bash
# Generate both MediaWiki and Markdown renders
python scripts/generate_wiki.py && python scripts/generate_markdown.py
```

Output: `wiki/Main_Page.wiki` and `wiki/Main_Page.md`

## Lint Check

Deterministic structural check — no model required. Verifies compression budgets, thread sizes, frontmatter, cross-reference integrity, and orphan detection.

```bash
bash scripts/memex-lint.sh
```

Exit code 0 means all checks passed. Non-zero reports the error count.

## Graph Health

Analyzes the thread graph for connectivity properties the lint script doesn't cover: backlink index, 3-hop reachability (the constitutional invariant), and single-bridge edges whose removal would disconnect the graph.

```bash
# Report only
python scripts/graph_health.py

# Report + graph visualization + JSON health record
python scripts/graph_health.py --image wiki/thread-graph.png --json wiki/graph-health.json
```

Output: terminal report, optional `wiki/thread-graph.png` (graph with directed edges, tier coloring, and health score panel), and optional `wiki/graph-health.json` (machine-readable health record with date, scores, orphan list, and structural stats).

**Dependencies**: `pip install -r requirements.txt` (networkx, matplotlib)

## Recommended Cadence

- **Lint**: run before committing structural changes (thread creation, demotion, splits)
- **Graph health**: run after adding or removing threads, or when cross-references change
- **Wiki render**: run before pushing to main, so the public-facing wiki stays current

## Connections

→ [memex-enhancements.md](memex-enhancements.md) — graph-health instrumentation (item 1) delivered this tooling
→ [knowledge-systems-comparison.md](knowledge-systems-comparison.md) — scaling analysis that identified graph maintenance as the failure point
→ [agent-performance-latency.md](agent-performance-latency.md) — tool-call round trips are the latency cost of maintenance operations

## Health Score

The graph image includes a stats panel and composite health score (0-100), graded as HEALTHY/FAIR/UNHEALTHY. Four dimensions, equally weighted:

- **Reachability** (100 = all pairs within 3 hops, 0 = disconnected)
- **Resilience** (100 = no bridge edges, -30 per bridge)
- **Connectivity** (100 = no orphans, -25 per orphan thread with zero inbound links)
- **Distribution** (100 = no hub concentration, degrades when one node carries >50% of edges)

Orphans and bridges are constitutional invariant violations — the scoring penalizes them heavily. A glance at the graph image tells you: is the Memex healthy right now, and where are the weak points?

## Small Next Features

- **More visible arrowheads on graph edges.** Current `-|>` style renders as a subtle flat bar at this scale. Switch to larger triangular arrowheads or increase arrowsize so directionality is obvious at a glance — will matter more as the graph grows.
- **Simulate mode for graph health.** Preview the impact of a new cross-reference before committing it. E.g., `python scripts/graph_health.py --simulate "git-role-in-memex.md -> memex-maintenance.md"` — shows the score delta, bridge/orphan changes, and before/after comparison. Lets the adjudicator shape the graph topology with real-time feedback, like evaluating a chess move before making it. Important constraint: the tool shows structural impact, but semantic justification remains a human judgment. A link that improves the score but doesn't represent a real conceptual connection is gaming the metric.

## Open Questions

- Should wiki generation and graph health run as a pre-commit hook or stay manual?
- Should the graph image be committed to the repo or regenerated on demand?
- What's the right health score formula? Weighted composite, or simple pass/fail per dimension?
