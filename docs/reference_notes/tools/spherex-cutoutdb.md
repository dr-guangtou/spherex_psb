# yayasaikou1/spherex-cutoutdb

## Metadata

- **Author**: GitHub user `yayasaikou1` ("yayasaikou"), self-described as "a student" at the **University of Chinese Academy of Sciences** (per GitHub profile). No named co-authors.
- **License**: No open-source license. `LICENSE` states: "No open-source license has been selected in this release candidate. All rights are reserved unless the project maintainers provide a separate license grant." GitHub reports `license.key = "other"` / SPDX `NOASSERTION`.
- **Language**: Python (>=3.10), ~16,200 lines of source under `src/spherex_cutoutdb/` (excludes tests/docs).
- **Stars/forks**: 3 stars, 0 forks (as of 2026-09-23).
- **Commits**: only 4 commits, all within ~80 minutes on **2026-05-09** (11:33–12:44 UTC). `created_at` and last push are the same day; `updated_at` (2026-09-18) reflects only metadata/star activity, not new commits — this is the entire commit history.
- **Open issues**: 0. One GitHub release, `v1.0.0rc1` (2026-05-09), matching the packaged version `1.0.0rc1` in `pyproject.toml`.
- **PyPI**: not published (`pypi.org/pypi/spherex-cutoutdb/json` and `spherex_cutoutdb` both 404). README instructs installing a locally-built wheel or `pip install -e ".[dev]"`.
- **Tests**: yes — 14 test modules under `tests/` (catalog, database, downloader, photometry pipeline, planner, SIA parser, validator, etc.), using `pytest` with a `live_irsa` marker for optional live-network tests, plus `responses` for mocking HTTP. Depth not fully audited but the presence of dedicated science/pipeline/mask tests is a positive sign.
- **Docs**: extensive — `docs/` contains 20 Markdown files including `DATA_MODEL.md`, `science_method.md`, `qa_flags.md`, `PHOTOMETRY_TUTORIAL.md`, `INTEGRATED_WORKFLOW_TUTORIAL.md`, `DOWNLOAD_STRATEGY.md`, `calibration.md`, `VALIDATION_PLAN.md`; built with MkDocs and published on Read the Docs (`spherex-cutoutdb.readthedocs.io`).
- **Associated paper**: none found; no citation file, no arXiv/ADS link.
- **Note on provenance**: the extreme thoroughness of the docs/tests/config-validation layers, delivered in a single ~80-minute commit burst by a single student author, strongly suggests heavy LLM/code-generation assistance rather than organic development over time. This does not by itself indicate incorrectness, but the code has not been exercised by real users beyond the author, has no issue-driven bug history, and should be treated as unvetted regardless of its polished appearance.

## Purpose and scope

`spherex-cutoutdb` is a command-line tool (`spxcutdb`) that turns an input catalog of (RA, Dec) targets into a local SQLite-backed "cutout database": it discovers overlapping SPHEREx Level-2 spectral-image MEFs via IRSA SIA2, downloads per-target cutouts, and runs a **fixed-position PSF forced-photometry** pipeline on each cutout to build a per-source flux-vs-wavelength CSV table ("spectrum"). It is explicitly **point-source only** — the docs describe it as "conservative PSF forced-photometry," and the pipeline actively flags/deprioritizes anything that looks extended (see below). Intended targets are individual point-like sources at known sky positions, not maps, moving objects, or resolved galaxies.

## Data access layer

- Discovery uses IRSA's **SIA2** service (`irsa_sia.py`) with `COLLECTION`, `POS=circle ra dec radius`, `RESPONSEFORMAT=VOTABLE`, `MAXREC` parameters, parsed via `astropy.io.votable` with careful FIELD-name-vs-ID reconciliation (`_votable_to_dataframe`). Default collections are hard-coded to **`spherex_qr2`, `spherex_qr2_deep`** with `spherex_qr2_cal` excluded — there is no QR3/DR1 awareness anywhere (no `spherex_qr3` string appears in the source).
- Cutout retrieval is via the on-prem IRSA cutout access URL pattern (`access_url` + `?center=<ra>,<dec>&size=<size_deg>`), handled by a large (`downloader.py`, ~1930 lines) file-level downloader with retry/backoff, an event-stream/state-machine model (retryable/nonretryable/open failures), configurable worker pools, and a SQLite-recorded manifest per download.
- Calibration products (Spectral WCS `CWAVE`/`CBAND` and the Solid Angle Pixel Map) are separately synced from either the public **AWS Open Data S3 bucket** (`s3://nasa-irsa-spherex/qr2/...`) or the **IRSA IBE** directory listing, resolved per-detector, hashed (SHA256) and version-tracked in SQLite with a fail-closed policy (`version_policy: exact_required`) if the calibration release doesn't match `QR2` exactly.
- Config defaults are aggressive: 64 file-level download workers, 2048 per-host concurrency, 4096 request-starts/sec, 64 calibration workers, 32 fit workers — far above what IRSA's cutout service tolerates in practice (per `spherex-retrieval`, IRSA returns HTTP 503 above ~4 concurrent cutout requests), so these defaults are unrealistic/risky rather than validated.
- A local SQLite database (`schema.sql`, `database.py`, 682 lines) tracks sources, discovered products, matches, download work items, calibration products, photometry runs/measurements, and output manifests — a fairly complete relational schema for a reproducible pipeline state machine.
- Caching: SIA2 discovery results are cached with a TTL keyed on source/config hash (skippable with `--force-discovery`); calibration products are cached under `cache/calibrations` with SHA256 provenance.

