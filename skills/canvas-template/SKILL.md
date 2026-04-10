---
name: canvas-template
description: >
  Browse and instantiate 12 canvas template archetypes: presentation, flowchart,
  mind-map, gallery, dashboard, storyboard, knowledge-graph, mood-board,
  timeline, comparison, kanban, project-brief. Each template generates a
  ready-to-use canvas with proper layout, zones, and placeholder content.
  Triggers on: canvas template, canvas template list, browse templates,
  canvas from template, use template, show archetypes.
user-invocable: false
---

# canvas-template: Template Browser & Instantiation

---

## Operations

### List Templates (`/canvas template list`)

Run the template script to list available archetypes:

```bash
python3 scripts/canvas_template.py --list
```

Present the results as a formatted table:

| Archetype | Layout | Description |
|-----------|--------|-------------|
| presentation | linear-vertical | Slide deck for Advanced Canvas (1200x675 slides) |
| flowchart | linear-vertical → auto dagre | Process flow with connected step nodes |
| mind-map | grid → auto radial | Radial expansion from central topic |
| gallery | grid | Image placeholder grid with title zone |
| dashboard | grid | Metric cards + status zones |
| storyboard | linear-horizontal | Scene cards for video planning |
| knowledge-graph | grid → auto force | Entity nodes for relationship mapping |
| mood-board | grid | Asymmetric image grid for creative direction |
| timeline | linear-horizontal | Horizontal event sequence |
| comparison | grid | Side-by-side columns for option analysis |
| kanban | grid | Todo/Doing/Done column board |
| project-brief | linear-vertical | Stacked zones for project kickoff |

### Instantiate Template (`/canvas template use [name]`)

1. Validate the template name against the 12 archetypes.
2. Ask for required parameters:
   - **title** (all templates): What's the canvas title?
   - Template-specific params (slide_count, step_count, image_count, etc.)
3. Determine output path (canvas directory detection from orchestrator).
4. Run instantiation:

```bash
python3 scripts/canvas_template.py [template] [output_path] --param title="[title]" --param [key]=[value]
```

5. Validate the output:

```bash
python3 scripts/canvas_validate.py [output_path]
```

6. **MANDATORY: Content Quality Gate** — Read the orchestrator's Quality Standards section. Before reporting:
   - Replace ALL placeholder text in every node with real content relevant to the title
   - Verify no "Describe this", "YYYY-MM-DD", "Value: 0", or "Content goes here" strings remain
   - Run `python3 scripts/canvas_validate.py` and confirm 0 errors, 0 overlap warnings
   - If the template has `post_layout` (mind-map→radial, knowledge-graph→force, flowchart→dagre), confirm the layout was applied
7. Report: "Created [name] canvas at [path] with [N] nodes, [E] edges, [G] groups."

---

## Template Parameters

Each template has defaults that can be overridden:

| Template | Key Parameters | Defaults |
|----------|---------------|----------|
| presentation | slide_count | 6 |
| flowchart | step_count | 5 |
| mind-map | branch_count | 5 |
| gallery | image_count, columns | 9, 3 |
| dashboard | metric_count | 4 |
| storyboard | scene_count | 6 |
| knowledge-graph | entity_count | 8 |
| mood-board | image_count | 8 |
| timeline | event_count | 6 |
| comparison | criteria_count | 4 |
| kanban | cards_per_column | 3 |
| project-brief | objective_count | 3 |

All templates accept `color_title`, `color_body`, `color_accent` to override the color scheme (values: `"1"`-`"6"`).

---

## Post-Instantiation

After creating a template canvas, suggest next steps based on the archetype:

- **presentation**: "Add content to each slide. Use `/canvas add banana` for hero images."
- **gallery/mood-board**: "Replace placeholder slots with `/canvas add image` or `/canvas add banana`."
- **flowchart**: "Edit step text. Run `/canvas layout dagre` to re-flow after changes."
- **mind-map**: "Edit branches. Run `/canvas layout radial` for proper expansion."
- **knowledge-graph**: "Add entities and edges. Run `/canvas layout force` to visualize relationships."
- **kanban**: "Add task cards with `/canvas add text`. Move between columns manually in Obsidian."
