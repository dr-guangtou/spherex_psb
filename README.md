# spherex_psb

Nearby post-starburst galaxies with SPHEREx spectrophotometry: what the instrument measures, how its public
data are reached and reduced, and forced photometry of resolved SDSS galaxies on the individual exposures.

Documentation site: <https://dr-guangtou.github.io/spherex_psb/> (built from `docs/` with Sphinx, MyST Markdown and
customised Furo following the note-style standard; entry point `docs/index.md`). Pages: SPHEREx primer, data access, data reduction and analysis, SED extraction for
SDSS galaxies, spectral index measurement, plus the project specification, task list, lessons, checkpoint
reports and per-source reference notes.

## Layout

| Path | Content |
|---|---|
| `spherex_psb/` | the package: archive discovery, cutout products (bundles, ePSF, flags), Sersic rendering and joint forced photometry, SED assembly, validation, figure style |
| `scripts/sed_demo/` | the six-galaxy SED demonstration (sample, measurement, validation, figures, H-minus bump feasibility) |
| `scripts/site_figures.py` | figures for the documentation made from calibration products and our measurements |
| `docs/` | the documentation site (markdown sources, figures, references, reports) |
| `docs/conf.py`, `docs/_static/`, `docs/_templates/`, `.github/workflows/docs.yml` | site configuration, the note-style assets (bundled MathJax under `_static/vendor/`) and the GitHub Pages deployment |

Data (cutout bundles, calibration cache, results) live outside the repository under
`/Users/shuang/data/spherex/`.

## Setup

```
uv sync                                        # analysis environment (uv only; no pip, conda or poetry)
uv run pre-commit install
bash scripts/build_docs.sh                     # strict Sphinx build into docs/_build/html, then opens it
uv run --only-group docs python -m http.server 8765 --directory docs/_build/html --bind 127.0.0.1  # with search
```

The project rules are in `CLAUDE.md`; the architecture and scope in `docs/SPEC.md`; the documentation
standard in `docs/html_documentation_guide.md`.

## Licence

GPL-3.0 (see `LICENSE`). Figures reproduced from publications in `docs/figures/external/` carry their own
credit lines and remain the property of their authors. The MathJax runtime and fonts bundled under
`docs/_static/vendor/` are Apache-2.0 (see the NOTICE file there).
