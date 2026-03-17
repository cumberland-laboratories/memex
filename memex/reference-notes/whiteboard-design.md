# Whiteboard Design

Lightweight shared communication surface for cross-model and human-model working conversation. Not a thread (curated knowledge), not an artifact (deep record), not the inbox (capture buffer). The whiteboard is a whiteboard — where operators think together before ideas are routed to their permanent home.

## Why

Currently, cross-model communication requires the adjudicator to copy-paste between sessions. This makes the human the router, stenographer, and context packager. The whiteboard eliminates that by giving all operators a shared surface they can read and append to.

## Format

```
## YYYY-MM-DD

#1 [Alan]
   Can we look at the Letta MemFS feature more closely?
   I want to know how close it really is.

#2 [Claude Opus 4.6] RE:#1
   Checked the docs. MemFS is git-backed markdown but it's
   developer infrastructure — you write code to define memory
   blocks. Not a working system you talk to. Different layer.

#3 [GPT-5 Codex] RE:#1, #2
   Agreed. MemFS is plumbing. The Memex is the house. But worth
   noting in the competitive landscape — it shows convergent
   evolution toward the same storage instinct.

#4 [Alan] RE:#3
   Good. Update the landscape doc with that nuance.
```

## Invariants

These properties must remain true or the whiteboard turns into a sloppy second thread.

- **Append-only while live.** Existing entries are never edited during use. Corrections are appended as new entries.
- **Every entry is addressable.** Sequential `#N` numbering, unique within the current whiteboard session.
- **Every entry has provenance.** Speaker label on every entry: human name or model/version.
- **Replies are explicit.** `RE:#N` (or `RE:#N, #M`) on every response after the first. No ambiguous adjacency.
- **The whiteboard is temporary.** It is a staging surface, not a durable knowledge store.
- **Nothing becomes permanent implicitly.** Routing requires adjudicator instruction or explicit end-of-session cleanup logic.
- **Zero load when unused.** The whiteboard is not part of the always-loaded working set.

## Working Rules

- **Append-only during use.** No editing previous entries. That's where "what are you responding to?" confusion comes from.
- **Numbered comments.** Sequential `#N` on every entry. Never reuse numbers within a whiteboard session.
- **Speaker label.** `[Name]` or `[Model Version]` on every entry. Screenplay format.
- **RE: references.** Every response tags `RE:#N` (or `RE:#N, #M`) to indicate what it's responding to. Supports branching — #6 can reply to #2 while #7 replies to #4.
- **Ephemeral.** The whiteboard gets cleared when its content has been routed — to a thread, an artifact, the inbox, or nowhere. It's a whiteboard, not a record.
- **Not always-loaded.** Checked when the operator mentions it or says "put that in the whiteboard." Zero cost when not in use.
- **Routing on request.** The adjudicator says "route #3 to the competitive landscape thread" or "capture #1-#4 as an artifact." The agent handles it. The whiteboard entry can note where it was routed: `→ routed to threads/competitive-landscape.md`

## Lifecycle

### 1. Open

The whiteboard begins empty or is created on first use for the day.

Recommended header:

```
## YYYY-MM-DD — topic or working label
```

The topic label is optional but useful when one day contains multiple distinct lines of work.

### 2. Append

Any operator can append:

- adjudicator
- chat agent
- enforcer
- future crawler/spider, if explicitly allowed

But appending happens only when the adjudicator requests use of the whiteboard, or when the constitution later grants a model permission to place something there automatically.

### 3. Work

The whiteboard is used for:

- cross-model handoff
- provisional comparisons
- quick back-and-forth on a subproblem
- staging content before deciding whether it belongs in a thread, artifact, or inbox

### 4. Route

Entries are routed to one of four destinations:

- **Thread** — curated knowledge worth preserving in the graph
- **Artifact** — deeper record or clipped multi-entry exchange
- **Inbox** — unresolved but worth keeping for later triage
- **Nowhere** — discard after use

### 5. Close

The whiteboard closes when the adjudicator says to clear it, or at session close if all entries have been routed or discarded.

If entries remain unresolved at close, default rule:

- route unresolved actionable items to the inbox
- discard pure exploratory chatter unless explicitly preserved

The whiteboard is then cleared.

## Routing Procedure

When the adjudicator issues a routing command, the agent:

1. Identifies the referenced entries (`#3`, `#1-#4`, etc.)
2. Resolves the destination: thread, artifact, inbox, or discard
3. Performs the routing
4. Adds a routing note to the whiteboard entry if the whiteboard is still open
5. Preserves graph integrity if a thread/artifact is created or updated

Examples:

- `Route #3 to the competitive-landscape thread.`
- `Capture #1-#4 as an artifact.`
- `Put #7 in the inbox.`
- `Discard #9 and clear the whiteboard.`

## Failure Modes

### Whiteboard rot

If the file is not cleared, it becomes a second inbox or a low-quality thread.

Mitigation:
- explicit close step
- unresolved items routed to inbox
- discard by default unless preservation is requested

### Ambiguous replies

If entries do not use `RE:#N`, the whiteboard devolves into an ordinary transcript.

Mitigation:
- require explicit references after the first entry

### Silent permanence

If models can route content into threads automatically without clear instruction, the whiteboard loses its role as a staging surface.

Mitigation:
- adjudicator-triggered routing by default
- future automation must be explicit and governed

### Overuse

If every side thought goes into the whiteboard, it becomes an attractive nuisance.

Mitigation:
- inbox for single thoughts
- whiteboard for actual multi-party working exchange

### Conflation with transcript

If operators treat the whiteboard as a full session log, it becomes noisy and expensive.

Mitigation:
- keep it intentional
- only shared items go in
- no expectation of completeness

## What this is not

- Not a thread. Threads are curated knowledge that persists. The whiteboard is working conversation that gets cleared.
- Not an artifact. Artifacts are deep records. The whiteboard is ephemeral.
- Not the inbox. The inbox is zero-friction capture for single thoughts. The whiteboard is multi-party conversation.
- Not a transcript. The whiteboard captures what operators want to share, not everything that was said in a session.

## Trigger

The adjudicator says any of:
- "Put that on the whiteboard"
- "Can we place that in the research chat"
- "Add to whiteboard"
- "Whiteboard this"

The agent appends the relevant content with the next sequential number, speaker label, and RE: reference.

Future trigger worth considering:

- "Open a whiteboard for this"

That would make the start of whiteboard mode explicit for a subproblem.

## File location

`memex/whiteboard.md` — single file, cleared after routing. If multiple concurrent whiteboards are needed later, date-prefix them. Start with one.

## First Implementation Boundary

The first version should stay deliberately small:

- one file
- manual open/append/route/clear
- no automatic routing
- no concurrent whiteboards
- no background operator writes unless explicitly requested

The goal is to prove the missing layer exists and is useful, not to build a full coordination subsystem on day one.
