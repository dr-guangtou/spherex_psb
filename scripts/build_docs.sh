#!/usr/bin/env bash
# Build the documentation (note-style: Sphinx, MyST, Furo) into docs/_build/html and open it.
# usage: bash scripts/build_docs.sh [--no-open]
set -euo pipefail
cd "$(dirname "$0")/.."
uv run --only-group docs sphinx-build -E -W --keep-going -b html docs docs/_build/html
echo "site built: $(pwd)/docs/_build/html/index.html"
if [[ "${1:-}" != "--no-open" ]]; then
  open "docs/_build/html/index.html"
fi
