#!/usr/bin/env python3
"""Spawn — create a new Memex repo from seed threads.

Knowledge-layer operation: selects threads, follows artifact/vault references,
copies the portable Memex skeleton, and mechanically repairs the subgraph.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPTS_DIR.parent.parent

sys.path.insert(0, str(SCRIPTS_DIR))
from generate_wiki import parse_frontmatter, parse_sections


# ── Constants ────────────────────────────────────────────────────────────────

# File extensions considered textual (safe to copy from vault)
TEXT_EXTENSIONS = {
    ".md", ".txt", ".csv", ".json", ".yaml", ".yml",
    ".py", ".sh", ".tex", ".bib", ".r", ".jl", ".toml",
}

# Markdown link pattern: [text](path)
LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")


# ── Dependency resolution ────────────────────────────────────────────────────

def resolve_seed_threads(memex_dir: Path, names: list[str]) -> list[Path]:
    """Resolve thread names to file paths. Fails fast if any not found."""
    from memex import resolve_thread, list_thread_names

    paths = []
    for name in names:
        name = name.strip()
        if not name:
            continue
        path = resolve_thread(memex_dir, name)
        if not path:
            candidates = list_thread_names(memex_dir)
            print(f"Thread not found: '{name}'")
            if candidates:
                print(f"Available: {', '.join(candidates)}")
            raise SystemExit(1)
        paths.append(path)
    return paths


def collect_dependencies(memex_dir: Path, seed_paths: list[Path]) -> dict:
    """Collect artifacts and vault files referenced by seed threads."""
    artifacts = []
    vault_files = []

    artifacts_dir = memex_dir / "artifacts"
    vault_dir = memex_dir / "vault"

    for thread_path in seed_paths:
        text = thread_path.read_text(encoding="utf-8")

        # Find inline artifact references (links containing artifacts/)
        for match in LINK_RE.finditer(text):
            link_target = match.group(2)
            if "artifacts/" in link_target:
                # Resolve relative to thread's directory
                resolved = (thread_path.parent / link_target).resolve()
                if resolved.exists() and resolved not in artifacts:
                    artifacts.append(resolved)

    # For each artifact, check for vault references via source: frontmatter
    for art_path in artifacts:
        text = art_path.read_text(encoding="utf-8")
        fm, _ = parse_frontmatter(text)
        source = fm.get("source", "")
        if source and "vault/" in source:
            # source is relative to repo root
            vault_path = REPO_ROOT / source
            if not vault_path.exists():
                # Try relative to memex dir
                vault_path = memex_dir / source.replace("memex/", "", 1)
            if vault_path.exists() and vault_path.suffix.lower() in TEXT_EXTENSIONS:
                if vault_path not in vault_files:
                    vault_files.append(vault_path)

    # Also check seed threads for direct vault references
    for thread_path in seed_paths:
        text = thread_path.read_text(encoding="utf-8")
        for match in LINK_RE.finditer(text):
            link_target = match.group(2)
            if "vault/" in link_target:
                resolved = (thread_path.parent / link_target).resolve()
                if not resolved.exists():
                    resolved = REPO_ROOT / link_target.lstrip("./")
                if not resolved.exists():
                    resolved = memex_dir / link_target.replace("memex/", "", 1)
                if resolved.exists() and resolved.suffix.lower() in TEXT_EXTENSIONS:
                    if resolved not in vault_files:
                        vault_files.append(resolved)

        # Also check for source: lines outside frontmatter (like -> Source: path)
        for line in text.splitlines():
            if line.strip().startswith("-> Source:") or line.strip().startswith("→ Source:"):
                # Extract backtick-quoted path or bare path
                path_match = re.search(r"`([^`]+)`", line)
                if path_match:
                    source_ref = path_match.group(1)
                elif ":" in line:
                    source_ref = line.split(":", 1)[1].strip()
                else:
                    continue
                if "vault/" in source_ref:
                    vault_path = REPO_ROOT / source_ref
                    if not vault_path.exists():
                        vault_path = memex_dir / source_ref.replace("memex/", "", 1)
                    if vault_path.exists() and vault_path.suffix.lower() in TEXT_EXTENSIONS:
                        if vault_path not in vault_files:
                            vault_files.append(vault_path)

    return {
        "threads": seed_paths,
        "artifacts": artifacts,
        "vault_files": vault_files,
    }


# ── Skeleton creation ────────────────────────────────────────────────────────

GENERIC_CONSTITUTION = """\
# {project_name} — Constitution

A Memex for {project_name} — tracking ideas, experiments, and progress across sessions.

## What This Is

