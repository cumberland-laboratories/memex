# Roadmap

## Milestones

1. **Skeleton** — Minimal loop: user prompt -> Claude API call -> print response. No tools, no context management. Just prove the bones work. `[done]`

2. **Tool protocol** — Define tool schema shape, dispatch mechanism, and error contract. Tools are pure functions: (args, context) -> result. `[done]`

3. ~~**React-style event loop** — Observation-thought-action cycle with explicit state machine. Would give fine-grained control over each reasoning step.~~ *Replaced by plan-execute after testing showed the observation loop added latency without improving task completion. Simpler is better.* `[cut]`

4. **Context manager** — Token accounting, budget enforcement, and compression triggers. The hard problem: when to summarize, when to drop, when to refuse. `[in progress]`

5. **Error recovery** — Graceful handling of tool failures, rate limits, and malformed responses. Currently the agent just dies on any unexpected state. `[planned]`

6. **Ask-vs-act thresholds** — Confidence-gated execution: when should the agent act autonomously vs. ask for confirmation? Added after watching the prototype silently overwrite a file it shouldn't have. `[planned — added 2026-04-08]`
