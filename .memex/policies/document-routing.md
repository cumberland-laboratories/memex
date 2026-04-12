# Policy Draft: Document Routing — Where Does This Go?

Draft policy for `.memex/policies/` — the concierge's decision tree for routing content to the right document type. This is the most common judgment call the agent makes, and getting it wrong degrades the knowledge graph.

## The Core Question

Something came up in conversation. Where does it go?

## Decision Tree

### Step 1: Is it a fleeting thought or a structured idea?

**Fleeting** → `memex/inbox.md`. Don't organize it. Don't route it. Just capture it. One line. Triage later. The cost of losing it is higher than the cost of triaging it tomorrow.

**Structured** → continue to Step 2.

### Step 2: Does it have momentum — will we come back to this?

**No** — it's a fact, a definition, a framework, a cognitive aid that might be useful someday but isn't being actively worked. → `memex/reference-notes/`. It sits on the shelf until someone needs it.

The test: *you don't sit down to work on a reference note. You pull it off the shelf mid-task because you need it right now, then put it back.*

**Yes** — it's a topic with energy, open questions, a next step. → `memex/active-threads/` (or `memex/threads/` if it's lightweight). Continue to Step 3 for related outputs.

### Step 3: Has the idea stabilized into "how something works"?

**Not yet** — it's still evolving, being debated, has open questions. → stays as a **thread**. Threads capture momentum. Let it develop.

**Yes** — the design has settled, it describes a working subsystem or a stable concept. → `docs/systems/`. A living document that is always current. "If I'm wrong, that's a bug — fix me."

The test: *would someone ask "how does X work?" and expect this document to be the current answer?*

### Step 4: Is it a record of what happened or what was decided?

**A point-in-time record** — what we learned, what we tried, what we decided, what someone reviewed. → `memex/artifacts/`. Date-prefixed. Effectively immutable. "I was true when written."

This includes:
- Paper reviews
- Experiment results
- Dead ends (we tried X, it failed because Y)
- Conversation clips (`[save]` or `[clip]`)
- Archived documents (old constitutions, migrated charters)
- Competitive analyses, research syntheses

The test: *would editing this document be rewriting history?*

### Step 5: Is it a frozen judgment or audit?

**An assessment at a point in time** — enforcer audit, crawler report, design review, health check. → `docs/reports/`. Immutable. May be superseded by later reports but never edited.

The test: *this document says "the graph scored 76 on March 22." That's a fact about March 22, not a fact about today.*

### Step 6: Is it a step-by-step recipe?

**Executable steps for a Memex operation** (session opening, thread lifecycle, wiki generation) → `.memex/procedures/` (core, portable).

**Executable steps for THIS project** (how to run the experiment, how to submit the paper, how to deploy the app) → `memex/procedures/` (project-specific).

The test: *does this document say "do this, then this, then this"?*

### Step 7: Is it operational wisdom — how to think, not what to do?

**Guidelines for how the agent should behave** — when to suggest a spawn, how to detect scope drift, how to recognize a stale thread, how to talk to a mathematician vs. an experimentalist. → `.memex/policies/`.

The test: *this document makes the agent better at its job, but it's not a step-by-step recipe. It's judgment, not procedure.*

## Quick Reference

| What it is | Where it goes | The test |
|---|---|---|
| A fleeting thought | `inbox.md` | Would I lose this if I don't write it down now? |
| A cognitive aid / framework | `reference-notes/` | Do I reach for this mid-task, not work on it? |
| A topic with momentum | `active-threads/` or `threads/` | Will we come back to this next week? |
| How a subsystem works (stable) | `docs/systems/` | Would someone ask "how does X work?" and expect this answer? |
| A historical record | `artifacts/` | Would editing this be rewriting history? |
| A frozen assessment | `docs/reports/` | Is this a fact about a specific date? |
| Steps for operating the Memex | `.memex/procedures/` | Is this "do this, then this" for any Memex? |
| Steps for this project | `memex/procedures/` | Is this "do this, then this" for THIS project? |
| Agent judgment guidelines | `.memex/policies/` | Does this make the concierge better, not the project? |

## Edge Cases

**A design note that's still evolving**: starts as a reference note (cognitive aid consulted during design work), promotes to a systems doc when the design stabilizes and becomes "how it works."

**A thread that cooled off**: demote to `threads/` (lightweight stub with cross-references). If it heats up again, promote back. Never delete.

**A thread that became historical**: the work is done, the thread is now a record of what happened. Consider converting to an artifact (date-prefixed, immutable).

**An artifact with ongoing relevance**: don't promote it to a thread. Instead, create a thread that references the artifact. The artifact stays immutable; the thread captures new momentum.

**A conversation worth saving verbatim**: `[clip]` → artifact with `clip: true`. No summary, no synthesis. The raw exchange is the value.

## Connections

→ [Thread Lifecycle Procedure](../procedures/thread-lifecycle.md) — promotion, demotion, splitting rules
→ [Constitution (core)](../../constitution-core.md) — the authority this policy serves
→ [Constitution (domain)](../../constitution.md) — instance-specific conventions
