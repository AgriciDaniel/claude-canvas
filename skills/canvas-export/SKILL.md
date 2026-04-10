---
name: canvas-export
description: >
  Export Obsidian Canvas files to PNG, SVG, or PDF formats. Uses the Advanced
  Canvas plugin's built-in export when Obsidian is running, or falls back to
  Playwright browser-based screenshot capture. Supports single canvas export,
  presentation slide-per-page PDF export, and batch export.
  Triggers on: canvas export, export canvas, canvas to png, canvas to pdf,
  canvas to svg, save canvas as image, screenshot canvas, export presentation.
user-invocable: false
---

# canvas-export: Export Canvas to Image/PDF

---

## Export Methods

### Method 1: Advanced Canvas Plugin Export (Preferred)

The [Advanced Canvas](https://github.com/Developer-Mike/obsidian-advanced-canvas) plugin provides built-in PNG and SVG export with transparency support.

**Requirements**: Obsidian running with Advanced Canvas installed.

**Workflow**:
1. Instruct the user: "In Obsidian, right-click the canvas background → Advanced Canvas → Export as PNG/SVG"
2. Or use Obsidian's command palette: `Advanced Canvas: Export as PNG`
3. The exported file appears in the canvas directory.

This is the highest-quality export method — it uses Obsidian's own rendering engine.

### Method 2: Playwright Screenshot (Fallback)

When Obsidian is not running or Advanced Canvas is not installed, use Playwright to capture the canvas.

**Requirements**: Playwright installed (`pip install playwright && playwright install chromium`)

**Workflow**:
1. Check if Playwright is available:
   ```bash
   python3 -c "from playwright.sync_api import sync_playwright; print('ok')" 2>/dev/null && echo "available" || echo "not available"
   ```
2. If available, generate a standalone HTML viewer of the canvas and screenshot it:
   ```bash
   # Generate HTML from canvas JSON
   python3 -c "
   import json, sys
   canvas = json.load(open(sys.argv[1]))
   # ... render to HTML with absolute positioning ...
   " [canvas_path] > /tmp/canvas-preview.html

   # Screenshot with Playwright
   python3 -c "
   from playwright.sync_api import sync_playwright
   with sync_playwright() as p:
       browser = p.chromium.launch()
       page = browser.new_page(viewport={'width': 1920, 'height': 1080})
       page.goto('file:///tmp/canvas-preview.html')
       page.screenshot(path='[output_path]', full_page=True)
       browser.close()
   "
   ```
3. Report the output path and dimensions.

### Method 3: User-Assisted Screenshot

When neither method is available:
1. Tell the user: "Open the canvas in Obsidian, zoom to fit all content, then take a screenshot."
2. On Linux (COSMIC): suggest `Print` key for screenshot tool.
3. On macOS: suggest `Cmd+Shift+4`.

---

## Operations

### Export to PNG (`/canvas export png [output_path]`)

1. Identify the target canvas (default: active canvas or `main.canvas`).
2. Determine output path:
   - If provided: use it.
   - If not: `[canvas_dir]/exports/[canvas-name].png`
3. Try Method 1 (Advanced Canvas) first.
4. If not available: try Method 2 (Playwright).
5. If neither: use Method 3 (user-assisted).
6. Report: "Exported [canvas] to [path] ([width]x[height] pixels)"

### Export to SVG (`/canvas export svg [output_path]`)

1. Same flow as PNG, but use SVG format.
2. Advanced Canvas supports SVG export with transparency.
3. Playwright fallback: render HTML, use `page.screenshot(type='svg')` — note: Playwright doesn't natively export SVG. Fall back to PNG.
4. Report format and path.

### Export to PDF (`/canvas export pdf [output_path]`)

For standard canvases:
1. Export to PNG first, then convert: `convert [png] [pdf]` (ImageMagick).

For presentation canvases:
1. Detect if canvas has edge-connected slide groups (presentation pattern).
2. Export each slide group as a separate PNG.
3. Combine into a multi-page PDF:
   ```bash
   convert slide-1.png slide-2.png slide-3.png output.pdf
   ```
4. Report: "Exported [N]-slide presentation to [path]"

---

## Output Directory Convention

Exports go to `[canvas_dir]/exports/` by default:
- Vault mode: `wiki/canvases/exports/`
- Standalone mode: `.canvases/exports/`

Create the directory if it doesn't exist.

---

## Limitations

- Playwright rendering is approximate — it doesn't replicate Obsidian's exact canvas renderer
- SVG export via Playwright is not supported — falls back to PNG
- PDF export requires ImageMagick (`convert` command)
- Mermaid diagrams in text nodes may not render in Playwright screenshots (requires Mermaid JS library)
- GIF animations are captured as static frames in screenshots
- Export quality depends on the method used (Advanced Canvas > Playwright > Screenshot)
