---
date: 2026-04-29
depth: medium
tags: [charters, constitutional-architecture, gist, onboarding, public]
source-thread: n/a
source: claude + ren
summary: Standalone guide to constitutional architecture for AI-assisted development — charters, notation, adversarial review, the feedback loop, and getting started. Intended for GitHub gist distribution.
---

# Constitutional Architecture for AI-Assisted Software Development

A practical guide to building and maintaining codebases with AI coding agents. This is not theory — it's a pattern validated on a 97K-line production codebase, where an AI agent completed three god-function decompositions without regressions and identified a cross-module CSRF bug through charter cross-references alone.

The core idea: **AI generates code faster than you can read it. You need a structural layer that preserves your comprehension at the speed code is now produced.** That structural layer is charters, governed by a constitution, validated by adversarial review.

---

## The problem

Before LLMs, code and comprehension scaled together — you wrote it, so you understood it. AI breaks that coupling. Your codebase grows without a corresponding growth in your understanding. You become a reviewer of output you didn't write, in a system that's expanding faster than you can read.

This isn't a tooling problem. It's a governance problem. The same problem organizations faced when they grew past the size where everyone could know everything. The solution then was constitutions and separation of powers — not smarter individuals. The solution now is the same.

## Three Levels of Documentation

Most projects have two levels of documentation. Constitutional architecture adds a third.

| Level | Audience | Purpose | Example |
|-------|----------|---------|---------|
| **Inline** | Developers reading code | Explain *what* and *why* at point of use | Code comments, docstrings |
| **Human-readable** | Humans navigating the system | Describe business flows and subsystems | Design docs, architecture docs, READMEs |
| **Charters** | LLMs modifying the code | Map every function's access patterns, dependencies, and tripwires | Per-module charter files with structured notation |

The first two levels are familiar. The third is new, and it's the one that changes the game.

**Charters are written for LLMs, by LLMs** (with human oversight). They use a notation optimized for how models process text — line anchors for verifiable location, access patterns for predicting side effects, and tripwire markers (`!`) that spike model attention through contradiction. A human *can* read them, but the primary consumer is the AI agent about to modify your code.

**Charters are intentionally short.** A charter for a 2,000-line module is 50-100 lines of structured notation. A set of 20 charters covering a 97K-line codebase totals ~2,000 lines — roughly 2% of the code they describe. This matters because every token loaded into an LLM's context window displaces something else. Charters earn their token cost by compressing architectural knowledge into a fraction of the tokens that loading the source files would require. The LLM gets the map without paying for the territory.

**LLM coding agents are uniquely good at this.** Tools like Claude Code and Codex are built to navigate cross-referenced markdown files — following `→` links between charters, reading the referenced function, checking the access patterns, tracing the dependency graph. This is exactly what these agents do well. The charter format exploits this strength: structured notation in linked markdown files is the native habitat of an agentic coding tool.

**The AI writes and maintains the charters.** The primary agent (your coding AI) explores the code, writes the charters, and updates them after changes — the human oversees but doesn't do the mechanical work. This is 99% AI labor. Is there risk of error? Of course. The agent might mischaracterize an access pattern, miss a cross-cutting dependency, or let a charter go stale. This is exactly why the enforcer exists: a *different* model audits the primary agent's charters against the actual code. The charters become the **lingua franca** between the primary agent and the enforcer — the shared, structured language they use to communicate about the codebase. The primary agent says "this function reads Submission and writes Grade." The enforcer checks: does it really? This only works because charters are precise enough to be mechanically verifiable. Prose documentation can't be audited this way. Charters can.

## What a Charter Looks Like

Each charter covers a code module. Each function gets a block:

```
### apply_grade(submission, raw_score, grader) [L45]
File: core/utils/grading.py
Creates Grade record with penalty-adjusted score.
Models: Submission(R), Grade(W), Enrollment(RW)
Session R: current_grader_id, active_rubric
Session W: last_graded_at
← grade_submission() in views_assignments
→ see cross_cutting.md "Late Penalty Timing"
! The instructor sees raw_score, but Grade.score
  is penalty-adjusted. These are different numbers.
```

**The notation:**

| Symbol | Meaning | Why |
|--------|---------|-----|
| `[Lnnn]` | Line anchor | Verifiable location — if the function isn't near this line, the charter is stale |
| `(R)/(W)/(RW)` | Access pattern | Predicts side effects without reading code |
| `!` | Tripwire | Inverts the reader's assumption — spikes LLM attention through contradiction |
| `→` / `←` | Cross-reference (outbound/inbound) | Shows what calls what — your blast radius |
| `Session R:` / `Session W:` | State access | Tracks untyped state that code alone can't reveal |
| `TRIPWIRE` | Section-level danger label | Multi-function patterns that must be preserved as a unit |

This is all the LLM needs to make a safe code change — what the function touches, what depends on it, and what will surprise you.

## The Cross-Cutting Charter

The most important charter in any set. It doesn't map to a single module — it maps to patterns that span modules.

Every codebase has behaviors that emerge from module interactions: a data flow that traverses four files, an implicit contract between a prompt and the code that parses its output, an invariant that must hold across every exit path. These are invisible in any individual charter. They're what breaks during refactors.

The cross-cutting charter documents these with `TRIPWIRE` labels. Read it first, every time.

## The Constitution: Closing the Feedback Loop

Charters are inert without governance. The constitution is a short document (one page) that tells the AI agent:

1. **Before modifying code, look up the relevant charter.** A dispatch table maps code paths to charter files — not "find the right charter" but "if you're changing `views_quiz.py`, read `charter-views_quiz.md` and `charter-cross_cutting.md`."
2. **After modifying code, update the charter.** Same commit, same PR, same operation. A stale charter is worse than no charter.
3. **The enforcer audits compliance.** A different model (not the one that wrote the code) checks charters against code and flags drift.

The chain: **Constitution → Charter Lookup → Read Charter → Modify Code → Update Charter → Enforcer Audit**. This is the feedback loop that prevents architectural decay.

## Adversarial Design: Use Models Against Each Other

Same-model review has blind spots — shared training biases create shared blind spots. Cross-model review is structurally stronger.

**The pattern**: Use one agent to write code (e.g., Claude Code), then use a different agent or model (e.g., Codex, Gemini) to critique it. The critic reads the charters, reads the code changes, and asks: *did this change violate any charter constraints? Did it introduce new cross-cutting concerns that aren't documented? Are the access patterns still accurate?*

This is the enforcer role. It doesn't edit — it audits. The primary agent (with the human present) reviews the audit and decides what to act on. Separation of powers, applied to code.

## The Recipe

### For a new codebase:

1. **Write skeleton charters alongside skeleton code.** They force you to articulate module boundaries before writing implementations.
2. **Write the cross-cutting charter** as patterns emerge. Don't wait until the system is "done" — cross-cutting concerns appear early.
3. **Add the constitution rule**: "before modifying code, consult the relevant charters." Put the dispatch table in your CLAUDE.md, AGENTS.md, or equivalent entry point.
4. **Set up adversarial review.** Run a different model against the charters periodically. Even a quick pass catches drift.

### For an existing ("hopeless") codebase:

1. **Write charters first, code changes second.** The act of chartering a module forces you to understand it. This is the most valuable step — even if you never refactor, you now have a map.
2. **Start with the god functions and the cross-cutting concerns.** These are where the complexity lives. Charter them, then decompose them with the charter as your invariant checklist.
3. **Use the charters as your refactoring safety net.** Every function's access patterns and cross-references tell you what will break when you move code. The `←` annotations are your blast radius.
4. **Update charters as you refactor.** The charter evolves with the code. After the refactor, you have both clean code and an accurate map.

This approach was validated on a 97K-line Django monolith: 20 charter files created before the refactor, three god-function decompositions completed without regressions, cross-module bug found through charter cross-references.

## The Three-Layer Documentation Architecture

At scale, charters are one layer of three:

1. **Charters** — per-module API references for the AI agent. Every function, its access patterns, tripwires, cross-references. Organized by code structure.
2. **Designs** — flow-oriented documents for humans. Each one describes a business flow (checkout, authentication) from the user's perspective, referencing charters for technical detail.
3. **Systems** — infrastructure documentation. How subsystems work (CI/CD, caching, deployment).

Charters are the ground truth. Designs are generated from charters as a more human-readable layer. Systems docs cover what charters don't reach.

## PI Syllabus: What the Human Needs to Know

The human in this system is the PI (principal investigator) — they hold mission, taste, and architectural coherence. The AI handles execution; the PI handles judgment. To make good judgment calls, the PI needs:

**Week 1-2: The inference engine.** What actually happens in the context window. Attention patterns, positional encoding, why 200K tokens isn't 200K tokens of equal-quality attention. Read: Vaswani 2017 ("Attention Is All You Need"), Liu 2023 ("Lost in the Middle"). *Why*: every charter design decision — where to put information, how much to load, what to pin — is downstream of how the model processes context.

**Week 3-4: Tools and feedback.** Tool protocol design, the schema tax, failure modes of agentic loops. Read: Anthropic tool use docs, Shinn 2023 ("Reflexion"), Yao 2023 ("ReAct"). *Why*: the PI needs to recognize when the agent is looping, drifting, or hallucinating tool calls — and know whether the fix is a prompt change, a tool change, or an architecture change.

**Week 5-6: Governance and knowledge architecture.** Context budget economics, adversarial review, commons governance. Read: Bush 1945 ("As We May Think"), Perez 2022 ("Red Teaming Language Models with Language Models"), Ostrom 1990 (*Governing the Commons* Ch. 1-3). *Why*: the PI designs the constitution, the charter format, and the enforcement process. These are governance decisions, not engineering decisions — and they require governance thinking.

**Short path (8 days):** Vaswani + "Lost in the Middle" (2 days) → Anthropic tool docs (1 day) → ReAct + Reflexion (2 days) → Bush + Anthropic long-context tips (1 day) → Perez + Ostrom (2 days).

## Getting Started Today

You don't need a Memex, a formal constitution, or a six-week syllabus to start. You need:

1. **One charter file.** Pick the most complex module in your codebase. Write a charter for it using the notation above. This takes 30-60 minutes and will teach you more about your code than a week of reading it.

2. **One rule in your entry point.** Add to your CLAUDE.md or equivalent: "Before modifying [module], read [charter file]." That's your constitution, version 0.1.

3. **One adversarial pass.** After your AI agent makes changes, ask a different model: "Read this charter and this diff. Did the change violate any documented constraints?" That's your enforcer, version 0.1.

Everything else — the cross-cutting charter, the dispatch table, the three-layer architecture, the formal enforcer — grows organically from these three steps.

---

**Source**: "Constitutional Architecture for AI-Assisted Software Development" (Cumberland Laboratories, 2026). Working reference implementation: [github.com/cumberland-laboratories/memex](https://github.com/cumberland-laboratories/memex) — see `memex/charters/` for philosophy, notation, and working examples.
