---
date: 2026-04-29
depth: medium
tags: [charters, constitutional-architecture, gist, onboarding, public]
source-thread: n/a
source: claude + ren
summary: Standalone guide to constitutional architecture for AI-assisted development — charters, notation, adversarial review, the feedback loop, and getting started. Intended for GitHub gist distribution.
---

# Constitutional Architecture for AI-Assisted Software Development

The core idea: **AI generates code faster than you can read it. You need a structural layer that preserves your comprehension at the speed code is now produced.** That structural layer is charters, governed by a constitution, validated by adversarial review.

This guide synthesizes several lines of work into a practical, integrated approach. It's opinionated — it proposes a specific architecture — but it builds on real problems that others have identified and are actively working on.

**Companion document:** The [Constitutional Architecture Starter Kit](https://gist.github.com/cumberland-laboratories/4ff65ab7ada163d603bf1cad8cf35e07) is the tactical counterpart to this guide — give it to an AI coding agent and it will build the full charter architecture for your codebase step by step.

## Prior work and the gap

**The comprehension problem has a name.** Addy Osmani's "[Comprehension Debt](https://www.oreilly.com/radar/comprehension-debt-the-hidden-cost-of-ai-generated-code/)" (O'Reilly, 2025) articulates the core issue precisely: "the growing gap between how much code exists in your system and how much of it any human being genuinely understands." AI-generated code breaks the traditional feedback loop — surface correctness masks systemic ignorance. He prescribes vigilance. This guide proposes structure.

**Constitutional governance is emerging.** Khaireh-Hoss et al.'s "[Constitutional Spec-Driven Development](https://arxiv.org/html/2602.02584v1)" (arXiv, 2026) uses a versioned constitution to constrain AI code generation *before* it happens — security requirements as machine-readable principles with CWE mappings and enforcement levels. It's governance with teeth, but it's focused on security constraints, not on giving the AI a map of the codebase it's about to modify.

**Tiered documentation for AI agents is being explored.** Vasilopoulos's "[Codified Context](https://arxiv.org/html/2602.20478v1)" (arXiv, 2026) builds a three-tier knowledge infrastructure for AI agents: a constitution (~660 lines), 19 agent specifications (~9,300 lines), and a knowledge base (~16,250 lines) — totaling ~26,200 lines for a 108K-line codebase. Specifications are "written explicitly for machine consumption," with trigger tables routing tasks to specialist agents by file pattern. This is the closest neighbor to the approach described here.

**Multi-model governance is on the horizon.** Bommena's "[LLM Council](https://medium.com/@srinib100/llm-council-a-new-architectural-governance-layer-for-the-ai-integrated-sdlc-5d879aab3d60)" (Medium, 2026) proposes cross-model governance at the organizational level — multiple models validating each other's work. The idea is sound. The missing piece is a shared, structured language precise enough to make that validation mechanical.

**What's missing is the integration.** Each of these addresses a piece of the problem:

| Work | Contribution | Gap |
|------|-------------|-----|
| Osmani (2025) | Named the comprehension problem | No structural solution — prescribes human vigilance |
| CSDD (2026) | Constitutional governance for security | No codebase map — constrains but doesn't orient |
| Codified Context (2026) | Tiered AI documentation | Heavy (~24% overhead) and no cross-model enforcement |
| LLM Council (2026) | Multi-model validation | No shared verification language at the code level |

Constitutional architecture integrates these into a single system: **lightweight charters** (~2% overhead, not 24%) that give the AI a verifiable map, **governed by a constitution** that enforces the lookup-before-modify discipline, **validated by cross-model adversarial review** using the charters as the shared language between agents.

---

## The problem

Before LLMs, code and comprehension scaled together — you wrote it, so you understood it. AI breaks that coupling. Your codebase grows without a corresponding growth in your understanding. You become a reviewer of output you didn't write, in a system that's expanding faster than you can read.

This isn't a tooling problem. It's a governance problem. The same problem organizations faced when they grew past the size where everyone could know everything. The solution then was constitutions and separation of powers — not smarter individuals. The solution now is the same.

## Three levels of documentation

Most projects have two levels of documentation. Constitutional architecture adds a third.

| Level | Audience | Purpose | Example |
|-------|----------|---------|---------|
| **Inline** | Developers reading code | Explain *what* and *why* at point of use | Code comments, docstrings |
| **Human-readable** | Humans navigating the system | Describe business flows and subsystems | Design docs, architecture docs, READMEs |
| **Charters** | LLMs modifying the code | Map every function's access patterns, dependencies, and tripwires | Per-module charter files with structured notation |

