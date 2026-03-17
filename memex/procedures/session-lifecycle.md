# Procedure: Session Opening

## Steps

1. Check `memex/inbox.md` for captured thoughts. Triage each entry: route to an existing thread, create a new lightweight thread, or surface to the human for discussion. Clear the inbox after processing.
2. Check `memex/patterns/` (rhythms) for any payments, birthdays, or renewals due within the advance-notice window (default: 2 days from today's date).
3. Check `memex/audit-tracker.md` for open findings. Don't recite them — just be aware.
4. Read the active threads. Check for **Next Up** items first (explicit intent). If none, use `last-touched` frontmatter to identify the most recently active thread.
5. Greet formally with time of day and first name — e.g., *"Good morning."* Then surface naturally — upcoming obligations, inbox triage results, most relevant thread or Next Up item.
6. If there are multiple Next Up items, mention the most recent or most specific one. Don't list them all like a menu.
7. If there's nothing queued, no inbox items, and no upcoming payments, just say hello — don't fabricate continuity.

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
5. **Commit draft**: Append a summary of session changes to `commit_draft.md`.

This is lightweight — not a ceremony. If the session ends abruptly (human closes the window), the next session-open triage catches anything that was missed.
