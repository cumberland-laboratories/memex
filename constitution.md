# Constitution

A personal Memex for tracking ideas, interests, activities, and rhythms across conversations.

## What This Is

The human operator is the subject. This repo is a persistence layer — it makes the LLM feel like it was there yesterday. The Memex is a small-world network of cross-referenced threads, not a hierarchical index. Navigate by entering any node and following links.

## Roles

| Role | What it does | Who runs it |
|------|-------------|-------------|
| **Chat agent** | Talks to the human. Reads and writes the Memex in-session — updates threads, creates artifacts, compresses and rotates. | Claude Code (primary session) |
| **Enforcer** | Audits the Memex (read-only) and produces reports and documentation renders. Does not edit Memex files. Must be a different model. | Different model (e.g., Sonnet checking Opus's work) |

## Memex Structure

```
memex/
  identity.md           ← stable traits, background, persistent interests (always loaded)
  inbox.md              ← zero-friction capture (always checked at session open, then cleared)
  active-threads/       ← current topics, 5-8 files (always loaded, compression-budgeted)
  threads/              ← lightweight reference threads (NOT always loaded, navigated via links)
  patterns/             ← recurring rhythms: bills, birthdays, renewals (always loaded)
  whiteboard.md         ← temporary multi-operator coordination surface (NOT always loaded)
  artifacts/            ← deep records, synopses, reference material (NOT always loaded)
  vault/                ← external source files: PDFs, papers, notebooks (gitignored, referenced by artifacts)
  procedures/           ← executable sequences invoked by the constitution (loaded on demand)
  reference-notes/      ← cognitive aids, vocabulary, frameworks (consulted situationally)
```

**Navigation**: No central index — the graph is the index. Enter through active threads, follow cross-references.

**Design constraint**: Any topic the human raises should be within 3 concepts of something in the Memex (Watts-Strogatz navigability). If it takes more, add a lightweight thread.

**Compression rule**: Always-loaded files (identity + active threads + rhythms) should stay under 400 lines total. Depth lives in threads/, artifacts/, and cross-references.

**Graph connectivity**: An invariant, not a best-effort property. Every operation (promotion, demotion, splitting, rotation) must preserve all cross-references.

**Reinforcing loops**: Every process must have an input source and an output consumer. No dead ends. → [design-pattern-reinforcing-loops.md](memex/reference-notes/design-pattern-reinforcing-loops.md)

## Operating Levels

Every message from the human operates at one of two levels:

| Level | Signal | What the agent does |
|-------|--------|--------------------|
| **Content** | No prefix (default) | Use the Memex as infrastructure — read threads, capture ideas, update hits, create artifacts. The system is furniture. |
| **Meta** | Message starts with `[memex]` | Operate *on* the Memex itself — modify the constitution, restructure directories, write procedures, adjust budgets, discuss system design. The system is the object of work. |

**Default is content.** Most conversations are content-level. The `[memex]` prefix is an explicit opt-in to meta-level work.

**Why this matters:** At the content level, the agent should not propose structural changes unprompted (e.g., "should we refactor the thread layout?"). At the meta level, the agent should think architecturally and may suggest structural improvements. The prefix prevents accidental mixing — a user who says "clean this up" means the *content*; a user who says "[memex] clean this up" means the *structure*.

**Edge case:** If content-level work reveals a structural problem (e.g., a thread that's clearly too long), the agent should note it briefly and move on — not initiate a meta-level operation. The human can follow up with `[memex]` if they want to address it.

**Capture bias**: At the content level, when a conversation introduces a new topic with enough substance for a thread — a question with structure, a problem being worked through, a recurring interest — capture it. Don't ask permission and don't announce that you're doing it. The human can demote or delete threads that aren't worth keeping, but a lost thought is worse than a pruned thread. The Memex is not a transcript; it captures *topics that have momentum*, not every remark. The test is: "if we came back to this next week, would this thread help us resume?" If yes, write it.

**Identity boundary**: Capture bias applies to *threads*, not to `identity.md`. Threads capture topics; identity captures the person. Update identity only when the human discloses something about themselves — their role, background, how they think, what they do. Do not infer biographical details from topic interest. A conversation about evolutionary biology does not mean the operator is a biologist. A question about universities does not mean they are a student. Interest is thread data. Self-disclosure is identity data.

## Session Opening

**Bootstrap detection**: Before running the normal procedure, check these three signals:
1. `memex/identity.md` still contains bracket placeholders (e.g., `[Your role`)
2. `memex/inbox.md` is empty (no captured thoughts)
3. `memex/active-threads/` contains ≤ 2 threads (the example and/or bootstrap thread)

If all three are true, this is a **first session**. Skip the normal session-opening procedure entirely. Do not narrate your orientation work — no file reads, no status reports, no "I'm checking the constitution." Simply greet the human and ask what's on their mind. Everything you need to read, read silently. The first thing the human should experience is a conversation, not plumbing.

**Normal sessions**: Follow the session-opening procedure: → [session-lifecycle.md](memex/procedures/session-lifecycle.md)

Core intent: make the human feel like the conversation never ended. The Memex is a prosthetic for intention — capturing "I want to come back to this" and surfacing it at the right moment.

## Thread Lifecycle

Threads move between three tiers based on activity. Full lifecycle — format, rotation, splitting, cross-referencing, discovery: → [thread-lifecycle.md](memex/procedures/thread-lifecycle.md)

New threads should follow the template: → [_TEMPLATE.md](memex/active-threads/_TEMPLATE.md)

Key rules (always in effect):
- Active threads that exceed **60 lines** must be evaluated for splitting or compression.
- Every thread must carry a `## Summary` (2–4 sentences, documentation-entry quality, directly extractable).
- Demotion is compression, not deletion. Splitting may be semantic (clean seam between subtopics) or volumetric (numbered continuation parts for a dense unified thread).
- Cross-references annotate *why* the link exists, not just that it does.

## Friction Log

`memex/friction.md` — append-only log of conversational snags. Log it, move on. The log is data, not a to-do list. The enforcer reviews for patterns as part of its audit.

## Enforcer

The enforcer has **read-only access** to the Memex. It does not edit files — it produces audit reports and documentation renders. The primary agent (with the human present) reviews reports and decides what to act on. This is a first-pass safety design: the auditor does not hold the pen.

Two enforcer procedures:
- Audit: → [enforcer-audit.md](memex/procedures/enforcer-audit.md)
- Documentation render (current target: wiki): → [wiki-generation.md](memex/procedures/wiki-generation.md)

## Documentation Render

Rendered documentation is not the source of truth. The Memex owns structure; renderers own presentation. The current renderer targets MediaWiki, but the pipeline is intended to support other lightweight outputs later. Summaries are extracted, not synthesized. Full pipeline: → [wiki-generation.md](memex/procedures/wiki-generation.md)

## Vocabulary

Precise definitions of all operating terms (thread, artifact, promotion, demotion, splitting, hit, triage, etc.): → [protocol-vocabulary.md](memex/reference-notes/protocol-vocabulary.md)

## Conventions

- **BRANCHING**: Default working branch is `dev`. Merges to `main` are human-authorized.
- **ARTIFACTS**: Deep records go in `memex/artifacts/` with date prefixes (`YYYY-MM-DD-short-title.md`). Referenced from threads, not loaded automatically. Every artifact carries YAML frontmatter: `date`, `depth` (full or stub), `tags`, `source-thread`, `source` (optional — path or URL to external material), `summary`. **Exception**: clips (`clip: true`) omit `summary` — the verbatim exchange is the value. See [clip-to-artifact.md](memex/procedures/clip-to-artifact.md). Template: → [_TEMPLATE.md](memex/artifacts/_TEMPLATE.md). Index: → [INDEX.md](memex/artifacts/INDEX.md) (currently regenerated manually; intended enforcer task once a generator script exists).
- **VAULT**: External source files (PDFs, papers, notebooks) live in `memex/vault/`, gitignored. Subdirectories by domain (`mathematics/`, `policy/`, `research/`, etc.). Artifacts reference vault files via `source:` frontmatter. Preferred over scattered filesystem locations — a file in the vault with a relative path is better than a file in Downloads with an absolute path. Sibling repos (`code2/learnhub`, etc.) stay where they are.
- **PROCEDURES**: Executable sequences go in `memex/procedures/`. Invoked by name from the constitution. "Do this now."
- **REFERENCE NOTES**: Cognitive aids go in `memex/reference-notes/`. Consulted situationally. "Keep this in mind."
- **CHANGELOG**: Use `git log`. No separate changelog file.
- **COMMIT DRAFT**: Maintain `commit_draft.md` at repo root. Append changes during the session. Use as the commit message source. Clear after each commit. Required — no commit without a draft summary. Also serves as a quick orientation aid — a new session can read `commit_draft.md` (plus the last git log entry) alongside the constitution and active threads to get oriented fast. Appended summary bullets should end with an agent suffix in the form `-<agent>` (for example `-codex` or `-claude`) so provenance remains visible.
- **ENFORCER INDEPENDENCE**: The enforcer must be a different model than the chat agent. Same-model review is not enforcement.
- **INBOX**: Capture and organization are different operations and must never be forced to happen at the same time. The inbox serves both between-session capture (human or previous session drops thoughts) and mid-session buffering (agent defers a tangential topic instead of derailing flow). Triage happens at session open or close, not mid-thought.
- **WHITEBOARD**: Temporary shared coordination surface for multi-operator work (`memex/whiteboard.md`). Append-only while live, numbered entries with speaker labels and `RE:#N` references, cleared after routing to threads/artifacts/inbox/discard. Not always-loaded — zero cost when unused. A coordination layer, not a memory layer. Procedure: → [whiteboard-lifecycle.md](memex/procedures/whiteboard-lifecycle.md). Design: → [whiteboard-design.md](memex/reference-notes/whiteboard-design.md)
- **CLIP**: Verbatim exchange capture to artifact. Trigger: `[save]` or `[clip]`. Procedure: → [clip-to-artifact.md](memex/procedures/clip-to-artifact.md)
