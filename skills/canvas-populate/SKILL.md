---
name: canvas-populate
description: >
  Add content to existing Obsidian Canvas files. Supports all node types:
  images (with auto aspect ratio detection), text cards, PDFs, wiki notes,
  web links, Mermaid diagrams, SVGs, GIFs, AI-generated images via banana.
  Also adds zones (groups), edges between nodes, and imports recent banana images.
  Triggers on: canvas add, add to canvas, put on canvas, canvas zone, canvas
  connect, canvas from banana, add image to canvas, add text to canvas.
user-invocable: false
---

# canvas-populate: Add Content to Canvases

Read `../canvas/references/canvas-spec.md` for the full JSON format before any edit.
Read `../canvas/references/performance-guide.md` for node limits and constraints.

---

## General Workflow

For every add operation:

1. **Read** the target canvas JSON. Parse `nodes` and `edges` arrays.
2. **Collect existing IDs** to prevent collisions.
3. **Generate a new ID**: `[type]-[slug]-[unix-timestamp]`.
4. **Calculate position** using the auto-positioning algorithm (see canvas orchestrator).
5. **Spacing check**: Verify the calculated position has at least 80px horizontal and 60px vertical gap from ALL existing content nodes. If not, shift the position until spacing is clear.
6. **Append** the new node to the `nodes` array (after any groups — z-index ordering).
7. **Validate**: Run `python3 scripts/canvas_validate.py <path>` — check for overlaps and node count.
8. **Write** the updated canvas JSON.
9. **Report**: "Added [description] to [zone] zone at position ([x], [y])."

---

## Node Operations

### add image (`/canvas add image [path or url]`)

**Resolve the image:**
- If URL (starts with `http`): download with `curl -sL [url] -o [media_dir]/[filename]`.
  Derive filename from URL path, or use `img-[timestamp].jpg` if unclear.
- If local path outside canvas dir: `cp [path] [media_dir]/`
- If already canvas-relative: use as-is.

**Detect aspect ratio:**
```bash
python3 -c "from PIL import Image; img=Image.open('[path]'); print(img.width, img.height)"
# or fallback
identify -format '%w %h' [path]
```

Map to the sizing table in `../canvas/references/canvas-spec.md` (7 ratios + PDF + fallback).

**Create file node** with calculated dimensions. Position using auto-layout.

### add text (`/canvas add text [content]`)

```json
{
  "id": "text-[slug]-[timestamp]",
  "type": "text",
  "text": "[content]",
  "x": 0, "y": 0,
  "width": 300, "height": 120
}
```

For multi-line content, estimate height: count newlines, multiply by 24, add 40px padding. Minimum 120px.

### add pdf (`/canvas add pdf [path]`)

Copy to `[media_dir]/` if outside canvas dir. Fixed size: width=400, height=520.

### add note (`/canvas add note [wiki-page]`)

1. Search for a file matching the page name (case-insensitive, partial match).
2. Use `"type": "file"` with vault-relative path. Not `"type": "link"` — that's for URLs only.
3. Default size: width=300, height=100.

### add link (`/canvas add link [url]`)

```json
{
  "id": "link-[slug]-[timestamp]",
  "type": "link",
  "url": "[url]",
  "x": 0, "y": 0,
  "width": 400, "height": 120
}
```

Obsidian fetches Open Graph preview automatically.

### add mermaid (`/canvas add mermaid [code]`)

Mermaid renders natively in Obsidian text nodes. Wrap in a fenced code block:

```json
{
  "id": "text-mermaid-[timestamp]",
  "type": "text",
  "text": "```mermaid\n[code]\n```",
  "x": 0, "y": 0,
  "width": 500, "height": 400,
  "color": "5"
}
```

Wider text nodes work better for Mermaid (min 400px wide, 300px tall).

### add svg (`/canvas add svg [description or path]`)

- If path: copy SVG to media dir, add as file node. Width=400, height based on viewBox aspect ratio.
- If description: delegate to `/svg` skill to generate, then add the output file.
- SVGs render as `<img>` — no interactivity. Must have `viewBox` attribute.

### add gif (`/canvas add gif [description or path]`)

- If path: copy GIF to media dir, add as file node.
- If description: delegate to `/claude-gif-generate` skill, then add the output.
- Performance limit: max 3 GIFs per canvas, max 480px width. Warn if exceeded.

### add banana (`/canvas add banana [prompt]`)

1. Check if banana skill is available. If not: "Install the banana skill for AI image generation."
2. Delegate to banana skill with the prompt.
3. Wait for image generation.
4. Add the generated image as a file node (detect aspect ratio, auto-size).
5. Log the path to `.recent-images.txt` in the canvas directory.

---

## Zone Operations

### zone (`/canvas zone [name] [color]`)

1. Read canvas JSON.
2. Find max_y of all existing nodes. Use `-80` if canvas is empty (consistent with starter canvas layout where title is at y=-300 and default zone at y=-140):
   ```python
   if not canvas_nodes:
       max_y = -80
   else:
       max_y = max(n["y"] + n.get("height", 0) for n in canvas_nodes) + 60
   ```
3. Create group node:

```json
{
  "id": "zone-[slug]-[timestamp]",
  "type": "group",
  "label": "[name]",
  "x": -400,
  "y": "[max_y]",
  "width": 1000,
  "height": 400,
  "color": "[color or '4']"
}
```

Valid colors: `"1"`=red `"2"`=orange `"3"`=yellow `"4"`=green `"5"`=cyan `"6"`=purple

4. Insert the group node BEFORE content nodes in the array (z-index: groups render behind).
5. Write and report.

---

## Edge Operations

### connect (`/canvas connect [from] [to] [label]`)

1. Read canvas JSON.
2. Find `from` and `to` nodes by ID, label text, or partial match.
3. If ambiguous, list matches and ask the user to clarify.
4. Create edge:

```json
{
  "id": "e-[from-slug]-[to-slug]-[timestamp]",
  "fromNode": "[from-id]",
  "toNode": "[to-id]",
  "toEnd": "arrow"
}
```

5. Omit `fromSide`/`toSide` for auto-routing (better results).
6. Add optional `label` if provided.
7. Write and report.

---

## Banana Import

### from banana (`/canvas from banana`)

1. Check `[canvas_dir]/.recent-images.txt` for recently logged image paths.
2. If not found or empty: search for images modified in the last 10 minutes:
   ```bash
   find [media_dir] -name "*.png" -o -name "*.jpg" -newer /tmp/ten-min-ago
   ```
3. If still none: show the 5 most recently modified images.
4. Present list: "Found N recent images. Add to canvas? Which zone?"
5. On confirmation: add each using the add image logic.

---

## Media Directory

- Vault mode: `_attachments/images/canvas/`
- Standalone mode: `.canvases/assets/`
- Create if it doesn't exist.
- All file node paths must be relative to the vault/project root.
