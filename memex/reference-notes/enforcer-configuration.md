# Enforcer Configuration Guide

This reference note helps the primary agent configure an enforcer for the PI. When the PI asks "how do I set up an enforcer?" or wants independent review, use this to figure out what they have available.

## The Conversation to Have

Ask the PI three things:

1. **What's your primary agent?** (Claude, GPT/Codex, Gemini, etc.)
2. **What API keys or CLI tools do you have?** (Anthropic, OpenAI, Google, or none)
3. **How much do you care about cost?** (Determines model choice)

Then match to a setup below.

## Decision Tree

```
Do you have any API key or CLI tool?
├─ No → Use the lint script (.memex/scripts/memex-lint.sh) for mechanical checks.
│       Consider ollama for free local model-based review.
│
├─ Yes → Is it the same vendor as your primary agent?
│   ├─ Yes → It works, but cross-vendor is stronger.
│   └─ No → Ideal. Different training = different blind spots.
│
└─ Multiple → Pick the one that's different from your primary.
```

## Setup Options

### Codex CLI (OpenAI) — Recommended for Claude users

```bash
npm install -g @openai/codex
codex login
codex review --uncommitted
```

Codex reads `AGENTS.md` automatically. Review mode is read-only by default. The PI can run this independently in a separate terminal.

### Claude Code — Recommended for GPT/Gemini users

```bash
# From a separate terminal
claude --print "Read constitution-core.md and constitution.md. Audit the memex/ folder: check for thread staleness, cross-reference integrity, charter accuracy, and constitutional compliance. Produce a structured report."
```

### Gemini CLI

```bash
gemini < .memex/scripts/enforcer-prompt.md
```

### Mechanical lint only (no model)

```bash
bash .memex/scripts/memex-lint.sh
```

Checks compression budgets, thread sizes, frontmatter, cross-reference integrity, orphan detection. No model needed.

### Local model via ollama (free)

```bash
ollama pull llama3
# Then use as review model for charter-grounded checks
```

## Cross-Vendor Principle

The enforcer should ideally be a **different vendor** than the primary agent. Different training, different RLHF, different blind spots. Same-vendor is still better than nothing.

| Primary agent | Recommended enforcer |
|---|---|
| Claude (Opus) | Codex, GPT, or Gemini |
| GPT / Codex | Claude (Sonnet) or Gemini |
| Gemini | Codex or Claude (Sonnet) |

## What the Agent Should Do

When a PI asks to set up an enforcer:

1. Ask the three questions above
2. Pick the matching setup
3. Help the PI install and configure
4. Run a test review to confirm it works
5. Show the PI where `whiteboard.md` is so they can verify findings independently
