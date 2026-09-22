# freddavies/spherextract

## Metadata

- **Author**: Frederick "Fred" Davies (GitHub `freddavies`). No institutional affiliation stated on the GitHub profile or in the repo.
- **License**: none (`license: null` in the API, no `LICENSE` file) — legally ambiguous for reuse; clarify with the author before borrowing substantial code.
- **Language**: Python (three top-level scripts, ~3,300 lines), plus ~65 MB of bundled binary calibration data (see below).
- **Stars/forks**: 8 stars, 3 forks, 0 open issues (as of 2026-09-23).
- **Commit history (`main`, the branch reviewed)**: 55 commits, first 2026-05-04 ("Initial commit"), most recent on `main` 2026-07-08 ("shhh"). `pushed_at` (2026-09-15) is newer than `main`'s last commit because three other branches exist — `develop`, `gotta_go_fast`, `inspector` — not reviewed here (only `main` cloned per scope). One contains `spherextract_fast.py`, using a database/"tall table" pixel-query backend (`talltable.PixelQuery`) instead of per-object cutout downloads — worth a follow-up look for our stacking/background needs.
- **Open issues**: 0. Single-author development, 3 self-merged PRs.
- **PyPI**: not published; run as standalone scripts from a local clone.
- **Tests**: none found. **CI**: none.
- **Docs**: one well-written `README.md` with worked CLI examples and a "Known issues" section.
- **Associated paper**: none directly, but the README credits two direct ancestors: the cutout-download machinery from Eduardo Bañados' `spherex-tools` (reviewed alongside this note) and the PSF-downsampling code from Jonathan Gagné's `SPIFF` (arXiv:2604.22012). The README states the code was AI-assisted.

## Purpose and scope

`spherextract` downloads SPHEREx Level-2 cutouts around one, two, or three nearby target coordinates from IRSA and extracts spectrophotometry via a 2D analogy to optimal spectral extraction (Horne 1986): a fixed, PSF-shaped matched filter fit to each cutout with iterative sigma-clipped outlier rejection, rather than aperture summation. Three scripts cover increasing source multiplicity: `spherextract.py` (single point source), `spherextract_two.py`/`spherextract_three.py` (simultaneous linear-least-squares deblending of 2-3 nearby point sources sharing the same PSF model). The README states the tool assumes **point-source morphology** and that "extended sources may be supported in the future" — not yet implemented. Worked examples are a high-z quasar and a lensed-quasar-plus-star pair.

## Data access layer

- Discovery uses the same `astroquery.ipac.irsa.Irsa.query_sia(pos=..., instrument="SPHEREx")` call as `spherex-tools` (`spherextract.py:_query_spherex`, lines ~132-144), with no release/collection pinning — same caveat about silently mixing QR2/QR3/DR1 products as IRSA's index evolves.
- Cutout URLs are built the same way as in `spherex-tools`: strip a base-URL or `ibe/data/` prefix from `access_url` and reassemble as `.../ibe/cutout?ra=...&dec=...&size=...&path=...` (`_build_cutout_url`, lines 148-163), but degrades gracefully rather than hitting an unhandled "TBD" branch.
- Downloads are parallelized with a `ThreadPoolExecutor` (`download_cutouts`, lines 210-303, default 8 workers), each with a configurable timeout, retry count, and retry delay (`_download_file`, lines 168-201) — more production-hardened than `spherex-tools`' single-threaded, single-attempt downloader.
- Caching is skip-if-exists on disk (`overwrite` flag); no content/version-aware caching.
- The repo bundles ~65 MB of static calibration data not referenced by any code on `main`: `spherex_calibs/psf/average_psf_D{1-6}_spx_cal-psf-v{4,5}-2026-{161,082}.fits` (six per-detector average PSF files, two calibration versions) and `spherex_calibs/image.parquet` (30 MB). These likely feed the `talltable`/`spherextract_fast.py` pixel-query workflow visible only on other branches — worth asking the author about directly, since neither file is wired into the `main` scripts reviewed here.

## Data model handling

