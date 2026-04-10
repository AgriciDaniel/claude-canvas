# Template Catalog

12 canvas archetype templates for common visual patterns. Each produces a ready-to-use `.canvas` file with proper layout, zones, and placeholder content.

Run via: `python3 scripts/canvas_template.py <template> <output> --param key=value`
List all: `python3 scripts/canvas_template.py --list`

---

## Archetypes

### presentation
**Layout**: linear-vertical | **Slides**: 1200x675 groups connected by edges
**Use**: Slide decks for Advanced Canvas plugin (arrow-key navigation)
**Params**: `slide_count` (default 6)
**Next step**: Add content to each slide, generate hero images with `/canvas add banana`

### flowchart
**Layout**: linear-vertical → **auto-applies dagre** after instantiation | **Nodes**: Sequential text cards with edges
**Use**: Process documentation, decision flows
**Params**: `step_count` (default 5)
**Next step**: Edit step text to describe your actual process

### mind-map
**Layout**: grid → **auto-applies radial** after instantiation | **Nodes**: Center + branch cards
**Use**: Brainstorming, idea exploration, concept mapping
**Params**: `branch_count` (default 5)
**Next step**: Edit branches, add sub-branches, run `/canvas layout radial --center [center-id]`

### gallery
**Layout**: grid | **Nodes**: Image placeholder text cards in a title zone
**Use**: Image showcases, screenshot collections, visual portfolios
**Params**: `image_count` (default 9), `columns` (default 3)
**Next step**: Replace placeholders with `/canvas add image` or `/canvas add banana`

### dashboard
**Layout**: grid | **Nodes**: Header + metrics zone + metric cards + status zone
**Use**: Project status boards, KPI tracking, monitoring views
**Params**: `metric_count` (default 4)
**Next step**: Update metric values, add charts with `/canvas add svg` or `/canvas add mermaid`

### storyboard
**Layout**: linear-horizontal | **Nodes**: Scene cards with visual/audio/duration fields
**Use**: Video planning, animation sequences, narrative design
**Params**: `scene_count` (default 6)
**Next step**: Fill in scene details, add reference images with `/canvas add image`

### knowledge-graph
**Layout**: grid → **auto-applies force** after instantiation | **Nodes**: Entity cards
**Use**: Concept mapping, entity relationships, domain modeling
**Params**: `entity_count` (default 8)
**Next step**: Edit entities, add edges with `/canvas connect`, run `/canvas layout force`

### mood-board
**Layout**: grid | **Nodes**: Title card + inspiration zone + image placeholders
**Use**: Creative direction, design inspiration, aesthetic exploration
**Params**: `image_count` (default 8)
**Next step**: Replace placeholders with images via `/canvas add banana` for AI generation

### timeline
**Layout**: linear-horizontal | **Nodes**: Event cards with date/description fields
**Use**: Project timelines, historical events, release schedules
**Params**: `event_count` (default 6)
**Next step**: Fill in dates and descriptions, add milestone markers

### comparison
**Layout**: grid | **Nodes**: Two option zones + criteria cards
**Use**: Feature comparisons, decision analysis, A/B evaluation
**Params**: `criteria_count` (default 4)
**Next step**: Fill in criteria for each option, add summary/winner card

### kanban
**Layout**: grid | **Nodes**: Todo/Doing/Done zones + task cards
**Use**: Task management, sprint boards, workflow tracking
**Params**: `cards_per_column` (default 3)
**Next step**: Add task cards with `/canvas add text`, drag between columns in Obsidian

### project-brief
**Layout**: linear-vertical | **Nodes**: Hero zone + objectives + deliverables zones
**Use**: Project kickoff, scope documents, client briefs
**Params**: `objective_count` (default 3)
**Next step**: Fill in project details, add timeline with `/canvas add mermaid` gantt chart

---

## Common Parameters

All templates accept:

| Parameter | Type | Description |
|-----------|------|-------------|
| `title` | string | Canvas title (replaces `$title` in templates) |
| `color_title` | `"1"`-`"6"` | Color for title/header elements (default: `"6"` purple) |
| `color_body` | `"1"`-`"6"` | Color for body content zones (default: `"4"` green) |
| `color_accent` | `"1"`-`"6"` | Color for accent/highlight elements (default: `"5"` cyan) |

---

## Creating Custom Templates

Save any canvas as a template by extracting its structure into a JSON file in `templates/`:

```json
{
  "name": "Custom Template",
  "description": "What this template is for",
  "layout": "grid|linear-vertical|linear-horizontal",
  "defaults": {
    "item_count": 5,
    "color_title": "6",
    "color_body": "4",
    "color_accent": "5"
  },
  "node_templates": [
    {
      "role": "item",
      "type": "text",
      "repeat": "$item_count",
      "repeat_default": 5,
      "text": "## Item {n}",
      "width": 300,
      "height": 120,
      "color": "$color_body"
    }
  ],
  "edge_templates": [
    {
      "from_role": "item",
      "to_role": "item",
      "pattern": "sequential"
    }
  ]
}
```

Template variables: `$title`, `$color_title`, `$color_body`, `$color_accent`, `{n}` (repeat index).
Repeat values: `"$param_name"` references a template parameter, `"repeat_default"` is the fallback.
Edge patterns: `"sequential"` (n[i]→n[i+1]) or `"broadcast"` (n[0]→all others).
