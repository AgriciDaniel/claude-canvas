# claude-canvas — AI-Orchestrated Visual Production

This is a Claude Code plugin for creating, populating, and laying out Obsidian Canvas files with AI assistance.

## What It Does

Claude acts as Creative Director for Obsidian Canvas. Describe what you want — a presentation, mood board, flowchart, or knowledge graph — and get a fully populated, professionally laid-out canvas with AI-generated images, diagrams, and text.

## Directory Structure

```
skills/
  canvas/              Main orchestrator — routes commands to sub-skills
  canvas-create/       Create blank or templated canvases
  canvas-populate/     Add nodes, edges, zones to existing canvases
  canvas-layout/       Re-layout with 6 algorithms
  canvas-present/      Build presentation-mode canvases for Advanced Canvas
  canvas-generate/     AI-orchestrated full canvas generation (flagship)
  canvas-template/     Browse and instantiate 12 archetype templates
  canvas-export/       Export canvas to PNG/SVG/PDF
agents/                3 sub-agents: layout, media, composer
scripts/               Python CLI tools (validate, layout, template)
templates/             12 JSON Canvas archetype templates
bin/                   Setup script for optional dependencies
```

## Quick Commands

| You say | Claude does |
|---------|-------------|
| `/canvas` | List canvases with node counts |
| `/canvas create my-project` | Create a new canvas |
| `/canvas add image photo.png` | Add an image node |
| `/canvas add banana "hero image"` | Generate AI image, add to canvas |
| `/canvas layout dagre` | Re-layout with hierarchical algorithm |
| `/canvas present "Q3 Review"` | Build a presentation canvas |
| `/canvas generate "mood board for game"` | Full AI-orchestrated generation |
| `/canvas template list` | Browse 12 archetypes |

## Canvas Location

- If `wiki/canvases/` exists (claude-obsidian vault): uses that
- Otherwise: creates `.canvases/` in the current project directory

## Integration

Works with `/banana` (AI images), `/svg` (diagrams), `/claude-gif-*` (animations) when installed. Gracefully degrades if not available.
