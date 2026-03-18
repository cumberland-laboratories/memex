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


def report_backlinks(G: nx.DiGraph, path_to_title: dict[Path, str]) -> None:
    """Report inbound links for each thread."""
    print("-- Backlink Index --")
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
            warn(f"{title} <- (no inbound links)")
    print()


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


def render_graph_image(G: nx.DiGraph, path_to_title: dict[Path, str], output_path: Path) -> None:
    """Render the thread graph as a PNG image."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    print("-- Graph Visualization --")

    # Build a labeled graph for display
    labels = {node: title for node, title in path_to_title.items() if node in G}

    # Color by tier
    tier_colors = {"Active thread": "#4A90D9", "Reference thread": "#999999"}
    node_colors = [tier_colors.get(G.nodes[n].get("tier", ""), "#CCCCCC") for n in G.nodes()]

    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
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
    info(f"Nodes: {G.number_of_nodes()}, Edges: {G.number_of_edges()}")
    print()

    errors = 0
    report_backlinks(G, path_to_title)
    errors += report_reachability(G, path_to_title, max_hops=args.max_hops)
    errors += report_bridges(G, path_to_title)

    if args.image:
        image_path = args.image
        if not image_path.is_absolute():
            image_path = repo_root / image_path
        render_graph_image(G, path_to_title, image_path)

    print("==============================")
    if errors == 0:
        print(f"{GREEN}All graph-health checks passed.{NC}")
    else:
        print(f"{RED}{errors} issue(s) found.{NC}")
    print("==============================")

    return min(errors, 1)


if __name__ == "__main__":
    raise SystemExit(main())