The first two levels are familiar. The third is new, and it's the one that changes the game.

**Charters are written for LLMs, by LLMs** (with human oversight). They use a notation optimized for how models process text — line anchors for verifiable location, access patterns for predicting side effects, and tripwire markers (`!`) that spike model attention through contradiction. A human *can* read them, but the primary consumer is the AI agent about to modify your code.

**Charters are intentionally short.** A charter for a 2,000-line module is 50-100 lines of structured notation — roughly 2% of the code it describes. This matters because every token loaded into an LLM's context window displaces something else. Charters earn their token cost by compressing architectural knowledge into a fraction of the tokens that loading the source files would require. The LLM gets the map without paying for the territory.

**LLM coding agents are uniquely good at this.** Tools like Claude Code and Codex are built to navigate cross-referenced markdown files — following `→` links between charters, reading the referenced function, checking the access patterns, tracing the dependency graph. This is exactly what these agents do well. The charter format exploits this strength: structured notation in linked markdown files is the native habitat of an agentic coding tool.

**The AI writes and maintains the charters.** The primary agent (your coding AI) explores the code, writes the charters, and updates them after changes — the human oversees but doesn't do the mechanical work. This is 99% AI labor. Is there risk of error? Of course. The agent might mischaracterize an access pattern, miss a cross-cutting dependency, or let a charter go stale. This is exactly why the enforcer exists: a *different* model audits the primary agent's charters against the actual code. The charters become the **lingua franca** between the primary agent and the enforcer — the shared, structured language they use to communicate about the codebase. The primary agent says "this function reads Submission and writes Grade." The enforcer checks: does it really? This only works because charters are precise enough to be mechanically verifiable. Prose documentation can't be audited this way. Charters can.

## What a charter looks like

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

## The cross-cutting charter

The most important charter in any set. It doesn't map to a single module — it maps to patterns that span modules.

Every codebase has behaviors that emerge from module interactions: a data flow that traverses four files, an implicit contract between a prompt and the code that parses its output, an invariant that must hold across every exit path. These are invisible in any individual charter. They're what breaks during refactors.

The cross-cutting charter documents these with `TRIPWIRE` labels. Read it first, every time.

## The constitution: closing the feedback loop

Charters are inert without governance. The constitution is a short document (one page) that tells the AI agent:

1. **Before modifying code, look up the relevant charter.** A dispatch table maps code paths to charter files — not "find the right charter" but "if you're changing `views_quiz.py`, read `charter-views_quiz.md` and `charter-cross_cutting.md`."
2. **After modifying code, update the charter.** Same commit, same PR, same operation. A stale charter is worse than no charter.
3. **The enforcer audits compliance.** A different model (not the one that wrote the code) checks charters against code and flags drift.

The chain: **Constitution → Charter Lookup → Read Charter → Modify Code → Update Charter → Enforcer Audit**. This is the feedback loop that prevents architectural decay.

## Adversarial design: use models against each other

Same-model review has blind spots — shared training biases create shared blind spots. Cross-model review is structurally stronger.

**The pattern**: Use one agent to write code (e.g., Claude Code), then use a different agent or model (e.g., Codex, Gemini) to critique it. The critic reads the charters, reads the code changes, and asks: *did this change violate any charter constraints? Did it introduce new cross-cutting concerns that aren't documented? Are the access patterns still accurate?*

This is the enforcer role. It doesn't edit — it audits. The primary agent (with the human present) reviews the audit and decides what to act on. Separation of powers, applied to code.

## The recipe

### For a new codebase:

1. **Write skeleton charters alongside skeleton code.** They force you to articulate module boundaries before writing implementations.
2. **Write the cross-cutting charter** as patterns emerge. Don't wait until the system is "done" — cross-cutting concerns appear early.
3. **Add the constitution rule**: "before modifying code, consult the relevant charters." Put the dispatch table in your CLAUDE.md, AGENTS.md, or equivalent entry point.
4. **Set up adversarial review.** Run a different model against the charters periodically. Even a quick pass catches drift.

### For an existing ("hopeless") codebase:

