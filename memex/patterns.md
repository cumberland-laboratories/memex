# Patterns

Recurring rhythms for keeping the Memex and codebase healthy.

---

**Weekly: Crawler dry-run**
Run `python .memex/scripts/crawler.py --dry-run` to catch orphaned threads, broken links, and frontmatter drift before they accumulate. Fix anything flagged before starting the week's work.

**Monthly: Enforcer audit**
Run the enforcer role against the full Memex. Check for policy violations, stale threads, and structural decay. Log results in an artifact if anything non-trivial surfaces.

**Pre-commit: Lint check**
Run `python .memex/scripts/memex.py lint` before committing Memex changes. Catches malformed frontmatter, missing required fields, and files that violate document-routing policy.

**Session-close: Compression pass**
At the end of every session, compress `commit_draft.md` into a commit message, triage `inbox.md`, and update any thread that received meaningful work. The goal is that the next session opens clean.
