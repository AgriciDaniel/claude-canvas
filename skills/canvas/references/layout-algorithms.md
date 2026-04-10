# Layout Algorithms Reference

Six algorithms for re-arranging canvas nodes. Each is optimized for a different canvas archetype.

Run via: `python3 scripts/canvas_layout.py <canvas> <algorithm> [options]`

---

## Algorithm Selection Guide

| Algorithm | Best For | Edge Behavior | Parameters |
|-----------|----------|---------------|------------|
| **grid** | Galleries, mood boards, comparisons | Ignores edges | `--columns N`, `--sort-by type\|size` |
| **dagre** | Flowcharts, org charts, processes | Follows edge direction | `--direction TB\|LR\|BT\|RL` |
| **radial** | Mind maps, concept maps, topic exploration | Builds rings from center | `--center node-id` |
| **force** | Knowledge graphs, entity relationships | Attracts connected, repels unconnected | `--iterations N` |
| **linear** | Timelines, sequences, step-by-step | Ignores edges | `--axis horizontal\|vertical` |
| **auto** | When unsure | Analyzes content + edges | (none — auto-detects) |

---

## Auto-Detection Heuristics

The `auto` algorithm inspects content and edges to pick the best layout:

1. **>60% file nodes + few edges** → `grid` (gallery/mood board pattern)
2. **Zero edges** → `grid` (no relationship data to layout)
3. **One node has >40% of all connections** → `radial` (hub-and-spoke)
4. **Clear hierarchy (pure source nodes) + edges** → `dagre` (flowchart)
5. **Dense edges (>1 edge per node)** → `force` (network graph)
6. **Fallback** → `dagre` (most versatile structured layout)

---

## Grid Layout

Arranges nodes in rows and columns. Nodes are centered within uniform cells.

**Auto-columns**: `ceil(sqrt(node_count))`, clamped to 2-6.

**Cell sizing**: Uses the maximum node width + 60px gap horizontally, maximum height + 40px gap vertically. Each node is centered within its cell.

**Sort options**:
- `type` (default): Groups by node type (text → file → link)
- `size`: Largest nodes first (Pinterest masonry feel)

```
┌──────┐  ┌──────┐  ┌──────┐
│  A   │  │  B   │  │  C   │
└──────┘  └──────┘  └──────┘
┌──────┐  ┌──────┐  ┌──────┐
│  D   │  │  E   │  │  F   │
└──────┘  └──────┘  └──────┘
```

---

## Dagre Layout (Hierarchical / Sugiyama)

Assigns nodes to layers based on edge direction, then positions within layers.

**Layer assignment**: BFS from root nodes (nodes with no incoming edges). Each edge increases the layer by 1.

**Directions**:
- `TB` (default): Top to bottom — classic flowchart
- `LR`: Left to right — process flow
- `BT`: Bottom to top — org chart (inverted)
- `RL`: Right to left — reverse flow

**Within-layer positioning**: Nodes in the same layer are evenly spaced perpendicular to the flow direction. Centering reduces edge crossings.

```
TB direction:              LR direction:
    ┌───┐                  ┌───┐
    │ A │                  │ A │──→ ┌───┐
    └─┬─┘                  └───┘    │ C │
  ┌───┴───┐                ┌───┐    └───┘
┌─┴─┐  ┌──┴─┐             │ B │──→ ┌───┐
│ B │  │ C  │              └───┘    │ D │
└───┘  └────┘                       └───┘
```

---

## Radial Layout

Expands outward from a center node in concentric rings.

**Center selection**: Node with the most connections (edges). Override with `--center node-id`.

**Ring assignment**: BFS from center. Ring 0 = center, Ring 1 = direct neighbors, etc.

**Positioning**: Each ring has radius = 300px × ring_number. Nodes are evenly distributed around the ring using angle_step = 2π / node_count.

```
         ○ C
        ╱
   ○ B ─── ● Center ─── ○ D
        ╲
         ○ E
```

---

## Force-Directed Layout (Fruchterman-Reingold)

Physics simulation: connected nodes attract, all nodes repel. Iterates until stable.

**Forces**:
- Repulsive (all pairs): `k² / distance` — pushes nodes apart
- Attractive (edges only): `distance² / k` — pulls connected nodes together
- k = `sqrt(area / node_count)` — optimal spacing

**Temperature**: Starts high (allows large movements), cools by 5% per iteration. At 100 iterations, the layout is typically stable.

**Performance**: O(n²) per iteration. For >50 nodes, consider reducing iterations to 50.

```
    ○──────○
   ╱ ╲    ╱
  ○   ○──○
   ╲ ╱
    ○
```

---

## Linear Layout (Timeline)

Places nodes in a single line along one axis.

**Horizontal** (default): Left to right, centered vertically. Good for timelines.
**Vertical**: Top to bottom, centered horizontally. Good for step sequences.

**Ordering**: Preserves current position order on the layout axis. Nodes are sorted by their current x (horizontal) or y (vertical) coordinate before placement.

**Spacing**: Node width/height + 60px horizontal gap or 40px vertical gap.

```
Horizontal:  ┌──┐  ┌──┐  ┌──┐  ┌──┐
             │A │──│B │──│C │──│D │
             └──┘  └──┘  └──┘  └──┘

Vertical:    ┌──┐
             │A │
             └──┘
             ┌──┐
             │B │
             └──┘
             ┌──┐
             │C │
             └──┘
```

---

## Group Preservation

All algorithms preserve group (zone) membership:

1. Before layout: record which content nodes are inside which groups
2. During layout: only content nodes are repositioned
3. After layout: groups are **refitted** to tightly wrap their member nodes with 20px padding (plus 40px top for the label)

Groups that had no members remain at their original position.

---

## Common Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--dry-run` | false | Calculate layout without writing changes |
| `--columns` | auto | Grid columns (grid only) |
| `--direction` | TB | Flow direction (dagre only) |
| `--center` | auto | Center node ID (radial only) |
| `--axis` | horizontal | Layout axis (linear only) |
| `--iterations` | 100 | Simulation steps (force only) |
| `--sort-by` | type | Sort order (grid only) |

All outputs are JSON:

```json
{
  "success": true,
  "algorithm": "dagre",
  "auto_detected": false,
  "nodes_moved": 12,
  "total_nodes": 15,
  "groups_preserved": 3,
  "backup": "canvas.canvas.bak",
  "dry_run": false
}
```

| Field | Type | Description |
|-------|------|-------------|
| `success` | bool | Whether the layout completed without errors |
| `algorithm` | string | The algorithm that was actually applied |
| `auto_detected` | bool | Whether `auto` was used and this algorithm was chosen |
| `nodes_moved` | int | Number of content nodes that changed position |
| `total_nodes` | int | Total content nodes (excludes groups) |
| `groups_preserved` | int | Number of groups that were refitted |
| `backup` | string/null | Path to backup file (null if dry-run) |
| `dry_run` | bool | Whether changes were actually written |
