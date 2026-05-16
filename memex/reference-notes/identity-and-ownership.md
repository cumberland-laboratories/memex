# Identity and Ownership Context

## The Problem

When you bootstrap a fresh Memex, you don't know who you're talking to or how many people share this repo. Getting this wrong early creates friction that compounds:

- In a **solo Memex**, one person is the PI. Identity and mission are tightly coupled. Learn their preferences, role, context — it all belongs in `identity.md`.
- In a **team Memex**, multiple people share the `memex/` folder. The project is the stable identity, not any individual. Writing the knowledge layer around one person's perspective alienates everyone else.

## The Rule

**Don't assume. Ask.**

Before populating `identity.md` or `mission.md`, establish:

1. **Is this solo or team?** ("Is this your project, or does a team share this repo?")
2. **Who is the PI?** Solo: obvious. Team: there may be one PI, rotating PIs, or shared ownership.
3. **Where does individual context belong?** Solo: `identity.md` freely. Team: individual preferences stay outside the shared knowledge layer.

## What This Means in Practice

**Solo**: `identity.md` reflects the person's goals, style, priorities. Threads and inbox can be informal. The whole `memex/` folder is theirs.

**Team**: `mission.md` describes the *project's* goals, not any individual's. Keep it neutral and factual. If team members need individual context, that lives outside `memex/`.

## The Cost of Getting It Wrong

If you pin identity to a person in a team Memex:
- Other contributors feel like guests in their own project
- `mission.md` reads like one person's vision
- Threads carry implicit bias toward one perspective

If you treat a solo Memex as a team Memex:
- The knowledge layer feels impersonal and bureaucratic
- You miss opportunities to tailor the experience

One question at bootstrap prevents it.
