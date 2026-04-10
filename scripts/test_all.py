#!/usr/bin/env python3
"""test_all.py — Comprehensive test suite for claude-canvas.

Runs template instantiation, layout algorithms, and validation checks.
Reports pass/fail for each test case.

Usage:
    python3 scripts/test_all.py
    python3 scripts/test_all.py --output-dir /tmp/canvas-tests
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
TEMPLATES_DIR = PROJECT_DIR / "templates"

PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"
WARN = "\033[93mWARN\033[0m"

results = {"pass": 0, "fail": 0, "warn": 0}


def run_script(script, args):
    """Run a Python script and return (exit_code, stdout, stderr)."""
    cmd = [sys.executable, str(SCRIPT_DIR / script)] + args
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    return proc.returncode, proc.stdout, proc.stderr


def test(name, condition, detail=""):
    """Record a test result."""
    if condition:
        results["pass"] += 1
        print(f"  [{PASS}] {name}")
    else:
        results["fail"] += 1
        print(f"  [{FAIL}] {name}{f' — {detail}' if detail else ''}")


def warn(name, detail=""):
    """Record a warning."""
    results["warn"] += 1
    print(f"  [{WARN}] {name}{f' — {detail}' if detail else ''}")


def test_templates(output_dir):
    """Test all 12 template instantiations."""
    print("\n=== TEMPLATE INSTANTIATION ===")

    templates = [f.stem for f in sorted(TEMPLATES_DIR.glob("*.json"))]
    test("12 templates found", len(templates) == 12, f"found {len(templates)}")

    for tmpl in templates:
        out = output_dir / f"{tmpl}.canvas"
        ec, stdout, stderr = run_script("canvas_template.py", [tmpl, str(out), "--param", f"title=Test {tmpl}"])
        if ec == 0:
            try:
                result = json.loads(stdout)
                test(f"{tmpl}: instantiate", result.get("success"), stderr)
            except json.JSONDecodeError:
                test(f"{tmpl}: instantiate", False, "invalid JSON output")
        else:
            test(f"{tmpl}: instantiate", False, stderr.strip())

    # Validate all generated canvases
    print("\n=== TEMPLATE VALIDATION ===")
    for tmpl in templates:
        out = output_dir / f"{tmpl}.canvas"
        if not out.exists():
            test(f"{tmpl}: validate", False, "canvas not created")
            continue
        ec, stdout, _ = run_script("canvas_validate.py", [str(out)])
        try:
            result = json.loads(stdout)
            valid = result.get("valid", False)
            errors = result.get("errors", [])
            warnings = result.get("warnings", [])
            overlaps = [w for w in warnings if "overlap" in w.lower()]
            test(f"{tmpl}: valid JSON Canvas", valid, "; ".join(errors[:2]))
            test(f"{tmpl}: no overlaps", len(overlaps) == 0,
                 f"{len(overlaps)} overlaps: {overlaps[0][:60]}" if overlaps else "")
        except json.JSONDecodeError:
            test(f"{tmpl}: validate", False, "validator returned invalid JSON")

    # Group containment check
    print("\n=== GROUP CONTAINMENT ===")
    multi_group_templates = ["kanban", "presentation", "project-brief", "dashboard", "comparison", "mood-board"]
    for tmpl in multi_group_templates:
        out = output_dir / f"{tmpl}.canvas"
        if not out.exists():
            continue
        data = json.loads(out.read_text())
        groups = [n for n in data["nodes"] if n.get("type") == "group"]
        content = [n for n in data["nodes"] if n.get("type") != "group"]
        total_contained = 0
        for g in groups:
            members = [c for c in content
                       if g["x"] <= c["x"] + c["width"]/2 <= g["x"] + g["width"]
                       and g["y"] <= c["y"] + c["height"]/2 <= g["y"] + g["height"]]
            total_contained += len(members)
        orphans = len(content) - total_contained
        # Allow some orphans for templates with intentional uncontained nodes
        test(f"{tmpl}: group containment ({total_contained}/{len(content)} contained)",
             orphans == 0 or tmpl in ["dashboard"],
             f"{orphans} nodes outside all groups" if orphans > 0 else "")


def test_layout(output_dir):
    """Test all 6 layout algorithms."""
    print("\n=== LAYOUT ALGORITHMS ===")

    # Create a test canvas with mixed nodes and edges
    test_canvas = {
        "nodes": [
            {"id": "zone-a", "type": "group", "label": "Zone A", "x": 0, "y": 0, "width": 800, "height": 600, "color": "4"},
            {"id": "t1", "type": "text", "text": "# Root", "x": 0, "y": 0, "width": 200, "height": 80},
            {"id": "t2", "type": "text", "text": "Child A", "x": 0, "y": 0, "width": 200, "height": 120},
            {"id": "t3", "type": "text", "text": "Child B", "x": 0, "y": 0, "width": 300, "height": 60},
            {"id": "t4", "type": "text", "text": "Grandchild", "x": 0, "y": 0, "width": 200, "height": 200},
            {"id": "f1", "type": "file", "file": "test.png", "x": 0, "y": 0, "width": 420, "height": 236},
            {"id": "orphan", "type": "text", "text": "Disconnected", "x": 0, "y": 0, "width": 200, "height": 80},
        ],
        "edges": [
            {"id": "e1", "fromNode": "t1", "toNode": "t2"},
            {"id": "e2", "fromNode": "t1", "toNode": "t3"},
            {"id": "e3", "fromNode": "t2", "toNode": "t4"},
        ],
    }

    for algo in ["auto", "grid", "dagre", "radial", "force", "linear"]:
        canvas_path = output_dir / f"layout-{algo}.canvas"
        canvas_path.write_text(json.dumps(test_canvas, indent=2))

        extra_args = []
        if algo == "dagre":
            extra_args = ["--direction", "LR"]
        elif algo == "linear":
            extra_args = ["--axis", "vertical"]

        ec, stdout, stderr = run_script("canvas_layout.py", [str(canvas_path), algo] + extra_args)
        if ec == 0:
            result = json.loads(stdout)
            test(f"{algo}: layout success", result.get("success"), stderr)
            test(f"{algo}: nodes moved", result.get("nodes_moved", 0) > 0, f"moved={result.get('nodes_moved')}")
            test(f"{algo}: groups preserved", result.get("groups_preserved", 0) == 1)
        else:
            test(f"{algo}: layout", False, stderr.strip())

        # Validate the result
        ec2, stdout2, _ = run_script("canvas_validate.py", [str(canvas_path)])
        result2 = json.loads(stdout2)
        overlaps = [w for w in result2.get("warnings", []) if "overlap" in w.lower()]
        test(f"{algo}: valid after layout", result2.get("valid", False))
        test(f"{algo}: no overlaps after layout", len(overlaps) == 0,
             overlaps[0][:60] if overlaps else "")

    # Test dagre all 4 directions
    print("\n=== DAGRE DIRECTIONS ===")
    for direction in ["TB", "LR", "BT", "RL"]:
        canvas_path = output_dir / f"dagre-{direction}.canvas"
        canvas_path.write_text(json.dumps(test_canvas, indent=2))
        ec, stdout, _ = run_script("canvas_layout.py", [str(canvas_path), "dagre", "--direction", direction])
        result = json.loads(stdout)
        test(f"dagre {direction}", result.get("success"))

    # Test dry-run
    print("\n=== DRY RUN ===")
    canvas_path = output_dir / "dry-run.canvas"
    canvas_path.write_text(json.dumps(test_canvas, indent=2))
    original = canvas_path.read_text()
    run_script("canvas_layout.py", [str(canvas_path), "grid", "--dry-run"])
    test("dry-run: file unchanged", canvas_path.read_text() == original)

    # Test backup guard
    print("\n=== BACKUP GUARD ===")
    canvas_path = output_dir / "backup-test.canvas"
    canvas_path.write_text(json.dumps(test_canvas, indent=2))
    run_script("canvas_layout.py", [str(canvas_path), "grid"])
    bak1 = Path(str(canvas_path) + ".bak")
    test("backup: .bak created", bak1.exists())
    run_script("canvas_layout.py", [str(canvas_path), "dagre"])
    bak2 = Path(str(canvas_path) + ".bak2")
    test("backup: .bak2 created (guard)", bak2.exists())


def test_validation(output_dir):
    """Test all validator error/warning paths."""
    print("\n=== VALIDATION ERROR DETECTION ===")

    error_cases = {
        "invalid-json": "{not valid}",
        "missing-id": json.dumps({"nodes": [{"type": "text", "text": "hi", "x": 0, "y": 0, "width": 200, "height": 100}], "edges": []}),
        "missing-type": json.dumps({"nodes": [{"id": "a", "text": "hi", "x": 0, "y": 0, "width": 200, "height": 100}], "edges": []}),
        "dup-node-id": json.dumps({"nodes": [
            {"id": "a", "type": "text", "text": "1", "x": 0, "y": 0, "width": 200, "height": 100},
            {"id": "a", "type": "text", "text": "2", "x": 0, "y": 200, "width": 200, "height": 100}
        ], "edges": []}),
        "dup-edge-id": json.dumps({"nodes": [
            {"id": "a", "type": "text", "text": "x", "x": 0, "y": 0, "width": 200, "height": 100}
        ], "edges": [
            {"id": "e1", "fromNode": "a", "toNode": "a"},
            {"id": "e1", "fromNode": "a", "toNode": "a"}
        ]}),
        "abs-path": json.dumps({"nodes": [{"id": "a", "type": "file", "file": "/home/user/img.png", "x": 0, "y": 0, "width": 200, "height": 100}], "edges": []}),
        "file-missing": json.dumps({"nodes": [{"id": "a", "type": "file", "x": 0, "y": 0, "width": 200, "height": 100}], "edges": []}),
        "link-missing-url": json.dumps({"nodes": [{"id": "a", "type": "link", "x": 0, "y": 0, "width": 200, "height": 100}], "edges": []}),
    }

    for name, content in error_cases.items():
        path = output_dir / f"val-{name}.canvas"
        path.write_text(content)
        ec, stdout, _ = run_script("canvas_validate.py", [str(path)])
        try:
            result = json.loads(stdout)
            test(f"error: {name} → valid=False", not result.get("valid", True))
        except json.JSONDecodeError:
            test(f"error: {name}", False, "validator crashed")

    print("\n=== VALIDATION WARNING DETECTION ===")
    warning_cases = {
        "bad-url": json.dumps({"nodes": [{"id": "a", "type": "link", "url": "javascript:x", "x": 0, "y": 0, "width": 200, "height": 100}], "edges": []}),
        "empty-text": json.dumps({"nodes": [{"id": "a", "type": "text", "text": "", "x": 0, "y": 0, "width": 200, "height": 100}], "edges": []}),
        "color-int": json.dumps({"nodes": [{"id": "a", "type": "text", "text": "x", "x": 0, "y": 0, "width": 200, "height": 100, "color": 3}], "edges": []}),
        "grid-misalign": json.dumps({"nodes": [{"id": "a", "type": "text", "text": "x", "x": 13, "y": 27, "width": 201, "height": 99}], "edges": []}),
        "z-index-bad": json.dumps({"nodes": [
            {"id": "a", "type": "text", "text": "x", "x": 0, "y": 0, "width": 200, "height": 100},
            {"id": "z", "type": "group", "label": "G", "x": 0, "y": 0, "width": 500, "height": 300}
        ], "edges": []}),
        "orphan-edge": json.dumps({"nodes": [{"id": "a", "type": "text", "text": "x", "x": 0, "y": 0, "width": 200, "height": 100}], "edges": [{"id": "e1", "fromNode": "missing", "toNode": "a"}]}),
        "overlap": json.dumps({"nodes": [
            {"id": "a", "type": "text", "text": "1", "x": 0, "y": 0, "width": 200, "height": 200},
            {"id": "b", "type": "text", "text": "2", "x": 50, "y": 50, "width": 200, "height": 200}
        ], "edges": []}),
    }

    for name, content in warning_cases.items():
        path = output_dir / f"val-{name}.canvas"
        path.write_text(content)
        ec, stdout, _ = run_script("canvas_validate.py", [str(path)])
        result = json.loads(stdout)
        has_warnings = len(result.get("warnings", [])) > 0
        test(f"warning: {name} detected", has_warnings,
             f"warnings={result.get('warnings', [])}" if not has_warnings else "")

    # Test --fix flag
    print("\n=== --fix FLAG ===")
    path = output_dir / "val-fixable.canvas"
    path.write_text(json.dumps({"nodes": [{"id": "a", "type": "text", "text": "x", "x": 13, "y": 27, "width": 201, "height": 99, "color": 3}], "edges": []}))
    run_script("canvas_validate.py", [str(path), "--fix"])
    _, stdout2, _ = run_script("canvas_validate.py", [str(path)])
    result2 = json.loads(stdout2)
    test("--fix: grid alignment fixed", len([w for w in result2.get("warnings", []) if "grid" in w]) == 0)

    # Test edge cases
    print("\n=== EDGE CASES ===")
    # Empty canvas
    path = output_dir / "val-empty.canvas"
    path.write_text('{"nodes":[],"edges":[]}')
    _, stdout, _ = run_script("canvas_validate.py", [str(path)])
    test("empty canvas: valid", json.loads(stdout).get("valid"))

    # 120 nodes (warning threshold)
    nodes = [{"id": f"n{i}", "type": "text", "text": f"N{i}", "x": (i%10)*220, "y": (i//10)*120, "width": 200, "height": 100} for i in range(120)]
    path = output_dir / "val-120nodes.canvas"
    path.write_text(json.dumps({"nodes": nodes, "edges": []}))
    _, stdout, _ = run_script("canvas_validate.py", [str(path)])
    result = json.loads(stdout)
    has_warn = any("threshold" in w or "exceeds" in w for w in result.get("warnings", []))
    test("120 nodes: warning triggered", has_warn)

    # 250 nodes (error threshold)
    nodes250 = [{"id": f"n{i}", "type": "text", "text": f"N{i}", "x": (i%10)*220, "y": (i//10)*120, "width": 200, "height": 100} for i in range(250)]
    path = output_dir / "val-250nodes.canvas"
    path.write_text(json.dumps({"nodes": nodes250, "edges": []}))
    _, stdout, _ = run_script("canvas_validate.py", [str(path)])
    test("250 nodes: error triggered", not json.loads(stdout).get("valid"))

    # File not found
    ec, _, _ = run_script("canvas_validate.py", ["/tmp/nonexistent-canvas.canvas"])
    test("file not found: exit code 2", ec == 2)


def test_color_params(output_dir):
    """Test color parameter handling (BUG 1 fix)."""
    print("\n=== COLOR PARAMETER FIX ===")
    path = output_dir / "color-test.canvas"
    ec, stdout, stderr = run_script("canvas_template.py", [
        "dashboard", str(path),
        "--param", "title=Color Test",
        "--param", "color_title=1",
        "--param", "color_body=2",
        "--param", "color_accent=3",
    ])
    test("color as int: no crash", ec == 0, stderr.strip() if ec != 0 else "")
    if ec == 0 and path.exists():
        data = json.loads(path.read_text())
        colors = {n.get("color") for n in data["nodes"] if n.get("color")}
        all_strings = all(isinstance(n.get("color"), str) for n in data["nodes"] if n.get("color"))
        test("color values are strings", all_strings)
        test("custom colors applied", colors == {"1", "2", "3"}, f"got {colors}")


def main():
    parser = argparse.ArgumentParser(description="Test suite for claude-canvas")
    parser.add_argument("--output-dir", default=None, help="Directory for test outputs")
    args = parser.parse_args()

    if args.output_dir:
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
    else:
        output_dir = Path(tempfile.mkdtemp(prefix="canvas-test-"))

    print(f"claude-canvas Test Suite")
    print(f"Output: {output_dir}")
    print(f"{'='*60}")

    test_templates(output_dir)
    test_layout(output_dir)
    test_validation(output_dir)
    test_color_params(output_dir)

    print(f"\n{'='*60}")
    print(f"Results: {results['pass']} passed, {results['fail']} failed, {results['warn']} warnings")
    total = results["pass"] + results["fail"]
    pct = round(results["pass"] / max(total, 1) * 100)
    print(f"Score: {pct}% ({results['pass']}/{total})")

    sys.exit(0 if results["fail"] == 0 else 1)


if __name__ == "__main__":
    main()
