# Protocol Vocabulary

Operating language for the Memex system. Each term has a defined meaning, scope, and output contract. Using these terms precisely makes the system teachable and portable.

## Knowledge Units

| Term | What it is | Scope | Key property |
|------|-----------|-------|-------------|
| **Thread** | A dense index card — a node in the knowledge graph | 5–80 lines | Carries frontmatter (category, tags, hits), Summary section, cross-references |
| **Active thread** | A thread in the always-loaded working set | `active-threads/` | Compression-budgeted, 5–8 max |
| **Lightweight thread** | A dormant/reference thread, not always loaded | `threads/` | 5–20 lines, keeps the graph connected cheaply |
| **Artifact** | Deep storage — full synopses, design notes, session records | `artifacts/` | Date-prefixed, referenced from threads like footnotes |
| **Identity** | Stable encoding of who the operator is and how they think | `identity.md` | Not a user profile — shapes how the agent reasons, not just what it retrieves |
| **Rhythm** | Recurring temporal obligation (bill, birthday, renewal). Directory still named `patterns/` but the operating term is "rhythm" to avoid collision with "design pattern" (Alexander sense). | `patterns/` | Checked at session open against advance-notice window |
| **Whiteboard** | Temporary shared coordination surface for multi-operator work before routing to a permanent home | `whiteboard.md` | Append-only while live; cleared after routing |

## Operations

| Term | What it does | Trigger | Output |
|------|-------------|---------|--------|
| **Promotion** | Moves a thread up a tier (lightweight → active, or artifact synopsis → thread) | Repeated use / rising heat | Expanded thread in higher tier; cross-references preserved |
| **Demotion** | Compresses a thread down a tier (active → lightweight) | Cooling off — no touches, no Next Up | Stub in `threads/`; graph connectivity invariant holds |
| **Splitting (semantic)** | Divides a thread at a seam between independent subtopics | Active thread exceeds 60 lines with separable concerns | Two threads, cross-referenced, both with Summaries |
| **Splitting (volume)** | Divides a dense but unified thread into numbered parts (`-1`, `-2`) | Active thread exceeds 60 lines with no clean semantic seam | Parts share Summary/category/tags, cross-reference each other as continuations |
| **Rotation** | The general term for promotion + demotion — threads moving between tiers | Activity signals (hits, last-touched, Next Up) | Budget stays under 400 lines; nothing is deleted |
| **Hit** | One substantive engagement with a thread in a session | Thread is a focus of discussion (not incidental mention) | Frontmatter `hits:` incremented by 1 |
| **Triage** | Processing inbox entries at session open or close | Session opening (inbox non-empty) or session close (inbox accumulated mid-session entries) | Each entry routed to a thread, new thread created, or surfaced for discussion |
| **Mid-session capture** | Appending a thought to the inbox during conversation to avoid derailing flow | Agent notices something worth capturing that isn't part of the current discussion | One-line entry in `inbox.md`. No routing, no thread updates, no cross-references. Triage happens later. |
| **Whiteboard routing** | Moving one or more whiteboard entries into a thread, artifact, inbox, or discard path | Adjudicator instruction (`Route #3...`, `Capture #1-#4...`, etc.) | Permanent destination updated; whiteboard remains temporary |

## Rendered Outputs

| Term | What it produces | Audience | Production |
|------|-----------------|----------|------------|
| **Documentation render** | A rendered presentation of the thread graph for a human-facing platform | Human / team | Mechanical pipeline extracting Summaries and metadata from the Memex source |
| **Wiki** | MediaWiki-format documentation render | Human / team | Current default target; grouped by category, weighted by hits |
| **Report** | Technical narrative document — design status, novelty assessment, forward plan | Human / external | Written by agent, captures architectural state at a point in time |

## Roles

