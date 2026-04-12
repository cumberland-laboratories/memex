# Inbox

Drop anything here. No formatting needed. The chat agent triages at session open.

---

- Should tool schemas carry example invocations? The current bare JSON Schema is correct but gives Claude no usage hints. Could add an `examples` key to each tool definition — but that burns context tokens on every turn. Tradeoff unclear.
- prompt caching for the system prompt would cut costs on long sessions but
- The context-budget thread needs a concrete answer on token accounting: do we count tool-result tokens against the budget at insertion time or at API-call time? They're different numbers if compression happened between.
- Wondering if `session.json` should actually be JSONL — one line per turn instead of a monolithic object. Would make partial reads and crash recovery trivial. Downside: harder to load the full session for replay.
- The anthropic SDK streaming interface is awkward for tool use — you get content deltas and tool_use deltas interleaved, and there's no clean way to know a tool call is "complete" until the next event arrives. Filed mentally under "things I'd redesign."
- Trail race in October. Need to figure out taper schedule. (Not relevant but this is inbox.)
