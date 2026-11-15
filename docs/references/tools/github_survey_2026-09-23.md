# GitHub survey of SPHEREx tools (2026-09-23)

Scope: software beyond the already-reviewed set (`banados/spherex-tools`,
`freddavies/spherextract`, `jgagneastro/SPIFF`, `andrijazupic/SPHEREx_pipeline`,
`yayasaikou1/spherex-cutoutdb`, `hbahk/spherex-retrieval`, `huntbrooks85/xcavation`,
`afaisst/SPHERExSpecPhot`, `Caltech-IPAC/irsa-tutorials`,
`Caltech-IPAC/spherex-archive-documentation`, and the official
`SPHEREx/spherex-sky-simulator`-style repos), relevant to extracting reliable
0.75-5 um spectra of nearby galaxies (unresolved / semi-resolved / resolved)
from SPHEREx Level 2 spectral images with custom PSF forward modeling,
background handling, and stacking.

## Search method (queries run, pages fetched)

All lookups used the unauthenticated GitHub REST search API
(`api.github.com/search/repositories`, `sort=updated`) and the GitHub REST API
for individual repos/orgs/README contents (raw.githubusercontent.com), plus
`WebSearch` for arXiv/GitHub cross-references. No repository was cloned or
executed; only repo metadata and `README.md` files were fetched.

Repository-search queries (each `q=` term, `per_page` 30-50, first 1-2 pages
where `total_count` warranted it):
`spherex`, `spherex+irsa`, `spherex+spectrophotometry`, `spherex+cutout`,
`spherex+psf`, `spherex+tractor`, `spherex+mosaic`, `spherex+galaxy`,
`spherex+spectra`, `spherex+extraction`, `spherex+forward+modeling`,
`spherex+stacking`, `spherex+catalog`, `spherex+jax`, `spherex+background`,
`spherex+decontamination`, `spherex+forced+photometry`, `spherex+resolved`,
`spherex+aperture`, `spherex+source`, `spherex+L2`, `spherex+point+spread`,
`spherex+PSF+photometry`, `spherex+dust`, `spherex+nearby`. The bare `spherex`
query returned 144 total repositories (2 pages pulled, sorted by most recently
pushed, covering activity back to late 2024).

Org listings pulled directly: `api.github.com/orgs/SPHEREx/repos` and
`api.github.com/orgs/Caltech-IPAC/repos` (filtered for SPHEREx/tractor names).

`WebSearch` queries: `SPHEREx galaxy spectra extraction github 2026 arxiv` and
`SPHEREx L2 spectral image PSF forward modeling extended source 2026`, used to
find recent arXiv papers (2026 postings) with software/data-availability
statements, then each candidate paper's arXiv abstract page was fetched with
`WebFetch` to extract code/Zenodo links.

## Official / SPHEREx-team repositories

