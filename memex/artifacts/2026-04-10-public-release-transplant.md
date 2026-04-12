---
date: 2026-04-10
depth: deep
tags: [handoff, public-release, tinyagent, reference-instance, restructure]
source-thread: session-handoff
source: claude
summary: Full phased plan for the public-release-prep branch — architectural transplant from cl-memex, tinyagent scaffolding, Memex population, machinery validation, and polish.
---

*Archived from `active-threads/session-handoff.md` on 2026-04-12 after completion of all phases.*

# Session Handoff — Public Release Prep

## Summary

This Memex has just been restructured (2026-04-10) on the `public-release-prep` branch to serve as the public MIT-licensed **reference instance** of the Memex architecture. The architectural transplant from the parent design repo (`cl-memex`) is complete: portable machinery, two-layer constitution, procedures, policies, roles, and entry points are in place. The repo's previous meta-architecture active-threads have been preserved as `reference-notes/essay-*.md` ("Memex architecture essays"). What remains is authoring a small illustrative code project — **`tinyagent`**, a minimal pure-Python Claude-API coding assistant — and populating the Memex around it. This thread is the plan; read it first, then execute the phases below.

## Operating Context

- **Branch**: `public-release-prep` (off `dev`). You are already on it.
- **Parent design repo**: `cl-memex` (not linked here — separate local repo). All architectural decisions for the public release were captured there and ported to this repo by the prior session. Do not try to reach it; everything you need is local.
- **Target deadline**: weekend of 2026-04-11/12. Tight but scope is sized for it.
- **Scope priority**: readable-on-GitHub > runnable code. See "Runnability" below.

## What Just Happened (the transplant, 2026-04-10)

1. **Baseline commit on `dev`**: in-progress `memex-enhancements.md` edits and the 2026-03-18 enforcer audit report were committed, `tmp/` added to `.gitignore`.
2. **Branch `public-release-prep` created** off that baseline.
3. **Machinery moved into `.memex/`**:
   - `scripts/` → `.memex/scripts/` (history preserved via `git mv`)
   - Added from parent: `memex.py`, `crawler.py`, `spawn.py`
   - Existing scripts retained: `graph_health.py`, `generate_wiki.py`, `generate_markdown.py`, `memex-lint.sh`
4. **`.memex/procedures/`** populated with portable procedures: `session-lifecycle.md`, `thread-lifecycle.md`, `enforcer-audit.md`, `wiki-generation.md`, `clip-to-artifact.md`, `graph-health-response.md`. `whiteboard-lifecycle.md` deliberately omitted (reference instance has no whiteboard).
5. **`.memex/policies/`** populated with `document-routing.md` — the concierge's decision tree for routing content.
6. **`.memex/roles.yaml`** added — PI / agent / enforcer / crawler role definitions.
7. **`constitution-core.md`** added (portable governance, from parent). **`constitution.md`** rewritten as a lean domain layer explaining this is a reference instance with a fictional PI and omitted conventions.
8. **Entry points updated**: `CLAUDE.md`, `AGENTS.md`, `GEMINI.md` now point to both constitution layers and specify role defaults.
9. **Heritage preserved**: six prior active-threads moved to `memex/reference-notes/essay-*.md`, frontmatter updated (`category: essay`), preamble added identifying them as architecture essays.
10. **cl-memex-specific conventions removed**: `memex/friction.md`, `memex/whiteboard.md`, `memex/audit-tracker.md`, `memex/procedures/` (dupes of core procedures), `memex/patterns/` directory, `memex/reference-notes/whiteboard-design.md`.
11. **Scrubs**: all cl-memex / Cumberland / Alan references removed from ported files.

The repo is now structurally the current Memex architecture but **empty of a real project**. That's your job.

## What You Need To Do

### Phase A — Orient

1. Read `constitution-core.md` then `constitution.md`.
2. Run `python .memex/scripts/memex.py status --full --role agent --format json` to verify the CLI works in this repo. If it errors, triage — the script was ported from the parent and may have path assumptions. Fix minimally.
3. Read this thread fully. Read `reference-notes/essay-*.md` in any order to absorb the architectural heritage that's already here.
4. Read `README.md` — it's article-format and already strong. Do not rewrite it. You may add one paragraph at the end pointing readers at `tinyagent` once the project exists.

### Phase B — Populate tinyagent scaffolding

The goal: **a design-quality Python skeleton that demonstrates architectural decisions**, not a production-grade working tool. The PI (Alan, operating through you) has said explicitly: *the workability of tinyagent is secondary; code design and update-ability are what matter. Leaving the cloner to hook up the API (with instructions in the Memex) is fine.*

