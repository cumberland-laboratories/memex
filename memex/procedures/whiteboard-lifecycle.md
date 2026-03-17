# Procedure: Whiteboard Lifecycle

The whiteboard is a temporary shared coordination surface for cross-model and human-model work. It is not a thread, artifact, inbox, or transcript. Use it when operators need a shared place to think together before routing the result to its permanent home.

## When to Open

Open the whiteboard when:

1. The adjudicator explicitly asks for it (`put that on the whiteboard`, `whiteboard this`, `open a whiteboard for this`)
2. A subproblem needs multi-operator exchange and would be awkward to route directly into a thread
3. The cost of cross-model copy-paste is becoming higher than the cost of maintaining a temporary shared surface

Do **not** open the whiteboard for:

- single thoughts better suited to `inbox.md`
- on-topic discussion that should update the current thread directly
- routine chat that does not need multi-operator coordination

## File

Use `memex/whiteboard.md`.

Single whiteboard only in the first implementation. If concurrency becomes necessary later, move to date- or topic-prefixed files.

## Opening Format

If the file is empty, initialize it like this:

```md
# Whiteboard

Temporary multi-operator working surface. Append-only while live. Route entries to a thread, artifact, inbox, or discard, then clear.

## YYYY-MM-DD — topic
```

If the file already exists and is active, append a new dated section instead of overwriting.

## Entry Format

Each entry must include:

- sequential `#N`
- speaker label in brackets
- optional `RE:#N` reply reference
- body text

Example:

```md
#3 [GPT-5 Codex] RE:#1, #2
   Agreed. MemFS is plumbing, not the product surface.
```

## During Use

1. Append only. Do not edit or rewrite previous entries.
2. Use explicit `RE:#N` references after the first entry.
3. Keep entries concise; the whiteboard is a working surface, not a long-form note.
4. Only shared items go in. The whiteboard is not a transcript.

## Routing

When the adjudicator issues a routing command:

1. Identify the referenced entries.
2. Resolve the destination:
   - thread
   - artifact
   - inbox
   - discard
3. Perform the routing.
4. If the whiteboard remains open, append a routing note such as:
   - `-> routed to threads/foo.md`
   - `-> captured to artifacts/YYYY-MM-DD-bar.md`
   - `-> sent to inbox`
   - `-> discarded`

## Closing

Close the whiteboard when:

1. The adjudicator says to clear it
2. The current subproblem has been fully routed
3. Session close arrives and no further whiteboard work is needed

Default close behavior:

- unresolved actionable items -> `inbox.md`
- preserved multi-entry exchange -> artifact
- durable conclusions -> thread
- exploratory chatter with no reuse value -> discard

After routing, clear `memex/whiteboard.md` back to its template state.

## Failure Modes

- **Rot**: if never cleared, it becomes a second inbox
- **Transcript drift**: if everything gets copied in, it becomes noise
- **Silent permanence**: if models route automatically without adjudicator control, the staging boundary collapses
- **Overuse**: if used for every small thought, it replaces the inbox and threads badly

## Key Principle

The whiteboard is a coordination layer, not a memory layer.