| Term | What it does | Who | Key constraint |
|------|-------------|-----|---------------|
| **Adjudicator** | Human who holds mission, taste, architecture, and final meaning across the system; resolves tradeoffs the models cannot legitimately resolve on their own | Human | Must remain substantively engaged — not a rubber stamp |
| **Systems Adjudicator** | Stronger form of adjudicator for multi-model or multi-process systems. Integrates outputs across agents, enforcers, crawlers, and domain workflows to keep the whole system aligned with its purpose | Human | Requires multi-layer understanding of both local work and global architecture |
| **Chat agent** | Reads/writes the Memex in-session, talks to the human | Primary model (e.g., Claude Opus) | Follows the constitution |
| **Enforcer** | Audits for staleness, contradiction, bloat; produces documentation renders | Different model (e.g., Sonnet, Gemini) | Must NOT be the same model as the chat agent |

**Terminology note:** `operator` is still usable as a generic human-in-the-loop term, but `adjudicator` is more precise when the human is not merely operating the interface but actively judging mission, architectural coherence, and tradeoffs.

### Role Stack

The complete set of roles in a fully operational system, from human to background process:

| Role | Type | Function | Key property |
|------|------|----------|-------------|
| **Systems Adjudicator** | Human | Holds mission, architectural coherence, and final judgment. Integrates outputs across all agents and processes. | Irreducible — models generate, critique, and compress, but the human is the final integrator of meaning |
| **Chat Agent** | Model (primary) | Talks to the human. Reads/writes the Memex in-session. | Follows the constitution. Session-scoped. |
| **Enforcer** | Model (different) | Audits the Memex (read-only). Produces reports and documentation renders. | Must be a different model than the chat agent. Does not edit. |
| **Crawler** | Model (any, cheap) | Scheduled background maintenance: compression budgets, lifecycle enforcement, stale thread detection, missing backlinks. | Deterministic, rule-following. Produces candidate changes for human review. |
| **Spider** | Model (any) | Stochastic background discovery: missed cross-references, unexpected connections, candidate concept bridges. | Exploratory, suggestion-oriented, merge-gated. Proposes, never silently edits. |

The adjudicator is not a "human in the loop" checkbox. The adjudicator is the reason the loop exists. Models are interchangeable operators; the adjudicator is the constant.

## Operating Levels

| Term | Signal | What it means |
|------|--------|--------------|
| **Content level** | No prefix (default) | The Memex is infrastructure — the agent reads/writes threads, captures ideas, updates hits. Normal conversation. |
| **Meta level** | Message starts with `[memex]` | The Memex is the object of work — the agent modifies constitution, procedures, structure, budgets. Explicit opt-in. |

## Interaction Directives

Terms for shaping the agent's response. These are output contracts — when the human uses one, the agent knows the expected format, depth, and purpose without further negotiation.

| Term | What it means | Output contract |
|------|--------------|-----------------|
| **Bite** | A 30-second human-readable response. The atomic unit of AI output. Concise, self-contained, no preamble. | ~1–3 short paragraphs. One screen. If it needs a scroll, it's not a bite. |
| **2-Bite, 3-Bite** | Scaled versions. A 2-bite is a 60-second read; a 3-bite is 90 seconds. Use when the topic needs room but not a full treatment. | Proportional to bite. Still concise — scaling length, not density. |
| **Review** | What a manager would ask a team member for. Technical if needed, flexible in scope, evaluative. Not a summary — a *judgment*. May flag risks, question assumptions, or recommend changes. | Variable length. Structured like a professional review: what's here, what works, what doesn't, what's next. |
| **Formal plan** | A sequenced implementation plan with dependencies, decision points, and scope boundaries. Not aspirational — executable. | Numbered steps, explicit dependencies, named decision points. Could be handed to a second agent and followed without further context. |
| **Feedback** | Specific, actionable response to work presented. Not a review (which evaluates the whole) — feedback targets what the human just showed. | Direct, no throat-clearing. "This works because..." / "This doesn't work because..." / "Consider..." |
| **Turn** | One human message + one agent response. The atomic unit of conversation. Not currently numbered (see friction log 2026-03-15). | — |
| **Clip** | Verbatim capture of one or more turns to artifact. Trigger: `[save]` or `[clip]`. | Raw exchange preserved as-is. See → [clip-to-artifact.md](../procedures/clip-to-artifact.md) |