1. Create `tinyagent/` at the repo root (sibling to `memex/`, `.memex/`, `docs/`).
2. Structure the code to demonstrate clear architectural seams:
   - `tinyagent/__main__.py` — CLI entry point, argparse, dispatch
   - `tinyagent/agent.py` — the agentic loop (plan → act → observe → reflect)
   - `tinyagent/context.py` — the context-budget manager (the headline design concern)
   - `tinyagent/tools/` — tool definitions, one file per tool
   - `tinyagent/session.py` — session persistence (continuity without memory)
   - `tinyagent/client.py` — thin wrapper over `anthropic.Anthropic`
3. Pure Python + the `anthropic` SDK. No framework. No database — session state on disk as JSON.
4. ~600-1200 lines total is the target. Leaner is better if the design is clearer for it.
5. Include `tinyagent/README.md` explaining setup (env var `ANTHROPIC_API_KEY`, install `anthropic`, run `python -m tinyagent "<task>"`).
6. Include a root `.env.example` with `ANTHROPIC_API_KEY=sk-ant-...`.
7. **Code does not need to run end-to-end.** Leave clearly marked `TODO` stubs in places where the Memex threads discuss an open design question. The code is a *teaching artifact*; the Memex explains it.

### Phase C — Populate the tinyagent Memex

This is where the reference instance actually demonstrates the Memex. Author these in order. The headline (`context-budget-economics`) must be *genuinely good* — if it's not, scrap it and rewrite before moving on.

**Scaffolding files** (`memex/`):
1. `mission.md` — what tinyagent is, why it exists, scope boundaries. ≤ 30 lines.
2. `roadmap.md` — 5-6 milestones; one visibly struck through (evidence of a pivot), one added later (evidence of capture).
3. `issues.md` — 2-4 real fragilities, honestly written: e.g., "context explosion on large file reads", "tool race on concurrent writes", "no retry/backoff for rate limits yet".
4. `patterns.md` — minimal recurring rhythms: weekly crawler dry-run, monthly enforcer audit.
5. `identity.md` — **fictional PI "Ren"**. Populate all sections (timezone, background, intellectual disposition, working style, interests). Ren is a solo dev building agentic tools; keep it credible and a little quirky. Frontmatter: `operating-mode: user`. Remove all `[bracket placeholders]`.
6. `commit_draft.md` — a **mid-session state**. 3-5 bullets with decision tags and `-claude` / `-ren` attribution; one bullet deliberately incomplete to signal an in-flight session. Proof of life.
7. `inbox.md` — seed with 5-6 items: raw, uneven quality, one half-sentence, one that references an open thread, one that looks like a genuine tangent. Clear this thread's seed item (the one I'm about to add below) once you've internalized it.

