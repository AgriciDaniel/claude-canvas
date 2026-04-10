---
name: canvas
description: >
  AI-orchestrated visual production for Obsidian Canvas. Create presentations,
  flowcharts, mood boards, knowledge graphs, galleries, storyboards, timelines,
  dashboards, and more with intelligent layout and AI-generated content. Claude
  acts as Creative Director — dispatching sub-agents for image generation, SVG
  diagrams, GIF creation, and spatial layout. Supports 12 template archetypes,
  6 layout algorithms, and Advanced Canvas presentation mode.
  Triggers on: /canvas, create canvas, build canvas, make a presentation,
  visual board, mood board, flowchart canvas, storyboard, canvas from template,
  lay out canvas, export canvas, canvas layout, canvas generate, add to canvas,
  put this on the canvas, open canvas, canvas present, canvas template.
---

# canvas: AI-Orchestrated Visual Production

Claude acts as Creative Director for Obsidian Canvas. Describe what you want and get a fully populated, professionally laid-out `.canvas` file.

---

## Context Detection

Before any operation, determine the canvas directory:

1. If `wiki/canvases/` exists in the current directory or a parent: use it (claude-obsidian vault mode).
   - Media goes to `_attachments/images/canvas/`
2. Otherwise: use `.canvases/` in the current working directory (standalone mode).
   - Media goes to `.canvases/assets/`
3. Create the directory if it doesn't exist.

**Default canvas**: `[canvas_dir]/main.canvas`

---

## Command Routing

| Command | Sub-skill | Description |
|---------|-----------|-------------|
| `/canvas` (no args) | (inline) | Status: list canvases, node counts, zones |
| `/canvas create [name]` | canvas-create | Create blank or templated canvas |
| `/canvas create [name] from [template]` | canvas-create | Create from archetype |
| `/canvas add [type] [content]` | canvas-populate | Add node (image/text/pdf/note/link/mermaid/svg/gif/banana) |
| `/canvas zone [name] [color]` | canvas-populate | Add group node |
| `/canvas connect [from] [to] [label]` | canvas-populate | Add edge between nodes |
| `/canvas from banana` | canvas-populate | Import recent AI-generated images |
| `/canvas layout [algorithm]` | canvas-layout | Re-layout (auto/grid/dagre/radial/force/linear) |
| `/canvas present [topic]` | canvas-present | Build presentation canvas (1200x675 slides) |
| `/canvas present from [notes]` | canvas-present | Presentation from existing content |
| `/canvas generate [description]` | canvas-generate | AI-orchestrated full canvas generation |
| `/canvas template list` | canvas-template | Browse 12 archetypes |
| `/canvas template use [name]` | canvas-template | Instantiate a template |
| `/canvas export [format] [path]` | canvas-export | Export to PNG/SVG/PDF |
| `/canvas list` | (inline) | List all canvases with stats |

---

## Status / List (Inline Operations)

### `/canvas` (no args)

1. Detect canvas directory (vault or standalone).
2. Find default canvas (`main.canvas`).
3. If exists: read JSON, count nodes by type, list zone labels.
   Report: "Canvas has N nodes: X images, Y text, Z files. Zones: [list]"
4. If not exists: report "No canvas found. Run `/canvas create [name]` to start."

### `/canvas list`

1. Glob `[canvas_dir]/*.canvas`.
2. For each: read JSON, count nodes by type.
3. Report table:

```
main.canvas              14 nodes (8 images, 3 text, 2 file, 1 group)
design-ideas.canvas      42 nodes (30 images, 4 text, 8 groups)
```

---

## Key References

Read these references before performing canvas operations:

- `references/canvas-spec.md` — JSON Canvas 1.0 format, coordinate system, node types, edges, colors, sizing
- `references/performance-guide.md` — Node limits, GIF lag, SVG gotchas, 20px grid snapping

Additional references:
- `references/layout-algorithms.md` — 6 layout algorithms (canvas-layout)
- `references/template-catalog.md` — 12 archetypes (canvas-template)

- `references/presentation-spec.md` — Advanced Canvas slides (canvas-present)

- `references/mermaid-patterns.md` — Mermaid in text nodes (canvas-populate, canvas-generate)
- `references/media-guide.md` — Image/GIF/SVG integration (canvas-generate, canvas-populate)

---

## Auto-Positioning Algorithm

Used by canvas-populate to place new nodes. Read `references/canvas-spec.md` for the full coordinate system.

