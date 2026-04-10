---
name: canvas-generate
description: >
  AI-orchestrated full canvas generation. Given a description, detects the best
  archetype, generates content and visuals, instantiates a template, applies
  layout, and produces a complete canvas. The flagship command. Dispatches
  canvas-media and canvas-composer agents for parallel asset generation.
  Triggers on: canvas generate, generate canvas, create a visual board,
  build me a canvas, make a canvas about, canvas from description,
  auto-generate canvas, full canvas generation.
user-invocable: false
---

# canvas-generate: AI-Orchestrated Canvas Generation

The flagship command. Takes a high-level description and produces a complete, populated canvas.

Read `../canvas/references/template-catalog.md` for archetype descriptions.
Read `../canvas/references/media-guide.md` for image/SVG/GIF integration.
Read `../canvas/references/mermaid-patterns.md` for native diagram options.
Read `../canvas/references/performance-guide.md` for node limits.

---

## Pipeline

```
User: "/canvas generate [description]"
          │
          ▼
   1. Analyze description
          │
          ▼
   2. Detect archetype
          │
          ▼
   3. Plan content (what nodes, what media)
          │
          ▼
   4. Generate in parallel:
      ┌─────────────┬────────────────┐
      │ Composer     │ Media agent    │
      │ (text nodes) │ (images/SVGs)  │
      └──────┬──────┴───────┬────────┘
             │              │
             ▼              ▼
   5. Instantiate template with content
          │
          ▼
   6. Apply layout algorithm
          │
          ▼
   7. Validate + write
```

---

## Workflow

### Step 1: Analyze Description

Parse the user's description to extract:
- **Topic**: What is the canvas about?
- **Purpose**: What will it be used for? (presenting, planning, exploring, showcasing)
- **Content hints**: Any specific items, data, or requirements mentioned?
- **Visual requests**: Does the user want images, diagrams, or text-only?

### Step 2: Detect Archetype

Map the description to one of the 12 template archetypes:

| Keywords in description | Archetype |
|------------------------|-----------|
| "presentation", "slides", "deck", "present" | presentation |
| "flowchart", "process", "workflow", "steps" | flowchart |
| "mind map", "brainstorm", "ideas", "explore" | mind-map |
| "gallery", "images", "photos", "showcase" | gallery |
| "dashboard", "metrics", "KPIs", "status" | dashboard |
| "storyboard", "scenes", "video", "script" | storyboard |
| "knowledge graph", "entities", "relationships" | knowledge-graph |
| "mood board", "inspiration", "aesthetic", "vibe" | mood-board |
| "timeline", "events", "history", "milestones" | timeline |
| "comparison", "vs", "compare", "options" | comparison |
| "kanban", "tasks", "board", "sprint" | kanban |
| "brief", "kickoff", "project plan", "objectives" | project-brief |

If the archetype is ambiguous, ask the user to clarify.

### Step 3: Plan Content

Based on the archetype and description, plan:
- **Node count**: How many nodes does this canvas need? (respect <120 target)
- **Text content**: What text goes in each node?
- **Media assets**: What images, SVGs, or GIFs are needed?
- **Mermaid diagrams**: What data visualizations should be embedded as Mermaid?
- **Edges**: What connections exist between nodes?

### Step 4: Generate Content and Media

**For simple canvases** (text-only, <10 nodes): Generate content inline — no agents needed.

**For complex canvases** (media required or >10 nodes): Dispatch agents in parallel:

a. **Dispatch canvas-composer agent** with:
   - Archetype name
   - Topic description
   - Number of text nodes needed
   - Any source files for context

b. **Dispatch canvas-media agent** with (if media requested):
   - List of images/SVGs/GIFs needed
   - Prompt descriptions for each
   - Target dimensions

c. Wait for both agents to complete. Collect their JSON output.

### Step 5: Instantiate Template

Use the template engine to create the base canvas:

```bash
python3 scripts/canvas_template.py [archetype] [output_path] \
  --param title="[topic]" --param [archetype_param]=[count]
```

Then update each node's content with the composer agent's output using the Edit tool.

If the media agent generated images:
- Add each as a file node inside the appropriate zone/slide
- Use the auto-positioning algorithm or manual placement inside groups

### Step 6: Apply Layout

If the template's built-in layout is insufficient (e.g., mind-map needs radial, knowledge-graph needs force), apply the appropriate algorithm:

```bash
python3 scripts/canvas_layout.py [output_path] [algorithm]
```

### Step 7: Quality Gate (MANDATORY)

This is the most critical step. A canvas that passes validation but has placeholder text is a FAILURE.

1. **Content check**: Read every text node in the canvas. Search for these forbidden strings:
   - "Describe this" — replace with real content
   - "YYYY-MM-DD" — replace with real dates
   - "Content goes here" — replace with real content
   - "Value: 0" — replace with realistic values
   - "Define this entity" — replace with real definition
   - "What happened" — replace with real event
   If ANY are found, edit the canvas to replace them before proceeding.

2. **Layout check**: Verify the correct layout was applied:
   - Mind-map → radial layout (nodes should expand from center, not in a grid)
   - Knowledge-graph → force layout (nodes should be organically spread, not in a grid)
   - Flowchart → dagre layout (hierarchical top-down or left-right flow)
   If the layout looks wrong, run `python3 scripts/canvas_layout.py <path> <algorithm>`.

3. **Spacing check**: Run validation to catch overlaps:
   ```bash
   python3 scripts/canvas_validate.py [output_path]
   ```
   Must return `valid: true` with 0 errors and 0 overlap warnings.

4. **Visual scan**: Is this canvas something you'd be proud to show? Would a user open it and immediately understand it? If not, improve it.

Only after ALL four checks pass, report success.

---

## Examples

### Example 1: Text-Only Dashboard

User: `/canvas generate "project dashboard for mobile app launch"`

1. Archetype: dashboard
2. Plan: 4 metric cards (Downloads, DAU, Crashes, Rating), 1 status zone
3. Generate content inline (simple, text-only)
4. Instantiate: `python3 scripts/canvas_template.py dashboard output.canvas --param title="Mobile App Launch" --param metric_count=4`
5. Edit metric nodes with specific content
6. No layout change needed (grid is fine)
7. Validate and report

### Example 2: Mood Board with AI Images

User: `/canvas generate "mood board for a cyberpunk game"`

1. Archetype: mood-board
2. Plan: 8 image slots, title card with aesthetic description
3. Dispatch canvas-composer: write title card content (mood, colors, style)
4. Dispatch canvas-media: generate 8 images via `/banana`:
   - "neon cityscape, cyberpunk, rain, reflections"
   - "cyberpunk character portrait, augmented, glowing eyes"
   - (6 more themed prompts)
5. Instantiate mood-board template
6. Replace placeholder text nodes with generated image file nodes
7. Validate and report

### Example 3: Presentation from Topic

User: `/canvas generate "presentation about our Q3 results"`

1. Archetype: presentation
2. Plan: 6 slides (title, overview, revenue, growth, challenges, next steps)
3. Dispatch canvas-composer: write 6 slides of content
4. Optionally dispatch canvas-media: 1-2 hero images
5. Instantiate presentation template with `slide_count=6`
6. Edit each slide's text with composer output
7. Validate and report

---

## Fallback Behavior

| Scenario | Action |
|----------|--------|
| User description too vague | Ask: "What type of canvas? (presentation, mood board, dashboard, etc.)" |
| Archetype detected but uncertain | Confirm: "I'll create a [archetype] canvas. Sound right?" |
| Media skills not available | Build text-only canvas, suggest manual image addition |
| Canvas would exceed 120 nodes | Warn and suggest splitting into sub-canvases |
| Template instantiation fails | Fall back to manual canvas construction with the orchestrator |
