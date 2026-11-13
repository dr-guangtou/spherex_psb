# hbahk/spherex-retrieval

## Metadata

- **Author**: Hyeonguk Bahk (GitHub `hbahk`), graduate student at **Seoul National University**. Single named author (`pyproject.toml`, `LICENSE`).
- **License**: **MIT**. Freely reusable.
- **Language**: Python (>=3.10), compact — ~3,230 lines across 13 modules in `src/spherex_retrieval/`.
- **Stars/forks**: 3 stars, 0 forks (as of 2026-09-23).
- **Commits**: 14 commits spanning **2026-04-26 to 2026-09-19** (latest: "fix: attach the ePSF library even when the full cutout is already cached"), nearly five months of incremental development, most recent only 4 days before this review — active maintenance, not a single burst.
- **Open issues**: 0. Three tagged releases (`v0.2.0`, `v0.3.0`, `v0.3.1`) published within 24 h on 2026-09-19, but the underlying commit/`CHANGELOG.md` history is genuinely spread over months (`[0.1.0] 2026-04 … 2026-09` was the initial QR2-only work).
- **PyPI**: not published; install is `pip install -e .` from source.
- **Tests**: yes — 6 focused regression-test modules, each with a docstring pinning down a specific previously-real bug (e.g., a pixel-origin sign error that silently mirrored wavelength maps; a PSF-centering off-by-one). Unusually good regression-test hygiene for a small tool.
- **Docs**: one thorough `README.md` (no separate docs site) plus a `CHANGELOG.md` that documents calibration reasoning in detail (gain corrections, PSF-kind differences).
- **Associated paper**: README/CHANGELOG repeatedly cite "the paper's configuration" / "the SPHEREx deblending paper" as the configuration of record for `psf_source="cal"`/`gain_correction=False`, implying this tool underlies an in-progress SPHEREx deblending/forced-photometry paper, though no citation/arXiv ID is given.

## Purpose and scope

`spherex-retrieval` is a **pure data-retrieval and PSF-preparation** library (no fitting/photometry itself). Given a sky position and cutout size, `retrieve()` discovers all overlapping SPHEREx Level-2 spectral-image MEFs across QR2 and QR3 collections, fetches a cropped cutout for each, attaches the correct PSF product (QR2 optical cube or QR3/DR1 effective PSF, whichever the caller asks for), crops the matching per-pixel wavelength (`CWAVE`/`CBAND`) and solid-angle (`SAPM`) calibration maps to the same pixel footprint, optionally applies a QR2→QR3 gain correction, and writes one self-contained MEF "bundle" per overlapping pointing plus a `summary.ecsv` manifest. It is explicitly designed to hand off to "any forward modeller" (the README names Tractor). Targets are implicitly point/unresolved (one PSF per position), but nothing in the retrieval layer prevents feeding cutouts into an extended-source model — it's a data-preparation layer, not a modeling choice.

## Data access layer

- Two discovery backends (`query.py`): default **`astroquery`** (IRSA SIA2 via `Irsa.query_sia`) and an alternate **`pyvo`/TAP ADQL** backend against `spherex.plane`/`spherex.artifact`. Critically, it knows that **QR3 is not yet in IRSA's SIA2/CAOM service** (`SIA2_MISSING_RELEASES = ("qr3",)`, dated comment "2026-09-18") and automatically routes QR3/QR3_deep queries through TAP even when the caller asked for `astroquery` — exactly the release-transition-aware logic this project needs, already solved.
- Default collection list covers both current releases oldest-first: `("spherex_qr2", "spherex_qr2_deep", "spherex_qr3", "spherex_qr3_deep")`, unlike `spherex-cutoutdb` which is QR2-only.
- Cutout fetch backends (`cutout.py`): `"irsa"` (server-side cutout service, `?center=&size=`) or `"fsspec"` (HTTP byte-range or direct `nasa-irsa-spherex` **S3** reads via `s3fs`). A custom streaming reader (`_PsfHeaderScanner`) can terminate a download right after the PSF header when a shared/cal PSF product is used instead, saving ~97% of transferred bytes per cutout.
- Calibration discovery (`cal_index.py`) resolves per-detector, per-release cal tokens (spectral WCS, SAPM, average PSF, EPSF, `l3_flux_corrections`) via SIA2 or IBE listing, with token parsing and pinning (`sapm_cal_token`, `psf_cal_token`).
- Caching: `~/.cache/spherex-retrieval` (overridable via `SPHEREX_RETRIEVAL_CACHE`/`cache_dir=`).
- Parallelism: `ThreadPoolExecutor(max_workers=8)` default. Rate-limit awareness is explicit and empirical: "The IRSA cutout service answers HTTP 503 under four concurrent requests; two are fine" — a far more realistic, apparently-tested posture than `spherex-cutoutdb`'s defaults.
- Shared-PSF registry (`psf_shared.py`): downloads the per-detector PSF/EPSF product once and periodically re-verifies it against a full cutout download (`psf_verify_every`, default ~200th cutout), warning and falling back to full downloads on mismatch. R7/EPSF cutouts are additionally cross-checked on every download via the `EPSF` header's own provenance string.
- No local database — state is a per-run `summary.ecsv` with one row per overlapping pointing; status (`ok`, `out_of_bounds`, `download_failed`, `qa_excluded`, `wavelength_missing`) is always recorded, so failures are never silently dropped.

