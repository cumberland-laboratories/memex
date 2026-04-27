---
last-touched: 2026-04-27
category: reference
tags: [charters, philosophy, architecture, comprehension, ai-assisted-development, notation]
---

# Why Charters

## Summary

Charters solve a comprehension problem, not a documentation problem. When AI generates code faster than a human can review it line-by-line, the human stops being the architect of their own system — unless there's a structural layer that preserves comprehension at the speed code is now produced. Charters are that layer. This note makes the philosophical case and describes the two levels of charter granularity. For the practical recipe, see -> [Codebase Charter Pattern](codebase-charter-pattern.md).

## The Problem

The bottleneck in AI-assisted development is not code generation. Models are good at writing code. The bottleneck is *comprehension* — the human's ability to understand, evaluate, and direct the system they're nominally in charge of.

Before LLMs, code and comprehension scaled together: you wrote it, so you understood it. AI breaks that coupling. Code volume grows without a corresponding growth in human understanding. The developer becomes a reviewer of output they didn't write, in a codebase that's growing faster than they can read.

This is not a tooling problem. It's a governance problem. The same problem organizations faced when they grew beyond the size where everyone could know everything: you need institutional structures — constitutions, charters, separation of powers — not smarter individuals.

## The Inversion

Traditional documentation describes code. You write the code first, then document it. The documentation is secondary, the code is primary.

Charters invert this relationship.

The charter network — function signatures, access patterns, cross-references, tripwires — is the primary artifact the human works with. It's the layer where architectural decisions are legible, where you can reason about the system without reading every file. The code is the *implementation* of what the charters describe. AI reads the code; humans read the charters; the charters keep them synchronized.

This is the same inversion the Memex makes at a larger scale: you navigate the graph, not the filesystem. Charters are the Memex pattern applied to code — a small-world network of cross-referenced nodes where you enter any module and follow links to understand the whole.

## Session Zero

Every reader — human or LLM — arrives at a codebase with zero history. They don't know why a function exists, what invariants it assumes, or which design decisions look wrong but are intentional.

Code alone doesn't fix this. Code tells you *what* the system does. It doesn't tell you *why* it's shaped this way, *what state it reads and writes*, or *what the system deliberately doesn't do*. These are the things that matter most when you're about to make a change, and they're invisible in the source.

Charters surface what cannot be inferred from reading code:

- **Access patterns**: what a function reads and writes — models, session state, caches, external APIs — so you can predict side effects without reading the body
- **Dependency direction**: what calls this function (`←`) and what it calls (`→`) — so you know what breaks when you change it
- **Tripwires**: the non-obvious patterns that *must* be preserved — rendering dualities, race conditions, intentional workarounds that look like bugs
- **Negative space**: what the system deliberately lacks, stated explicitly to prevent false assumptions

That last point matters especially for LLMs. A model's training data creates priors about what systems "should" have. If your system intentionally omits error retry, or deliberately uses a naive algorithm, the model will "fix" it unless the charter says otherwise. Negative space documentation corrects false priors before they become false code.

## Two Levels of Charter

Charters operate at two granularities that serve different purposes. Both are legitimate charter formats; which one you need depends on the size of the codebase and what you're trying to do.

### Function-Level Charters (the original format)

The format from the Constitutional Architecture paper, battle-tested on a 97K-line production codebase. Each charter covers a code module, and each *function* within that module gets its own block with a fixed notation:

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

| Symbol | Meaning | Why it exists |
|--------|---------|---------------|
| `[Lnnn]` | Line anchor | Verifiable location — if the function isn't near this line, the charter is stale |
| `(R)/(W)/(RW)` | Access pattern | Predicts side effects without reading code — `(R)` is safe to call, `(RW)` requires checking downstream effects |
| `!` | Tripwire | Inverts the reader's assumption — the paper argues this spikes LLM attention on contradiction |
| `→` | Outbound cross-reference | "This function depends on..." — follow to understand downstream effects |
| `←` | Inbound cross-reference | "This function is called by..." — follow to understand blast radius |
| `Session R:` / `Session W:` | State access | Tracks untyped state (session dicts, Redis keys) that code analysis alone can't reveal |
| `TRIPWIRE` | Section-level danger label | Flags architectural patterns that span multiple functions and must be preserved as a unit |

This is the format that drove a successful large-scale refactor. The charters were created *before* the refactor as a way to understand the monolith, and they served four roles during the work:

1. **Navigation map**: every function, its line number, and its cross-module dependencies — so the agent could trace call chains without reading every file
2. **Dependency graph**: the `←` and `→` annotations show what calls what, so you know what will break when moving code
3. **Tripwire documentation**: the `!` annotations flag dangerous patterns that must be preserved during refactoring
4. **Invariant checking**: after moving code, verify that all charter-documented call paths still work

### Module-Level Charters (simplified form)

For smaller codebases where function-level detail is overkill, a module-level format answers five questions per module:

1. **What does this module own?** Single responsibility as a noun phrase.
2. **What does it NOT own?** Boundaries that prevent accretion.
3. **What are its inputs and outputs?** Concrete: signatures, formats, side effects.
4. **Where does it connect?** Import relationships and dependency direction.
5. **What should you know before changing it?** Institutional knowledge — the non-obvious.

This format works at the *architecture* level: deciding where to put new code, understanding module boundaries, onboarding to a small project. It's the format used for tinyagent's charters. For the practical recipe, see -> [Codebase Charter Pattern](codebase-charter-pattern.md).

