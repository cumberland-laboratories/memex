#!/usr/bin/env python3
"""Memex CLI — git-style interface to the Memex knowledge graph.

Usage:
  python .memex/scripts/memex.py status              Quick health + inbox count + hot threads
  python .memex/scripts/memex.py status --full       Full session-opening dump
  python .memex/scripts/memex.py status --full --role agent --format json
  python .memex/scripts/memex.py search "query"      Full-text search across the graph
  python .memex/scripts/memex.py read thread <name>  Render a thread to terminal
  python .memex/scripts/memex.py hit <thread>        Increment hit count + update last-touched
  python .memex/scripts/memex.py inbox add "text"    Add an item to the inbox
  python .memex/scripts/memex.py connect <from> <to> --why "annotation"
  python .memex/scripts/memex.py spawn <name> --threads "thread1,thread2"
  python .memex/scripts/memex.py init
  python .memex/scripts/memex.py health --image docs/wiki/thread-graph.png
  python .memex/scripts/memex.py crawl [--fix]
"""

from __future__ import annotations

import argparse
import datetime as dt
import io
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

# --- Reuse existing parsing infrastructure ---
SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))
from generate_wiki import (
    Thread,
    extract_links,
    load_threads,
    parse_frontmatter,
    parse_sections,
)

# ── Terminal colors ──────────────────────────────────────────────────────────

RED = "\033[0;31m"
YELLOW = "\033[0;33m"
GREEN = "\033[0;32m"
CYAN = "\033[0;36m"
BOLD = "\033[1m"
DIM = "\033[2m"
NC = "\033[0m"

TODAY = dt.date.today()


# ── Role configuration ───────────────────────────────────────────────────────

def find_repo_root(override: str | None = None) -> Path:
    """Walk up from the script to find the repo root (contains memex/).

    If override is provided (--repo flag), use that path instead.
    """
    if override:
        p = Path(override).resolve()
        if (p / "memex").is_dir():
            return p
        print(f"Not a Memex repo: {p} (no memex/ directory)")
        raise SystemExit(1)
    # Scripts live at .memex/scripts/, so repo root is two levels up
    candidate = SCRIPTS_DIR.parent.parent
    if (candidate / "memex").is_dir():
        return candidate
    # Fallback: cwd
    cwd = Path.cwd()
    if (cwd / "memex").is_dir():
        return cwd
    return candidate


def load_roles(repo_root: Path) -> dict:
    """Load role definitions from .memex/roles.yaml."""
    roles_path = repo_root / ".memex" / "roles.yaml"
    if not roles_path.exists():
        return {}
    try:
        import yaml
        return yaml.safe_load(roles_path.read_text(encoding="utf-8")).get("roles", {})
    except ImportError:
        # Minimal YAML parser for simple structure
        return _parse_simple_yaml(roles_path)


def _parse_simple_yaml(path: Path) -> dict:
    """Bare-minimum YAML parser for roles.yaml (no dependency needed)."""
    text = path.read_text(encoding="utf-8")
    roles: dict = {}
    current_role: str | None = None

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        # Top-level "roles:" key
        if stripped == "roles:":
            continue

        # Role name (2-space indent, ends with colon)
        if line.startswith("  ") and not line.startswith("    ") and stripped.endswith(":"):
            current_role = stripped[:-1]
            roles[current_role] = {}
            continue

        # Role property (4-space indent)
        if line.startswith("    ") and current_role and ":" in stripped:
            key, value = stripped.split(":", 1)
            key = key.strip()
            value = value.strip()

            # Parse lists
            if value.startswith("[") and value.endswith("]"):
                value = [item.strip() for item in value[1:-1].split(",") if item.strip()]
            elif value == "null":
                value = None

            roles[current_role][key] = value

    return roles


def get_role(roles: dict, role_name: str | None) -> dict:
    """Get role config, defaulting to pi for humans."""
    if role_name is None:
        role_name = "pi"
    if role_name not in roles:
        # Graceful fallback
        return {
            "description": f"Unknown role: {role_name}",
            "permissions": ["read"],
            "provenance": f"-{role_name}",
            "session-open-emphasis": [],
        }
    return roles[role_name]


# ── File readers ─────────────────────────────────────────────────────────────

def read_file_safe(path: Path) -> str:
    """Read a file, returning empty string if it doesn't exist."""
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def parse_inbox(memex_dir: Path) -> list[str]:
    """Parse inbox items (lines starting with '- ')."""
    text = read_file_safe(memex_dir / "inbox.md")
    items = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("- ") and not stripped.startswith("- Drop anything"):
            items.append(stripped[2:])
    return items


def parse_patterns(memex_dir: Path) -> list[dict]:
    """Parse monthly bills/patterns and find items due within 2 days."""
    import calendar

    bills_path = memex_dir / "patterns" / "monthly-bills.md"
    if not bills_path.exists():
        return []

    text = bills_path.read_text(encoding="utf-8")
    upcoming = []

    # Compute the next occurrence of each due day using real calendar math
    days_in_month = calendar.monthrange(TODAY.year, TODAY.month)[1]

    # Find table rows with a day in the first column
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cols = [c.strip() for c in stripped.split("|")]
        if len(cols) < 4:
            continue
        day_str = cols[1]
        try:
            # Handle "2nd", "17th", "1st" etc.
            day = int(re.sub(r"(st|nd|rd|th)", "", day_str))
        except (ValueError, IndexError):
            continue

        # Compute next occurrence using real dates
        try:
            if day >= TODAY.day:
                # Due this month
                due_date = TODAY.replace(day=min(day, days_in_month))
            else:
                # Due next month
                next_month = TODAY.month + 1
                next_year = TODAY.year
                if next_month > 12:
                    next_month = 1
                    next_year += 1
                next_days_in_month = calendar.monthrange(next_year, next_month)[1]
                due_date = dt.date(next_year, next_month, min(day, next_days_in_month))
        except ValueError:
            continue

        delta = (due_date - TODAY).days
        if 0 <= delta <= 2:
            vendor = cols[2] if len(cols) > 2 else "?"
            amount = cols[3] if len(cols) > 3 else "?"
            upcoming.append({
                "day": day,
                "vendor": vendor,
                "amount": amount,
                "due": "today" if delta == 0 else f"in {delta} day(s)",
            })

    return upcoming


def parse_audit_tracker(memex_dir: Path) -> list[str]:
    """Parse open findings from audit-tracker.md."""
    text = read_file_safe(memex_dir / "audit-tracker.md")
    findings = []
    in_open = False
    for line in text.splitlines():
        if line.strip() == "## Open":
            in_open = True
            continue
        if line.strip().startswith("## "):
            in_open = False
        if in_open and line.strip().startswith("- "):
            findings.append(line.strip()[2:])
    return findings


def get_thread_next_up(thread_path: Path) -> list[str]:
    """Extract Next Up items from a thread file."""
    text = read_file_safe(thread_path)
    _, sections = parse_sections(text.split("---\n", 2)[-1] if text.startswith("---") else text)
    next_up_lines = sections.get("Next Up", [])
    items = []
    for line in next_up_lines:
        stripped = line.strip()
        if stripped.startswith("- "):
            items.append(stripped[2:])
    return items


def thread_staleness(thread: Thread) -> int:
    """Days since last touched."""
    try:
        last = dt.date.fromisoformat(thread.last_touched)
        return (TODAY - last).days
    except (ValueError, TypeError):
        return 999


# ── Output formatting ────────────────────────────────────────────────────────

