# banados/spherex-tools

## Metadata

- **Author**: Eduardo Bañados (per the docstring of `get_cutouts_spherex.py`, "Eduardo Banados"; GitHub user `banados`). No institutional affiliation is stated anywhere in the repo. Secondary contributor: Frederick Davies (2 commits, 2025-11-07), the author of `freddavies/spherextract` reviewed alongside this repo — the two projects are directly linked (see below).
- **License**: MIT (`LICENSE` file present, copyright "SPHEREx Data Downloader", 2025).
- **Language**: GitHub reports "Jupyter Notebook" as the dominant language (one example notebook is large), but the functional code is three plain Python scripts/modules (~2,630 lines total).
- **Stars/forks**: 9 stars, 5 forks, 0 open issues (as of 2026-09-23).
- **Commit history**: 21 commits total. First commit 2025-07-29 ("Initial commit: SPHEREX data downloader"), most recent commit on `main` 2025-11-17 ("added Paschen lines"). Development is bursty: most commits cluster on 2025-07-29 (initial build-out) and 2025-11-07 (a same-day round of fixes co-authored with Frederick Davies: "fixed wavelength hdu", "fixed variance", "fixed crazy cutout wcs problems", "added bright object mode").
- **Open issues**: 0.
- **PyPI**: not published; usage is by cloning the repo and running the scripts directly (`pip install -r requirements.txt`).
- **Tests**: none (`find . -iname "*test*"` returns nothing; no CI workflow file).
- **Docs**: a single, unusually thorough `README.md` (usage examples, CLI option tables, troubleshooting section, output-format examples); docstrings in the code are present but terse.
- **Associated paper**: none. README credits "the SPHEREx mission papers," IRSA/IPAC, astroquery, and explicitly the original `spherex_quicklook` repo by Fred Davies (predecessor of `spherextract`) for the photometry-extraction approach.

## Purpose and scope

`spherex-tools` is a small, two-stage command-line toolkit: `get_cutouts_spherex.py` queries IRSA for SPHEREx Level-2 exposures near a list of target coordinates and downloads either full ~80 MB files or small (0.01°≈36″≈6-pixel) cutouts via the IRSA cutout service; `extract_spherex_photometry.py` (using helper functions in `spherex_utils.py`) then turns a directory of such 6×6-pixel cutouts into a crude "spectrum" by fixed-aperture photometry on each individual exposure, with plotting and text/CSV export. The example target lists (`sources_list/fu2025_z4qsos.txt`, `qsos_with_most_spherex.txt`) and the example notebook (`tdwarf_quasar.ipynb`) indicate the intended targets are **unresolved point sources** — high-z quasars and T dwarfs — not galaxies. There is no notion of resolved or extended morphology anywhere in the code.

## Data access layer

- Discovery uses `astroquery.ipac.irsa.Irsa.query_sia(pos=(ra, dec, radius), instrument="SPHEREx")` (`get_cutouts_spherex.py:220`, duplicated in `check_spherex_coverage.py:305`) — IRSA's SIA service, generic, with no release/collection filtering. It picks up whatever SPHEREx products IRSA currently indexes (QR2/QR3/DR1 automatically as the archive evolves), but has no way to *select* a specific release and no version/collection string hard-coded anywhere.
- Cutout URLs are built by hand-editing the returned `access_url` string: `build_download_url()` (`get_cutouts_spherex.py:216-252`) hard-codes `base_url = "https://irsa.ipac.caltech.edu/"` and the endpoint pattern `ibe/cutout?ra={ra}&dec={dec}&size={size}&path={data_path}`, stripping a leading `ibe/data/` (or the full base URL) from `access_url`. Fragile string manipulation with an explicit "TBD" fallback branch for unmatched URLs — a likely breakage point if IRSA changes its URL scheme for QR3/DR1.
- Full-file downloads are also supported (`--cutout` omitted), fetching the entire ~80 MB Level-2 MEF via plain `urlopen`.
- "Caching" is skip-if-exists on local disk (`--overwrite` forces re-download); no content hashing, no ETag/version check — every rerun re-hits IRSA's SIA service.
- `check_spherex_coverage.py` is a separate, useful utility: it batch-queries SIA for many targets (CSV/whitespace/FITS-table input via `read_input_file()`, line 78), appends a `spherex_data` column (image count, or `-1` on error), and supports `--retry-errors`/`--update` — a lightweight target-list vetting workflow.

## Data model handling

