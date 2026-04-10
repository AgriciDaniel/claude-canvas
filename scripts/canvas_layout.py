#!/usr/bin/env python3
"""canvas_layout.py — Re-layout Obsidian Canvas nodes using spatial algorithms.

Supports 6 layout algorithms:
  - dagre:  Hierarchical/Sugiyama layout (top-down or left-right flow)
  - grid:   Grid/masonry layout (rows and columns)
  - radial: Radial/circular layout (center-out expansion)
  - force:  Force-directed spring layout (knowledge graphs)
  - linear: Linear timeline layout (horizontal or vertical)
  - auto:   Auto-detect best algorithm from canvas content

Usage:
    python3 canvas_layout.py <canvas_path> <algorithm> [options]
    python3 canvas_layout.py input.canvas grid --columns 4
    python3 canvas_layout.py input.canvas dagre --direction LR
    python3 canvas_layout.py input.canvas radial --center node-id
    python3 canvas_layout.py input.canvas auto
    python3 canvas_layout.py input.canvas grid --dry-run

Output (JSON):
    {
        "success": true,
        "algorithm": "grid",
        "nodes_moved": 12,
        "groups_preserved": 3,
        "backup": "input.canvas.bak"
    }

Exit codes:
    0 = success
    1 = error (invalid input, algorithm failure)
    2 = file not found
"""

import argparse
import json
import math
import sys
from copy import deepcopy
from pathlib import Path

GRID = 20
H_GAP = 100  # horizontal gap between nodes (80px min + 20px margin)
V_GAP = 80   # vertical gap between nodes (60px min + 20px margin)
GROUP_PAD = 40  # padding inside groups


def snap(value):
    """Snap a value to the nearest grid increment."""
    return round(value / GRID) * GRID


def get_center(node):
    """Get the center point of a node."""
    return (
        node["x"] + node["width"] / 2,
        node["y"] + node["height"] / 2,
    )


def separate_groups_and_content(nodes):
    """Split nodes into groups (zones) and content nodes."""
    groups = [n for n in nodes if n.get("type") == "group"]
    content = [n for n in nodes if n.get("type") != "group"]
    return groups, content


def find_group_membership(groups, content):
    """Map each content node to the group it's inside (if any).

    Uses node center point for containment (matches Obsidian behavior).
    """
    membership = {}
    for node in content:
        # Use center point for containment check (Obsidian uses center)
        ncx = node["x"] + node["width"] / 2
        ncy = node["y"] + node["height"] / 2
        for group in groups:
            gx, gy = group["x"], group["y"]
            gw, gh = group["width"], group["height"]
            if gx <= ncx <= gx + gw and gy <= ncy <= gy + gh:
                membership[node["id"]] = group["id"]
                break
    return membership


# ─────────────────────────────────────────────
# Algorithm: GRID
# ─────────────────────────────────────────────

def layout_grid(content, columns=None, sort_by="type"):
    """Arrange content nodes in a grid pattern.

    Good for: galleries, mood boards, comparison matrices.
    """
    if not content:
        return content

    # Auto-detect columns from node count
    if columns is None:
        n = len(content)
        columns = max(2, min(6, math.ceil(math.sqrt(n))))

    # Sort nodes for visual grouping
    if sort_by == "type":
        type_order = {"text": 0, "file": 1, "link": 2}
        content.sort(key=lambda n: (type_order.get(n.get("type"), 3), n.get("id", "")))
    elif sort_by == "size":
        content.sort(key=lambda n: n["width"] * n["height"], reverse=True)

    # Calculate cell dimensions (use max node size per column)
    max_w = max(n["width"] for n in content)
    max_h = max(n["height"] for n in content)
    cell_w = max_w + H_GAP
    cell_h = max_h + V_GAP

    # Place nodes
    start_x = 0
    start_y = 0
    for i, node in enumerate(content):
        col = i % columns
        row = i // columns
        # Center node within cell
        x_offset = (cell_w - node["width"]) // 2
        y_offset = (cell_h - node["height"]) // 2
        node["x"] = snap(start_x + col * cell_w + x_offset)
        node["y"] = snap(start_y + row * cell_h + y_offset)

    return content