**Active threads** (`memex/active-threads/`) — 7 threads, headlined by the first:
1. `context-budget-economics.md` — **the headliner**. Name a principle. Present the tradeoff (how much context costs, what's worth loading, the opportunity cost of every token). Cross-ref an artifact with a formal model. Leave one question explicitly open. Target 40-60 lines. This thread sells the repo.
2. `tool-grain-size.md` — when tools are too fine (call overhead, schema bloat) vs too coarse (brittle, un-composable). Propose a grain-size heuristic.
3. `agentic-loop-failure-modes.md` — name the failure modes: brute-force retry, plan drift, context exhaustion, tool hallucination. For each, a countermeasure.
4. `session-continuity-without-memory.md` — the bridge to the Memex itself. How does yesterday's agent feel like today's agent when the model is stateless? This thread is where the code project meets the reference-instance thesis.
5. `ask-vs-act-thresholds.md` — reversibility, blast radius, authorization scope. Same spirit as the Claude Code system prompt's guidance but generalized.
6. `error-recovery-as-design.md` — errors as first-class signals, not exceptions to handle. What does the agent *do* when a tool fails?
7. `tool-schema-ergonomics.md` — the model's-eye view of tool definitions. Names, descriptions, parameter typing, examples.

**Artifacts** (`memex/artifacts/`) — 3 dated decision records:
1. `2026-04-NN-pivot-react-loop-to-plan-execute.md` — the "we were wrong" record. A design pivot mid-project with reasoning.
2. `2026-04-NN-tool-protocol-decision-record.md` — formal decision record for the tool schema.
3. `2026-04-NN-context-budget-formal-model.md` — the ambitious one. A formal model of context economics referenced by the headline thread.

**Reference notes** (`memex/reference-notes/`) — alongside the existing essays:
1. `agentic-design-vocabulary.md` — named concepts: blast radius, grain size, plan drift, etc. A glossary the threads cite.
2. `claude-api-cheatsheet.md` — practical reference for the cloner.
3. `failure-mode-taxonomy.md` — the named failures from the loop-failure-modes thread, expanded.

**Systems docs** (`docs/systems/`) — 3 "how it works" docs:
1. `tinyagent-architecture.md` — overview, module map, setup instructions.
2. `tool-protocol.md` — the tool schema and its justification.
3. `context-manager.md` — how the context-budget manager works.

**Light threads** (`memex/threads/`) — 3-4 lightweight reference threads:
- `streaming-vs-batched-output.md`
- `prompt-caching-tradeoffs.md`
- `history-compaction-strategies.md`
- `subprocess-sandboxing-notes.md`

### Phase D — Run the machinery for real

Everything so far was authoring. This phase proves the apparatus works *on this Memex*.

1. `python .memex/scripts/graph_health.py --json > docs/reports/$(date +%Y-%m-%d)-graph-health.json` (plus a markdown render if the script supports it). Commit.
2. `python .memex/scripts/crawler.py --dry-run > docs/reports/$(date +%Y-%m-%d)-crawler-dryrun.md`. Commit.
3. **Enforcer audit** — run a different model (Codex, Gemini, or Sonnet) against this Memex per `.memex/procedures/enforcer-audit.md`. Write the report to `docs/reports/$(date +%Y-%m-%d)-enforcer-audit.md`. **This must be a different model than the one authoring the content.** Same-model review is not enforcement (per the constitution). The PI may need to run this step externally if you're Opus-authoring and need a Sonnet/Codex auditor.
4. `python .memex/scripts/generate_wiki.py` and `generate_markdown.py` → regenerate `wiki/Main_Page.md` and friends. Commit.
5. Regenerate `wiki/thread-graph.png` if the toolchain supports it.

### Phase E — Polish and PR

1. Delete or update this `session-handoff.md` thread once its work is done. It was scaffolding for the transplant; the live repo shouldn't ship with it. **Convert to an artifact if its historical value is worth preserving** (`memex/artifacts/2026-04-10-public-release-transplant.md`), otherwise remove it and the cross-references to it.
2. Clear `memex/inbox.md` of the seed item pointing at this thread.
3. Fresh-clone test: in a separate directory, `git clone` the repo, run `python .memex/scripts/memex.py status`, verify the CLI works from a clean checkout.
4. Link-integrity check: grep for broken cross-references in threads. The artifacts under `memex/artifacts/` and the reports under `docs/reports/` reference paths that changed during the move (`active-threads/essay-*` → `reference-notes/essay-*`) — these are historical documents and **should not be edited** (they were true when written), but broken links in *new* content must be fixed.
5. Commit a clean final state on `public-release-prep`. Open a PR `public-release-prep → dev`. PI reviews and merges. Then `dev → main` when the PI is satisfied.

## Constraints and Reminders

- **Runnability is secondary.** Design quality and update-ability are primary. `tinyagent` is a *design artifact*. Skeleton code with TODOs is acceptable and even preferred where it makes the Memex threads richer.
- **Fictional PI is Ren.** Do not use real names. The README can note that the Memex content is an illustrative instance.
- **Never edit historical artifacts or reports** except to fix purely mechanical cross-reference breakage. They were true when written.
- **Active-threads budget**: ≤ 60 lines per thread; total always-loaded content under ~400 lines. If a thread overflows, compress or split per `.memex/procedures/thread-lifecycle.md`.
- **Heritage essays are NOT working threads.** Don't update them, don't cross-reference them from the tinyagent project threads as if they were peers. Treat them as reference material.
- **Capture bias applies.** If the PI raises a topic during Phase B/C/D, capture it into inbox or a thread. Don't stop to organize.
- **Commit draft discipline.** Every substantive change gets a bullet in `memex/commit_draft.md` with decision tags and `-<agent>` attribution before committing.

## Connections

→ [Document Routing Policy](../../.memex/policies/document-routing.md) — where does this idea go?
→ [Thread Lifecycle Procedure](../../.memex/procedures/thread-lifecycle.md) — promotion, demotion, compression
→ [Enforcer Audit Procedure](../../.memex/procedures/enforcer-audit.md) — how Phase D step 3 works
→ [Session Lifecycle Procedure](../../.memex/procedures/session-lifecycle.md) — how to open and close sessions
→ [Memex Architecture Essays](../reference-notes/) — heritage content from before the public release pivot; read for architectural context
→ [Constitution (core)](../../constitution-core.md) — the portable governance
→ [Constitution (domain)](../../constitution.md) — this instance's rules

## Next Up

- Phase A: orient. Read constitution, verify CLI, read this thread fully.
- Phase B: scaffold `tinyagent/` code.
- Phase C: populate the Memex (headline thread first — gate the rest on its quality).
- Phase D: run the machinery.
- Phase E: polish, bootstrap test, PR.
