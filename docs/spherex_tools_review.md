# Review of existing SPHEREx software (2026-09-23)

Scope: the eight repositories suggested by the user plus candidates found by a GitHub and
arXiv search. Each repository was cloned into a temporary folder, read (not installed or
run), and written up in `docs/reference_notes/tools/<repo>.md`. This file is the
synthesis. Nothing here is adopted yet; the recommendation section says what to try
first and in which order.

## 1. Summary table

| Repository | Author / status | License | Release support | Extraction method | Extended sources | Verdict |
|---|---|---|---|---|---|---|
| Caltech-IPAC/spherex-pipelines | SSDC official snapshot 6.5.5 (2026-06-30); no external support | BSD-3 | QR2-era code (11x11 PSF cube); R7 not in snapshot | Tractor forced photometry, global spectral background + Background2D, local 15x15 fallback | Sersic via Tractor, positions and shapes frozen | Borrow `spx_utils`/`spx_data`; read tasks as the algorithmic spec |
| Caltech-IPAC/tractor-spherex | SSDC fork of The Tractor, documented in FORK.md | GPLv2 | n/a | Lanczos-3 sub-pixel shift, arbitrary-oversampling FFT rendering of Sersic through a pixelized PSF | yes (SersicGalaxy) | Use directly as a dependency (needs astrometry.net utils and SWIG build) |
| hbahk/spherex-retrieval | SNU grad student; active to 2026-09-19; regression tests | MIT | QR2 and QR3 (PSF cube and EPSF), TAP fallback, QR2 to R7 flux corrections | none (retrieval and PSF preparation only) | n/a | Use directly for retrieval and PSF prep, or vendor |
| hbahk/tractorjax-spherex | same author; alpha, well tested; tied to Bahk et al. 2026 (arXiv:2606.19875) | GPL-3 | QR2 and QR3 via PSFKIND dispatch | JAX Tractor forced photometry, catalog positions and shapes fixed, CWAVE-binned airglow background + Background2D | MoG Sersic rendering, not independently validated in the repo | Borrow pieces (background model, PSF-kind dispatch, SAPM units, channel grid) |
| jgagneastro/SPIFF | Gagne et al. 2026 pipeline; MIT; 11 commits | MIT | QR2 only (cube PSF, MP_* flags, hard-coded collections) | PSF fit with floating position, scipy + UltraNest, 15-px median background, error-weighted binning to 102 channels | none | Borrow pieces (PSF-zone selection, S3 byte-range cutouts, WCS-WAVE interpolation, binning, retry logic) |
| freddavies/spherextract | Davies; successor of spherex-tools + SPIFF; no license; unreviewed branches | none | QR2 only | 2D optimal (matched-filter) extraction with flux-conserving PSF downsample; 2-3 source linear deblending | none | Borrow ideas (deblending normal equations, ExtractionResult schema); license must be clarified before copying |
| WenkeRen/spxquery | PyPI 0.4.1, ReadTheDocs, CI; last commit 2026-07-11 | MIT | QR2 only (requires 7 extensions and 101x101x121 PSF) | FWHM-adaptive apertures, window and annulus backgrounds; `drizzle3d` spatial+spectral cube with inverse-variance weights and flag propagation | cubes only, no profile fits | Borrow pieces (drizzle3d, background estimators) after patching for QR3 |
| fkiwy/spexpi | Kiwy; RNAAS + Zenodo; no tests | MIT | QR2 only; `qr3` not recognized | aperture and weighted-linear PSF fit with centroid grid search; SAPM flux calibration | none | Borrow pieces (PSF kernel extraction, PSF fit, SAPM use) |
| leejjoon/sphx_spec_stack | Lee; 9 commits; no LICENSE file | MIT (classifier only) | n/a (no FITS access) | Gaussian-process super-resolution stacking of pooled (wavelength, flux, variance) samples via tinygp | region-agnostic pooling only | Borrow the GP reconstruction routine; add rest-frame shift and refit hyperparameters |
| banados/spherex-tools | Banados; 2025; no tests | MIT | SIA without release pinning | central 2x2 pixel box minus median of a 6x6 cutout; no flags, no PSF | none | Ideas only |
| afaisst/SPHERExSpecPhot | Faisst (SSDC member) personal repo, Aug 2026; unlicensed | none | QR-era hard-coded flags | fixed circular aperture with annulus; bootstrap errors; VARIANCE unused | none | Ideas only; not the basis of the IRSA tool |
| huntbrooks85/xcavation | Brooks; PyPI; RNAAS | MIT | QR2 TAP query marked "will need updates" | forced circular aperture per exposure, radius from PSF_FWHM | none | Ideas only (retry wrapper, proper-motion utilities) |
| yayasaikou1/spherex-cutoutdb | student; 4 commits in 80 minutes | none | QR2 only | SQLite cutout database, fixed-position PSF fit | rejects extended sources | Ideas only |
| andrijazupic/SPHEREx_pipeline | unmaintained since June 2026; no license | none | via spxquery | spxquery apertures rescaled by a hard-coded regression toward SPIFF fluxes | none | Ideas only (contamination flagging) |
| gregreen/spherex_spectra | Green; JAX + Equinox design study; no license | none | no real-data ingestion | closed-form amplitude solve in a JAX forward model | none | Ideas only (design document) |