- Extensions are read by **fixed positional index** (not `EXTNAME`), assuming the QR2/pipeline-6.x layout: `hdul[1]`=IMAGE+header, `hdul[2]`=FLAGS, `hdul[3]`=VARIANCE, `hdul[5]`=PSF cube (with header `hdr_psf`), `hdul[6]`=WCS-WAVE table (`optimal_extract`, `spherextract.py:594-599, 320-326`). Extension 4 (presumably ZODI) is never opened — **no ZODI handling anywhere**, as in `spherex-tools`.
- **PSF**: reads a genuine PSF *cube* (`hdul[5].data`, shape `(n_zones, ny_hr, nx_hr)`), the QR2/pipeline-6.x product, not the QR3/pipeline-7.x `EPSF` binary table (`BINX BINY XCENTER YCENTER NEFF_MEAN CWAVE CBAND EPSF`) — "EPSF"/"CWAVE"/"CBAND"/"NEFF"/"BINX"/"BINY" appear nowhere in the three scripts (checked by grep); cannot read a QR3-format PSF product without new code.
- **Flags**: a real bitmask against explicit `MP_*`-named bit positions hard-coded in a dict (`_MP = {"TRANSIENT": 0, "OVERFLOW": 1, ..., "SOURCE": 21}`, lines ~471-478), combined into `_BAD_BITS` (fit exclusion: `SUR_ERROR`, `NONFUNC`, `MISSING_DATA`, `HOT`, `COLD`, `NONLINEAR`, `PERSIST`) and a stricter `_BAD_BITS_BCG` (adds `OVERFLOW`, `SOURCE`, `OUTLIER`, `TRANSIENT`) for background. QR2 `MP_*`-specific, no `MSKN`/`MSKM` awareness; a 2026-06-30 commit ("new mask bits") shows the dict already needed one manual update as flags evolved during QR2 — actively tracked but still QR2-only.
- **Wavelength**: reads the `WCS-WAVE` table (extension 6, `_load_wcswave`, lines 316-354), bilinearly interpolating center wavelength and channel width at the target's *full-detector* pixel position (not CWAVE/CBAND calibration files).
- **Cutout-to-parent pixel mapping**: handled carefully and documented in-code (lines 632-660) — the cutout-local position (from the cutout's own WCS) is used for PSF placement, and the full-detector position (recovered via `CRPIX1A`/`CRPIX2A` offsets) is used for PSF-zone selection and WCS-WAVE evaluation. Materially more careful than the "assume center pixel 3" hack in `spherex-tools`.
- **Solid angle**: read from header keyword `HIERARCH OMEGA_MEDIAN` (arcsec², converted to sr), not a dedicated Solid Angle map file.

## Photometry / extraction method

- **PSF-fit matched filter, not aperture photometry.** The amplitude is estimated as a Horne-1986-style inverse-variance-weighted matched filter, f_hat = sum(P*ivar*D)/sum(P^2*ivar), var(f_hat) = 1/sum(P^2*ivar), iterated with outlier rejection (|D - f_hat*P| > kappa*sigma, default kappa=4, up to 10 iterations) that progressively masks pixels (`optimal_extract`, lines ~800-860).
- **PSF preparation** (`_make_psf_detgrid`, lines 415-460): crop the oversampled PSF cube plane to a size divisible by the oversampling factor, embed in a zero-padded high-resolution canvas sized to the cutout, apply a cubic-spline sub-pixel `scipy.ndimage.shift` to center it at the target's exact cutout position, then flux-conserving block-sum to the detector grid. The correct PSF *zone* is chosen per-exposure by nearest-neighbor match on `XCTR_n`/`YCTR_n` header cards against the target's full-detector position (lines 726-745), respecting SPHEREx's field-dependent PSF.
- **Background**: local median of non-flag-masked, finite pixels in a 21x21-pixel cutout, with a fallback to an unmasked median if too few clean pixels remain (lines 700-712). A code comment (and a since-superseded commit, "made linear bkg optional") notes the median background can be inaccurate near sky lines (e.g., He I 1.083 um) - flagged by the author as a known limitation, not yet fixed on `main`.
- **Deblending**: `spherextract_two.py`/`spherextract_three.py` extend the same matched-filter idea to a simultaneous linear least-squares fit for 2-3 point sources sharing one cutout, solving a small normal-equations system from pairwise PSF-PSF/PSF-data inner products (e.g. `A[0,0] = sum(P1^2*w)`, `A[0,1] = sum(P1*P2*w)`, `spherextract_two.py:437-439`). The default kappa=4 is noted in the README as "too aggressive" for close, comparably-bright blends (`--kappa 25` in the worked example).
- **Error propagation**: fit-covariance-based flux uncertainty (1/sum(P^2*ivar)), converted to integrated flux via the PSF sum and pixel solid angle; chi2/dof reported per exposure.
- **Combination of exposures**: **none** - each exposure yields one independent (wavelength, flux, error) point; all such points across repeat visits are written together as the "spectrum," sorted but not binned or inverse-variance-averaged, same as `spherex-tools` and unlike `SPIFF`'s 102-channel binning.
- **Output format**: per-target CSV (`{name}_spherex_photometry.csv`, one row per exposure - position, detector/OBSID/exposure metadata, quality-flag counts, background, optimal flux in MJy/sr and uJy, S/N, chi2/dof) and a three-column text spectrum (`{name}_spherex_spectrum.txt`), plus optional four-panel diagnostic figures per exposure.

## Extended-source support

None on `main`. The README's "Known issues" section states this explicitly: "The single-object tool assumes a point-source morphology for the target. Extended sources may be supported in the future." The model is always `flux × PSF` (or a linear sum of such terms for 2-3 blended point sources); no Sersic profile, elliptical aperture, or aperture-correction table anywhere (grep for "sersic"/"extended"/"elliptical" returns nothing).

## Code quality

- **Structure**: three largely self-contained scripts (1,277 / 963 / 1,054 lines) that intentionally duplicate the download and PSF-preparation helpers rather than sharing a common library module — pragmatic for a fast-moving personal project but a maintenance cost if a bug fix in one variant is not propagated to the others.
- **Dependencies**: mainstream and modest (`astropy`, `astroquery`, `numpy`, `scipy`, `matplotlib`); no exotic dependencies on `main` (no `ultranest`, no S3 libraries).
- **Hard-coded paths**: none found; I/O directories are CLI-configurable.
- **Robustness to QR3 EPSF and flag-header changes**: the single biggest weakness. Extension access is entirely positional (breaks silently if IRSA reorders/adds MEF extensions for QR3/DR1), and the PSF code hard-assumes a cube (`hdul[5]` with `OVERSAMP`/`CDELT1` header and `XCTR_n`/`YCTR_n` zone cards) with no path for a QR3 `EPSF` binary table. The flag-bit dictionary is QR2 `MP_*`-flavored and has already needed one manual update as flag definitions evolved ("new mask bits," 2026-06-30) — actively tracked by hand, but still QR2-only, so a QR3 migration will again require manual code changes.
- **Tests**: none. **CI**: none. Given single-author, no-review development and still-evolving flag/PSF handling, correctness for edge cases should be independently verified.

## Reusable pieces for our project

- `spherextract.py:_make_psf_detgrid` (lines ~415-460): clean, self-contained, flux-conserving PSF crop -> high-res canvas -> sub-pixel shift -> block-sum implementation; a good starting point for our own QR2-cube PSF forward-modeling step (needs a parallel path for QR3 `EPSF` stamps).
- `spherextract.py:optimal_extract`, "5. Select PSF zone" (lines ~726-745): simple, correct nearest-neighbor PSF-zone selection from `XCTR_n`/`YCTR_n` header cards, smaller and easier to read than the equivalent, more defensive logic in `SPIFF`'s `spherex_psf_selection.py`.
- The cutout-local-vs-full-detector pixel-coordinate bookkeeping (lines 632-660, well-commented) is a concise explanation of a subtlety (`CRPIX1A`/`CRPIX2A` offsets) we will also need to get right.
- `_MP` flag-bit dictionary and the `_BAD_BITS`/`_BAD_BITS_BCG` split (lines 471-503): a concrete example of which QR2 `MP_*` bits matter for photometry vs. background, worth cross-checking against official QR2 flag docs (and `MSKN`/`MSKM` semantics once reviewed for QR3).
- `spherextract_two.py`'s simultaneous linear-least-squares deblending normal equations (lines ~430-460): a clean template for semi-resolved systems with two-to-three point-like/compact components (e.g. a compact nucleus plus companion), though it needs generalizing beyond point sources for genuinely extended light.
- The `ExtractionResult` dataclass (lines ~78-127): a well-thought-out per-exposure metadata schema (quality-flag counts, background, χ²/dof, flux-density and integrated-flux units) worth using as a checklist for our own output schema.

## Risks and limitations

- **No license file**: legal status of reuse is unclear; clarify with the author before copying non-trivial code into a project intended for publication.
- **QR3/EPSF incompatibility by construction**: positional extension access, PSF-cube-only model, and a manually-maintained QR2 `MP_*` flag dictionary mean this tool cannot process QR3 (since 2026-07-20) or DR1 without a real migration (EPSF-based PSF prep, pipeline-version dispatch, `MSKN`/`MSKM` flag handling).
- **Point-source-only**: honestly documented by the author; none of the extraction code is usable as-is for resolved galaxies, only partially usable (2-/3-object deblending) for semi-resolved, compact systems.
- **No ZODI subtraction, no exposure combination/binning**: local median background only (same caveat as `spherex-tools`); raw per-exposure points only, with stacking/binning left to be built on top.
- **Background near sky lines flagged as unreliable by the author** (median background inaccurate near He I 1.083 µm) — a concrete risk for wavelength-dependent background work.
- **Single author, active/unstable development**: 55 commits in ~2 months on `main`, plus unreviewed work on `develop`/`gotta_go_fast`/`inspector`; messages ("okay THIS time it will work") suggest the logic hasn't fully stabilized, and there are no tests to guard regressions.
- **Bundled binary calibration data** (~65 MB of average-PSF FITS files and a parquet table) unused on `main` signals a more advanced, database-backed path (`talltable`/`spherextract_fast.py`) on other branches — possibly more relevant to our stacking/background goals, worth a follow-up.

## Verdict

**Borrow pieces.** `spherextract` is meaningfully more sophisticated than its `spherex-tools` ancestor — genuine PSF-cube forward modeling with sub-pixel shifting and flux-conserving downsampling, real flag-bitmask handling, careful cutout-to-full-detector pixel bookkeeping, iterative sigma-clipped matched-filter extraction, and a working multi-point-source deblending scheme — a much closer methodological match to this project's goals than `spherex-tools`. However, it is explicitly point-source-only, hard-wired to the QR2 PSF-cube and `MP_*` flag data model with no QR3/EPSF support, has no license file, no tests, and is under active single-author development with visible instability. It should not be depended on as an installed library, but the PSF-preparation function, PSF-zone-selection logic, coordinate bookkeeping, QR2 flag-bit reference, and multi-source deblending scheme are all worth adapting into our own pipeline — and the unreviewed branches plus unused calibration data warrant a follow-up look before finalizing this assessment.