```python
def next_position(canvas_nodes, target_zone_label, new_w, new_h):
    # Find zone group node
    zone = next((n for n in canvas_nodes
                 if n.get('type') == 'group'
                 and n.get('label') == target_zone_label), None)

    if zone is None:
        # No zone: place below all content
        max_y = max((n['y'] + n.get('height', 0) for n in canvas_nodes), default=-140)
        return snap_grid(-400, max_y + 60)

    zx, zy = zone['x'], zone['y']
    zw, zh = zone['width'], zone['height']

    # Nodes inside this zone (exclude groups)
    inside = [n for n in canvas_nodes
              if n.get('type') != 'group'
              and zx <= n['x'] < zx + zw
              and zy <= n['y'] < zy + zh]

    if not inside:
        return snap_grid(zx + 20, zy + 20)

    # Find the bottom-most row: nodes whose bottom edge is closest to the zone bottom
    max_bottom = max(n['y'] + n.get('height', 0) for n in inside)
    # Nodes on the last row: those whose top y is within one row-height of the bottom
    last_row = [n for n in inside if n['y'] + n.get('height', 0) >= max_bottom - 20]
    if not last_row:
        last_row = inside  # fallback

    rightmost_x = max(n['x'] + n.get('width', 0) for n in last_row)
    next_x = rightmost_x + 40

    if next_x + new_w > zx + zw:
        # Overflow: new row below the current last row
        return snap_grid(zx + 20, max_bottom + 20)

    # Same row: align to top of the LAST row (not all nodes)
    current_row_y = min(n['y'] for n in last_row)
    return snap_grid(next_x, current_row_y)

def snap_grid(x, y, grid=20):
    return (round(x / grid) * grid, round(y / grid) * grid)
```

---

## ID Generation

Read the canvas JSON first. Collect all existing IDs. Never reuse one.

**Pattern**: `[type]-[content-slug]-[full-unix-timestamp]`

Use the full 10-digit Unix timestamp to avoid collisions in batch operations.

Examples: `img-cover-1744032823`, `text-note-1744032845`, `zone-branding-1744032901`

If a collision is detected (ID already exists), append `-2`, `-3`, etc.

---

## Canvas JSON Structure

The minimal valid canvas:

```json
{
  "nodes": [],
  "edges": []
}
```

**Z-index rule**: First node in the array renders at the bottom (background). Last node renders on top (foreground). Groups MUST come before their contained nodes so content renders in front of zone backgrounds.

**Grid snapping**: All x, y, width, height values should be multiples of 20.

**Node limit**: Warn the user if a canvas exceeds 100 nodes. Error if it exceeds 200.

---

## Quality Standards (MANDATORY)

Every canvas produced by any sub-skill MUST pass these checks before reporting success. These are not optional — they are the definition of "done."

### Content Quality
- **NO placeholder text** in any node. Replace ALL of these:
  - "Describe this step" → write a real step description relevant to the title
  - "YYYY-MM-DD" → use today's date or a realistic date
  - "Value: 0, Target: 100" → use realistic example values
  - "Content goes here" → write actual content matching the slide topic
  - "Define this entity" → write a real definition
  - "What happened" → write a real event description
- Every text node must contain **real, useful content** that a user can immediately understand
- Template instantiation is STEP 1 — writing real content into the nodes is STEP 2 (never skip it)

### Layout Quality
- **Minimum 80px horizontal gap** between adjacent content nodes
- **Minimum 60px vertical gap** between adjacent content nodes
- **Mind-map canvases** must have radial layout (run `canvas layout radial` after instantiation)
- **Knowledge-graph canvases** must have force layout (run `canvas layout force` after instantiation)
- **Flowchart canvases** should have dagre layout applied (run `canvas layout dagre` for proper hierarchy)
- **No overlapping nodes** — run `canvas_validate.py` to confirm

### Structural Quality
- Groups (zones) appear BEFORE content nodes in the array (z-index)
- All coordinates are multiples of 20 (grid snapping)
- Node count under 120 (warn at 100, error at 200)
- All file paths are vault-relative (no absolute paths)
- Edge IDs are unique, node IDs are unique

### Before Reporting Success
1. Run `python3 scripts/canvas_validate.py <path>` — must return `valid: true` with 0 errors
2. Visually scan the generated JSON — are there any "Describe this" or "YYYY-MM-DD" strings remaining?
3. If the canvas has groups, verify content nodes are inside their designated zones (center-point check)
4. If the archetype needs a specific layout (mind-map→radial, kg→force), verify it was applied

---

## Integration with Other Skills

**banana** (AI image generation):
- `/canvas add banana [prompt]` delegates to the banana skill, then adds the result as a file node.
- `/canvas from banana` reads `.recent-images.txt` or finds images modified in the last 10 minutes.
- If banana is not installed, report gracefully: "Install the banana skill for AI image generation."

**svg** (diagram/chart/icon generation):
- `/canvas add svg [description]` delegates to the svg skill, then adds the SVG as a file node.
- SVGs render as `<img>` in Obsidian — no interactivity. Must include `viewBox` for proper scaling.

**claude-gif-*** (GIF generation/editing):
- `/canvas add gif [description]` delegates to the gif skill, then adds as a file node.
- Performance warning: limit to 3 GIFs per canvas, cap dimensions at 480px width.

**Mermaid** (native in text nodes):
- Mermaid code blocks render natively in Obsidian text nodes. No external skill needed.
- Wrap in triple-backtick mermaid code fence inside a text node.
