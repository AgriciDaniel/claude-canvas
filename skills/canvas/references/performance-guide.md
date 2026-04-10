# Canvas Performance Guide

Constraints and limits for generating Obsidian Canvas files that perform well.

---

## Node Limits

| Threshold | Impact | Action |
|-----------|--------|--------|
| <50 nodes | Smooth on all hardware | No concerns |
| 50-100 nodes | Fine on modern hardware | Monitor |
| 100-200 nodes | Lag on mid-range systems | Warn the user |
| 200+ nodes | Severe lag, panning/zooming breaks | Error — refuse to generate |

**Recommendation**: Target 15-30 visible nodes per viewport for comprehension. Keep total under 120 nodes for broad hardware compatibility.

If a canvas exceeds 100 nodes, suggest splitting into sub-canvases linked via file nodes (nested canvas preview).

---

## Minimum Spacing Between Nodes

Nodes must have adequate spacing to prevent visual overlap and clipping:

| Between | Minimum Gap | Recommended |
|---------|------------|-------------|
| Adjacent content nodes (horizontal) | 80px | 100px |
| Adjacent content nodes (vertical) | 60px | 80px |
| Node and zone boundary (padding) | 20px | 30px |
| Zone label area (top of zone) | 60px | 60px |
| Rows of different content types | 60px | 80px |

**Mermaid diagram nodes** need extra space — the rendered diagram often exceeds the text node bounds. Use minimum 600x500 for flowcharts, 500x400 for simpler diagrams.

**Overlap prevention**: Run `canvas_validate.py` after generation — it detects node overlaps >10% and warns.

---

## Grid Snapping

All generated coordinates (`x`, `y`, `width`, `height`) must be multiples of 20.

```python
def snap(value, grid=20):
    return round(value / grid) * grid
```

Obsidian's native grid is ~20px. Misaligned coordinates cause visual jitter when dragging nodes.

---

## Z-Index (Array Order)

The `nodes` array order determines rendering order:
- **First** node renders at the bottom (background)
- **Last** node renders on top (foreground)

**Rule**: Always place group nodes (zones) before their contained nodes in the array. This ensures content renders on top of zone backgrounds.

```json
{
  "nodes": [
    {"id": "zone-a", "type": "group", ...},
    {"id": "zone-b", "type": "group", ...},
    {"id": "text-in-zone-a", "type": "text", ...},
    {"id": "img-in-zone-b", "type": "file", ...}
  ]
}
```

---

## GIF Performance

Animated GIFs play automatically in canvas and continue rendering even when scrolled off-screen.

| Constraint | Limit | Reason |
|-----------|-------|--------|
| Max GIFs per canvas | 3 | Each GIF consumes GPU/CPU continuously |
| Max GIF width | 480px | Larger GIFs cause frame drops during pan/zoom |
| Max GIF file size | 2MB | Larger files cause load lag |

**Gotcha**: Pasting GIFs from clipboard loses animation. Must use drag-and-drop or file node reference.

---

## SVG Rendering

SVGs render as `<img>` tags in canvas — no interactivity, no hover effects, no clickable links.

**Requirements**:
- Must include `viewBox` attribute for proper scaling
- CSS animations may or may not render (inconsistent)
- For interactive SVGs, the only workaround is iframe embedding (not recommended in canvas)

**Recommendation**: Generate SVGs with explicit `viewBox="0 0 width height"`. Use `currentColor` for theme compatibility (though it won't resolve in `<img>` context — default to dark colors).

---

## Image Resolution

Obsidian does **not upscale** images beyond native resolution. Extra space shows as blank area.

| Guideline | Max recommended |
|-----------|----------------|
| Image width | 2000px |
| Image height | 2000px |
| Total image file size | 5MB |

For AI-generated images (banana), 1024x1024 or 1920x1080 is optimal.

---

## Text Node Size

| Constraint | Limit |
|-----------|-------|
| Max characters in one text node | ~5000 (performance degrades at 26K+) |
| Min readable width | 200px |
| Min readable height | 60px |
| Height rule of thumb | content-lines x 24px |

---

## Canvas File Size

| Threshold | Impact |
|-----------|--------|
| <100KB | Fast load |
| 100-500KB | Acceptable |
| 500KB-1MB | Slow to open |
| 1MB+ | May cause Obsidian hangs |

File size grows with text node content and the number of nodes. Image data is NOT stored in the canvas file (only paths).

---

## Recommended Plugin

**Canvas Performance Patch** (Qbject) fixes a media embed re-rendering bug. CSS workaround: setting canvas wrapper size to 1000% prevents node loading/unloading at viewport edges.

**Advanced Canvas** (Developer-Mike) adds Graph View integration, PNG/SVG export, and presentation mode.

---

## Performance Checklist

Before writing a canvas file, verify:

- [ ] Total nodes < 200 (warn at 100)
- [ ] All coordinates are multiples of 20
- [ ] Groups appear before contained nodes in array
- [ ] GIFs: max 3 per canvas, max 480px width
- [ ] SVGs: all have `viewBox` attribute
- [ ] Text nodes: none exceed 5000 characters
- [ ] No absolute paths in file nodes (vault-relative only)
