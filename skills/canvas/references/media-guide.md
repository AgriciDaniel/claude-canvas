# Media Integration Guide

How to generate and place images, GIFs, SVGs, and video thumbnails on Obsidian Canvas using external skills.

---

## Integration Architecture

```
User request → canvas-generate/canvas-populate
                    ↓
            ┌───────┼───────┐
            │       │       │
         /banana   /svg   /gif
         (Gemini)  (Python) (Veo/Remotion)
            │       │       │
            ↓       ↓       ↓
       _attachments/images/canvas/
       .canvases/assets/
                    ↓
            file node on canvas
```

---

## Image Generation via /banana

**Skill**: `/banana` (requires `nanobanana-mcp` MCP server)
**Output**: PNG at `~/Documents/nanobanana_generated/`

### Workflow

1. Check if banana skill is available. If not: "Install `/banana` for AI image generation."
2. Generate image with prompt:
   ```
   /banana generate "[prompt]" --size 1024x1024
   ```
3. Copy the generated image to the canvas media directory.
4. Detect aspect ratio and compute canvas node dimensions.
5. Add as file node to the canvas.

### Prompt Patterns for Canvas

| Context | Prompt Pattern |
|---------|---------------|
| Presentation hero | `[topic], presentation slide style, clean, professional, minimal` |
| Mood board | `[aesthetic], mood board reference, high quality photography` |
| Dashboard icon | `[concept] icon, flat design, simple, white background` |
| Storyboard scene | `[scene description], cinematic, 16:9 aspect ratio` |
| Gallery showcase | `[subject], product photography, studio lighting` |

### Sizing After Generation

Map generated image dimensions to canvas file node sizes using the aspect ratio table in `canvas-spec.md`:

| Image Dimensions | Canvas Width | Canvas Height |
|-----------------|-------------|--------------|
| 1024×1024 (1:1) | 280 | 280 |
| 1920×1080 (16:9) | 420 | 236 |
| 1080×1920 (9:16) | 200 | 356 |
| 1024×768 (4:3) | 380 | 285 |

---

## SVG Generation via /svg

**Skill**: `/svg` (sub-skills: svg-diagram, svg-chart, svg-icon)
**Output**: SVG file in project directory

### Workflow

1. Generate SVG with the appropriate sub-skill:
   - `/svg diagram` — flowcharts, architecture diagrams
   - `/svg chart` — bar, line, pie, radar charts
   - `/svg icon` — icons and symbol sprites
2. Copy the SVG to the canvas media directory.
3. Add as file node to the canvas.

### SVG-Specific Constraints

- SVGs render as `<img>` in Obsidian — **no interactivity**
- **Must include `viewBox` attribute** for proper scaling
- CSS animations may not render
- `currentColor` does not resolve (use explicit colors)
- File node sizing: width=400, height based on viewBox aspect ratio

### Recommended Sizing

```python
# Compute canvas dimensions from SVG viewBox
viewbox = "0 0 800 600"  # width=800, height=600
vb_w, vb_h = 800, 600
ratio = vb_w / vb_h

canvas_w = 400
canvas_h = round(canvas_w / ratio)
```

---

## GIF Generation via /gif Skills

**Skills**: `/claude-gif-generate`, `/claude-gif-create`, `/claude-gif-convert`
**Output**: GIF file

### Performance Limits

| Constraint | Limit | Reason |
|-----------|-------|--------|
| Max GIFs per canvas | 3 | GPU/CPU overhead from continuous rendering |
| Max GIF width | 480px | Prevents frame drops during pan/zoom |
| Max GIF file size | 2MB | Load lag on large files |

### GIF Canvas Sizing

GIFs use the same aspect ratio table as images. Common GIF dimensions:

| GIF Dimensions | Canvas Width | Canvas Height |
|---------------|-------------|--------------|
| 480×270 (16:9) | 420 | 236 |
| 480×480 (1:1) | 280 | 280 |
| 320×240 (4:3) | 380 | 285 |

### When to Use GIFs vs. Static Images

- **Use GIF**: Animated demos, loading indicators, attention-grabbing hero images
- **Use PNG/JPG**: Everything else (better performance, smaller files)
- **Use SVG**: Diagrams, charts, icons (vector quality, tiny files)

---

## Mermaid Diagrams (Native)

Mermaid renders **natively in text nodes** — no external file or skill needed. See `mermaid-patterns.md` for all diagram types and sizing recommendations.

### When to Use Mermaid vs. /svg

| Use Case | Mermaid | /svg |
|----------|---------|------|
| Quick flowchart on canvas | Yes | Overkill |
| Styled architecture diagram | No | Yes |
| Data chart with custom colors | No | Yes |
| Live-editable in Obsidian | Yes | No |

---

## Media Directory Convention

| Context | Media Directory | Example Path |
|---------|----------------|-------------|
| Vault mode | `_attachments/images/canvas/` | `_attachments/images/canvas/hero.png` |
| Standalone mode | `.canvases/assets/` | `.canvases/assets/hero.png` |

All file node paths in canvas JSON must be **vault-relative** (not absolute). Copy external files to the media directory before adding to canvas.

---

## Graceful Degradation

When a media skill is not installed:

| Skill | Fallback |
|-------|----------|
| `/banana` | "Install the banana skill for AI image generation. Add images manually with `/canvas add image`." |
| `/svg` | Use Mermaid in text nodes for diagrams. For charts, embed data tables in text nodes. |
| `/gif` | Use static images instead. "Install gif skills for animated content." |

Never fail silently. Always inform the user what's missing and how to work around it.