## Data model handling

- Reads **`IMAGE`, `FLAGS`, `VARIANCE`, `ZODI`, `PSF`** (or `EPSF`) HDUs per cutout, and separately fetches/crops the **`CWAVE`/`CBAND`** spectral-WCS product and (optionally) **SAPM**. `FLAGS` is passed through as a raw bitmask with no bit-name decoding — deliberately left to the downstream photometry layer, unlike `spherex-cutoutdb` which decodes flags itself.
- **PSF vs EPSF handled correctly and explicitly** (`psf_shared.py`, `psf.py`): `PSFKIND` (`'OPTICAL'` vs `'EPSF'`) and `OVERSAMP` (10 vs 5) are read from the product and threaded through the pipeline; `zone_table_from_epsf()` builds the zone lookup from the actual EPSF table columns (`BINX`/`BINY`/`XCENTER`/`YCENTER`/`NEFF_MEAN`) rather than assuming a fixed lattice, correctly handling the R7 `EPSF` schema. The README documents the physical difference (effective PSF must be point-sampled, never re-integrated, or width is off by ~30% in N_eff) — a level of correctness the other reviewed repo does not reach.
- The **QR2 PSF header erratum** (`VERSION <= 6.5.5` without `+psffix1`, wrong `XCTR_i`/`YCTR_i`) is detected and fixed in-place (`psf.fix_psf_header_if_needed`).
- **Wavelength**: uses `CWAVE`/`CBAND` (never `WCS-WAVE`), citing the Explanatory Supplement's guidance that `WCS-WAVE` is visualization-only. `calibration_release` (default `"qr3"`) lets the caller choose QR2-era vs. R7 on-sky-recalibrated spectral WCS/SAPM for every image, with quantified band-by-band differences documented (D1–D3 identical, band 5 shifted +0.0064 µm).
- **ZODI**: retrieved as its own HDU, explicitly left untouched by the gain correction and never subtracted or used as a background prior — consistent with the stated project background facts.
- **VARIANCE**: cropped alongside `IMAGE`; when the QR2→R7 `l3_flux_corrections` gain correction is applied, `VARIANCE` is scaled by the factor **squared** — correct multiplicative-calibration error propagation.
- **Solid Angle map**: optional `SAPM` HDU (arcsec²), with a documented MJy/sr→µJy conversion recipe.
- **Cutout-to-parent pixel mapping**: a standout strength. `psf.cutout_to_orig()` implements and regression-tests (`tests/test_pixel_origin.py`) the correct sign convention for the cutout's alternate `'A'` WCS (0-based detector origin of cutout pixel (0,0) is `-(CRPIX*A - 1)`, not the naive `CRPIX*A - 1`). The test explains a real, previously-shipped bug this fixed — a within-detector wavelength reversal from negative-index wraparound — exactly the kind of subtle bug our project would otherwise rediscover independently.

## Photometry / extraction method

None — by design. `spherex-retrieval` stops at data preparation: no flux fitting, no background model beyond providing `ZODI` unmodified, no source detection/deblending. The README's "Forced-photometry recipe" shows the four hand-off steps a caller performs: (1) map cutout pixels to detector pixels via `cutout_to_orig`, (2) pick the PSF/EPSF zone via `select_zone_for_source`, (3) resample the oversampled PSF to native pixels at the source's sub-pixel phase via `resample_psf_to_native` (regression-tested for centering), (4) get wavelength/bandwidth at the exact source position via `wavelength_at` (bilinear interpolation). No combination of exposures and no spectrum output format beyond the per-cutout MEF bundle plus manifest — combining multiple epochs into a spectrum is left entirely to the user.

## Extended-source support

N/A by design — a retrieval/PSF-preparation layer, not a fitter, so no Sersic/elliptical-aperture code, but also no architectural assumption preventing extended-source modeling downstream (unlike `spherex-cutoutdb`, which actively rejects targets it judges extended). The PSF-zone and wavelength-at-position utilities (`select_zone_for_source`, `wavelength_at`) work at arbitrary (x, y), so they are directly usable for building a PSF library across a resolved galaxy's footprint — this tool would sit underneath our own extended-source model rather than obstruct it.

## Code quality

