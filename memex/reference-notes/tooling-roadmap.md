# Tooling Roadmap

Status tracker for scripts, background operators, and automation. Check this before building something that may already be planned or in progress.

## Scripts — Shipped

| Script | Purpose | Status |
|--------|---------|--------|
| `.memex/scripts/generate_wiki.py` | MediaWiki render from thread graph | Working |
| `.memex/scripts/generate_markdown.py` | Markdown render from thread graph | Working |
| `.memex/scripts/memex-lint.sh` | Budget compliance, thread sizes, frontmatter, cross-references, orphan detection | Working |
| `.memex/scripts/graph_health.py` | Graph health scoring (v2 subway model), cluster detection, bridge analysis, visualization | Working |
| `.memex/scripts/memex.py` | Session status CLI: graph health, inbox, patterns, active threads, full state dump | Working |
| `.memex/scripts/crawler.py` | Automated graph maintenance: health check → triage → optional Sonnet-powered fixes | Working |
| `.memex/scripts/spawn.py` | Create a new Memex from seed threads, copying portable skeleton, repairing subgraph | Working |

## Scripts — Planned

| Script | Purpose | Priority | Notes |
|--------|---------|----------|-------|
| Artifact INDEX.md generator | Parse artifact frontmatter, regenerate INDEX.md (by-date, by-tag views) | Medium | Currently manual. Intended as enforcer task. |
| Blind review automation | Strip authorship markers and send to fresh model instance for unbiased review | Low | Speculative — needs design work. |

## Background Operators — Defined

| Operator | Type | Purpose | Status | Notes |
|----------|------|---------|--------|-------|
| **Crawler** | Scheduled, deterministic | Compression budget checks, lifecycle enforcement, stale thread detection, missing backlink detection, candidate demotions/promotions | **Shipped** | `crawler.py` with `--fix` mode invokes Sonnet for proposed fixes on a maintenance branch. |
| **Spider** | Stochastic, exploratory | Random thread pairs, missed cross-references, unexpected connections, concept bridges | Not implemented | Suggestion-oriented, merge-gated. Proposes, never silently edits. Requires more design before implementation. |

## Render Pipeline — Future

| Enhancement | Priority | Notes |
|-------------|----------|-------|
| Enforcer/scheduled job runs generators | Low | wiki-generation procedure notes this as future architecture. Currently manual. |
| Additional render targets | Low | Pipeline designed for thin format adapters. Markdown and MediaWiki exist. Next target TBD. |

## Implementation Notes

- All background operators produce candidate deltas for human review — no silent edits.
- The `memex-lint.sh` script covers deterministic checks (budget, thread sizes). The crawler extends this with model-powered semantic checks (stale content, missing connections).
- The `spawn.py` script is the adoption path — create a fresh Memex without manually cleaning example content.
