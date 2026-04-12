#!/usr/bin/env python3
"""Graph-health analysis for the Memex thread graph.

Reports:
  - Backlink index (who links to each thread)
  - 3-hop reachability violations
  - Single-bridge edges (removal disconnects the graph)
  - Graph visualization (PNG)

Usage:
  python .memex/scripts/graph_health.py
  python .memex/scripts/graph_health.py --image docs/wiki/thread-graph.png
"""

from __future__ import annotations

import argparse
import io
import datetime as dt
import json
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


def build_graph(memex_dir: Path, graph_filter: str | None = None) -> tuple[nx.DiGraph, dict[Path, str]]:
    """Build a directed graph from thread cross-references.

    If graph_filter is set, only include threads whose `graph:` frontmatter
    matches the filter. Cross-graph links to excluded threads are dropped.
    If graph_filter is None, all threads are included (whole-graph analysis).
    """
    threads = load_threads(memex_dir)

    # Build path-to-graph mapping for all threads
    path_to_graph: dict[Path, str] = {}
    for thread in threads:
        resolved = thread.source_path.resolve()
        path_to_graph[resolved] = thread.graph

    # Filter threads if requested
    if graph_filter is not None:
        threads = [t for t in threads if t.graph == graph_filter]

    G = nx.DiGraph()
    path_to_title: dict[Path, str] = {}

    for thread in threads:
        resolved = thread.source_path.resolve()
        path_to_title[resolved] = thread.title
        G.add_node(resolved, title=thread.title, tier=thread.tier_label,
                   graph=thread.graph)

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


def report_reachability(G: nx.DiGraph, path_to_title: dict[Path, str], health: dict, max_hops: int = 3) -> int:
    """Report reachability, split into intra-cluster (errors) and cross-cluster (info)."""
    print(f"-- {max_hops}-Hop Navigability (cluster-aware) --")
    errors = 0

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

    intra = health.get("intra_hop_violations", [])
    cross = health.get("cross_hop_violations", [])

    if intra:
        error(f"{len(intra)} intra-cluster pair(s) exceed {max_hops}-hop limit:")
        for v in intra:
            warn(f"  {v['a']} <-> {v['b']} ({v['hops']} hops)")
        errors += len(intra)
    else:
        ok(f"All intra-cluster pairs reachable within {max_hops} hops")

    if cross:
        info(f"{len(cross)} cross-cluster pair(s) exceed {max_hops} hops (penalized at 0.25x weight):")
        for v in cross[:10]:
            info(f"  {v['a']} <-> {v['b']} ({v['hops']} hops)")
        if len(cross) > 10:
            info(f"  ... and {len(cross) - 10} more")
    else:
        ok(f"All cross-cluster pairs also within {max_hops} hops")

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


def report_clusters(health: dict) -> None:
    """Report detected clusters."""
    print("-- Cluster Detection (Louvain) --")
    clusters = health.get("cluster_summary", [])
    if not clusters:
        info("No clusters detected")
        print()
        return
    info(f"{len(clusters)} cluster(s) detected")
    for c in clusters:
        print(f"  Cluster {c['id'] + 1} ({c['size']} nodes):")
        for name in c["members"]:
            print(f"    - {name}")
    print()


def report_efficiency(health: dict) -> int:
    """Report edge redundancy / efficiency."""
    print("-- Edge Efficiency --")
    errors = 0
    ratio = health.get("redundancy_ratio", 0)
    redundant = health.get("redundant_edges", 0)
    total = health.get("total_undirected_edges", 0)

    if total == 0:
        ok("No edges to evaluate")
        print()
        return 0

    # Finding 4 fix: report branches must match scoring branches
    if ratio < 0.30:
        warn(f"{redundant}/{total} edges redundant ({ratio:.0%}) — too sparse, fragile tree structure")
        errors += 1
    elif ratio <= 0.60:
        ok(f"{redundant}/{total} edges redundant ({ratio:.0%}) — within sweet spot")
    else:
        warn(f"{redundant}/{total} edges redundant ({ratio:.0%}) — over-linked, {redundant - int(total * 0.60)} edges are noise")
        errors += 1
    info(f"Sweet spot: 30-60% redundancy. Below 30% = fragile tree. Above 60% = noisy.")
    print()
    return errors


