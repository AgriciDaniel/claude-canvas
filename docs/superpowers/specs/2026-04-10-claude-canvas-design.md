# claude-canvas Design Spec

**Date**: 2026-04-10
**Author**: AgriciDaniel
**Status**: Approved

## Problem

The existing `/canvas` skill in `claude-obsidian` (v1.4.1) is a passive reference board — users manually add images, text, PDFs to wiki canvases one node at a time. There is no intelligent layout, no AI-generated content, no template system, no presentation mode, and no batch generation. Canvas creation is tedious and results are visually unorganized.

## Solution

Build `claude-canvas` — a standalone Claude Code plugin that transforms Obsidian Canvas into an AI-orchestrated visual production system. Claude acts as Creative Director, dispatching sub-agents for image generation, SVG diagrams, GIF creation, and intelligent spatial layout. Users describe what they want ("create a mood board for a cyberpunk game") and get a fully populated, professionally laid-out canvas.

## Architecture Decision: Standalone Plugin

**Choice**: New repo `claude-canvas` at `~/Desktop/claude-canvas/`, separate from `claude-obsidian`.

**Reasoning**:
- Canvas orchestration is substantial enough for its own plugin (7 sub-skills, 3 agents, 12 templates)
- Works outside Obsidian vaults (blog projects, ad campaigns, standalone presentations)
- Avoids bloating claude-obsidian beyond its "knowledge companion" mission
- Independent versioning, discovery, and community
- Detects vault context when available, falls back to local `.canvases/` directory

## Plugin Structure

```
~/Desktop/claude-canvas/
├── .claude-plugin/plugin.json         # 8 fields, 13 keywords
├── CLAUDE.md                          # ~65 lines: summary + skill table + usage
├── README.md                          # Hero GIF, 3 install paths, command table
├── LICENSE                            # MIT
├── hooks/hooks.json                   # PostToolUse: auto-validate canvas writes
├── commands/canvas.md                 # Entry point: "Read the canvas skill..."
├── skills/
│   ├── canvas/                        # Main orchestrator (Tier 4)
│   │   ├── SKILL.md                   # Routes commands, detects context (~250 lines)
│   │   └── references/
│   │       ├── canvas-spec.md         # JSON Canvas 1.0 (migrated + enhanced)
│   │       ├── layout-algorithms.md   # 6 algorithms with pseudocode
│   │       ├── presentation-spec.md   # Advanced Canvas slides (1200x675)
│   │       ├── performance-guide.md   # <200 nodes, GIF lag, 20px grid
│   │       ├── template-catalog.md    # 12 archetypes with parameters
│   │       ├── mermaid-patterns.md    # Native Mermaid in text nodes
│   │       └── media-guide.md         # Image/GIF/SVG integration
│   ├── canvas-create/SKILL.md         # Create blank or templated canvases
│   ├── canvas-populate/SKILL.md       # Add nodes, edges, zones
│   ├── canvas-layout/SKILL.md         # Re-layout with 6 algorithms
│   ├── canvas-present/SKILL.md        # Presentation-mode canvas builder
│   ├── canvas-generate/SKILL.md       # AI-orchestrated full generation (flagship)
│   ├── canvas-template/SKILL.md       # Browse & instantiate archetypes
│   └── canvas-export/SKILL.md         # Export to PNG/SVG/PDF
├── agents/
│   ├── canvas-layout.md               # Spatial positioning specialist
│   ├── canvas-media.md                # Media dispatcher (banana/svg/gif)
│   └── canvas-composer.md             # Content writer for text nodes
├── scripts/
│   ├── canvas_layout.py               # 6 layout algorithms (argparse, JSON)
│   ├── canvas_validate.py             # Validate canvas JSON (argparse, JSON)
│   └── canvas_template.py             # Template instantiation (argparse, JSON)
├── templates/*.json                   # 12 archetype templates
└── bin/setup.sh                       # Install Python deps
```

