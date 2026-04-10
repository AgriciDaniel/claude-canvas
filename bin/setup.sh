#!/bin/bash
# setup.sh — Install optional Python dependencies for claude-canvas
#
# Required: Python 3.10+
# Optional: Playwright (for canvas export screenshots)
#
# Usage:
#   bash bin/setup.sh
#   bash bin/setup.sh --with-playwright

set -e

echo "claude-canvas setup"
echo "==================="

# Check Python version
python3 -c "import sys; assert sys.version_info >= (3, 10), f'Python 3.10+ required, got {sys.version}'" 2>/dev/null || {
    echo "ERROR: Python 3.10+ is required"
    exit 1
}
echo "✓ Python $(python3 --version | cut -d' ' -f2)"

# Core dependencies (stdlib only — no pip install needed)
echo "✓ Core scripts use stdlib only (no pip install needed)"

# Check for PIL (optional, for image aspect ratio detection)
python3 -c "from PIL import Image; print('✓ Pillow available (image aspect ratio detection)')" 2>/dev/null || {
    echo "⚠ Pillow not installed — will fall back to ImageMagick 'identify' for aspect ratio detection"
    echo "  Install with: pip install Pillow"
}

# Check for ImageMagick (optional, for export)
which convert >/dev/null 2>&1 && echo "✓ ImageMagick available (PDF export)" || {
    echo "⚠ ImageMagick not installed — PDF export will not be available"
    echo "  Install with: sudo apt install imagemagick"
}

# Playwright (optional, for canvas export screenshots)
if [ "$1" = "--with-playwright" ]; then
    echo ""
    echo "Installing Playwright..."
    pip install playwright
    playwright install chromium
    echo "✓ Playwright installed (canvas export screenshots)"
else
    python3 -c "from playwright.sync_api import sync_playwright" 2>/dev/null && {
        echo "✓ Playwright available (canvas export screenshots)"
    } || {
        echo "⚠ Playwright not installed — canvas export will use Advanced Canvas plugin or manual screenshots"
        echo "  Install with: bash bin/setup.sh --with-playwright"
    }
fi

echo ""
echo "Setup complete. Run '/canvas' in Claude Code to get started."
