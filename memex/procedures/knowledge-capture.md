# Procedure: Knowledge Capture — Where Things Go

## Context

AI models have built-in memory systems (Claude's `MEMORY.md`, Gemini's memory, Copilot's context, etc.). These are designed to persist information for a single user on a single model. They are **invisible** to other users and other models working in the same repo.

The Memex is designed to work across multiple users and multiple AI models. The `memex/` folder is the shared knowledge layer. If project knowledge ends up in a model's personal memory instead, it creates information silos that defeat the purpose.

## The Decision Rule

When you learn something worth remembering, ask: **"Is this about the project or about the person?"**

### Goes in `memex/` (shared, visible to all)

- Architectural decisions and their rationale
- Code invariants, constraints, tripwires
- Module boundaries and ownership (charters)
- Research findings, hypotheses, experimental results
- Bug context, incident notes, post-mortems
- Project priorities, milestones, deadlines
- Patterns that span modules or topics
- Anything a different user or model would need to work here effectively

**Where in `memex/`:**

| What you learned | Where it goes |
|---|---|
| Something about a function or module | Charter update |
| A decision with rationale | Thread in `active-threads/` or `threads/` |
| A pattern or invariant spanning modules | Cross-cutting charter |
| An idea or observation (unstructured) | `inbox.md` |
| A priority shift | `roadmap.md` |
| A project direction change | `mission.md` |
| A recurring obligation or rhythm | `patterns.md` |
| A bug or blocker | `issues.md` |
| Deep research, design doc, or analysis | `artifacts/` |
| A reference, vocabulary, or cognitive aid | `reference-notes/` |
| A session change or decision | `commit_draft.md` |

### Goes in model memory (personal, per-user)

- The user's communication preferences (terse vs. verbose, etc.)
- The user's role and expertise level
- Workflow habits specific to one person
- Editor or tooling preferences

### When in doubt

Put it in `memex/`. A redundant note in `inbox.md` costs nothing. Knowledge trapped in one model's memory is invisible and eventually lost.

## Common Mistakes

**Saving a PI decision to memory instead of a thread.** The next model won't know about it. The decision will be relitigated.

**Saving a tripwire to memory instead of a charter.** Tripwires protect everyone. A tripwire only one model knows about protects no one.

**Saving project context to memory instead of `mission.md` or `roadmap.md`.** This creates drift — different models develop different understandings of what the project is.