class PrettyFormatter:
    """Human-readable terminal output."""

    def status(self, data: dict) -> str:
        lines = []
        role_info = data.get("role", {})
        role_name = data.get("role_name", "pi")

        # Header
        lines.append(f"{BOLD}Memex Status{NC}  {DIM}role: {role_name}{NC}")
        lines.append("")

        # Graph health (if available)
        health = data.get("graph_health")
        if health:
            verdict = health["verdict"]
            score = health["overall"]
            color = GREEN if verdict == "HEALTHY" else (YELLOW if verdict == "FAIR" else RED)
            lines.append(f"  Graph:   {color}{verdict}{NC} ({score}/100)  "
                         f"{DIM}{health['nodes']} threads, {health['edges']} edges{NC}")

        # Inbox
        inbox = data.get("inbox", [])
        lines.append(f"  Inbox:   {len(inbox)} item(s)")

        # Patterns due
        patterns = data.get("patterns_due", [])
        if patterns:
            lines.append(f"  {YELLOW}Due:{NC}     {len(patterns)} payment(s) upcoming")
            for p in patterns:
                lines.append(f"           {p['vendor']} {p['amount']} — {p['due']}")

        # Audit findings
        findings = data.get("audit_findings", [])
        if findings:
            lines.append(f"  Audit:   {YELLOW}{len(findings)} open finding(s){NC}")

        lines.append("")

        # Active threads
        threads = data.get("active_threads", [])
        if threads:
            lines.append(f"{BOLD}Active Threads{NC}  ({len(threads)})")
            for t in threads:
                stale_flag = f"  {DIM}({t['staleness_days']}d ago){NC}" if t["staleness_days"] > 7 else ""
                hits_str = f"{DIM}hits:{t['hits']}{NC}"
                lines.append(f"  {t['title']}  {hits_str}{stale_flag}")

                # Next Up items (in full mode)
                for item in t.get("next_up", []):
                    lines.append(f"    {CYAN}→{NC} {item}")

            lines.append("")

        # Inbox items (full mode)
        if data.get("show_inbox_items") and inbox:
            lines.append(f"{BOLD}Inbox Items{NC}")
            for i, item in enumerate(inbox, 1):
                # Truncate long items for terminal readability
                display = item if len(item) <= 120 else item[:117] + "..."
                lines.append(f"  {i}. {display}")
            lines.append("")

        return "\n".join(lines)

    def search_results(self, results: list[dict]) -> str:
        if not results:
            return f"{DIM}No results found.{NC}"
        lines = [f"{BOLD}{len(results)} result(s){NC}", ""]
        for r in results:
            lines.append(f"  {GREEN}{r['file']}{NC}  {DIM}{r['type']}{NC}")
            for match in r.get("matches", [])[:3]:
                lines.append(f"    {match['line_num']}: {match['text'].strip()}")
            lines.append("")
        return "\n".join(lines)

    def thread_view(self, data: dict) -> str:
        lines = []
        lines.append(f"{BOLD}{data['title']}{NC}")

        # Build metadata line based on what's available
        meta_parts = [data['tier']]
        if data.get("status"):
            status_colors = {"building": YELLOW, "shipped": GREEN, "designing": CYAN,
                             "considering": DIM, "maintaining": GREEN}
            sc = status_colors.get(data["status"], "")
            meta_parts.append(f"status: {sc}{data['status']}{NC}")
        if data.get("hits"):
            meta_parts.append(f"hits: {data['hits']}")
        if data.get("owner"):
            meta_parts.append(f"owner: {data['owner']}")
        meta_parts.append(f"last-touched: {data['last_touched']}")
        if data.get("tags"):
            meta_parts.append(f"tags: {', '.join(data['tags'])}")
        lines.append(f"{DIM}{' | '.join(meta_parts)}{NC}")
        lines.append("")

        # If showing a specific section, show just that
        if data.get("_section_content") is not None:
            lines.append(f"{BOLD}{data['_section_name']}{NC}")
            for line in data["_section_content"]:
                lines.append(f"  {line}")
            lines.append("")
            return "\n".join(lines)

        # Summary / Overview
        if data.get("summary"):
            label = "Overview" if data["tier"] == "system" else "Summary"
            lines.append(f"{BOLD}{label}{NC}")
            for line in data["summary"]:
                lines.append(f"  {line}")
            lines.append("")

        # Section list (for system docs — shows navigable structure)
        if data["tier"] in ("system", "report") and data.get("sections"):
            lines.append(f"{BOLD}Sections{NC}")
            for s in data["sections"]:
                lines.append(f"  {DIM}--section{NC} \"{s}\"")
            lines.append("")

        if data.get("connections"):
            lines.append(f"{BOLD}Connections{NC}")
            for line in data["connections"]:
                if line.strip():
                    lines.append(f"  {line.strip()}")
            lines.append("")
        if data.get("next_up"):
            lines.append(f"{BOLD}Next Up{NC}")
            for item in data["next_up"]:
                lines.append(f"  {CYAN}→{NC} {item}")
            lines.append("")
        return "\n".join(lines)


class JsonFormatter:
    """Structured JSON output for agent consumption."""

    def status(self, data: dict) -> str:
        # Remove non-serializable bits, keep the data clean
        output = {
            "role": data.get("role_name", "pi"),
            "date": TODAY.isoformat(),
            "graph_health": data.get("graph_health"),
            "inbox_count": len(data.get("inbox", [])),
            "inbox_items": data.get("inbox") if data.get("show_inbox_items") else None,
            "patterns_due": data.get("patterns_due", []),
            "audit_findings": data.get("audit_findings", []),
            "active_threads": data.get("active_threads", []),
        }
        return json.dumps(output, indent=2, default=str)

    def search_results(self, results: list[dict]) -> str:
        return json.dumps({"results": results, "count": len(results)}, indent=2, default=str)

    def thread_view(self, data: dict) -> str:
        return json.dumps(data, indent=2, default=str)


def get_formatter(fmt: str):
    """Return the appropriate formatter."""
    if fmt == "json":
        return JsonFormatter()
    return PrettyFormatter()


# ── Commands ─────────────────────────────────────────────────────────────────

def cmd_status(args: argparse.Namespace) -> int:
    """Show Memex status — quick summary or full session-opening dump."""
    repo_root = find_repo_root(getattr(args, 'repo', None))
    memex_dir = repo_root / "memex"
    roles = load_roles(repo_root)
    role = get_role(roles, args.role)
    formatter = get_formatter(args.format)

    # Collect data
    data: dict = {
        "role_name": args.role or "pi",
        "role": role,
        "show_inbox_items": args.full,
    }

    # Inbox
    data["inbox"] = parse_inbox(memex_dir)

    # Patterns due
    data["patterns_due"] = parse_patterns(memex_dir)

    # Audit tracker
    data["audit_findings"] = parse_audit_tracker(memex_dir)

    # Active threads
    threads = load_threads(memex_dir)
    active = [t for t in threads if t.tier_label == "Active thread"]
    active.sort(key=lambda t: (
        -t.hits,
        thread_staleness(t),
        t.title.lower(),
    ))

    thread_data = []
    for t in active:
        entry = {
            "title": t.title,
            "hits": t.hits,
            "last_touched": t.last_touched,
            "staleness_days": thread_staleness(t),
            "tags": t.tags,
            "category": t.category,
            "graph": t.graph,
        }
        if args.full:
            entry["next_up"] = get_thread_next_up(t.source_path)
            entry["summary"] = "\n".join(t.summary_lines).strip()
        thread_data.append(entry)

    data["active_threads"] = thread_data

    # Graph health (quick score only — not the full expensive report)
    try:
        from graph_health import build_graph, compute_health
        G, path_to_title = build_graph(memex_dir)
        health = compute_health(G, path_to_title)
        data["graph_health"] = {
            "verdict": health["verdict"],
            "overall": health["overall"],
            "nodes": health["nodes"],
            "edges": health["edges"],
        }
    except Exception:
        data["graph_health"] = None

    print(formatter.status(data))
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    """Full-text search across the Memex graph."""
    repo_root = find_repo_root(getattr(args, 'repo', None))
    memex_dir = repo_root / "memex"
    formatter = get_formatter(args.format)

    query = args.query.lower()
    results = []

    docs_dir = repo_root / "docs"

    # Search directories (memex/ graph + docs/ project docs)
    search_dirs = [
        (memex_dir / "active-threads", "active-thread"),
        (memex_dir / "threads", "reference-thread"),
        (memex_dir / "artifacts", "artifact"),
        (memex_dir / "reference-notes", "reference-note"),
        (memex_dir / "procedures", "procedure"),
        (docs_dir / "systems", "system"),
        (docs_dir / "reports", "report"),
    ]
    # Also search top-level memex files
    top_level_files = [
        memex_dir / "mission.md",
        memex_dir / "roadmap.md",
        memex_dir / "issues.md",
        memex_dir / "identity.md",
        memex_dir / "inbox.md",
    ]

    for path in top_level_files:
        if not path.exists():
            continue
        matches = _search_file(path, query)
        if matches:
            results.append({
                "file": path.name,
                "type": "top-level",
                "path": str(path),
                "matches": matches,
                "match_count": len(matches),
            })

    for dirpath, type_label in search_dirs:
        if not dirpath.is_dir():
            continue
        for path in sorted(dirpath.glob("*.md")):
            if path.name == "_TEMPLATE.md":
                continue
            matches = _search_file(path, query)
            if matches:
                results.append({
                    "file": f"{dirpath.relative_to(repo_root)}/{path.name}",
                    "type": type_label,
                    "path": str(path),
                    "matches": matches,
                    "match_count": len(matches),
                })

    # Sort by match count descending (rough relevance)
    results.sort(key=lambda r: -r["match_count"])

    print(formatter.search_results(results))
    return 0