- The two extraction implementations in the repo are **inconsistent** with each other, a real maintenance smell:
  - `spherex_utils.py:extract_spherex_from_files()` (older/library version) reads extensions **by positional index**: `hdul[1].data` for the image, `hdul[2].data` for a 2D wavelength lookup table (`X`, `Y`, `VALUES[...,0]`=wavelength, `VALUES[...,1]`=bandwidth). Never touches VARIANCE/FLAGS/ZODI; estimates variance ad hoc from sky-pixel scatter instead.
  - `extract_spherex_photometry.py:extract_spherex_from_files()` (the version actually invoked by the CLI, same function name) instead reads **by EXTNAME** — `hdul['IMAGE']`, `hdul['WCS-WAVE']`, `hdul['VARIANCE']` — the more robust approach, using the real `VARIANCE` extension summed over the aperture mask. Still never reads `FLAGS` or `ZODI`.
- Neither implementation reads a `PSF`/`EPSF` extension — no PSF-based modeling anywhere in this repo.
- `WCS-WAVE` handling assumes a fixed **6×6-pixel cutout** (`len(img.flatten()) == 36` gate) and hard-codes the "center" pixel index as `3` for the wavelength interpolator (`interp_wave((3 - hdr['CRPIX2W'], 3 - hdr['CRPIX1W']))`) rather than deriving the target's actual sub-pixel position from its own WCS — silently mis-locates wavelength/flux for any other cutout size or off-center target.
- No ZODI handling, no explicit Solid Angle map extension use (there is no per-pixel solid-angle read at all — flux-unit conversion instead uses a fixed default `omega_pix=37.932` arcsec² constant in `get_flam()`), and no cutout-to-parent pixel bookkeeping beyond the implicit IRSA cutout WCS.

## Photometry / extraction method

- **Aperture, not PSF-fit.** The "aperture" is a hard-coded central 2×2-pixel box (`mask[2:4, 2:4] = True`) inside the 6×6 cutout — explicitly flagged in a code comment as "definitely suboptimal (PSF FWHM can be <1 pixel) but should capture most of the light even at the long wavelength end." There is a `bright` mode that instead sums the entire 6×6 cutout with no background subtraction, for saturated/very bright sources.
- **Background**: the median of all non-aperture, non-NaN pixels in the same 6×6 cutout (`np.median(img[sky])`), subtracted as a flat scalar times the aperture pixel count. An optional `mask2` argument lets the user manually exclude a second contaminating source from the sky region, described in the docstring as "Experimental."
- **No PSF preparation** of any kind (no shift/downsample/normalize step exists).
- **Deblending**: none beyond the manual `mask2` sky-exclusion mask; no simultaneous multi-source fit.
- **Error propagation**: in the CLI-used version, `VARIANCE` extension values inside the aperture mask are summed; in the library version, variance is estimated from sky-pixel scatter — the two are inconsistent and only the former is exposed through the command-line tool.
- **Combination of exposures**: none by default — every individual exposure/cutout produces one (wavelength, flux, variance) triplet, and all such points across the mission's repeat coverage of the target are kept as a raw, highly oversampled "spectrum." An optional `rebin_spherex()` (`spherex_utils.py:220-249`) groups points within `tol × dwave` of each other and combines them with an unweighted mean and an error-of-the-mean computed as `sqrt(sum(std**2))/N` (equal-weight, not inverse-variance-weighted, combination).
- **Output**: a plain-text spectrum file (`wavelength[μm] flux[erg/s/cm²/Å] error`), plus `f_λ`/`f_ν` diagnostic plots with rest-frame emission-line markers for a given redshift, and (in `extract_spherex_photometry.py`) optional overlay of a scaled Vanden Berk (2001) QSO composite template.
- A hard flux cut (`cr_thresh`, default 10 MJy/sr) is the *only* outlier/cosmic-ray rejection mechanism; there is no flag-based masking at all.

## Extended-source support

None. The extraction aperture is a fixed 2×2-pixel box with no configurable shape, no elliptical or Kron-style aperture, no Sersic or other galaxy morphology model, and no aperture correction. The README's own "Troubleshooting" section frames non-6×6 cutouts and off-center sources as error conditions to be worked around, not a resolved-source use case to be supported. This tool is unambiguously point-source-only.

## Code quality

