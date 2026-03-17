# Tooling Roadmap

Status tracker for scripts, background operators, and automation. Check this before building something that may already be planned or in progress.

## Scripts — Planned

| Script | Purpose | Priority | Notes |
|--------|---------|----------|-------|
| `scripts/generate_wiki.py` | MediaWiki render from thread graph | High | Previously shipped in cl-memex, not yet ported to public repo. |
| `scripts/generate_markdown.py` | Markdown render from thread graph | High | Previously shipped in cl-memex, not yet ported to public repo. |
| `scripts/memex-lint.sh` | Budget compliance, thread sizes, frontmatter, cross-references, orphan detection | High | Previously shipped in cl-memex, not yet ported to public repo. |
| Artifact INDEX.md generator | Parse artifact frontmatter, regenerate INDEX.md (by-date, by-tag, external-sources views) | Medium | Currently manual. Referenced in constitution, self-documenting-systems thread, INDEX.md header. Intended as enforcer task. |
| Batch state-dump for session open | Single script that outputs inbox, patterns, audit-tracker, active thread summaries — reduces 14 tool calls to 1 | Low | Friction log 2026-03-15, session-opening-ux thread. UX improvement, not functional blocker. |
| Blind review automation | Strip authorship markers and send to fresh model instance for unbiased review | Low | adversarial-review-techniques thread. Speculative — needs design work. |

## Background Operators — Defined, Not Implemented

| Operator | Type | Purpose | Priority | Notes |
|----------|------|---------|----------|-------|
| **Crawler** | Scheduled, deterministic | Compression budget checks, lifecycle enforcement, stale thread detection, missing backlink detection, candidate demotions/promotions | Near-term | Cheap model can do this. Rule-following, not reasoning. Could be a cron job or git hook invoking a model against the thread directory. Produces candidate changes for human review. |
| **Spider** | Stochastic, exploratory | Random thread pairs, missed cross-references, unexpected connections, concept bridges | Later-stage | Suggestion-oriented, merge-gated. Proposes, never silently edits. Requires more design before implementation. |

## Render Pipeline — Future

| Enhancement | Priority | Notes |
|-------------|----------|-------|
| Enforcer/scheduled job runs generators | Low | wiki-generation procedure notes this as future architecture. Currently manual. |
| Additional render targets | Low | Pipeline designed for thin format adapters. Markdown and MediaWiki exist. Next target TBD. |

## Implementation Notes

- Crawler is the highest-value near-term automation. It's the most scriptable and addresses real maintenance pressure as the thread count grows.
- All background operators produce candidate deltas for human review — no silent edits.
- The `memex-lint.sh` script already covers some crawler-like checks (budget, thread sizes). A crawler extends this with model-powered semantic checks (stale content, missing connections).
