#!/usr/bin/env bash
# run_tests.sh — Install dependencies and run the full test suite.
# Usage:
#   chmod +x run_tests.sh
#   ./run_tests.sh              # run all tests
#   ./run_tests.sh --coverage   # include coverage report

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ── Ensure virtual environment exists ─────────────────────────────────────
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment…"
    python3 -m venv .venv
fi

# shellcheck source=/dev/null
source .venv/bin/activate

# ── Install / upgrade dependencies ────────────────────────────────────────
echo "Installing dependencies…"
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
pip install pytest pytest-cov --quiet

# ── Run tests ─────────────────────────────────────────────────────────────
echo ""
echo "Running tests…"
echo "────────────────────────────────────────────"

if [[ "${1:-}" == "--coverage" ]]; then
    pytest tests/ \
        --cov=core \
        --cov=config \
        --cov-report=term-missing \
        --cov-report=html:coverage_html \
        -v
    echo ""
    echo "Coverage report written to: coverage_html/index.html"
else
    pytest tests/ -v
fi

echo "────────────────────────────────────────────"
echo "Done."