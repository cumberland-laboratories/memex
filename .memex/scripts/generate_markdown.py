#!/usr/bin/env python3
"""Render the Memex thread graph into Markdown."""

from __future__ import annotations

import argparse
import datetime as dt
import re
from pathlib import Path

from generate_wiki import (
    CATEGORY_ORDER,
    IDENTITY_SECTIONS,
    category_threads,
    extract_links,
    load_threads,
    parse_identity,
    section_blocks,
)


LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


def slugify_heading(text: str) -> str:
    slug = text.strip().lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"\s", "-", slug)
    return slug


def convert_inline(text: str, title_lookup: dict[Path, str], source_dir: Path) -> str:
    def replace_link(match: re.Match[str]) -> str:
        label = match.group(1)
        raw_target = match.group(2)
        if raw_target.endswith(".md"):
            target_path = (source_dir / raw_target).resolve()
            target_title = title_lookup.get(target_path)
            if target_title:
                return f"[{label}](#{slugify_heading(target_title)})"
        return label

    return LINK_RE.sub(replace_link, text)


def render_markdown_lines(
    lines: list[str], title_lookup: dict[Path, str], source_dir: Path
) -> list[str]:
    rendered: list[str] = []
    for kind, block in section_blocks(lines):
        if kind == "bullet":
            for line in block:
                rendered.append("- " + convert_inline(line.lstrip()[2:], title_lookup, source_dir))
        else:
            paragraph = " ".join(line.strip() for line in block)
            rendered.append(convert_inline(paragraph, title_lookup, source_dir))
        rendered.append("")

    if rendered and rendered[-1] == "":
        rendered.pop()
    return rendered


def render_identity(identity_path: Path, title_lookup: dict[Path, str]) -> list[str]:
    sections = parse_identity(identity_path)
    rendered = ["## About the Operator", ""]
    for section_name in IDENTITY_SECTIONS:
        lines = sections.get(section_name, [])
        if not lines:
            continue
        rendered.append(f"### {section_name}")
        rendered.extend(
            render_markdown_lines(lines, title_lookup=title_lookup, source_dir=identity_path.parent)
        )
        rendered.append("")
    if rendered[-1] == "":
        rendered.pop()
    return rendered


def render_see_also(thread, title_lookup: dict[Path, str]) -> list[str]:
    items: list[str] = []
    seen: set[Path] = set()
    for link in extract_links(thread.connection_lines, thread.source_path):
        if link.target_path is None or link.target_path in seen:
            continue
        target_title = title_lookup.get(link.target_path)
        if not target_title:
            continue
        seen.add(link.target_path)
        item = f"- [{link.label}](#{slugify_heading(target_title)})"
        if link.annotation:
            item += f" - {link.annotation}"
        items.append(item)
    return items


def render_thread(thread, title_lookup: dict[Path, str]) -> list[str]:
    lines = [
        f"### {thread.title}",
        "",
        f"*{thread.tier_label} | hits: {thread.hits} | last touched: {thread.last_touched} | tags: {', '.join(thread.tags)}*",
        "",
    ]

    if thread.summary_lines:
        lines.extend(
            render_markdown_lines(
                thread.summary_lines,
                title_lookup=title_lookup,
                source_dir=thread.source_path.parent,
            )
        )
    else:
        lines.append("*Missing Summary section in source thread.*")

    see_also = render_see_also(thread, title_lookup)
    if see_also:
        lines.extend(["", "**See also**", ""])
        lines.extend(see_also)
    return lines


def render_main_page(repo_root: Path, output_path: Path) -> str:
    memex_dir = repo_root / "memex"
    identity_path = memex_dir / "identity.md"
    threads = load_threads(memex_dir)
    title_lookup = {thread.source_path.resolve(): thread.title for thread in threads}
    grouped = category_threads(threads)

    today = dt.date.today().isoformat()
    lines = [
        "# Memex - Personal Knowledge System",
        "",
        f"**Last rendered:** {today}  ",
        f"**Threads:** {len(threads)}  ",
        f"**Categories:** {len(CATEGORY_ORDER)}",
        "",
        "This page is auto-generated from the Memex thread graph. The Memex is the source of truth; this file is a rendered summary for human navigation.",
        "",
        "**To regenerate:** `python .memex/scripts/generate_wiki.py && python .memex/scripts/generate_markdown.py`",
        "",
        "**Memex CLI** (`python .memex/scripts/memex.py`):",
        "- `memex status` — graph health, inbox count, patterns due, active threads (`--full` for complete state dump)",
        "- `memex search <query>` — full-text search across threads, artifacts, designs, reports",
        "- `memex read <type> <name>` — render thread/artifact/design/report (`--section` for specific sections)",
        "- Add `--format json` for structured agent output, `--role <name>` for role-aware views",
        "",
    ]

    lines.extend(render_identity(identity_path, title_lookup))
    lines.extend(["", "", "## Categories", ""])

    for key, label in CATEGORY_ORDER:
        titles = [thread.title for thread in grouped.get(key, [])]
        if not titles:
            continue
        lines.append(f"- [{label}](#{slugify_heading(label)}) - {', '.join(titles)}")

    for key, label in CATEGORY_ORDER:
        category_items = grouped.get(key, [])
        if not category_items:
            continue
        lines.extend(["", "", f"## {label}", ""])
        for thread in category_items:
            lines.extend(render_thread(thread, title_lookup))
            lines.extend(["", ""])

    while lines and lines[-1] == "":
        lines.pop()

    lines.extend(
        [
            "",
            "",
            "_This Markdown render was generated mechanically from the Memex thread graph. Summaries are extracted from source threads; no thread prose is synthesized during rendering._",
            "",
        ]
    )

    text = "\n".join(lines)
    output_path.write_text(text, encoding="utf-8")
    return text


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        default=Path(__file__).resolve().parents[2],
        type=Path,
        help="Path to the repository root.",
    )
    parser.add_argument(
        "--output",
        default=Path("docs/wiki/Main_Page.md"),
        type=Path,
        help="Output path, relative to repo root unless absolute.",
    )
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    output_path = args.output
    if not output_path.is_absolute():
        output_path = repo_root / output_path

    render_main_page(repo_root=repo_root, output_path=output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