1. **Write charters first, code changes second.** The act of chartering a module forces you to understand it — and the AI does the work. Point your coding agent at a module and ask it to produce a charter. This is the most valuable step: even if you never refactor, you now have a map.
2. **Start with the god functions and the cross-cutting concerns.** These are where the complexity lives. Charter them, then decompose them with the charter as your invariant checklist.
3. **Use the charters as your refactoring safety net.** Every function's access patterns and cross-references tell you what will break when you move code. The `←` annotations are your blast radius.
4. **Update charters as you refactor.** The charter evolves with the code. After the refactor, you have both clean code and an accurate map.

## The three-layer documentation architecture

At scale, the three levels of documentation each serve a distinct audience:

1. **Inline** — code comments, docstrings, type annotations. Written by developers (or AI) for developers reading the code. Explains *what* and *why* at point of use.
2. **Charters** — per-module structured notation for the AI agent. Every function, its access patterns, tripwires, cross-references. The map the LLM reads before modifying code. Written by AI, verified by the enforcer.
3. **Human-readable** — design docs, architecture docs, flow narratives. Written for humans navigating the system at a business-flow level. Referencing charters for technical detail when needed.

Charters are the ground truth. Inline comments explain local decisions. Human-readable docs provide the big picture. The three layers serve different audiences and don't replace each other.

## The PI's learning path: let the system teach you

The human in this system is the PI (principal investigator) — they hold mission, taste, and architectural coherence. The AI handles execution; the PI handles judgment. But judgment requires knowledge, and the PI can't know everything about every codebase in advance.

This is where the constitutional architecture becomes self-teaching. The feedback loop — primary agent proposes, enforcer critiques, PI adjudicates — naturally surfaces the gaps in the PI's understanding. When the enforcer flags a stale access pattern and the primary agent disagrees, the PI needs to understand access patterns well enough to decide who's right. When the enforcer says a refactor violated a cross-cutting invariant, the PI needs to understand *that specific invariant* to adjudicate.

**The system generates its own syllabus.** Each disagreement between agent and enforcer is a learning opportunity targeted at exactly what the PI needs to know for *this* codebase. Over time, the PI builds domain expertise not by studying in the abstract, but by adjudicating real disputes grounded in real code — with the charters as the shared reference both sides are arguing from.

This means the constitution can include a directive: "When the PI adjudicates a dispute, capture the reasoning as a reference note — what was the disagreement, what did the PI decide, and why." Those notes accumulate into a codebase-specific body of architectural knowledge that makes future adjudications faster and more consistent. The PI doesn't need to know everything on day one. They need to know how to learn from the system's own feedback.

## Getting started today

You don't need a Memex, a formal constitution, or a six-week syllabus to start. You need:

1. **One charter file.** Pick the most complex module in your codebase. Write a charter for it using the notation above — or better, point your AI coding agent at it and ask it to produce one. This takes 30-60 minutes and will teach you more about your code than a week of reading it.

2. **One rule in your entry point.** Add to your CLAUDE.md or equivalent: "Before modifying [module], read [charter file]." That's your constitution, version 0.1.

3. **One adversarial pass.** After your AI agent makes changes, ask a different model: "Read this charter and this diff. Did the change violate any documented constraints?" That's your enforcer, version 0.1.

Everything else — the cross-cutting charter, the dispatch table, the three-layer architecture, the formal enforcer — grows organically from these three steps.

---

**References:**
- Osmani, A. (2025). "[Comprehension Debt: The Hidden Cost of AI-Generated Code](https://www.oreilly.com/radar/comprehension-debt-the-hidden-cost-of-ai-generated-code/)." O'Reilly Radar.
- Khaireh-Hoss, V. et al. (2026). "[Constitutional Spec-Driven Development: Enforcing Security by Construction in AI-Assisted Code Generation](https://arxiv.org/html/2602.02584v1)." arXiv.
- Vasilopoulos, A. (2026). "[Codified Context: Infrastructure for AI Agents in a Complex Codebase](https://arxiv.org/html/2602.20478v1)." arXiv.
- Bommena, S. (2026). "[LLM Council: A New Architectural Governance Layer for the AI-Integrated SDLC](https://medium.com/@srinib100/llm-council-a-new-architectural-governance-layer-for-the-ai-integrated-sdlc-5d879aab3d60)." Medium.
- Cumberland Laboratories (2026). "[Constitutional Architecture for AI-Assisted Software Development](https://cumberlandlaboratories.substack.com/p/constitutional-architecture-for-ai)." Substack.

**Working reference implementation:** [github.com/cumberland-laboratories/memex](https://github.com/cumberland-laboratories/memex) — see `memex/charters/` for philosophy, notation, and working examples.