- **Structure**: three flat scripts/modules with no packaging (no `setup.py`/`pyproject.toml`), meant to be run in place after `pip install -r requirements.txt`. `extract_spherex_photometry.py` (1,072 lines) is a single monolithic file mixing extraction, template loading, unit conversion, rebinning, CLI parsing, and plotting.
- **Duplicated logic**: as noted above, `spherex_utils.py` and `extract_spherex_photometry.py` each define their own, subtly different `extract_spherex_from_files()`; a bug fix or improvement in one (e.g., the November 2025 "fixed variance"/"fixed wavelength hdu" commits) was applied only to the CLI-facing copy, leaving the library copy in `spherex_utils.py` with the older, less correct behavior — a trap for anyone importing `spherex_utils` directly as advertised in the README.
- **Hard-coded values**: `base_url` string for IRSA, the `36`-pixel/6×6-cutout size gate, the "center pixel = 3" assumption, and the default `omega_pix=37.932` arcsec² solid angle are all hard-coded rather than derived from FITS headers.
- **Robustness to QR3 EPSF / flag-header changes**: not applicable in the sense that neither PSF nor FLAGS extensions are ever read, so there is nothing to break when QR3 switches from PSF cubes to `EPSF` tables or from `MP_*` to `MSKN`/`MSKM` flag keywords — but this "robustness" is really an absence of quality control (no cosmic-ray/bad-pixel flag rejection at all, relying solely on a blunt flux threshold).
- **Tests**: none. **CI**: none.

## Reusable pieces for our project

- `get_cutouts_spherex.py:read_input_file()` (lines ~52-180) and the near-identical, more flexible `check_spherex_coverage.py:read_input_file()` (lines 78-~230, supports CSV/whitespace/FITS-table input and flexible name/ra/dec column aliasing): decent, defensive target-list ingestion utilities, useful as a starting point for our own batch target-list handling even if we rewrite the extraction logic entirely.
- `check_spherex_coverage.py` as a whole: a lightweight, resumable "does SPHEREx cover this target, and how many exposures" pre-flight check (`--retry-errors`, `--update`) — worth adapting as a coverage-vetting step before committing to full cutout/PSF downloads for a post-starburst-galaxy sample.
- `spherex_utils.py:get_flam()` / `get_fnu_from_flam()` (lines ~185-215): compact MJy/sr → f_λ/f_ν conversion helpers; useful as a cross-check reference for our own unit-conversion code, though the hard-coded default pixel solid angle (`omega_pix=37.932` arcsec²) should not be trusted blindly and ought to be replaced with a per-pixel value read from the data.
- The emission-line list and rest-wavelength/redshift plotting logic in `plot_spherex_flam`/`plot_spherex_fnu` (`spherex_utils.py:255-330`) is generic and could save time for quick-look diagnostic plots.
- Nothing in the photometry/PSF-handling code itself (aperture, background, variance) is worth reusing directly — it is simpler and less correct than what we need, and than what `spherextract` (reviewed alongside this repo) already provides.

## Risks and limitations

- **No PSF, no flags, no ZODI**: fundamentally incompatible with the project's goal of PSF forward modeling and careful background/flag handling; adopting this tool's extraction logic would be a regression relative to even a basic aperture-photometry-with-flags approach.
- **Fixed 6×6-cutout / center-pixel-3 assumption**: silently wrong wavelength and flux for any other cutout geometry or off-center target placement; a latent bug rather than a documented limitation.
- **Inconsistent duplicate implementations** (`spherex_utils.py` vs. `extract_spherex_photometry.py`) mean the "library" API documented in the README does not match the better-tested CLI path — a correctness trap if reused programmatically.
- **Fragile, hand-built cutout-service URLs** with an explicit unhandled fallback case; likely to break silently if IRSA changes its URL scheme for QR3/DR1.
- **No release/version pinning** in the SIA query — reruns of the same script at different times could silently mix QR2 and QR3/DR1 products as IRSA's archive evolves, with no code-level awareness of the difference.
- **No tests, no CI, single-purpose scripts with duplicated logic**: low confidence in long-term correctness or maintenance.

## Verdict

**Read for ideas only.** `spherex-tools` is a reasonable quick-look / target-vetting utility (particularly `check_spherex_coverage.py` and the input-file parsing helpers) but its core photometric extraction — a fixed 2×2-pixel aperture in a hard-coded 6×6 cutout, flat median background, no flag masking, no ZODI handling, and no PSF model — is far below the bar needed for reliable point-source, semi-resolved, or resolved post-starburst-galaxy spectra. The two duplicated and inconsistent extraction implementations are themselves a caution against depending on this code as a library. Its main value to us is as a source of small, generic utilities (target-list I/O, coverage checking, unit-conversion cross-checks) and as a cautionary example of the data-model pitfalls (extension access by index vs. name, cutout-geometry assumptions) to avoid in our own pipeline. Its historical role as the ancestor of `freddavies/spherextract` — which is substantially more capable and is reviewed alongside this note — also makes it useful background reading for understanding that tool's lineage.
