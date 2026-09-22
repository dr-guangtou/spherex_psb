# A SPHEREx Pipeline and Spectral Library for Ultracool Dwarfs (arXiv:2604.22012)

## Bibliographic info

Lead author Jonathan Gagné (Planétarium de Montréal; Université de Montréal), with ~136 co-authors from NASA Goddard, Caltech/IPAC, University of Leicester, UC San Diego, and the Backyard Worlds: Planet 9 citizen-science collaboration. Submitted 2026 April 23 (v1), revised 2026 May 8 (v2); accepted for publication in the Astrophysical Journal. Science goal in one sentence: the authors build a custom point-source photometry/PSF-fitting pipeline (SPIFF) to extract 0.75–5.0 µm SPHEREx spectrophotometry for >6000 ultracool dwarfs (known, photometric-candidate, and newly identified), producing a public spectral library and per-spectral-type templates useful for classification and for flagging peculiar/young/subdwarf objects.

## SPHEREx data used

- Release: **SPHEREx Quick Release 2 (QR2)**.
- Product type: individual **L2 image cutouts** (not full 2048×2048 frames) retrieved as small 20×20-pixel FITS cutouts.
- Access mechanism: the **IPAC SIA2 service** is queried with a 5″ cone search around each target to identify the URLs of individual exposures, and the cutouts are then pulled from **Amazon S3** storage. The official IRSA "spectrophotometry tool" (https://irsa.ipac.caltech.edu/applications/spherex/tool-spectrophotometry) is used as a point of comparison/benchmark rather than as the primary extraction path — the authors built their own tool (SPIFF) instead.
- The compiled library is additionally hosted on the Montreal Open Clusters and Associations database (mocadb.ca) and archived with a versioned DOI on Zenodo (10.5281/zenodo.19051216).
- Sample size: 6003 high-quality spectrophotometric products for 6003 objects total (2050 known ultracool dwarfs, 3008 known photometric candidates, 945 newly identified ultracool dwarfs), each built from many individual per-epoch/per-channel SPHEREx exposures (SPHEREx revisits each sky position multiple times over the survey, producing repeated small-bandwidth photometric samples per object).

## Target selection and sample properties relevant to extraction

All targets are **unresolved point sources** (brown dwarfs/ultracool dwarfs, L0 and later), so this paper is a point-source/moving-source photometry problem, not resolved-galaxy extraction — but the pixel-level and PSF-fitting machinery is directly transferable technique.
- Known UCDs: 2050 objects, spectral type L0+.
- Photometric candidates drawn from SIMBAD brown-dwarf flags, Backyard Worlds: Planet 9, BASS/BASS-Ultracool searches, and custom proper-motion/color cuts across CatWISE, UKIDSS LAS DR11++, UHS DR3, Gaia DR3, and Pan-STARRS1 DR2 (example cuts: CatWISE total proper motion ≥20 mas/yr with W1−W2≥0.5; UHS DR3 proper motion significant at ≥5σ; Gaia DR3 G−GRP≥1.55 with absolute G ≳14.0 mag).
- Brightness cut for high-quality output: objects with WISE W2 ≤14.0 mag give average S/N≈10 per spectral channel; fainter objects show a much higher (18.8%) failure/quality-flag rate.
- Because targets are fast/high-proper-motion point sources, proper motions are propagated to adjust the expected detector position at the epoch of each individual SPHEREx image before extraction — a key difference from static extragalactic targets.

## Spectrum / photometry extraction method

Tool: **SPIFF** ("SPHEREx Photometry and Image Fitting Framework"), open source at https://github.com/jgagneastro/SPIFF.

Step-by-step:
1. **Cutout retrieval** — for each target and epoch, query IPAC SIA2 for exposures within 5″, pull a 20×20-pixel cutout from S3 (rather than downloading full-frame images), with the expected detector position of the source shifted for its proper motion at that epoch.
2. **PSF model** — the pipeline uses the **instrumental SPHEREx PSF provided in the mission calibration files**, which is oversampled relative to detector pixels. SPIFF laterally shifts the oversampled PSF via linear interpolation and then downgrades it to detector resolution using a box-sum, effectively re-sampling the PSF onto the predicted sub-pixel source position for each exposure. Because each detector pixel has its own spectral response that varies with position (even within a fixed nominal spectral channel), the PSF/response is evaluated at the best-fit detector position.
3. **PSF fitting** — flux and position are fit with `scipy.optimize`; the detector position of the PSF is allowed to float during fitting (unlike the standard IRSA tool, which fixes position), which the authors argue improves robustness for fast-moving/poorly-registered sources.
4. **Uncertainty sampling** — the `ultranest` nested-sampling package explores the Bayesian likelihood to give posterior-based flux and position uncertainties; the reported flux is the **median of the ultranest samples** and the reported error is the **median absolute deviation** of those samples.
5. **Three parallel flux "flavors"** are produced per exposure/channel: (a) classical aperture photometry over a grid of 18 aperture radii (1.0–5.0 pixels ≈ 6.56″–30.83″), (b) `scipy`-optimized PSF-fit flux, and (c) `ultranest`-based PSF-fit flux/error — allowing cross-checks and flexibility for different source-density/contamination regimes.
6. **Wavelength assignment** — because SPHEREx uses linear variable filters (LVFs), the "spectral channel" a given pixel samples depends on its exact location on the detector. SPIFF extracts the central wavelength and an approximate bin width from the SPHEREx calibration files evaluated **at the best-fitting PSF detector position**, rather than assuming a fixed nominal channel wavelength.
7. **Combining exposures / binning** — because each SPHEREx revisit of a given sky location samples a slightly different detector position (hence a slightly different central wavelength, with individual bandpasses of ~0.02–0.08 µm), raw SPIFF output is a set of individually wavelength-tagged photometric points (stored in `data_spherex_spectra_spiff`) that are spectrally oversampled in a non-trivial way. A simplified data product (`data_spectra`) is then produced by computing the **error-weighted mean of all measurements falling within each of the 102 nominal SPHEREx spectral channels** (0.75–5.0 µm, R≈λ/Δλ≈50).
8. **Error propagation** — a **linear error-propagation formula** combines per-exposure measurement uncertainties into the per-channel error-weighted mean (exact formula not spelled out in the fetched text, but described as standard linear/Gaussian propagation).

## Background and systematics treatment

- **Local background subtraction**: median flux in a 15-pixel-wide box around the source, after masking bad pixels and known contaminating stars, is subtracted — i.e., a local-sky annulus/box approach rather than a global zodiacal-light model or ZODI extension.
- **Flat field / calibration**: SPIFF applies the mission's **preliminary per-channel response functions** as published in the SPHEREx QR explanatory supplement; the authors explicitly caveat that "refined response functions will eventually be released" and will be incorporated in future SPIFF versions — i.e., current absolute calibration is provisional.
- **No explicit treatment of persistence, dark current, or detector flat-fielding beyond the calibration-file response function** is mentioned in the fetched sections.
- **Quality control** is done by visual inspection, with four documented failure modes affecting known UCDs: contaminating background star (8.6%), false-positive star reddened by interstellar dust (0.3%), ambiguous/low-quality data (0.3%, mostly W2>14 mag), and source confusion between two close sources (2.6%).
- **Validation**: SPIFF spectra of the T2.5 dwarf SIMP J013656.5+093347.3 are directly compared to a **JWST NIRSpec prism spectrum** (GO program 3548). SPIFF recovers a flux 2.2% fainter than JWST (vs. 3.4% brighter for the IRSA tool spectrum of the same source); the median absolute deviation of the residuals is 7.6% for SPIFF vs. JWST and 5.8% for IRSA vs. JWST. Based on this the authors recommend adopting a **conservative absolute-flux-calibration error floor of ≈8%** on any SPIFF measurement, pending a fuller SPHEREx absolute-calibration characterization.

## Stacking or combining multiple objects

Not a stack of independent objects per se, but the paper builds **per-spectral-type composite templates**, which is methodologically similar to a stack:
1. Each individual object spectrum is first scaled to its own median flux (normalization).
2. For each spectral subtype bin, a per-channel **median** of the normalized spectra is computed as an initial template estimate.
3. Each individual spectrum is then optimally rescaled by the factor that minimizes χ² between it and this template.
4. The rescaled spectra are recombined via a **median** (not mean) to form the final template, with the **median absolute deviation per channel** recorded as the template's uncertainty/spread.
5. **Hybrid wavelength stitching**: because SPHEREx S/N degrades toward the blue and low-resolution ground/space spectral standards exist for many subtypes, the templates splice a literature standard (synthetically convolved onto SPHEREx bandpasses) for λ<2.4 µm with the higher-S/N SPHEREx-derived template redward of that; the splice point is set by χ²-minimized scaling of the standard onto the SPHEREx data. For the latest types (T6–Y1), JWST NIRSpec PRISM spectra (programs GO 2302, GTO 1189, GTO 4539) substitute for SPHEREx data entirely because of low native S/N.

No explicit redshift handling is needed (Galactic point sources), and no inverse-variance galaxy-stacking scheme is used — the closest analog is the median/χ²-rescale-and-remedian templating procedure above.

## Validation and quoted uncertainties

- JWST NIRSpec prism cross-check (above): ≈2–3% absolute flux offset, ~6–8% RMS scatter per channel.
- Recommended **8% systematic error floor** on SPIFF absolute flux calibration.
- Average per-channel S/N≈10 for objects with W2≤14 mag.
- Automated spectral typing from SPIFF spectra agrees with literature types to a median absolute deviation of 1.5 subtypes.
- No explicit comparison to 2MASS or WISE broadband photometry beyond selection cuts is described in the fetched text (WISE is used mainly for target selection/brightness cuts, not as an independent flux check).

## Lessons and reusable techniques for extracting spectra of nearby galaxies

- **Pull small cutouts via IRSA's SIA2 service + S3**, not full-frame images — efficient for a large target list and directly reusable for galaxy cutout extraction.
- **Evaluate the wavelength solution/response at the fitted (not nominal) detector position** — because SPHEREx's LVF means wavelength is a strong function of pixel position, any extraction (point-source or extended-aperture) should assign wavelengths per-pixel/per-exposure rather than assuming a fixed channel grid, then resample onto a common grid afterward. This is directly relevant to resolved/semi-resolved galaxy extraction where multiple pixels at different detector positions sample different parts of the LVF simultaneously.
- **Error-weighted mean binning onto the 102-channel grid** is a simple, reusable strategy for combining many irregularly-sampled per-exposure measurements into a standard spectral grid — applicable to stacking or even single-object spectral compilation for galaxies.
- **Local box/annulus background subtraction with bad-pixel masking** is simple and was sufficient here; the paper does not use a ZODI model, suggesting for extragalactic point/compact sources a local background estimate may be adequate, though the target population (high Galactic latitude, faint IR objects) may differ from crowded/bright zodiacal backgrounds relevant to a PSB galaxy study.
- **Adopt a conservative ~8% calibration error floor** as a reusable rule of thumb pending revised SPHEREx calibration products, and treat the "preliminary response functions" caveat as an ongoing calibration risk to track (revised versions are expected).
- **Median-based (not mean-based) template stacking with χ²-rescaling** is a robust way to combine many faint, variable-S/N spectra into representative composites, and could be adapted for stacking post-starburst galaxy spectra across small sample sizes with heterogeneous S/N.

## Caveats the authors state

- Absolute flux calibration relies on **preliminary QR response functions**; results will change as refined mission calibration is released.
- The per-channel binned spectra in the simplified `data_spectra` product are only an **"approximate reconstruction"** of the underlying, spectrally oversampled raw measurements — users needing full fidelity should use the raw `data_spherex_spectra_spiff` table.
- Recommend an **8% conservative systematic error floor** on absolute flux until further calibration characterization.
- ~18.8% of targets near the S/N limit (W2≈14 mag) show quality issues (contamination, blending, low S/N, source confusion) requiring visual vetting; automated pipelines applied blindly at low S/N risk significant failure rates.
- The pipeline currently does not address persistence, stray light, dark current, or flat-fielding beyond the PSF/response calibration files — these are not modeled or discussed as separate systematics in this paper.
