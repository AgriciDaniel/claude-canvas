---
name: canvas-layout
description: >
  Re-layout existing Obsidian Canvas nodes using 6 spatial algorithms: grid
  (galleries, mood boards), dagre (flowcharts, org charts), radial (mind maps),
  force-directed (knowledge graphs), linear (timelines), and auto-detect.
  Preserves group membership, snaps to 20px grid, refits zones around content.
  Triggers on: canvas layout, re-layout canvas, arrange canvas, auto-layout,
  organize canvas, fix canvas layout, canvas grid, canvas dagre.
user-invocable: false
---

# canvas-layout: Re-Layout Canvas Nodes

Read `../canvas/references/layout-algorithms.md` for algorithm details and selection guide.
Read `../canvas/references/performance-guide.md` for node limits.

---

## Workflow

1. **Identify target canvas**: Use the active canvas or ask which one (`/canvas list` to show options).
2. **Select algorithm**: Use the user-specified algorithm, or run `auto` detection.
3. **Confirm before applying**: Show what will happen:
   "Will apply [algorithm] layout to [canvas] ([N] nodes, [M] groups). Create backup? [Y/n]"
4. **Run the layout script**:
   ```bash
   python3 scripts/canvas_layout.py [canvas_path] [algorithm] [options]
   ```
5. **Report results**: "Moved [N] of [M] nodes. [G] groups refitted. Backup at [path].bak"
6. **Validate**: Run `python3 scripts/canvas_validate.py [canvas_path]` to confirm valid output.

---

## Algorithm Selection

When the user says `/canvas layout auto` or doesn't specify an algorithm, use the auto-detection in the script. It analyzes edge density, node types, and connection patterns.

For explicit requests, map user intent to algorithm:

| User says | Algorithm | Options |
|-----------|-----------|---------|
| "organize these images" | grid | `--sort-by type` |
| "make a grid" | grid | |
| "flowchart layout" | dagre | `--direction TB` |
| "left to right flow" | dagre | `--direction LR` |
| "mind map layout" | radial | |
| "expand from [node]" | radial | `--center [node-id]` |
| "untangle this" | force | |
| "spread out the nodes" | force | |
| "make a timeline" | linear | `--axis horizontal` |
| "vertical sequence" | linear | `--axis vertical` |
| "auto-layout" | auto | |
| "fix the layout" | auto | |

---

## Options Forwarding

Pass algorithm-specific options to the script:

- **grid**: `--columns N` (override auto-detection), `--sort-by type|size`
- **dagre**: `--direction TB|LR|BT|RL`
- **radial**: `--center node-id` (override auto-detection of hub node)
- **force**: `--iterations N` (default 100, reduce to 50 for 50+ nodes)
- **linear**: `--axis horizontal|vertical`

Add `--dry-run` to preview without writing.

---

## For Complex Layouts (30+ Nodes)

When a canvas has more than 30 nodes, dispatch the `canvas-layout` agent instead of running the script directly. The agent can:

- Analyze the canvas content to choose sub-groups for different algorithms
- Split large canvases into zone-by-zone layouts
- Handle edge crossing minimization that the basic dagre doesn't cover
- Refine positions after the algorithm runs for better visual balance

---

## Edge Cases

- **Empty canvas**: Report "No nodes to layout" and skip.
- **Single node**: Center it at (0, 0) and skip.
- **No edges + dagre requested**: Warn "dagre works best with edges. Using grid instead." Fall back to grid.
- **100+ nodes**: Warn about performance. Suggest splitting into sub-canvases.
- **Backup conflict**: If `.bak` already exists, use `.bak2`, `.bak3`, etc.
