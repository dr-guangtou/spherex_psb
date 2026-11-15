# WenkeRen/spxquery

## Metadata

- **Author/maintainer**: Wenke Ren (`wenkeren.astro@gmail.com`, GitHub `WenkeRen`). No institutional affiliation stated in README, `pyproject.toml`, or docs; commit history shows collaborative commits from a Claude-associated account alongside Wenke Ren's own commits (AI-assisted development), but a single human maintainer.
- **License**: MIT (`LICENSE` file present, and declared in `pyproject.toml`).
- **Language**: Python, requires >=3.11 (supports 3.11–3.13).
- **Stars/forks**: 10 stars, 3 forks, 0 open issues (as of 2026-09-23).
- **First commit**: 2025-11-05. **Last commit**: 2026-07-11 ("fix: update colormap validation to use matplotlib.colormaps API"). 87 commits total per GitHub.
- **PyPI**: published, `pip install spxquery`, current version **0.4.1** (uploaded 2026-05-19; `INSTALL.md` in the repo is stale and still says "PyPI installation coming soon" / expects `0.2.0`, so docs lag the released package).
- **Tests**: `tests/test_advanced_config.py` (437 lines) plus a GitHub Actions workflow (`.github/workflows/python-package.yml`); `pyproject.toml` wires `pytest`, `pytest-cov`, `ruff`, `mypy` as dev dependencies with `addopts = "-v --cov=spxquery --cov-report=html --cov-report=term"`. Test coverage is limited to configuration validation, not photometry correctness.
- **Docs**: ReadTheDocs site ([spxquery documentation](https://spxquery.readthedocs.io), Sphinx + `myst-parser` + `nbsphinx`), plus an in-repo `docs/` tree (API reference stubs, user guides for batch photometry, cutouts, drizzle3d, parameters, pipeline, quality control) and a `CONTRIBUTING.md`.
- **Associated paper**: none found; only a generic "Based on SPHEREx data from NASA/IPAC IRSA" acknowledgment.

This is the most actively developed and best-packaged of the three repos reviewed.

## Purpose and scope

SPXQuery automates an end-to-end "query → download → photometry → visualization" workflow for **time-domain** analysis of SPHEREx spectral-image data at a fixed sky position (its flagship demo is a light curve/spectrum of the Cloverleaf quasar). Alongside the core single-position pipeline it ships two significant extensions relevant to our use case: a `batch/` module for running many sources through the pipeline, and a `drizzle3d/` module that combines multiple dithered SPHEREx exposures into a true 3-D (X, Y, λ) spectral cube — i.e., resolved/IFU-like output, not just a single aperture light curve.

## Data access layer

- **TAP**: hard-coded IRSA TAP endpoint `TAP_URL = "https://irsa.ipac.caltech.edu/TAP"` (`src/spxquery/core/query.py`), queried via `pyvo.dal.TAPService` with synchronous-first/async-fallback execution (`_execute_tap_query`). The ADQL query joins `spherex.artifact` and `spherex.plane` tables and parses `obs_publisher_did` (format `ivo://irsa.ipac/spherex_qr?<obsid>/D<n>`) with a hard-coded regex — this schema/format is IRSA's current QR-era metadata model and would need revisiting if IRSA changes table names or the `obs_publisher_did` convention at DR1.
- **Cutouts**: supports server-side cutout download to avoid pulling full 2040×2040 parent images (~99% storage reduction claimed in README), configurable by pixel size or angular size (e.g. `"200px"`, `"3arcmin"`).
- **Caching/resumability**: pipeline state is persisted to YAML (`{source_name}.yaml`) after every stage, enabling `pipeline.resume()`; downloads support `skip_existing`.
- **drizzle3d** additionally queries IRSA TAP over a sky *region* (`CONTAINS(POINT, poly)`), grouping observations by detector, and downloads in parallel with configurable worker count and a `max_images` safety cap — this is the piece relevant to resolved-source cube-building.
- No S3/IBE access path was found; IRSA TAP + HTTP cutout download only.

## Data model handling

Central class `SPHERExMEF` (`src/spxquery/utils/spherex_mef.py`, ~1100 lines) wraps `astropy.io.fits`:
- Reads extensions **by name** — `IMAGE`, `FLAGS`, `VARIANCE`, `ZODI`, `PSF` — and requires `len(hdulist) >= 7`. It reads `spatial_wcs` from the primary header and a separate `spectral_wcs = WCS(header, fobj=hdulist, key="W")` (i.e., the alternate WCS-WAVE key, exactly as documented for SPHEREx), used in `pixel_to_wavelength()` for per-pixel wavelength/bandwidth. A dedicated `drizzle3d/spectral.py` module *additionally* loads the official `SPECTRAL_CHANNELS` calibration table (CWAVE/CBAND-equivalent, 102 rows = 17×6 bands) from a bundled aux file `spectral_channels_spx_cal-sch-v1-2026-106.fits` to build the standard output wavelength grid — but this calibration file is used only by `drizzle3d`, not by the core single-aperture pipeline, which relies solely on WCS-WAVE.
- **PSF**: the `SPHERExMEF` docstring and reader hard-code the PSF array shape as `(101, 101, 121)` — i.e. the QR2 11×11-zone, 10×-oversampled PSF **cube**. There is **no EPSF handling anywhere in the codebase** (no reference to `EPSF`, `BINX/BINY/XCENTER/YCENTER/NEFF_MEAN`, or the QR3 binary-table PSF format was found by grep). The bundled PSF array is read into the `SPHERExMEF.psf` attribute but a full grep found no PSF-*fitting* code path using it (see Photometry section) — it appears to be carried through but not exploited by the extraction routines.
- **Flags**: decoded via a hard-coded Python dict mapping flag *names* to fixed bit numbers (e.g. `TRANSIENT=0, OVERFLOW=1, SUR_ERROR=2, NONFUNC=6, ... SOURCE=21`), pre-combined into an `int` bitmask (`_BAD_FLAG_BITS`). These bit numbers are **not read from the FITS header** (no MP_* keyword lookup, no MSKN/MSKM QR3-style dynamic mapping) — assumed fixed, matching QR2's documented MP_* layout. If a future pipeline version renumbers bits (as the QR2→QR3 MP_*→MSKN/MSKM change already illustrates), this would silently misclassify pixels rather than error out.
- **ZODI**: read as a separate extension; `subtract_zodiacal_background()` performs explicit ZODI subtraction with amplitude scaling (not simply subtracted at face value) — the actual model, not pre-subtracted.
- **VARIANCE**: read per-pixel; `repair_variance_for_flagged_pixels()` explicitly validates that NaN variance correlates with flagged pixels and raises `ValueError` if NaN appears in *unflagged* pixels (a genuinely useful sanity check rather than silent replacement) before filling with the image-median variance for flagged pixels only.
- **Solid Angle map**: not found — SPXQuery works natively in surface-brightness units (MJy/sr) with an internal MJy/sr→μJy/arcsec² conversion helper (`_get_unit_conversion_factor`, factor 0.02350443) rather than loading the official per-pixel solid-angle calibration product.
- **Cutout-to-parent mapping**: cutouts are downloaded pre-cropped from IRSA's cutout service; WCS in the cutout header is used directly, so no separate parent-to-cutout pixel remapping logic is needed for the core pipeline. `drizzle3d` builds its own output WCS independent of any input cutout/parent frame.

## Photometry / extraction method

Pure **aperture photometry** via `photutils.aperture.CircularAperture` (`src/spxquery/processing/photometry.py`), with the headline feature being **FWHM-adaptive aperture sizing** driven by wavelength-dependent PSF FWHM (read from the `PSF_FWHM` header keyword, falling back to a hard-coded 6.0″ if missing) — not a PSF-fit. No PSF-fitting/forced-photometry code path was found anywhere in the package (`grep -i "psf_fit\|tractor\|forced photometry"` returns nothing), despite the PSF cube being read into `SPHERExMEF.psf`.

**Background**: two interchangeable local methods in `processing/background.py` — `estimate_window_background` (rectangular window around the source with aperture-overlap pixels excluded, sigma-clipped) and an annulus-based method — directly addressing the documented "official SPHEREx source masks are overly conservative" problem by letting the user switch to the window method when annulus background pixels are unavailable near bright/extended contaminants. `fast_sigma_clip` reimplements sigma-clipped mean/median/std with plain NumPy for speed.

**Deblending**: none.

**Error propagation**: aperture-photometry variance propagated per pixel (with the flagged-pixel variance repair described above); no explicit PSF-fit covariance since there is no PSF fit.

**Combining exposures**: multiple epochs/exposures at one position are treated as independent measurements assembled into a `lightcurve.csv` (one row per MJD/band/exposure) rather than co-added into a single spectrum — appropriate for its time-domain design goal, less directly useful for a static-spectrum "combine N exposures into one spectral point" use case (though inverse-variance combination across the resulting rows would be straightforward to add).

**Output format**: `lightcurve.csv` with MJD, flux, wavelength, band, quality flags, SNR — a photometry *table*, not a FITS spectrum, on the native per-visit SPHEREx wavelength sampling (not resampled to the 102-channel grid) for the core pipeline; `drizzle3d`'s cube output (see below) does use the standard 102-channel (17×6) grid when in "native" mode.

## Stacking method

N/A for the core single-aperture pipeline (produces a time series/list of measurements, not a GP-stacked spectrum). The **`drizzle3d` module** is the closest analog to spatial/extended-source combination, but it is a different algorithm class (inverse-variance-weighted spatial+spectral drizzle onto a regular (X,Y,λ) grid, not a GP): per input pixel it computes bilinear spatial-overlap weights onto an output TAN-projected spatial grid and a top-hat spectral-overlap weight onto a configurable Z (wavelength) grid (native 17-bin/detector, log-oversampled, or user-supplied edges), accumulates `Σ(w·f_xy·f_z·F)` and `Σ(w·f_xy·f_z)` per output voxel via vectorized `np.add.at`, and reports `flux = flux_weighted/weight_total`, `variance = var_accum/weight_total²`. This is a genuine, well-engineered multi-exposure combination for resolved sources, but is not a GP-based irregular-sampling stack and has no rest-frame-shifting, normalization, or cross-object stacking concept — it combines multiple *exposures of one field*, not multiple *objects*.

## Extended-source support

The core pipeline is circular-aperture, single-position, point/quasi-point-source oriented (its own README calls out that large official source masks are a known problem "if your target is located in an extended nebula"). No Sersic/galaxy-profile fitting, elliptical apertures, or aperture corrections exist. `drizzle3d`, however, is directly useful for **resolved** sources: it produces a genuine 3-D spectral cube (7-HDU FITS: SCI, VARIANCE, AND_MASK, OR_MASK, COUNT, WAVELENGTH bintable) over an arbitrary user-defined sky region and detector, from which arbitrary spatial apertures/regions (elliptical or otherwise) could be extracted downstream — but region/profile extraction itself is left to the user (demoed only via `example/drizzle3d_demo/ngc4395_explore.ipynb`, an interactive click-to-spectrum notebook).

## Code quality

The best-engineered of the three repos: clear submodules (`core`, `batch`, `drizzle3d`, `processing`, `utils`, `visualization`), Poetry-managed pinned dependencies, `ruff`+`mypy` configured, a GitHub Actions CI workflow, real (if narrow) tests, ReadTheDocs, and per-version changelogs. Docstrings are thorough (NumPy style); `drizzle3d` has its own README and pipeline diagram. Weaknesses for our purposes: hard-coded QR2 assumptions (7-extension minimum, 101×101×121 PSF cube, fixed flag-bit numbers) with **no version detection or EPSF fallback**, so this would likely break on QR3/DR1 EPSF-only files without a patch; `INSTALL.md` is stale relative to the PyPI release; and the bundled CWAVE/CBAND calibration file is pinned to one dated collection with no visible update mechanism.

## Reusable pieces for our project

- `src/spxquery/utils/spherex_mef.py::read_spherex_mef` and the `SPHERExMEF` dataclass — a clean, general MEF reader (WCS-WAVE handling, unit conversion, ZODI/VARIANCE/FLAGS access) that is a good structural template even though its PSF/flag assumptions need updating for QR3.
- `src/spxquery/processing/background.py::estimate_window_background` / `estimate_local_background` — directly reusable dual annulus/window local-background estimators, useful for our own background handling requirement.
- `src/spxquery/utils/spherex_mef.py::create_background_mask`, `get_flag_info`, `check_flag_bits` — a template for flag-based masking logic (bit numbers need re-deriving from QR3 header keywords, MSKN/MSKM, before reuse).
- `src/spxquery/drizzle3d/` (`spatial.py::compute_spatial_mapping`, `accumulate.py::drizzle_image`/`DrizzleCube`, `spectral.py::build_z_grid`) — the most valuable subsystem for our resolved/semi-resolved use case: a working, vectorized multi-exposure spatial+spectral drizzle onto a standard-grid spectral cube, including proper inverse-variance accumulation and AND/OR flag-mask combination across exposures.
- `src/spxquery/processing/photometry.py::repair_variance_for_flagged_pixels` — a useful QA pattern (assert NaN-variance ⟺ flagged) worth adopting regardless of whether the rest of the module is reused.

## Risks and limitations

- Hard assumption of a 7-extension MEF with a `(101,101,121)` PSF cube and fixed flag-bit numbers — will very likely need patching for QR3 EPSF files (different extension name, binary-table format, 33×33/5× oversampled) and any QR3 MSKN/MSKM-driven flag renumbering; no such handling exists today.
- No PSF-fit photometry despite reading the PSF cube — aperture-only, so not directly suited to crowded/blended point sources without extension.
- Docs (`INSTALL.md`) lag the actual PyPI release, a minor but real trust signal to double-check before relying on documented behavior.
- `drizzle3d` combines exposures of one field, not spectra of multiple distinct objects — stacking across our sample of PSB galaxies would still need to be built on top.
- Single (if productive) maintainer; sustained-maintenance risk for a fast-evolving SPHEREx pipeline is unclear beyond the 0.4.x line (last commit 2026-07-11, i.e. before QR3's 2026-07-20 release, so QR3 compatibility is unverified as of this review).

## Verdict

**Borrow pieces.** SPXQuery is the most solid engineering of the three and its `drizzle3d` cube-building code is genuinely valuable for the resolved/semi-resolved side of our project, and its dual background estimators are directly reusable. It should not be adopted wholesale as a dependency, however: its data-model layer is QR2-hard-coded (extension names, PSF cube shape, fixed flag-bit numbers) with no EPSF/QR3 path, so before relying on it for new IRSA downloads it needs to be verified — and likely patched — against current QR3 (pipeline 7.0.x) files.