# ─────────────────────────────────────────────
# Algorithm: DAGRE (Hierarchical / Sugiyama)
# ─────────────────────────────────────────────

def layout_dagre(content, edges, direction="TB"):
    """Hierarchical layout using a simplified Sugiyama algorithm.

    Good for: flowcharts, org charts, process diagrams.
    Directions: TB (top-bottom), LR (left-right), BT, RL.
    """
    if not content:
        return content

    node_map = {n["id"]: n for n in content}
    node_ids = set(node_map.keys())

    # Build adjacency from edges
    children = {nid: [] for nid in node_ids}
    parents = {nid: [] for nid in node_ids}
    for edge in edges:
        fn = edge.get("fromNode")
        tn = edge.get("toNode")
        if fn in node_ids and tn in node_ids:
            children[fn].append(tn)
            parents[tn].append(fn)

    # Find roots (nodes with no incoming edges from within content)
    roots = [nid for nid in node_ids if not parents[nid]]
    if not roots:
        # Cycle detected — pick the node with fewest parents
        roots = [min(node_ids, key=lambda nid: len(parents[nid]))]

    # Assign layers via BFS from roots
    layers = {}
    visited = set()
    queue = [(r, 0) for r in roots]
    for r, _ in queue:
        visited.add(r)
        layers[r] = 0

    while queue:
        current, layer = queue.pop(0)
        for child in children.get(current, []):
            new_layer = layer + 1
            if child not in visited or new_layer > layers.get(child, -1):
                layers[child] = new_layer
                if child not in visited:
                    visited.add(child)
                    queue.append((child, new_layer))

    # Assign disconnected nodes to a separate layer beyond the graph
    max_layer = max(layers.values()) if layers else 0
    disconnected_layer = max_layer + 1
    for nid in node_ids:
        if nid not in layers:
            layers[nid] = disconnected_layer

    # Group nodes by layer
    layer_groups = {}
    for nid, layer in layers.items():
        layer_groups.setdefault(layer, []).append(nid)

    # Sort within each layer for consistent ordering
    for layer in layer_groups:
        layer_groups[layer].sort()

    # Pre-compute cumulative layer offsets to handle heterogeneous node sizes
    sorted_layers = sorted(layer_groups.keys())
    layer_dims = {}  # layer_idx -> (max_w_in_layer, max_h_in_layer)
    for li in sorted_layers:
        nids = layer_groups[li]
        layer_dims[li] = (
            max(node_map[n]["width"] for n in nids),
            max(node_map[n]["height"] for n in nids),
        )

    # Cumulative offsets (forward direction)
    cumulative_y = {}  # for TB
    cumulative_x = {}  # for LR
    cy, cx = 0, 0
    for li in sorted_layers:
        cumulative_y[li] = cy
        cumulative_x[li] = cx
        mw, mh = layer_dims[li]
        cy += mh + V_GAP * 2
        cx += mw + H_GAP * 2

    total_y = cy
    total_x = cx

    # Position nodes
    for layer_idx in sorted_layers:
        nodes_in_layer = layer_groups[layer_idx]
        n_in_layer = len(nodes_in_layer)
        mw, mh = layer_dims[layer_idx]

        for pos, nid in enumerate(nodes_in_layer):
            node = node_map[nid]

            if direction == "TB":
                cell_w = mw + H_GAP
                total_w = n_in_layer * cell_w
                start_x = -total_w // 2
                node["x"] = snap(start_x + pos * cell_w + (cell_w - node["width"]) // 2)
                node["y"] = snap(cumulative_y[layer_idx])

            elif direction == "LR":
                cell_h = mh + V_GAP
                total_h = n_in_layer * cell_h
                start_y = -total_h // 2
                node["x"] = snap(cumulative_x[layer_idx])
                node["y"] = snap(start_y + pos * cell_h + (cell_h - node["height"]) // 2)

            elif direction == "BT":
                cell_w = mw + H_GAP
                total_w = n_in_layer * cell_w
                start_x = -total_w // 2
                node["x"] = snap(start_x + pos * cell_w + (cell_w - node["width"]) // 2)
                node["y"] = snap(total_y - cumulative_y[layer_idx] - mh)

            elif direction == "RL":
                cell_h = mh + V_GAP
                total_h = n_in_layer * cell_h
                start_y = -total_h // 2
                node["x"] = snap(total_x - cumulative_x[layer_idx] - mw)
                node["y"] = snap(start_y + pos * cell_h + (cell_h - node["height"]) // 2)

    return content


# ─────────────────────────────────────────────
# Algorithm: RADIAL
# ─────────────────────────────────────────────

def layout_radial(content, edges, center_id=None):
    """Radial layout expanding from a center node.

    Good for: mind maps, concept maps, topic exploration.
    """
    if not content:
        return content

    node_map = {n["id"]: n for n in content}
    node_ids = set(node_map.keys())

    # Pick center node
    if center_id and center_id in node_map:
        center = center_id
    else:
        # Use the node with most connections
        conn_count = {nid: 0 for nid in node_ids}
        for edge in edges:
            fn, tn = edge.get("fromNode"), edge.get("toNode")
            if fn in conn_count:
                conn_count[fn] += 1
            if tn in conn_count:
                conn_count[tn] += 1
        center = max(conn_count, key=conn_count.get) if conn_count else content[0]["id"]

    # BFS to assign rings
    rings = {center: 0}
    visited = {center}
    queue = [center]

    # Build undirected adjacency
    adj = {nid: set() for nid in node_ids}
    for edge in edges:
        fn, tn = edge.get("fromNode"), edge.get("toNode")
        if fn in adj and tn in adj:
            adj[fn].add(tn)
            adj[tn].add(fn)

    while queue:
        current = queue.pop(0)
        for neighbor in adj.get(current, set()):
            if neighbor not in visited:
                visited.add(neighbor)
                rings[neighbor] = rings[current] + 1
                queue.append(neighbor)

    # Assign unvisited nodes to outermost ring + 1
    max_ring = max(rings.values()) if rings else 0
    for nid in node_ids:
        if nid not in rings:
            rings[nid] = max_ring + 1

    # Group by ring
    ring_groups = {}
    for nid, ring in rings.items():
        ring_groups.setdefault(ring, []).append(nid)

    # Position: center node at origin, rings expand outward
    center_node = node_map[center]
    center_node["x"] = snap(-center_node["width"] // 2)
    center_node["y"] = snap(-center_node["height"] // 2)

    base_radius = 300
    for ring_idx in sorted(ring_groups.keys()):
        if ring_idx == 0:
            continue  # center already placed

        nodes_in_ring = ring_groups[ring_idx]
        n_nodes = len(nodes_in_ring)
        # Scale radius with both ring index and node count to prevent overlap
        max_node_w = max(node_map[nid]["width"] for nid in nodes_in_ring)
        min_arc = max_node_w + H_GAP
        min_radius_for_count = math.ceil(n_nodes * min_arc / (2 * math.pi)) if n_nodes > 1 else 0
        radius = max(base_radius * ring_idx, min_radius_for_count)
        angle_step = 2 * math.pi / max(n_nodes, 1)

        for i, nid in enumerate(sorted(nodes_in_ring)):
            node = node_map[nid]
            angle = angle_step * i - math.pi / 2  # start from top
            cx = radius * math.cos(angle)
            cy = radius * math.sin(angle)
            node["x"] = snap(cx - node["width"] // 2)
            node["y"] = snap(cy - node["height"] // 2)

    return content


# ─────────────────────────────────────────────
# Algorithm: FORCE-DIRECTED
# ─────────────────────────────────────────────

def layout_force(content, edges, iterations=100):
    """Force-directed spring layout using Fruchterman-Reingold.

    Good for: knowledge graphs, entity relationships, network diagrams.
    """
    if not content:
        return content
    if len(content) == 1:
        content[0]["x"] = 0
        content[0]["y"] = 0
        return content

    node_map = {n["id"]: n for n in content}
    node_ids = list(node_map.keys())
    n = len(node_ids)

    # Initialize positions in a circle
    # Scale area with node count so k stays larger than typical node widths
    max_dim = max(max(nd["width"], nd["height"]) for nd in content)
    min_spacing = max_dim + H_GAP
    area = max(800 * 800, n * min_spacing * min_spacing)
    k = math.sqrt(area / max(n, 1))  # optimal distance (>= node size + gap)
    positions = {}
    for i, nid in enumerate(node_ids):
        angle = 2 * math.pi * i / n
        radius = k * 2
        positions[nid] = [radius * math.cos(angle), radius * math.sin(angle)]

    # Build edge set
    edge_set = set()
    for edge in edges:
        fn, tn = edge.get("fromNode"), edge.get("toNode")
        if fn in node_map and tn in node_map:
            edge_set.add((fn, tn))

    # Fruchterman-Reingold iterations
    temp = k * 2  # initial temperature

    for iteration in range(iterations):
        # Calculate repulsive forces (all pairs)
        displacements = {nid: [0.0, 0.0] for nid in node_ids}

        for i in range(n):
            for j in range(i + 1, n):
                ni, nj = node_ids[i], node_ids[j]
                dx = positions[ni][0] - positions[nj][0]
                dy = positions[ni][1] - positions[nj][1]
                dist = max(math.sqrt(dx * dx + dy * dy), 0.01)

                # Repulsive force: k^2 / dist
                force = (k * k) / dist
                fx = (dx / dist) * force
                fy = (dy / dist) * force

                displacements[ni][0] += fx
                displacements[ni][1] += fy
                displacements[nj][0] -= fx
                displacements[nj][1] -= fy

        # Calculate attractive forces (edges only)
        for fn, tn in edge_set:
            dx = positions[fn][0] - positions[tn][0]
            dy = positions[fn][1] - positions[tn][1]
            dist = max(math.sqrt(dx * dx + dy * dy), 0.01)

            # Attractive force: dist^2 / k
            force = (dist * dist) / k
            fx = (dx / dist) * force
            fy = (dy / dist) * force

            displacements[fn][0] -= fx
            displacements[fn][1] -= fy
            displacements[tn][0] += fx
            displacements[tn][1] += fy

        # Apply displacements with temperature limiting
        for nid in node_ids:
            dx = displacements[nid][0]
            dy = displacements[nid][1]
            dist = max(math.sqrt(dx * dx + dy * dy), 0.01)

            # Limit displacement by temperature
            scale = min(dist, temp) / dist
            positions[nid][0] += dx * scale
            positions[nid][1] += dy * scale

        # Cool down
        temp *= 0.95

    # Apply positions to nodes
    for nid in node_ids:
        node = node_map[nid]
        node["x"] = snap(positions[nid][0] - node["width"] // 2)
        node["y"] = snap(positions[nid][1] - node["height"] // 2)

    return content


# ─────────────────────────────────────────────
# Algorithm: LINEAR (Timeline)
# ─────────────────────────────────────────────

def layout_linear(content, axis="horizontal"):
    """Linear layout along a single axis.

    Good for: timelines, sequences, step-by-step processes.
    """
    if not content:
        return content

    # Sort by current position on the layout axis
    if axis == "horizontal":
        content.sort(key=lambda n: n["x"])
    else:
        content.sort(key=lambda n: n["y"])

    pos = 0
    for node in content:
        if axis == "horizontal":
            node["x"] = snap(pos)
            node["y"] = snap(-node["height"] // 2)  # center vertically
            pos += node["width"] + H_GAP
        else:
            node["x"] = snap(-node["width"] // 2)  # center horizontally
            node["y"] = snap(pos)
            pos += node["height"] + V_GAP

    return content


# ─────────────────────────────────────────────
# Algorithm: AUTO (detect best algorithm)
# ─────────────────────────────────────────────

def detect_algorithm(content, edges):
    """Auto-detect the best layout algorithm based on canvas content.

    Heuristics:
    - Many edges + clear hierarchy → dagre
    - Many edges + no clear hierarchy → force
    - Mostly images/files → grid
    - Single central node with spokes → radial
    - No edges → grid
    """
    n_nodes = len(content)
    n_edges = len([e for e in edges
                   if e.get("fromNode") in {n["id"] for n in content}
                   and e.get("toNode") in {n["id"] for n in content}])

    if n_nodes == 0:
        return "grid"

    edge_ratio = n_edges / max(n_nodes, 1)
    file_ratio = sum(1 for n in content if n.get("type") == "file") / n_nodes

    # Mostly images/files with few edges → grid (gallery/mood board)
    if file_ratio > 0.6 and edge_ratio < 0.5:
        return "grid"

    # No edges → grid
    if n_edges == 0:
        return "grid"

    # Check for hub-and-spoke pattern → radial (internal edges only)
    node_ids = {n["id"] for n in content}
    conn_counts = {nid: 0 for nid in node_ids}
    for edge in edges:
        fn, tn = edge.get("fromNode"), edge.get("toNode")
        if fn in node_ids and tn in node_ids:
            conn_counts[fn] += 1
            conn_counts[tn] += 1

    if conn_counts:
        max_conn = max(conn_counts.values())
        if max_conn > n_nodes * 0.4 and n_edges > 3:
            return "radial"

    # Check for hierarchy (more sources than sinks) → dagre
    sources = set()
    sinks = set()
    for edge in edges:
        fn, tn = edge.get("fromNode"), edge.get("toNode")
        if fn in node_ids:
            sources.add(fn)
        if tn in node_ids:
            sinks.add(tn)
    pure_sources = sources - sinks
    if len(pure_sources) >= 1 and edge_ratio > 0.5:
        return "dagre"

    # Dense edges → force
    if edge_ratio > 1.0:
        return "force"

    # Default → dagre (most common structured layout)
    return "dagre"


# ─────────────────────────────────────────────
# Main orchestration
# ─────────────────────────────────────────────

def layout_canvas(canvas_path, algorithm, **kwargs):
    """Apply a layout algorithm to a canvas file."""
    path = Path(canvas_path)

    try:
        original_text = path.read_text(encoding="utf-8")
        data = json.loads(original_text)
    except FileNotFoundError:
        return {"success": False, "error": f"File not found: {path}"}
    except json.JSONDecodeError as e:
        return {"success": False, "error": f"Invalid JSON: {e}"}

    nodes = data.get("nodes", [])
    edges = data.get("edges", [])

    groups, content = separate_groups_and_content(nodes)
    membership = find_group_membership(groups, content)

    # Store original positions for move counting
    original_positions = {n["id"]: (n["x"], n["y"]) for n in content}

    # Auto-detect if needed
    actual_algorithm = algorithm
    if algorithm == "auto":
        actual_algorithm = detect_algorithm(content, edges)

    # Apply the selected algorithm
    if actual_algorithm == "grid":
        columns = kwargs.get("columns")
        sort_by = kwargs.get("sort_by", "type")
        content = layout_grid(content, columns=columns, sort_by=sort_by)

    elif actual_algorithm == "dagre":
        direction = kwargs.get("direction", "TB")
        content = layout_dagre(content, edges, direction=direction)

    elif actual_algorithm == "radial":
        center_id = kwargs.get("center")
        content = layout_radial(content, edges, center_id=center_id)

    elif actual_algorithm == "force":
        iterations = kwargs.get("iterations", 100)
        content = layout_force(content, edges, iterations=iterations)

    elif actual_algorithm == "linear":
        axis = kwargs.get("axis", "horizontal")
        content = layout_linear(content, axis=axis)

    else:
        return {"success": False, "error": f"Unknown algorithm: {actual_algorithm}"}

    # Refit groups around their content
    # Snap endpoints individually THEN compute dimensions to prevent overflow
    for group in groups:
        members = [n for n in content if membership.get(n["id"]) == group["id"]]
        if members:
            raw_min_x = min(n["x"] for n in members) - GROUP_PAD
            raw_min_y = min(n["y"] for n in members) - GROUP_PAD - 40  # extra for label
            raw_max_x = max(n["x"] + n["width"] for n in members) + GROUP_PAD
            raw_max_y = max(n["y"] + n["height"] for n in members) + GROUP_PAD

            gx = snap(raw_min_x)
            gy = snap(raw_min_y)
            # Snap the far edges outward to ensure content fits
            gx2 = snap(raw_max_x + GRID - 1)  # round up
            gy2 = snap(raw_max_y + GRID - 1)

            group["x"] = gx
            group["y"] = gy
            group["width"] = gx2 - gx
            group["height"] = gy2 - gy

    # Count moved nodes
    nodes_moved = sum(
        1 for n in content
        if (n["x"], n["y"]) != original_positions.get(n["id"], (n["x"], n["y"]))
    )

    # Reassemble: groups first (z-index), then content
    data["nodes"] = groups + content

    # Write result
    dry_run = kwargs.get("dry_run", False)
    backup_path = None

    if not dry_run:
        # Backup original (use cached text, not re-read)
        backup_path = str(path) + ".bak"
        suffix = 1
        while Path(backup_path).exists():
            suffix += 1
            backup_path = f"{path}.bak{suffix}"
        Path(backup_path).write_text(original_text, encoding="utf-8")

        # Write laid-out canvas
        path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    return {
        "success": True,
        "algorithm": actual_algorithm,
        "auto_detected": algorithm == "auto",
        "nodes_moved": nodes_moved,
        "total_nodes": len(content),
        "groups_preserved": len(groups),
        "backup": backup_path,
        "dry_run": dry_run,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Re-layout Obsidian Canvas nodes using spatial algorithms"
    )
    parser.add_argument("canvas_path", help="Path to .canvas file")
    parser.add_argument(
        "algorithm",
        choices=["auto", "grid", "dagre", "radial", "force", "linear"],
        help="Layout algorithm to apply",
    )
    parser.add_argument(
        "--columns", type=int, default=None,
        help="Number of columns for grid layout (auto-detected if omitted)",
    )
    parser.add_argument(
        "--direction", choices=["TB", "LR", "BT", "RL"], default="TB",
        help="Flow direction for dagre layout (default: TB = top-bottom)",
    )
    parser.add_argument(
        "--center", default=None,
        help="Center node ID for radial layout (auto-detected if omitted)",
    )
    parser.add_argument(
        "--axis", choices=["horizontal", "vertical"], default="horizontal",
        help="Axis for linear layout (default: horizontal)",
    )
    parser.add_argument(
        "--iterations", type=int, default=100,
        help="Number of iterations for force layout (default: 100)",
    )
    parser.add_argument(
        "--sort-by", choices=["type", "size"], default="type",
        help="Sort order for grid layout (default: type)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Calculate layout without writing changes",
    )

    args = parser.parse_args()

    path = Path(args.canvas_path)
    if not path.exists():
        print(json.dumps({"success": False, "error": f"File not found: {path}"}))
        sys.exit(2)

    result = layout_canvas(
        args.canvas_path,
        args.algorithm,
        columns=args.columns,
        direction=args.direction,
        center=args.center,
        axis=args.axis,
        iterations=args.iterations,
        sort_by=args.sort_by,
        dry_run=args.dry_run,
    )

    print(json.dumps(result, indent=2))
    sys.exit(0 if result.get("success") else 1)


if __name__ == "__main__":
    main()
