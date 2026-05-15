# Concierge Responses

When the Memex is working well, the PI should feel like they're working with someone who deeply knows the project, the process, and the context. That means the agent handles orientation questions naturally — not with a docs dump, but with a concise, grounded answer that draws from the knowledge layer.

This maps common PI questions to where the answers live and how to frame them.

## How to Use This

When the PI asks a question that matches a pattern below, read the referenced files and synthesize a response. Don't recite file contents — answer like a colleague who knows everything. Be concise. Offer to go deeper if the PI wants.

---

## Orientation and Workflow

### "What happened last session?" / "Catch me up"

**Draw from**: `commit_draft.md`, `inbox.md`, `whiteboard.md`, `issues.md`

**Frame as**: Summarize commit draft entries (what changed, who decided), any new inbox items, unresolved whiteboard findings, and open issues. The goal: make the PI feel like the conversation never ended.

### "What should I work on?" / "Where do I start?"

**Draw from**: `roadmap.md`, `inbox.md`, `issues.md`, `commit_draft.md`

**Frame as**: Check roadmap for current priorities, issues for blockers, inbox for captured ideas. Suggest the highest-priority item. Ask if priorities have shifted.

### "What are we building?" / "What's the mission?"

**Draw from**: `mission.md`

**Frame as**: The mission in the PI's own words. If stale or vague, flag it and offer to refine together.

### "What's the priority?" / "What's next?"

**Draw from**: `roadmap.md`

**Frame as**: Present top items by status. Suggest the next concrete step for the highest-priority active item.

---

## Research and Knowledge

### "What do we know about [topic]?"

**Draw from**: `active-threads/`, `threads/`, `artifacts/` — search by title, tags, and cross-references

**Frame as**: Start with the thread summary (2-4 sentences). Offer to go deeper into the thread or follow connections. If no thread exists, say so and suggest creating one if the topic has momentum.

### "What connects to [topic]?"

**Draw from**: Thread cross-references, artifact connections

**Frame as**: Follow the annotated links. Show the PI the connection graph outward from their topic. Cross-references explain *why* the link exists — surface that.

### "Create a thread for this" / "Let's capture this"

**Draw from**: `active-threads/_TEMPLATE.md` (if exists), constitution thread rules

**Frame as**: Create the thread with a Summary and Connections section. Place in `active-threads/` if it has current momentum, `threads/` if it's reference. The test: "if we came back to this next week, would this help us resume?"

### "This thread is getting long" / "This should be an artifact"

**Draw from**: Constitution compression rules (60-line trigger)

**Frame as**: If over 60 lines, either split (distinct subtopics that stand alone) or move depth to an artifact and leave a stub. Preserve cross-references. Nothing is deleted — depth moves, it doesn't disappear.

---

## Codebase (for coding projects)

### "How does [module] work?" / "Explain [this code]"

**Draw from**: Relevant charter(s) via `charters/INDEX.md`, then the actual code

**Frame as**: Start from the charter — what the module owns, doesn't own, key functions, data flows. Then go to code for specifics. Charter gives the overview; code gives the detail.

### "Is it safe to change [X]?" / "What would break?"

**Draw from**: Charter `←`/`→` annotations, `cross-cutting.md` TRIPWIREs

**Frame as**: Check callers, callees, tripwires. Give a concrete blast radius. Suggest an enforcer review if the change touches cross-cutting patterns.

### "Run the enforcer" / "Check this"

**Draw from**: `procedures/enforcer-review.md`, enforcer configuration

**Frame as**: Run the appropriate enforcer level. Present findings with context. Ask the PI what to do. Do not start fixing things.

---

## The Memex Itself

### "What is this memex folder?"

**Frame as**: The Memex is a persistence layer — it makes the AI feel like it was there yesterday. Threads capture topics, artifacts hold depth, the constitution governs how it all works. It grows by being used, not by being configured. Keep it to 2-3 sentences unless they want more.

### "Why do we do it this way?"

**Draw from**: `constitution-core.md`, `charters/README.md`

**Frame as**: The problem — context is lost between sessions, knowledge rots without governance, and AI generates from stale assumptions without a maintained map. The Memex solves this structurally. Frame in terms of what it does for *this PI on this project*.

### "Can I change the process?"

**Frame as**: The PI is the authority. The constitution is a starting point. If something isn't working, change it. The only things that truly matter: the session opening (continuity), capture bias (don't lose thoughts), and the charter loop (for coding projects). Everything else is in service of those. Suggest capturing the change in the constitution so the next session respects it.

---

## Where Things Go

### "Where should I put this?"

**Draw from**: Constitution file purposes table

| What you have | Where it goes |
|---|---|
| A quick idea or observation | `inbox.md` |
| A decision with rationale | Thread |
| Deep research or analysis | `artifacts/` |
| A repeatable workflow | `procedures/` |
| A code-level fact | `charters/` |
| A project direction change | `mission.md` |
| A priority shift | `roadmap.md` |
| A bug or blocker | `issues.md` |
| A recurring rhythm | `patterns.md` |
| A reference or cognitive aid | `reference-notes/` |
| Session change or decision | `commit_draft.md` |

### "What's the difference between a thread and an artifact?"

**Frame as**: Size and depth. Threads are lightweight (5-20 lines) — a topic with a name, a summary, connections. Artifacts are deep storage — design docs, research, anything that needs space. If a thread grows past ~60 lines, it probably wants to be an artifact.

### "Active thread vs. regular thread?"

**Frame as**: Temperature. Active threads are loaded every session — they're what you're working on this week (5-8 max). Regular threads are reference — loaded on demand when a cross-reference leads there. When a topic cools off, demote it from active to regular. When it heats up, promote it.

---

## Tone Guidance

- **Be a colleague, not a manual.** "The auth redesign thread covers this — here's the key decision" not "According to active-threads/auth-redesign.md..."
- **Lead with the answer, then offer depth.** "That decision was made in March. Want me to pull up the full rationale?"
- **Ground everything in the knowledge layer.** If you're answering from training data rather than the Memex, say so. The PI should trust that answers come from the actual project state.
- **Flag gaps.** If the PI asks about something the Memex doesn't cover, say "we don't have a thread on this — should we capture it?" That's the system working.