def _search_file(path: Path, query: str) -> list[dict]:
    """Search a single file for a query string. Returns matching lines."""
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return []

    matches = []
    for i, line in enumerate(text.splitlines(), 1):
        if query in line.lower():
            matches.append({"line_num": i, "text": line})

    return matches


def cmd_read(args: argparse.Namespace) -> int:
    """Read and render a thread or artifact."""
    repo_root = find_repo_root(getattr(args, 'repo', None))
    memex_dir = repo_root / "memex"
    formatter = get_formatter(args.format)

    file_type = args.type
    name = args.name

    docs_dir = repo_root / "docs"

    # Resolve the file path
    search_dirs = {
        "thread": [memex_dir / "active-threads", memex_dir / "threads"],
        "artifact": [memex_dir / "artifacts"],
        "reference-note": [memex_dir / "reference-notes"],
        "procedure": [memex_dir / "procedures"],
        "system": [docs_dir / "systems"],
        "report": [docs_dir / "reports"],
    }

    if file_type not in search_dirs:
        print(f"Unknown type: {file_type}. Use: {', '.join(search_dirs.keys())}")
        return 1

    # Find the file — try exact match, then fuzzy
    target = None
    for dirpath in search_dirs[file_type]:
        exact = dirpath / f"{name}.md"
        if exact.exists():
            target = exact
            break
        # Fuzzy: find files containing the name
        for path in dirpath.glob("*.md"):
            if path.name == "_TEMPLATE.md":
                continue
            if name.lower() in path.stem.lower():
                target = path
                break
        if target:
            break

    if not target:
        print(f"Not found: {file_type} '{name}'")
        # Suggest alternatives
        candidates = []
        for dirpath in search_dirs[file_type]:
            if dirpath.is_dir():
                candidates.extend(p.stem for p in dirpath.glob("*.md") if p.name != "_TEMPLATE.md")
        if candidates:
            print(f"Available: {', '.join(sorted(candidates))}")
        return 1

    # Parse and render
    text = target.read_text(encoding="utf-8")
    fm_text, body = text.split("---\n", 2)[1:] if text.startswith("---") else ("", text)
    frontmatter, _ = parse_frontmatter(text)
    h1, sections = parse_sections(body)

    data = {
        "title": frontmatter.get("title") or h1 or target.stem,
        "tier": file_type,
        "hits": int(frontmatter.get("hits", "0")),
        "last_touched": frontmatter.get("last-touched", frontmatter.get("last-updated", "unknown")),
        "tags": [t.strip() for t in frontmatter.get("tags", "").strip("[]").split(",") if t.strip()],
        "graph": frontmatter.get("graph", "user"),
        "category": frontmatter.get("category", ""),
        "status": frontmatter.get("status", ""),
        "owner": frontmatter.get("owner", ""),
        "summary": [line for line in sections.get("Summary", sections.get("Overview", [])) if line.strip()],
        "connections": sections.get("Connections", []),
        "next_up": [line.strip()[2:] for line in sections.get("Next Up", []) if line.strip().startswith("- ")],
        "open_questions": [line.strip()[2:] for line in sections.get("Open Questions", []) if line.strip().startswith("- ")],
        "decision_log": sections.get("Decision Log", []),
        "sections": list(sections.keys()),
        "file": str(target.relative_to(repo_root)),
    }

    # Section-level navigation
    if args.section:
        section_name = args.section
        # Fuzzy match section name
        matched = None
        for s in sections:
            if section_name.lower() in s.lower():
                matched = s
                break
        if matched is None:
            print(f"Section '{section_name}' not found in {data['title']}")
            print(f"Available sections: {', '.join(sections.keys())}")
            return 1
        data["_section_name"] = matched
        data["_section_content"] = sections[matched]

    print(formatter.thread_view(data))
    return 0


# ── Write-side shared infrastructure ─────────────────────────────────────────


def require_permission(role: dict, role_name: str, permission: str = "write") -> None:
    """Check that the role has the required permission. Exit if not."""
    perms = role.get("permissions", [])
    if isinstance(perms, str):
        perms = [perms]
    if "all" in perms or permission in perms:
        return
    # write-maintenance permits hit and connect (structural maintenance)
    if permission == "write" and "write-maintenance" in perms:
        return
    print(f"Permission denied: role '{role_name}' does not have '{permission}' permission.")
    raise SystemExit(1)


def resolve_thread(memex_dir: Path, name: str) -> Path | None:
    """Resolve a thread name to a file path (active-threads/ then threads/).

    Tries exact match, then substring match on stem.
    """
    for subdir in ["active-threads", "threads"]:
        dirpath = memex_dir / subdir
        if not dirpath.is_dir():
            continue
        exact = dirpath / f"{name}.md"
        if exact.exists():
            return exact
        for path in dirpath.glob("*.md"):
            if path.name == "_TEMPLATE.md":
                continue
            if name.lower() in path.stem.lower():
                return path
    return None


def list_thread_names(memex_dir: Path) -> list[str]:
    """List all thread stems for error suggestions."""
    names = []
    for subdir in ["active-threads", "threads"]:
        dirpath = memex_dir / subdir
        if dirpath.is_dir():
            names.extend(
                p.stem for p in dirpath.glob("*.md") if p.name != "_TEMPLATE.md"
            )
    return sorted(names)


def rewrite_frontmatter_field(path: Path, updates: dict[str, str | int]) -> dict:
    """Rewrite specific frontmatter fields in a Markdown file.

    Operates on raw text line-by-line to preserve formatting.
    Returns dict with old and new values for each updated field.
    """
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        raise ValueError(f"File {path.name} has no frontmatter block.")

    # Split into frontmatter and body
    parts = text.split("---\n", 2)
    if len(parts) < 3:
        raise ValueError(f"File {path.name} has malformed frontmatter.")

    fm_lines = parts[1].splitlines()
    changes = {}

    for key, new_value in updates.items():
        found = False
        for i, line in enumerate(fm_lines):
            if line.startswith(f"{key}:"):
                old_value = line.split(":", 1)[1].strip()
                fm_lines[i] = f"{key}: {new_value}"
                changes[key] = {"old": old_value, "new": str(new_value)}
                found = True
                break
        if not found:
            raise ValueError(f"Field '{key}' not found in {path.name} frontmatter.")

    # Reassemble and write
    new_text = "---\n" + "\n".join(fm_lines) + "\n---\n" + parts[2]
    path.write_text(new_text, encoding="utf-8")
    return changes


