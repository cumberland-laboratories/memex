#!/usr/bin/env python3
"""Crawler — automated Memex maintenance operator.

Runs graph_health.py, triages findings against the graph-health-response
procedure thresholds, and either produces a report (dry-run) or invokes
Sonnet to propose fixes on a maintenance branch (fix mode).

Usage:
  python .memex/scripts/crawler.py                       # dry-run: report only
  python .memex/scripts/crawler.py --fix                  # propose fixes via Sonnet
  python .memex/scripts/crawler.py --graph design         # check only the design layer
  python .memex/scripts/crawler.py --fix --no-branch      # fix mode without git branching
"""

from __future__ import annotations

import argparse
import datetime as dt
import io
import json
import subprocess
import sys
import textwrap
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parents[2]
MEMEX_DIR = REPO_ROOT / "memex"
SCRIPTS_DIR = Path(__file__).resolve().parent
REPORTS_DIR = REPO_ROOT / "docs" / "reports"
PROCEDURE_PATH = REPO_ROOT / ".memex" / "procedures" / "graph-health-response.md"

# ── Colors ─────────────────────────────────────────────────────────────

RED = "\033[0;31m"
YELLOW = "\033[0;33m"
GREEN = "\033[0;32m"
CYAN = "\033[0;36m"
BOLD = "\033[1m"
NC = "\033[0m"


def run_health_check(graph_filter: str | None = None) -> dict:
    """Run graph_health.py --json and return parsed results."""
    cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "graph_health.py"),
        "--json", str(REPO_ROOT / "wiki" / "graph-health-crawler.json"),
        "--repo-root", str(REPO_ROOT),
    ]
    if graph_filter:
        cmd.extend(["--graph", graph_filter])

    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")

    json_path = REPO_ROOT / "wiki" / "graph-health-crawler.json"

    # graph_health.py exits 1 when findings exist (normal) — only fail if
    # it didn't produce JSON output (actual error, e.g., bad --graph filter)
    if not json_path.exists():
        output = (result.stdout or "") + (result.stderr or "")
        import re
        clean = re.sub(r"\033\[[0-9;]*m", "", output)
        print(f"{RED}ERROR:{NC} graph_health.py failed to produce output")
        for line in clean.strip().splitlines()[-5:]:
            print(f"  {line}")
        sys.exit(1)

    return json.loads(json_path.read_text(encoding="utf-8"))


def triage(health: dict) -> list[dict]:
    """Triage health data against procedure thresholds. Returns findings."""
    findings = []
    scores = health.get("scores", {})

    # Navigability
    nav = scores.get("navigability", 100)
    intra = health.get("intra_hop_violations", 0)
    cross = health.get("cross_hop_violations", 0)
    if nav < 70:
        findings.append({
            "dimension": "navigability",
            "severity": "red",
            "score": nav,
            "detail": f"{intra} intra-cluster + {cross} cross-cluster violations",
            "action": "Propose transfer station links for intra-cluster violations (worst first)",
        })
    elif nav < 90:
        findings.append({
            "dimension": "navigability",
            "severity": "yellow",
            "score": nav,
            "detail": f"{intra} intra-cluster + {cross} cross-cluster violations",
            "action": "Report intra-cluster violations; suggest candidate transfer station links",
        })

    # Resilience
    res = scores.get("resilience", 100)
    bridges = health.get("bridges", 0)
    if res < 70:
        findings.append({
            "dimension": "resilience",
            "severity": "red",
            "score": res,
            "detail": f"{bridges} bridge edge(s)",
            "action": "Propose redundant paths for all bridge edges (urgent)",
        })
    elif res < 100:
        findings.append({
            "dimension": "resilience",
            "severity": "yellow",
            "score": res,
            "detail": f"{bridges} bridge edge(s)",
            "action": "Propose one redundant path per bridge edge",
        })

    # Connectivity
    conn = scores.get("connectivity", 100)
    orphans = health.get("orphans", [])
    intra_orphans = health.get("intra_cluster_orphans", [])
    if conn < 50:
        findings.append({
            "dimension": "connectivity",
            "severity": "red",
            "score": conn,
            "detail": f"{len(intra_orphans)} intra-cluster orphan(s), {len(orphans)} global orphan(s)",
            "action": "Propose inbound links for all intra-cluster orphans",
            "orphans": intra_orphans,
        })
    elif conn < 80:
        findings.append({
            "dimension": "connectivity",
            "severity": "yellow",
            "score": conn,
            "detail": f"{len(intra_orphans)} intra-cluster orphan(s), {len(orphans)} global orphan(s)",
            "action": "Report intra-cluster orphans; suggest cluster neighbor inbound links",
            "orphans": intra_orphans,
        })

    # Efficiency
    eff = scores.get("efficiency", 100)
    ratio = health.get("redundancy_ratio", 0.5)
    if ratio > 0.75:
        findings.append({
            "dimension": "efficiency",
            "severity": "red",
            "score": eff,
            "detail": f"Redundancy ratio {ratio:.0%} (>75%)",
            "action": "Propose pruning candidates — list redundant edges sorted by easiest to prune",
        })
    elif ratio > 0.60:
        findings.append({
            "dimension": "efficiency",
            "severity": "yellow",
            "score": eff,
            "detail": f"Redundancy ratio {ratio:.0%} (>60%)",
            "action": "Flag over-linked threads; list threads with most redundant connections",
        })
    elif ratio < 0.30:
        findings.append({
            "dimension": "efficiency",
            "severity": "yellow",
            "score": eff,
            "detail": f"Redundancy ratio {ratio:.0%} (<30%)",
            "action": "Flag fragile tree structure; suggest adding redundant paths",
        })

    # Legibility
    leg = scores.get("legibility", 100)
    stranded = health.get("peripherals_stranded", [])
    if leg < 70:
        findings.append({
            "dimension": "legibility",
            "severity": "red",
            "score": leg,
            "detail": f"{len(stranded)} stranded peripheral(s)",
            "action": "Propose hub connections for all stranded peripherals",
            "stranded": stranded,
        })
    elif leg < 90:
        findings.append({
            "dimension": "legibility",
            "severity": "yellow",
            "score": leg,
            "detail": f"{len(stranded)} stranded peripheral(s)",
            "action": "Report stranded peripherals; suggest hub connections",
            "stranded": stranded,
        })

    return findings


