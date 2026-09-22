# leejjoon/sphx_spec_stack

## Metadata

- **Author**: Jae-Joon Lee (`lee.j.joon@gmail.com`, GitHub `leejjoon`). No institutional affiliation stated anywhere in the repo (README, docs, pyproject.toml, commit messages).
- **License**: MIT per the `pyproject.toml` classifier (`License :: OSI Approved :: MIT License`); there is no standalone `LICENSE` file in the repository, so the license is not formally attached to the code.
- **Language**: Python (>=3.9 declared; developed/run under conda env `sphx`, Python 3.13 per `CLAUDE.md`).
- **Stars/forks**: 0 stars, 0 forks, 0 watchers (as of 2026-09-23) — effectively unpublicized/private-use repo.
- **First commit**: 2026-06-23 ("Initial commit: Set up sphx_spec_stack package with GP stacking and examples"). **Last commit**: 2026-07-05 ("Implement P3 line discovery: find_lines + first test suite + example"). Nine commits total (GitHub commit-history page), all authored by Jae-Joon Lee, spanning under two weeks.
- **Open issues**: 0. No PRs, no CI workflow, no GitHub Actions.
- **PyPI**: not published.
- **Tests**: `tests/test_discovery.py`, 11 synthetic pytest cases covering `find_lines` only; the core `reconstruct_spectrum` GP solver has **no automated tests** (explicitly flagged as open roadmap item P0 in the repo's own docs).
- **Docs**: unusually extensive in-repo Markdown documentation (`docs/00_overview.md` through `05_roadmap.md`, plus an append-only decision log and a frozen `archive/initial_plan/`). No ReadTheDocs/Sphinx site.
- **Associated paper**: none found.

This repository reads like a personal/lab research-software project developed with heavy AI-agent assistance (there is a `CLAUDE.md` session entry point, an append-only "decision log," and hard-coded absolute paths to `/home/jjlee/...`), rather than a community package.

## Purpose and scope

`sphx_spec_stack` does **one narrowly-scoped thing**: 1D super-resolution reconstruction of a spectrum from many undersampled, independently-dithered wavelength samples, using an exact (non-approximate) Gaussian Process regression. It explicitly targets two use cases — stacking many observations of similar point sources (stars), and stacking many spatial samples (pixels/regions) of one extended source — but **only at the level of pooled `(wavelength, flux, flux_error)` triples**. It does not ingest SPHEREx L2 images, does not do photometry, and does not do continuum fitting; all of that is assumed to happen upstream, outside this package.

## Data access layer

**None.** There is no IRSA/IBE/TAP/S3 client anywhere in the codebase. The package's only "data access" is `pandas.read_parquet()` on a pre-extracted local Parquet file (`examples/ex.parquet`, 593,079 rows, columns `wvl, image, image_cont, variance, pah, tmpl_ind, src_x, src_y, expidn, band, pipe_run`). That file is `.gitignore`d and, per `docs/03_implementation.md`, exists **only on the original author's machine** — a fresh clone of the repo cannot run any example. Its provenance (which upstream pipeline produced `image_cont`/`pah`, which nebula, which SPHEREx data-release version) is explicitly recorded as "not recorded — TBD" in the docs (roadmap item P1). There is therefore nothing hard-coded about SPHEREx release names, S3 paths, or IRSA endpoints to worry about — but also nothing reusable for actually getting data out of SPHEREx L2 products.

## Data model handling

**Not applicable / out of scope.** The package never opens a FITS file. It has no concept of MEF extensions, PSF vs EPSF, FLAGS bitmasks (MP_* or MSKN/MSKM), WCS-WAVE vs CWAVE/CBAND, ZODI, VARIANCE-as-array, or solid-angle maps. All of this is assumed to have already been reduced, by an external ("upstream") pipeline, into the four/five flat columns the public API consumes (`wvl`, `image`, `image_cont`, `variance`, optional `norm`). The `tmpl_ind` column (template-image pixel index = per-region source identity for the extended-source case) is carried through in the bundled example data as the pandas index but is **not consumed by the API** — the package is blind to spatial structure entirely.

## Photometry / extraction method

N/A — no photometry or flux extraction is performed. The package's input is already-extracted, already-continuum-baselined flux (`image`), a broad continuum baseline (`image_cont`, "provided per-point by the upstream pipeline"), a variance, and an optional normalization profile. The rectification the package itself performs is `y = (image − image_cont) / norm`, with `y_err = sqrt(variance) / norm`, in log-wavelength coordinate `x = ln(λ)`.

## Stacking method

This is the substantive part of the tool and is well worth reading closely:

- **Irregular per-object wavelength sampling**: handled by simply pooling all `(x_j, y_j, σ_j)` triples from every input observation/region into one long vector, globally sorted by `x = ln λ` (a hard requirement of the O(N) solver). There is no per-object alignment step beyond this — see below.
- **GP kernel**: a stationary, **quasiseparable** kernel from `tinygp.kernels.quasisep`, giving an exact O(N) GP solve (Kalman-filter-style sequential sweep) rather than the O(N³) dense-GP solve, which is what makes N≈600k tractable (~3 s on a laptop CPU). Default is **Matérn-5/2** (`kernels.quasisep.Matern52`); **Matérn-3/2** is kept as a legacy option; a critically-damped **SHO** kernel is also available. Squared-exponential is discussed but explicitly rejected as "not O(N) in tinygp's quasiseparable framework."
- **Hyperparameters**: `sigma_gp` (GP amplitude), `f_scale` (multiplicative inflation of the nominal per-point error — found empirically to need ≈4× inflation relative to the naive `variance` column, flagged as a real, unresolved data/pipeline-noise-model problem, not a kernel artifact), `s_jitter` (flat noise floor). All three are fit once, offline, to the bundled dataset by marginal-likelihood minimization (`examples/compare_kernels.py:refit_hyperparams`, **not yet promoted into the package API** — roadmap P2) and are **not** refit automatically for new data; the function-signature defaults are dataset-specific and would need to be refit for a PSB spectra application.
- **Length-scale calibration**: rather than fitting the kernel length-scale ρ, it is analytically calibrated so the kernel's autocorrelation FWHM equals the assumed instrumental resolution element `1/R_TRUE` in log-wavelength, via kernel-specific constants (`_FWHM_FACTORS` in `reconstruction.py`: 1.9380 for Matérn-3/2, 2.0842 for Matérn-5/2, solved numerically from the half-max condition). The docs record a genuine historical bug (using the Gaussian FWHM↔σ constant 2.3548 with a Matérn-3/2 kernel, oversizing the length scale by ~21%) as a worked cautionary example — useful reading even if you don't reuse the code.
- **Rest-frame shifting**: **not done.** Data are assumed already on a common observed-wavelength system; no radial-velocity/redshift correction exists anywhere in the package. This is an explicit, documented scope exclusion (`docs/01_method.md` §8), so it is *not* directly usable for combining post-starburst galaxies at different redshifts without adding this step yourself.
- **Normalization/weighting**: division by a user-supplied `norm` profile (e.g., a PAH continuum shape) before stacking; a scalar fallback of 8.5 if `norm` is omitted is flagged in the docs as a "wart" to be removed. Per-point weighting in the GP solve is via the heteroscedastic diagonal noise model `(f_scale·σ_y)² + s_jitter²`, i.e. inverse-variance-like weighting through the GP machinery itself, not an explicit external weight.
- **Uncertainty of the stack**: exact GP posterior variance on the output grid (`Σ* = K** − K*ᵀ(K+Σ)⁻¹K*`), returned as `std_all`/`gp_std` alongside the mean. A separate validation study (`examples/explore_sample_size.py`) demonstrates empirical σ ∝ 1/√N convergence from N=18 to N=593k.
- **Extended-source region handling**: there is **no special-cased code path** for extended sources. The "extended source spatial-region stacking" capability referenced in third-party descriptions of this repo is really just that the generic pooling mechanism is agnostic to whether input rows come from many stars or many sky pixels of one nebula — the bundled `ex.parquet` example happens to be the latter (593k SPHEREx-like samples of a diffuse emission nebula, one row per template-image pixel per epoch), but the reconstruction algorithm treats it identically to a star-stack. No spatial/PSF-aware weighting, deblending across sky positions, or region definition logic exists.
- **Output grid**: uniform in log-wavelength, `Δx = 1/(N_SUB·R_TARGET)` with `R_TARGET` defaulting to `3·R_TRUE`, mapped back to `λ = exp(x)`.

## Extended-source support

Point-source and extended-source inputs are handled identically because the package operates purely on pooled scalar triples; there is no Sersic/galaxy-profile modeling, no elliptical apertures, no aperture corrections, and no spatial-region definition tooling. Any "extended source" support is entirely the responsibility of whatever upstream pipeline produced the pooled `(wvl, image, image_cont, variance, norm)` table — which this repo does not provide or document beyond a TBD provenance note.

## Code quality

Small, clean, single-purpose codebase: `sphx_spec_stack/reconstruction.py` (~215 lines), `discovery.py`, `plotting.py`, three-function public API (`reconstruct_spectrum`, `find_lines`, `plot_reconstruction`). Documentation-to-code ratio is very high and unusually candid about limitations, divergences from an original plan, and even a historical numerical bug — genuinely useful for understanding *why* design choices were made. However: no CI, no packaging release, zero external users/stars, only 9 commits over 12 days, hard-coded absolute paths to the author's machine in `CLAUDE.md` and `examples/README.md` (`/home/jjlee/...`), and the core reconstruction function has no test coverage at all. It is completely agnostic to (and therefore immune to) any SPHEREx pipeline-version changes (QR2→QR3→DR1) since it never touches FITS files, EPSF, or flag headers — but that same fact means none of the SPHEREx-specific robustness concerns in this review apply, positively or negatively.

## Reusable pieces for our project

- `sphx_spec_stack/reconstruction.py::reconstruct_spectrum` — the whole O(N) tinygp quasiseparable-kernel stacking routine is directly reusable as-is once you have pooled `(wvl, flux, continuum, variance[, norm])` arrays from your own PSB spectra/regions; this is the single highest-value piece of the repo.
- `sphx_spec_stack/reconstruction.py::_FWHM_FACTORS` and `_build_kernel` — the per-kernel FWHM→length-scale calibration constants and derivation are directly portable to any tinygp/celerite-based GP stacker, including the underlying math worked out in `docs/01_method.md` §4-5.
- `sphx_spec_stack/discovery.py::find_lines` — SNR-thresholded peak-finding with parabolic sub-grid refinement, curvature-based blend flagging, and second-derivative shoulder detection on a GP posterior — reusable for finding PAH/emission features in a stacked PSB spectrum.
- `examples/compare_kernels.py::refit_hyperparams` — L-BFGS-B marginal-likelihood refit pattern (via `jax.value_and_grad`) for `(sigma_gp, f_scale, s_jitter)` on a strided subsample; needed before the defaults can be trusted on any new dataset.
- `docs/01_method.md` — worth reading in full as a design reference even without reusing code, particularly the length-scale-calibration bug writeup and the "what the method does NOT do" scope fence (§8), which doubles as a checklist of what *we* would still need to build (rest-frame shifting, per-source continuum fitting, deblending) on top of this core.

## Risks and limitations

- No data-access or SPHEREx-format layer whatsoever — this only helps with the *last* step (stacking already-extracted spectra/pixel photometry), not extraction from L2 images.
- Default hyperparameters (`sigma_gp`, `f_scale`, `s_jitter`) are fit to one specific, undocumented dataset and must be refit for PSB spectra; the refit tool is not in the package API.
- No rest-frame/redshift alignment — required for stacking spectra across multiple PSB galaxies at different z, and entirely absent.
- No continuum-fitting, deblending, or physically-motivated line model; `find_lines` only flags blends, doesn't resolve them.
- Essentially unmaintained/unreleased research code: 0 stars, 9 commits, no CI, no packaging, untested core algorithm, single author, no external validation beyond one dataset.
- Absolute machine-specific paths in docs (not a functional bug, but signals low portability maturity).

## Verdict

**Borrow pieces.** Do not adopt this as a dependency (unpublished, untested core, single-author research script), but the `reconstruct_spectrum` GP-stacking routine and its length-scale calibration are a strong, working reference implementation for the exact problem we'll face when combining irregularly-sampled SPHEREx spectra across multiple PSB galaxies and/or spatial regions — reusing or adapting `reconstruction.py` directly (with our own hyperparameter refit and an added rest-frame-shift step) is a reasonable starting point, rather than re-deriving the tinygp quasiseparable-kernel FWHM calibration from scratch.