## Naming Convention

Repo name: `claude-canvas` (repo names CAN have "claude-").
Skill names: `canvas`, `canvas-create`, `canvas-layout`, etc. (skill names CANNOT have "claude-" per Agent Skills standard).

## Command Interface

| Command | Sub-skill | Description |
|---------|-----------|-------------|
| `/canvas` | canvas (inline) | Status: list canvases, node counts |
| `/canvas create [name]` | canvas-create | Blank canvas or from template |
| `/canvas add [type] [content]` | canvas-populate | Add image/text/pdf/note/link/mermaid/svg/gif/banana |
| `/canvas zone [name] [color]` | canvas-populate | Add group node |
| `/canvas connect [from] [to]` | canvas-populate | Add edge |
| `/canvas from banana` | canvas-populate | Import recent AI images |
| `/canvas layout [algorithm]` | canvas-layout | Re-layout (auto/grid/dagre/radial/force/linear) |
| `/canvas present [topic]` | canvas-present | Presentation (1200x675 slides) |
| `/canvas generate [desc]` | canvas-generate | AI-orchestrated full generation |
| `/canvas template list` | canvas-template | Browse 12 archetypes |
| `/canvas export png` | canvas-export | Export to PNG/SVG/PDF |

## Design Constraints

1. **Skill names cannot contain "claude" or "anthropic"** (Agent Skills standard)
2. **<200 node limit** — validation warns at 100, errors at 200
3. **20px grid snapping** — all coordinates aligned to multiples of 20
4. **Z-index = array order** — groups first (background), content after (foreground)
5. **Edge sides omitted by default** — let Obsidian auto-route
6. **Presentation slides = 1200x675** group nodes connected by edges
7. **Vault-aware, not vault-dependent** — detects `wiki/canvases/` or uses `.canvases/`
8. **Plugin canvas supersedes standalone** — installed plugin takes priority over `~/.claude/skills/canvas/`

## Scripts Convention

Each script: `#!/usr/bin/env python3`, docstring with usage, argparse CLI, JSON stdout, exit codes (0=ok, 1=error, 2=blocking), no hardcoded paths, stdlib-only core (optional `igraph` for layout).

## Agent Convention

Frontmatter: `name` (kebab-case), `description` (with `<example>` blocks), `model: sonnet`, `maxTurns: 20-30`, explicit `tools` list. Body = system prompt in second person.

## Template System

12 JSON archetype files with placeholder nodes (`$title`, `$slide_count`, `$colors.*`, `repeat: N`). Each specifies its layout algorithm. Instantiated by `canvas_template.py`.

Archetypes: presentation, flowchart, mind-map, gallery, dashboard, storyboard, knowledge-graph, mood-board, timeline, comparison, kanban, project-brief.

## Integration Points

| Skill | How | When |
|-------|-----|------|
| `/banana` | nanobanana-mcp image gen | `/canvas add banana`, generate mode |
| `/svg` | Diagram/chart/icon gen | `/canvas add svg`, flowchart templates |
| `/claude-gif-*` | GIF gen/edit | `/canvas add gif`, storyboard templates |
| `mcpvault` MCP | Read wiki notes | `/canvas present from [notes]` |

## Implementation Phases

1. **Foundation** — plugin scaffold, canvas CRUD, create + populate skills, validate script
2. **Layout Engine** — 6 algorithms, layout skill, layout agent
3. **Templates** — 12 archetypes, template engine, template skill
4. **Presentation** — Advanced Canvas slides, present skill
5. **AI Generation** — generate skill, media + composer agents
6. **Export + Polish** — export skill, hooks, setup script

## Verification

After each phase: create test canvas, open in Obsidian, run `canvas_validate.py`, check <200 nodes, check 20px alignment, test both vault and standalone modes.

Final test: `/canvas generate "product launch presentation for a SaaS tool with AI-generated hero images"` → 6-8 slide canvas with images, text, layout, edge navigation.