Official repositories found but not reviewed in depth: the `SPHEREx` GitHub organization
holds documentation and visualization infrastructure only; `SPHEREx-Sky-Simulator` and
`SPHEREx-Parameters` are referenced by the pipeline as optional extras (the zodi model
lives there) and were not cloned.

## 2. What nobody provides

- Forward modeling of extended galaxies with free shape parameters, or joint fits across
  exposures. The official pipeline and tractorjax-spherex render Sersic profiles but
  freeze positions and shapes from an external catalog; every other tool is point-source
  only.
- An explicit zodiacal-light treatment for photometry. Everyone fits a local background
  per exposure; the only zodi subtraction is the Mosaic Tool's IMAGE minus ZODI, and the
  only airglow-aware background is the CWAVE-binned model in tractorjax-spherex.
- A spectrum stacker that starts from spectra of different galaxies at different
  redshifts. sphx_spec_stack pools samples but has no rest-frame step.
- Complete QR3 support outside the two hbahk repositories. Every other reader assumes the
  QR2 PSF cube and MP_* flag names.
- Validation on resolved sources. The one relevant validation is Bahk et al. 2026
  (arXiv:2606.19875, galaxy clusters, classic Tractor), which should be read before we
  design our extended-source fits.

## 3. Recommended plan

Build our own thin pipeline on top of two official and one third-party component, and
copy well-defined functions from the rest.

1. Retrieval and PSF preparation: `hbahk/spherex-retrieval` (MIT). It already does what
   we verified by hand: TAP discovery for QR3, cutout bundles with a manifest, QR2 and
   QR3 PSF handling, the cutout-to-parent pixel convention, ePSF resampling, and QR2 to R7
   flux corrections with variance propagation. Vendor it (copy the package into our repo)
   rather than depend on an unpublished package; keep its regression tests.
2. Rendering: `Caltech-IPAC/tractor-spherex` for the Lanczos shift and the FFT rendering
   of point sources and Sersic profiles through the oversampled ePSF, plus the standard
   Tractor `PointSource`, `SersicGalaxy`, `LinearPhotoCal` and `optimize_forced_photometry`
   API. Cost: a C/SWIG build and the astrometry.net Python utilities. Fallback if the
   build is painful: upstream `tractor` plus the corrected `OversampledPixelizedPSF`
   subclass from tractorjax-spherex.
3. Photometry layer (ours): per exposure, subtract ZODI, fit the local background with
   the official `estimate_loc_bkg` configuration (spherex-pipelines `window_utils.py`) or
   the CWAVE-binned model from tractorjax-spherex, then fit flux with positions and shapes
   frozen from optical imaging (unresolved and semi-resolved) or aperture and isophotal
   photometry (resolved). Use `MJysr_to_uJy` with the Solid Angle map and the official flag
   aggregation within 2.5 pixels. Read `perform_forced_photometry.py` and
   `estimate_diffuse_background.py` as the specification.
4. Spectrum assembly: per-measurement CWAVE/CBAND at the fitted position
   (spherex-retrieval `wavelength_at`), then SPIFF-style inverse-variance binning onto the
   102-channel grid (`spherex_binning.py`, or tractorjax `spectra.py`).
5. Stacking: rest-frame shift and normalization ourselves, then either a median with
   bootstrap errors or the tinygp reconstruction from sphx_spec_stack with refitted
   hyperparameters.
6. Resolved galaxies and quick looks: adapt `spxquery.drizzle3d` for our own
   inverse-variance cubes with flag propagation, after patching its MEF reader for QR3.
7. Validation: compare every test galaxy with the IRSA Spectrophotometry Tool output
   (point and Sersic modes) and with 2MASS/WISE synthetic photometry; reproduce the Bahk
   et al. 2026 extended-source tests on a simulated Sersic galaxy injected into real
   cutouts.

License notes: MIT for spherex-retrieval, SPIFF, spxquery, spexpi; BSD-3 for
spherex-pipelines; GPLv2 for tractor-spherex (fine as a dependency); GPL-3 for
tractorjax-spherex (copying code into our repo would make our code GPL; re-implement the
ideas instead); spherextract, SPHERExSpecPhot, spherex_spectra and SPHEREx_pipeline have
no license and must not be copied.

## 4. Open items before adopting anything

- Confirm that tractor-spherex builds in our `uv` environment (astrometry.net utilities
  are an undeclared dependency).
- Check whether spherex-retrieval's ePSF calibration source (`psf_source="epsf-cal"`)
  matches what the September 2026 IRSA tutorial recommends for QR2 images.
- Read Bahk et al. 2026 (arXiv:2606.19875) for the extended-source validation results
  and the failure modes at low surface brightness.
- Decide whether shapes for semi-resolved galaxies come from SDSS/DESI Legacy Survey
  models or from our own fits to deeper imaging.
