# Scaling Approach Report - 2026-03-17

## Basis

This report is based on the most recent scaling discussion in [memex/active-threads/knowledge-systems-comparison.md](../memex/active-threads/knowledge-systems-comparison.md) and the supporting implementation notes in [memex/reference-notes/tooling-roadmap.md](../memex/reference-notes/tooling-roadmap.md) and [constitution.md](../constitution.md).

## Framing

The core scaling problem is not storage size or prompt budget. The tiered Memex design already contains those reasonably well: active material stays compressed, lightweight threads hold colder context, and artifacts hold depth. The failure point is graph maintenance.

At small scale, a human or chat agent can preserve cross-links by care and memory. At thousands of threads, that becomes unreliable. The system's main promise, "the graph is the index," starts to fail unless the graph is continuously checked and regenerated in places where hand-maintenance is too brittle.

## Recommended Approach

The right approach is to keep the graph-first architecture and add generated support structures around it rather than replacing it with a hierarchy.

### 1. Make graph health measurable first

Extend the current lint/audit layer so the system can answer:

- Which threads have zero inbound links?
- Which links are broken after rename, split, or demotion?
- Which clusters are reachable only through a single bridge?
- Which topics violate the 3-hop expectation in practice?

This is the minimum viable scaling layer because it turns a vague failure mode into an observable one.

### 2. Generate secondary indexes, do not hand-maintain them

The thread identifies two missing indexes that should be generated:

- backlink index
- tag/faceted index

These should be treated as support structures, not as the primary navigation model. The Memex should still be entered through threads and links, but these indexes provide recovery when associative navigation fails.

### 3. Add orphan and connectivity checks before adding smarter automation

Before introducing model-driven background work, add deterministic checks for:

- orphaned threads
- unreachable nodes
- single-bridge clusters
- link churn after structural operations

This keeps the first scaling step auditable and low-risk.

### 4. Introduce the `Crawler` as a candidate-change operator

The roadmap already points to the right near-term automation: a scheduled, deterministic crawler that proposes candidate fixes and maintenance actions for human review.

Its initial scope should stay narrow:

- stale thread detection
- missing backlink detection
- candidate promotions/demotions
- possible cross-reference gaps flagged for review

It should not silently edit the Memex. The report thread is clear that the maintenance burden is the issue; the answer is assisted upkeep, not autonomous graph mutation.

### 5. Revisit active-window limits only after graph tooling exists

The "5-8 active threads" constraint may feel too narrow at higher activity levels, but expanding it first would increase hot-tier noise without solving discovery or link integrity. The active window should be reconsidered only after backlink, orphan, and connectivity tooling are in place.

## Claude's Concerns

The most recent thread raises five substantive concerns:

1. Graph navigability degrades with scale.
   The 3-hop small-world property is declared as an invariant, but the current system relies on agent diligence rather than verification.

2. Forgotten threads become effectively invisible.
   If inbound links disappear during compression, splitting, or demotion, recovery falls back to search rather than graph navigation.

3. Cross-reference maintenance cost compounds quickly.
   At 5,000 threads, even a modest link count creates tens of thousands of edges to preserve across structural edits.

4. The active window may force artificial rotation.
   If genuine concurrent interests exceed the 5-8 active thread budget, the current operating model may cool topics too aggressively.

5. The constitution specifies invariants without enforcement mechanisms.
   This is the deepest concern. The design says connectivity must be preserved, but the system does not yet supply the tools that make that guarantee credible at scale.

## Recommended Sequence

1. Strengthen `memex-lint.sh` or an equivalent audit path to emit backlink, orphan, and reachability findings.
2. Generate a backlink index and tag index from frontmatter and links.
3. Add a graph-connectivity report as a standard enforcer artifact.
4. Implement the narrow first version of the `Crawler` as a candidate-change producer.
5. Reassess active-thread window size using evidence from those reports.

## Bottom Line

The scaling issue should be treated as a graph operations problem, not a storage problem. The architecture can likely scale if link integrity, discoverability, and reachability become generated and verified properties instead of manual expectations.
