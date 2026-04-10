# Commit Draft

Append session changes here. Use as commit message source. Clear after each commit.

---

- Architectural transplant from parent design repo (cl-memex) to public-release-prep branch: ported portable machinery, two-layer constitution, procedures, policies, roles.yaml, and entry points so the repo matches the current Memex architecture. [#architecture] [#transplant] [#public-release] -claude
- Created `.memex/` directory with `scripts/` (memex.py, crawler.py, spawn.py added; existing graph_health/wiki generators/lint moved via git mv), `procedures/` (session-lifecycle, thread-lifecycle, enforcer-audit, wiki-generation, clip-to-artifact, graph-health-response — whiteboard-lifecycle omitted), `policies/document-routing.md`, and `roles.yaml`. [#structure] -claude
- Added `constitution-core.md` (portable governance) and rewrote `constitution.md` as a lean domain layer explaining this is a reference instance with fictional PI and omitted cl-memex-specific conventions. [#constitution] [#two-layer-split] -claude
- Updated `CLAUDE.md`, `AGENTS.md`, `GEMINI.md` to point to both constitution layers and specify role defaults (agent / enforcer / enforcer). [#entry-points] -claude
- Preserved six prior active-threads as `memex/reference-notes/essay-*.md` with updated `category: essay` frontmatter and preamble noting their role as architecture heritage. Moves via git mv to preserve history. [#heritage] -claude
- Removed cl-memex-specific files not appropriate for a public reference instance: `memex/friction.md`, `memex/whiteboard.md`, `memex/audit-tracker.md`, `memex/procedures/` (duplicates of the ported core procedures), `memex/patterns/` directory, `memex/reference-notes/whiteboard-design.md`. [#cleanup] -claude
- Scrubbed cl-memex/Cumberland/Alan references from all ported files (spawn.py, session-lifecycle.md, enforcer-audit.md). [#scrub] -claude
- Created `memex/active-threads/session-handoff.md`: the full phased plan for the next session to author `tinyagent/` (design-quality skeleton, pure Python, Claude API, runnability secondary), populate its Memex (7 active-threads headlined by `context-budget-economics`, 3 artifacts, reference-notes, systems docs), and run the machinery. [#handoff] [#plan] -claude
- Seeded `memex/inbox.md` with a READ FIRST pointer to the handoff thread, preventing bootstrap-detection in the next session. [#handoff] -claude