def report_legibility(health: dict) -> int:
    """Report peripheral node access to high-betweenness hubs."""
    print("-- Legibility (peripheral access to hubs) --")
    errors = 0
    peripherals = health.get("peripherals", 0)
    stranded = health.get("peripherals_stranded", [])
    hubs = health.get("hubs", [])

    if peripherals == 0:
        ok("No peripheral nodes (degree <= 3)")
        print()
        return 0

    info(f"Hubs (top 20% betweenness): {', '.join(hubs)}")
    reached = peripherals - len(stranded)
    if stranded:
        warn(f"{reached}/{peripherals} peripheral nodes reach a hub within 2 hops")
        for name in stranded:
            warn(f"  Stranded: {name}")
        errors += len(stranded)
    else:
        ok(f"All {peripherals} peripheral nodes reach a hub within 2 hops")
    print()
    return errors


def detect_clusters(U: nx.Graph, path_to_title: dict[Path, str]) -> list[set]:
    """Detect natural clusters using Louvain community detection."""
    if U.number_of_nodes() == 0:
        return []
    try:
        from networkx.algorithms.community import louvain_communities
        return list(louvain_communities(U, seed=42))
    except ImportError:
        # Fallback: treat entire graph as one cluster
        return [set(U.nodes())]


def compute_redundancy(U: nx.Graph) -> tuple[int, int]:
    """Count redundant edges (endpoints within 2 hops even without the edge).

    Returns (redundant_count, total_undirected_edges).
    """
    redundant = 0
    total = U.number_of_edges()
    for u, v in list(U.edges()):
        H = U.copy()
        H.remove_edge(u, v)
        if nx.has_path(H, u, v) and nx.shortest_path_length(H, u, v) <= 2:
            redundant += 1
    return redundant, total


