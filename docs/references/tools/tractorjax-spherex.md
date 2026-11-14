# hbahk/tractorjax-spherex

## Metadata

- **Author**: Hyeonguk Bahk (`bahkhyeonguk@gmail.com`, GitHub `hbahk`), sole committer across all 52 commits (first `524c4f4`, 2026-07-23; last `2203359`, 2026-09-20). Tags `v0.2.0`/`v0.2.1`/`v0.3.0`/`v0.3.1`; current version `0.3.1`.
- **License**: GPL-3.0-or-later, because it links the GPL `tractor-jax` engine; the optional upstream `tractor` dependency (GPLv2) is an optional CPU-fallback backend only.
- **Stars/forks/issues**: 1 star, 0 forks, 0 open issues (issue creation restricted).
- **PyPI**: not published. `tractorjax-spherex`, `tractor-jax` (the engine), and `spherex-retrieval` (the IRSA downloader) are three separate `hbahk` repos, all installed from source. `requires-python >= 3.11`, "Development Status :: 3 - Alpha".
- **Associated paper**: **arXiv:2606.19875**, Bahk et al. (2026), "The SPHEREx View of Galaxy Clusters: A Simulation-based Validation of the Forced Photometry Pipeline for Extended Sources" (posted 2026-06-18), same lead author. **Key nuance, confirmed by inspection**: that paper's validated pipeline used the classic CPU `The Tractor` (`dstndstn/tractor`), not JAX. `tractorjax-spherex` is a separate, later JAX reimplementation, and — notably — **the arXiv id never appears anywhere in this repo** (`grep -rn "2606.19875\|arXiv" docs/ src/` is empty). The repo instead repeatedly credits a private internal codebase, "the production driver" (`proj-spherex-gpupipe`), as the source of key modules and claims "bit-identical" reproduction of it (`constants.py:3`, `models.py:3`, `psf_cache.py:5`, `config.py:315`). Whether that private driver is the same code validated in the arXiv paper, a JAX port of it, or a distinct later "SPHEREx deblending campaign" pipeline is **not stated anywhere public** — `docs/paper_reproduction.md` targets a "catalog-depth paper" whose Appendix A concerns photo-z calibration, which reads as a different paper from the extended-source validation one. Any claim that this package reproduces arXiv:2606.19875's extended-source results is **unverified from public materials**.

## Purpose and scope

Reference-catalog forced photometry and spectrum assembly from SPHEREx L2 cutouts: positions/shapes come from an external catalog (typically Legacy Survey DR10 via `fetch_ls_dr10`) and are held fixed; only per-source fluxes are solved, jointly within spatial tiles, on a GPU/JAX engine (`tractor_jax`) with a CPU fallback. Output is one flux per (source, visit); `spectra.py` assembles per-source spectra. Source detection, position/shape fitting, and image-space deconfusion are explicitly out of scope for now (Roadmap: "Deconfusion image models," "Free-parameter (LM) fitting" both deferred).

## Data access layer

- **No IRSA access of its own.** `retrieve()` (`__init__.py:44-53`) is a thin passthrough to `spherex_retrieval.retrieve`, raising an actionable `ImportError` if that package isn't installed. `spherex-retrieval` is not vendored here and could not be inspected; facts about it below are second-hand from this repo's docs.
- Discovery is purely local-filesystem: `discover_cutouts` (`io/cutouts.py:87-96`) globs `cutout_<idx>_<obs>_D<det>.fits`; `filter_ok` (99-108) keeps only `status == "ok"` entries from a sibling `summary.ecsv`. No IRSA URLs, release strings, or version pins appear anywhere in the source.
- `docs/faq.md` states `spherex_retrieval`'s current default (`psf_source="epsf-cal"`) fetches one PSF product per detector and **substitutes the R7 effective PSF even for QR2 images** unless `psf_source="cal"` is set — i.e. retrieval defaults can silently swap PSF kind even for "QR2" data. This repo's PSF-kind auto-detection (below) is what makes that survivable.
- `catalog/fetch_ls.py` queries NOIRLab Data Lab's `ls_dr10.tractor` directly (needs `DATALAB_USER`/`PASSWORD`) — a separate access path from the pixel data.

## Data model handling

