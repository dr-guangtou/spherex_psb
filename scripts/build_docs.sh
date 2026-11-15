#!/usr/bin/env bash
# Build the documentation (note-style: Sphinx, MyST, Furo) in its two versions and open the internal one.
#   docs/_build/html      the public site, exactly what GitHub Pages publishes
#   docs/_build/internal  the public pages plus the internal ones listed in docs/conf.py
#                         (specification, to do, lessons, task specs, ...), for the owner's review only
# usage: bash scripts/build_docs.sh [--no-open]
set -euo pipefail
cd "$(dirname "$0")/.."
# Sphinx never deletes pages that are no longer built, so start from empty folders.
/bin/rm -rf docs/_build/html docs/_build/internal
uv run --only-group docs sphinx-build -E -W --keep-going -b html docs docs/_build/html
uv run --only-group docs sphinx-build -E -W --keep-going -t internal -b html docs docs/_build/internal
echo "public site:   $(pwd)/docs/_build/html/index.html"
echo "internal site: $(pwd)/docs/_build/internal/index.html"
if [[ "${1:-}" != "--no-open" ]]; then
  open "docs/_build/internal/index.html"
fi
