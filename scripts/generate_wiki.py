#!/usr/bin/env python3
"""Render the Memex thread graph into MediaWiki markup."""

from __future__ import annotations

import argparse
import datetime as dt
import re
from dataclasses import dataclass
from pathlib import Path


CATEGORY_ORDER = [
    ("mathematics", "Mathematics"),
    ("cognition", "Cognition"),
    ("systems", "Systems"),
    ("ventures", "Ventures"),
    ("economics", "Economics"),
    ("civic", "Civic"),
]

IDENTITY_SECTIONS = [
    "Background",
    "Intellectual Disposition",
    "Working Style",
    "Civic Engagement",
    "Interests",
]

THREAD_DIRECTORIES = [
    ("active-threads", "Active thread"),
    ("threads", "Reference thread"),
]

LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


@dataclass
class Link:
    label: str
    annotation: str
    target_path: Path | None


@dataclass
class Thread:
    source_path: Path
    tier_label: str
    category: str
    hits: int
    last_touched: str
    tags: list[str]
    title: str
    summary_lines: list[str]
    connection_lines: list[str]


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        return {}, text

    parts = text.split("---\n", 2)
    if len(parts) < 3:
        return {}, text

    _, raw_frontmatter, body = parts
    frontmatter: dict[str, str] = {}
    for line in raw_frontmatter.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        frontmatter[key.strip()] = value.strip()
    return frontmatter, body


def parse_sections(body: str) -> tuple[str | None, dict[str, list[str]]]:
    h1: str | None = None
    sections: dict[str, list[str]] = {}
    current_section: str | None = None

    for line in body.splitlines():
        if line.startswith("# ") and h1 is None:
            h1 = line[2:].strip()
            continue
        if line.startswith("## "):
            current_section = line[3:].strip()
            sections[current_section] = []
            continue
        if current_section is not None:
            sections[current_section].append(line)

    return h1, sections


def parse_tags(raw_tags: str) -> list[str]:
    raw_tags = raw_tags.strip()
    if raw_tags.startswith("[") and raw_tags.endswith("]"):
        raw_tags = raw_tags[1:-1]
    if not raw_tags:
        return []
    return [item.strip() for item in raw_tags.split(",") if item.strip()]


def fallback_title(path: Path) -> str:
    return path.stem.replace("-", " ").replace("_", " ").title()


def parse_iso_date(value: str) -> dt.date:
    return dt.date.fromisoformat(value)


def load_thread(path: Path, tier_label: str) -> Thread:
    text = path.read_text(encoding="utf-8")
    frontmatter, body = parse_frontmatter(text)
    h1, sections = parse_sections(body)

    title = frontmatter.get("title") or h1 or fallback_title(path)
    summary_lines = sections.get("Summary", [])
    connection_lines = sections.get("Connections", [])

    return Thread(
        source_path=path,
        tier_label=tier_label,
        category=frontmatter["category"],
        hits=int(frontmatter.get("hits", "0")),
        last_touched=frontmatter["last-touched"],
        tags=parse_tags(frontmatter.get("tags", "")),
        title=title,
        summary_lines=summary_lines,
        connection_lines=connection_lines,
    )


def load_threads(memex_dir: Path) -> list[Thread]:
    threads: list[Thread] = []
    for folder_name, tier_label in THREAD_DIRECTORIES:
        folder = memex_dir / folder_name
        for path in sorted(folder.glob("*.md")):
            if path.name == "_TEMPLATE.md":
                continue
            threads.append(load_thread(path, tier_label))
    return threads


def section_blocks(lines: list[str]) -> list[tuple[str, list[str]]]:
    blocks: list[tuple[str, list[str]]] = []
    current: list[str] = []
    current_kind: str | None = None

    for raw_line in lines:
        line = raw_line.rstrip()
        if not line.strip():
            if current:
                blocks.append((current_kind or "paragraph", current))
                current = []
                current_kind = None
            continue

        kind = "bullet" if line.lstrip().startswith("- ") else "paragraph"
        if current and kind != current_kind:
            blocks.append((current_kind or "paragraph", current))
            current = []
        current.append(line)
        current_kind = kind

    if current:
        blocks.append((current_kind or "paragraph", current))

    return blocks


def convert_inline(text: str, title_lookup: dict[Path, str], source_dir: Path) -> str:
    def replace_link(match: re.Match[str]) -> str:
        label = match.group(1)
        raw_target = match.group(2)
        if raw_target.endswith(".md"):
            target_path = (source_dir / raw_target).resolve()
            target_title = title_lookup.get(target_path)
            if target_title:
                return f"[[#{target_title}|{label}]]"
        return label

    text = LINK_RE.sub(replace_link, text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"'''\1'''", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"''\1''", text)
    return text


def render_markdown_lines(
    lines: list[str], title_lookup: dict[Path, str], source_dir: Path
) -> list[str]:
    rendered: list[str] = []
    for kind, block in section_blocks(lines):
        if kind == "bullet":
            for line in block:
                content = line.lstrip()[2:]
                rendered.append("* " + convert_inline(content, title_lookup, source_dir))
        else:
            paragraph = " ".join(line.strip() for line in block)
            rendered.append(convert_inline(paragraph, title_lookup, source_dir))
        rendered.append("")

    if rendered and rendered[-1] == "":
        rendered.pop()
    return rendered