This repo is a persistence layer — it makes the LLM feel like it was there yesterday. The Memex is a small-world network of cross-referenced threads, not a hierarchical index. Navigate by entering any node and following links.

## Roles

| Role | What it does | Who runs it |
|------|-------------|-------------|
| **Chat agent** | Talks to the human. Reads and writes the Memex in-session — updates threads, creates artifacts, compresses and rotates. | Claude Code (primary session) |
| **Enforcer** | Audits the Memex (read-only) and produces reports and documentation renders. Does not edit Memex files. Must be a different model. | Different model (e.g., Sonnet checking Opus's work) |

## Memex Structure

```
.memex/                   ← machinery (portable, upstream-maintained, don't modify)
  roles.yaml              ← role definitions
  policies/               ← concierge wisdom and operational guidelines
  procedures/             ← core Memex operational procedures
  scripts/                ← CLI and tooling
memex/                    ← knowledge graph (navigable, compressed, cross-referenced)
  mission.md              ← what we're building and why (always loaded)
  roadmap.md              ← feature roadmap (always loaded)
  issues.md               ← active bugs, blockers, known fragilities (always loaded)
  identity.md             ← stable traits, background, persistent interests (always loaded)
  inbox.md                ← zero-friction capture (always checked at session open, then cleared)
  active-threads/         ← current topics, 5-8 files (always loaded, compression-budgeted)
  threads/                ← lightweight reference threads (NOT always loaded, navigated via links)
  patterns/               ← recurring rhythms (always loaded)
  artifacts/              ← deep records, synopses, reference material (NOT always loaded)
  vault/                  ← external source files (gitignored, referenced by artifacts)
  procedures/             ← project-specific workflows (organic, PI-owned)
  reference-notes/        ← cognitive aids (consulted situationally)
  commit_draft.md         ← session change log, used as commit message source (cleared after commit)
docs/                     ← project documentation
  systems/                ← subsystem documentation
  reports/                ← enforcer audits, design reviews
  wiki/                   ← rendered output
```

**Navigation**: No central index — the graph is the index. Enter through active threads, follow cross-references.

**Compression rule**: Always-loaded files should stay under 400 lines total. Depth lives in threads/, artifacts/, and cross-references.

**Graph connectivity**: Every operation must preserve all cross-references.

## Operating Levels

Every message from the human operates at one of two levels:

| Level | Signal | What the agent does |
|-------|--------|--------------------|
| **Content** | `*c` prefix (or no prefix in user mode) | Use the Memex as infrastructure — read threads, capture ideas, update hits, create artifacts. The system is furniture. |
| **Meta** | `*m` prefix (or no prefix in designer mode) | Operate *on* the Memex itself — modify the constitution, restructure, write procedures. The system is the object of work. |

### Operating Mode

The default level is set by `operating-mode:` in `identity.md` frontmatter:

| Mode | Default level | Override |
|------|--------------|----------|
| `designer` | Meta | `*c` prefix switches to content |
| `user` | Content | `*m` prefix switches to meta |

## Session Opening

**Bootstrap detection**: Before running the normal procedure, check these three signals:
1. `memex/identity.md` still contains bracket placeholders (e.g., `[Your role`)
2. `memex/inbox.md` is empty (no captured thoughts)
3. `memex/active-threads/` contains ≤ 2 threads

If all three are true, this is a **first session**. Skip the normal session-opening procedure entirely. Simply greet the human and ask what's on their mind. Everything you need to read, read silently.

**Normal sessions**: Follow the session-opening procedure: → [session-lifecycle.md](.memex/procedures/session-lifecycle.md). Prefer the CLI path (`python .memex/scripts/memex.py status --full --role <your-role> --format json`). Your role is specified in your entry point file.

## Thread Lifecycle

Threads move between three tiers based on activity. Full lifecycle: → [thread-lifecycle.md](.memex/procedures/thread-lifecycle.md)

New threads should follow the template: → [_TEMPLATE.md](memex/active-threads/_TEMPLATE.md)

Key rules:
- Active threads that exceed **60 lines** must be evaluated for splitting.
- Every thread must carry a `## Summary` (2–4 sentences).
- Demotion moves threads intact — no compression, no information loss.
- Cross-references annotate *why* the link exists, not just that it does.

## Conventions

- **BRANCHING**: Default working branch is `dev`. Merges to `main` are human-authorized.
- **ARTIFACTS**: Deep records go in `memex/artifacts/` with date prefixes (`YYYY-MM-DD-short-title.md`).
- **VAULT**: External source files in `memex/vault/`, gitignored.
- **PROCEDURES**: Core procedures in `.memex/procedures/`. Project-specific workflows in `memex/procedures/`.
- **REFERENCE NOTES**: Cognitive aids in `memex/reference-notes/`.
- **CHANGELOG**: Use `git log`. No separate changelog file.
- **COMMIT DRAFT**: Maintain `memex/commit_draft.md`. Append changes during the session.
- **ENFORCER INDEPENDENCE**: The enforcer must be a different model than the chat agent.
- **INBOX**: Capture and organization are different operations.
- **CLIP**: Verbatim exchange capture: `[save]` or `[clip]`. Procedure: → [clip-to-artifact.md](.memex/procedures/clip-to-artifact.md)
"""

BLANK_IDENTITY = """\
---
operating-mode: user
---

# Identity

[Your role, background, how you think, what you're working on. The agent uses this to calibrate collaboration style.]
"""

BLANK_MISSION = """\
# Mission

## What We're Building

[What this project is and why it exists.]

## What Success Looks Like

[How you'll know it's working.]
"""

BLANK_ROADMAP = """\
# Feature Roadmap

Last updated: {date}

## Active

| # | Feature | Status | Next step |
|---|---------|--------|-----------|

## Connections

→ [mission.md](mission.md) — what success looks like
"""

BLANK_ISSUES = """\
# Issues

## Open

(none yet)

## Working

(none yet)

## Resolved

(none yet)
"""

BLANK_INBOX = """\
# Inbox

Drop anything here. No formatting needed. The chat agent triages at session open.

---
"""


def create_skeleton(target_dir: Path, project_name: str, source_repo: Path) -> None:
    """Create the portable Memex skeleton in target_dir."""
    import datetime as dt
    today = dt.date.today().isoformat()

    target_dir.mkdir(parents=True, exist_ok=False)

    # Directory structure
    dirs = [
        "memex/active-threads",
        "memex/threads",
        "memex/artifacts",
        "memex/vault",
        "memex/procedures",
        "memex/reference-notes",
        "memex/patterns",
        ".memex/scripts",
        ".memex/procedures",
        ".memex/policies",
        "docs/systems",
        "docs/reports",
        "docs/wiki",
    ]
    for d in dirs:
        (target_dir / d).mkdir(parents=True, exist_ok=True)

    # Constitution
    (target_dir / "constitution.md").write_text(
        GENERIC_CONSTITUTION.format(project_name=project_name),
        encoding="utf-8",
    )

    # Entry point files
    for ep in ["CLAUDE.md", "AGENTS.md", "GEMINI.md"]:
        src = source_repo / ep
        if src.exists():
            shutil.copy2(src, target_dir / ep)

    # Roles
    roles_src = source_repo / ".memex" / "roles.yaml"
    if roles_src.exists():
        shutil.copy2(roles_src, target_dir / ".memex" / "roles.yaml")

    # Scripts
    for script in (source_repo / ".memex" / "scripts").glob("*.py"):
        shutil.copy2(script, target_dir / ".memex" / "scripts" / script.name)

    # Core procedures
    for proc in (source_repo / ".memex" / "procedures").glob("*.md"):
        shutil.copy2(proc, target_dir / ".memex" / "procedures" / proc.name)

    # Policies
    for policy in (source_repo / ".memex" / "policies").glob("*.md"):
        shutil.copy2(policy, target_dir / ".memex" / "policies" / policy.name)

    # Templates
    for template_path in [
        "memex/active-threads/_TEMPLATE.md",
        "memex/artifacts/_TEMPLATE.md",
    ]:
        src = source_repo / template_path
        if src.exists():
            shutil.copy2(src, target_dir / template_path)

    docs_template = source_repo / "docs" / "systems" / "_TEMPLATE.md"
    if docs_template.exists():
        shutil.copy2(docs_template, target_dir / "docs" / "systems" / "_TEMPLATE.md")

    # Blank top-level memex files
    (target_dir / "memex" / "identity.md").write_text(BLANK_IDENTITY, encoding="utf-8")
    (target_dir / "memex" / "mission.md").write_text(BLANK_MISSION, encoding="utf-8")
    (target_dir / "memex" / "roadmap.md").write_text(
        BLANK_ROADMAP.format(date=today), encoding="utf-8",
    )
    (target_dir / "memex" / "issues.md").write_text(BLANK_ISSUES, encoding="utf-8")
    (target_dir / "memex" / "inbox.md").write_text(BLANK_INBOX, encoding="utf-8")
    (target_dir / "memex" / "commit_draft.md").write_text("", encoding="utf-8")

    # Gitignore for vault
    (target_dir / "memex" / "vault" / ".gitkeep").write_text("", encoding="utf-8")
    gitignore = target_dir / ".gitignore"
    gitignore.write_text("memex/vault/**\n!memex/vault/.gitkeep\n", encoding="utf-8")


# ── Copy seed content ────────────────────────────────────────────────────────

def copy_seed_content(target_dir: Path, deps: dict, memex_dir: Path) -> list[str]:
    """Copy seed threads, artifacts, and vault files into the new repo."""
    copied = []

    for thread_path in deps["threads"]:
        dest = target_dir / "memex" / "active-threads" / thread_path.name
        shutil.copy2(thread_path, dest)
        copied.append(f"memex/active-threads/{thread_path.name}")

    for art_path in deps["artifacts"]:
        dest = target_dir / "memex" / "artifacts" / art_path.name
        shutil.copy2(art_path, dest)
        copied.append(f"memex/artifacts/{art_path.name}")

    for vault_path in deps["vault_files"]:
        # Preserve subdirectory structure under vault/
        try:
            rel = vault_path.relative_to(memex_dir / "vault")
        except ValueError:
            rel = Path(vault_path.name)
        dest = target_dir / "memex" / "vault" / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(vault_path, dest)
        copied.append(f"memex/vault/{rel}")

    return copied


# ── Mechanical graph repair ──────────────────────────────────────────────────

def repair_graph(target_dir: Path, copied_files: list[str]) -> list[str]:
    """Mechanically repair cross-references in copied threads and artifacts.

    - Remove connections to threads that don't exist in the new repo
    - Fix relative paths for connections that do exist
    - Leave HTML comments noting what was pruned
    Returns list of repair descriptions.
    """
    repairs = []

    # Build index of files that exist in the new repo
    existing_stems = set()
    existing_files = {}  # stem -> relative path from active-threads
    for f in copied_files:
        p = Path(f)
        existing_stems.add(p.stem)
        existing_files[p.stem] = p.name

    # Also include templates and top-level files
    for md in (target_dir / "memex").rglob("*.md"):
        existing_stems.add(md.stem)

    # Process each copied thread and artifact
    for rel_path in copied_files:
        if not rel_path.endswith(".md"):
            continue

        file_path = target_dir / rel_path
        text = file_path.read_text(encoding="utf-8")
        original = text
        file_dir = file_path.parent

        # Fix connections section
        new_lines = []
        in_connections = False
        for line in text.splitlines():
            stripped = line.strip()

            if stripped == "## Connections":
                in_connections = True
                new_lines.append(line)
                continue

            if in_connections and stripped.startswith("## "):
                in_connections = False

            if in_connections and (stripped.startswith("->") or stripped.startswith("→")):
                # Parse the link target
                link_match = LINK_RE.search(stripped)
                if link_match:
                    link_text = link_match.group(1)
                    link_target = link_match.group(2)
                    target_stem = Path(link_target).stem

                    if target_stem not in existing_stems:
                        # Target doesn't exist — prune silently
                        # (no comment: parent thread names may be permission-sensitive)
                        repairs.append(f"PRUNED {rel_path}: 1 connection removed")
                        continue
                    else:
                        # Target exists — fix relative path if needed
                        # All seed threads are in active-threads/ now
                        if target_stem in existing_files:
                            target_file = existing_files[target_stem]
                            # Compute correct relative path
                            target_abs = None
                            for subdir in ["active-threads", "artifacts", "threads"]:
                                candidate = target_dir / "memex" / subdir / target_file
                                if candidate.exists():
                                    target_abs = candidate
                                    break
                            if target_abs:
                                import os
                                new_rel = os.path.relpath(target_abs, file_dir)
                                new_rel = Path(new_rel).as_posix()
                                # Get the annotation (everything after " — " or " - ")
                                annotation_match = re.search(
                                    r" [—\-] (.+)$", stripped
                                )
                                annotation = annotation_match.group(1) if annotation_match else ""
                                arrow = "→" if "→" in stripped else "->"
                                new_line = f"{arrow} [{link_text}]({new_rel})"
                                if annotation:
                                    new_line += f" — {annotation}"
                                new_lines.append(new_line)
                                if new_line != stripped:
                                    repairs.append(
                                        f"FIXED {rel_path}: path to {link_text}"
                                    )
                                continue

            # Also fix inline links outside connections
            if not in_connections:
                def fix_link(m):
                    lt, lp = m.group(1), m.group(2)
                    ts = Path(lp).stem
                    if ("threads/" in lp or "artifacts/" in lp) and ts not in existing_stems:
                        repairs.append(f"INLINE {rel_path}: removed link to {lt}")
                        return lt  # Plain text, no link
                    return m.group(0)

                line = LINK_RE.sub(fix_link, line)

            new_lines.append(line)

        new_text = "\n".join(new_lines)
        # Preserve trailing newline if original had one
        if original.endswith("\n") and not new_text.endswith("\n"):
            new_text += "\n"

        if new_text != original:
            file_path.write_text(new_text, encoding="utf-8")

    # Fix artifact source-thread paths
    for rel_path in copied_files:
        if "artifacts/" not in rel_path or not rel_path.endswith(".md"):
            continue
        file_path = target_dir / rel_path
        text = file_path.read_text(encoding="utf-8")
        if "source-thread:" in text:
            # Update source-thread to point to active-threads/
            new_text = re.sub(
                r"(source-thread:\s*)[\./]*(?:threads|active-threads)/",
                r"\1../active-threads/",
                text,
            )
            if new_text != text:
                file_path.write_text(new_text, encoding="utf-8")
                repairs.append(f"FIXED {rel_path}: source-thread path")

    return repairs


# ── Git initialization ───────────────────────────────────────────────────────

def git_init_and_commit(target_dir: Path, project_name: str) -> None:
    """Initialize git repo and create initial commit."""
    subprocess.run(["git", "init"], cwd=str(target_dir), check=True,
                   capture_output=True)
    subprocess.run(["git", "checkout", "-b", "dev"], cwd=str(target_dir),
                   check=True, capture_output=True)
    subprocess.run(["git", "add", "-A"], cwd=str(target_dir), check=True,
                   capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", f"Spawn {project_name} from parent Memex\n\n"
         f"Memex skeleton + seed threads from parent graph.\n"
         f"Knowledge-layer spawn — independent repo, no upstream."],
        cwd=str(target_dir), check=True, capture_output=True,
    )


# ── Main entry point (called from memex.py) ─────────────────────────────────

def run_spawn(name: str, thread_names: list[str], dry_run: bool = False,
              fmt: str = "pretty") -> int:
    """Execute the spawn operation."""
    import json

    memex_dir = REPO_ROOT / "memex"
    target_dir = REPO_ROOT.parent / name

    if target_dir.exists() and not dry_run:
        print(f"Target directory already exists: {target_dir}")
        return 1

    # Resolve seed threads
    seed_paths = resolve_seed_threads(memex_dir, thread_names)

    # Collect dependencies
    deps = collect_dependencies(memex_dir, seed_paths)

    if dry_run:
        result = {
            "command": "spawn",
            "project": name,
            "target": str(target_dir),
            "dry_run": True,
            "threads": [p.stem for p in deps["threads"]],
            "artifacts": [p.stem for p in deps["artifacts"]],
            "vault_files": [str(p.name) for p in deps["vault_files"]],
        }
        if fmt == "json":
            print(json.dumps(result, indent=2))
        else:
            print(f"  Spawn: {name}")
            print(f"  Target: {target_dir}")
            print(f"  Threads: {', '.join(p.stem for p in deps['threads'])}")
            print(f"  Artifacts: {', '.join(p.stem for p in deps['artifacts'])}")
            print(f"  Vault files: {', '.join(p.name for p in deps['vault_files'])}")
            print(f"\n  Dry run — no files created.")
        return 0

    # Create skeleton
    print(f"  Creating skeleton: {target_dir}")
    create_skeleton(target_dir, name, REPO_ROOT)

    # Copy seed content
    print(f"  Copying seed content...")
    copied = copy_seed_content(target_dir, deps, memex_dir)
    for c in copied:
        print(f"    + {c}")

    # Repair graph
    print(f"  Repairing graph...")
    repairs = repair_graph(target_dir, copied)
    for r in repairs:
        print(f"    {r}")

    # Git init
    print(f"  Initializing git repo...")
    git_init_and_commit(target_dir, name)

    if fmt == "json":
        result = {
            "command": "spawn",
            "project": name,
            "target": str(target_dir),
            "threads": [p.stem for p in deps["threads"]],
            "artifacts": [p.stem for p in deps["artifacts"]],
            "vault_files": [str(p.name) for p in deps["vault_files"]],
            "repairs": repairs,
        }
        print(json.dumps(result, indent=2))
    else:
        print(f"\n  ✓ Spawned {name} at {target_dir}")
        print(f"    {len(deps['threads'])} thread(s), "
              f"{len(deps['artifacts'])} artifact(s), "
              f"{len(deps['vault_files'])} vault file(s)")
        print(f"    {len(repairs)} graph repair(s)")
        print(f"    Branch: dev")
        print(f"\n  cd {target_dir} && claude")

    return 0