def print_report(health: dict, findings: list[dict], graph_filter: str | None) -> str:
    """Print triage report to console and return as string for file output."""
    today = dt.date.today().isoformat()
    graph_label = f" ({graph_filter} layer)" if graph_filter else ""

    lines = []
    lines.append(f"# Crawler Report — {today}{graph_label}")
    lines.append(f"")
    lines.append(f"Model: {health.get('model', 'unknown')}")
    lines.append(f"Verdict: **{health['verdict']}** ({health['overall']}/100)")
    lines.append(f"")
    lines.append(f"| Dimension | Score |")
    lines.append(f"|-----------|-------|")
    for dim in ["navigability", "resilience", "connectivity", "efficiency", "legibility"]:
        score = health.get("scores", {}).get(dim, "?")
        lines.append(f"| {dim.capitalize()} | {score} |")
    lines.append(f"")
    lines.append(f"Nodes: {health['nodes']}  Edges: {health['edges']}  "
                 f"Clusters: {health.get('clusters', '?')}  "
                 f"Redundancy: {health.get('redundancy_ratio', 0):.0%}")
    lines.append(f"")

    if not findings:
        lines.append(f"## Findings")
        lines.append(f"")
        lines.append(f"All dimensions green. No action needed.")
    else:
        lines.append(f"## Findings ({len(findings)})")
        lines.append(f"")
        for i, f in enumerate(findings, 1):
            severity_icon = "🔴" if f["severity"] == "red" else "🟡"
            lines.append(f"### {i}. {f['dimension'].capitalize()} — {f['severity'].upper()}")
            lines.append(f"")
            lines.append(f"Score: {f['score']}/100")
            lines.append(f"Detail: {f['detail']}")
            lines.append(f"Action: {f['action']}")
            if "orphans" in f:
                lines.append(f"Orphans: {', '.join(f['orphans'])}")
            if "stranded" in f:
                lines.append(f"Stranded: {', '.join(f['stranded'])}")
            lines.append(f"")

    report_text = "\n".join(lines)

    # Console output
    print(f"\n{BOLD}{'=' * 40}{NC}")
    print(f"{BOLD}  Crawler Report{graph_label}{NC}")
    print(f"{BOLD}{'=' * 40}{NC}\n")

    verdict_color = GREEN if health["verdict"] == "HEALTHY" else (YELLOW if health["verdict"] == "FAIR" else RED)
    print(f"  {verdict_color}{health['verdict']}{NC}  ({health['overall']}/100)\n")

    scores = health.get("scores", {})
    for dim in ["navigability", "resilience", "connectivity", "efficiency", "legibility"]:
        score = scores.get(dim, 0)
        color = GREEN if score >= 90 else (YELLOW if score >= 70 else RED)
        print(f"  {color}{score:3d}{NC}  {dim.capitalize()}")
    print()

    if not findings:
        print(f"  {GREEN}All dimensions green. No action needed.{NC}\n")
    else:
        print(f"  {YELLOW}{len(findings)} finding(s):{NC}\n")
        for f in findings:
            sev_color = RED if f["severity"] == "red" else YELLOW
            print(f"  {sev_color}[{f['severity'].upper()}]{NC} {f['dimension'].capitalize()}: {f['detail']}")
            print(f"        → {f['action']}")
            print()

    return report_text