def extract_links(lines: list[str], source_path: Path) -> list[Link]:
    links: list[Link] = []
    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue
        match = LINK_RE.search(line)
        if not match:
            continue

        label = match.group(1)
        raw_target = match.group(2)
        annotation = ""
        if " - " in line:
            annotation = line.split(" - ", 1)[1].strip()
        elif " — " in line:
            annotation = line.split(" — ", 1)[1].strip()

        target_path = None
        if raw_target.endswith(".md"):
            target_path = (source_path.parent / raw_target).resolve()

        links.append(Link(label=label, annotation=annotation, target_path=target_path))
    return links


def render_see_also(thread: Thread, title_lookup: dict[Path, str]) -> str | None:
    rendered_links: list[str] = []
    seen: set[Path] = set()
    for link in extract_links(thread.connection_lines, thread.source_path):
        if link.target_path is None:
            continue
        if link.target_path in seen:
            continue
        target_title = title_lookup.get(link.target_path)
        if not target_title:
            continue
        seen.add(link.target_path)
        item = f"[[#{target_title}|{link.label}]]"
        if link.annotation:
            item += f" ({link.annotation})"
        rendered_links.append(item)

    if not rendered_links:
        return None
    return "'''See also:''' " + ", ".join(rendered_links)


def parse_identity(identity_path: Path) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for line in identity_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            current = line[3:].strip()
            sections[current] = []
            continue
        if current is not None:
            sections[current].append(line)
    return sections


def render_identity(identity_path: Path, title_lookup: dict[Path, str]) -> list[str]:
    sections = parse_identity(identity_path)
    rendered = ["== About the Operator ==", ""]
    for section_name in IDENTITY_SECTIONS:
        lines = sections.get(section_name, [])
        if not lines:
            continue
        rendered.append(f"=== {section_name} ===")
        rendered.extend(
            render_markdown_lines(lines, title_lookup=title_lookup, source_dir=identity_path.parent)
        )
        rendered.append("")
    if rendered[-1] == "":
        rendered.pop()
    return rendered


def category_threads(threads: list[Thread]) -> dict[str, list[Thread]]:
    grouped: dict[str, list[Thread]] = {key: [] for key, _ in CATEGORY_ORDER}
    for thread in threads:
        grouped.setdefault(thread.category, []).append(thread)

    for key in grouped:
        grouped[key] = sorted(
            grouped[key],
            key=lambda thread: (
                -thread.hits,
                -parse_iso_date(thread.last_touched).toordinal(),
                thread.title.lower(),
            ),
        )
    return grouped


def render_thread(
    thread: Thread, title_lookup: dict[Path, str]
) -> list[str]:
    lines = [
        f"=== {thread.title} ===",
        f"''{thread.tier_label} | hits: {thread.hits} | last touched: {thread.last_touched} | tags: {', '.join(thread.tags)}''",
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
        lines.append("''Missing Summary section in source thread.''")

    see_also = render_see_also(thread, title_lookup)
    if see_also:
        lines.extend(["", see_also])
    return lines


def render_main_page(repo_root: Path, output_path: Path) -> str:
    memex_dir = repo_root / "memex"
    identity_path = memex_dir / "identity.md"
    threads = load_threads(memex_dir)
    title_lookup = {thread.source_path.resolve(): thread.title for thread in threads}
    grouped = category_threads(threads)

    today = dt.date.today().isoformat()
    lines = [
        "{{DISPLAYTITLE:Memex - Personal Knowledge System}}",
        f"'''Last rendered:''' {today} | '''Threads:''' {len(threads)} | '''Categories:''' {len(CATEGORY_ORDER)}",
        "",
        "This wiki is auto-generated from the Memex thread graph. The Memex is the source of truth; this page is a rendered summary for human navigation.",
        "",
        "'''To regenerate:''' <code>python scripts/generate_wiki.py && python scripts/generate_markdown.py</code>",
        "",
    ]

    lines.extend(render_identity(identity_path, title_lookup))
    lines.extend(["", "", "== Categories ==", ""])

    for key, label in CATEGORY_ORDER:
        titles = [thread.title for thread in grouped.get(key, [])]
        if not titles:
            continue
        lines.append(f"* [[#{label}|{label}]] - {', '.join(titles)}")

    lines.extend(["", "----"])

    for key, label in CATEGORY_ORDER:
        category_items = grouped.get(key, [])
        if not category_items:
            continue
        lines.extend(["", f"== {label} ==", ""])
        for index, thread in enumerate(category_items):
            lines.extend(render_thread(thread, title_lookup))
            if index != len(category_items) - 1:
                lines.append("")
        lines.extend(["", "----"])

    if lines[-1] == "----":
        lines.pop()

    lines.extend(
        [
            "",
            "",
            "''This wiki was generated mechanically from the Memex thread graph. Summaries are extracted from source threads; no thread prose is synthesized during rendering.''",
            "",
            "[[Category:Memex]]",
            "[[Category:Auto-generated]]",
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
        default=Path(__file__).resolve().parents[1],
        type=Path,
        help="Path to the repository root.",
    )
    parser.add_argument(
        "--output",
        default=Path("wiki/Main_Page.wiki"),
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
