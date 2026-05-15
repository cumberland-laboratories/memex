# Memex Start-Up — Concierge Bootstrap

**When to use**: First session on a fresh Memex, OR when identity.md still has bracket placeholders and active-threads/ is empty.

This procedure guides the PI through populating their Memex. The goal is not configuration — it's a conversation that produces a working knowledge layer. The Memex grows by being used, not by being set up.

## The Concierge Approach

Don't dump forms on the PI. Have a conversation. Ask questions. Populate files from the answers. The PI should feel like they're talking about their project, not filling out templates.

## Step 1: Who Are You?

Ask the PI about themselves — not a biography, just enough to calibrate:
- What do you do? (role, domain, experience level)
- How do you like to work? (fast iterations? careful planning? morning person?)
- What interests you beyond this project?

Populate `identity.md` from the conversation.

## Step 2: What Are We Building?

Ask about the project:
- What is this project? (→ mission.md)
- What problem does it solve? Who is it for?
- What are the current priorities? (→ roadmap.md)
- What's in scope and what's deliberately out of scope?

Populate `mission.md` and `roadmap.md`.

## Step 3: Is There Code?

If the project has a codebase:
- What's the tech stack?
- How is the code organized?
- Walk the directory structure, identify module boundaries (3-8 charters typical)
- Generate skeleton charters using `charters/_template.md` as format reference
- Build `charters/INDEX.md` mapping code paths → charter files
- Write the cross-cutting charter (most important — multi-module patterns, TRIPWIREs)

Study the worked example first: → [reference-notes/example-tinyagent-instance.md](reference-notes/example-tinyagent-instance.md) (or check out git tag `v1-tinyagent-example` for the full populated state).

Charter notation reference: → [charters/README.md](charters/README.md)

If the project is research/knowledge work (no codebase), skip charters entirely. The Memex works without them — threads, artifacts, and the knowledge graph are the primary surface.

## Step 4: What's Already in Flight?

Ask what's already underway:
- Any active topics with momentum? (→ create threads in active-threads/)
- Any decisions already made that shouldn't be revisited? (→ thread or artifact)
- Any recurring obligations or patterns? (→ patterns.md)
- Anything captured elsewhere (notes, docs, prior conversations) to ingest? (→ inbox.md)

Don't force threads. Let them emerge from the conversation. The test: "if we came back to this next week, would this thread help us resume?"

## Step 5: Verify

After bootstrap, check:
- [ ] identity.md populated (at least basics and working style)
- [ ] mission.md populated (what, why, scope)
- [ ] roadmap.md has at least 2-3 priorities
- [ ] If code exists: charters bootstrapped, INDEX.md populated, cross-cutting charter exists
- [ ] The PI has reviewed and corrected anything off

## What "Done" Looks Like

The Memex is bootstrapped when the next session can follow the normal opening:
1. Read constitution-core.md + constitution.md
2. Read mission, roadmap, identity
3. Check inbox, issues, commit_draft
4. The PI feels like the conversation never ended

This might take one session or several. There's no rush. A half-populated Memex that accurately reflects reality is better than a fully-populated one that the PI didn't verify.

## Reference

→ [Constitution Core](../constitution-core.md) — the portable governance layer
→ [Constitution](../constitution.md) — project-specific rules
→ [Charter Format](charters/README.md) — notation, philosophy, anti-patterns
→ [Example Instance](reference-notes/example-tinyagent-instance.md) — what a mature Memex looks like