def build_thread_inventory(memex_dir: Path, graph_filter: str | None = None) -> str:
    """Build an inventory of thread files with their titles and paths for Sonnet."""
    sys.path.insert(0, str(SCRIPTS_DIR))
    from generate_wiki import load_threads
    threads = load_threads(memex_dir)
    if graph_filter:
        threads = [t for t in threads if t.graph == graph_filter]

    lines = []
    for t in sorted(threads, key=lambda t: t.title):
        rel_path = t.source_path.relative_to(REPO_ROOT)
        lines.append(f"  {rel_path}  |  {t.title}  |  graph:{t.graph}")
    return "\n".join(lines)


def build_sonnet_prompt(health: dict, findings: list[dict], procedure_text: str,
                        thread_inventory: str) -> str:
    """Build the prompt for Sonnet to propose fixes."""
    health_summary = json.dumps(health, indent=2)

    findings_text = ""
    for f in findings:
        findings_text += f"\n- [{f['severity'].upper()}] {f['dimension']}: {f['detail']}\n"
        findings_text += f"  Action: {f['action']}\n"
        if "orphans" in f:
            findings_text += f"  Orphans: {', '.join(f['orphans'])}\n"
        if "stranded" in f:
            findings_text += f"  Stranded: {', '.join(f['stranded'])}\n"

    return textwrap.dedent(f"""\
    You are the Crawler — an automated maintenance operator for a Memex knowledge graph.

    Your job: propose specific, minimal fixes for the findings below. Each fix is an edit
    to a thread file's ## Connections section (add or remove a link). Every connection you
    add must have a genuine semantic justification in the annotation.

    ## Procedure (your governing rules)

    {procedure_text}

    ## Thread Inventory (exact file paths — use these, do not guess paths)

    {thread_inventory}

    ## Current Health Data

    ```json
    {health_summary}
    ```

    ## Findings Requiring Fixes

    {findings_text}

    ## Output Format (STRICT — must be machine-parseable)

    Output ONLY fix blocks in this exact format, one per fix. No prose before or after.
    No markdown headers. No explanations outside the blocks. Start immediately with FIX 1.

    FIX 1
    FILE: memex/threads/example-thread.md
    ACTION: add_connection
    LINE: → [Target Thread](relative-path-to-target.md) — semantic justification
    REASON: One sentence explaining why this connection is genuine.

    FIX 2
    FILE: memex/threads/another-thread.md
    ACTION: remove_connection
    LINE: → [Target Thread](relative-path-to-target.md) — the existing line to remove
    REASON: One sentence explaining why this removal is safe.

    Rules:
    - Use EXACT file paths from the Thread Inventory above
    - For link targets in the LINE, use paths relative to the source file's directory
    - Every added connection must be semantically genuine — the REASON must explain WHY
    - No thread should have fewer than 2 outbound connections after changes
    - Do not add connections just to improve a score — the Gillettes principle applies
    - Prefer adding one well-chosen link over multiple weak ones
    - For orphans: add one inbound link from the most semantically related cluster neighbor
    - For bridges: add one redundant path via a third thread related to both endpoints
    """)


