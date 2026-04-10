#!/usr/bin/env python3
"""canvas_template.py — Instantiate Obsidian Canvas template archetypes.

Loads a template JSON, substitutes parameters, generates unique IDs,
applies the specified layout algorithm, and writes a ready-to-use .canvas file.

Usage:
    python3 canvas_template.py <template> <output_path> [--param key=value ...]
    python3 canvas_template.py presentation out.canvas --param title="Q3 Review" --param slide_count=6
    python3 canvas_template.py gallery out.canvas --param title="Screenshots" --param columns=4
    python3 canvas_template.py --list

Output (JSON):
    {
        "success": true,
        "template": "presentation",
        "output": "out.canvas",
        "nodes": 24,
        "edges": 5,
        "groups": 6
    }

Exit codes:
    0 = success
    1 = error
    2 = template not found
"""

import argparse
import json
import math
import sys
import time
from pathlib import Path

GRID = 20
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


def snap(value):
    """Snap to 20px grid."""
    return round(value / GRID) * GRID


_id_counter = 0


def gen_id(prefix, slug=""):
    """Generate a unique ID with incrementing counter to prevent collisions."""
    global _id_counter
    _id_counter += 1
    ts = int(time.time())
    if slug:
        slug = slug.lower().replace(" ", "-")[:20]
        return f"{prefix}-{slug}-{ts}-{_id_counter}"
    return f"{prefix}-{ts}-{_id_counter}"


