# fkiwy/spexpi

## Metadata

- **Author**: Frank Kiwy (GitHub `fkiwy`). No institutional affiliation stated; personal-project styling (custom emblem image, brown-dwarf/ultracool-dwarf focus suggests an amateur/citizen-science or independent-researcher background, consistent with Kiwy's known WISE/brown-dwarf discovery work, though this is not stated in the repo itself).
- **License**: MIT (`LICENSE` file present, copyright 2026 Frank Kiwy).
- **Language**: Python, requires >=3.10.
- **Stars/forks**: 0 stars, 0 forks, 0 open issues (as of 2026-09-23).
- **First commit**: ~2026-05-05. **Last commit**: 2026-05-23 ("Update citation section in README"). ~57 total commits on the `master` branch (per GitHub repo summary), all in under three weeks.
- **PyPI**: not published (install is `git clone` + `pip install .`).
- **Tests**: **none found** — no `tests/` directory, no CI workflow file.
- **Docs**: no ReadTheDocs/Sphinx site; documentation lives entirely in a long, detailed `README.md` (full API reference section, configuration reference, troubleshooting, recommended workflow).
- **Associated paper**: yes — this is the only one of the three repos with a real publication. Cited via Zenodo archive (DOI `10.5281/zenodo.20287823`) and an RNAAS research note (DOI `10.3847/2515-5172/ae707b`).

## Purpose and scope

SPExPI extracts and inspects low-resolution SPHEREx spectrophotometry **of point sources**, explicitly designed around ultracool-dwarf science (including high proper-motion targets) but stated to generalize to "any isolated point source covered by SPHEREx image products." It bundles three workflows: (1) spectrum extraction via aperture photometry, PSF photometry, or both in one run; (2) spectral-type template matching via chi-square comparison against a bundled L0–T9 standards library; (3) multi-detector image stacking/plotting for visual QA. It is the only one of the three repos that performs true PSF-fit photometry from the native SPHEREx PSF cube.

## Data access layer

- **IRSA TAP** for cutout discovery (`query_spherex_cutouts`), plus two download backends: `download_backend="http"` (IRSA HTTP cutout service, the documented default/fastest path) and `download_backend="s3_cutout"` (direct S3 parent-image access via `fsspec`/`s3fs`, with a documented `s3_cutout_fallback_to_http` option — noted in the README as slower because the full parent FITS must be streamed).
- **Data-release inference**: rather than requiring a user-supplied release, the pipeline infers it from (in order) the source URL/S3 key, the local cached file path, or FITS header keywords (`DATAREL`, `OBS_COLLECTION`, `COLLECTION`, etc.), then **stamps `DATAREL` back into the cached FITS file** so re-runs on cached data are self-contained. `infer_data_release_from_uri`/`_from_header`/`_from_fits` and `normalize_data_release` recognize `qr1`, `qr2`, `qr2_deep` by substring matching on URLs/paths — **`qr3` is not in the recognized set**, so as shipped it would silently fall through to `"unknown"` (which then hard-fails calibration loading, e.g. `load_sapm` explicitly raises `ValueError` when the release is unknown) rather than mis-tagging data, which is at least a fail-safe (not fail-silent) behavior.
- **Calibration caching**: solid-angle pixel maps (SAPM) and `spectral_channels` calibration files are fetched from the public SPHEREx S3 bucket (anonymous `fsspec`/`s3fs` access) and cached locally under a directory tree keyed by inferred release and calibration-collection name (e.g. `cal-sapm-v2-2025-164`, `cal-sch-v1-2026-106`), with `redownload_*` flags to force refresh. Collection version strings are user-configurable, not hard-coded to one value, which is a real strength (in contrast to spxquery's single pinned collection).

## Data model handling

- Reads MEF extensions by name: `IMAGE`, `FLAGS` (optional, `if "FLAGS" in hdul`), `VARIANCE` (optional), `ZODI` (optional), `PSF` (optional) — the pipeline degrades gracefully when an extension is absent rather than requiring a fixed extension count (unlike spxquery's `len(hdulist) >= 7` assertion).
- **PSF**: hard-codes the QR2 PSF-cube model — `extract_spherex_psf_kernel` reads a 3-D cube, infers the zone grid as `ngrid = round(sqrt(nplanes))` (defaulting to 11, i.e. the 11×11=121-zone layout), reads `OVERSAMP` from the PSF header (default 10), selects the nearest zone plane to the source position, sub-pixel-shifts it via `scipy.ndimage.shift`, and downsamples oversampled→native pixels by block-summing. A dedicated, documented workaround (`fix_psf_zone_ordering`/`psf_fix_applied`, ~90 lines) fixes a **known bug in some cached QR2 files' PSF per-plane zone metadata ordering** (`XCTR_*`/`YCTR_*`/`XWID_*`/`YWID_*`), rewriting to consistent x-fast ordering and stamping a `+psffix1` tag — genuinely useful, hard-won domain knowledge. **No EPSF (QR3, binary-table, 33×33, 5× oversampled) handling exists**; the extractor unconditionally requires `psf_cube.ndim == 3` and would raise on a QR3 EPSF-only file.
- **Flags**: same pattern as spxquery — a hard-coded tuple of "fatal" bit numbers (`bad_flag_bits = (0,1,2,4,6,7,9,10,11,14,15,17,19,22,24,26,27,28,29)`, a superset of spxquery's list, notably including bits 4, 22, 24, 26–29 that spxquery omits), applied via `(flags & mask_value) != 0`; no MP_*/MSKN/MSKM header-driven bit lookup, so a QR3 bit renumbering would not be detected automatically.
- **Wavelengths**: no direct evidence of WCS-WAVE usage in the core per-pixel flux extraction (the PSF/aperture routines operate at a fixed source pixel position rather than sweeping wavelength across the image); the *output* spectrum grid instead comes from (a) the native per-cutout central wavelength stored per exposure, optionally reduced/binned using the official `spectral_channels` (CWAVE/CBAND-equivalent) calibration table when `use_spectral_channels_for_binning=True`, with a documented `spectral_channels_bin_by="integrate"` mode, or (b) a hard-coded fallback of per-detector resolving power and 17-bin grids (`reduce_oversampling_per_detector`: bands defined as `{1:(0.75,1.11,41), 2:(1.11,1.64,41), 3:(1.64,2.42,41), 4:(2.42,3.82,35), 5:(3.82,4.42,110), 6:(4.42,5.00,130)}`) when the calibration file is unavailable.
- **ZODI**: read as an optional extension and carried through `process_cutout_row`, but no dedicated subtraction/model-amplitude-scaling function was found in the areas inspected (contrast with spxquery's explicit `subtract_zodiacal_background`) — treat as present-but-thin in this repo.
- **VARIANCE**: read and propagated through both aperture and PSF photometry as `var_ujy2` after SAPM-based unit conversion.
- **Solid Angle map**: explicitly and centrally used — `load_sapm` downloads/caches the official per-detector SAPM FITS product from S3 and applies it as the MJy/sr→flux-density calibration step before any photometry, which is the physically correct calibration path (this is the one repo of the three that uses the official SAPM product rather than an assumed pixel-scale-based conversion).
- **Cutout-to-parent mapping**: cutouts are either IRSA-server-cropped (HTTP backend) or locally cropped from S3-streamed parent images (S3 backend); WCS in the cutout is used directly for source positioning, with proper-motion epoch propagation (`project_to_epoch`) applied per-exposure before flux extraction — important for the high-PM ultracool-dwarf use case, less relevant for extragalactic PSB targets (proper motion negligible) but harmless/ignorable.

## Photometry / extraction method

Both aperture and PSF methods are implemented and can run side-by-side (`photometry_method="both"`):
- **Aperture**: `photutils.aperture.CircularAperture` at multiple configurable radii (diagnostics) with one `selected_aperture_radius_pix` chosen for the final spectrum; local **annulus** background with configurable sigma clipping and choice of `mean`/`median`/`mode` estimator; bad pixels excluded from both source aperture and background annulus, with known-object masking applied only to the background annulus (not the source aperture).
- **PSF**: `psf_flux_fit` — weighted linear least-squares fit of `image = flux·PSF + background [+ dx + dy]` using the native-pixel PSF kernel extracted above; optional local grid-search centroid refinement (`enable_psf_local_grid_search`, configurable half-range/step, optimizing `snr` or `chi2`) around the WCS-predicted position, addressing SPHEREx's imprecise absolute astrometry for faint sources. Optional background-gradient term (`psf_fit_background_gradient`).
- **Deblending**: none (single-source model only in the PSF fit; no simultaneous multi-source fit).
- **Error propagation**: per-pixel VARIANCE flows through both methods (aperture sums propagate variance in-aperture; the PSF fit is a weighted linear model using `var_ujy2` as weights).
- **Combining exposures**: each cutout/epoch is measured independently (`measure_cutout_photometry`) and assembled into a raw spectrum table (`build_spectrum_table`); combination across repeated exposures at the same nominal wavelength happens via the same inverse-variance-weighted binning step used for oversampling reduction (`reduce_oversampling_per_detector`/`reduce_oversampling_with_spectral_channels`), i.e. exposure-combination and spectral-oversampling-reduction are the same binning operation, not a separate co-add step.
- **Output format**: a FITS binary table per method (`<object>_aperture_spectrum.fits`, `<object>_psf_spectrum.fits`) with columns `WAVELENGTH [um]`, `FLUX [Jy]`, `ERR [Jy]`, `DETECTOR`; optional raw per-cutout measurement FITS and CSV/JSONL provenance manifests. Output can be binned onto the standard SPHEREx spectral-channel grid (via `spectral_channels`) or left on a hard-coded per-detector 17-bin grid.

## Stacking method

N/A — no multi-object or multi-region stacking of any kind. Within a single object, repeated exposures are combined only via wavelength-bin averaging (inverse-variance-weighted, per `reduce_oversampling_per_detector`), not a GP or other super-resolution method, and there is no cross-object combination logic at all. `spectrum_comparator.py`'s chi-square template matching is a *comparison* tool (observed vs. library templates), not a stack.

## Extended-source support

Point-source only, by explicit design. No Sersic/galaxy-profile fitting, no elliptical apertures, no aperture corrections, and the PSF model itself assumes a single point source at one (proper-motion-corrected) position. Using this on a resolved or semi-resolved PSB galaxy would require substantial modification (multi-position sampling, aperture-correction curves, or an entirely different PSF-forward-model formulation).

## Code quality

A single very large module (`spherex_pipeline.py`, 3494 lines) holding config, I/O, calibration, both photometry methods, spectrum assembly, and plotting — functionally organized (well-documented NumPy-style docstrings, and an accurate "Complete API documentation" README section) but not modularized, with **zero automated tests**. Genuinely strong points: graceful degradation when optional extensions are missing, an explicit fix for a real QR2 PSF-metadata bug, and a release-inference/self-stamping scheme more robust to unlabeled cached files than spxquery's simpler substring matching. Weak points: release inference does not recognize `qr3` (fails safe to "unknown"), the PSF path is unconditionally 3-D-cube-shaped with no EPSF fallback, and the flag-bit list is hard-coded with no header-driven remapping — the same QR2-lock-in risk as spxquery, without spxquery's CI/test safety net.

## Reusable pieces for our project

- `src/spexpi/spherex_pipeline.py::extract_spherex_psf_kernel` — a complete, working native-pixel PSF-kernel extraction from the QR2 121-zone PSF cube (nearest-zone selection, sub-pixel shift via `ndimage.shift`, oversample block-summing) — the most directly reusable PSF-handling code among the three repos, and a good template for what an EPSF-based (QR3) equivalent would need to do.
- `src/spexpi/spherex_pipeline.py::psf_flux_fit` and `psf_flux_fit_with_local_grid_search` — weighted-linear PSF photometry with optional background gradient and SNR/χ²-optimized centroid grid search; directly relevant to our own PSF-forward-modeling requirement even if the multi-source/deblending extension has to be added ourselves.
- `src/spexpi/spherex_pipeline.py::fix_psf_zone_ordering` / `psf_fix_applied` — worth reading even if not reused, as documentation of a genuine QR2 data-quality gotcha in PSF-cube header metadata.
- `src/spexpi/spherex_pipeline.py::load_sapm` and the SAPM-based calibration path — the one instance among the three repos of using the official solid-angle pixel map product; a good reference for correct MJy/sr↔flux-density calibration.
- `src/spexpi/spherex_pipeline.py::infer_data_release_from_uri/_from_header/_from_fits`, `stamp_data_release_in_fits` — a reusable pattern for making a local FITS cache self-describing and release-aware, useful groundwork for handling a mixed QR2/QR3/DR1 corpus.
- `src/spexpi/spectrum_comparator.py::SpectrumTemplateComparator` — chi-square/least-squares spectral-type template matching against a bundled L0–T9 standards library; not directly applicable to PSB galaxies but a clean pattern if a comparison-to-template step is ever needed.

## Risks and limitations

- No EPSF/QR3 support in the PSF path; would need real development work to extract PSF kernels from 33×33/5×-oversampled binary-table EPSF stamps instead of the 121-zone cube.
- `normalize_data_release`/`infer_data_release_from_*` do not recognize `qr3` (only `qr1`, `qr2`, `qr2_deep`), so as-shipped it would treat QR3 files as "unknown release" and fail calibration loading rather than working correctly, until patched.
- Zero test coverage on a 3500-line core module; any reuse should be validated independently before trusting outputs.
- Point-source-only design (single-position PSF/aperture model, no extended-source machinery) — not directly usable for resolved/semi-resolved PSB galaxies without substantial extension.
- Hard-coded flag-bit list, same header-driven-remapping gap as spxquery.
- No packaging release (PyPI) and very short active-development window (< 3 weeks of commits), single author, 0 stars — maintenance trajectory beyond the RNAAS publication is unclear.

## Verdict

**Borrow pieces.** SPExPI is the only one of the three repos with genuine, working PSF-forward-model photometry from the native SPHEREx PSF cube (plus a documented real-world PSF-metadata bug fix and correct SAPM-based flux calibration), which makes its PSF-extraction and PSF-fitting functions valuable reading and a reasonable starting point to adapt for our own point-source PSF modeling — but it is untested, QR2-locked (no EPSF/QR3 path, no `qr3` release recognition), and point-source-only, so it should not be used unmodified, especially not for the semi-resolved/resolved PSB galaxies that are part of our science case.