def call_sonnet(prompt: str) -> str:
    """Call Sonnet via Anthropic API. Returns the response text."""
    try:
        import anthropic
    except ImportError:
        print(f"{RED}ERROR:{NC} anthropic package not installed. Run: pip install anthropic")
        sys.exit(1)

    import os
    api_key = os.environ.get("ANTHROPIC_API_KEY")

    # Fallback: load from VS Code settings if not in environment
    if not api_key:
        vscode_settings = Path.home() / "AppData" / "Roaming" / "Code" / "User" / "settings.json"
        if vscode_settings.exists():
            try:
                import json as _json
                vs = _json.loads(vscode_settings.read_text(encoding="utf-8"))
                api_key = vs.get("terminal.integrated.env.windows", {}).get("ANTHROPIC_API_KEY")
            except Exception:
                pass

    if not api_key:
        print(f"{RED}ERROR:{NC} ANTHROPIC_API_KEY not found in environment or VS Code settings")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def parse_fixes(response: str) -> list[dict]:
    """Parse Sonnet's FIX blocks into structured edits."""
    fixes = []
    current: dict | None = None

    for line in response.splitlines():
        stripped = line.strip()
        if stripped.startswith("FIX "):
            if current and "file" in current:
                fixes.append(current)
            current = {}
        elif current is not None:
            if stripped.startswith("FILE:"):
                current["file"] = stripped[5:].strip()
            elif stripped.startswith("ACTION:"):
                current["action"] = stripped[7:].strip()
            elif stripped.startswith("LINE:"):
                current["line"] = stripped[5:].strip()
            elif stripped.startswith("REASON:"):
                current["reason"] = stripped[7:].strip()

    if current and "file" in current:
        fixes.append(current)

    return fixes


def apply_fixes(fixes: list[dict]) -> list[str]:
    """Apply parsed fixes to thread files. Returns list of applied descriptions."""
    applied = []

    for fix in fixes:
        file_path = REPO_ROOT / fix["file"]
        action = fix.get("action", "")
        line = fix.get("line", "")
        reason = fix.get("reason", "")

        if not file_path.exists():
            print(f"  {YELLOW}SKIP:{NC} File not found: {fix['file']}")
            continue

        if not line:
            print(f"  {YELLOW}SKIP:{NC} No LINE specified for {fix['file']}")
            continue

        text = file_path.read_text(encoding="utf-8")

        if action == "add_connection":
            # Find the ## Connections section and append the line
            if "## Connections" not in text:
                print(f"  {YELLOW}SKIP:{NC} No ## Connections section in {fix['file']}")
                continue

            # Insert before the next ## heading or at end of file
            sections = text.split("## Connections")
            if len(sections) < 2:
                continue

            before = sections[0] + "## Connections"
            after = sections[1]

            # Find where the connections section ends (next ## or end of file)
            after_lines = after.split("\n")
            insert_idx = len(after_lines)
            for i, aline in enumerate(after_lines):
                if i > 0 and aline.startswith("## "):
                    insert_idx = i
                    break

            # Insert the new connection line before the next section
            # Find the last non-empty line in the connections section
            last_content = insert_idx - 1
            while last_content > 0 and not after_lines[last_content].strip():
                last_content -= 1

            after_lines.insert(last_content + 1, line)
            new_text = before + "\n".join(after_lines)

            file_path.write_text(new_text, encoding="utf-8")
            desc = f"ADD  {fix['file']}: {line[:80]}"
            print(f"  {GREEN}APPLIED:{NC} {desc}")
            applied.append(desc)

        elif action == "remove_connection":
            if line in text:
                new_text = text.replace(line + "\n", "")
                if new_text == text:
                    new_text = text.replace(line, "")
                file_path.write_text(new_text, encoding="utf-8")
                desc = f"REMOVE {fix['file']}: {line[:80]}"
                print(f"  {GREEN}APPLIED:{NC} {desc}")
                applied.append(desc)
            else:
                print(f"  {YELLOW}SKIP:{NC} Line not found in {fix['file']}")

        else:
            print(f"  {YELLOW}SKIP:{NC} Unknown action '{action}' for {fix['file']}")

    return applied