### When to use which

| | Function-level | Module-level |
|---|---|---|
| **Codebase size** | Large (10K+ lines) | Small (under 10K lines) |
| **Purpose** | Safe code changes | Architectural orientation |
| **Key value** | Access patterns, tripwires, line anchors | Boundaries ("does not own") |
| **Audience** | Agent about to *modify* specific code | Agent deciding *where* to put code |
| **Maintenance cost** | Higher — line numbers shift, functions move | Lower — module boundaries change slowly |

A large project may use both: module-level charters for orientation, function-level charters for the modules where code changes happen. The module-level format is not a replacement for the function-level format — it's a different tool for a different job.

## The Three-Layer Documentation Architecture

In a mature codebase, charters are one layer of a three-layer structure:

1. **Charters** — per-module API references. Every public function, its line number, what it reads/writes, what models it touches, session keys, cross-references, and tripwires. Organized by code structure. The machine-readable map.
2. **Designs** — flow-oriented user journey documents. Each one describes a complete business flow (checkout, authentication, quiz-taking) from the user's perspective, referencing charters for technical detail. Organized by what the user does.
3. **Systems** — infrastructure and subsystem documentation. How specific subsystems work (CI/CD, caching, rendering pipeline). Technical reference.

Charters are the ground truth. Designs are generated *from* charters as a more human-readable layer. Systems docs cover the infrastructure charters don't reach. The layers serve different audiences and don't replace each other.

## Why Boundaries Matter More Than Descriptions

A description of what a module does is useful. A declaration of what it does *not* do is essential.

Without explicit boundaries, modules grow. Every feature that "sort of" relates to a module's purpose gets added there. Over time, modules become god objects — and comprehension collapses, because you can no longer hold a module's responsibility in your head.

Boundaries are enforceable in a way descriptions are not. "Owns session persistence" is a description — it tells you what's here but doesn't prevent you from adding API logic too. "Does not own API calls" is a boundary — it gives a concrete reason to put that code somewhere else. When an LLM is generating code and deciding where to put a new function, the boundary is what keeps the architecture from degrading.

This is governance, not documentation. Constitutions work not because they describe what a government does, but because they define what it *may not* do.

## The Maintenance Obligation

Charters that fall out of sync with code are worse than no charters — a wrong map is more dangerous than no map. This isn't a best-effort suggestion. It's a structural obligation.

The update chain runs: **code change → charter update → design doc update**. If you change a function's signature, access patterns, or cross-references, the charter must be updated in the same operation. Not "later." Not "when we get to it." The charter is part of the change, the same way a migration is part of a schema change.

Line anchors `[Lnnn]` serve double duty here: they're both navigation aids and staleness detectors. When an LLM reads `apply_grade [L45]` and opens the file to find the function at line 300, it knows the charter is stale before it trusts anything else in the entry.

This obligation should be embedded in project governance (the constitution, procedures, or PR checklists), not left to individual discipline. Discipline decays. Structure persists.

## Charters and LLMs

Charters are disproportionately effective for LLM-assisted development, for four specific reasons:

**Token efficiency.** Loading every source file into context to understand a system is expensive and often impossible. A charter set compresses a 97K-line codebase into ~20 files of structured notation — function signatures, access patterns, cross-references, and tripwires for the entire system. The LLM gets the map without paying for the territory.

**Access pattern prediction.** `Models: Submission(R), Grade(W), Enrollment(RW)` tells the LLM exactly what a function mutates without reading a single line of the body. For session state — often an untyped dictionary with hundreds of references across dozens of files — `Session R:` / `Session W:` annotations are the *only* way to track state flow without loading every file.

**Tripwire attention.** The `!` notation exploits how models process text: contradiction spikes attention. When a charter says `! The instructor sees raw_score, but Grade.score is penalty-adjusted — these are different numbers`, the model's prediction is immediately corrected at the point of maximum relevance. This is more salient than burying the same information in a prose paragraph or code comment.

**Negative space correction.** Training-data priors are strong and often wrong for your specific system. Charters are the cheapest way to override them — a single line saying "no retry logic; failures are intentional signals" prevents the model from "improving" your design. The `TRIPWIRE` label on cross-cutting patterns (like a Q1/Q2+ rendering duality) tells the model "this looks wrong but it's not — preserve it."

## Connections

-> [Codebase Charter Pattern](codebase-charter-pattern.md) — the practical recipe: module-level five questions, when to write, where they live, anti-patterns
-> tinyagent function-level charters: [Agent Loop](../artifacts/2026-04-27-charter-agent-loop.md) | [Context Budget](../artifacts/2026-04-27-charter-context-budget.md) | [Infrastructure](../artifacts/2026-04-27-charter-infrastructure.md) | [Tools](../artifacts/2026-04-27-charter-tools.md) — worked example of function-level notation on a small codebase
-> [tinyagent Module-Level Charters](../artifacts/2026-04-12-tinyagent-module-charters.md) — historical example of module-level five-question format (superseded)
-> [Error Recovery as Design](../active-threads/error-recovery-as-design.md) — the "failures are information" principle connects to negative space: don't let an LLM "fix" intentional error exposure
-> Source essay: "Constitutional Architecture for AI-Assisted Software Development" (Cumberland Laboratories, 2026)
