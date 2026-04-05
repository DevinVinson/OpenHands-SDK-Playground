# Test Fixtures

This directory contains sample projects used for integration testing and agent validation.

## insecure_app/

A sample Python application with intentionally hardcoded secrets. Used to test the **Auditor** agent configuration.

**Files:**
- `app.py` - Main app with hardcoded API keys and credentials
- `config.py` - Configuration with more embedded secrets

**Expected agent behavior:** The auditor should identify all hardcoded secrets and suggest moving them to environment variables or a `.env` file.

**Example usage:**
```bash
uv run python -m lab run \
  --agent auditor \
  --workspace tests/fixtures/insecure_app \
  --task "Find all hardcoded secrets and suggest secure alternatives"
```

## js_project/

A sample JavaScript project for testing the **Modernizer** agent configuration.

**Files:**
- `utils.js` - Utility functions without type annotations
- `component.js` - UI component classes
- `config.js` - Configuration module

**Expected agent behavior:** The modernizer should convert `.js` files to `.ts` and add TypeScript type annotations.

**Example usage:**
```bash
uv run python -m lab run \
  --agent modernizer \
  --workspace tests/fixtures/js_project \
  --task "Convert all JavaScript files to TypeScript with proper type annotations"
```