- Reads the fixed MEF layout `PRIMARY IMAGE FLAGS VARIANCE ZODI PSF PSF_ZONES [CWAVE][CBAND][SAPM]` via astropy or a ~4x-faster `fitsio` path, asserted identical by `tests/test_io_fast.py`. Optional HDUs degrade gracefully when empty (NaN wavelength/bandwidth, WCS-area fallback) rather than erroring.
- **No `WCS-WAVE` extension is ever read.** Wavelength comes entirely from `CWAVE`/`CBAND`, bilinearly sampled at each source's own sub-pixel position (`sample_map_bilinear_vec`) because CWAVE drifts ~0.2 nm/pixel across a cutout.
- **PSF-kind auto-detection is real and load-bearing.** `psf_kind_from_header()` (`io/cutouts.py:197-205`) reads `PSFKIND` (`EPSF`/`EFFECTIVE`→`"effective"`; `OPTICAL`/`PSF`/missing→`"optical"`; else raises). This branches in three places: `psf_stamp_5x` (`prepare.py:60-76`, downsample QR2 10x cube vs. pass R7 33x33 ePSF through), `pixel_integration_for` (78-81, `"window"` vs `"point"`, wired into the engine's static solver option), and `core_shift_applies` (84-102, QR2 core-registration auto-skipped on EPSF). `tests/test_epsf.py::test_window_on_the_epsf_is_biased` deliberately forces the wrong mode and asserts a measurable bias — real regression coverage, not just plausible code.
- **Flag handling is not release-keyword-aware — a real risk.** `grep -rn "MP_\|MSKN\|MSKM" src/ docs/` returns nothing. `constants.py:20-33` hardcodes bit *positions* in a Python dict; the header's own flag-name keywords (QR2 `MP_*`, QR3 `MSKN`/`MSKM`) are never read. If QR3/DR1 ever reassigns bit positions (not just keyword names), masking would silently break with no error.
- **ZODI** seeds every background model and is never discarded; `fit_background()` (`background.py:118-133`) always returns "zodi plus a refinement."
- **VARIANCE** is scaled by `(Ω_sr·IMG_SCALE)²` (`prepare.py:155-176`), inverted to `invvar`, zeroed on non-finite/`MASKBITS`, used directly as the fit weight — no separate covariance model. `docs/backgrounds_systematics.md` discloses a faint-end weight-noise bias from VARIANCE being affine in the *observed* rate.
- **SAPM** is genuinely used: `cutout_pixel_area_sr()` (`io/cutouts.py:249`) prefers the per-pixel SAPM map and only falls back to a single WCS pixel area when absent.
- **Cutout-to-parent WCS**: `CRPIX1A`/`CRPIX2A` map cutout pixels to detector coordinates for PSF-zone selection (`prepare.py:29-35`). Per-tile WCS objects are deliberately skipped by default (`PER_TILE_WCS = False`, only the CD matrix is shared) and `tests/test_per_tile_wcs.py` pins three explicit invariants proving that shortcut is output-identical — solid, tested engineering.

## Photometry / extraction method

- **Background is global-per-cutout, not a local aperture background** — unlike the IRSA Spectrophotometry Tool's local 15-pixel background. `background.py` fits a whole-cutout 2D model: `Background2D` on the ZODI residual, a CWAVE-binned PCHIP airglow removal + `Background2D` (default), a 3-parameter WLS plane, or none. The tiled solve additionally fits a **free constant per 15-px tile**, jointly with fluxes (`cpu_tile_background`, default on) — a two-level background, meaningfully different from a fixed local annulus.
- **Rendering**: every source is rendered on a 5x-oversampled grid then binned to native pixels; Sersic profiles use a Mixture-of-Gaussians approximation (`tractor_jax.sersic.SersicMixture`, `models.py:92-100`) — same conceptual family as classic Tractor's MoG rendering, but a separate JAX reimplementation.
- **Deblending**: real joint multi-source per-tile linear solves (`build_cutout_tiles`, `tiling.py`) — every source in a tile's halo is fit together; all tiles of a cutout run in one `vmap` (JAX) or one upstream `optimize_forced_photometry` per tile (cpu-tractor), on the same 15-px-core/3-px-halo grid.
- **Multiple exposures/visits are NOT jointly fit — the key finding for stacking.** `pipeline.run_photometry`'s per-cutout loop (`pipeline.py:150-201`) builds/solves/extracts each visit independently; there is no cross-cutout linear system anywhere. Combination across visits is purely post-hoc, inverse-variance-weighted averaging of already-fitted per-visit fluxes (`spectra.bin_spectrum`/`bin_to_channels`), grouped by id and sorted by wavelength. Genuine joint multi-exposure forward-model stacking would get no help here beyond downstream ivar binning.
- **Four solvers** (verified against `make_tiled_solver`, `jax_backend.py:~275-310`): `linear` (ridge WLS); `eigfloor` (default; sign-free eigenvalue floor on the normalized normal equations, keeps negative fluxes, calibrated errors per docs); `eigfloor_prior` (`eigfloor` + per-source Gaussian SED priors from log-log interpolation over LS g/r/i/z/W1/W2, `priors.py`, faint sources only); `lasso` (non-negative LASSO with auto SNR penalty, sign-free debias on protected sources). `cpu-tractor` supports `linear` only, else `ConfigError`.
- **Error propagation** differs by backend: JAX variance marginalizes over co-fit neighbours in the tile; `cpu-tractor`'s is upstream Tractor's raw Fisher diagonal, explicitly documented as **not** marginalized over neighbours or the per-tile background — systematically too-small errors in blended tiles. The `eigfloor` error calibration is a documented claim about the author's own real-data campaign, not reproduced by any test here.
- **Output**: one parquet row per (source, visit) with config/solver-spec/schema-version in metadata; `build_spectra` groups by id, sorted by wavelength (handles SPHEREx's within-detector wavelength non-monotonicity).

## Extended-source support

- Shape convention: `shape_r` arcsec (`0`/missing ⇒ point source, **no range clamp** — unlike the IRSA tool's stated 1-20" range), `sersic` (missing ⇒ 1.0), `shape_e1/e2` → `shape_ab`/`shape_phi` via `ls_shapes_to_ab_phi` (`models.py:17-31`), whose docstring notes it fixes a "2026-07-04 PA sign bug" — evidence of both active correctness work and a real prior bug in shape-angle handling.
- Convolution accuracy is **backend-dependent, and the recommended GPU-free path is the worse one**: JAX renders the whole galaxy at 5x and convolves/bins like point sources; `cpu-tractor` (the docs' recommended no-GPU path) renders the galaxy at **native** resolution before Fourier-domain PSF convolution — `docs/cpu_backend.md` states this plainly.
- No aperture-correction step exists anywhere — consistent with fitting the whole profile rather than a finite aperture, but worth noting as absent rather than handled.
- **In-repo quantitative validation is thinner than the gallery figures suggest.** `tests/test_cpu_backend.py::test_cross_backend_agreement_for_galaxies` fits four synthetic Sersic sources (n=1,4) on both backends and gets 0.1% agreement — a genuine but purely **self-consistency** check, not validation against external truth. `docs/worked_example.md`'s only quantitative galaxy recovery is against the package's own toy Gaussian-injected simulator, explicitly caveated as approximate; its stronger claim for real data ("bit-identical to the validated production driver, see the project notes") points at non-public material. `docs/gallery.md`'s six real-A2537-galaxy figure compares solvers against LS/WISE broadbands explicitly framed as a bracketing sanity check "not truth," plus a genuinely useful documented failure mode (catalog "shredding" of a resolved galaxy into spurious extra sources). **Net: in-repo extended-source evidence is cross-backend self-consistency plus qualitative real-data plots, not validation against known truth**; arXiv:2606.19875's validation (a different, non-JAX codebase) should not be assumed to transfer.

## Code quality

- Extensive, cross-referenced Sphinx docs (readthedocs) that mostly match the code on direct inspection — PSF-kind branching, background models, solver descriptions all check out. Gaps found: `roadmap.md` stuck at "v0.1"; `paper_reproduction.md`'s "the paper" is never precisely identified.
- CI (`.github/workflows/ci.yml`) runs `ruff check` + `pytest` on `JAX_PLATFORMS=cpu` (Python 3.11/3.12) and a Sphinx build, but does **not** install upstream `tractor` — every `cpu-tractor` test is skipped in CI and only runs if a developer has it installed locally. No GPU CI exists, so GPU-path correctness rests entirely on the author's own testing.
- All fixtures are synthetic (`tests/fixtures/synth.py`); there is no real-SPHEREx fixture in the repo, so "tested" here means "against synthetic injected sources."
- Careful coverage: `test_epsf.py` (QR2/R7 dispatch incl. the wrong-mode regression), `test_per_tile_wcs.py`/`test_occupancy_caps.py` (narrow, pinned invariants), `test_zone_psf_blend.py`, `test_models_priors_bg.py`.
- Several inline comments document specific historical bugs with numbers (CPU Fourier-path galaxy under-normalization fixed in 0.3.1, `psf_zone_interp`/core-shift silent no-op, the PA sign bug) — transparent, but also evidence the numerics have been wrong more than once in ~2 months.

## Reusable pieces for our project

Reusable independent of the reference-catalog design:

- **QR2/QR3 PSF-kind auto-detection** (`io/cutouts.py:psf_kind_from_header`, `prepare.py:psf_stamp_5x`/`pixel_integration_for`/`core_shift_applies`) — small, well-tested dispatch-on-header pattern worth copying conceptually, including testing the wrong-mode failure explicitly.
- **`prepare.py:downsample_psf_oversample2`** — sum-preserving 10x→5x PSF downsample with documented centering math.
- **`background.py:fit_background_cwave`** — CWAVE-binned PCHIP airglow removal then `Background2D`, a self-contained technique for the He I 1.083 µm line and other iso-wavelength stripes, useful independent of forced photometry.
- **`io/cutouts.py:cutout_pixel_area_sr`** (SAPM-preferring solid-angle map) and **`sample_map_bilinear_vec`** (per-source CWAVE/CBAND sampling) — small, correct, directly reusable for flux calibration and per-object wavelength labelling.
- **`tiling.py`/`occupancy.py`** — core+halo tiling and pre-solve occupancy scanning are a solid pattern for tiled forward-model fits, though our own "occupancy" notion would differ without a dense external catalog.
- **`backends/cpu_psf.py:OversampledPixelizedPSF`** — fixes a real, non-obvious `1/sampling**2` flux-normalization bug in stock `tractor.psf.PixelizedPSF`; valuable if we use plain Tractor for a free-parameter (non-forced) fit.
- **`spectra.py`** (`spherex_channels`, `channel_index`, `bin_to_channels`) — the 102-channel SPHEREx grid and detector-aware channel assignment are reusable as-is.

Tied to this repo's specific design, needing rework for our own approach:

- The fit is entirely *forced*: positions/shapes never fit. Free-parameter fitting is roadmapped, not implemented — semi-resolved/resolved post-starburst galaxies lacking trustworthy external shape priors are exactly what this package doesn't yet handle; we'd build that layer ourselves, likely on `tractor_jax` directly.
- Output is a crowded-field flux table; a clean per-object spectrum is a much smaller problem than the catalog-depth/deblending/SED-prior machinery here, which would be unneeded complexity to carry.
- No cross-visit joint solve exists — true forward-model stacking across visits is new work, not inheritable from `pipeline.run_photometry`.

## Risks and limitations

- **arXiv:2606.19875 connection is unverified from the public repo** — no citation anywhere, unclear relationship to the cited private "production driver."
- **Flag handling is not release-aware** — fixed bit-position table, no `MP_*`/`MSKN`/`MSKM` reading; a QR3 bit-position change would silently break masking.
- **Background is global-per-cutout + per-tile constant**, not a local per-source aperture background — a real methodological difference from the IRSA tool.
- **No cross-exposure/visit joint fit** — stacking is post-hoc ivar-weighted combination only.
- **Extended-source accuracy is asserted more strongly in prose than pinned by tests** — only cross-backend self-consistency and toy-simulator checks exist in-repo.
- **CPU-only users are steered to the backend that is worse for resolved sources** (`cpu-tractor`'s native-resolution galaxy rendering).
- **Very small, single-author project**: 1 star, restricted issues, ~2 months old, Alpha, three interdependent non-PyPI packages by one author — mitigated somewhat by unusually careful tests/docs.
- **`shape_r`/Sersic index are unvalidated inputs** — no range checks; bad catalog values pass straight to the renderer.

## Verdict

**Borrow pieces.** `tractorjax-spherex` is well-engineered, well-tested, and well-documented for its actual use case — reference-catalog fluxes on a crowded field with a trusted external position/shape catalog — and several components (QR2/QR3 PSF-kind dispatch, CWAVE-airglow background, SAPM-aware units, tiling/occupancy machinery, the corrected oversampled-PSF Tractor subclass, the SPHEREx channel grid) are directly reusable or worth close imitation. But its central design — fixed external positions/shapes, independent per-visit fits combined only afterward — does not match the target project's need for its own PSF forward modeling of resolved/semi-resolved post-starburst galaxies without reliable external shape priors, nor does it offer multi-exposure joint fitting or local background estimation. Its extended-source handling is conceptually sound (MoG-Sersic at oversampled resolution, same lineage as arXiv:2606.19875) but not independently validated in this public repo. Read it closely for data-model handling and PSF/background utilities; do not adopt `run_photometry` as our extraction backbone.