def get_thread_title(path: Path) -> str:
    """Extract the title from a thread file (frontmatter title or H1)."""
    text = path.read_text(encoding="utf-8")
    fm, _ = parse_frontmatter(text)
    if fm.get("title"):
        return fm["title"]
    # Fall back to H1
    for line in text.splitlines():
        if line.startswith("# ") and not line.startswith("## "):
            return line[2:].strip()
    return path.stem


# ── Write commands ───────────────────────────────────────────────────────────


def cmd_hit(args: argparse.Namespace) -> int:
    """Increment hit count and update last-touched on a thread."""
    repo_root = find_repo_root(getattr(args, 'repo', None))
    memex_dir = repo_root / "memex"
    roles = load_roles(repo_root)
    role_name = args.role or "pi"
    role = get_role(roles, role_name)
    formatter = get_formatter(args.format)

    require_permission(role, role_name)

    target = resolve_thread(memex_dir, args.name)
    if not target:
        print(f"Thread not found: '{args.name}'")
        candidates = list_thread_names(memex_dir)
        if candidates:
            print(f"Available: {', '.join(candidates)}")
        return 1

    # Read current hits
    text = target.read_text(encoding="utf-8")
    fm, _ = parse_frontmatter(text)
    old_hits = int(fm.get("hits", "0"))
    new_hits = old_hits + 1

    changes = rewrite_frontmatter_field(target, {
        "hits": new_hits,
        "last-touched": TODAY.isoformat(),
    })

    provenance = role.get("provenance", f"-{role_name}")
    result = {
        "command": "hit",
        "thread": target.stem,
        "file": str(target.relative_to(repo_root)),
        "hits": {"old": old_hits, "new": new_hits},
        "last_touched": changes.get("last-touched", {}),
        "provenance": provenance,
    }

    if isinstance(formatter, JsonFormatter):
        print(json.dumps(result, indent=2))
    else:
        old_lt = changes.get("last-touched", {}).get("old", "?")
        print(f"  {GREEN}✓{NC} {BOLD}{target.stem}{NC}  "
              f"hits: {old_hits} → {new_hits}  "
              f"last-touched: {TODAY.isoformat()}")

    return 0


def cmd_inbox(args: argparse.Namespace) -> int:
    """Inbox operations (add)."""
    if args.inbox_command == "add":
        return cmd_inbox_add(args)
    # Future: list, clear, etc.
    print("Usage: memex inbox add \"text\"")
    return 1


def cmd_inbox_add(args: argparse.Namespace) -> int:
    """Add an item to the inbox."""
    repo_root = find_repo_root(getattr(args, 'repo', None))
    memex_dir = repo_root / "memex"
    roles = load_roles(repo_root)
    role_name = args.role or "pi"
    role = get_role(roles, role_name)
    formatter = get_formatter(args.format)

    require_permission(role, role_name)

    text = args.text.strip()
    if not text:
        print("Cannot add empty inbox item.")
        return 1

    inbox_path = memex_dir / "inbox.md"
    provenance = role.get("provenance", f"-{role_name}")

    # Count existing items
    old_items = parse_inbox(memex_dir)
    old_count = len(old_items)

    # Append to inbox
    entry = f"- {text} {provenance}\n"
    if inbox_path.exists():
        content = inbox_path.read_text(encoding="utf-8")
        if not content.endswith("\n"):
            content += "\n"
        content += entry
        inbox_path.write_text(content, encoding="utf-8")
    else:
        inbox_path.write_text(
            "# Inbox\n\nDrop anything here. No formatting needed. "
            "The chat agent triages at session open.\n\n---\n\n" + entry,
            encoding="utf-8",
        )

    new_count = old_count + 1
    result = {
        "command": "inbox_add",
        "text": text,
        "provenance": provenance,
        "inbox_count": {"old": old_count, "new": new_count},
        "file": "memex/inbox.md",
    }

    if isinstance(formatter, JsonFormatter):
        print(json.dumps(result, indent=2))
    else:
        print(f"  {GREEN}✓{NC} inbox  +1 item ({new_count} total)")

    return 0


def cmd_connect(args: argparse.Namespace) -> int:
    """Add an annotated cross-reference between two threads."""
    repo_root = find_repo_root(getattr(args, 'repo', None))
    memex_dir = repo_root / "memex"
    roles = load_roles(repo_root)
    role_name = args.role or "pi"
    role = get_role(roles, role_name)
    formatter = get_formatter(args.format)

    require_permission(role, role_name)

    if not args.why or not args.why.strip():
        print("Connection annotation is required (--why).")
        print("Constitutional rule: cross-references annotate why the link exists.")
        return 1

    source = resolve_thread(memex_dir, args.source)
    target = resolve_thread(memex_dir, args.target)

    if not source:
        print(f"Source thread not found: '{args.source}'")
        candidates = list_thread_names(memex_dir)
        if candidates:
            print(f"Available: {', '.join(candidates)}")
        return 1
    if not target:
        print(f"Target thread not found: '{args.target}'")
        candidates = list_thread_names(memex_dir)
        if candidates:
            print(f"Available: {', '.join(candidates)}")
        return 1

    # Compute relative path from source's directory to target
    rel_path = Path(os.path.relpath(target, source.parent))
    # Normalize to forward slashes for Markdown links
    rel_path_str = rel_path.as_posix()

    target_title = get_thread_title(target)
    annotation = args.why.strip()
    connection_line = f"→ [{target_title}]({rel_path_str}) — {annotation}"

    # Read source file and check for duplicates
    text = source.read_text(encoding="utf-8")

    # Check if target is already referenced in Connections
    if target.stem in text and "## Connections" in text:
        # More precise check: is the target filename in a connection line?
        conn_section_start = text.index("## Connections")
        conn_section = text[conn_section_start:]
        # Find end of connections section (next ## or EOF)
        next_heading = re.search(r"\n## ", conn_section[len("## Connections"):])
        if next_heading:
            conn_section = conn_section[:len("## Connections") + next_heading.start()]
        if target.name in conn_section or target.stem in conn_section:
            result = {
                "command": "connect",
                "from": {"thread": source.stem, "file": str(source.relative_to(repo_root))},
                "to": {"thread": target.stem, "file": str(target.relative_to(repo_root))},
                "annotation": annotation,
                "already_existed": True,
            }
            if isinstance(formatter, JsonFormatter):
                print(json.dumps(result, indent=2))
            else:
                print(f"  {DIM}Connection already exists: {source.stem} → {target.stem}{NC}")
            return 0

    # Insert the connection line
    if "## Connections" in text:
        # Find the end of the Connections section (next ## heading or EOF)
        lines = text.splitlines(keepends=True)
        conn_idx = None
        insert_idx = None
        for i, line in enumerate(lines):
            if line.strip() == "## Connections":
                conn_idx = i
            elif conn_idx is not None and line.startswith("## "):
                # Insert before this heading, with a blank line
                insert_idx = i
                break
        if conn_idx is not None and insert_idx is None:
            insert_idx = len(lines)  # Connections is the last section

        if insert_idx is not None:
            # Insert before the next heading (or at end), after the last connection line
            # Walk backwards from insert_idx to find last non-blank line in section
            actual_insert = insert_idx
            for j in range(insert_idx - 1, conn_idx, -1):
                if lines[j].strip():
                    actual_insert = j + 1
                    break
            lines.insert(actual_insert, connection_line + "\n")
            text = "".join(lines)
    else:
        # No Connections section — insert before Open Questions, Next Up, or at end
        insert_before = None
        for heading in ["## Open Questions", "## Next Up"]:
            if heading in text:
                insert_before = heading
                break
        if insert_before:
            section_block = f"## Connections\n\n{connection_line}\n\n"
            text = text.replace(insert_before, section_block + insert_before)
        else:
            text = text.rstrip() + f"\n\n## Connections\n\n{connection_line}\n"

    source.write_text(text, encoding="utf-8")

    provenance = role.get("provenance", f"-{role_name}")
    result = {
        "command": "connect",
        "from": {"thread": source.stem, "file": str(source.relative_to(repo_root))},
        "to": {"thread": target.stem, "file": str(target.relative_to(repo_root))},
        "annotation": annotation,
        "relative_path": rel_path_str,
        "provenance": provenance,
        "already_existed": False,
    }

    if isinstance(formatter, JsonFormatter):
        print(json.dumps(result, indent=2))
    else:
        print(f"  {GREEN}✓{NC} connected  {BOLD}{source.stem}{NC} → {BOLD}{target.stem}{NC}")
        print(f"    \"{annotation}\"")

    return 0