def create_maintenance_branch() -> str:
    """Create and checkout a maintenance branch. Returns branch name."""
    today = dt.date.today().isoformat()
    branch_name = f"crawler/maintenance-{today}"

    # Check if branch already exists
    result = subprocess.run(
        ["git", "branch", "--list", branch_name],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    if result.stdout.strip():
        # Branch exists, just check it out
        subprocess.run(["git", "checkout", branch_name], cwd=str(REPO_ROOT), check=True)
    else:
        subprocess.run(["git", "checkout", "-b", branch_name], cwd=str(REPO_ROOT), check=True)

    return branch_name


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--fix", action="store_true",
        help="Invoke Sonnet to propose fixes (requires ANTHROPIC_API_KEY)",
    )
    parser.add_argument(
        "--graph", default=None, type=str,
        help="Filter by graph namespace (e.g., 'design', 'user')",
    )
    parser.add_argument(
        "--no-branch", action="store_true",
        help="In fix mode, don't create a git branch (just output fixes)",
    )
    args = parser.parse_args()

    # Ensure UTF-8 output on Windows
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    # Step 1: Run health check
    print(f"{CYAN}Running graph health check...{NC}")
    health = run_health_check(graph_filter=args.graph)

    # Step 2: Triage
    findings = triage(health)

    # Step 3: Report
    report_text = print_report(health, findings, args.graph)

    # Save report
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    today = dt.date.today().isoformat()
    graph_suffix = f"-{args.graph}" if args.graph else ""
    report_path = REPORTS_DIR / f"{today}-crawler-report{graph_suffix}.md"
    report_path.write_text(report_text, encoding="utf-8")
    print(f"  Report saved to {report_path}\n")

    # Step 4: If dry-run, stop here
    if not args.fix:
        if findings:
            print(f"  {YELLOW}Dry run. Use --fix to invoke Sonnet for proposed fixes.{NC}")
        return 1 if any(f["severity"] == "red" for f in findings) else 0

    # Step 5: Fix mode — call Sonnet
    if not findings:
        print(f"  {GREEN}No findings to fix.{NC}")
        return 0

    # Read the procedure
    if not PROCEDURE_PATH.exists():
        print(f"{RED}ERROR:{NC} Procedure not found: {PROCEDURE_PATH}")
        return 1
    procedure_text = PROCEDURE_PATH.read_text(encoding="utf-8")

    # Create maintenance branch BEFORE applying fixes
    branch = None
    if not args.no_branch:
        print(f"\n{CYAN}Creating maintenance branch...{NC}")
        branch = create_maintenance_branch()
        print(f"  Branch: {branch}")

    # Build prompt with thread inventory and call Sonnet
    print(f"\n{CYAN}Building thread inventory...{NC}")
    thread_inventory = build_thread_inventory(MEMEX_DIR, graph_filter=args.graph)
    print(f"{CYAN}Invoking Sonnet for fix proposals...{NC}")
    prompt = build_sonnet_prompt(health, findings, procedure_text, thread_inventory)
    response = call_sonnet(prompt)

    print(f"\n{BOLD}{'=' * 40}{NC}")
    print(f"{BOLD}  Sonnet's Response{NC}")
    print(f"{BOLD}{'=' * 40}{NC}\n")
    print(response)

    # Parse and apply fixes
    fixes = parse_fixes(response)
    if not fixes:
        print(f"\n  {YELLOW}No parseable fixes found in Sonnet's response.{NC}")
        full_report = report_text + f"\n\n## Sonnet's Response\n\n{response}\n"
        report_path.write_text(full_report, encoding="utf-8")
        return 0

    print(f"\n{BOLD}{'=' * 40}{NC}")
    print(f"{BOLD}  Applying {len(fixes)} Fix(es){NC}")
    print(f"{BOLD}{'=' * 40}{NC}\n")

    applied = apply_fixes(fixes)

    if applied:
        # Re-run health check to verify improvement
        print(f"\n{CYAN}Re-running health check to verify...{NC}")
        new_health = run_health_check(graph_filter=args.graph)
        new_scores = new_health.get("scores", {})
        old_scores = health.get("scores", {})

        print(f"\n{BOLD}  Before → After{NC}\n")
        for dim in ["navigability", "resilience", "connectivity", "efficiency", "legibility"]:
            old = old_scores.get(dim, 0)
            new = new_scores.get(dim, 0)
            delta = new - old
            arrow = f"{GREEN}+{delta}{NC}" if delta > 0 else (f"{RED}{delta}{NC}" if delta < 0 else "  0")
            print(f"  {dim.capitalize():15s}  {old:3d} → {new:3d}  ({arrow})")
        print(f"  {'Overall':15s}  {health['overall']:3d} → {new_health['overall']:3d}")

        # Save full report
        applied_text = "\n".join(f"- {a}" for a in applied)
        full_report = (report_text +
                       f"\n\n## Sonnet's Response\n\n{response}\n"
                       f"\n## Applied Fixes\n\n{applied_text}\n"
                       f"\n## Post-Fix Health\n\n"
                       f"Verdict: **{new_health['verdict']}** ({new_health['overall']}/100)\n")
        report_path.write_text(full_report, encoding="utf-8")
        print(f"\n  Report saved to {report_path}")

        if branch:
            print(f"\n  {CYAN}Fixes applied on branch: {branch}{NC}")
            print(f"  Review the changes, then commit and open a PR to dev.")
            print(f"  To return to dev: git checkout dev")
    else:
        print(f"\n  {YELLOW}No fixes were applied.{NC}")
        full_report = report_text + f"\n\n## Sonnet's Response\n\n{response}\n"
        report_path.write_text(full_report, encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