## Session Governance

Courtroom-derived directives for real-time control of conversational and coding flow. These are single-word or two-word commands with centuries of refinement behind them — maximum information density, zero ambiguity. Prior art: adversarial legal proceedings, where statements have consequences, scope must be controlled, and the record matters.

| Term | What it means | Agent behavior |
|------|--------------|----------------|
| **Strike that** | Retract the agent's last response from the working context. It's off-track; don't let it influence what follows. | Agent treats its last response as void. Does not reference, build on, or continue from the struck material. Analogous to stricken testimony — the jury (context) must disregard it. |
| **Withdrawn** | The human retracts their own immediately preceding statement. "I said that, but I'm taking it back before you act on it." Distinct from *strike that* (which targets the agent's output). | Agent treats the withdrawn statement as if it was never sent. Does not act on it, respond to it, or let it shape subsequent context. No clarification needed — the retraction is complete. Analogous to counsel withdrawing a question — the witness (agent) does not answer. |
| **Sidebar** | A process-level aside outside the main line of work. Quick clarification, logistics, or tooling question — not part of the current thread or task. Distinct from `[memex]` (which operates *on* the Memex structure); sidebar is about the *conversation process*, not the system. | Agent responds to the aside, then returns to the prior line of work as if the sidebar didn't happen. Nothing captured to threads or artifacts unless explicitly requested. |
| **Sustained** | The human rules that the agent's most recent objection, concern, or flagged issue is valid. Binds to the most recent agent-raised concern in the immediately preceding turn. If ambiguous, the agent asks which concern is sustained before proceeding. | Agent continues in the direction the sustained concern indicated. |
| **Overruled** | The human rules that the agent's most recent objection or concern is not valid. Binds to the same target as sustained — most recent agent-raised concern. If ambiguous, agent asks before proceeding. | Agent drops the concern and proceeds. Does not re-raise the same objection. |
| **For the record** | Explicitly marks a statement as important enough to capture — but lighter than `[clip]`. A flag, not a full artifact save. | Agent notes the statement in the most relevant active thread (as a bullet, a quote, or a connection). Quick capture, no ceremony. |
| **Stipulate** | Both parties agree on a fact for the current task or session. Don't explain it, don't argue it, just use it as a given. Session-local by default — does not persist to the Memex unless the human explicitly says "stipulate and record" or "for the record." | Agent treats the stipulated fact as established context for the remainder of the current task. No preamble, no justification, no "as you know." Saves turns. |
| **Objection — scope** | Human or agent flags that the conversation has drifted outside the declared scope of the current task. | Work pauses. The scope violation is named. Human decides: expand scope, table the digression, or return to the original task. |
| **Objection — form** | The response shape is wrong — too long, too short, wrong format, wrong level of detail. | Agent re-delivers in the correct form. No defensiveness, no explanation of why the first attempt was shaped that way. |

## Structural Terms

| Term | What it means |
|------|--------------|
| **Constitution** | Governance document (`constitution.md`) defining roles, constraints, and pointers to procedures. Not content — operating charter. Model-specific entry points (`CLAUDE.md`, `AGENTS.md`) redirect here. |
| **Procedure** | Executable sequence invoked by the constitution. Lives in `procedures/`. "Do this now." |
| **Reference note** | Cognitive aid consulted situationally. Lives in `reference-notes/`. "Keep this in mind." |
| **Friction log** | Append-only record of conversational snags. Data, not a to-do list. Feeds enforcer review. |
| **Cross-reference** | Annotated link between threads explaining *why* the connection exists. The graph's edges. |
| **Whiteboard session** | One bounded period of temporary multi-operator work on a subproblem. Usually opened explicitly by the adjudicator and closed after routing. |
| **Summary** | 2–4 sentence section in every thread. Written at documentation-entry quality. Directly extractable by the render pipeline. |
| **Graph connectivity** | Invariant: every operation preserves all cross-references. Nothing is orphaned. |
| **3-hop constraint** | Any topic should be reachable within 3 associative hops. If not, add a lightweight thread. (Watts-Strogatz navigability.) |