# ── New commands (Phase 1 MVP) ────────────────────────────────────────────────


def cmd_suggest(args: argparse.Namespace) -> int:
    """Suggest what to work on based on graph state."""
    repo_root = find_repo_root(getattr(args, 'repo', None))
    memex_dir = repo_root / "memex"
    formatter = get_formatter(args.format)

    threads = load_threads(memex_dir)
    active = [t for t in threads if t.tier_label == "Active thread"]

    suggestions = []

    # 1. Next Up items (explicit intent — highest priority)
    for t in active:
        next_up = get_thread_next_up(t.source_path)
        if next_up:
            for item in next_up:
                suggestions.append({
                    "type": "next_up",
                    "thread": t.title,
                    "item": item,
                    "priority": 1,
                })

    # 2. Hot threads (high hits, recently touched)
    hot = sorted(active, key=lambda t: (-t.hits, thread_staleness(t)))
    for t in hot[:3]:
        if t.hits > 0:
            suggestions.append({
                "type": "hot",
                "thread": t.title,
                "hits": t.hits,
                "staleness_days": thread_staleness(t),
                "priority": 2,
            })

    # 3. Stale threads (need attention or demotion)
    for t in active:
        days = thread_staleness(t)
        if days > 14:
            suggestions.append({
                "type": "stale",
                "thread": t.title,
                "staleness_days": days,
                "priority": 3,
            })

    # 4. Inbox items waiting
    inbox = parse_inbox(memex_dir)
    if inbox:
        suggestions.append({
            "type": "inbox",
            "count": len(inbox),
            "priority": 2,
        })

    if isinstance(formatter, JsonFormatter):
        print(json.dumps({"suggestions": suggestions}, indent=2, default=str))
    else:
        if not suggestions:
            print(f"  {DIM}Nothing urgent. You're free to explore.{NC}")
            return 0

        print(f"{BOLD}Suggestions{NC}\n")
        for s in sorted(suggestions, key=lambda x: x["priority"]):
            if s["type"] == "next_up":
                print(f"  {CYAN}→{NC} {BOLD}{s['thread']}{NC}: {s['item']}")
            elif s["type"] == "hot":
                print(f"  {GREEN}●{NC} {s['thread']}  {DIM}(hits: {s['hits']}, {s['staleness_days']}d ago){NC}")
            elif s["type"] == "stale":
                print(f"  {YELLOW}⚠{NC} {s['thread']}  {DIM}stale ({s['staleness_days']} days) — revisit or demote?{NC}")
            elif s["type"] == "inbox":
                print(f"  {YELLOW}▶{NC} {s['count']} inbox item(s) waiting for triage")
        print()

    return 0


def cmd_draft(args: argparse.Namespace) -> int:
    """Show the current commit draft."""
    repo_root = find_repo_root(getattr(args, 'repo', None))
    draft_path = repo_root / "memex" / "commit_draft.md"

    if not draft_path.exists():
        print(f"  {DIM}No commit draft found.{NC}")
        return 0

    text = draft_path.read_text(encoding="utf-8").strip()
    if not text:
        print(f"  {DIM}Commit draft is empty.{NC}")
        return 0

    if isinstance(get_formatter(args.format), JsonFormatter):
        lines = [l.strip() for l in text.splitlines() if l.strip().startswith("- ")]
        print(json.dumps({"draft": lines, "count": len(lines)}, indent=2))
    else:
        print(f"{BOLD}Commit Draft{NC}\n")
        for line in text.splitlines():
            if line.strip():
                print(f"  {line}")
        print()

    return 0


def cmd_thread_new(args: argparse.Namespace) -> int:
    """Create a new thread from the template."""
    repo_root = find_repo_root(getattr(args, 'repo', None))
    memex_dir = repo_root / "memex"
    roles = load_roles(repo_root)
    role_name = args.role or "pi"
    role = get_role(roles, role_name)

    require_permission(role, role_name)

    name = args.name.strip().lower().replace(" ", "-")
    target = memex_dir / "active-threads" / f"{name}.md"

    if target.exists():
        print(f"Thread already exists: {target.relative_to(repo_root)}")
        return 1

    category = args.category or "systems"
    tags = args.tags or name

    content = f"""---
last-touched: {TODAY.isoformat()}
category: {category}
hits: 0
tags: [{tags}]
---

# {args.title or name.replace('-', ' ').title()}

## Summary

[2-4 sentences. What this thread is about.]

## Detail

[Content goes here.]

## Connections

[→ links to related threads]
"""

    target.write_text(content, encoding="utf-8")

    provenance = role.get("provenance", f"-{role_name}")
    if isinstance(get_formatter(args.format), JsonFormatter):
        print(json.dumps({
            "command": "thread_new",
            "name": name,
            "file": str(target.relative_to(repo_root)),
            "provenance": provenance,
        }, indent=2))
    else:
        print(f"  {GREEN}✓{NC} created  {BOLD}{name}{NC}")
        print(f"    {target.relative_to(repo_root)}")

    return 0


