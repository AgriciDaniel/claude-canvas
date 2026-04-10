---
name: canvas-create
description: >
  Create new Obsidian Canvas files — blank with a starter structure, or from
  one of 12 template archetypes (presentation, flowchart, mind-map, gallery,
  dashboard, storyboard, knowledge-graph, mood-board, timeline, comparison,
  kanban, project-brief). Handles directory creation, slug generation, and
  starter zone setup.
  Triggers on: canvas create, create canvas, new canvas, canvas new, start canvas.
user-invocable: false
---

# canvas-create: Create New Canvases

---

## Operations

### Blank Canvas (`/canvas create [name]`)

1. Slugify the name: lowercase, spaces to hyphens, strip special chars.
2. Determine canvas directory (see canvas orchestrator for context detection).
3. Create `[canvas_dir]/[slug].canvas` with starter structure:

```json
{
  "nodes": [
    {
      "id": "zone-default",
      "type": "group",
      "label": "General",
      "x": -400, "y": -140, "width": 800, "height": 400, "color": "4"
    },
    {
      "id": "title",
      "type": "text",
      "text": "# [Name]\n\nDrop images, PDFs, and notes here.",
      "x": -400, "y": -300, "width": 400, "height": 120, "color": "6"
    }
  ],
  "edges": []
}
```

Note: Groups MUST come before content nodes in the array (z-index ordering — groups render behind content).

4. Report: "Created [canvas_dir]/[slug].canvas. Open it in Obsidian to view."

### Templated Canvas (`/canvas create [name] from [template]`)

1. Validate template name against the 12 archetypes.
2. If no template name given or unclear, show available templates:

```
presentation   — Slide deck (1200x675, Advanced Canvas)
flowchart      — Process flow (Sugiyama/dagre layout)
mind-map       — Radial center-out expansion
gallery        — Grid of image nodes
dashboard      — Metric cards + charts + zones
storyboard     — Linear scene cards + script annotations
knowledge-graph — Force-directed entity map
mood-board     — Asymmetric image grid
timeline       — Horizontal event sequence
comparison     — Side-by-side columns
kanban         — Column zones (Todo/Doing/Done)
project-brief  — Hero zone + objectives + deliverables
```

3. Ask the user for template-specific parameters (title, number of items, color scheme).
4. Delegate to canvas-template skill for instantiation.
5. **MANDATORY: Replace ALL placeholder text** in every node with real, relevant content based on the title and topic. This is not optional:
   - Read the generated canvas JSON
   - For each text node, replace generic text ("Describe this step", "YYYY-MM-DD", "Value: 0") with real content relevant to the canvas title
   - Use the Edit tool to update each node's `text` field
   - This is the difference between a skeleton and a finished canvas
6. Run `python3 scripts/canvas_validate.py <path>` to verify validity.
7. Report the created canvas with node/zone counts.

---

## Slug Generation

```python
import re
def slugify(name):
    slug = name.lower().strip()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'[\s]+', '-', slug)
    slug = re.sub(r'-+', '-', slug)
    return slug.strip('-')
```

---

## Directory Rules

- Vault mode (`wiki/canvases/` exists): create there, media to `_attachments/images/canvas/`
- Standalone mode: create in `.canvases/`, media to `.canvases/assets/`
- Create the directory if it doesn't exist.
- Never overwrite an existing canvas without asking the user.
