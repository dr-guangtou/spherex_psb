# spherex_psb specification

Source of truth for scope and architecture. Update before implementing new features.
Status: v0.1, 2026-09-22, learning phase complete; no analysis code yet.

## 1. Scientific goal

Use SPHEREx 0.75-5.0 um spectrophotometry to study the star formation histories and
stellar populations of low-redshift post-starburst (fast-quenching) galaxies, with
emphasis on NIR/MIR continuum shape and absorption features (e.g. CO bandheads, H2O and
CN features, the 1.6 um bump) that are sensitive to intermediate-age populations such as
AGB and TP-AGB stars.

## 2. Primary technical deliverable

Reliable rest-frame NIR spectra (flux density versus wavelength with realistic errors and
per-point provenance) for galaxies that are, relative to the 6.15 arcsec SPHEREx pixel
and the wavelength-dependent PSF:

- unresolved (point-like),
- semi-resolved (Re of a few to ~20 arcsec), or
- resolved (arcminute scale),

plus stacked spectra for sub-samples. Mosaics are a secondary, quick-look product.

## 3. Constraints and decisions

- Data source: SPHEREx Level 2 spectral images (QR2 and QR3 now; DR1 when released) from
  IRSA, accessed via TAP for discovery and the IBE cutout service or S3 for pixels.
  The IRSA Spectrophotometry Tool is the baseline for unresolved and semi-resolved
  targets and the reference against which our own extraction is validated.
- Knowledge base: `docs/spherex_data_guide.md` (synthesis) and `docs/reference_notes/`
  (per-source notes). No third-party SPHEREx GitHub tools until the user decides
  otherwise.
- Wavelengths come from the per-pixel CWAVE/CBAND products, never from nominal channels.
- Backgrounds: ZODI extension subtracted first, then a local background fit per exposure.
  Exposure-level screening for airglow, shuttle glow, Moon and ghost contamination.
- PSF: QR3/DR1 ePSF products (binary table, 5x oversampled) for all forward modeling,
  including QR2 images, following the official September 2026 tutorial.
- Flags: canonical bit table from the Explanatory Supplement, hard-coded; QR2 and QR3
  header conventions differ.
- Versioning: every measurement stores pipeline version, release, obs_id, detector and
  MJD so the analysis can be re-run on DR1 and QR2/QR3 flux corrections can be applied.
- Python 3.12, `uv`, `ruff` via pre-commit, snake_case everywhere.

## 4. Planned architecture (not yet implemented)

```
spherex_psb/
  archive/        discovery (TAP/SIA), cutout and S3 retrieval, local cache with provenance
  products/       readers for L2 MEF (QR2 and QR3), Spectral WCS, ePSF, Spectral Channels,
                  Solid Angle map, flag table and mask builders
  extraction/     per-exposure measurements: point-source and Sersic forward model (Tractor
                  or photutils based), aperture and isophotal photometry, background models
  spectra/        assembly of per-exposure measurements into spectra on the 102-channel
                  grid, error propagation, calibration floors, QR2->QR3 flux corrections
  stacking/       rest-frame normalization and combination with bootstrap errors
  validation/     synthetic photometry versus 2MASS/WISE/SDSS, comparison with the IRSA
                  Spectrophotometry Tool output, survey-to-survey repeatability
  samples/        target selection and cross-matching with SPHEREx coverage
scripts/          small validation and probe scripts (present)
docs/             guide, spec, lessons, todo, reference notes (present)
```

Data flow: sample table -> coverage query (TAP) -> cutouts per exposure -> per-exposure
measurement records (Parquet) -> spectrum per object -> stacks -> figures.

## 5. Validation plan

Small scale first: one unresolved, one semi-resolved and one resolved galaxy, each
compared against the IRSA Spectrophotometry Tool (where applicable), 2MASS/WISE synthetic
photometry, and repeat measurements across surveys. Only then run the full sample.

## 6. Open questions for the user

- Sample definition (redshift range, angular size distribution, parent catalog).
- Whether to reproduce the Tractor fit locally (SPIFF-like) from the start or rely on the
  IRSA tool for the first pass.
- Priority of resolved-galaxy work versus stacking of unresolved targets.