def cmd_init(args: argparse.Namespace) -> int:
    """Initialize a new Memex project interactively or via flags."""
    from spawn import (
        GENERIC_CONSTITUTION, BLANK_ROADMAP, BLANK_ISSUES, BLANK_INBOX,
    )

    # Repo root: use --repo, or cwd (init may run before memex/ exists)
    if args.repo:
        repo_root = Path(args.repo).resolve()
    else:
        repo_root = Path.cwd()

    memex_dir = repo_root / "memex"
    formatter = get_formatter(args.format)
    is_json = isinstance(formatter, JsonFormatter)

    # Already-initialized detection
    identity_path = memex_dir / "identity.md"
    if identity_path.exists() and not getattr(args, 'force', False):
        text = identity_path.read_text(encoding="utf-8")
        if "[Your role" not in text and "[your " not in text.lower() and "[Add more" not in text:
            if is_json:
                print(json.dumps({"command": "init", "error": "already_initialized"}, indent=2))
            else:
                print(f"\n  {YELLOW}Already initialized.{NC} Run {BOLD}memex status{NC} to see where things stand.")
                print(f"  Use {DIM}memex init --force{NC} to re-initialize.\n")
            return 1

    # Gather answers
    project_name = getattr(args, 'name', None)
    building = getattr(args, 'building', None)
    pi_name = getattr(args, 'pi', None)

    # JSON mode requires all flags (no interactive prompts)
    if is_json and not (project_name and building and pi_name):
        print(json.dumps({
            "command": "init",
            "error": "missing_flags",
            "message": "JSON mode requires --name, --building, and --pi flags",
        }, indent=2))
        return 1

    # Interactive prompts
    if not (project_name and building and pi_name):
        print(f"\n  {BOLD}Welcome to the Memex.{NC}")
        print(f"  Three questions and you're up and running.\n")

        if not project_name:
            project_name = input(f"  {BOLD}What's this project called?{NC}  ").strip()
        if not building:
            building = input(f"\n  {BOLD}In one sentence, what are you building or researching?{NC}\n  ").strip()
        if not pi_name:
            pi_name = input(f"\n  {BOLD}What's your name?{NC}  ").strip()
        print()

    if not project_name or not building or not pi_name:
        print(f"  {RED}All three answers are needed.{NC}")
        return 1

    today = TODAY.isoformat()
    created = []
    skipped = []

    # ── Create directory structure ──────────────────────────────────────────
    dirs = [
        "memex/active-threads", "memex/threads", "memex/artifacts",
        "memex/vault", "memex/procedures", "memex/reference-notes",
        "memex/patterns",
        "docs/systems", "docs/reports", "docs/wiki",
    ]
    for d in dirs:
        (repo_root / d).mkdir(parents=True, exist_ok=True)

    # ── Helper: write file if missing or placeholder ────────────────────────
    def write_if_needed(rel_path: str, content: str) -> None:
        path = repo_root / rel_path
        if path.exists() and not getattr(args, 'force', False):
            existing = path.read_text(encoding="utf-8")
            # Skip if file has real content (not a placeholder)
            if existing.strip() and "[Your role" not in existing and "[What this" not in existing:
                skipped.append(rel_path)
                return
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        created.append(rel_path)

    # ── Knowledge-layer files ───────────────────────────────────────────────

    # Identity — populated with PI info
    write_if_needed("memex/identity.md", f"""\
---
operating-mode: user
---

# Identity

{pi_name}. Working on {project_name}.

[Add more here — your background, how you think, what you're good at.
The agent uses this to calibrate how it collaborates with you.]
""")

    # Mission — populated with what they're building
    write_if_needed("memex/mission.md", f"""\
# Mission

## What We're Building

{building}

## What Success Looks Like

[How you'll know it's working.]
""")

    # Roadmap, issues, inbox — blank structures
    write_if_needed("memex/roadmap.md", BLANK_ROADMAP.format(date=today))
    write_if_needed("memex/issues.md", BLANK_ISSUES)
    write_if_needed("memex/inbox.md", BLANK_INBOX)

    # Commit draft — empty
    draft_path = repo_root / "memex" / "commit_draft.md"
    if not draft_path.exists():
        draft_path.write_text("", encoding="utf-8")
        created.append("memex/commit_draft.md")

    # ── Constitution ────────────────────────────────────────────────────────

    # constitution-core.md: check if it exists (cloned repo has it)
    has_core = (repo_root / "constitution-core.md").exists()

    # constitution.md: generate with project name
    const_path = repo_root / "constitution.md"
    if not const_path.exists() or getattr(args, 'force', False):
        if has_core:
            # Lightweight domain constitution that references the core
            const_content = f"""\
# {project_name} — Domain Constitution

Project-specific rules for this Memex. The core governance lives in → [constitution-core.md](constitution-core.md).

## Project

{building}

## Operating Mode

`operating-mode: user` — default to content-level (working on your project). Use `*m` prefix to switch to meta-level (modifying the Memex itself).

## Domain Conventions

(Add project-specific conventions here as they emerge.)
"""
        else:
            # Standalone: use the full generic constitution from spawn
            const_content = GENERIC_CONSTITUTION.format(project_name=project_name)
        const_path.write_text(const_content, encoding="utf-8")
        created.append("constitution.md")
    else:
        skipped.append("constitution.md")

    # ── Entry point files ───────────────────────────────────────────────────

    const_refs = (
        "[`constitution-core.md`](constitution-core.md) and then [`constitution.md`](constitution.md)"
        if has_core
        else "[`constitution.md`](constitution.md)"
    )

    write_if_needed("CLAUDE.md", f"""\
# Claude Code Entry Point

Your default role is **agent** (`--role agent`).

You MUST read {const_refs}, and execute the session-opening procedure before your first response. Do not use MEMORY.md or any other auto-loaded context as a substitute — the constitution governs this project.
""")

    write_if_needed("AGENTS.md", f"""\
# Agent Entry Point

Your default role is **enforcer** (`--role enforcer`).

You MUST read {const_refs}, and execute the session-opening procedure before your first response. Do not use MEMORY.md or any other auto-loaded context as a substitute — the constitution governs this project.
""")

    write_if_needed("GEMINI.md", f"""\
# Gemini Entry Point

Your default role is **enforcer** (`--role enforcer`).

You MUST read {const_refs}, and execute the session-opening procedure before your first response. Do not use MEMORY.md or any other auto-loaded context as a substitute — the constitution governs this project.
""")

    # ── Templates ───────────────────────────────────────────────────────────

    write_if_needed("memex/active-threads/_TEMPLATE.md", """\
---
last-touched: YYYY-MM-DD
category: choose-one [mathematics, cognition, systems, ventures, economics, civic]
hits: 0
tags: [relevant, keywords]
---

# Thread Title

## Summary

2-4 sentences. Self-contained, readable without the rest of the thread.

## Detail

Dense index-card content. Domain-specific subheadings optional.

## Connections

→ [Related Thread](relative-path.md) — why this link exists

## Open Questions

- Questions that remain unresolved

## Next Up

- Forward intent for the next session (optional — only write when clear intent exists)
""")

    write_if_needed("memex/artifacts/_TEMPLATE.md", """\
---
date: YYYY-MM-DD
depth: full | stub
tags: [relevant, keywords]
source-thread: relative/path/to/thread.md
source: (optional) path or URL to the original external material
summary: One to two sentences.
---

# Artifact Title

Content goes here. Artifacts at depth: full are self-contained.
Artifacts at depth: stub contain a summary and a pointer to external material.
""")

    write_if_needed("docs/systems/_TEMPLATE.md", """\
---
title: System Doc Title
status: active | deprecated | experimental
last-updated: YYYY-MM-DD
owner: pi
tags: [relevant, keywords]
source-thread: memex/active-threads/thread-name.md
---

# System Doc Title

## Overview

2-4 sentences. What this subsystem is, what it does, how it fits.

## Connections

→ [Thread Name](../../memex/active-threads/thread-name.md) — relationship
""")

    # ── Vault + gitignore ───────────────────────────────────────────────────

    gitkeep = repo_root / "memex" / "vault" / ".gitkeep"
    if not gitkeep.exists():
        gitkeep.write_text("", encoding="utf-8")

    gitignore = repo_root / ".gitignore"
    vault_rule = "memex/vault/**"
    if gitignore.exists():
        gi_text = gitignore.read_text(encoding="utf-8")
        if vault_rule not in gi_text:
            with open(gitignore, "a", encoding="utf-8") as f:
                f.write(f"\n{vault_rule}\n!memex/vault/.gitkeep\n")
            created.append(".gitignore (updated)")
    else:
        gitignore.write_text(f"{vault_rule}\n!memex/vault/.gitkeep\n", encoding="utf-8")
        created.append(".gitignore")

    # ── Output ──────────────────────────────────────────────────────────────

    if is_json:
        print(json.dumps({
            "command": "init",
            "project": project_name,
            "pi": pi_name,
            "building": building,
            "files_created": created,
            "files_skipped": skipped,
        }, indent=2))
    else:
        print(f"  {GREEN}✓{NC} {BOLD}{project_name}{NC} is ready.\n")
        if created:
            for f in created:
                print(f"    {GREEN}+{NC} {f}")
        if skipped:
            print()
            for f in skipped:
                print(f"    {DIM}~ {f} (kept existing){NC}")
        print(f"\n  {BOLD}Next steps:{NC}")
        print(f"    memex status          See where things stand")
        print(f"    memex explain         Learn what the Memex can do")
        print(f"    Start an AI session — the agent picks up from here.\n")

    return 0


