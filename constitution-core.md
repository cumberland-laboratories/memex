# Memex — Core Constitution

This is the portable governance document for any Memex-powered project. It defines the machinery: roles, structure, operating levels, session opening, thread lifecycle, and conventions. Domain-specific rules live in `constitution.md` (the project's own layer).

## What This Is

This repo is a persistence layer — it makes the LLM feel like it was there yesterday. The Memex is a small-world network of cross-referenced threads, not a hierarchical index. Navigate by entering any node and following links.

## Roles

| Role | What it does | Who runs it |
|------|-------------|-------------|
| **PI (principal investigator)** | Holds mission, taste, and architectural coherence. Adjudicates all decisions — resolves tradeoffs the models cannot legitimately resolve on their own. Full access. | Human |
| **Chat agent** | Talks to the human. Reads and writes the Memex in-session — updates threads, creates artifacts, compresses and rotates. | Claude Code (primary session) |
| **Enforcer** | Audits the Memex (read-only) and produces reports and documentation renders. Does not edit Memex files. Must be a different model. | Different model (e.g., Sonnet checking Opus's work) |

## Memex Structure

```
.memex/                   ← machinery (portable, upstream-maintained, don't modify)
  roles.yaml              ← role definitions
  policies/               ← concierge wisdom and operational guidelines
  procedures/             ← core Memex operational procedures
  scripts/                ← CLI and tooling
memex/                    ← knowledge graph (navigable, compressed, cross-referenced)
  mission.md              ← what we're building and why (always loaded)
  roadmap.md              ← feature roadmap (always loaded)
  issues.md               ← active bugs, blockers, known fragilities (always loaded)
  identity.md             ← stable traits, background, persistent interests (always loaded)
  inbox.md                ← zero-friction capture (always checked at session open, then cleared)
  active-threads/         ← current topics, 5-8 files (always loaded, compression-budgeted)
  threads/                ← lightweight reference threads (NOT always loaded, navigated via links)
  patterns/               ← recurring rhythms (always loaded)
  artifacts/              ← deep records, synopses, reference material (NOT always loaded)
  vault/                  ← external source files (gitignored, referenced by artifacts)
  procedures/             ← project-specific workflows (organic, PI-owned)
  reference-notes/        ← cognitive aids, vocabulary, frameworks (consulted situationally)
  commit_draft.md         ← session change log, used as commit message source (cleared after commit)
docs/                     ← project documentation (living, can be long, structured for reference)
  systems/                ← subsystem documentation: how each piece works, kept current
  reports/                ← enforcer audits, crawler reports (dated snapshots)
  wiki/                   ← rendered output from wiki generators
```

**Navigation**: No central index — the graph is the index. Enter through active threads, follow cross-references.

**Compression rule**: Always-loaded files should stay under 400 lines total. Depth lives in threads/, artifacts/, and cross-references.

**Graph connectivity**: An invariant, not a best-effort property. Every operation must preserve all cross-references.

## Operating Levels

Every message from the human operates at one of two levels:

| Level | Signal | What the agent does |
|-------|--------|--------------------|
| **Content** | `*c` prefix (or no prefix in user mode) | Use the Memex as infrastructure — read threads, capture ideas, update hits, create artifacts. The system is furniture. |
| **Meta** | `*m` prefix (or no prefix in designer mode) | Operate *on* the Memex itself — modify the constitution, restructure, write procedures. The system is the object of work. |

### Operating Mode

The default level is set by `operating-mode:` in `identity.md` frontmatter:

| Mode | Default level | Override |
|------|--------------|----------|
| `designer` | Meta | `*c` prefix switches to content |
| `user` | Content | `*m` prefix switches to meta |

**Capture bias**: At the content level, when a conversation introduces a topic with enough momentum for a thread, capture it. Don't ask permission. A lost thought is worse than a pruned thread. The test: "if we came back to this next week, would this thread help us resume?"

**Identity boundary**: Capture bias applies to threads, not to identity.md. Interest is thread data. Self-disclosure is identity data.

## Session Opening

**Bootstrap detection**: Before running the normal procedure, check these three signals:
1. `memex/identity.md` still contains bracket placeholders (e.g., `[Your role`)
2. `memex/inbox.md` is empty (no captured thoughts)
3. `memex/active-threads/` contains ≤ 2 threads

If all three are true, this is a **first session**. Skip the normal procedure. Greet the human and ask what's on their mind. Read everything silently.

**Normal sessions**: Follow the session-opening procedure: → [session-lifecycle.md](.memex/procedures/session-lifecycle.md). Prefer the CLI path (`python .memex/scripts/memex.py status --full --role <your-role> --format json`). Your role is specified in your entry point file.

Core intent: make the human feel like the conversation never ended.

## Thread Lifecycle

Threads move between three tiers based on activity. Full lifecycle: → [thread-lifecycle.md](.memex/procedures/thread-lifecycle.md)

Key rules:
- Active threads that exceed **60 lines** must be evaluated for splitting.
- Every thread must carry a `## Summary` (2–4 sentences, documentation-entry quality, directly extractable).
- Demotion moves the thread intact — no compression, no stub creation. The thread is already out of the always-loaded set, so its length doesn't cost context tokens. Information loss is never justified by housekeeping.
- Threads where the work is concluded can become artifacts (frozen historical records) instead of demoted threads.
- Cross-references annotate *why* the link exists, not just that it does.

## Enforcer

The enforcer has **read-only access**. It does not edit files — it produces audit reports and documentation renders. The primary agent (with the human present) reviews reports and decides what to act on.

Two enforcer procedures:
- Audit: → [enforcer-audit.md](.memex/procedures/enforcer-audit.md)
- Documentation render: → [wiki-generation.md](.memex/procedures/wiki-generation.md)

## Enforcer Findings Are for the PI

When enforcer findings arrive — whether from the whiteboard, script output, or a CLI review — the agent **presents them to the PI and asks for direction**. The agent does not silently fix findings, dismiss them, or start acting on them unprompted.

The correct behavior:
1. Summarize the findings clearly
2. Offer context: what the finding means, what thread/charter/tripwire is involved, what the options are
3. **Ask the PI what to do next**

The incorrect behavior:
- "The enforcer found X, let me fix that now" → No. The PI decides.
- Silently fixing a finding without mentioning it → No. The PI needs to see it.
- Dismissing a finding as unimportant → No. The PI judges importance.

Enforcer findings are a forcing function for the PI to think deeply. The value isn't just the fix — it's the PI's understanding that comes from deciding *whether* and *how* to fix it.

## Knowledge Lives in the Repo

Many AI models maintain per-user memory systems (Claude's `MEMORY.md`, Gemini's memory, etc.). These are external to the repo and invisible to other users and other models. **Repo knowledge belongs in `memex/`, not in model-specific memory.**

The `memex/` folder is the shared knowledge layer — it works across users, across models, across sessions. If you learn something about this project that would help the next person (or the next model) work here, it goes in the repo:

- Decisions, invariants, patterns → threads, charters, or `inbox.md`
- Project context and priorities → `mission.md`, `roadmap.md`
- Ideas and observations → `inbox.md`

Model-specific memory is fine for user preferences (communication style, workflow habits). But anything about the **project, the research, or how to work in this repo** must be captured in `memex/`. If it's not in the repo, it doesn't exist for the team.

→ [Knowledge Capture Procedure](memex/procedures/knowledge-capture.md)

## Conventions

- **BRANCHING**: Default working branch is `dev`. Merges to `main` are human-authorized.
- **ARTIFACTS**: Deep records in `memex/artifacts/` with date prefixes. Every artifact carries YAML frontmatter: `date`, `depth`, `tags`, `source-thread`, `source`, `summary`. Clips (`clip: true`) omit summary. Procedure: → [clip-to-artifact.md](.memex/procedures/clip-to-artifact.md)
- **VAULT**: External source files in `memex/vault/`, gitignored.
- **PROCEDURES**: Core operational procedures in `.memex/procedures/` (portable). Project-specific workflows in `memex/procedures/` (PI-owned).
- **POLICIES**: Concierge wisdom and operational guidelines in `.memex/policies/`. Consulted by the agent for judgment calls.
- **REFERENCE NOTES**: Cognitive aids in `memex/reference-notes/`. Consulted situationally.
- **CHANGELOG**: Use `git log`. No separate changelog file.
- **COMMIT DRAFT**: Maintain `memex/commit_draft.md`. Each bullet ends with decision tags and attribution: `[#tag1] [#tag2] -agent`. Tags classify decision type. Attribution identifies who decided.
- **ENFORCER INDEPENDENCE**: The enforcer must be a different model than the chat agent. Same-model review is not enforcement.
- **INBOX**: Capture and organization are different operations. Never forced to happen at the same time.
- **DOCS**: Project documentation in `docs/`. Systems docs (always current), reports (frozen snapshots), wiki (rendered output).

## Domain Rules

→ [constitution.md](constitution.md) — project-specific rules, vocabulary, and conventions for this galaxy.
