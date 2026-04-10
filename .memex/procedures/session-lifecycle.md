# Procedure: Session Opening

## Steps

### CLI path (preferred — saves ~14 tool calls)

If `.memex/scripts/memex.py` is available, use the CLI for orientation:

1. Run `python .memex/scripts/memex.py status --full --role <your-role> --format json` — one call returns graph health, inbox items, patterns due, and all active threads with summaries and Next Up items. Your role is specified in your entry point file (`CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, or equivalent). Role definitions live in `.memex/roles.yaml`.
2. Read `memex/mission.md` and `operating-mode:` from `identity.md` frontmatter (still needed — the CLI does not yet surface these). If `designer`, default to meta-level. If `user` or absent, default to content-level.
3. Apply prioritization to the CLI output: check for **Next Up** items first (explicit intent). If multiple, surface the most recent or most specific — don't list them like a menu. If none, use `last-touched` to identify the most recently active thread.
4. Greet formally with time of day and first name. Surface naturally — upcoming obligations, inbox triage results, most relevant thread or Next Up item. If there's nothing queued, just say hello.

The CLI provides the *data*. The agent applies the *prioritization*. The CLI state dump is not a transcript to recite — it's orientation material to inform the greeting.

### Manual path (fallback — if CLI is unavailable)

1. Read `memex/mission.md` (what we're building) and `operating-mode:` from `identity.md` frontmatter. If `designer`, default to meta-level (architectural thinking, structural proposals). If `user` or absent, default to content-level (system is furniture). This sets the session's default posture — overridable per-message with `*c` or `*m`.
2. Check `memex/inbox.md` for captured thoughts. Triage each entry: route to an existing thread, create a new lightweight thread, or surface to the human for discussion. Clear the inbox after processing.
3. Check `memex/patterns.md` (rhythms) for any items due within the advance-notice window (default: 2 days from today's date). Skip if not present.
4. Read the active threads. Check for **Next Up** items first (explicit intent). If none, use `last-touched` frontmatter to identify the most recently active thread.
5. Greet formally with time of day and first name — e.g., *"Good morning."* Then surface naturally — upcoming obligations, inbox triage results, most relevant thread or Next Up item.
6. If there are multiple Next Up items, mention the most recent or most specific one. Don't list them all like a menu.
7. If there's nothing queued, no inbox items, and no upcoming rhythms, just say hello — don't fabricate continuity.

## Mid-Session CLI Usage

During the session, prefer CLI commands over raw file operations when available:

- **Search**: `python .memex/scripts/memex.py search "<query>"` — one call instead of multiple Grep passes. Use `--format json` for structured results.
- **Read a thread**: `python .memex/scripts/memex.py read thread <name>` — renders the thread with summary, connections, and Next Up. Fuzzy name matching. Use `--section` for specific sections of long documents.
- **Read a system doc**: `python .memex/scripts/memex.py read system <name>` — same pattern, for `docs/systems/`.
- **Check status mid-session**: `python .memex/scripts/memex.py status` — quick health check without reading multiple files.

Direct file reads and edits are still appropriate for write operations (updating threads, editing frontmatter, adding connections) until write-side CLI commands are shipped.

## Mid-Session Inbox (during session)

During conversation, topics will emerge that deserve capture but would interrupt flow to route properly — a tangential idea, a connection worth recording, a to-do that doesn't belong in the current thread. **Do not stop to organize.** Append it to `memex/inbox.md` and continue the conversation.

The inbox is a buffer, not a destination. Entries accumulate during the session and get triaged at session close or next session open — never mid-thought. This keeps the conversation focused on thinking, not housekeeping.

**When to use**: The agent notices something worth capturing that isn't part of the current discussion. The cost of routing it now (finding the right thread, updating cross-references, checking compression) exceeds the cost of writing one line in the inbox.

**When NOT to use**: The topic *is* the current discussion. If you're already talking about it, update the thread directly. The inbox is for things that would derail, not for things that are on-topic.

## Thread Hygiene (during session)

- **last-touched**: Update the date in frontmatter when an active thread is substantively discussed.
- **Next Up**: Write a `## Next Up` section when a session ends with clear forward intent.
- **Hit counting**: Increment `hits:` by 1 when a thread is a focus of discussion. Do not increment for incidental mentions. Update in batch at natural breakpoints — end of a topic, session close. Low-energy operation; do not interrupt conversational flow.

## Session Close

When a session ends naturally or the human signs off:

1. **Triage inbox**: If entries accumulated during the session via mid-session capture, route each one now — to an existing thread, a new lightweight thread, or flag for next session. Clear after processing.
2. **Hit counts**: Batch-update any outstanding `hits:` increments not yet written.
3. **last-touched**: Update frontmatter dates for any active threads substantively discussed.
4. **Next Up**: If the conversation ended with clear forward intent, write or update `## Next Up` on the relevant thread(s).
5. **Commit draft**: Append a summary of session changes to `memex/commit_draft.md`.

This is lightweight — not a ceremony. If the session ends abruptly (human closes the window), the next session-open triage catches anything that was missed.
