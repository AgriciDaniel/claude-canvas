# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.0.x   | Yes       |

## Reporting a Vulnerability

If you discover a security vulnerability in claude-canvas, please report it responsibly:

1. **Do NOT open a public issue** for security vulnerabilities
2. Email the maintainer or open a private security advisory on GitHub
3. Include a description of the vulnerability, steps to reproduce, and potential impact

## Security Design

### No Network Access

claude-canvas operates entirely locally. The Python scripts (`canvas_validate.py`, `canvas_layout.py`, `canvas_template.py`) make zero network requests. They read and write local files only.

### No Credential Storage

claude-canvas does not store, process, or require any API keys, tokens, passwords, or credentials. Third-party integrations (`/banana`, `/svg`) manage their own credentials independently.

### File Path Safety

- The validation script (`canvas_validate.py`) checks that all file node paths are vault-relative, not absolute. Absolute paths like `/home/user/secret.png` are flagged as errors.
- The template engine uses `Path(__file__).parent` for script-relative paths — no hardcoded system paths.

### Input Validation

- Canvas JSON is parsed with Python's `json.loads()` — no `eval()` or dynamic code execution
- Template parameters are string-substituted, not evaluated as code
- The `--fix` flag in `canvas_validate.py` only modifies numeric coordinates and color type fields — it cannot inject content

### Hook Safety

The PostToolUse hook in `hooks/hooks.json` is a prompt-type hook (advisory text to Claude), not a command-type hook. It does not execute shell commands automatically.

## Dependencies

### Required
- Python 3.10+ (stdlib only — no pip packages required for core functionality)

### Optional
- Pillow (PIL) — image dimension detection (fallback: ImageMagick `identify`)
- Playwright — canvas export screenshots (fallback: manual screenshots)
- ImageMagick — PDF export via `convert` command

No dependencies are installed automatically. The `bin/setup.sh` script checks for optional dependencies and reports their status.
