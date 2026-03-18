# Memex

## A persistence architecture that gives stateless LLMs continuous intelligence.

Memex is a governed markdown knowledge structure that LLMs maintain
and update across sessions. 

Instead of storing memories in opaque
model features or vector databases, the system maintains a transparent
wiki-like repository with explicit lifecycle rules.

The result: conversations that continue across sessions without
fine-tuning, proprietary infrastructure, or large context windows.

---

## What this means for you

Clone this repo.  Launch an agentic coding tool (Claude Code, Codex CLI, or Gemini CLI) from the repo root and start working as you would for any research project.

If the conversation is sufficient, Claude Code will save a thread for you automatically.  If you hit a point that is important to you, you can also say "let's make a note of this", or "let's record this please".  

This is how you will start to build a body of "threads" in the Memex.  Claude Code will maintain the threads and connections because it will follow the rules (constitution.md)

At a certain point, ask Claude Code to propose an idea or plan based on the threads you have built.  Now launch Codex from the repo root, and ask Codex to write a formal review of the plan.  Return to Claude Code and ask for an assessment of the Codex review.

Soon you will be researching with a primary agent (Claude Code) and an "enforcer" (Codex).  Codex — unemotional, cold — is suited for the enforcer role.  This is the best configuration we have found.  

Now close the session. Walk away. Come back tomorrow.

Start a new session with Claude Code and watch as it knows where to begin again — what you were working on, what's still open, and what to load to continue your research across sessions.

---

## Multi-model architecture

The rules file (constitution.md) is the interface contract. Any model that can read markdown and follow instructions can operate the Memex.

We handed this repo to OpenAI's Codex — no prompt engineering, no model-specific tuning. Just the rules file and the wiki. Codex didn't just read it — it operated in it. It assumed the enforcer role (auditing the wiki, producing reports), and it assumed the primary agent role upon request (updating pages, creating threads, providing substantive feedback).

Three vendors' models (Claude, Gemini, Codex) can all run on the same architecture, governed by the same rules file.  

Be warned however, that different models have a different temperament around following rules, just as humans do.  The best configuration for research is Claude Code as primary agent and Codex as an enforcer and critical reviewer.

The architecture outlives any individual model. The governance is in the files. 

---

## Not a message board, not a wiki

It borrows from both. Cross-linked pages from wikis. Thread lifecycle from message boards. But the thing it does that neither can:

### The knowledge layer maintains itself.

A wiki requires humans to keep it current. A message board lets everything sink under new activity. The Memex updates its own pages as a side effect of conversation — documentation nobody has to write.

### Orientation is pre-loaded, not searched.

A wiki waits for you to search it. A message board waits for you to browse it. The Memex loads your active working set before you say anything. The LLM already knows what you were working on yesterday.

### Governance is machine-readable.

A wiki has moderation norms. A message board has house rules. The Memex has an executable constitution — what to capture, what to ignore, when to compress, when to archive, who can do what. Encode the rules once, correctness follows by design.

### A hard budget prevents infinite growth.

Wikis grow forever. Message boards decay forever. The Memex keeps a fixed working set (~400 lines — roughly 8K tokens, leaving room for conversation in a 128K context window) and demotes everything else to reference. Active topics stay on the desk. Cold topics move to the filing cabinet. Nothing is deleted — it just costs less to carry.

### Importance is behavioral, not declared.

Wikis don't know what matters. Message boards use votes and views. The Memex tracks what you actually return to. The system self-organizes around real attention, not stated priorities.

---

## Efficient context preloading

Usable context is not the same as loading everything. The system is designed so that total context cost per session stays fixed — regardless of how large the archive grows.

### Three tiers, one working set

**Active threads** (5-8 files) load every session. These are your current topics — what you're working on this week. Hard-capped at ~400 lines total. This is the desk.

**Lightweight threads** live in the repo but never auto-load. They hold reference material, cooled-off topics, background knowledge. The LLM navigates to them on demand through cross-references — not search, not retrieval, but following links the way you'd click through a wiki.

