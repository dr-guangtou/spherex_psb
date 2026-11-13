#!/usr/bin/env bash
# Build the documentation site into site/ and open it in the default browser.
# usage: bash scripts/build_docs.sh [--no-open]
set -euo pipefail
cd "$(dirname "$0")/.."
NO_MKDOCS_2_WARNING=1 uv run --only-group docs mkdocs build --strict
echo "site built: $(pwd)/site/index.html"
if [[ "${1:-}" != "--no-open" ]]; then
  open "site/index.html"
fi