def compute_health(G: nx.DiGraph, path_to_title: dict[Path, str], max_hops: int = 3) -> dict:
    """Compute graph stats and a health score.

    Model v2.1 — subway-informed, cluster-aware (post Codex review):
      - Navigability: intra-cluster 3-hop (full weight) + cross-cluster (0.25 weight)
      - Resilience: bridge edges (unchanged)
      - Connectivity: intra-cluster orphans (20 pts) + global-only orphans (10 pts)
      - Efficiency: edge redundancy ratio (sweet spot 30-60%)
      - Legibility: peripheral nodes' access to high-betweenness hubs
    """
    n_nodes = G.number_of_nodes()
    n_edges = G.number_of_edges()
    U = G.to_undirected()

    # Basic stats
    avg_degree = (2 * U.number_of_edges() / n_nodes) if n_nodes > 0 else 0
    components = nx.number_connected_components(U) if n_nodes > 0 else 0

    # Cluster detection
    clusters = detect_clusters(U, path_to_title)
    n_clusters = len(clusters)
    node_to_cluster: dict[Path, int] = {}
    for i, comm in enumerate(clusters):
        for n in comm:
            node_to_cluster[n] = i
    cluster_summary = []
    for i, comm in enumerate(clusters):
        names = sorted(path_to_title.get(n, "?") for n in comm)
        cluster_summary.append({"id": i, "size": len(comm), "members": names})

    # Bridges
    bridges = list(nx.bridges(U)) if n_nodes >= 2 else []

    # --- NAVIGABILITY: cluster-aware 3-hop reachability ---
    # Finding 5 fix: compute all-pairs distances once, outside the loop
    intra_violations = []
    cross_violations = []
    all_distances: dict[Path, dict[Path, int]] = {}
    if n_nodes > 0 and nx.is_connected(U):
        all_distances = dict(nx.all_pairs_shortest_path_length(U))
        nodes = list(G.nodes())
        seen_pairs = set()
        for source in nodes:
            lengths = nx.single_source_shortest_path_length(U, source, cutoff=max_hops)
            for target in nodes:
                if target != source and target not in lengths:
                    pair = tuple(sorted([source, target], key=lambda n: path_to_title.get(n, "")))
                    if pair not in seen_pairs:
                        seen_pairs.add(pair)
                        actual_dist = all_distances[source].get(target, float("inf"))
                        entry = {
                            "a": path_to_title[pair[0]],
                            "b": path_to_title[pair[1]],
                            "hops": actual_dist,
                        }
                        if node_to_cluster.get(source) == node_to_cluster.get(target):
                            intra_violations.append(entry)
                        else:
                            cross_violations.append(entry)

    # --- CONNECTIVITY: per-cluster orphan detection ---
    inbound_counts = defaultdict(int)
    for _, target in G.edges():
        inbound_counts[target] += 1
    # Global orphans (no inbound from anywhere)
    global_orphans = [path_to_title[n] for n in G.nodes() if inbound_counts.get(n, 0) == 0]
    # Intra-cluster orphans (no inbound from within own cluster)
    intra_cluster_orphans = []
    for node in G.nodes():
        cluster_id = node_to_cluster.get(node)
        cluster_members = clusters[cluster_id] if cluster_id is not None else set()
        has_intra_inbound = False
        for source, target in G.edges():
            if target == node and source in cluster_members and source != node:
                has_intra_inbound = True
                break
        if not has_intra_inbound:
            intra_cluster_orphans.append(path_to_title[node])

    # --- EFFICIENCY: edge redundancy ratio ---
    redundant_count, total_undirected = compute_redundancy(U)
    redundancy_ratio = (redundant_count / total_undirected) if total_undirected > 0 else 0.0

    # --- LEGIBILITY: peripheral access to hubs ---
    # Peripheral = degree <= 3. Hub = top 20% by betweenness centrality.
    # Score: fraction of peripherals that reach a hub within 2 hops.
    bc = nx.betweenness_centrality(U) if n_nodes > 0 else {}
    if bc:
        bc_threshold = sorted(bc.values(), reverse=True)[max(0, n_nodes // 5 - 1)] if n_nodes >= 5 else 0
        hubs = {n for n, v in bc.items() if v >= bc_threshold and v > 0}
    else:
        hubs = set()
    # If no nodes have positive betweenness (e.g., complete graphs where all paths
    # are length 1), fall back to top 20% by degree. A fully connected graph has no
    # stranded peripherals — legibility should be 100, not 0.
    if not hubs and n_nodes > 0:
        degree_sorted = sorted(U.degree(), key=lambda x: -x[1])
        top_count = max(1, n_nodes // 5)
        hubs = {n for n, _ in degree_sorted[:top_count]}
    peripherals = [n for n in U.nodes() if U.degree(n) <= 3]
    peripherals_with_hub_access = 0
    peripherals_stranded = []
    for p in peripherals:
        lengths = nx.single_source_shortest_path_length(U, p, cutoff=2)
        if any(h in lengths for h in hubs):
            peripherals_with_hub_access += 1
        else:
            peripherals_stranded.append(path_to_title[p])

    # ===== SCORING =====

    # Navigability (Finding 1 fix: soft cross-cluster penalty, not zero-cost)
    # Intra-cluster violations are full-weight errors (break local navigation).
    # Cross-cluster violations get a soft penalty: each one costs 1/4 what an intra-cluster
    # violation costs. This prevents cluster growth from hiding long paths for free.
    if n_nodes <= 1:
        navigability_score = 100
    elif components > 1:
        navigability_score = 0
    else:
        total_pairs = n_nodes * (n_nodes - 1) // 2
        # Weighted violation count: intra = 1.0, cross = 0.25
        weighted_violations = len(intra_violations) + len(cross_violations) * 0.25
        navigability_score = max(0, int(100 * (1 - weighted_violations / max(total_pairs, 1))))

    # Resilience: bridges (unchanged)
    if n_edges == 0:
        resilience_score = 100
    elif len(bridges) == 0:
        resilience_score = 100
    else:
        resilience_score = max(0, 100 - (len(bridges) * 30))

    # Connectivity: per-cluster orphans (Finding 2 fix: use intra_cluster_orphans, not global)
    # A thread with no inbound links from within its own cluster is disconnected from its
    # neighborhood, even if some cross-cluster thread links to it. Both are problems, but
    # intra-cluster orphans are weighted heavier (they break local navigability).
    if n_nodes == 0:
        connectivity_score = 100
    else:
        # Intra-cluster orphans: 20 points each (breaks local navigation)
        # Global orphans that aren't intra-cluster orphans: 10 points each (less severe)
        intra_only = set(intra_cluster_orphans)
        global_only = [o for o in global_orphans if o not in intra_only]
        penalty = len(intra_cluster_orphans) * 20 + len(global_only) * 10
        connectivity_score = max(0, 100 - penalty)

    # Efficiency: sweet spot is 30-60% redundancy
    # Below 30% = fragile (tree-like). Above 70% = noisy (over-linked).
    # 100 at 30-60%, drops linearly outside that band.
    if total_undirected == 0:
        efficiency_score = 100
    elif redundancy_ratio < 0.30:
        # Too sparse — fragile
        efficiency_score = max(0, int(100 * (redundancy_ratio / 0.30)))
    elif redundancy_ratio <= 0.60:
        # Sweet spot
        efficiency_score = 100
    else:
        # Over-linked — noisy. 100% redundancy = 0 score.
        efficiency_score = max(0, int(100 * (1 - (redundancy_ratio - 0.60) / 0.40)))

    # Legibility: peripheral access to hubs
    if len(peripherals) == 0:
        legibility_score = 100
    else:
        legibility_score = int(100 * peripherals_with_hub_access / len(peripherals))

    # Overall: 5 dimensions, equal weight
    overall = (navigability_score + resilience_score + connectivity_score
               + efficiency_score + legibility_score) // 5
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
        "clusters": n_clusters,
        "cluster_summary": cluster_summary,
        "orphans": global_orphans,
        "intra_cluster_orphans": intra_cluster_orphans,
        "bridges": len(bridges),
        "intra_hop_violations": intra_violations,
        "cross_hop_violations": cross_violations,
        "redundancy_ratio": round(redundancy_ratio, 2),
        "redundant_edges": redundant_count,
        "total_undirected_edges": total_undirected,
        "peripherals": len(peripherals),
        "peripherals_stranded": peripherals_stranded,
        "hubs": sorted(path_to_title.get(h, "?") for h in hubs),
        "navigability_score": navigability_score,
        "resilience_score": resilience_score,
        "connectivity_score": connectivity_score,
        "efficiency_score": efficiency_score,
        "legibility_score": legibility_score,
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

    BG = "#f0f0f0"
    TEXT_COLOR = "#222222"
    PANEL_BG = "#ffffff"
    PANEL_EDGE = "#cccccc"
    EDGE_COLOR = "#8888aa"

    # Color by cluster (from health data) with tier as shape indicator via edge style
    CLUSTER_PALETTE = ["#4A90D9", "#E07B39", "#5BA55B", "#C75B8F", "#8B6FBF", "#C4A132", "#49B6A6"]
    node_to_cluster_map: dict[Path, int] = {}
    if health and "cluster_summary" in health:
        clusters = detect_clusters(G.to_undirected(), path_to_title)
        for i, comm in enumerate(clusters):
            for n in comm:
                node_to_cluster_map[n] = i
    node_colors = [CLUSTER_PALETTE[node_to_cluster_map.get(n, 0) % len(CLUSTER_PALETTE)] for n in G.nodes()]
    # Reference threads get a lighter alpha via edge ring
    node_edge_colors = []
    for n in G.nodes():
        tier = G.nodes[n].get("tier", "")
        if tier == "Reference thread":
            node_edge_colors.append("#888888")
        else:
            node_edge_colors.append("#ffffff")

    # Use gridspec: graph on top, stats panel below
    if health:
        fig = plt.figure(figsize=(14, 11))
        gs = fig.add_gridspec(2, 1, height_ratios=[4, 1], hspace=0.05)
        ax = fig.add_subplot(gs[0])
        ax_stats = fig.add_subplot(gs[1])
    else:
        fig, ax = plt.subplots(1, 1, figsize=(14, 9))
        ax_stats = None

    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)

    pos = nx.spring_layout(G, k=2.5, iterations=50, seed=42)

    # Draw edges
    nx.draw_networkx_edges(
        G, pos, ax=ax,
        edge_color=EDGE_COLOR,
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
        edgecolors=node_edge_colors,
        linewidths=2.0,
    )

    # Draw labels
    nx.draw_networkx_labels(
        G, pos, labels=labels, ax=ax,
        font_size=9,
        font_color=TEXT_COLOR,
        font_weight="bold",
    )

    ax.set_title("Memex Thread Graph", color=TEXT_COLOR, fontsize=14, fontweight="bold", pad=20)

    # Legend — clusters + tier indicators
    from matplotlib.lines import Line2D

    legend_elements = []
    if health and "cluster_summary" in health:
        for c in health["cluster_summary"]:
            color = CLUSTER_PALETTE[c["id"] % len(CLUSTER_PALETTE)]
            legend_elements.append(
                Line2D([0], [0], marker="o", color=BG, markerfacecolor=color,
                       markersize=10, label=f"Cluster {c['id'] + 1} ({c['size']} nodes)")
            )
    legend_elements.append(
        Line2D([0], [0], marker="o", color=BG, markerfacecolor="#CCCCCC",
               markeredgecolor="#888888", markeredgewidth=2,
               markersize=10, label="Reference thread (gray ring)")
    )
    ax.legend(handles=legend_elements, loc="lower right", facecolor=PANEL_BG,
              edgecolor=PANEL_EDGE, labelcolor=TEXT_COLOR, fontsize=8)

    ax.axis("off")

    # Health stats panel below graph
    if health and ax_stats is not None:
        ax_stats.set_facecolor(BG)
        ax_stats.axis("off")

        verdict = health["verdict"]
        verdict_colors = {"HEALTHY": "#2E7D32", "FAIR": "#F57F17", "UNHEALTHY": "#C62828"}
        verdict_color = verdict_colors.get(verdict, TEXT_COLOR)

        stats_lines = (
            f"Nodes: {health['nodes']}    Edges: {health['edges']}    Avg degree: {health['avg_degree']}    Clusters: {health['clusters']}\n"
            f"Components: {health['components']}    Bridges: {health['bridges']}    Orphans: {len(health['orphans'])}    Redundancy: {health['redundancy_ratio']:.0%}\n"
            f"\n"
            f"Navigability: {health['navigability_score']}    "
            f"Resilience: {health['resilience_score']}    "
            f"Connectivity: {health['connectivity_score']}    "
            f"Efficiency: {health['efficiency_score']}    "
            f"Legibility: {health['legibility_score']}"
        )

        props = dict(boxstyle="round,pad=0.8", facecolor=PANEL_BG, edgecolor=PANEL_EDGE, alpha=0.95)

        # Verdict line (colored, bold)
        ax_stats.text(
            0.5, 0.82,
            f"Health: {verdict}  ({health['overall']}/100)",
            transform=ax_stats.transAxes,
            fontsize=12,
            fontfamily="monospace",
            fontweight="bold",
            color=verdict_color,
            verticalalignment="center",
            horizontalalignment="center",
        )

        # Stats below verdict
        ax_stats.text(
            0.5, 0.35, stats_lines,
            transform=ax_stats.transAxes,
            fontsize=10,
            fontfamily="monospace",
            color=TEXT_COLOR,
            verticalalignment="center",
            horizontalalignment="center",
            bbox=props,
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
        default=Path(__file__).resolve().parents[2],
        type=Path,
    )
    parser.add_argument(
        "--image",
        default=None,
        type=Path,
        help="Output path for graph PNG (e.g., docs/wiki/thread-graph.png)",
    )
    parser.add_argument(
        "--json",
        default=None,
        type=Path,
        help="Output path for health JSON (e.g., docs/wiki/graph-health.json)",
    )
    parser.add_argument(
        "--max-hops",
        default=3,
        type=int,
        help="Maximum hops for reachability check (default: 3)",
    )
    parser.add_argument(
        "--graph",
        default=None,
        type=str,
        help="Filter by graph namespace (e.g., 'design', 'user'). Default: all threads.",
    )
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    memex_dir = repo_root / "memex"

    # Ensure UTF-8 output on Windows
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    graph_label = f" ({args.graph} layer)" if args.graph else ""
    print("==============================")
    print(f"  Graph Health Report{graph_label}")
    print("==============================")
    print()

    G, path_to_title = build_graph(memex_dir, graph_filter=args.graph)

    # Validate --graph filter: fail on empty result from a non-None filter
    if args.graph is not None and G.number_of_nodes() == 0:
        # Check if the graph name exists at all
        all_threads = load_threads(memex_dir)
        known_graphs = sorted(set(t.graph for t in all_threads))
        error(f"No threads found with graph: {args.graph}")
        info(f"Known graph values: {', '.join(known_graphs)}")
        return 1

    health = compute_health(G, path_to_title, max_hops=args.max_hops)

    info(f"Nodes: {health['nodes']}, Edges: {health['edges']}, Avg degree: {health['avg_degree']}")
    info(f"Components: {health['components']}, Clusters: {health['clusters']}, Bridges: {health['bridges']}, Orphans: {len(health['orphans'])}")
    print()

    errors = 0
    report_clusters(health)
    errors += report_backlinks(G, path_to_title)
    errors += report_reachability(G, path_to_title, health, max_hops=args.max_hops)
    errors += report_bridges(G, path_to_title)
    errors += report_efficiency(health)
    errors += report_legibility(health)

    # Health score summary
    print("-- Health Score (v2 — subway model) --")
    verdict_color = GREEN if health["verdict"] == "HEALTHY" else (YELLOW if health["verdict"] == "FAIR" else RED)
    print(f"{verdict_color}{health['verdict']}{NC}  ({health['overall']}/100)")
    info(f"Navigability: {health['navigability_score']}  Resilience: {health['resilience_score']}  Connectivity: {health['connectivity_score']}  Efficiency: {health['efficiency_score']}  Legibility: {health['legibility_score']}")
    print()

    if args.image:
        image_path = args.image
        if not image_path.is_absolute():
            image_path = repo_root / image_path
        render_graph_image(G, path_to_title, image_path, health=health)

    if args.json:
        json_path = args.json
        if not json_path.is_absolute():
            json_path = repo_root / json_path
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_data = {
            "date": dt.date.today().isoformat(),
            "model": "v2.1-subway",
            "verdict": health["verdict"],
            "overall": health["overall"],
            "nodes": health["nodes"],
            "edges": health["edges"],
            "avg_degree": health["avg_degree"],
            "components": health["components"],
            "clusters": health["clusters"],
            "cluster_summary": health["cluster_summary"],
            "bridges": health["bridges"],
            "orphans": health["orphans"],
            "intra_cluster_orphans": health["intra_cluster_orphans"],
            "intra_hop_violations": len(health["intra_hop_violations"]),
            "cross_hop_violations": len(health["cross_hop_violations"]),
            "redundancy_ratio": health["redundancy_ratio"],
            "redundant_edges": health["redundant_edges"],
            "total_undirected_edges": health["total_undirected_edges"],
            "peripherals": health["peripherals"],
            "peripherals_stranded": health["peripherals_stranded"],
            "hubs": health["hubs"],
            "scores": {
                "navigability": health["navigability_score"],
                "resilience": health["resilience_score"],
                "connectivity": health["connectivity_score"],
                "efficiency": health["efficiency_score"],
                "legibility": health["legibility_score"],
            },
        }
        json_path.write_text(json.dumps(json_data, indent=2) + "\n", encoding="utf-8")
        ok(f"Health JSON saved to {json_path}")
        print()

    print("==============================")
    if errors == 0:
        print(f"{GREEN}All graph-health checks passed.{NC}")
    else:
        print(f"{RED}{errors} issue(s) found.{NC}")
    print("==============================")

    return min(errors, 1)


if __name__ == "__main__":
    raise SystemExit(main())
