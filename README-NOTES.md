# README Planning Notes

## Tone & Expectations

- Lead with "this is a prototype" — working system, not polished UX
- Lots of "naked thinking" in the docs — LLMs reasoning through the constitution in real time, visible to the user
- Coders working with LLMs may be used to this, but set expectations explicitly
- Not ready for general consumer UX — this is for people comfortable with the raw loop
- Single user, no security, no auth — intentional. This is proof of substrate, not a product
- Designed for one person + their LLMs. Not multi-tenant, not collaborative (yet)
- Realistic scale: 50–150 threads year 1, 300–500 by year 5. Personal knowledge, not institutional. The architecture can handle more, but a single user probably won't generate thousands of threads

## Latency Expectations

- Session open takes 15–60 seconds depending on thread count. The LLM is reading your files, checking patterns, triaging inbox. This is the cost of continuity.
- Comparable to loading a document into any LLM chat — the difference is you didn't have to prepare the document.
- The system is optimized for session quality, not response latency. The tradeoff is explicit.
- The right comparison isn't "Memex vs. bare Claude" — it's "Memex vs. you opening 6 tabs, re-explaining your project, and pasting context back in every session." Even 60 seconds beats 5–10 minutes of manual setup.
- Be honest about this in the README. The audience is people tired of re-explaining themselves, not people optimizing for sub-second responses.

## Author's Note (end of README)

- Break the fourth wall. Everything above is the system describing itself. This is a person saying "I built this because nothing else worked."
- 10–15 lines max. Plain-speaking, no block longer than 3 lines. A person talking, not a founder pitching.
- Key beats:
  1. "This works for me. It may or may not work for you." Not a sales pitch.
  2. The speed question: "Yes, session open takes 30 seconds. That replaces 10 minutes of re-explaining myself."
  3. What I tried before: Claude.ai conversations that go stale, ChatGPT threads that can't cross-reference, Notion/Obsidian that require *me* to be the maintenance layer. The Memex is the first thing that actually remembers where we left off.
  4. The real value: not the architecture — the feeling of picking up a conversation that never ended. The LLM knows what you were working on yesterday.
  5. Who this is for: people who think in threads, work with LLMs daily, and are tired of losing context. Not everyone.
- Published under Cumberland Laboratories, but the author's note is personal — first person, signed

## Quick Start (high priority, near top of README)

- Show the user how to start a thread: "I want to start a thread on ..."
- The system has capture bias (auto-creates threads when topics have momentum), but the user shouldn't have to discover that by accident
- Avoid the "hey, where are my threads?" confusion — make it clear early that:
  1. You can explicitly ask for a thread
  2. The system will also create threads on its own when a topic has enough substance
  3. Threads live in memex/active-threads/ and you can always look there
- Give-and-take on automatic creation is fine, but the user needs to know both modes exist up front
