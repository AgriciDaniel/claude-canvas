#!/usr/bin/env python3
"""canvas_validate.py — Validate Obsidian Canvas JSON files.

Checks for common issues: invalid JSON, missing required fields, ID collisions,
node count limits, coordinate alignment, z-index ordering, and path formats.

Usage:
    python3 canvas_validate.py <canvas_path>
    python3 canvas_validate.py <canvas_path> --quiet
    python3 canvas_validate.py <canvas_path> --fix

Output (JSON):
    {
        "valid": true,
        "path": "path/to/canvas.canvas",
        "nodes": 42,
        "edges": 8,
        "groups": 3,
        "warnings": ["Node count 42 approaching limit (100)"],
        "errors": []
    }

Exit codes:
    0 = valid (may have warnings)
    1 = invalid (has errors)
    2 = file not found or not readable
"""

import argparse
import json
import sys
from pathlib import Path


VALID_NODE_TYPES = {"text", "file", "link", "group"}
VALID_COLORS = {"1", "2", "3", "4", "5", "6"}
VALID_SIDES = {"top", "bottom", "left", "right"}
VALID_ENDS = {"none", "arrow"}
NODE_LIMIT_WARN = 100
NODE_LIMIT_ERROR = 200
GRID_SIZE = 20


def validate_canvas(canvas_path: Path, fix: bool = False) -> dict:
    """Validate a canvas file and return a report."""
    result = {
        "valid": True,
        "path": str(canvas_path),
        "nodes": 0,
        "edges": 0,
        "groups": 0,
        "warnings": [],
        "errors": [],
    }

    # Read and parse JSON
    try:
        text = canvas_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        result["valid"] = False
        result["errors"].append(f"File not found: {canvas_path}")
        return result
    except Exception as e:
        result["valid"] = False
        result["errors"].append(f"Cannot read file: {e}")
        return result

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        result["valid"] = False
        result["errors"].append(f"Invalid JSON: {e}")
        return result

    # Top-level structure
    if not isinstance(data, dict):
        result["valid"] = False
        result["errors"].append("Root must be a JSON object")
        return result

    nodes = data.get("nodes", [])
    edges = data.get("edges", [])

    if not isinstance(nodes, list):
        result["valid"] = False
        result["errors"].append("'nodes' must be an array")
        return result

    if not isinstance(edges, list):
        result["valid"] = False
        result["errors"].append("'edges' must be an array")
        return result

    result["nodes"] = len(nodes)
    result["edges"] = len(edges)

    # Node count limits
    if len(nodes) > NODE_LIMIT_ERROR:
        result["errors"].append(
            f"Node count {len(nodes)} exceeds limit ({NODE_LIMIT_ERROR})"
        )
        result["valid"] = False
    elif len(nodes) > NODE_LIMIT_WARN:
        result["warnings"].append(
            f"Node count {len(nodes)} exceeds warning threshold ({NODE_LIMIT_WARN}). Hard limit is {NODE_LIMIT_ERROR}."
        )

    # Validate nodes
    seen_ids = set()
    first_content_idx = None
    last_group_idx = None
    modified = False

    for i, node in enumerate(nodes):
        if not isinstance(node, dict):
            result["errors"].append(f"Node at index {i} is not an object")
            result["valid"] = False
            continue

        # Required fields
        node_id = node.get("id")
        if not node_id:
            result["errors"].append(f"Node at index {i} missing 'id'")
            result["valid"] = False
        elif node_id in seen_ids:
            result["errors"].append(f"Duplicate node ID: '{node_id}'")
            result["valid"] = False
        else:
            seen_ids.add(node_id)

        node_type = node.get("type")
        if not node_type:
            result["errors"].append(f"Node '{node_id}' missing 'type'")
            result["valid"] = False
        elif node_type not in VALID_NODE_TYPES:
            result["errors"].append(
                f"Node '{node_id}' has invalid type: '{node_type}'"
            )
            result["valid"] = False

        # Track z-index ordering
        if node_type == "group":
            last_group_idx = i
            result["groups"] += 1
        elif first_content_idx is None:
            first_content_idx = i

        # Position fields
        for field in ("x", "y", "width", "height"):
            val = node.get(field)
            if val is None:
                result["errors"].append(f"Node '{node_id}' missing '{field}'")
                result["valid"] = False
            elif not isinstance(val, (int, float)):
                result["errors"].append(
                    f"Node '{node_id}' field '{field}' must be numeric"
                )
                result["valid"] = False
            elif field in ("width", "height") and val <= 0:
                result["warnings"].append(
                    f"Node '{node_id}' has non-positive {field}: {val}"
                )

        # Grid alignment check (all four positional fields)
        for field in ("x", "y", "width", "height"):
            val = node.get(field)
            if isinstance(val, (int, float)) and val % GRID_SIZE != 0:
                result["warnings"].append(
                    f"Node '{node_id}' {field}={val} not aligned to {GRID_SIZE}px grid"
                )
                if fix:
                    node[field] = round(val / GRID_SIZE) * GRID_SIZE
                    modified = True

        # Color validation
        color = node.get("color")
        if color is not None:
            if isinstance(color, int):
                result["warnings"].append(
                    f"Node '{node_id}' color is integer {color}, should be string \"{color}\""
                )
                if fix:
                    node["color"] = str(color)
                    modified = True
            elif isinstance(color, str) and not color.startswith("#") and color not in VALID_COLORS:
                result["warnings"].append(
                    f"Node '{node_id}' has unknown color: '{color}'"
                )

        # Type-specific checks
        if node_type == "text" and "text" not in node:
            result["errors"].append(f"Text node '{node_id}' missing 'text' field")
            result["valid"] = False
        elif node_type == "text" and node.get("text", None) == "":
            result["warnings"].append(
                f"Text node '{node_id}' has empty 'text' field"
            )

        if node_type == "file" and "file" not in node:
            result["errors"].append(f"File node '{node_id}' missing 'file' field")
            result["valid"] = False
        elif node_type == "file":
            file_path = node.get("file", "")
            if file_path.startswith("/") or file_path.startswith("~"):
                result["errors"].append(
                    f"File node '{node_id}' uses absolute path: '{file_path}'. Must be vault-relative."
                )
                result["valid"] = False

        if node_type == "link" and "url" not in node:
            result["errors"].append(f"Link node '{node_id}' missing 'url' field")
            result["valid"] = False
        elif node_type == "link":
            url = node.get("url", "")
            if url and not (url.startswith("http://") or url.startswith("https://")):
                result["warnings"].append(
                    f"Link node '{node_id}' url does not start with http(s)://: '{url}'"
                )

    # Z-index ordering check
    if last_group_idx is not None and first_content_idx is not None:
        if last_group_idx > first_content_idx:
            result["warnings"].append(
                "Z-index issue: some group nodes appear after content nodes. "
                "Groups should come first in the array for proper background rendering."
            )

    # Node overlap detection (content nodes only — groups are visual containers)
    content_nodes = [n for n in nodes if isinstance(n, dict) and n.get("type") != "group"]
    for i in range(len(content_nodes)):
        for j in range(i + 1, len(content_nodes)):
            a = content_nodes[i]
            b = content_nodes[j]
            # Check bounding box overlap
            a_right = a.get("x", 0) + a.get("width", 0)
            a_bottom = a.get("y", 0) + a.get("height", 0)
            b_right = b.get("x", 0) + b.get("width", 0)
            b_bottom = b.get("y", 0) + b.get("height", 0)

            if (a.get("x", 0) < b_right and a_right > b.get("x", 0)
                    and a.get("y", 0) < b_bottom and a_bottom > b.get("y", 0)):
                # Calculate overlap area for severity
                overlap_x = min(a_right, b_right) - max(a.get("x", 0), b.get("x", 0))
                overlap_y = min(a_bottom, b_bottom) - max(a.get("y", 0), b.get("y", 0))
                overlap_area = overlap_x * overlap_y
                min_area = min(
                    a.get("width", 1) * a.get("height", 1),
                    b.get("width", 1) * b.get("height", 1),
                )
                overlap_pct = round(overlap_area / max(min_area, 1) * 100)

                if overlap_pct > 10:  # Only warn for significant overlaps (>10%)
                    result["warnings"].append(
                        f"Node overlap: '{a.get('id')}' and '{b.get('id')}' "
                        f"overlap by {overlap_pct}% ({overlap_x}x{overlap_y}px)"
                    )

    # Validate edges
    node_ids = seen_ids
    seen_edge_ids = set()
    for i, edge in enumerate(edges):
        if not isinstance(edge, dict):
            result["errors"].append(f"Edge at index {i} is not an object")
            result["valid"] = False
            continue

        edge_id = edge.get("id")
        if not edge_id:
            result["errors"].append(f"Edge at index {i} missing 'id'")
            result["valid"] = False
        elif edge_id in seen_edge_ids:
            result["errors"].append(f"Duplicate edge ID: '{edge_id}'")
            result["valid"] = False
        else:
            seen_edge_ids.add(edge_id)

        from_node = edge.get("fromNode")
        to_node = edge.get("toNode")

        if not from_node:
            result["errors"].append(f"Edge '{edge_id}' missing 'fromNode'")
            result["valid"] = False
        elif from_node not in node_ids:
            result["warnings"].append(
                f"Edge '{edge_id}' references unknown fromNode: '{from_node}'"
            )

        if not to_node:
            result["errors"].append(f"Edge '{edge_id}' missing 'toNode'")
            result["valid"] = False
        elif to_node not in node_ids:
            result["warnings"].append(
                f"Edge '{edge_id}' references unknown toNode: '{to_node}'"
            )

        # Side validation
        for side_field in ("fromSide", "toSide"):
            side = edge.get(side_field)
            if side is not None and side not in VALID_SIDES:
                result["warnings"].append(
                    f"Edge '{edge_id}' has invalid {side_field}: '{side}'"
                )

        # End validation
        for end_field in ("fromEnd", "toEnd"):
            end = edge.get(end_field)
            if end is not None and end not in VALID_ENDS:
                result["warnings"].append(
                    f"Edge '{edge_id}' has invalid {end_field}: '{end}'"
                )

    # Write fixes if requested
    if fix and modified:
        canvas_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        result["warnings"].append("Applied fixes (grid alignment, color types)")

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Validate Obsidian Canvas JSON files"
    )
    parser.add_argument("canvas_path", help="Path to .canvas file")
    parser.add_argument(
        "--quiet", "-q", action="store_true",
        help="Only output if errors found"
    )
    parser.add_argument(
        "--fix", action="store_true",
        help="Fix auto-fixable issues (grid alignment, color types)"
    )
    args = parser.parse_args()

    path = Path(args.canvas_path)
    if not path.exists():
        print(json.dumps({
            "valid": False,
            "path": str(path),
            "nodes": 0, "edges": 0, "groups": 0,
            "warnings": [],
            "errors": [f"File not found: {path}"]
        }))
        sys.exit(2)

    result = validate_canvas(path, fix=args.fix)

    if args.quiet and result["valid"]:
        sys.exit(0)

    print(json.dumps(result, indent=2))
    sys.exit(0 if result["valid"] else 1)


if __name__ == "__main__":
    main()
