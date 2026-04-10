# Privacy Policy

## Data Collection

claude-canvas does **not** collect, store, transmit, or process any personal data. It is a local-only Claude Code plugin that generates Obsidian Canvas files on your machine.

## What claude-canvas Does

- Reads and writes `.canvas` JSON files in your local project or Obsidian vault directory
- Runs Python scripts locally for validation, layout, and template instantiation
- All processing happens on your machine — no network requests, no telemetry, no analytics

## What claude-canvas Does NOT Do

- Does not send canvas data to any external server
- Does not collect usage statistics or telemetry
- Does not access your Obsidian vault beyond the canvas files you explicitly create
- Does not store API keys, tokens, or credentials
- Does not make network requests of any kind

## Third-Party Integrations

claude-canvas can optionally integrate with these skills (if installed separately):

- **`/banana`** — AI image generation via Gemini API. Image generation requests go through the `nanobanana-mcp` MCP server, which has its own privacy policy. claude-canvas does not control or intermediate these requests.
- **`/svg`** — SVG diagram generation. Runs locally, no network requests.
- **`/gif`** — GIF generation. May use external APIs depending on the skill implementation.

These integrations are optional. claude-canvas works without them.

## File Storage

All files created by claude-canvas are stored locally:
- Canvas files: `wiki/canvases/` (vault mode) or `.canvases/` (standalone mode)
- Media files: `_attachments/images/canvas/` (vault) or `.canvases/assets/` (standalone)
- Backup files: `*.canvas.bak` (created by layout operations, stored alongside originals)

No files are uploaded, synced, or transmitted unless you explicitly configure Obsidian Sync or Git.

## Contact

For privacy questions, open an issue at [github.com/AgriciDaniel/claude-canvas](https://github.com/AgriciDaniel/claude-canvas/issues).