**Artifacts** are deep records — synopses, research notes, conversation captures. Write-once, read-rarely. They exist to be *findable*, not to be in working memory. Tagged frontmatter and summaries let the LLM decide whether to load the full file.

### What connects the tiers

Every thread carries annotated cross-references — not just "see also" but *why the link exists*. The LLM enters through the active threads it already loaded and follows links outward as the conversation requires. The design constraint: any topic should be reachable within 3 hops from any other topic in the graph. The graph is the index. No central lookup table needed.

### What keeps it lean

- **Summaries as gatekeepers.** Every thread has a 2-4 sentence summary. The LLM can triage a directory by reading summaries without loading full files.
- **Frontmatter as metadata.** Tags, hit counts, last-touched dates — all in the first 6 lines. Enough to decide relevance without reading the body.
- **Compression as demotion.** When a thread gets too long or too stale, it compresses into a lighter form or splits into parts. Information moves deeper, not out.
- **The inbox separates capture from organization.** New thoughts get dropped in one file. The LLM triages them at session open. No mid-conversation restructuring.
- **The constitution is the boot sequence.** A new session reads one file, follows its procedure, loads the working set, and is oriented. Fixed cost, every time.

---

## How it stays honest

LLMs drift. They misinterpret rules, take shortcuts, and silently degrade state over time. A governed system that depends on good behavior isn't governed — it's lucky. The Memex addresses this with three layers of integrity checking.

### The enforcer

The writer never reviews its own work. A different model — from a different vendor — audits the Memex read-only and produces reports. It checks for contradictions between files, missing cross-references, structural drift from the constitution, and bloat. It does not edit. It reports. The human reviews the findings and decides what to act on.

This is not optional redundancy. It is the mechanism that turns soft governance into something closer to hard governance. Same-model review catches formatting errors. Cross-model review catches assumption errors.

### The lint script

`scripts/memex-lint.sh` is a deterministic mechanical check — no model required. It verifies compression budgets, thread sizes, frontmatter structure, cross-reference integrity, and orphan detection. It answers the question: does the Memex comply with its own constitution right now?

The lint script catches what models miss: silent structural decay. A thread that grew past 60 lines. A cross-reference pointing to a file that was renamed. An artifact missing required frontmatter fields. These are not judgment calls — they are invariant violations that a shell script can flag in seconds.

### The rendered wiki

`scripts/generate_wiki.py` and `scripts/generate_markdown.py` render the thread graph into human-readable documentation. This is the third check: the human reads the output. Threads that looked fine as individual files may reveal gaps, redundancies, or broken narratives when rendered as a coherent document.

The rendered wiki is an audit surface, not just a presentation layer. If something is wrong in the Memex, you'll see it in the wiki before you see it in the files.

### The honest assessment

Is this airtight? No. The enforcer can miss things. The lint script only catches what it's programmed to check. The wiki render depends on someone reading it. But the combination — model audit, mechanical check, human review — creates overlapping coverage that no single layer provides alone. The system degrades gracefully rather than silently.

---

## Getting started

```bash
git clone https://github.com/cumberland-laboratories/memex.git
cd memex
```

Or just download the files. The Memex is constructed with markdown, git, interchangeable LLMs, and governance rules.

---

## Repo structure

```
constitution.md             ← the rules file (governs everything)
memex/
  identity.md               ← who you are (you fill this in over time)
  inbox.md                  ← zero-friction capture (drop anything here)
  active-threads/            ← current topics (loaded every session)
  threads/                   ← reference threads (loaded on demand)
  artifacts/                 ← deep records, synopses (loaded on demand)
  patterns/                  ← recurring obligations (bills, renewals)
  vault/                     ← external files: PDFs, papers (gitignored)
  procedures/                ← how the system operates
  reference-notes/           ← design rationale and cognitive aids
scripts/                     ← optional lint and render tools
```

---

## License

MIT. See [LICENSE](LICENSE).
