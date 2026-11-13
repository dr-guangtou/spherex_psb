# spherex_psb

Nearby post-starburst galaxies with SPHEREx spectrophotometry: what the instrument measures, how its public
data are reached and reduced, and forced photometry of resolved SDSS galaxies on the individual exposures.

Documentation site: <https://dr-guangtou.github.io/spherex_psb/> (built from `docs/` with MkDocs; entry
point `docs/index.md`). Pages: SPHEREx primer, data access, data reduction and analysis, SED extraction for
SDSS galaxies, spectral index measurement, plus the project specification, task list, lessons, checkpoint
reports and per-source reference notes.

## Layout

| Path | Content |
|---|---|
| `spherex_psb/` | the package: archive discovery, cutout products (bundles, ePSF, flags), Sersic rendering and joint forced photometry, SED assembly, validation, figure style |
| `scripts/sed_demo/` | the six-galaxy SED demonstration (sample, measurement, validation, figures, H-minus bump feasibility) |
| `scripts/site_figures.py` | figures for the documentation made from calibration products and our measurements |
| `docs/` | the documentation site (markdown sources, figures, references, reports) |
| `mkdocs.yml`, `.github/workflows/docs.yml` | site configuration and the GitHub Pages deployment |

Data (cutout bundles, calibration cache, results) live outside the repository under
`/Users/shuang/data/spherex/`.

## Setup

```
uv sync                                        # analysis environment (uv only; no pip, conda or poetry)
uv run pre-commit install
uv run --only-group docs mkdocs serve          # documentation preview at http://127.0.0.1:8000
uv run --only-group docs mkdocs build --strict # what the Pages workflow runs
```

The project rules are in `CLAUDE.md`; the architecture and scope in `docs/SPEC.md`.

## Licence

GPL-3.0 (see `LICENSE`). Figures reproduced from publications in `docs/figures/external/` carry their own
credit lines and remain the property of their authors.