def cmd_explain(args: argparse.Namespace) -> int:
    """Explain what the Memex can do."""
    topic = args.topic if hasattr(args, 'topic') and args.topic else "overview"
    topic = topic.lower()

    explanations = {
        "overview": f"""
{BOLD}The Memex{NC} — a knowledge system that maintains itself.

Your AI sessions build on each other instead of starting from zero.
The Memex captures what you learn, what you decide, and what you
intend to do next — as a navigable graph, not a chat log.

{BOLD}Quick start:{NC}
  memex status          See where things stand
  memex search "topic"  Find anything in your knowledge graph
  memex suggest         Get a prioritized recommendation
  memex inbox add "..." Capture a thought without stopping

{BOLD}Learn more:{NC}
  memex explain threads     How knowledge is organized
  memex explain health      How graph quality is measured
  memex explain commands    All available commands
""",
        "threads": f"""
{BOLD}Threads{NC} — topics with momentum.

A thread captures something you're working on or thinking about.
It has a summary, connections to related threads, and a "Next Up"
section for forward intent.

Three tiers:
  {GREEN}active-threads/{NC}  Live working set (always loaded, 5-8 files)
  {DIM}threads/{NC}          Dormant topics (on demand, compressed)
  {DIM}artifacts/{NC}        Deep records (dated, historical)

Threads move between tiers based on activity. Hot threads promote.
Cool threads demote. Nothing is deleted — demotion is compression.

{BOLD}Commands:{NC}
  memex read thread <name>    Read a thread
  memex thread new <name>     Create a new thread
  memex hit <name>            Mark a thread as actively discussed
  memex connect A B --why "..." Link two threads
""",
        "health": f"""
{BOLD}Graph Health{NC} — structural quality of your knowledge graph.

Five dimensions, each scored 0-100:

  {BOLD}Navigability{NC}   Can you reach any thread within 3 hops?
  {BOLD}Resilience{NC}     Can you remove any edge without disconnecting the graph?
  {BOLD}Connectivity{NC}   Does every thread have inbound links from its neighbors?
  {BOLD}Efficiency{NC}     Is the graph appropriately connected (not too sparse, not too dense)?
  {BOLD}Legibility{NC}     Can peripheral threads reach well-connected hubs?

Overall: HEALTHY (≥80), FAIR (50-79), UNHEALTHY (<50).

{BOLD}Commands:{NC}
  memex health            Full health report
  memex crawl             Automated maintenance (dry-run)
  memex crawl --fix       Propose fixes via a different AI model
""",
        "commands": f"""
{BOLD}All Commands{NC}

{BOLD}Read:{NC}
  memex status              Graph health, inbox, active threads
  memex status --full       Complete state dump (Next Up, summaries)
  memex search "query"      Full-text search across the graph
  memex read <type> <name>  Render a thread/artifact/system doc
  memex suggest             Prioritized work recommendation
  memex draft               Show current commit draft
  memex explain [topic]     This help system

{BOLD}Write:{NC}
  memex hit <name>          Increment hit count + update last-touched
  memex inbox add "text"    Capture a thought
  memex connect A B --why   Add annotated cross-reference
  memex thread new <name>   Create a new thread

{BOLD}Maintain:{NC}
  memex health              Graph health report (5 dimensions)
  memex crawl               Automated health triage (dry-run)
  memex crawl --fix         Propose fixes via different AI model

{BOLD}Create:{NC}
  memex init                           Set up a new Memex project
  memex spawn <name> --threads "a,b"   New repo from seed threads

{BOLD}Flags:{NC}
  --format json    Structured output for agents
  --role <name>    Operator role (pi, agent, enforcer, crawler)
  --repo <path>    Operate on a different Memex repo
""",
    }

    text = explanations.get(topic)
    if text:
        print(text)
    else:
        print(f"  Unknown topic: {topic}")
        print(f"  Available: {', '.join(explanations.keys())}")
        return 1

    return 0


# ── Script wrappers (thin shims to standalone scripts) ───────────────────────


def cmd_health(args: argparse.Namespace) -> int:
    """Run graph health check and optionally generate PNG + JSON."""
    import subprocess
    repo_root = find_repo_root(getattr(args, 'repo', None))
    cmd = [sys.executable, str(SCRIPTS_DIR / "graph_health.py"),
           "--repo-root", str(repo_root)]
    if args.image:
        cmd.extend(["--image", args.image])
    if args.json_out:
        cmd.extend(["--json", args.json_out])
    if args.graph:
        cmd.extend(["--graph", args.graph])
    return subprocess.run(cmd).returncode


def cmd_crawl(args: argparse.Namespace) -> int:
    """Run the crawler (graph health triage + optional Sonnet fixes)."""
    import subprocess
    cmd = [sys.executable, str(SCRIPTS_DIR / "crawler.py")]
    if args.fix:
        cmd.append("--fix")
    if args.graph:
        cmd.extend(["--graph", args.graph])
    if args.no_branch:
        cmd.append("--no-branch")
    return subprocess.run(cmd).returncode


# ── Main entry point ─────────────────────────────────────────────────────────

