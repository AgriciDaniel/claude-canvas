# Obsidian Canvas JSON Specification

Canvas files are JSON with two top-level keys: `nodes` (array) and `edges` (array).
Obsidian reads and writes them as UTF-8 JSON files with `.canvas` extension.

This reference aligns with the [JSON Canvas 1.0 open specification](https://jsoncanvas.org/spec/1.0/). All structures support arbitrary additional fields (`[key: string]: any`) for forward compatibility. Obsidian will preserve unknown fields when reading and writing canvas files.

**ID format**: Use descriptive IDs with timestamps: `[type]-[content-slug]-[unix-timestamp]` (e.g., `img-cover-1744032823`). Obsidian also accepts 16-character lowercase hex IDs. Both are valid JSON Canvas.

---

## Coordinate System

```
        x increases →
   ┌─────────────────────────────────
   │  (-920, -2400)      (0, -2400)
   │
y  │  (-920, 0)          (0, 0) ← origin
↓  │
   │  (-920, 540)        (500, 540)
```

- **Origin** (0, 0) is the center of the canvas viewport.
- **x increases rightward.** Negative x = left of center.
- **y increases downward.** Negative y = above center.
- Node `x` and `y` are the **top-left corner** of the node, not the center.
- Obsidian pans to fit all nodes on first open. No saved viewport state.
- **Grid snapping**: Obsidian snaps to ~20px increments. Align generated coordinates to multiples of 20.

---

## Node Types

### Common Fields (All Nodes)

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | string | yes | Unique within the canvas |
| `type` | string | yes | `"text"`, `"file"`, `"link"`, `"group"` |
| `x` | integer | yes | Top-left corner x (pixels) |
| `y` | integer | yes | Top-left corner y (pixels) |
| `width` | integer | yes | Width in pixels |
| `height` | integer | yes | Height in pixels |
| `color` | string | no | Preset `"1"`-`"6"` or hex `"#FF0000"` |

### Text Node

Renders markdown content as a styled card. Supports full Obsidian Flavored Markdown: headings, bold/italic, wikilinks, embeds, callouts, code blocks, LaTeX math, **Mermaid diagrams**, tables, task lists, tags, footnotes, and Dataview queries.

```json
{
  "id": "text-title-4821",
  "type": "text",
  "text": "# Heading\n\nParagraph with **bold** and `code`.",
  "x": -400, "y": -300, "width": 400, "height": 120, "color": "6"
}
```

- `text`: markdown string. Use `\n` for newlines.
- Minimum readable size: width >= 200, height >= 60.
- `color` is optional. Omit for default (no color).

### File Node

Renders an image, PDF, markdown note, or other vault file inline.

```json
{
  "id": "img-cover-7823",
  "type": "file",
  "file": "_attachments/images/example.png",
  "x": -900, "y": -100, "width": 420, "height": 236
}
```

- `file`: **vault-relative path** (not absolute, not `~/`).
- `subpath` (optional): heading or block reference, starts with `#`.
- Supported inline rendering: `.png` `.jpg` `.webp` `.gif` (animated, auto-plays) `.pdf` `.md` `.canvas` `.mp4` `.webm` `.ogv` (video with controls) `.mp3` `.flac` `.wav` `.ogg` (audio player)
- SVG renders as `<img>` tag — no interactivity, no hover effects. Must include `viewBox` for proper scaling.
- Images use `object-fit: contain`. Not upscaled beyond native resolution.
- No `color` field for file nodes: color is ignored.

### Group Node (Zone)

A labeled rectangular region. Does not clip or contain nodes — purely visual guide.
Nodes placed "inside" a group are just positioned within its bounding box.
Moving a group in Obsidian moves all spatially-contained nodes.

```json
{
  "id": "zone-branding-3391",
  "type": "group",
  "label": "Brand Identity",
  "x": -920, "y": -880, "width": 1060, "height": 290, "color": "6",
  "background": "_attachments/images/grid-bg.png",
  "backgroundStyle": "cover"
}
```

- `label`: shown at the top of the group box.
- `color`: colors the group border and label.
- `background` (optional): vault-relative path to background image.
- `backgroundStyle` (optional): `"cover"` (fill, crop) | `"ratio"` (fit, preserve) | `"repeat"` (tile).

### Link Node

Renders a web URL as an embedded preview card with Open Graph data.

```json
{
  "id": "link-karpathy-2233",
  "type": "link",
  "url": "https://github.com/karpathy",
  "x": 200, "y": -300, "width": 400, "height": 120
}
```

- `url`: must be a valid `https://` URL.

---

## Edges

Connections between nodes. Rendered as Bezier curves by default.

```json
{
  "id": "e-hub-cidx",
  "fromNode": "hub",
  "toNode": "c-idx",
  "fromSide": "right",
  "fromEnd": "none",
  "toSide": "left",
  "toEnd": "arrow",
  "label": "concepts",
  "color": "5"
}
```

**Required**: `id`, `fromNode`, `toNode`. Everything else is optional.

| Field | Values | Default | Notes |
|-------|--------|---------|-------|
| `fromSide` / `toSide` | `"top"` `"bottom"` `"left"` `"right"` | auto-calculated | Omit for better auto-routing |
| `fromEnd` | `"none"` `"arrow"` | `"none"` | End-cap on source side |
| `toEnd` | `"none"` `"arrow"` | `"arrow"` | End-cap on target side (asymmetric default!) |
| `label` | string | — | Text shown on the edge |
| `color` | `"1"`-`"6"` or hex | — | Edge color |

**Pro tip**: Omitting `fromSide`/`toSide` lets Obsidian auto-route edges dynamically. This often produces better results than manual specification.

---

## Color Reference

| Code | Color | Hex (approx) | Use case |
|------|-------|-------------|----------|
| `"1"` | Red / Tomato | #e03e3e | Warnings, archive |
| `"2"` | Orange | #d09035 | Active work |
| `"3"` | Yellow / Gold | #d0a023 | WIP, notes |
| `"4"` | Green / Teal | #448361 | Content, sources |
| `"5"` | Blue / Cyan | #3ea7d3 | Navigation, info |
| `"6"` | Purple / Violet | #9063d2 | Title, identity |

Colors are strings, not integers: `"1"` not `1`. Specific RGB values are theme-dependent. These map to CSS variables (`--canvas-color-1` through `--canvas-color-6`).

Omit `color` entirely for the default (no border color, transparent label).

---

## Image Sizing Guidelines

Calculate from actual image dimensions using PIL or `identify`:

```bash
python3 -c "from PIL import Image; img=Image.open('path.png'); print(img.width, img.height)"
# or
identify -format '%w %h' path.png
```

| Aspect ratio | Condition | Canvas width | Canvas height |
|-------------|-----------|-------------|--------------|
| 16:9 (wide) | ratio 1.6–2.0 | 420 | 236 |
| 2:1 (ultra wide) | ratio > 2.0 | 440 | 220 |
| 4:3 | ratio 1.2–1.6 | 380 | 285 |
| 1:1 (square) | ratio 0.9–1.1 | 280 | 280 |
| 3:4 | ratio 0.6–0.9 | 240 | 320 |
| 9:16 (portrait) | ratio < 0.6 | 200 | 356 |
| PDF | any | 400 | 520 |
| Unknown | fallback | 320 | 240 |

---

## Undocumented Behaviors

These are not in the JSON Canvas 1.0 spec but are confirmed Obsidian behaviors:

1. **Z-index = array order**: First node in `nodes` array renders at bottom, last on top. Selecting a card moves it to end of array.
2. **Group containment is spatial only**: No parent-child relationship in JSON. If node coordinates fall inside group bounds, it appears inside.
3. **Canvas links don't create backlinks**: Edges are visual-only, don't appear in Graph View. The Advanced Canvas plugin fixes this.
4. **Placeholder rendering**: At far zoom levels, nodes collapse to colored rectangles for performance.
5. **Nested canvases**: `.canvas` files render as static schematic previews (since v1.1.5), not interactive.

---

## Common Mistakes

- **Wrong path format**: use `_attachments/images/file.png` not `/home/user/...` or `~/...`
- **ID collision**: always read existing IDs before generating a new one
- **Negative y confusion**: `y: -2400` is ABOVE `y: -1000` (more negative = higher up)
- **Group does not clip**: positioning a node "inside" a group is just bounding box overlap
- **Missing height on text nodes**: Obsidian may clip text if height too small. Use height >= content-lines x 24.
- **Color as integer**: Use `"1"` not `1` — colors are strings
- **Specifying edge sides unnecessarily**: Omit fromSide/toSide for auto-routing unless flow direction matters

---

## Full Example: Two-Zone Canvas

```json
{
  "nodes": [
    {
      "id": "zone-logos",
      "type": "group",
      "label": "Logos & Icons",
      "x": -920, "y": -2200, "width": 1800, "height": 320, "color": "6"
    },
    {
      "id": "title-0001",
      "type": "text",
      "text": "# Brand Reference\n\n**AI Marketing Hub** visual assets",
      "x": -920, "y": -2440, "width": 560, "height": 180, "color": "6"
    },
    {
      "id": "img-logo-pro",
      "type": "file",
      "file": "_attachments/images/example.png",
      "x": -900, "y": -2180, "width": 420, "height": 236
    },
    {
      "id": "img-icon-free",
      "type": "file",
      "file": "_attachments/images/example-icon.png",
      "x": -440, "y": -2180, "width": 280, "height": 280
    },
    {
      "id": "zone-covers",
      "type": "group",
      "label": "Skill Covers",
      "x": -920, "y": -1820, "width": 1800, "height": 340, "color": "3"
    },
    {
      "id": "img-seo",
      "type": "file",
      "file": "_attachments/images/example-cover.png",
      "x": -900, "y": -1800, "width": 420, "height": 236
    }
  ],
  "edges": []
}
```

Note: Groups come before their contained nodes in the array (z-index ordering).
