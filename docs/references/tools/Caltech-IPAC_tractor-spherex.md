# Caltech-IPAC/tractor-spherex

## Metadata

- **URL**: https://github.com/Caltech-IPAC/tractor-spherex
- **License**: `NOASSERTION` per GitHub API (`license.key: other`) — the fork keeps upstream's verbatim GPLv2 text without a repo-specific SPDX header. `FORK.md`: **GPLv2 only** (no "or later" clause anywhere); fork modifications `Copyright (C) 2023-2026, California Institute of Technology`; upstream copyright (`Dustin Lang & David W. Hogg`) preserved verbatim in `README.md`.
- **Language**: Python (100%), plus SWIG-wrapped C extensions built via `setup.py`.
- **Size**: 43,743 KB on GitHub; ~23 MB shallow clone.
- **Stars/forks/issues** (2026-09-23): 0/2/2.
- **Created** 2025-01-24, **last pushed** 2026-06-29 (HEAD `066680f`, PR merge documenting the fork).
- **Tags**: mirrors upstream `dstndstn/tractor`'s full tag history (`0.1` 2015-07-28 through `dr10.5`) plus SPHEREx-specific `dr9.4`, `dr9.5`, `dr9.6`, `rc-spectrophoto-1.0`, `test2` — confirms this fork was created by cloning/rebasing full upstream history, not importing snapshots.
- **Fork point** (`FORK.md`): upstream commit `8dc2bd8bce29db73968b1edf99a23b1c9130d074`, 2025-10-06, just after `dr10.6`.
- **Structure**: standard upstream layout — `tractor/` (`engine.py`, `image.py`, `psf.py`, `galaxy.py`, `sersic.py`, `optimize.py`, `lsqr_optimizer.py`, plus new `spherex_utils.py`), `doc/`, `examples/`, `projects/`, `test/`, `wise/`.
- **Installable**: yes in principle — `pyproject.toml` (fork-added) declares `dependencies = ["numba", "numpy", "opencv-python-headless"]`; `spherex-pipelines`' `[tractor]` extra installs via `pip install git+https://github.com/Caltech-IPAC/tractor-spherex.git@main`. Friction beyond declared deps: `setup.py` (still present) builds three SWIG/C extensions (`_mix`, `_emfit`, `_mp_fourier`), needing a C compiler + SWIG; upstream README instructs installing `astrometry.net` first, and `spherex_utils.py`/`optimize.py`/`lsqr_optimizer.py` import `astrometry.util.*` — **a hard runtime dependency not declared in `pyproject.toml`**. Optional Ceres support needs a system Ceres install. Not on PyPI as `tractor` (verified: no match).
- **Dependencies**: declared `numba`, `numpy`, `opencv-python-headless` (all needed specifically for the fork's changes). Undeclared-but-required: `astrometry.net` Python utilities, `scipy`.
- **Docs**: upstream `doc/` (generic, not SPHEREx-specific); `README.md` (fork banner + verbatim upstream); **`FORK.md`** — an unusually thorough, itemized account of what changed and why.
- **Tests**: upstream `test/` suite (`test_tractor.py`, `test_galaxy.py`, `test_forced_phot.py`, `test_psfex.py`) present but, per `FORK.md`'s change list and a listing of `test/`, **not extended** with SPHEREx-specific tests for `spherex_utils.py` or the `psf.py`/`optimize.py` changes.
- **CI**: `.github/workflows/codeql-analysis.yml`; `.circleci/` reports to upstream's CircleCI project (README's own badge disclaimer: badges reflect upstream CI, not this fork).

## What is public and what is not

The fork appears fully public: `FORK.md` itemizes every changed file, and inspection confirms the changes match the stated intent, with no evidence of undisclosed forked files. Five changed areas per `FORK.md`:
1. `pyproject.toml`/`requirements.txt` — packaging only.
2. `tractor/lsqr_optimizer.py` — "memory optimized derivative handling."
3. `tractor/optimize.py` — "time optimized image addition; computed covariant errors."
4. `tractor/psf.py` — "`numba` optimized Lanczos shifting."
5. `tractor/spherex_utils.py` — new module, "SPHEREx-specific utilities; added function to support arbitrary PSF oversampling when fitting shapes."

