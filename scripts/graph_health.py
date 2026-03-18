#!/usr/bin/env python3
"""Graph-health analysis for the Memex thread graph.

Reports:
  - Backlink index (who links to each thread)
  - 3-hop reachability violations
  - Single-bridge edges (removal disconnects the graph)
  - Graph visualization (PNG)

Usage:
  python scripts/graph_health.py
  python scripts/graph_health.py --image wiki/thread-graph.png
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

import networkx as nx

# Re-use the existing thread/link infrastructure
sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_wiki import extract_links, load_threads

RED = "\033[0;31m"
YELLOW = "\033[0;33m"
GREEN = "\033[0;32m"
CYAN = "\033[0;36m"
NC = "\033[0m"


def error(msg: str) -> None:
    print(f"{RED}ERROR:{NC} {msg}")


def warn(msg: str) -> None:
    print(f"{YELLOW}WARN:{NC}  {msg}")


def ok(msg: str) -> None:
    print(f"{GREEN}OK:{NC}    {msg}")


def info(msg: str) -> None:
    print(f"{CYAN}INFO:{NC}  {msg}")


def build_graph(memex_dir: Path) -> tuple[nx.DiGraph, dict[Path, str]]:
    """Build a directed graph from thread cross-references."""
    threads = load_threads(memex_dir)
    G = nx.DiGraph()
    path_to_title: dict[Path, str] = {}

    for thread in threads:
        resolved = thread.source_path.resolve()
        path_to_title[resolved] = thread.title
        G.add_node(resolved, title=thread.title, tier=thread.tier_label)

    for thread in threads:
        source = thread.source_path.resolve()
        links = extract_links(thread.connection_lines, thread.source_path)
        for link in links:
            if link.target_path and link.target_path in path_to_title:
                G.add_edge(source, link.target_path, annotation=link.annotation)

    return G, path_to_title


def report_backlinks(G: nx.DiGraph, path_to_title: dict[Path, str]) -> int:
    """Report inbound links for each thread. Returns orphan count as errors."""
    print("-- Backlink Index --")
    errors = 0
    backlinks: dict[Path, list[Path]] = defaultdict(list)
    for source, target in G.edges():
        backlinks[target].append(source)

    for node in sorted(G.nodes(), key=lambda n: path_to_title.get(n, "")):
        title = path_to_title[node]
        inbound = backlinks.get(node, [])
        if inbound:
            sources = ", ".join(path_to_title[s] for s in inbound)
            info(f"{title} <- {sources}")
        else:
            error(f"{title} <- (no inbound links — orphan)")
            errors += 1
    print()
    return errors


def report_reachability(G: nx.DiGraph, path_to_title: dict[Path, str], max_hops: int = 3) -> int:
    """Check that every node can reach every other node within max_hops."""
    print(f"-- {max_hops}-Hop Reachability --")
    errors = 0

    # Use the undirected view for reachability (links are navigable in both directions)
    U = G.to_undirected()

    if U.number_of_nodes() == 0:
        ok("No threads to check")
        print()
        return 0

    if not nx.is_connected(U):
        components = list(nx.connected_components(U))
        error(f"Graph is disconnected: {len(components)} components")
        for i, comp in enumerate(components):
            titles = sorted(path_to_title[n] for n in comp)
            info(f"  Component {i + 1}: {', '.join(titles)}")
        errors += 1
        print()
        return errors

    # Check all pairs for 3-hop reachability
    violations = []
    nodes = list(G.nodes())
    for i, source in enumerate(nodes):
        lengths = nx.single_source_shortest_path_length(U, source, cutoff=max_hops)
        for target in nodes:
            if target != source and target not in lengths:
                pair = tuple(sorted([path_to_title[source], path_to_title[target]]))
                if pair not in violations:
                    violations.append(pair)

    if violations:
        error(f"{len(violations)} pair(s) exceed {max_hops}-hop limit:")
        # Get actual distances for violations
        all_lengths = dict(nx.all_pairs_shortest_path_length(U))
        for a, b in violations:
            # Look up paths by title
            a_node = next(n for n, t in path_to_title.items() if t == a)
            b_node = next(n for n, t in path_to_title.items() if t == b)
            dist = all_lengths[a_node].get(b_node, "inf")
            warn(f"  {a} <-> {b} ({dist} hops)")
        errors += len(violations)
    else:
        ok(f"All pairs reachable within {max_hops} hops")
    print()
    return errors


def report_bridges(G: nx.DiGraph, path_to_title: dict[Path, str]) -> int:
    """Report single-bridge edges whose removal disconnects the graph."""
    print("-- Single-Bridge Detection --")
    errors = 0
    U = G.to_undirected()

    if U.number_of_nodes() < 2:
        ok("Too few threads for bridge detection")
        print()
        return 0

    bridges = list(nx.bridges(U))
    if bridges:
        warn(f"{len(bridges)} bridge edge(s) found (removal would disconnect the graph):")
        for u, v in bridges:
            warn(f"  {path_to_title[u]} <-> {path_to_title[v]}")
        errors += len(bridges)
    else:
        ok("No bridge edges — graph is 2-edge-connected")
    print()
    return errors


def compute_health(G: nx.DiGraph, path_to_title: dict[Path, str], max_hops: int = 3) -> dict:
    """Compute graph stats and a health score."""
    n_nodes = G.number_of_nodes()
    n_edges = G.number_of_edges()
    U = G.to_undirected()

    # Stats
    avg_degree = (2 * U.number_of_edges() / n_nodes) if n_nodes > 0 else 0
    components = nx.number_connected_components(U) if n_nodes > 0 else 0

    # Orphans (no inbound links)
    inbound_counts = defaultdict(int)
    for _, target in G.edges():
        inbound_counts[target] += 1
    orphans = [path_to_title[n] for n in G.nodes() if inbound_counts.get(n, 0) == 0]

    # Bridges
    bridges = list(nx.bridges(U)) if n_nodes >= 2 else []

    # 3-hop reachability
    hop_violations = 0
    if n_nodes > 0 and nx.is_connected(U):
        nodes = list(G.nodes())
        for source in nodes:
            lengths = nx.single_source_shortest_path_length(U, source, cutoff=max_hops)
            for target in nodes:
                if target != source and target not in lengths:
                    hop_violations += 1
        hop_violations //= 2  # each pair counted twice

    # Hub concentration — max fraction of total edges held by one node
    max_hub_fraction = 0.0
    if n_nodes > 0 and U.number_of_edges() > 0:
        max_degree = max(dict(U.degree()).values())
        max_hub_fraction = max_degree / U.number_of_edges()

    # Health score: 4 dimensions, each 0-100, weighted equally
    # Reachability: 100 if all pairs within max_hops, 0 if disconnected
    if n_nodes <= 1:
        reachability_score = 100
    elif components > 1:
        reachability_score = 0
    elif hop_violations == 0:
        reachability_score = 100
    else:
        total_pairs = n_nodes * (n_nodes - 1) // 2
        reachability_score = max(0, int(100 * (1 - hop_violations / total_pairs)))

    # Bridges: 100 if none, each bridge is a serious invariant violation
    if n_edges == 0:
        bridge_score = 100
    elif len(bridges) == 0:
        bridge_score = 100
    else:
        # Each bridge drops the score hard — these are structural fragilities
        bridge_score = max(0, 100 - (len(bridges) * 30))

    # Orphans: 100 if none, each orphan is an invariant violation
    if n_nodes == 0:
        orphan_score = 100
    elif len(orphans) == 0:
        orphan_score = 100
    else:
        # Each orphan drops the score hard — the constitution says nothing is orphaned
        orphan_score = max(0, 100 - (len(orphans) * 25))

    # Hub concentration: 100 if evenly distributed, lower if one node dominates
    if max_hub_fraction <= 0.5:
        hub_score = 100
    else:
        hub_score = max(0, int(100 * (1 - (max_hub_fraction - 0.5) / 0.5)))

    overall = (reachability_score + bridge_score + orphan_score + hub_score) // 4
    if overall >= 80:
        verdict = "HEALTHY"
    elif overall >= 50:
        verdict = "FAIR"
    else:
        verdict = "UNHEALTHY"

    return {
        "nodes": n_nodes,
        "edges": n_edges,
        "avg_degree": round(avg_degree, 1),
        "components": components,
        "orphans": orphans,
        "bridges": len(bridges),
        "hop_violations": hop_violations,
        "max_hub_fraction": round(max_hub_fraction, 2),
        "reachability_score": reachability_score,
        "bridge_score": bridge_score,
        "orphan_score": orphan_score,
        "hub_score": hub_score,
        "overall": overall,
        "verdict": verdict,
    }


def render_graph_image(
    G: nx.DiGraph, path_to_title: dict[Path, str], output_path: Path, health: dict | None = None
) -> None:
    """Render the thread graph as a PNG image with optional health overlay."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches

    print("-- Graph Visualization --")

    # Build a labeled graph for display
    labels = {node: title for node, title in path_to_title.items() if node in G}

    # Color by tier
    tier_colors = {"Active thread": "#4A90D9", "Reference thread": "#999999"}
    node_colors = [tier_colors.get(G.nodes[n].get("tier", ""), "#CCCCCC") for n in G.nodes()]

    fig, ax = plt.subplots(1, 1, figsize=(14, 9))
    fig.patch.set_facecolor("#1a1a2e")
    ax.set_facecolor("#1a1a2e")

    pos = nx.spring_layout(G, k=2.5, iterations=50, seed=42)

    # Draw edges
    nx.draw_networkx_edges(
        G, pos, ax=ax,
        edge_color="#555577",
        arrows=True,
        arrowsize=15,
        arrowstyle="-|>",
        connectionstyle="arc3,rad=0.1",
        width=1.5,
    )

    # Draw nodes
    nx.draw_networkx_nodes(
        G, pos, ax=ax,
        node_color=node_colors,
        node_size=800,
        edgecolors="#ffffff",
        linewidths=1.5,
    )

    # Draw labels
    nx.draw_networkx_labels(
        G, pos, labels=labels, ax=ax,
        font_size=8,
        font_color="#e0e0e0",
        font_weight="bold",
    )

    ax.set_title("Memex Thread Graph", color="#e0e0e0", fontsize=14, fontweight="bold", pad=20)

    # Legend
    from matplotlib.lines import Line2D

    legend_elements = [
        Line2D([0], [0], marker="o", color="#1a1a2e", markerfacecolor="#4A90D9",
               markersize=10, label="Active thread"),
        Line2D([0], [0], marker="o", color="#1a1a2e", markerfacecolor="#999999",
               markersize=10, label="Reference thread"),
    ]
    ax.legend(handles=legend_elements, loc="lower right", facecolor="#16213e",
              edgecolor="#555577", labelcolor="#e0e0e0")

    ax.axis("off")

    # Health overlay
    if health:
        verdict = health["verdict"]
        verdict_colors = {"HEALTHY": "#4CAF50", "FAIR": "#FFC107", "UNHEALTHY": "#F44336"}
        verdict_color = verdict_colors.get(verdict, "#e0e0e0")

        stats_text = (
            f"Health: {verdict}  ({health['overall']}/100)\n"
            f"\n"
            f"Nodes: {health['nodes']}    Edges: {health['edges']}    Avg degree: {health['avg_degree']}\n"
            f"Components: {health['components']}    Bridges: {health['bridges']}    Orphans: {len(health['orphans'])}\n"
            f"\n"
            f"Reachability: {health['reachability_score']}    "
            f"Resilience: {health['bridge_score']}    "
            f"Connectivity: {health['orphan_score']}    "
            f"Distribution: {health['hub_score']}"
        )

        # Draw stats panel in top-left
        props = dict(boxstyle="round,pad=0.8", facecolor="#16213e", edgecolor="#555577", alpha=0.95)
        text_obj = ax.text(
            0.02, 0.98, stats_text,
            transform=ax.transAxes,
            fontsize=9,
            fontfamily="monospace",
            color="#e0e0e0",
            verticalalignment="top",
            bbox=props,
        )

        # Color the verdict line
        ax.text(
            0.02, 0.98,
            f"Health: {verdict}",
            transform=ax.transAxes,
            fontsize=9,
            fontfamily="monospace",
            fontweight="bold",
            color=verdict_color,
            verticalalignment="top",
            bbox=dict(facecolor="none", edgecolor="none"),
        )

    plt.tight_layout()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(str(output_path), dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)

    ok(f"Graph image saved to {output_path}")
    print()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        default=Path(__file__).resolve().parents[1],
        type=Path,
    )
    parser.add_argument(
        "--image",
        default=None,
        type=Path,
        help="Output path for graph PNG (e.g., wiki/thread-graph.png)",
    )
    parser.add_argument(
        "--max-hops",
        default=3,
        type=int,
        help="Maximum hops for reachability check (default: 3)",
    )
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    memex_dir = repo_root / "memex"

    print("==============================")
    print("  Graph Health Report")
    print("==============================")
    print()

    G, path_to_title = build_graph(memex_dir)
    health = compute_health(G, path_to_title, max_hops=args.max_hops)

    info(f"Nodes: {health['nodes']}, Edges: {health['edges']}, Avg degree: {health['avg_degree']}")
    info(f"Components: {health['components']}, Bridges: {health['bridges']}, Orphans: {len(health['orphans'])}")
    print()

    errors = 0
    errors += report_backlinks(G, path_to_title)
    errors += report_reachability(G, path_to_title, max_hops=args.max_hops)
    errors += report_bridges(G, path_to_title)

    # Health score summary
    print("-- Health Score --")
    verdict_color = GREEN if health["verdict"] == "HEALTHY" else (YELLOW if health["verdict"] == "FAIR" else RED)
    print(f"{verdict_color}{health['verdict']}{NC}  ({health['overall']}/100)")
    info(f"Reachability: {health['reachability_score']}  Resilience: {health['bridge_score']}  Connectivity: {health['orphan_score']}  Distribution: {health['hub_score']}")
    print()

    if args.image:
        image_path = args.image
        if not image_path.is_absolute():
            image_path = repo_root / image_path
        render_graph_image(G, path_to_title, image_path, health=health)

    print("==============================")
    if errors == 0:
        print(f"{GREEN}All graph-health checks passed.{NC}")
    else:
        print(f"{RED}{errors} issue(s) found.{NC}")
    print("==============================")

    return min(errors, 1)


if __name__ == "__main__":
    raise SystemExit(main())