Under the `SPHEREx` GitHub org (documentation/infrastructure, not science
pipelines):
- [SPHEREx/Public-products](https://github.com/SPHEREx/Public-products): static public-product reference material (16 stars, no recent activity).
- [SPHEREx/SPHEREx-Visualizer-Lite](https://github.com/SPHEREx/SPHEREx-Visualizer-Lite): lightweight all-sky/deep-coverage visualization code (Python), updated May 2026.
- `SPHEREx/spherex-doc-portal`, `spherex-doc-workflows`, `spherex-lander-plugin`, `spherex-sphinx`, `spherex-tex`, `spherex-templates` - internal documentation-build tooling (Sphinx/LaTeX/GitHub Actions), not analysis code.

Under `Caltech-IPAC` (the SPHEREx Science Data Center, SSDC):
- **[Caltech-IPAC/spherex-pipelines](https://github.com/Caltech-IPAC/spherex-pipelines)**: **public**, BSD-3-Clause, last pushed 2026-07-01. This *is* the official Level 1-3 pipeline code referenced in Akeson et al. (2026, arXiv:2511.15823). The README states it contains "essentially all the code for the SPHEREx Level 1 through Level 3 pipelines," built on Rubin Observatory's `dax`/`middleware` framework, and that it uses a modified fork of **The Tractor** for source photometry/extraction, maintained as `Caltech-IPAC/tractor-spherex`. Spacecraft telemetry handling, the data simulator (Crill et al. 2025), and shared system-engineering parameters are explicitly *not* included. The repo receives point-in-time snapshots tied to each public data release (starting with QR2, Oct 2025) rather than a live development history; SSDC states it cannot support external issues/PRs. This is the closest thing to ground truth for how L2 spectral images and L3 forced photometry are actually produced, and is worth reading even though it is not meant to be run outside IPAC/TACC.
- [Caltech-IPAC/tractor-spherex](https://github.com/Caltech-IPAC/tractor-spherex): SPHEREx-specific fork of `dstndstn/tractor`, last pushed 2026-06-29, license `NOASSERTION`. This is the actual forward-modeling engine (PSF + source-model rendering, optimization) used by the official L3 forced-photometry module, and by `hbahk/tractorjax-spherex` and the cluster-photometry validation paper below as the reference implementation.
- `Caltech-IPAC/spherex_butler_poc` - stale (2021) proof-of-concept for `dax_butler`; not relevant.

No separate, distinctly-named "SPHEREx sky simulator" repo turned up beyond what is already known; the simulator paper (arXiv:2505.24856) does not appear to ship a public standalone repo under `SPHEREx/*` at the time of this survey.

## Third-party repositories found

Table restricted to repositories with plausible astronomical/scientific content (many `spherex`-named hits are unrelated products - a Windows desktop-customization tool called "SphereXP", a chat app, firmware, a Solidity project, etc. - and were excluded).

| Repo | Author | Last push | Stars | Language | Purpose (one line) | Relevance |
|---|---|---|---|---|---|---|
| `hbahk/tractorjax-spherex` | hbahk | 2026-09-19 | 1 | Python | Reference-catalog forced photometry/spectrophotometry from L2 cutouts via a JAX port of Tractor | **High** |
| `gregreen/spherex_spectra` | gregreen (Gregory Green) | 2026-09-22 | 0 | Python | Modular JAX+Equinox PSF-photometry forward-modeling pipeline, multi-exposure spectra | **High** |
| `leejjoon/sphx_spec_stack` | leejjoon (Jae-Joon Lee) | 2026-08-26 | 0 | Python | 1D GP super-resolution spectral stacking (point sources or extended-source sky regions) | **High** |
| `WenkeRen/spxquery` | WenkeRen | 2026-07-11 | 10 | Python | Query/download/aperture-photometry/time-domain pipeline w/ dual background methods | **Medium-High** |
| `WenkeRen/spxdictlearn` | WenkeRen | 2026-09-01 | 1 | Python | ALS/HALS weighted-NMF dictionary learning to build empirical spectral templates from noisy, unaligned spectrophotometry | **Medium-High** |
| `fkiwy/spexpi` | fkiwy | 2026-05-23 | 0 | Python | Aperture + PSF photometry extraction pipeline for point sources, with template comparison and cutout stacking | **Medium** |
| `gemmahuai/deep-field-selection` | gemmahuai | 2025-02-10 | 1 | Jupyter | Tractor-based photometry-on-maps workflow for deep-field galaxies incl. PSF, ZL, and noise-map handling | **Medium** |
| `cli-tsinghua/SPIRAL` | cli-tsinghua (C. Li) | 2026-09-18 | 0 | Python | Zodi-subtracted, pixel-binned line/continuum feature-map pipeline (published, arXiv:2609.20295) | **Medium** |
| `MatthewDegtyar/spherex-noise-validation` | MatthewDegtyar | 2026-08-15 | 0 | Python | Validates SPHEREx per-pixel error bars against real noise; background/uncertainty QA | **Medium** |
| `RyanWills16/SPHEREx-airglow-analysis` | RyanWills16 | 2026-08-19 | 0 | Jupyter | Airglow (background) analysis code behind a published JGR:Atmospheres paper; Zenodo-archived | **Medium** |
| `leejjoon/ssiaat` | leejjoon | 2026-08-13 | 1 | HTML | "SPHEREx spectral image as a table" - tabular re-representation utility for L2 images | **Low-Medium** |
| `keflavich/spherex_cubemaking` | keflavich (Adam Ginsburg) | 2026-06-02 | 0 | Python | Exploratory downloader/cube-assembly scripts ("hacky") for SPHEREx spectral cubes | **Low-Medium** |
| `davidwhogg/SpherexZodi` | davidwhogg (David Hogg) | 2026-02-13 | 1 | TeX | Concept note for a purely empirical zodiacal-light model from SPHEREx data; no code yet | **Low-Medium** |
| `cmhainje/talltable` | cmhainje (Connor Hainje, w/ Hogg) | 2026-09-21 | 0 | Python | Data-format refactor of SPHEREx catalogs into a "tall table"; scope unclear from README | **Low** |
| `pwang55/prospector_emulator` | pwang55 | 2026-09-13 | 0 | Jupyter | PyTorch emulator of `prospector` SED fitting applied to SPHEREx-derived galaxy photometry | **Low** |
| `pwang55/SPHEREx-redshift-with-Dictionary-Learning` | pwang55 | 2026-02-02 | 1 | Jupyter | Online dictionary learning for photo-z from SPHEREx spectrophotometry | **Low** |
| `HyneSeeker/SPHEREx_DataProcessing` (a.k.a. `spherex-helium`) | HyneSeeker | 2026-06-22 | 0 | Python | Single-band (band 1) He I metastable-line intensity plotting tool | **Low** |
| `mpi-astronomy/spherex-tools` | mpi-astronomy (MPIA hack day) | 2025-11-07 | 0 | Jupyter | Grab-bag of scripts/notebooks from an MPIA SPHEREx Hack Day (Nov 2025) | **Low** |
| `rkiman/spherexminer` | rkiman | 2026-08-08 | 0 | Jupyter | Minimal/near-empty "extract and analyze data" scaffold | **Low** |
| `virajkaram/spherex` | virajkaram | 2026-09-17 | 0 | Python | No description; README is only a generic env-install snippet | **Low** |
| `andrijazupic`-adjacent, `jgizis/spherex-ucd-explore` | jgizis | 2026-06-18 | 0 | Jupyter | Exploration notebook built on SPIFF-extracted spectra (ultracool dwarfs) | **Low** |
| `ezhang33/Dusty-Galaxies-as-Seen-by-SPHEREx` | ezhang33 | 2023-10-15 | 1 | Jupyter | Pre-launch forecast: adds PAH features to AKARI/HSC photometry to mock SPHEREx colors | **Low** |
| `bscot/Broadband_tomography_with_CASTOR_and_SPHEREx` | bscot | 2024-07-12 | 0 | Jupyter | Forecast of CASTOR+SPHEREx joint background tomography (simulation only) | **Low** |
| `jadamo/covapt_mt` | jadamo | 2026-02-17 | 0 | Jupyter | Multi-tracer covariance refactor of CovaPT for SPHEREx power-spectrum inference | **Low (not extraction)** |
| `knguyen7224/SPHEREx-Star-Galaxy-Classification` | knguyen7224 | 2025-12-09 | 0 | Jupyter | Star/galaxy classifier on SPHEREx-derived features | **Low** |

Repositories checked and excluded as out of scope for galaxy-spectrum
extraction (ISM/line-intensity-mapping, cosmology inference, orbit/engineering,
or non-astronomical "SphereX"-named products): `tamojeetroychowdhury/SPHEREx-Prestellar-Cores`,
`MayankNAstro/SPHEREx_cube`, `MayankNAstro/SPHEREx_ice_map`, `bumhooLIM/spherex-comet`,
`bumhooLIM/SPHERExLC`, `yamada-yuka0322/LIM_Mock`, `yamada-yuka0322/SPHEREx_pipeline`,
`amata21/LCDM_null_tests_SPHEREx`, `MinjaeKim0827/KASI_SPHEREx_VHzQs`,
`poshakgandhi/spherex-varagn`, `johnarban/spherex-orbits`, `DominikaDu/SPHEREx_ciabatta`,
`Katerina-ll/spherex_OIII_Ha_overdensity`, `katieclogston/infrared-excesses-in-SPHEREx`,
`hbahk/spherex-challenge`, three `EnyuCAI-Eco/*` student repos, and
`davidwhogg/SPHERExImages` ("for Connor" - a notes/proposal TeX repo, no code).

## Detailed notes on the top 5 most relevant new candidates

**1.** [hbahk/tractorjax-spherex](https://github.com/hbahk/tractorjax-spherex)
Purpose: reference-catalog forced photometry/spectrophotometry directly from
SPHEREx L2 cutouts, by the same author as the already-known `spherex-retrieval`
downloader. Data access: wraps `spherex-retrieval` for cutout download and
expects an external position/shape catalog (e.g., Legacy Survey DR10).
Extraction method: joint deblending solve over all sources in a field, with
"four estimators, one flag" (blind vs. targeted vs. regularized full-catalog),
producing one spectrophotometric point per source per visit, assembled into
inverse-variance-binned, wavelength-sorted spectra. PSF handling: sources are
rendered on a 5x oversampled grid, then either pixel-integrated (QR2 optical
PSF) or point-sampled (R7 effective PSF, QR3+DR1), reading `PSFKIND` from the
bundle automatically. Runs on GPU or CPU via a JAX engine wrapping `tractor-jax`
([hbahk/tractor-jax](https://github.com/hbahk/tractor-jax)), with an optional classic-Tractor CPU
backend. Extended-source support: fixed catalog *shapes* (point + whatever
shape the input catalog provides) rather than free-form galaxy morphology
fitting; not yet validated for resolved/semi-resolved galaxies per its own
"alpha" status note. Maturity: alpha, not on PyPI, install-from-source, single
author, active (pushed 2026-09-19). License: GPL-3.0.

**2.** [gregreen/spherex_spectra](https://github.com/gregreen/spherex_spectra)
Purpose: "Modular SPHEREx PSF photometry pipeline in JAX + Equinox" (per its
`pyproject.toml`), built by Gregory Green (known for the Bayestar dust maps).
No top-level README, but an `explanatory_supplement.md` lays out a genuinely
relevant design: every physical ingredient (source spectrum, PSF, filter
transmission, telescope aperture) is a separate `equinox.Module` with a
well-defined interface contract, so PSF models, transmission curves, and
source-shape models are swappable without touching the image generator.
Explicitly aimed at sub-percent systematic accuracy, with quantile-based
wavelength integration for correct band-averaging. Package layout
(`spherex/image.py`, `image2.py`, `image3.py`, `psf.py`, `spectrum.py`,
`transmission.py`) suggests iterative versions of the forward image model.
Extraction method: forward-model fitting (not simple aperture photometry) via
`optimistix`/`lineax` (JAX nonlinear least squares). Extended-source support:
not evident from the file layout (no explicit galaxy-morphology module found);
looks point-source/PSF-photometry focused, but the modular design would make
adding a Sersic/extended-shape module straightforward. Maturity: active
(pushed 2026-09-22, most recently updated repo in this whole survey), no
license file, no stars/community yet - looks like an individual research
project rather than a released package. Worth watching given the author's
track record and the unusually careful numerical-precision design notes.

**3.** [leejjoon/sphx_spec_stack](https://github.com/leejjoon/sphx_spec_stack)
Purpose: **spectrum stacking** specifically - the one capability explicitly
named in the user's requirements that most other tools treat as an
afterthought. By Jae-Joon Lee (long-time IPAC/astropy-affiliated developer).
Method: 1D "super-resolution" reconstruction of a common spectrum from many
sparse, noisy, unaligned spectrophotometric points - explicitly supporting
both "multiple stars" and "different sky regions of an extended source,"
i.e., directly applicable to semi-resolved/resolved galaxy stacking across
spatial bins. Implementation: JAX-native Gaussian Process regression via
`tinygp`, with a default quasiseparable Matern-5/2 kernel whose length scale
is calibrated to instrumental spectral resolution; also ships a peak/line
finder (`find_lines`) with blend-flagging on the reconstructed spectrum.
PSF/background handling: none - this package consumes *already-extracted*
per-pixel/per-visit measurements (wavelength, flux, continuum-normalization
weight, variance) as a table; it is a pure post-extraction stacking/denoising
stage, meant to sit downstream of an extraction tool like SPIFF, spxquery, or
tractorjax-spherex. Maturity: documented (`docs/00_overview.md` through
`05_roadmap.md`), has example data and scripts, single author, no license
file, last pushed 2026-08-26.

**4.** [WenkeRen/spxquery](https://github.com/WenkeRen/spxquery)
Purpose: "SPHEREx Time-Domain Analysis Package" - automates query, download,
photometry, and visualization for a given sky position, on PyPI
(`pip install spxquery`), with ReadTheDocs documentation. Data access: queries
SPHEREx image products directly (IRSA), with cutout-only downloads (claimed
99% storage reduction) and parallelized, resumable execution. Extraction
method: **FWHM-based adaptive apertures** with **dual background-estimation
methods** (annulus and windowed background) - it already implements the kind
of background handling the user needs, even though its headline use case is
quasar/variable-source light curves rather than galaxy SEDs. PSF handling:
aperture-based, not forward-modeled. Extended-source support: not designed for
resolved galaxies - built around point-source time-domain targets (demoed on
the Cloverleaf lensed quasar). Maturity: the most productionized of the new
finds - PyPI release, readthedocs, QC/visual-inspection tooling, 10 stars, MIT
license, pushed 2026-07-11. Its companion package `WenkeRen/spxdictlearn`
(same author) was used in the 2026 paper "Empirical Near-Infrared Spectral
Templates from SPHEREx" (arXiv:2609.02167) to build a 14-component AGN/host
NMF dictionary from ~3,800 galaxies+AGN; that paper's code is archived on
Zenodo (DOI 10.5281/zenodo.22226283).

**5.** [fkiwy/spexpi](https://github.com/fkiwy/spexpi)
Purpose: "SPHEREx Spectrum Extraction Pipeline," built around ultracool-dwarf
use cases (including high-proper-motion targets) but stated to be applicable
to "any isolated point source." Data access: queries IRSA TAP for cutouts or
reuses a local cache, infers/stamps the data release (`DATAREL`) from
headers, and propagates target coordinates per-epoch for proper motion.
Extraction method: aperture photometry with local-annulus background
subtraction, and/or PSF photometry with an optional centroid grid search, both
runnable in the same pass (`photometry_method="both"`); converts detector
images/variance to flux via SPHEREx solid-angle pixel maps and can reduce
spectral oversampling using the calibration `spectral_channels` files. Also
ships template-spectrum comparison and cutout-stacking/plotting utilities.
Extended-source support: explicitly point-source only ("isolated point
source"); would need substantial extension for resolved galaxies. Maturity:
fairly complete/documented single-author package (full API docs section,
config reference, troubleshooting, citation block, project emblem image), MIT
license, pushed 2026-05-23, 0 stars.

## Software cited in 2026 SPHEREx papers

| Paper | Tool | Link |
|---|---|---|
| Akeson et al. 2026, "The SPHEREx Image and Spectrophotometry Processing Pipeline" (accepted, ApJS; arXiv:2511.15823) | Official L1-L3 pipeline (this *is* the description of `Caltech-IPAC/spherex-pipelines`) | [arXiv:2511.15823](https://arxiv.org/abs/2511.15823) ; [Caltech-IPAC/spherex-pipelines](https://github.com/Caltech-IPAC/spherex-pipelines) |
| Ren, Guo, Zheng et al. 2026, "Empirical Near-Infrared Spectral Templates from SPHEREx: Disentangling AGN and Host-Galaxy Emission" (arXiv:2609.02167) | `spxquery` extraction framework + weighted-NMF dictionary code (`spxdictlearn`); code/Zenodo archive | [arXiv:2609.02167](https://arxiv.org/abs/2609.02167) ; [WenkeRen/spxquery](https://github.com/WenkeRen/spxquery) ; [WenkeRen/spxdictlearn](https://github.com/WenkeRen/spxdictlearn) ; Zenodo DOI 10.5281/zenodo.22226283 |
| Bahk, Hwang, Bleem et al. 2026, "The SPHEREx View of Galaxy Clusters: A Simulation-based Validation of the Forced Photometry Pipeline for Extended Sources" (submitted, AAS Journals; arXiv:2606.19875) | The Tractor (official `Caltech-IPAC/tractor-spherex`) applied/validated for extended cluster-galaxy sources via simulated DESI+COSMOS mocks | [arXiv:2606.19875](https://arxiv.org/abs/2606.19875) ; [Caltech-IPAC/tractor-spherex](https://github.com/Caltech-IPAC/tractor-spherex) |
| Li, C. 2026, "SPHEREx 3.3 Micron Aromatic Emission in the Magellanic Clouds..." (accepted, ApJ; arXiv:2609.20295) | `SPIRAL` pipeline (zodi-subtracted, quality-masked, wavelength-window-binned feature-map builder) | [cli-tsinghua/SPIRAL](https://github.com/cli-tsinghua/SPIRAL) |
| Wills et al., JGR:Atmospheres (preprint arXiv:2605.00851) | `SPHEREx-airglow-analysis` (background/airglow characterization code) | [RyanWills16/SPHEREx-airglow-analysis](https://github.com/RyanWills16/SPHEREx-airglow-analysis) ; Zenodo DOI 10.5281/zenodo.21708478 |
| Green (unpublished/in-prep, per repo activity) | `spherex_spectra` JAX+Equinox forward-model pipeline | [gregreen/spherex_spectra](https://github.com/gregreen/spherex_spectra) |

(Surveyed via `WebSearch`/`WebFetch` only. Several other 2026 SPHEREx papers
appeared in search - star/galaxy separation, power-spectrum emulation,
redshift forecasting, ice/PAH mapping - but their abstracts did not surface a
distinct extraction/forward-modeling repo beyond what is listed above.)

## Recommendations (which of the new finds deserve a full code review)

1. **`hbahk/tractorjax-spherex`** - highest priority. It is the only
   third-party tool doing GPU/JAX Tractor-style forced photometry directly on
   L2 images with automatic PSF-kind handling (optical vs. effective PSF), by
   an author already producing validated extended-source Tractor results in
   the cluster-photometry paper. Read alongside `Caltech-IPAC/tractor-spherex`
   to understand how closely it tracks the official forward model.
2. **`gregreen/spherex_spectra`** - second priority. Its `explanatory_supplement.md`
   design write-up (quantile wavelength integration, oversampled
   PSF-convolution, modular interface contracts) is worth reading purely as a
   methods reference even before the code stabilizes; worth checking back
   periodically since it is currently the most actively updated repo found.
3. **`leejjoon/sphx_spec_stack`** - review for the stacking stage specifically;
   it is the clearest match to the "plus stacking" requirement and explicitly
   supports spatially-binned extended-source stacking, complementary to (1)/(2)
   rather than competing with them.
4. **`WenkeRen/spxquery`** - review its background-estimation code (annulus vs.
   window) even though its target use case is point-source time-domain
   photometry; the dual-background implementation is directly reusable, and
   it is the most production-grade codebase in this batch (PyPI + docs).
5. **`fkiwy/spexpi`** - lower priority than the above four, but worth a skim
   for its solid-angle pixel-map flux calibration and spectral-oversampling
   reduction logic, which are generic L2-image-handling utilities independent
   of the point-source focus.

Everything else in the table above (SPIRAL, deep-field-selection,
noise-validation, airglow, cubemaking, ssiaat, SpherexZodi, etc.) is worth a
bookmark for background/QA methodology but does not currently look like a
drop-in extraction/stacking engine for nearby-galaxy spectra and does not
warrant a full code review at this time.
