#!/bin/bash
set -euo pipefail

# ===========================================================================
# Phase 1 — Initialization
#
# Goal: prove the project is in a workable state BEFORE any feature work.
#   (a) Runnable environment   — deps installed, app boots, no env issues
#   (b) Verifiable test framework — at least one example test actually passes
# ===========================================================================
echo "=== Phase 1: Initialization ==="

# --- (a) Runnable environment ----------------------------------------------
echo "--- [1a] Runnable environment ---"

echo "> Installing/locking dependencies (uv sync)"
uv sync

echo "> Interpreter: $(uv run python --version)"

if [ ! -f .env ]; then
  echo "  (note: no .env file found — relying on the environment for"
  echo "   DATABASE_URL / OPENAI_API_KEY / YOUTUBE_API_KEY)"
fi

echo "> Booting the app module (loads config, wires routers, registers ORM models)"
uv run python -c "import src.main; print('  app OK —', len(src.main.app.routes), 'routes registered')"

# --- (b) Verifiable test framework -----------------------------------------
echo "--- [1b] Verifiable test framework ---"
echo "> Running the smoke test (proves pytest + asyncio are configured)"
uv run pytest tests/test_smoke.py -q

echo "=== Initialization OK: environment runnable, test framework verified ==="
echo ""

# ===========================================================================
# Phase 2 — Verification
#
# The full quality gate. Run this before claiming any feature done.
# ===========================================================================
echo "=== Phase 2: Verification ==="

echo "--- [2a] Test suite (uv run pytest) ---"
uv run pytest

echo "--- [2b] Lint (uv run ruff check src tests) ---"
uv run ruff check src tests

echo "=== Verification Complete ==="
echo ""
echo "Next steps:"
echo "1. Read feature_list.json to see current feature state"
echo "2. Pick ONE unfinished feature to work on"
echo "3. Implement only that feature"
echo "4. Re-run ./init.sh before claiming done"
