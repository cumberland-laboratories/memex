# Procedure: Documentation Render (Current Target: Wiki)

## Output

Current default outputs:

- `wiki/Main_Page.wiki` in MediaWiki markup
- `wiki/Main_Page.md` in Markdown

The stable concept is the **documentation render**. MediaWiki is just the first render target.

## Command

```bash
python scripts/generate_wiki.py
python scripts/generate_markdown.py
```

## Pipeline

Fully mechanical. No LLM synthesis is used during thread rendering.

Design principle: **the Memex owns structure; renderers own presentation.**

1. **Parse frontmatter** — extract `category`, `tags`, `hits`, `last-touched` from every thread. Build table of contents and sort order.
2. **Resolve title** — use `title:` from frontmatter if present; otherwise use the first `#` heading; otherwise derive from filename.
3. **Group and sort** — categories become wiki sections in fixed order: mathematics, cognition, systems, ventures, economics, civic. Within each category, sort by `hits` descending, then `last-touched` descending, then title ascending.
4. **Extract `## Summary`** — each thread's Summary section is the wiki entry. If a thread lacks a Summary, render a visible missing-summary notice rather than synthesizing content.
5. **Translate cross-references** — read `## Connections`; convert links that resolve to other thread files into renderer-local "See also" links. In the current MediaWiki target this becomes `'''See also:''' [[#Target Title|Link Label]] (annotation)`. In Markdown it becomes `[Link Label](#target-title) - annotation`. Ignore links to artifacts, reports, and external targets in single-page outputs.
6. **Template into target format** — each thread renders as: heading, metadata line (`tier`, `hits`, `last touched`, `tags`), Summary, then See also.
7. **Render identity section** — `identity.md` renders mechanically from fixed sections: `Background`, `Intellectual Disposition`, `Working Style`, `Civic Engagement`, `Interests`.
8. **Add header** — render date, thread count, category count, plus a fixed note that the wiki is a render.

## Scope Discipline

Keep the render layer simple and lightweight:

- one canonical parsed thread model
- one mechanical extraction pipeline
- thin target-specific format adapters
- minimal configuration

Do not build a plugin system or platform-specific schema until multiple targets actually require it.

## Who Runs This

**Current architecture:** The primary agent runs the generator on request or after substantial Memex updates.

**Future architecture:** The enforcer or a scheduled job may run the same command. The operation remains read-only on `memex/` and writes only to `wiki/`.

## Access

**Read-only** on the Memex. **Write** only to `wiki/` directory.

## Notes

- `wiki/Main_Page.wiki` and `wiki/Main_Page.md` are single-page renders of the thread graph, not separate pages per thread.
- Thread prose is extracted from `## Summary` only. Detail sections, Open Questions, and Next Up do not render into the output.
- Identity rendering is deterministic because the source sections are fixed by name.
- If the output looks wrong, fix the Memex source or the generator — do not hand-edit generated render files.
- Future targets should reuse the same parsed thread graph and differ only in formatting.
- When a second target is added, prefer a new lightweight renderer script or adapter over expanding thread semantics.
