---
last-touched: 2026-04-12
category: reference
tags: [syllabus, study-plan, agentic-systems, pi-development, easter-egg]
---

# Syllabus — Agentic Systems Foundations

A 6-week study plan for a developer building agentic coding tools. The goal is not survey-level familiarity — it's the ability to evaluate architectural tradeoffs, debug failure modes under pressure, and extend the system with confidence about what will break.

Each two-week block targets a layer of the stack. The progression: **Weeks 1–2** cover the inference engine (what the model actually does with your tokens). **Weeks 3–4** cover the interaction layer (tool protocols, feedback loops, human-AI handoff). **Weeks 5–6** cover the persistence layer (context management, knowledge architecture, governance).

Start with what's weakest. Skip what you already command. The whiteboard tests are your readiness check — if you can reason through them cold, move on.

---

## Weeks 1–2: The Inference Engine — What Happens Inside the Context Window

### Week 1: Attention, Context, and the Transformer's Actual Behavior

**Why**: Every architectural decision in an agentic system is downstream of what the model does with its context window. Token budgets, compaction strategies, prompt structure — none of these make sense without understanding attention patterns, positional encoding, and how information decays across long contexts.

| Level | Resource | Format | Why |
|-------|----------|--------|-----|
| Refresh | 3Blue1Brown — [But what is a GPT?](https://www.youtube.com/watch?v=wjZofJX0v4M) and the attention mechanism video | Video (25 min each) | Visual intuition for the transformer before formalism. How attention heads select and route information. |
| Working | Vaswani et al., "Attention Is All You Need" (2017) | Paper (15 pages) | The original. Read §3 (Model Architecture) carefully. Understand multi-head attention, positional encoding, the encoder-decoder split. Everything since is a variation on this. |
| Working | Anthropic, "In-context Learning and Induction Heads" (2022) | Paper | How transformers implement few-shot learning mechanically. Induction heads are the circuit that makes in-context tool use work. If you don't understand this, you're building on sand. |
| Deep | Liu et al., "Lost in the Middle" (2023) | Paper | Empirical evidence that LLMs attend unevenly to long contexts — strong at the beginning and end, weak in the middle. Directly relevant to context budget design: where you place information in the window matters. |

**Key concepts to own**: Self-attention as a weighted lookup. Positional encoding and why position matters. KV cache and why inference cost scales with context length. The "lost in the middle" phenomenon. Why 200K tokens ≠ 200K tokens of equal-quality attention.

**Whiteboard test**: Explain why doubling the context window does not double the model's effective knowledge. Draw the attention pattern for a tool-use conversation (system prompt, user task, assistant plan, tool call, tool result) and predict which tokens attend most strongly to which. Explain why pinning the system prompt at the top of context is not just convention — it's an attention architecture decision.

---

### Week 2: Sampling, Decoding, and the Mechanics of Generation

**Why**: The agent's behavior is not just a function of the prompt — it's a function of the sampling strategy. Temperature, top-p, tool_choice forcing, stop sequences — these are control surfaces. If you don't understand them, you're tuning a system you can't predict.

| Level | Resource | Format | Why |
|-------|----------|--------|-----|
| Working | Holtzman et al., "The Curious Case of Neural Text Degeneration" (2020) | Paper | Why greedy decoding degenerates and why nucleus sampling (top-p) works. The theoretical foundation for every sampling parameter you set. |
| Working | Anthropic API documentation — Messages API, tool use, streaming | Reference | The actual interface you're programming against. Read the tool_use spec carefully: how tool calls are structured, what tool_choice does, how tool_result must follow tool_use. The protocol IS the architecture. |
| Deep | Wei et al., "Chain-of-Thought Prompting" (2022) | Paper | Why asking the model to reason step-by-step works. Not magic — it's giving the model intermediate computation space in the output tokens. Directly relevant to the plan-act-observe-reflect loop. |

**Key concepts to own**: Temperature as entropy control. Top-p vs. top-k. Why tool calls need low temperature (you want deterministic structured output). Why reasoning benefits from moderate temperature (you want exploration). Stop sequences as a termination contract. The difference between "the model decided to stop" and "the API truncated at max_tokens."

**Whiteboard test**: Your agent is generating a tool call but occasionally hallucinates parameter values. Diagnose: is this a temperature problem, a schema problem, a context problem, or a training problem? How would you test each hypothesis? Now explain why `tool_choice: "auto"` vs `tool_choice: {"type": "tool", "name": "read_file"}` produces different behavior — not just different outputs, but different *attention patterns* in the model.

---

## Weeks 3–4: The Interaction Layer — Tools, Feedback, and Human-AI Handoff

### Week 3: Tool Protocol Design and the Model's-Eye View

**Why**: The model sees your tool definitions on every turn. Tool names, descriptions, and parameter schemas are not documentation — they're part of the prompt. Bad tool design doesn't just annoy developers; it degrades model performance measurably.

| Level | Resource | Format | Why |
|-------|----------|--------|-----|
| Working | Schick et al., "Toolformer: Language Models Can Teach Themselves to Use Tools" (2023) | Paper | The foundational work on LLM tool use. How models learn when to call tools and when to reason internally. The grain-size heuristic comes from this insight. |
| Working | Anthropic, "Tool Use Best Practices" | Documentation | Practical guidance from the people who trained the model. Naming conventions, description quality, parameter design. Treat this as a specification, not a suggestion. |
| Working | tinyagent `tools/` directory — read all four tool files | Code | Your own system. Read the tools through the model's eyes: if you were Claude and saw these schemas for the first time on every turn, could you use them correctly? |
| Deep | Qin et al., "Tool Learning with Foundation Models" (2023) | Survey paper | Comprehensive survey of tool-augmented LLMs. §4 on tool creation and §5 on tool selection are directly relevant. |

**Key concepts to own**: The schema tax (tokens per tool per turn). Grain size: too fine = loop bloat, too coarse = opacity. Why tool descriptions are model-facing instructions, not human documentation. The difference between tool selection (the model picks which tool) and tool execution (your code runs the tool). Why string returns are better than structured returns for LLM tools.

**Whiteboard test**: Design a tool schema for "search the codebase for a pattern." What's the name? What parameters does it take? What does the description say? Now estimate its schema tax in tokens. Now explain why this tool might be worse than just giving the model the file listing and letting it read files directly — when does search earn its schema tax?

→ [Tool Grain Size](../active-threads/tool-grain-size.md) — the heuristic
→ [Tool Schema Ergonomics](../active-threads/tool-schema-ergonomics.md) — the model's-eye view
→ [Tool Protocol Decision Record](../artifacts/2026-04-11-tool-protocol-decision-record.md) — why tinyagent chose this protocol

---

### Week 4: Feedback Loops, Failure Modes, and the Human in the Loop

**Why**: An agentic loop without feedback is an amplifier without a feedback resistor — it works until it oscillates. Understanding feedback theory (not just in the ML sense, but in the control-systems sense) is what separates a demo from a tool you'd trust with real work.

| Level | Resource | Format | Why |
|-------|----------|--------|-----|
| Refresh | Åström & Murray, *Feedback Systems* — Ch. 1 (Introduction) | Textbook (free online) | Control theory from first principles. Feedback, stability, reference tracking. The vocabulary transfers directly: the constitution is the reference signal, the enforcer is the sensor, the PI is the controller. |
| Working | Shinn et al., "Reflexion: Language Agents with Verbal Reinforcement Learning" (2023) | Paper | Agents that reflect on their failures and adjust. The reflect step in plan-act-observe-reflect is this paper's contribution. Understand what verbal reinforcement buys over simple retry. |
| Working | Yao et al., "ReAct: Synergizing Reasoning and Acting" (2023) | Paper | The reasoning-action loop that most agentic frameworks implement. tinyagent's loop is a simplified ReAct. Understand the original to know what was simplified and why. |
| Deep | Madaan et al., "Self-Refine: Iterative Refinement with Self-Feedback" (2023) | Paper | Self-critique as a refinement loop. The key question: when does self-review work, and when do you need cross-model review (the enforcer)? The answer is empirical, and this paper gives you the baseline. |

**Key concepts to own**: Open-loop vs. closed-loop agents. The five failure modes (brute-force retry, plan drift, context exhaustion, tool hallucination, infinite delegation). Why self-critique has limits (same-model blind spots). The escalation ladder: act → act-and-report → propose-and-wait → refuse. Authorization scope and why it doesn't generalize.

**Whiteboard test**: Your agent has been running for 15 iterations. It's reading the same file repeatedly and generating similar tool calls. Diagnose: which failure mode is this? What's the countermeasure? Now design a detection heuristic — how many repeated actions before you escalate? Is repetition always bad (consider: re-reading a file after modifying it is correct behavior)?

→ [Agentic Loop Failure Modes](../active-threads/agentic-loop-failure-modes.md) — the catalog
→ [Ask vs Act Thresholds](../active-threads/ask-vs-act-thresholds.md) — the escalation framework
→ [Error Recovery as Design](../active-threads/error-recovery-as-design.md) — errors as signals, not exceptions

---

## Weeks 5–6: The Persistence Layer — Context, Knowledge, and Governance

### Week 5: Context Window Economics and Knowledge Architecture

**Why**: The context window is the agent's working memory. Everything the agent knows in a given turn is what's in the window. Managing this budget — what to load, what to summarize, what to drop — is the single highest-leverage architectural decision. Get it wrong and the agent either drowns in noise or forgets what it's doing.

| Level | Resource | Format | Why |
|-------|----------|--------|-----|
| Working | Bush, "As We May Think" (The Atlantic, 1945) | Essay (8 pages) | The original Memex paper. Not historical curiosity — Bush's insight about associative trails is exactly what cross-referenced threads implement. The Memex is a literal implementation of a 1945 idea with 2025 technology. |
| Working | Nelson, *Computer Lib / Dream Machines* (1974) — the hypertext sections | Book (selected chapters) | Ted Nelson's transclusion and the idea that documents should be composed of references, not copies. The Memex's "navigable, not always-loaded" tier is transclusion by another name. |
| Working | Anthropic, "Long Context Prompting Tips" | Documentation | Practical guidance on using large context windows effectively. How to structure information for retrieval. Why position in the window matters (connects to "Lost in the Middle" from Week 1). |
| Deep | Xu et al., "Retrieval meets Long Context Large Language Models" (2024) | Paper | When is RAG better than long context? When is long context better than RAG? The answer depends on the task, and this paper maps the boundary. The Memex's tiered loading is a specific answer to this question. |

**Key concepts to own**: The budget model (max_tokens - output_reserve - pinned_cost = discretionary). Recency-weighted relevance. The compaction decision (summarize vs. drop vs. page out). Why "load everything" fails at scale. The always-loaded / navigable distinction as a context management strategy. Token ROI: each token should contribute more than the next-best alternative.

**Whiteboard test**: You have 200K tokens. System prompt + tool schemas cost 4K (pinned). Output reserve is 8K. You have 188K discretionary. Your agent has been running for 40 turns with 6 file reads averaging 3K tokens each. Draw the budget. Where is the pressure? What do you compact first? Now explain why summarizing the oldest 20 messages is not always the right answer — when would you drop tool results instead?

→ [Context Budget Economics](../active-threads/context-budget-economics.md) — the core tradeoff
→ [Context Budget Formal Model](../artifacts/2026-04-11-context-budget-formal-model.md) — the math
→ [Session Continuity Without Memory](../active-threads/session-continuity-without-memory.md) — persistence across sessions

---

### Week 6: Governance, Adversarial Review, and System Integrity

**Why**: A system that maintains itself must also police itself. LLMs drift, hallucinate, take shortcuts, and silently degrade state over time. Governance is not bureaucracy — it's the feedback loop that keeps the system honest. Without it, every self-maintaining system eventually maintains its own decay.

| Level | Resource | Format | Why |
|-------|----------|--------|-----|
| Working | Ostrom, *Governing the Commons* (1990) — Ch. 1–3 | Book | How self-governing systems work without top-down control. Ostrom's design principles for commons governance map directly to the Memex: clearly defined boundaries, monitoring, graduated sanctions, conflict resolution. The constitution is a commons governance document. |
| Working | Christiano et al., "Deep Reinforcement Learning from Human Feedback" (2017) | Paper | The RLHF paper. The PI's role in the Memex is structurally analogous to the human rater in RLHF — providing the reward signal that shapes the system's behavior. But the Memex is more explicit: the constitution is the reward function, written down. |
| Working | Perez et al., "Red Teaming Language Models with Language Models" (2022) | Paper | Using one model to find failures in another. The enforcer's job description. Understand why same-model review has blind spots (shared training biases) and cross-model review is structurally stronger. |
| Deep | Bowman et al., "Eight Things to Know about Large Language Models" (2023) | Paper | A sober assessment of what LLMs can and can't do. §5 ("LLMs don't always say what they believe") and §7 ("LLMs can be steered") are directly relevant to governance design. |

**Key concepts to own**: The constitution as executable specification. Roles as separation of concerns (PI, agent, enforcer, crawler). Why the enforcer must be a different model. The reinforcing loop: conversation → threads → wiki → enforcer → corrections → conversation. Mechanical checks vs. model-powered checks vs. human review — three layers, overlapping coverage. Why 100% coverage is impossible and graceful degradation is the goal.

**Whiteboard test**: Your enforcer reports that three threads contradict each other on a design decision. One is the most recent, one has the most hits, one is referenced by an artifact. Which is authoritative? Trick question — explain why the PI must decide, and why no automated rule can resolve this. Now design a policy for what the enforcer should do when it detects a contradiction it can't resolve: what goes in the report, and what does the PI see at session open?

→ [Constitution (core)](../../constitution-core.md) — the governance framework
→ [Enforcer Audit Procedure](../../.memex/procedures/enforcer-audit.md) — the audit protocol
→ [Adversarial Review Methods](essay-adversarial-review-methods.md) — the methodology
→ [Reinforcing Loops](design-pattern-reinforcing-loops.md) — the feedback architecture

---

## Reading Order (Short Path)

If 6 weeks is too long, this is the minimum path to making sound architectural decisions:

1. **Vaswani (2017) + "Lost in the Middle" (2023)** — attention mechanics and why context position matters (2 days)
2. **Anthropic tool use docs + tinyagent tools/** — the protocol you're building on (1 day)
3. **ReAct (2023) + Reflexion (2023)** — the reasoning-action loop and self-correction (2 days)
4. **Bush (1945) + Anthropic long-context tips** — knowledge architecture from first principles (1 day)
5. **Perez et al. (2022) + Ostrom Ch. 1–3** — adversarial review and governance (2 days)

Eight days to architectural fluency. The remaining four weeks build the depth to extend the system confidently.

---

## Connections

→ [Context Budget Economics](../active-threads/context-budget-economics.md) — the headline design concern; Week 5 builds the theory
→ [Agentic Loop Failure Modes](../active-threads/agentic-loop-failure-modes.md) — the failure catalog; Week 4 explains why they happen
→ [Tool Grain Size](../active-threads/tool-grain-size.md) — the design heuristic; Week 3 grounds it in the literature
→ [Adversarial Review Methods](essay-adversarial-review-methods.md) — the methodology essay; Week 6 provides the theoretical backing
→ [Codebase Charter Pattern](codebase-charter-pattern.md) — the pattern for navigating code before modifying it