def list_templates():
    """List all available template archetypes."""
    templates = {}
    if not TEMPLATES_DIR.exists():
        return templates
    for f in sorted(TEMPLATES_DIR.glob("*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            templates[f.stem] = {
                "name": data.get("name", f.stem),
                "description": data.get("description", ""),
                "layout": data.get("layout", "grid"),
                "defaults": data.get("defaults", {}),
            }
        except (json.JSONDecodeError, KeyError):
            templates[f.stem] = {"name": f.stem, "description": "Invalid template"}
    return templates


def instantiate_template(template_name, params, output_path):
    """Load a template, substitute params, generate canvas JSON."""
    template_path = TEMPLATES_DIR / f"{template_name}.json"

    if not template_path.exists():
        return {"success": False, "error": f"Template not found: {template_name}"}

    try:
        template = json.loads(template_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return {"success": False, "error": f"Invalid template JSON: {e}"}

    # Merge defaults with user params
    defaults = template.get("defaults", {})
    merged = {**defaults, **params}

    title = str(merged.get("title", template.get("name", template_name).replace("-", " ").title()))
    color_title = str(merged.get("color_title", "6"))
    color_body = str(merged.get("color_body", "4"))
    color_accent = str(merged.get("color_accent", "5"))

    # Build nodes and edges from template definition
    nodes = []
    edges = []

    # Reset global ID counter for each template instantiation
    global _id_counter
    _id_counter = 0

    # Process node templates
    node_templates = template.get("node_templates", [])
    generated_ids = {}  # role -> list of generated IDs

    for nt in node_templates:
        role = nt.get("role", "node")
        node_type = nt.get("type", "text")
        repeat = nt.get("repeat", 1)

        # Resolve repeat count from params
        if isinstance(repeat, str) and repeat.startswith("$"):
            param_key = repeat[1:]
            repeat = int(merged.get(param_key, nt.get("repeat_default", 1)))

        ids_for_role = []
        for i in range(repeat):
            node_id = gen_id(
                {"text": "text", "file": "file", "group": "zone", "link": "link"}.get(node_type, "node"),
                f"{role}-{i+1}"
            )
            ids_for_role.append(node_id)

            node = {
                "id": node_id,
                "type": node_type,
                "x": 0, "y": 0,
                "width": nt.get("width", 300),
                "height": nt.get("height", 120),
            }

            # Store group_role metadata for layout engine
            # Groups store their own role; content nodes store which group they belong to
            if node_type == "group":
                node["_group_role"] = role
            elif nt.get("group_role"):
                node["_group_role"] = nt["group_role"]

            # Apply color
            color = nt.get("color")
            if color:
                color = color.replace("$color_title", color_title)
                color = color.replace("$color_body", color_body)
                color = color.replace("$color_accent", color_accent)
                node["color"] = color

            # Type-specific fields
            if node_type == "text":
                text = nt.get("text", f"# {role.replace('_', ' ').title()} {i+1}")
                text = text.replace("$title", title)
                text = text.replace("{n}", str(i + 1))
                node["text"] = text

            elif node_type == "group":
                label = nt.get("label", f"{role.replace('_', ' ').title()} {i+1}")
                label = label.replace("$title", title)
                label = label.replace("{n}", str(i + 1))
                node["label"] = label

            elif node_type == "file":
                node["file"] = nt.get("file", f"placeholder-{i+1}.png")

            elif node_type == "link":
                node["url"] = nt.get("url", "https://example.com")

            nodes.append(node)

        generated_ids[role] = ids_for_role

    # Process edge templates
    edge_templates = template.get("edge_templates", [])
    for et in edge_templates:
        from_role = et.get("from_role")
        to_role = et.get("to_role")
        pattern = et.get("pattern", "sequential")  # sequential or broadcast

        from_ids = generated_ids.get(from_role, [])
        to_ids = generated_ids.get(to_role, [])

        if pattern == "sequential":
            # Connect n[i] → n[i+1] within the same role, or from_role[i] → to_role[i]
            if from_role == to_role:
                for i in range(len(from_ids) - 1):
                    edges.append({
                        "id": gen_id("e", f"{from_role}-{i}-{i+1}"),
                        "fromNode": from_ids[i],
                        "toNode": from_ids[i + 1],
                        "toEnd": "arrow",
                    })
            else:
                for i in range(min(len(from_ids), len(to_ids))):
                    edges.append({
                        "id": gen_id("e", f"{from_role}-{to_role}-{i}"),
                        "fromNode": from_ids[i],
                        "toNode": to_ids[i],
                        "toEnd": "arrow",
                    })

        elif pattern == "broadcast":
            # Connect from_role[0] → all to_role nodes
            if from_ids:
                for j, tid in enumerate(to_ids):
                    edges.append({
                        "id": gen_id("e", f"{from_role}-{to_role}-{j}"),
                        "fromNode": from_ids[0],
                        "toNode": tid,
                        "toEnd": "arrow",
                    })

    # Apply layout based on template's specified algorithm
    layout_algo = template.get("layout", "grid")
    nodes = apply_template_layout(nodes, edges, layout_algo, merged)

    # Ensure z-index: groups first
    groups = [n for n in nodes if n["type"] == "group"]
    content = [n for n in nodes if n["type"] != "group"]
    ordered_nodes = groups + content

    # Strip internal metadata (_group_role) before writing
    for node in ordered_nodes:
        node.pop("_group_role", None)

    # Write canvas
    canvas = {"nodes": ordered_nodes, "edges": edges}
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(canvas, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    # Post-instantiation layout: apply archetype-specific algorithm if specified
    post_layout = template.get("post_layout")
    post_layout_applied = None
    if post_layout and post_layout in ("dagre", "radial", "force", "grid", "linear"):
        try:
            from canvas_layout import layout_canvas
            result = layout_canvas(str(output), post_layout)
            if result.get("success"):
                post_layout_applied = post_layout
        except ImportError:
            # Try running as subprocess
            import subprocess
            layout_script = SCRIPT_DIR / "canvas_layout.py"
            if layout_script.exists():
                proc = subprocess.run(
                    [sys.executable, str(layout_script), str(output), post_layout],
                    capture_output=True, text=True, timeout=30,
                )
                if proc.returncode == 0:
                    post_layout_applied = post_layout

    return {
        "success": True,
        "template": template_name,
        "output": str(output),
        "nodes": len(ordered_nodes),
        "edges": len(edges),
        "post_layout": post_layout_applied,
        "groups": len(groups),
    }


def apply_template_layout(nodes, edges, algorithm, params):
    """Apply a simple layout to template nodes.

    Uses _group_role metadata (set during instantiation) to place content
    nodes inside their designated group. Falls back to round-robin if no
    _group_role is set.
    """
    groups = [n for n in nodes if n["type"] == "group"]
    content = [n for n in nodes if n["type"] != "group"]

    # Build group-to-content mapping using _group_role metadata
    # Use list-per-role to handle repeated groups (e.g., 6 slides all with role "slide")
    groups_by_role = {}
    for g in groups:
        role = g.get("_group_role", g.get("id", ""))
        groups_by_role.setdefault(role, []).append(g)

    # Map content to groups via _group_role with index-based matching
    # slide_title[0] → slide[0], slide_title[1] → slide[1], etc. (round-robin within role)
    content_per_group = {g["id"]: [] for g in groups}
    unassigned = []
    role_counters = {}  # tracks how many content nodes assigned per role

    for c in content:
        target_role = c.get("_group_role")
        if target_role and target_role in groups_by_role:
            role_groups = groups_by_role[target_role]
            idx = role_counters.get(target_role, 0) % len(role_groups)
            content_per_group[role_groups[idx]["id"]].append(c)
            role_counters[target_role] = role_counters.get(target_role, 0) + 1
        else:
            unassigned.append(c)

    # If NO content has _group_role at all, fall back to even distribution
    if unassigned and not any(c.get("_group_role") for c in content):
        unassigned = list(content)
        content_per_group = {g["id"]: [] for g in groups}
        if groups:
            items_per_group = max(1, math.ceil(len(unassigned) / len(groups)))
            for gi, group in enumerate(groups):
                batch = unassigned[:items_per_group]
                unassigned = unassigned[items_per_group:]
                content_per_group[group["id"]] = batch

    if algorithm == "linear-vertical":
        # Stack groups vertically with gaps — good for presentations, project briefs
        gap = int(params.get("gap", 100))
        y = 0
        for group in groups:
            group["x"] = snap(0)
            group["y"] = snap(y)

            # Place this group's content inside it
            cx = group["x"] + 40
            cy = group["y"] + 60  # below label
            for c in content_per_group.get(group["id"], []):
                c["x"] = snap(cx)
                c["y"] = snap(cy)
                cy += c["height"] + 80  # 80px min gap between nodes

            # Auto-expand group if content overflows
            needed_height = cy - group["y"] + 40
            if needed_height > group["height"]:
                group["height"] = snap(needed_height)

            y += group["height"] + gap

        # Place unassigned content below all groups
        for c in unassigned:
            c["x"] = snap(0)
            c["y"] = snap(y)
            y += c["height"] + 80

        # No groups: just stack content vertically
        if not groups:
            for node in content:
                node["x"] = snap(0)
                node["y"] = snap(y)
                y += node["height"] + 80

    elif algorithm == "grid":
        cols = int(params.get("columns", math.ceil(math.sqrt(max(len(content), 1)))))
        cols = max(1, cols)

        if len(groups) <= 1:
            # Single or no group: flat grid of all content
            if content:
                max_w = max(n["width"] for n in content)
                max_h = max(n["height"] for n in content)
            else:
                max_w, max_h = 300, 120
            cell_w = max_w + 100
            cell_h = max_h + 80

            for i, node in enumerate(content):
                col = i % cols
                row = i // cols
                node["x"] = snap(col * cell_w)
                node["y"] = snap(row * cell_h)

            if len(groups) == 1 and content:
                g = groups[0]
                g["x"] = snap(-20)
                g["y"] = snap(-60)
                g["width"] = snap(cols * cell_w + 20)
                g["height"] = snap((math.ceil(len(content) / cols)) * cell_h + 60)

        else:
            # Multiple groups: place groups side-by-side, content INSIDE each group
            group_gap = 100
            gx = 0
            for group in groups:
                group["x"] = snap(gx)
                group["y"] = snap(-60)

                members = content_per_group.get(group["id"], [])
                if members:
                    # Stack content vertically inside group
                    cy = group["y"] + 60
                    for c in members:
                        c["x"] = snap(gx + 20)
                        c["y"] = snap(cy)
                        cy += c["height"] + 80
                    # Resize group to fit
                    needed_h = cy - group["y"] + 20
                    group["height"] = snap(max(group["height"], needed_h))

                gx += group["width"] + group_gap

            # Place unassigned content after all groups
            for c in unassigned:
                c["x"] = snap(gx)
                c["y"] = snap(0)
                gx += c["width"] + 60

    elif algorithm == "linear-horizontal":
        x = 0
        gap = int(params.get("gap", 100))
        for node in content:
            node["x"] = snap(x)
            node["y"] = snap(0)
            x += node["width"] + gap

    else:
        # Default: stack vertically
        y = 0
        for node in nodes:
            node["x"] = snap(0)
            node["y"] = snap(y)
            y += node["height"] + 40

    return nodes


def main():
    parser = argparse.ArgumentParser(
        description="Instantiate Obsidian Canvas template archetypes"
    )
    parser.add_argument(
        "template", nargs="?", default=None,
        help="Template archetype name (e.g., presentation, flowchart, gallery)",
    )
    parser.add_argument(
        "output_path", nargs="?", default=None,
        help="Output .canvas file path",
    )
    parser.add_argument(
        "--param", action="append", default=[],
        help="Template parameter as key=value (can repeat)",
    )
    parser.add_argument(
        "--list", action="store_true",
        help="List available template archetypes",
    )

    args = parser.parse_args()

    if args.list:
        templates = list_templates()
        if not templates:
            print(json.dumps({"templates": {}, "message": "No templates found. Check templates/ directory."}))
        else:
            print(json.dumps({"templates": templates}, indent=2))
        sys.exit(0)

    if not args.template or not args.output_path:
        parser.error("template and output_path are required (use --list to browse)")

    # Parse params
    params = {}
    for p in args.param:
        if "=" in p:
            key, value = p.split("=", 1)
            # Try to parse as int
            try:
                value = int(value)
            except ValueError:
                pass
            params[key] = value

    result = instantiate_template(args.template, params, args.output_path)
    print(json.dumps(result, indent=2))
    sys.exit(0 if result.get("success") else 1)


if __name__ == "__main__":
    main()