Everything else (`engine.py`, `image.py`, `galaxy.py`, `sersic.py`, `wcs.py`, `patch.py`, C extensions, `wise/`, `projects/`) is unmodified upstream. **No SPHEREx-specific PSF class, galaxy-profile class, or likelihood/background term is defined in this repo.** The SPHEREx PSF object (`SPHERExTractorPSF`) lives in `spherex-pipelines` (`spx_utils/photometry/tractor_utils.py`), duck-typed against `tractor.ducks.ImageCalibration`/`Params`, calling this fork's `lanczos_shift_image` (from `psf.py`) and monkey-patching `tractor.galaxy.ProfileGalaxy.getUnitFluxModelPatch` with this fork's `getUnitFluxModelPatchSPHEREx` (from `spherex_utils.py`) at import time. **This repo supplies the low-level rendering primitives; the SPHEREx PSF object and monkey-patch wiring live in `spherex-pipelines`.** Reading only this repo would not reveal how SPHEREx's PSF is actually plugged into Tractor. No withheld SPHEREx-specific code was found — sync'd from an internal `IPAC-SW/tractor` remote per `spherex-pipelines`' changelog `SP-2187`.

## Level 3 photometry in detail

Not applicable as a standalone section: `tractor-spherex` is a generic probabilistic-modeling *library* (`Image`, `Tractor`, `PointSource`, `SersicGalaxy`, `optimize_forced_photometry`), not a SPHEREx pipeline task. The L3 forced-photometry algorithm (windowing, background modes, cutout sizes, flag aggregation) lives entirely in `spherex-pipelines` and is documented in the companion note; this repo is one of its two key dependencies (with `photutils`).

## Background and zodi modules in detail

None. No zodi or diffuse-background code exists here. `ConstantSky(0.0)`, used by `spherex-pipelines` to represent "background handled elsewhere," is upstream's unmodified trivial constant-sky class, not a fork addition. All background/zodi logic is external, in `spherex-pipelines`.

## Source mask and reference catalog handling

None — out of scope for a generic modeling library. Source masking and reference-catalog assembly are entirely in `spherex-pipelines` (companion note).

## PSF/ePSF handling in detail

The fork's primary contribution, in two files:

**`tractor/psf.py`** (990 lines; changes confined to a documented block, dated `2026-06-09: partial vectorization adapted for Numba`):
- `lanczos_filter(order, axis_array)` — new, `@njit`-compiled 1D Lanczos kernel: `L(x)=sinc(x)·sinc(x/order)` for `|x|<order` else 0, normalized (`kernel /= kernel.sum()`). Docstring notes this differs from `astrometry.util.miscutils`'s unnormalized, non-JIT version.
- `lanczos_shift_image(img, dx, dy, l_order=3, inplace=False)` — builds Lanczos-3 (7-tap) 1D kernels via `lanczos_filter`, applies as two sequential separable `cv2.filter2D` convolutions (`BORDER_CONSTANT`). Called both by `spherex-pipelines`' `SPHERExTractorPSF.getPointSourcePatch` (point-source sub-pixel centering) and this fork's own `spherex_utils.py` (Sersic/FFT sub-pixel centering).

**`tractor/spherex_utils.py`** (291 lines, entirely new): `getUnitFluxModelPatchSPHEREx(self, img, px, py, minval, modelMask, force_halfsize, **kwargs)` — a full reimplementation of Tractor's unit-flux galaxy-patch rendering:
- Reads PSF oversampling generically off `img.getPsf()._psf.oversampling` (scalar or `(y,x)`, must be equal) — genuinely "arbitrary PSF oversampling," not a hardcoded factor.
- Requires the PSF object to expose `getFourierTransformHiRes(px, py, halfsize)` (implemented by `SPHERExTractorPSF` in `spherex-pipelines`, not here).
- Computes the galaxy's Fourier profile at oversampled scale (via a synthetic `Image` with `NullWCS` pixel scale divided by the oversampling factor), multiplies by the PSF's FFT, inverse-FFTs, applies a sub-pixel **Lanczos-3 shift in the oversampled frame** (`lanczos_shift_image(..., inplace=True)`), then **downsamples with `cv2.resize(..., INTER_AREA)`** and **normalizes** (`G /= G.sum()`) back to native resolution, tracking integer-vs-sub-pixel offsets carefully for `modelMask`-constrained renders.
- Docstring states: unlike upstream (mixture-of-Gaussians *or* FFT), this method **only uses FFT rendering** for SPHEREx — the fast MoG path is bypassed for correctness at oversampled PSF scales.
- Wired in via monkey-patch executed as a **module-level side effect on import of `spherex-pipelines`' `tractor_utils.py`**, not by this file itself.

**Not present here**: any code reading `PSFZoneData`/a FITS PSF cube, or performing bilinear zone-blending — all in `spherex-pipelines`, which duck-types against this fork's PSF interface (`getPointSourcePatch`, `getFourierTransformHiRes`, `.shape`, `.getRadius()`).

## Wavelength assignment (how CWAVE/CBAND are used per measurement)

Not applicable — no concept of wavelength, CWAVE, or CBAND here; a `tractor.Image` is purely 2D (data, invvar, PSF, WCS, photocal, sky), with no wavelength-tagging mechanism. Per-source wavelength/bandwidth assignment happens entirely after the Tractor fit returns a flux, inside `spherex-pipelines`.

