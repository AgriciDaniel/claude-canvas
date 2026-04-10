---
description: AI-orchestrated visual canvas production — create, populate, layout, present, generate, and export Obsidian canvases
---

Read the canvas skill. Then execute the requested operation.

Usage:
- `/canvas` — show status and list canvases
- `/canvas create [name]` — create a new canvas (blank or from template)
- `/canvas add [type] [content]` — add a node (image, text, pdf, note, link, mermaid, svg, gif, banana)
- `/canvas zone [name] [color]` — create a labeled zone
- `/canvas connect [from] [to] [label]` — add an edge between nodes
- `/canvas from banana` — import recent AI-generated images
- `/canvas layout [algorithm]` — re-layout nodes (auto, grid, dagre, radial, force, linear)
- `/canvas present [topic]` — build a presentation canvas
- `/canvas generate [description]` — AI-orchestrated full generation
- `/canvas template list` — browse 12 archetypes
- `/canvas export png [path]` — export to image
- `/canvas list` — list all canvases with node counts

If no canvas directory exists, create `.canvases/` in the current project.
If `wiki/canvases/` exists (claude-obsidian vault), use that instead.