- Small, clean, single-responsibility modules totaling ~3,230 lines — an order of magnitude smaller and more auditable than `spherex-cutoutdb`.
- No hard-coded local filesystem paths; cache directory is configurable, defaulting to a standard user-cache location.
- **Robust to the QR2→QR3/EPSF transition by construction** — the central design axis of the package (`psf_kind_of_release`, `PSFKIND` propagated everywhere, `calibration_release` decoupled from `data_release`), kept current: QR3 discovery via TAP fallback was added within the last week of this review (commits ~2026-09-18/19).
- Does not itself decode the `FLAGS` bitmask or `MSKN`/`MSKM` header keywords — an intentional scope boundary (left to the photometry layer), but flag-name mapping still needs to come from elsewhere.
- Test suite is small (6 files) but high-signal: each targets a specific, previously-real bug with a docstring explaining the physics/geometry.
- `CHANGELOG.md` is unusually rigorous, documenting exact calibration tokens, quantitative validation numbers (e.g. chi²/dof 1.6 vs 2.9 for R7 vs QR2 PSF fits on A2537), and stop-gap caveats (gain correction provisional pending DR1 reprocessing).

## Reusable pieces for our project

- `src/spherex_retrieval/query.py` — `find_overlapping()`, `query_sia2()`, `query_tap()`: directly reusable QR2+QR3 discovery layer with correct SIA2/TAP release-aware fallback; MIT-licensed.
- `src/spherex_retrieval/psf.py` — `cutout_to_orig()` (pixel-origin sign convention), `select_zone_for_source()`, `resample_psf_to_native()`, `fix_psf_header_if_needed()` (QR2 header erratum): directly reusable for our own PSF forward-modeling, validated by regression tests we can re-run against our own cutouts.
- `src/spherex_retrieval/psf_shared.py` — `SharedPsfRegistry`/`get_registry`: shared-per-detector-PSF with periodic full-verification is a good template for efficient, IRSA-friendly bulk PSF retrieval, and handles the QR2-cube-vs-QR3-EPSF selection we need (`psf_source="epsf-cal"` logic in `core.py` ~lines 120–145).
- `src/spherex_retrieval/wavelength.py` — `wavelength_at()`, `crop_wavelength_maps()`: correct `CWAVE`/`CBAND` sampling at an exact source position (not just cutout center), useful for per-source wavelength grids across resolved sources.
- `src/spherex_retrieval/flux_correction.py` — QR2→R7 `l3_flux_corrections` gain application (`apply_flux_correction`, correct `VARIANCE`×factor² propagation, dead/hot-pixel row-median replacement) is directly relevant if we combine QR2 and QR3 epochs.
- `src/spherex_retrieval/bundle.py` — per-cutout MEF bundle writer/`summary.ecsv` manifest pattern (status enum that never silently drops a failed pointing) is a clean convention for our own multi-exposure retrieval bookkeeping, especially for stacking.

## Risks and limitations

- Not on PyPI; must be installed from source, which is fine for vendoring/forking but means no independent release-integrity guarantees beyond git.
- Small, single-author project — no external contributors or code review visible; correctness claims (e.g., the A2537 PSF chi²/dof comparison) are stated in the CHANGELOG/README but the underlying validation notebooks/data are not in the repository.
- Purely a retrieval/prep layer — our photometry, background modeling, deblending, and extended-source fitting still need to be written; this tool only delivers clean, correctly-aligned cutouts with the right PSF/EPSF and wavelength calibration attached.
- FLAGS bitmask is not interpreted here — we still need our own flag-name table, ideally sourced from QR3's `MSKN`/`MSKM` header keywords directly rather than a hard-coded table, to avoid the QR2-lock-in problem seen in `spherex-cutoutdb`.
- The `epsf-cal` default silently substitutes the R7 EPSF library onto QR2 images with no check against the L2 file possible for that attachment — defensible per the author's stated validation, but changes what PSF product QR2-era cutouts nominally carry; overridable via `psf_source="cal"`.
- Zero GitHub issues and only 3 stars suggest limited external usage/battle-testing so far, despite strong code-quality signals.

## Verdict

**Borrow pieces, leaning toward use-directly for the retrieval/PSF-prep layer.** This is a well-designed, actively maintained, MIT-licensed, QR2+QR3-aware retrieval and PSF-preparation library written by someone who has clearly worked through the same subtle SPHEREx L2 pixel-mapping and PSF-kind issues our project needs to get right (regression-tested pixel-origin sign convention, EPSF vs optical-PSF handling, QR2↔R7 gain reconciliation). It stops short of photometry by design, so it does not replace our own forward-modeling/background/stacking work, but as the data-access and PSF-preparation foundation underneath that work it is substantially more current and trustworthy than `spherex-cutoutdb`, and worth adopting largely as-is (vendoring or a thin fork) rather than reimplementing from scratch.
