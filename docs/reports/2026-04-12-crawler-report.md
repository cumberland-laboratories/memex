# Crawler Report — 2026-04-12

Model: v2.1-subway
Verdict: **UNHEALTHY** (45/100)

| Dimension | Score |
|-----------|-------|
| Navigability | 0 |
| Resilience | 0 |
| Connectivity | 60 |
| Efficiency | 76 |
| Legibility | 90 |

Nodes: 12  Edges: 19  Clusters: 4  Redundancy: 23%

## Findings (4)

### 1. Navigability — RED

Score: 0/100
Detail: 0 intra-cluster + 0 cross-cluster violations
Action: Propose transfer station links for intra-cluster violations (worst first)

### 2. Resilience — RED

Score: 0/100
Detail: 5 bridge edge(s)
Action: Propose redundant paths for all bridge edges (urgent)

### 3. Connectivity — YELLOW

Score: 60/100
Detail: 2 intra-cluster orphan(s), 1 global orphan(s)
Action: Report intra-cluster orphans; suggest cluster neighbor inbound links
Orphans: Session Continuity Without Memory, Session Handoff — Public Release Prep

### 4. Efficiency — YELLOW

Score: 76/100
Detail: Redundancy ratio 23% (<30%)
Action: Flag fragile tree structure; suggest adding redundant paths