## Data model handling

- Reads exactly four things from each cutout FITS: `IMAGE`, `VARIANCE`, `FLAGS`, and `PSF` (`photometry/fits_io.py`, `load_cutout`). **There is no `EPSF` handling anywhere in the codebase** (`grep` for `epsf`/`qr3`/`NEFF_MEAN` returns nothing in `src/`). The `PSF` extension is assumed to always be the QR2-style plane/cube; `photometry/psf.py` reads per-plane `XCTR_i`/`YCTR_i` header keywords (including a QR2-specific header-erratum fix for `VERSION <= 6.5.5`) and picks the nearest PSF zone to the target's detector position — this logic will simply break (raise `ValueError`, or silently mis-select) on a QR3/pipeline-7.x EPSF binary table.
- Flags: `photometry/constants.py` hard-codes a Python dict `SPHEREX_IMAGE_FLAG_BITS` with 27 named bits (`TRANSIENT`, `SOURCE`, `PERSIST`, `GHOST`, `SNOWBALL`, etc.) matching known QR2 bit assignments, **not read dynamically from the `MP_*` header keywords**. If QR3's `MSKN`/`MSKM` scheme changes bit meanings or numbering, this table will silently misinterpret flags rather than fail loudly.
- Wavelengths: uses the recommended **Spectral WCS `CWAVE`/`CBAND`** calibration product (`photometry/spectral_wcs.py`), not the approximate `WCS-WAVE` per-pixel lookup — this matches best practice. Wavelength/bandwidth are sampled either at the PSF-template-weighted centroid or the cutout center.
- `ZODI`: only used for **structural validation** (shape/dtype check against `IMAGE`, recorded in the SQLite `zodi_shape` column) — never subtracted, never used as a background prior. This is stated explicitly: `photometry_code_version = "photometry_psf_wls_v6_nozodi_failclosed_bkgfallback"`.
- Solid Angle map: required calibration product `solid_angle_pixel_map`; converted from arcsec² to steradians and used to convert `IMAGE`/`VARIANCE` from MJy/sr to µJy/pixel and (µJy/pixel)² (`photometry/solid_angle.py`).
- Cutout-to-parent pixel mapping: `fits_io.py` strips alternate/SIP WCS cards to build a clean spatial WCS per cutout; detector-frame coordinates for PSF-zone selection come from the cutout header's own keywords, not a separately validated cutout→parent-pixel offset like `spherex-retrieval`'s `CRPIX1A`/`CRPIX2A` convention (no evidence of the sign-convention issue that `spherex-retrieval`'s tests specifically regression-test).

## Photometry / extraction method

- **Fixed-position PSF forced photometry** via a weighted linear fit (`photometry/linear_fit.py`, `weighted_linear_fit`): the target PSF template (and any "material" neighbor templates found by `neighbors.py`) are fit jointly to the background-subtracted, variance-weighted cutout pixels, i.e. a simple linear (not full Tractor-style nonlinear) forced-photometry solve.
- PSF preparation (`photometry/psf.py`): selects nearest PSF-cube plane by detector position, normalizes to unit total flux, and rebins the ~10×-oversampled cube onto the native pixel grid at the sub-pixel source position (`_bin_oversampled_psf`).
- Background: `photometry/background.py` (842 lines) does source-masked local 2D plane fitting with iterative 3σ clipping, a `photutils`-based fallback, and multiple explicit failure/fallback flags (`BACKGROUND_2D_FALLBACK_CONSTANT`, `BACKGROUND_2D_UNSTABLE`, `BACKGROUND_POOR`).
- Deblending: `neighbors.py` finds "material" neighbor sources via connected-component analysis on the flag/residual maps and includes them as additional templates in the joint linear fit, with explicit protections (`TARGET_PROTECTED`, `TARGET_SPLIT_PROTECTED`) so the target footprint itself is never split into artificial neighbors.
- Error propagation: variance-weighted least squares with per-pixel invalid-variance masking; extensive per-region (core/fit-stamp/background) QA statistics (mask fractions, flag fractions, PSF-weighted bad-pixel fractions) are computed and stored (`photometry/masks.py`).
- Combination of exposures: **none** — "every valid cutout with valid calibration gets a target-position point-source PSF forced measurement" (per `docs/science_method.md`); each exposure/cutout yields one row in the output table. No stacking, coaddition, or inverse-variance combination of repeat visits into a single flux point.
- Output format: one CSV per source (`results/spectra/<source_name>.csv`) with columns for wavelength/bandwidth (µm), `point_flux_uJy`/`point_flux_err_uJy`/`point_snr`, `detection_status`, `science_recommended`, dozens of QA columns, plus a JSON provenance/manifest sidecar tying the CSV to calibration IDs, config hash, and code version. Also produces per-source SED PNGs and optional full per-measurement QA PNGs.

## Extended-source support

None. The pipeline is point-source-only by design, and it treats apparent extension as a **rejection condition**: `FLAG_TARGET_POSSIBLY_EXTENDED` and `FLAG_TARGET_PSF_MISMATCH` are explicit blocker flags in `science_selection.py` that set `science_recommended=False` when the joint PSF fit looks unstable or extended (`measure.py` lines ~136, ~194, ~239). There is no Sersic fitting, no elliptical aperture, and no aperture-correction machinery anywhere in the codebase. For resolved/semi-resolved post-starburst galaxies this tool would actively flag the target as unreliable rather than extract a spectrum.

## Code quality

- Structure is modular and idiomatic (dataclasses with `slots=True`, clear separation of discovery/download/calibration/photometry/output concerns, a real SQLite schema, `pydantic`-validated config).
- No hard-coded local filesystem paths found; paths are all config/CLI-driven.
- **Not robust to QR3**: no EPSF reading, no QR3 collection strings, hard-coded QR2 flag-bit table, and a calibration resolver that fails closed on anything but an exact QR2 version match. Everything about the flag/PSF/wavelength model assumes QR2 pipeline 6.4–6.5.7.
- Tests exist (14 files) but given the single-day, single-author commit burst, coverage against real IRSA data/live services is unverified (tests appear to rely on `responses` mocks and a bundled `tests/data/mock_sia_response.xml`, i.e. limited real-world validation).
- Aggressive default concurrency (thousands of in-flight requests) is a practical risk against IRSA's actual rate limits.

## Reusable pieces for our project

- `src/spherex_cutoutdb/irsa_sia.py` — clean, well-tested SIA2 VOTable discovery and normalization (`_votable_to_dataframe`, `normalize_sia_dataframe`, `query_sia_for_source` with retry/backoff) is a solid reference for querying `spherex_qr2`/`spherex_qr2_deep` collections; would need collection-name updates to cover QR3.
- `src/spherex_cutoutdb/photometry/masks.py` — the systematic per-region (core/fit-stamp/background) QA-fraction bookkeeping (`build_photometry_masks`) is a useful pattern for quantifying flag contamination around a source, independent of whether one reuses the exact bit table.
- `src/spherex_cutoutdb/photometry/background.py` — the source-masked iterative-clipping 2D background estimator with explicit fallback/failure states is a reasonable starting point for a custom background model, though it would need adaptation for extended targets.
- `src/spherex_cutoutdb/photometry/spectral_wcs.py` and `solid_angle.py` — small, self-contained, correctly use `CWAVE`/`CBAND` and SAPM-based MJy/sr→µJy conversion; easy to lift as reference even if not used verbatim.
- The **documentation set** (`docs/science_method.md`, `docs/qa_flags.md`, `docs/DATA_MODEL.md`) is a useful checklist of QA flags and conventions to compare against, even where we disagree with the design choices (e.g., no ZODI use, no exposure combination).

## Risks and limitations

- No open-source license — cannot legally reuse code verbatim without contacting the author for a grant; can only "read for ideas."
- Hard-locked to QR2 (pipeline 6.4–6.5.7): no EPSF, no QR3/DR1 collections, hard-coded flag bits keyed to QR2 `MP_*` assignments. Given QR3 has been current since 2026-07-20 and DR1 is expected late 2026, this tool is already behind the data releases our project needs.
- Point-source-only architecture actively penalizes extended targets rather than modeling them — unsuitable for resolved/semi-resolved post-starburst galaxies without a substantial rewrite of the template/fit machinery.
- No stacking/coaddition of repeat visits — spectra are per-exposure tables, not combined light curves or averaged spectra; downstream aggregation would need to be built separately.
- Single-author, single-day commit history with no external users, issues, or peer review; despite polished documentation, the code is effectively unvetted.
- Unrealistic default network concurrency settings pose a practical risk of triggering IRSA rate-limiting/503s if used as configured.

## Verdict

**Read for ideas only.** The discovery/calibration-resolution/QA-flag-bookkeeping patterns are well organized and worth referencing, but the tool itself is QR2-only, point-source-only, unlicensed, and has no track record — it cannot be used directly or safely borrowed as code for a project targeting current (QR3) and future (DR1) data with resolved/semi-resolved galaxy targets. `hbahk/spherex-retrieval` (reviewed separately) is a substantially better-matched and better-maintained alternative for the data-access/PSF-preparation layer.
