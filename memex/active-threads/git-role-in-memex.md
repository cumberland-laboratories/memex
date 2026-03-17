---
last-touched: 2026-03-17
category: systems
hits: 1
tags: [git, memex, version-control, branching, backup, infrastructure]
---

# Git's Role in the Memex

## Summary

Git serves double duty in the Memex: backup (push to remote = offsite copy) and version history. The dev/main branching convention, inherited from software engineering, deserves scrutiny — it was designed for release gating in collaborative codebases, and the Memex is neither collaborative nor release-gated. The question is whether the branching overhead buys anything a single-branch workflow doesn't already provide.

## Detail

**What git clearly provides:**

- **Backup via push.** The Memex lives in a repo; pushing to a remote is an automatic offsite backup. This alone justifies git's presence.
- **History.** Every structural change — thread creation, demotion, split, compression — is recorded. `git log` and `git diff` replace a changelog. The constitution already says "use `git log`" for this.
- **Rollback.** If a session makes bad edits (botched compression, lost cross-references), `git revert` or `git checkout` recovers cleanly.

**What the dev/main split is supposed to provide (in software):**

- `main` = stable, deployable, reviewed code
- `dev` = work-in-progress that might break things
- The gap between them is a review gate: code moves main → dev only after passing checks

**Why that logic doesn't obviously transfer:**

- The Memex has no "deployment." There's no consumer who needs `main` to be stable while `dev` is messy.
- There's no CI, no test suite, no merge review. The enforcer audits the Memex but doesn't gate merges.
- The single operator (human + chat agent) works on one branch at a time. There's no parallel development that needs isolation.
- Every session currently does: work on dev → merge to main → push. If the merge is always immediate and fast-forward, `dev` and `main` are the same branch with extra steps.

**Where it might earn its keep:**

- **Enforcer staging.** If the enforcer eventually runs against `main` while the chat agent works on `dev`, the branch split becomes a real gate: `main` reflects the last audited state, `dev` reflects the current session's work. The merge happens after the enforcer blesses it (or the human reviews the audit).
- **Multi-session safety.** If two agents (e.g., Codex producing a report while Claude runs a session) both write to the Memex, branches prevent collisions. But the whiteboard already handles coordination, and simultaneous writes are rare.
- **Checkpoint discipline.** Even without a gate, "commit to dev, merge to main at end of session" creates a natural rhythm: main always reflects a complete session, never a half-finished one. But `git tag` or even just disciplined commit messages could do this without a second branch.

**The honest assessment:**

Right now, dev/main is ritual without function. The merge is always fast-forward, always immediate, always approved. It adds two commands per session (`checkout main`, `merge dev`) with no decision point between them. The convention was set in the constitution as a default, not derived from a requirement.

It becomes functional *if and when* either (a) the enforcer gates merges, or (b) multiple operators write concurrently. Until then, it's a placeholder for a future gate.

## Connections

→ [constitution.md](../../constitution.md) — defines the dev/main convention and enforcer role
→ [knowledge-systems-comparison.md](knowledge-systems-comparison.md) — scaling analysis that implies future enforcer automation, which could activate the branch gate
→ [tooling-roadmap.md](../reference-notes/tooling-roadmap.md) — Crawler and Spider operators that might eventually write to dev

## Open Questions

- Should the constitution downgrade to single-branch until the enforcer actually gates merges?
- If we keep two branches, should `main` represent "last audited state" rather than "mirror of dev"?
- Is there a lighter mechanism (tags, commit conventions) that provides the same checkpoint value?
- Does the Codex/Claude multi-operator case actually need branch isolation, or is whiteboard + sequential access enough?