## Other modules relevant to us (mosaic, spectral channels, DQA)

None of these apply to `tractor-spherex` either — it has no mosaic, spectral-channel, or DQA code; it is purely the fitting/rendering engine invoked once per detector window by `spherex-pipelines`. The genuinely relevant "other modules" in this repo are the two general-purpose optimizer files below.

- **`tractor/optimize.py`** (593 lines; changes 2023-11-03 to 2026-03-03): adds/updates **covariant errors** (proper covariance, not diagonal-only), plus general performance work. Relevant if we need per-source flux *covariances* (e.g. blended-field error propagation) beyond the diagonal variance `optimize_forced_photometry(variance=True)` already returns.
- **`tractor/lsqr_optimizer.py`** (700 lines; change 2026-03-03): the `LsqrOptimizer` actually invoked by `optimize_forced_photometry`; performance-only changes.
- **Sync policy** (`FORK.md`): upstream `main` merged in periodically ahead of major SPHEREx processing cycles — not continuously rebased (fork point 2025-10-06, roughly a year stale relative to 2026-09-23).

## Reusable pieces for our project

- **Depend on this package directly** for bit-for-bit consistency with the official pipeline's rendering. No Rubin-Butler dependency — only `numpy`, `numba`, `opencv-python-headless`, `scipy`, and `astrometry.net`'s utilities (undeclared, install separately). `pip install git+https://github.com/Caltech-IPAC/tractor-spherex.git@main` (after `astrometry.net` + a C/SWIG toolchain) is realistically practical.
- **`tractor.psf.lanczos_shift_image`**: directly importable as our sub-pixel shift primitive to match the pipeline's exact kernel, independent of how we build our PSF object.
- **`tractor.spherex_utils.getUnitFluxModelPatchSPHEREx`**: directly reusable once we have a PSF object implementing `getFourierTransformHiRes` (would need our own such object, following `SPHERExTractorPSF`'s example, unless we reuse `spherex-pipelines`' `PSFZoneData` wholesale). Re-deriving this FFT/pad/shift/downsample bookkeeping from scratch would be significant and error-prone — worth the GPLv2 obligation to borrow.
- Standard upstream API (`Tractor`, `Image`, `PointSource`, `SersicGalaxy`, `GalaxyShape`, `SersicIndex`, `LinearPhotoCal`, `NullWCS`, `ConstantSky`, `optimize_forced_photometry`) is the natural common substrate for our own extraction code.

## Risks and limitations

- **GPLv2**: copyleft, stricter than `spherex-pipelines`' BSD-3-Clause. If our codebase links/imports `tractor`/`tractor-spherex`, GPLv2 obligations apply to the combined work — a licensing question for the user's own judgment, flagged here not resolved.
- **Undeclared `astrometry.net` dependency**: a naive `pip install` of only the declared deps fails at import time for `spherex_utils`/`optimize`/`lsqr_optimizer`.
- **C-extension build requirement**: SWIG + C compiler needed for `_mix`/`_emfit`/`_mp_fourier` (standard for Tractor generally, not fork-introduced, but real setup friction).
- **Fork lag**: only synced ahead of major processing cycles; fork point ~1 year stale relative to today — check `main`'s last upstream merge before assuming recent upstream behavior is present.
- **No SPHEREx-specific tests here**: correctness of `getUnitFluxModelPatchSPHEREx`/`lanczos_shift_image` is presumably validated by `spherex-pipelines`' own test suite, not this repo's.
- **Interface coupling, not inheritance**: understanding this repo's PSF work requires reading it alongside `spherex-pipelines`, since the actual SPHEREx PSF class lives there.

## Verdict

**Use directly**, as a dependency, for the PSF/galaxy-rendering primitives. A small, well-scoped, unusually well-documented fork (`FORK.md` is a model for documenting a scientific-code fork) whose real value — Lanczos-3 sub-pixel shifting and arbitrary-oversampling FFT rendering of Sersic/`ProfileGalaxy` models through a pixelized, oversampled PSF — is exactly the hard, easy-to-get-subtly-wrong machinery we would otherwise reimplement and validate ourselves. No middleware dependency (unlike `spherex-pipelines`), so realistically installable via `git+https` plus `astrometry.net` and a C/SWIG toolchain. Main friction is licensing (GPLv2) and setup, not code quality or scope. Plan to depend on this package for rendering, combined with our own PSF object (adapted from `spherex-pipelines`' `PSFZoneData`/`SPHERExTractorPSF`, or built fresh against the public ePSF FITS product), rather than reimplementing the FFT/Lanczos/downsample chain from scratch.