def main() -> int:
    # Ensure UTF-8 output on Windows
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    # Shared args via parent parser
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--format", choices=["pretty", "json"], default="pretty",
        help="Output format (default: pretty)",
    )
    common.add_argument(
        "--role", default=None,
        help="Operator role (pi, agent, enforcer, crawler)",
    )
    common.add_argument(
        "--repo", default=None,
        help="Path to a Memex repo (default: auto-detect from script location)",
    )

    parser = argparse.ArgumentParser(
        prog="memex",
        description="Git-style CLI for the Memex knowledge graph.",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # status
    status_parser = subparsers.add_parser("status", parents=[common],
                                          help="Memex status summary")
    status_parser.add_argument(
        "--full", action="store_true",
        help="Full session-opening dump (inbox items, Next Up, summaries)",
    )

    # search
    search_parser = subparsers.add_parser("search", parents=[common],
                                          help="Full-text search across the graph")
    search_parser.add_argument("query", help="Search query")

    # read
    read_parser = subparsers.add_parser("read", parents=[common],
                                        help="Read a thread, artifact, or reference note")
    read_parser.add_argument("type", choices=["thread", "artifact", "reference-note", "procedure", "system", "report"],
                             help="Type of document to read")
    read_parser.add_argument("name", help="Name (or partial name) of the document")
    read_parser.add_argument("--section", default=None,
                             help="Show only a specific H2 section (by heading name)")

    # hit
    hit_parser = subparsers.add_parser("hit", parents=[common],
                                        help="Increment hit count and update last-touched")
    hit_parser.add_argument("name", help="Thread name (exact or partial)")

    # inbox
    inbox_parser = subparsers.add_parser("inbox", parents=[common],
                                          help="Inbox operations")
    inbox_sub = inbox_parser.add_subparsers(dest="inbox_command")
    inbox_add = inbox_sub.add_parser("add", parents=[common],
                                      help="Add an item to the inbox")
    inbox_add.add_argument("text", help="Item text to add")

    # spawn
    spawn_parser = subparsers.add_parser("spawn", parents=[common],
                                          help="Create a new Memex repo from seed threads")
    spawn_parser.add_argument("name", help="Project name (becomes directory name)")
    spawn_parser.add_argument("--threads", required=True,
                               help="Comma-separated list of thread names to seed")
    spawn_parser.add_argument("--dry-run", action="store_true",
                               help="Show what would be copied without creating anything")

    # health
    health_parser = subparsers.add_parser("health", parents=[common],
                                           help="Run graph health check (PNG, JSON)")
    health_parser.add_argument("--image", default=None,
                                help="Output path for graph PNG (e.g., docs/wiki/thread-graph.png)")
    health_parser.add_argument("--json-out", default=None, metavar="PATH",
                                help="Output path for health JSON")
    health_parser.add_argument("--graph", default=None,
                                help="Filter by graph namespace (e.g., 'design', 'user')")

    # crawl
    crawl_parser = subparsers.add_parser("crawl", parents=[common],
                                          help="Run crawler (health triage + optional Sonnet fixes)")
    crawl_parser.add_argument("--fix", action="store_true",
                               help="Invoke Sonnet to propose fixes (requires ANTHROPIC_API_KEY)")
    crawl_parser.add_argument("--graph", default=None,
                               help="Filter by graph namespace")
    crawl_parser.add_argument("--no-branch", action="store_true",
                               help="In fix mode, don't create a git branch")

    # connect
    connect_parser = subparsers.add_parser("connect", parents=[common],
                                            help="Add annotated cross-reference between threads")
    connect_parser.add_argument("source", metavar="from", help="Source thread name")
    connect_parser.add_argument("target", metavar="to", help="Target thread name")
    connect_parser.add_argument("--why", required=True, help="Annotation: why this link exists")

    # suggest
    subparsers.add_parser("suggest", parents=[common],
                          help="Suggest what to work on next")

    # draft
    subparsers.add_parser("draft", parents=[common],
                          help="Show the current commit draft")

    # thread new
    thread_parser = subparsers.add_parser("thread", parents=[common],
                                           help="Thread operations")
    thread_sub = thread_parser.add_subparsers(dest="thread_command")
    thread_new = thread_sub.add_parser("new", parents=[common],
                                        help="Create a new thread")
    thread_new.add_argument("name", help="Thread name (will be slugified)")
    thread_new.add_argument("--title", default=None, help="Thread title (default: derived from name)")
    thread_new.add_argument("--category", default=None, help="Category (default: systems)")
    thread_new.add_argument("--tags", default=None, help="Comma-separated tags")

    # peek
    subparsers.add_parser("peek", parents=[common],
                          help="Quick cross-galaxy orientation: health, threads, roadmap, issues, last commit")

    # init
    init_parser = subparsers.add_parser("init", parents=[common],
                                         help="Initialize a new Memex project")
    init_parser.add_argument("--name", default=None,
                              help="Project name (skips interactive prompt)")
    init_parser.add_argument("--building", default=None,
                              help="What you're building (skips interactive prompt)")
    init_parser.add_argument("--pi", default=None,
                              help="Your name (skips interactive prompt)")
    init_parser.add_argument("--force", action="store_true",
                              help="Re-initialize even if already set up")

    # explain
    explain_parser = subparsers.add_parser("explain", parents=[common],
                                            help="Explain what the Memex can do")
    explain_parser.add_argument("topic", nargs="?", default="overview",
                                help="Topic: overview, threads, health, commands")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return 0

    def cmd_spawn(args):
        from spawn import run_spawn
        thread_list = [t.strip() for t in args.threads.split(",")]
        return run_spawn(args.name, thread_list, dry_run=args.dry_run, fmt=args.format)

    def cmd_thread(args):
        if getattr(args, 'thread_command', None) == "new":
            return cmd_thread_new(args)
        print("Usage: memex thread new <name>")
        return 1

    def cmd_peek(args):
        """Quick cross-galaxy orientation: roadmap, issues, threads, health, inbox, last commit."""
        import subprocess

        repo_root = find_repo_root(getattr(args, "repo", None))
        memex_dir = repo_root / "memex"
        fmt = get_formatter(args)

        # Graph health
        threads = load_threads(memex_dir)
        health_data = None
        try:
            from graph_health import build_graph, compute_health
            G, path_to_title = build_graph(memex_dir, threads)
            health_data = compute_health(G, path_to_title)
        except Exception:
            health_data = {"verdict": "UNKNOWN", "overall": 0, "nodes": len(threads), "edges": 0}

        # Inbox
        inbox = parse_inbox(memex_dir)

        # Active threads (sorted by staleness)
        active = [t for t in threads if t.tier_label.lower().startswith("active")]
        active.sort(key=lambda t: (thread_staleness(t), -t.hits, t.title.lower()))
        thread_data = [{
            "title": t.title,
            "hits": t.hits,
            "last_touched": t.last_touched,
            "staleness_days": thread_staleness(t),
            "category": t.category,
        } for t in active]

        # Roadmap summary (first 20 non-empty lines after the header)
        roadmap_path = memex_dir / "roadmap.md"
        roadmap_summary = None
        if roadmap_path.exists():
            lines = roadmap_path.read_text(encoding="utf-8").splitlines()
            content_lines = [l for l in lines if l.strip() and not l.startswith("---")]
            roadmap_summary = "\n".join(content_lines[:25])

        # Issues summary
        issues_path = memex_dir / "issues.md"
        issues_summary = None
        if issues_path.exists():
            lines = issues_path.read_text(encoding="utf-8").splitlines()
            content_lines = [l for l in lines if l.strip() and not l.startswith("---")]
            issues_summary = "\n".join(content_lines[:20])

        # Last git commit
        last_commit = None
        try:
            result = subprocess.run(
                ["git", "log", "--oneline", "-3"],
                cwd=str(repo_root), capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                last_commit = result.stdout.strip()
        except Exception:
            pass

        # Galaxy name
        galaxy_name = repo_root.name

        if args.format == "json":
            output = {
                "galaxy": galaxy_name,
                "date": TODAY.isoformat(),
                "graph_health": health_data,
                "inbox_count": len(inbox),
                "active_threads": thread_data,
                "roadmap_summary": roadmap_summary,
                "issues_summary": issues_summary,
                "last_commits": last_commit,
            }
            print(json.dumps(output, indent=2, default=str))
        else:
            print(f"\n{BOLD}Peek: {galaxy_name}{NC}\n")
            if health_data:
                score = health_data.get("overall", 0)
                verdict = health_data.get("verdict", "?")
                color = GREEN if score >= 80 else (YELLOW if score >= 60 else RED)
                print(f"  {BOLD}Health:{NC}  {color}{verdict} ({score}/100){NC}  {len(threads)} threads")
            print(f"  {BOLD}Inbox:{NC}   {len(inbox)} item(s)")
            print()
            if thread_data:
                print(f"  {BOLD}Active Threads{NC} ({len(thread_data)})")
                for t in thread_data[:8]:
                    stale = t["staleness_days"]
                    stale_color = GREEN if stale <= 3 else (YELLOW if stale <= 7 else RED)
                    print(f"    {t['title']}  {DIM}hits:{t['hits']}  {stale_color}{t['last_touched']}{NC}")
                print()
            if roadmap_summary:
                print(f"  {BOLD}Roadmap (excerpt){NC}")
                for line in roadmap_summary.splitlines()[:10]:
                    print(f"    {DIM}{line}{NC}")
                print()
            if issues_summary:
                print(f"  {BOLD}Issues (excerpt){NC}")
                for line in issues_summary.splitlines()[:8]:
                    print(f"    {DIM}{line}{NC}")
                print()
            if last_commit:
                print(f"  {BOLD}Last Commits{NC}")
                for line in last_commit.splitlines():
                    print(f"    {DIM}{line}{NC}")
                print()
        return 0

    commands = {
        "status": cmd_status,
        "search": cmd_search,
        "read": cmd_read,
        "hit": cmd_hit,
        "inbox": cmd_inbox,
        "connect": cmd_connect,
        "spawn": cmd_spawn,
        "health": cmd_health,
        "crawl": cmd_crawl,
        "suggest": cmd_suggest,
        "draft": cmd_draft,
        "thread": cmd_thread,
        "init": cmd_init,
        "explain": cmd_explain,
        "peek": cmd_peek,
    }

    return commands[args.command](args)


if __name__ == "__main__":
    raise SystemExit(main())
