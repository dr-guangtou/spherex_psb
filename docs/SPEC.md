# spherex_psb specification

Source of truth for scope and architecture. Update before implementing new features.
Status: v0.2, 2026-11-13, SED demo in progress (see section 7).

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
  (per-source notes).
- Third-party tools (permission granted 2026-11-13 for the SED demo): hbahk's
  `spherex-retrieval` (MIT), `tractor-jax` (GPL-2.0) and `tractorjax-spherex` (GPL-3.0) may be
  installed, run and read; licence compatibility is checked before copying code (this
  repository is GPL-3). Any other third-party SPHEREx tool needs the user's approval.
  `/Users/shuang/Dropbox/work/project/otters/spherex_photometry_code` is read only, never
  imported.
- Data: downloads under `/Users/shuang/data/spherex`; any single download above 300 MB needs
  approval; demo budget 10 GB; temporary material goes to `~/.Trash/<name>_<date>`.
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

## 6. Answered questions (2026-11-13)

- Sample: low-redshift SDSS galaxies from the MPA-JHU DR8 selection of
  `/Users/shuang/data/mpa` (0.03 < z < 0.06, log M* > 10, 48,111 galaxies; r-band R_e 1.6 / 4.3 /
  10.5 arcsec at the 5 / 50 / 95 percentiles, so mostly semi-resolved).
- First pass: our own per-exposure forced photometry with a PSF-convolved Sersic model at fixed
  optical shape (galaxy and neighbours fitted jointly), plus a model-corrected aperture flux;
  tractorjax-spherex as an independent cross-check; the IRSA tool only as an optional check.
  Point-source fits are ruled out (see `docs/reference_notes/photometry_study_2026-11.md`).
- Priority: semi-resolved galaxies first (the bulk of the sample); stacking later.

## 7. SED demo (feature/sed-demo, task spec in `docs/sed_demo_task.md`)

Scope: six SDSS galaxies with fixed roles (reference, compact, large, close neighbour, outside
the Legacy Survey, post-starburst-like); every DR1 + QR3 wide-survey exposure; per-exposure
forced photometry; SED assembly on the 102-channel grid; validation (detector-boundary test,
estimator consistency, point-source negative control, injection-recovery, external photometry,
cross-code check, error calibration); journal-style PNG figures; report in
`docs/demo_sed_report.md`. Out of scope: the full sample, stacking, SED fitting, mosaics.

Data decisions: DR1 + QR3 only (no `l3_flux_corrections`: they apply to QR2 images, which are
no longer searchable); the R7 ePSF, Spectral WCS (`cal-swcs-v5-2026-191`) and Solid Angle Pixel
Map (`cal-sapm-v3-2026-191`) shared by both releases; ZODI subtracted, then a local background
fitted jointly with the sources; the IRSA tool's flag set plus TRANSIENT, OVERFLOW and DICHROIC
excluded; NaN pixels removed from the fit.

Code layout for the demo (subset of section 4): `spherex_psb/archive` (discovery, cutouts via
spherex-retrieval or our own retry wrapper), `spherex_psb/products` (MEF reader, ePSF zone
selection, flags), `spherex_psb/extraction` (Sersic renderer, joint linear solve, background
models, estimators), `spherex_psb/spectra` (per-exposure records in Parquet, binning, extinction),
`spherex_psb/validation`, `spherex_psb/figures` (shared style). Scripts in `scripts/sed_demo/`.

Decisions from the demo (2026-11-14, `docs/demo_sed_report.md`): background = constant + quadratic in
CWAVE fitted jointly with the sources (repairs the He I exposures); Sersic templates integrated over the
core (32 x 32 sub-samples in a 7 x 7 oversampled-pixel block); per-exposure screening on near-target and
whole-cutout chi2 and on CWAVE; SED error = exposure scatter per channel, with a 1.5 % fractional floor
per exposure for n = 4 galaxies with R_e <= 2 arcsec; DR1 and QR3 combined without correction. Open
(user's call): the total-flux convention (analytic Sersic total versus the truncated tractor / SDSS model
total, 6 % apart for n = 4) and whether a position-jitter term is added before stacking.
