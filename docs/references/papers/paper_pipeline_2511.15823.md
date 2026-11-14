# The SPHEREx Image and Spectrophotometry Processing Pipeline (arXiv:2511.15823)

## Bibliographic info

- **Title:** "The SPHEREx Image and Spectrophotometry Processing Pipeline"
- **Authors (49):** Rachel Akeson, Gregory P. Dubois-Felsmann, Brendan P. Crill, Andreas L. Faisst, Tamim Fatahi, Candice M. Fazar, Tatiana Goldina, Daniel C. Masters, Christina Nelson, Roberta Paladini, Harry I. Teplitz, Gabriela Torrini, Phani Velicheti, Matthew L. N. Ashby, Dan Avner, Yoonsoo P. Bach, James J. Bock, Sean Bruton, Sean A. Bryan, Tzu-Ching Chang, Shuang-Shuang Chen, Asantha Cooray, Ari J. Cukierman, O. Doré, C. Darren Dowell, Spencer Everett, Richard M. Feder, Zhaoyu Huai, Howard Hui, Woong-Seob Jeong, Young-Soo Jo, Phil M. Korngut, Yuna G. Kwon, Bomee Lee, Gary J. Melnick, Giulia Murgia, Chi H. Nguyen, Milad Pourrahmani, Zafar Rustamkulov, Volker Tolls, Teresa Symons, Pao-Yu Wang, Yujin Yang, Michael Zemcov. Corresponding authors are R. Akeson (rla@ipac.caltech.edu) and G. Dubois-Felsmann (gpdf@ipac.caltech.edu).
- **Submission history:** v1 submitted 19 Nov 2025; v2 (current) revised 7 Jul 2026. Accepted by the Astrophysical Journal Supplement Series (ApJS). Comments field: "15 pages, 1 figure, accepted by the Astrophysical Journal Supplement Series." Subject: astro-ph.IM.
- **Pipeline version described:** the text states explicitly "At the time of writing, the pipeline version is 6.4." The paper documents the fixed, top-level architecture of the Level 0–3 pipeline; implementation-level details, module validation, and calibration-product provenance for each data release are deferred to a separate, continuously-updated "SPHEREx Explanatory Supplement" (living document at IRSA, https://irsa.ipac.caltech.edu/data/SPHEREx/docs/overview_qr.html) and to the module source code on GitHub (https://github.com/Caltech-IPAC/spherex-pipelines).
- **Data releases referenced:** QR1 (Quick Release 1, initial public release, July 2025, DOI 10.26131/IRSA629) and QR2 (reprocessing with improved PSF and absolute gain calibrations, produced Aug–Sep 2025, released Oct 2025, DOI 10.26131/IRSA652). The paper explicitly states: "we strongly recommend use of QR2 data for all science applications." Future releases: DR1 (after Year 1 = surveys 1+2) and DR2 (after Year 2 = surveys 1–4), plus the High Reliability Source Catalog (HRSC, planned July 2027).
- **Nature of the paper:** this is principally an *architecture and operations* paper describing the software framework, module organization, data flow, and data-product inventory of the pipeline. It is explicitly not a calibration/performance paper — quantitative accuracy numbers for absolute photometric calibration, sensitivity, color corrections, and PSF size are largely deferred to companion papers (Hui et al. 2026 on spectral response; Korngut et al. 2026 on instrument calibration/testing; Ashby et al. 2026 in prep on on-sky calibration; Huai et al. 2026 on spectral-confusion/error propagation; Yang et al. 2026 in prep on the SPHEREx Reference Catalog) and to the Explanatory Supplement.

## One-paragraph summary

This paper describes the software infrastructure and processing modules that convert SPHEREx's raw telemetry into science-ready calibrated data products. SPHEREx (launched 11 March 2025, science operations begun 1 May 2025) surveys the whole sky in 102 spectral channels from 0.75–5 μm at 6.″15 pixels using six H2RG detectors overlaid with linear variable filters (LVFs), split by a dichroic into short-wavelength (bands 1–3, 0.75–2.44 μm) and long-wavelength (bands 4–6, 2.40–5.01 μm) channels. Data flow through five processing levels: Level 0 (on-board slope/packet processing), Level 1 (engineering-unit FITS images with coarse astrometry), Level 2 (astrometrically and photometrically calibrated "spectral images" in MJy sr⁻¹, split into ordered Level 2a persistence-aware processing and parallelizable Level 2b calibration), Level 3 (Tractor-based forced photometry at reference-catalog positions, producing per-exposure and combined all-sky spectro-photometric catalogs in Parquet format), and Level 4 (science-team-led higher-level products, described in future papers). The Levels 1–3 pipeline is implemented in Python atop the Vera C. Rubin Observatory's open-source "Butler" data-access middleware and "Task"/"PipelineTask" pipeline-construction framework, run on-premises at IPAC's NASA Moderate Data Center for ingest/Level 1/Level 2, and at the Texas Advanced Computing Center (TACC) for the computationally heavier Level 3 forced photometry. The paper documents the module-by-module processing chain (astrometry, non-linearity, persistence, dark/flat/absolute-gain calibration, zodiacal-light modeling, background estimation, PSF-based forced photometry), the resulting public data products (spectral images, calibration files, all-sky data cubes, and the High Reliability Source Catalog) available through IRSA, and closes with a list of known instrumental artifacts and future pipeline development priorities.

## Pipeline overview (stages, from raw detector reads to Level 2/3 products; naming of levels and products)

Section II defines five discrete "Data Levels" (Table 1 of the paper):

| Level | Format | Description |
|---|---|---|
| 0 | Spacecraft packets | Instrument and spacecraft data |
| 1 | FITS | Formatted photocurrent images in engineering units |
| 2 | FITS | Calibrated spectral images |
| 3 | Apache Parquet | Spectro-photometric measurements |
| 4 | FITS and Parquet | Science catalogs and images |

The paper's scope is data ingestion plus Levels 1–3; Level 4 (redshifts, ice column densities, deep mosaics) is Science-Team-operated and will be documented elsewhere. Processing responsibility: algorithm definition/testing for Levels 1–3 is a joint SSDC (SPHEREx Science Data Center, Caltech/IPAC)/Science Team effort; implementation and operations are SSDC's responsibility; Level 0 flight software was built by the Instrument Team. Pre-launch testing used the SPHEREx Sky Simulator (Crill et al. 2025) plus a separate Level 0 simulator from the instrument team.

Processing flow (Sec. II.1): Level 1 runs independently per image. Level 2a (persistence modeling) must run in time order per detector/band. Level 2b (bulk of the compute) has no ordering constraint and produces the "quick release" calibrated spectral images delivered to IRSA. Level 3a performs per-image forced photometry to extract per-object spectra; Level 3b aggregates catalog-oriented outputs into per-object spectra/catalogs. Level 4 consumes both Level 2 images and Level 3 catalogs.

**Framework (Sec. II.2):** the pipeline reuses the Rubin Observatory "Butler" data-access framework — a database (PostgreSQL) + bulk POSIX (with possible future cloud) storage abstraction that manages dataset types, "data coordinates" (pointing IDs, detector/band numbers, HEALPixel tile IDs), serialization, and calibration/image associations. Pipeline algorithms are implemented as subclasses of a uniform `Task` interface; major pipeline segments (Level 1, Level 2a, Level 2b, Level 3a, Level 3b) are `PipelineTask` subclasses, enabling directed-acyclic-graph (DAG) execution planning and provenance tracking. This is the same middleware stack used by the Vera C. Rubin Observatory/LSST, adapted with a SPHEREx-specific data model.

## Detector and readout processing (sample-up-the-ramp, nonlinearity, saturation, persistence, dark, reference pixels, cosmic rays, glitches)

**On-board (Level 0):** six readout boards (one per detector/band) read out photocurrents, compute pixel-level slopes from up-the-ramp sampling, measure preamplifier drifts and detector offsets, **detect glitches**, and compress/packetize data via the CCSDS Space Packet Protocol (1010-byte packets), then wrap them in Sync-Marked Transfer Frames (1024 bytes) for downlink over a 600 Mbps Ka-band link (typically 1–5 downlinks/day) through NASA's Near Space Network (NSN)/DAPHNE+ system.

**Level 1 (7 modules):**
1. *GDS Image Association* — merges Ka-band detector data with S-band header/telemetry values.
2. *Estimate Coarse Astrometry* — initial pointing from survey plan + geometric inter-detector offsets, accuracy **2′–10′**.
3. *Validate Sample-up-the-Ramp (SUR)* — extracts an **8×34 pixel** subsection where the full SUR is recorded, to monitor noise performance and temporal stability.
4. *Convert to Engineering Units* — ADU → electrons/second using per-amplifier gains from the Instrument Team (the "Electronic Gain Factors" product: a YAML file with 32 gain values per detector).
5. *Correct Preamplifier* — corrects amplifier-chain drifts using **reference pixels** and interleaved **phantom pixels** (role described in Nguyen et al. 2025, ApJS 276, 43).
6. *Create Level 1 Image Data Files* — assembles standard-format FITS with engineering-unit data + header metadata.
7. *Data Quality Assessment for Level 1* — basic integrity checks/image statistics, recorded as header keywords.

**Level 2a (3 modules, must run in time order per band because of persistence):**
- *Correct Non-linearity* — corrects H2RG pixel gain decline with accumulated charge (Zengilowski et al. 2020); applied to all pixels except reference/phantom pixels; uses the "Non-Linearity Parameters" calibration file (per-band FITS, 83 MB).
- *Create Variance Map* — per-pixel variance from the Level 1 flux value, following the method of Robberto (2007, WFC3 ISR); this variance becomes the `VARIANCE` extension of the Level 2 spectral image. Uses the "Read Noise Parameters" calibration product (per-pixel electron noise, per-band FITS, 50 MB).
- *Update Persistence* — applies a parameterized analytic model (Fazar et al. 2025, JATIS 11, 011208; Fazar et al. 2026 in prep) estimating residual persistent charge per pixel from cumulative flux exposure history, and flags pixels significantly affected.

After Level 2a, reference and phantom pixels are stripped from the FITS files (they carry no sky photons and are not needed further), and the *Query Reference Catalog* module runs, pulling the relevant subset of the SPHEREx Reference Catalog (photometric/astrometric calibrators + science-theme sources for forced photometry) for the sky area covered, with proper-motion evolution to the observation epoch; this query is batched over an entire target-group footprint for efficiency rather than per image.

**Level 2b (9 modules)** — see the Flags/Backgrounds/Photometric-calibration sections below for detail on individual steps. Notably: **saturation** is not treated as an explicit named correction module in this paper (it appears only as an astrometric-calibrator selection criterion — "not predicted to be saturated in any SPHEREx band" — with detailed saturation handling presumably in the Explanatory Supplement/instrument papers, not reproduced here).

**Cosmic rays / transients / glitches:** handled at two stages — onboard glitch detection (Level 0) and, on the ground, the *Detect Outlier Pixels* module (Level 2b), which applies sigma-clipping to median-filtered images to flag transients missed onboard; results are folded into the flag extension. A per-image "transient count" is a key data-quality metric: images with **>435,000 flagged transient pixels** fail Level 2 data-quality assessment and trigger a re-observation request (calibrated to flag roughly **1% of images**). "Improved Transient Flagging" (to better catch Earth-orbiting satellites and extended cosmic-ray tracks) is listed explicitly as future work (Sec. VIII), implying the current transient mask is imperfect for these cases.

**Dark current:** derived jointly with the flat field (see Photometric calibration section) as the intercept of a linear fit; ~1000 images needed for a stable, repeatable estimate.

## Astrometric calibration (method, accuracy, distortion, WCS conventions)

Two-stage astrometry:
1. **Coarse astrometry (Level 1):** based on spacecraft pointing and known geometric detector offsets; accuracy **2′–10′**.
2. **Fine astrometry (Level 2b, "Estimate Fine Astrometry" module):** computes per-image translation/rotation. Astrometric calibrator stars must have a good Gaia astrometric solution, SNR > 10, not be predicted saturated in any SPHEREx band, and have no neighbor within 2 SPHEREx pixels brighter than 10% of the calibrator's own flux (an isolation cut relevant to PSF/blending work). Two-stage solve: an initial solution from **Astrometry.net** (Lang et al. 2010), refined by **SCAMP** (Bertin 2006) run iteratively (similar in approach to the WISE astrometry pipeline). A header keyword **`FINAST`** records astrometric performance, with `FINAST = 0` denoting images with rms < 1″. Quoted performance: **median astrometric alignment precision of 0.1″–0.4″** for images with `FINAST = 0`. `FINAST = 0` is also a hard requirement for a Level 2 image to be released to IRSA (see Flags section).

**Distortion:** the paper confirms the existence of a "per-detector distortion map calibration FITS images" product, used as an input to the Level 3 forced-photometry pipeline (alongside Level 2 images and `srccat` catalogs), but does not describe the distortion-map derivation method or give a quantitative distortion magnitude in this paper. Future work (Sec. VIII) explicitly targets improving fine astrometry by computing a "fixed distortion" from many images plus per-image differential corrections, and by recovering images with failed astrometric solutions using the solution from a neighboring image in the same slew/observation (small-slew offsets are 17′ within a target group).

**WCS conventions:** standard per-image WCS header keywords from the fine-astrometry solve; a distinct spectral WCS convention is used for wavelength (see next section) — the `WCS-WAVE` extension follows the FITS standard's `WAVE-TAB` specification.

## Spectral calibration (LVF wavelength solution, bandpass per pixel, WAVE-TAB, accuracy)

Because each SPHEREx pixel is imaged behind a fixed patch of the linear variable filter (LVF), each pixel has its own unique center wavelength and bandpass, not a shared per-band value. The "Spectral WCS" calibration product formalizes this:
- **`CWAVE`** and **`CBAND`** extensions: per-pixel central wavelength and bandwidth, based on **laboratory measurements by the instrument team** (Hui et al. 2026, "Spectral response of SPHEREx", arXiv:2602.09139). The central wavelength for a pixel is defined as the wavelength at which the **cumulative transmission curve reaches 50% of its total area** (i.e., the median of the transmission curve). The bandwidth is computed as **central wavelength divided by the detector's measured spectral resolution** (R). The paper states explicitly: "should be used for science investigations" — i.e., `CWAVE`/`CBAND` are the authoritative per-pixel wavelength solution.
- **`WCS-WAVE`** extension: a compact **piecewise-bilinear approximation** to the same wavelength solution, provided in the FITS-standard **WAVE-TAB** WCS convention, explicitly intended "for visualization" rather than for precision science use.
- The Spectral WCS calibration product is delivered as one FITS file per band, 33 MB.
- No explicit numerical wavelength-accuracy figure (e.g., a fractional or absolute Δλ uncertainty) is quoted in this paper; that level of detail is deferred to Hui et al. (2026).
- No explicit spectral-resolving-power (R) value is stated numerically in this paper (only that bandwidth = λ_center / R using the "detector's measured spectral resolution"); R must be obtained from Hui et al. (2026) or the Explanatory Supplement.

## Flat fielding and photometric calibration (standard stars, absolute calibration, surface brightness units MJy/sr, gain, accuracy, color corrections)

Photometric calibration is built from three calibration modules run at cadences matched to expected variability (Sec. IV.4):

1. **Estimate Dark Current and Flat Field:** for each pixel, fits the slope of pixel value (electrons/s) against a reference flux level — the median brightness in that pixel's spectral channel across many images — using **510 spectral channels per band** (chosen so the background flux is expected not to vary strongly across the spectral dimension within a channel). An additional tilt term per spectral channel corrects for **solar elongation** (i.e., the enhanced zodiacal-light brightness on one side of the band). The **slope** of the per-pixel relation over many images gives the relative pixel response (**flat field**); the **y-intercept** gives the **dark current** (electrons/s). ~1000 images are needed for a consistent, repeatable dark/flat estimate.
2. **Estimate Absolute Gain Matrix:** derives a 1D gain function (gain vs. spectral position on each detector) from measured-vs-expected flux of a set of pre-identified **primary calibrator stars** (well-studied community standards, listed in the Explanatory Supplement). Individual spectral measurements of these standards are **convolved with the known bandpass and color-corrected**; many thousands of such measurements are combined with statistical weights to build the gain function. This gain function is then **multiplied by the inverse of the derived flat-field response** to produce the final **Absolute Gain Matrix** (delivered as one FITS file per band, 17 MB).
3. **Apply Dark, Flat Field and Photometric Calibration (Level 2b module):** applies dark subtraction, flat-fielding, and the absolute gain calibration to the flux; **after this step, pixel values are in units of MJy sr⁻¹** (i.e., surface brightness, not integrated flux — appropriate given SPHEREx's extended, spatially-undersampled PSF and diffuse-background-dominated regime). This unit choice is central for any user wanting to do their own aperture photometry directly on Level 2 images.

**No explicit numerical absolute-photometric-calibration accuracy (e.g., a percent-level uncertainty floor) is stated anywhere in this paper.** Likewise, no quantitative statement of photometric repeatability (survey-to-survey flux stability) or sensitivity limits (e.g., 5σ point-source depth) is given; these are explicitly deferred to companion papers/Explanatory Supplement, though color corrections are mentioned qualitatively as part of the calibrator-star flux modeling in the gain-matrix step.

The **Solid Angle Pixel Map** (per-pixel solid angle in arcsec², one FITS file per band, 16 MB) is a distinct calibration product used specifically by the Level 3 *Perform Forced Photometry* module to convert model-fit flux density (surface brightness) into an integrated flux (μJy) for point/compact sources — i.e., the conversion from MJy/sr surface-brightness images back to a per-source flux depends on this pixel-solid-angle calibration, not a single fixed pixel scale, because pixel solid angle varies across the detector footprint.

## PSF (how modeled, zones, oversampling, wavelength dependence, PSF size numbers)

**Measure Exposure-Averaged Point Spread Function** module (calibration, Sec. IV.4):
- PSF is measured on an **11×11 grid = 121 zones** per band, to track spatial and wavelength-dependent variation of the PSF across a given band/detector (since wavelength varies with position under the LVF, spatial and spectral PSF variation are coupled).
- PSFs constructed by **stacking cutouts of individual stars** within each zone, drawn from **several hundred exposures**, yielding **>1000 stars per zone per band**.
- Stacking is done at **10× oversampled** pixel scale, because the PSF is "significantly undersampled at SPHEREx resolution" (native pixel = 6.″15).
- The resulting super-resolution stack is **iteratively deconvolved by the pixel-grid function** (accounting for flux spreading over the super-resolved pixel grid) as a final step.
- Delivered calibration product: one FITS file per band, dimensions **101×101×121** (i.e., a 101×101-pixel oversampled PSF stamp for each of the 121 zones), 5 MB per file.
- The exposure-averaged PSF is also embedded as a `PSF` extension directly in each Level 2 spectral image FITS file.
- **No PSF FWHM/size number in arcsec is quoted anywhere in this paper** — only the pixel scale (6.″15) and the qualitative statement that the PSF is significantly undersampled at that scale. Users needing quantitative PSF FWHM/ellipticity numbers must consult the Explanatory Supplement or instrument papers (e.g., Korngut et al. 2026).
- Future work (Sec. VIII) flags PSF measurement as an active improvement area: possible deconvolution by a kernel incorporating spacecraft **settling jitter** (estimated σ_jitter < 0.″1) not currently modeled, and exploration of **machine-learning PSF modeling** (citing Herbel et al. 2018) as an alternative to the current stacking approach.
- Per-image PSF size is tracked as a data-quality metric: the **Image Data Quality Report (IDQR)**, generated at the end of Level 2, records per-image pointing and PSF size information (used for trending/QA), though no numeric values are given in this paper.

## Backgrounds: zodiacal light model, stray light, Earthshine, sky background estimation, source masking; what IS and IS NOT subtracted in the delivered images

**Zodiacal light model ("Get Zodi Model" module, Level 2b):** provides an estimate of diffuse zodiacal light as a function of the image's spatial location, using an **empirical, time-variant model** based on Kelsall et al. (1998, the COBE/DIRBE interplanetary-dust-cloud model), **updated with spectral measurements from Tsumura et al. (2013, AKARI low-resolution zodiacal spectrum)**; a more detailed description is given in the SPHEREx Sky Simulator paper (Crill et al. 2025). Critically, the paper states explicitly: **"the zodiacal model is an image extension in the Level 2 spectral image (Sec. V) and is not subtracted from the image but is provided for later operations, such as mosaicing."** This is the single most operationally important statement in the paper for a user extracting galaxy fluxes: **delivered Level 2 (`IMAGE`) data still contain the zodiacal light signal**; the `ZODI` extension is only a model prediction, packaged alongside the data for the user (or a later pipeline stage) to subtract as needed.

**Source masking:** the *Create Source Mask* module flags pixels predicted to be impacted by flux from known sources, using the source list from the *Query Reference Catalog* module; this flag is written into the same multi-bit flag extension populated by *Apply Bad Pixel Mask*.

**Background estimation for photometry (Level 3a, "Estimate Diffuse Background" module):** this is a *separate*, re-derived background estimate used specifically to support forced photometry (distinct from, and in addition to, the `ZODI` model extension packaged with Level 2 images). Two modes:
- **Global mode** (used when >90% of image subregions are usable): starts with a **spectral fit to the zodiacal light contribution** in the source-masked image; the *residual* after that fit is modeled with **`Background2D`** from Photutils (Bradley et al. 2024); the combined spectral-fit + Background2D residual model is the final global background estimate. Subregions are rejected as unusable if **>75% of their pixels** are flagged as containing non-negligible source flux from SPHEREx Reference Catalog sources.
- **Local mode** (triggered when the global estimate fails due to unusably high source density, typically in the Galactic plane at **|b| ≲ 20°**): `Background2D` applied to a small **15×15 pixel** region around each source cutout.
- This locally/globally estimated background is then subtracted from the image *before* the forced-photometry flux fit (in the *Perform Forced Photometry* module, "this module first removes the background computed in the previous module").

**Stray light / ghosts / Earthshine:** the paper does **not** use the term "stray light" or "Earthshine" explicitly. The closest analogs appear only in the Future Development section (Sec. VIII, "Optical and Electrical Masking") as **known but not-yet-fully-corrected artifacts**: frame-edge ghosts (light scattering off the optical filter's mechanical structure), electrical crosstalk (in the detector substrate/multiplexer), optical ghosts from reflections at the dichroic band-defining beam splitter, other low-level optical ghosts from bright sources *outside* the field of view, and "**glow arising from large-angle response to the Moon**" (the nearest analog to an Earthshine-like contaminant). The paper states some of these were characterized pre-flight in the lab and others were discovered in flight operations, and that masking improvements for all of them are still in progress — i.e., **these are present in current data products at some level and are not fully masked/corrected as of pipeline v6.4 (QR2)**.

**South Atlantic Anomaly (SAA):** Level 2 images acquired while the spacecraft is inside the SAA fail data-quality assessment and are not released to IRSA (a hard gating criterion, alongside transient count and `FINAST`).

**Summary of what IS vs. IS NOT subtracted in the delivered Level 2 spectral image:**
- IS applied/subtracted: dark current, flat field, absolute gain (photometric calibration to MJy/sr), non-linearity correction, persistence-model flagging (not flux subtraction — see Flags), reference/phantom-pixel drift correction.
- IS NOT subtracted: zodiacal light (only modeled and provided as a separate `ZODI` extension), source flux from neighboring/blended objects (only flagged via source mask), any of the not-yet-corrected optical/electrical artifacts listed above (ghosts, crosstalk, Moon glow).
- The **only place a background (including a zodi-informed component) is actually subtracted from pixel values** in the documented pipeline is inside Level 3a's *Estimate Diffuse Background* → *Perform Forced Photometry* chain, and that subtraction happens transiently within the photometry fit, not as a persistent, delivered background-subtracted image product. Users who want a zodi-subtracted, science-ready image directly must apply the `ZODI` extension (or their own background model) themselves to the Level 2 `IMAGE` data.

## Flags and variance (full bitmask definitions if given; how variance is computed)

**Flags:** the Level 2 spectral image FITS file has a dedicated `FLAGS` image extension, initially populated by the *Apply Bad Pixel Mask* module, which "generate[s] a per-pixel map with a multi-bit flag tracking on-board information (e.g., transients, nonfunctional pixels, persistence and outlier pixels)." The paper explicitly states: **"The complete list of flags and their assigned bit mask is given in section 3.2.4 of the [SPHEREx] Explanatory Supplement"** — i.e., **the full bitmask table is not reproduced in this arXiv paper** and must be obtained from the living Explanatory Supplement document at IRSA. Additional flag bits are added downstream by other modules writing into the same `FLAGS` extension: the *Create Source Mask* module (source-contamination flag) and the *Detect Outlier Pixels* module (transient flag). Two specific flag names are given explicitly in this paper:
- **`DICHROIC`** — corresponds to the "Dichroic Impacted Pixels" calibration product: pixels where flux attenuation due to the dichroic filter is **≥50%**. Delivered per band as a 4 MB FITS bitmask.
- **`NONFUNC`** — corresponds to the "Nonfunctional Pixels" calibration product: permanently non-functioning pixels, value **0 = unaffected, 1 = impacted**. Delivered per band as a 34 MB FITS file.

A separate header keyword, **`FINAST`**, flags per-image astrometric quality (0 = rms < 1″; used as a release gate).

**Variance:** computed by the *Create Variance Map* module (Level 2a) on a per-pixel basis from the Level 1 flux value, following the method described by Robberto (2007, WFC3 ISR 12) — i.e., an up-the-ramp/read-noise-based variance estimator adapted from HST WFC3-IR practice. The resulting per-pixel variance is delivered as the `VARIANCE` extension of the Level 2 spectral image. Read-noise inputs come from the "Read Noise Parameters" calibration product (per-pixel electron values, one FITS file per band, 50 MB). No explicit variance formula (equation) is reproduced in this paper; readers must consult Robberto (2007) and/or the Explanatory Supplement for the exact expression.

**Level 3 error handling:** the *Perform Forced Photometry* module reports an **"improved error estimation procedure that accounts for covariance between blended sources"** (developed and detailed in Huai et al. 2026, "Simulating Spectral Confusion in SPHEREx Photometry and Redshifts") — i.e., flux uncertainties on Level 3 catalog entries are not simple independent per-source errors but explicitly account for source blending/confusion covariance. Additionally, per-source output includes an aggregation of pixel flags from the central source region plus an unspecified "fit metric" (goodness-of-fit indicator), with further detail deferred to the Explanatory Supplement.

## Spectrophotometry / source extraction (how the pipeline measures fluxes/spectra of sources: forced photometry, PSF fitting, aperture, catalog inputs, treatment of extended sources, deblending, per-exposure vs combined spectra, output catalog/spectrum products)

SPHEREx's Level 3 extraction is **exclusively forced, PSF-based photometry at pre-defined reference positions** — there is no free/blind source detection at Level 3 in the delivered pipeline (blind detection is offered separately as the "Source Discovery" archival tool, see below).

**Scatter-gather organization (Level 3a/3b):** Level 3a runs per Level-6 HEALPixel tile (`NSIDE=64`, ≈1 sq. deg.) covered by an image, performing background estimation (see above) and forced photometry; Level 3b, run after all Level 3a processing for a given sky region completes, aggregates results per HEALPixel tile into catalog-format outputs.

**Perform Forced Photometry module (Level 3a):**
- Extracts flux based on **prior knowledge of source position and shape from the SPHEREx Reference Catalog** (Yang et al. 2026, in prep), i.e., positions/morphologies are not measured by SPHEREx itself but supplied externally (this catalog presumably draws on deeper external surveys for morphology/position priors — the paper does not detail its construction beyond noting it is "assembled periodically by the Science Team" and includes both calibrator stars and science-theme target sources).
- The extraction algorithm is **based on the community package Tractor** (Lang, Hogg & Mykytyn 2016; methodological precedent also cited to Weaver et al. 2022's COSMOS2020 forced-photometry approach) — a maximum-likelihood image-modeling code. It works by finding the maximum-likelihood solution for source flux(es) by comparing the observed image with a parametric scene model built from the (measured) PSF and the known/fixed source positions.
- Background (from *Estimate Diffuse Background*, above) is removed first.
- The fit operates on a **15×15 pixel cutout**, generating a model containing **all sources within that region simultaneously** — this is the pipeline's built-in **deblending** mechanism: nearby/overlapping sources within the 15×15-pixel box are modeled jointly rather than measured independently, with the improved Huai et al. (2026) error treatment explicitly designed to capture blending covariance in the resulting flux errors.
- Fit flux is converted from image surface brightness to μJy using the **Solid Angle Pixel Map** calibration product (per-pixel solid angle).
- Output per measurement includes: flux, error (blend-covariance-aware), aggregated data-quality flags from the central source-region pixels, and a fit-quality metric.
- **Extended-source treatment:** the paper does not describe a dedicated extended/resolved-galaxy photometry mode distinct from the point-source forced-photometry described above. The 15×15-pixel fit box (≈92″×92″ at 6.″15/pixel) sets a natural spatial scale for what can be captured in a single forced-photometry measurement; sources with structure on larger angular scales, or genuinely extended low-surface-brightness emission, are implicitly handled only via whatever shape prior the SPHEREx Reference Catalog supplies to Tractor (not detailed here), and via the completely separate all-sky data-cube/mosaic products (below), not via Level 3 catalog photometry.

**Per-exposure vs. combined spectra (Level 3b):**
- **Create Primary All-sky Catalog:** merges per-exposure flux measurements from all Level 2 images into a single unified Parquet catalog. For each source-image pairing that was photometered, this catalog records measured flux, error, wavelength, and observation time (MJD) — i.e., this is the **per-exposure, per-wavelength-channel spectrophotometric record** ("All-Sky Spectral Catalog"). This product feeds both Level 4 science pipelines and the HRSC.
- **Create Secondary All-sky Catalog and Estimate Variability:** derives, from the primary catalog, a per-source spectrum **averaged over all observations from all surveys to date and interpolated onto a fixed wavelength grid** — i.e., this is the **combined/stacked spectrum product**. It requires ≥2 surveys of input data for valid wavelength gridding. It also flags variable sources using two methods depending on S/N: bright sources (S/N > 100) are compared to prior SPHEREx measurements **in their native spectral channels**; faint sources are first **collapsed to ~10 reference bands** before the same comparison, in both cases against a specified sigma noise-threshold.
- **Create High Reliability Source Catalog (HRSC):** selects the subset of the all-sky catalog meeting SNR and survey-to-survey consistency criteria (SNR > 10 in ≥5 of the 102 channels, plus survey-to-survey consistency after ~1.5 years of data / Nyquist sampling); includes both primary (per-exposure) and secondary (combined) measurement formats for each selected source.

**Archival extraction tools for user-defined sources (Sec. VI, IRSA-hosted):**
- **Spectrophotometry tool** (currently available): runs the *same* Tractor-based PSF-photometry method as the Level 3 pipeline, but at **user-supplied positions** instead of SPHEREx Reference Catalog positions — directly relevant for extracting a spectrum at an arbitrary galaxy position/nucleus not (yet) in the reference catalog.
- **Spectral Image Cutout tool** (currently available): returns native-pixel-sampling image cutouts by spatial area/band/time — the natural starting point for custom aperture or resolved photometry on Level 2 images.
- **Source Discovery** (under development, planned as a Python notebook): blind detection of significant signal in a user-supplied region, without position priors.
- **Custom Mosaic** (under development): builds single-wavelength images from spectral images with user-supplied criteria, including synthetic bands (i.e., user-defined wavelength-averaged bandpasses).
- **Spectral Cube Cutout** (under development): extracts subsets of the (future) All-sky Spectral Cube as HEALPix-projected FITS cubes, with optional interpolation to synthetic bands.

## Quantified performance and systematics (all numbers on photometric accuracy, repeatability, wavelength accuracy, sensitivity, known residual systematics)

This paper is sparse on quantitative performance/systematics numbers relative to what a calibration paper would provide; the following is the exhaustive list of numeric performance figures actually stated:

- Spatial resolution / pixel scale: **6.″15**.
- Coarse (Level 1) astrometric accuracy: **2′–10′**.
- Fine (Level 2) astrometric precision: **median 0.1″–0.4″** for images with `FINAST = 0` (rms < 1″ threshold for that flag).
- Dichroic-impacted-pixel threshold: flux attenuation **≥50%**.
- Transient-count release/re-observation threshold: **>435,000 flagged pixels**, calibrated to flag **~1%** of images for re-observation.
- Level 2 release requires passing **≥50%** of automated module data-quality tests, being outside the SAA, transient count below threshold, and `FINAST = 0`.
- PSF calibration: **121 zones** (11×11 grid) per band, **>1000 stars/zone**, **several hundred** exposures, **10×** oversampling, PSF product array size **101×101×121** per band.
- Flat field/dark current calibration: **510 spectral channels/band** used in the fit, **~1000 images** needed for a stable/repeatable solution.
- Astrometric-calibrator isolation cut: no neighbor within **2 SPHEREx pixels** brighter than **10%** of the calibrator's flux; calibrator SNR > 10.
- HRSC selection: SNR > 10 in ≥5 of 102 channels, plus survey-to-survey consistency, requiring ≥1.5 years of data.
- Variability test S/N threshold for "bright" regime: **S/N > 100** (native channels); faint-source regime uses **~10 reference bands**.
- Forced-photometry cutout size: **15×15 pixels** (both for background local-mode estimation and for the Tractor fit box).
- Spacecraft settling jitter (currently unmodeled in PSF): estimated **σ_jitter < 0.″1**.
- Data volumes: 72 MB per spectral-image FITS file; 190 TB total for all spectral images; 95 TB for all-sky data cubes; 120 TB for the HRSC.

**Not quantified in this paper** (explicitly deferred elsewhere): absolute photometric calibration accuracy/uncertainty (%), photometric repeatability/survey-to-survey flux stability, point-source sensitivity/5σ depths, wavelength-solution accuracy (Δλ), spectral resolving power R (only the definitional relation bandwidth = λ_center/R is given, not R's value), PSF FWHM/size in arcsec, quantitative distortion-map amplitude, and color-correction magnitudes. A user needing these specific numbers should consult Hui et al. (2026, spectral response), Korngut et al. (2026, instrument calibration/testing/performance), Ashby et al. (2026, in prep, on-sky calibration), Huai et al. (2026, spectral confusion/error covariance), and the Explanatory Supplement.

## Known limitations and planned improvements stated by the authors

Section VIII lists explicit, author-acknowledged limitations and active/planned work:

1. **Fine astrometry:** current per-image solve may be improved by separating a fixed (many-image) distortion solution from per-image differential corrections; also investigating recovery of images with failed astrometric solutions by borrowing solutions from neighboring images (offset by a small 17′ slew, or other images in the same observation).
2. **PSF:** current per-exposure PSF measurement may be improved by deconvolving a kernel that incorporates spacecraft settling jitter (σ_jitter < 0.″1, not currently modeled) or by adopting machine-learning-based PSF measurement (citing Herbel et al. 2018).
3. **Inter-/intra-pixel response:** H2RG detectors are known to have intra-pixel sensitivity variations (citing Le Graët et al. 2022, an Euclid NISP H2RG interpixel-capacitance study); the SPHEREx pipeline does not yet correct for this, though a method (comparing measured per-pixel flux to predicted sub-pixel-response sums, averaged over thousands of pixels) is described as a planned approach.
4. **Transient flagging:** current flagging is inadequate for Earth-orbiting satellites and extended cosmic-ray tracks; improvement is planned.
5. **Optical and electrical masking:** explicitly unresolved/only partially masked artifacts include frame-edge ghosts (filter-structure scattering), electrical crosstalk (detector substrate/multiplexer), optical ghosts from dichroic beam-splitter reflections, low-level ghosts from bright out-of-field sources, and Moon-glow (large-angle response to the Moon). Some were characterized pre-flight; others discovered in-flight.
6. **Level 3 Data Quality Assessment:** no automated Level 3 (catalog-level) QA module exists yet in the described pipeline; building one is listed as future work.
7. Data products explicitly not yet delivered as of this paper: the **All-sky Data Cubes** (Year 1/Year 2 releases, Nov 2026/Nov 2027) and the **HRSC** (July 2027) are future deliveries, as are several archival tools (Source Discovery, Custom Mosaic, Spectral Cube Cutout).

## Implications for extracting spectra of nearby galaxies (synthesis)

**What the pipeline gives us directly, out of the box:**
- Astrometrically (0.1″–0.4″ typical precision) and photometrically calibrated Level 2 "spectral images" in physically meaningful surface-brightness units (MJy sr⁻¹), one FITS file per band per exposure, with `IMAGE`, `FLAGS`, `VARIANCE`, `ZODI`, `PSF`, and `WCS-WAVE` extensions bundled together — this is the natural substrate for any custom resolved/semi-resolved photometry we build ourselves, since it retains full pixel-level information (not just catalog fluxes) and even ships a per-image PSF stamp and zodi model alongside the data.
- A per-pixel wavelength solution (`CWAVE`/`CBAND`) that must be used instead of any nominal "band center" — this is essential because a given galaxy observed in different exposures, or different parts of an extended galaxy in the same exposure, will fall on different detector pixels and therefore sample genuinely different (though nearby) wavelengths under the LVF. Any custom spectral extraction (stacking images by true per-pixel wavelength, not by band ID) must replicate the logic used in `CWAVE`/`CBAND`.
- A ready-made Tractor-based forced-photometry pathway (both the Level 3 pipeline itself, for sources already in the SPHEREx Reference Catalog, and the IRSA "Spectrophotometry" archival tool for arbitrary user-supplied positions) that already handles PSF-model construction, background subtraction, and blend-covariance-aware error estimation — a strong starting point for unresolved or marginally-resolved PSB galaxy nuclei, provided our targets can be treated as point/compact sources at the 6.″15 pixel scale and 15×15-pixel (~92″) fit box.
- A `VARIANCE` extension and (for Level 3) blend-aware flux errors, sparing us from re-deriving basic noise propagation from scratch, though the exact variance formula (Robberto 2007-based) and full flag bitmask are only in the Explanatory Supplement, not this paper — we will need to pull that document (and/or the GitHub module code) before trusting variance/flag semantics in detail.

**What we must do ourselves:**
- **Zodiacal light subtraction is not done for us.** The single most important operational fact from this paper: Level 2 `IMAGE` data are *not* zodi-subtracted; the `ZODI` extension is only a model prediction "provided for later operations, such as mosaicing." For nearby, typically low-surface-brightness post-starburst galaxies (especially their extended/resolved outskirts), we must explicitly subtract either the delivered `ZODI` model or our own independently-fit local background before doing any surface-photometry or resolved-spectrum extraction — using the raw `IMAGE` values as if they were sky-subtracted will bias fluxes, especially at longer wavelengths / near the ecliptic where zodi surface brightness is high and spatially/temporally variable.
- **The pipeline's own background-subtraction (Level 3a) is a photometry-fit-internal step, not a delivered product** — it is a spectral-zodi-fit + Photutils `Background2D` combination (global mode) or 15×15-pixel local `Background2D` (near the Galactic plane), used transiently inside forced photometry and not exposed as a standalone "background-subtracted image." If we want a science-ready background-subtracted mosaic/cutout for extended sources, we likely need to reimplement something similar (or adapt the same Photutils `Background2D` strategy) on the Level 2 images ourselves, being careful to mask our own galaxy properly (the pipeline's source mask is built from the SPHEREx Reference Catalog, which may not have detailed shape information for a nearby extended PSB galaxy).
- **No dedicated extended-source/resolved-galaxy photometry mode is described.** Level 3 forced photometry is fundamentally a point/compact-source (PSF-fit) method operating in fixed 15×15-pixel boxes; for resolved galaxies larger than this box (~92″, i.e. larger than ~15 kpc at ~30 Mpc, so relevant for many nearby PSBs), we cannot rely on the standard Level 3 catalog product and must build our own resolved extraction (e.g., aperture photometry, isophote fitting, or PSF-matched multi-band SED mapping) directly on Level 2 images (or the future All-sky Data Cubes / Custom Mosaic tool), explicitly handling the per-pixel wavelength solution and zodi/background subtraction ourselves.
- **Deblending is only handled within a 15×15-pixel box.** Any close companions, foreground stars, or internal galaxy substructure (e.g., a bright nuclear starburst region embedded in more diffuse host light) will only be jointly modeled by Tractor if all components fall within that box; more extended/complex blending situations (e.g., a merger pair or overlapping galaxies at larger separations) require custom modeling.
- **We need to pull the full flag bitmask (Explanatory Supplement Sec. 3.2.4)** before writing any QA/masking code — this paper explicitly does not reproduce the flag definitions beyond naming `DICHROIC`, `NONFUNC`, and (implicitly) transient/persistence/outlier flag categories generically. We should treat this paper's flag description as incomplete and go get the Supplement.
- **Known-uncorrected instrumental artifacts (ghosts, crosstalk, Moon glow) are a live systematic risk** for low-surface-brightness galaxy work, since these produce spatially structured, non-Poisson residual signal that will not be caught by simple sigma-clipping/transient flags, and are explicitly still under active masking development as of pipeline v6.4/QR2. For faint, extended PSB galaxy light (especially tidal features, low surface-brightness halos), we should budget for visually/statistically screening affected regions ourselves rather than trusting the delivered flags to catch everything.
- **QR2 (not QR1) is the recommended baseline**, and future DR1 (~Nov 2026)/DR2 (~Nov 2027) reprocessings will use improved calibrations/algorithms — our analysis pipeline should be built to be easily re-run against updated data releases rather than hard-coded to one calibration epoch, given the mission's own stated cadence of substantial pipeline revisions (QR1→QR2 already reflected "considerable improvements in the PSF and the absolute gain").
- **Combined/secondary-catalog spectra require ≥2 surveys** of data before the fixed-wavelength-grid interpolation is valid; single-survey (single-epoch) coverage, as in the first year of the mission, will not yet support the "stacked spectrum" product for point sources and even less so for any custom resolved stacking we do — early-mission analyses of nearby PSBs should expect single-epoch, non-Nyquist-sampled spectral coverage and design accordingly (fewer independent wavelength samples per sky position than the eventual multi-survey depth).
- **No sensitivity/depth numbers are given here**, so any exposure-time/feasibility planning for detecting resolved PSB galaxy features (e.g., faint tidal tails, extended post-starburst stellar populations) needs numbers pulled from Korngut et al. (2026) or the Explanatory Supplement, not from this architecture paper.

## Glossary of product names, acronyms and keywords introduced

- **SPHEREx** — Spectro-Photometer for the History of the Universe, Epoch of Reionization, and Ices Explorer (NASA MIDEX mission).
- **SSDC** — SPHEREx Science Data Center, Caltech/IPAC.
- **SPS** — Survey Planning Software.
- **GDS** — Ground Data System (at JPL).
- **NSN** — NASA Near Space Network.
- **DAPHNE+** — Data Acquisition Processing and Handling Network Environment (NSN high-rate Ka-band processing system, hosted on AWS/NASA Mission Cloud Platform, MCP).
- **UMGS** — User Mission Ground System (cloud bucket).
- **LDF** — List of Delivered Files (manifest).
- **ARP** — Accounting Report (Ka-band downlink completeness summary).
- **FRR** — File Receipt Report.
- **PEF** — Predicted Events File (3.5-day planning-period command sequence).
- **EVCFC** — Extended Virtual Frame Count (28-bit onboard frame counter).
- **NMDC** — NASA Moderate Data Center (IPAC on-premises compute, used for ingest/Level 1/Level 2).
- **TACC** — Texas Advanced Computing Center (used for Level 3).
- **ODIR** — Observation Data Integrity Report (Level 1 re-observation statistics).
- **IDQR** — Image Data Quality Report (Level 2; pointing and PSF size).
- **Butler** — Rubin Observatory's data-access middleware (PostgreSQL + bulk storage), reused for SPHEREx dataset/data-coordinate management.
- **Task / PipelineTask** — Rubin middleware base classes for pipeline modules/pipeline segments.
- **LVF** — Linear Variable Filter (SPHEREx's dispersing element, overlaid per detector).
- **H2RG** — HgCdTe 2K×2K near-IR detector array (six on SPHEREx, one per band).
- **SUR** — Sample-Up-the-Ramp (detector readout mode).
- **FINAST** — header keyword flagging fine-astrometry quality (0 = rms < 1″).
- **DICHROIC** — flag bit for pixels with ≥50% dichroic-induced flux attenuation.
- **NONFUNC** — flag bit for permanently non-functioning pixels.
- **ZODI** — zodiacal-light-model FITS extension in Level 2 spectral images (not subtracted from `IMAGE`).
- **CWAVE / CBAND** — per-pixel central wavelength / bandwidth extensions (lab-measured; for science use).
- **WCS-WAVE** — piecewise-bilinear WAVE-TAB wavelength WCS extension (for visualization).
- **WAVE-TAB** — FITS WCS standard convention for tabulated (non-analytic) coordinate systems, used for the spectral axis.
- **srccat** — Butler dataset type: source catalog output of the Query Reference Catalog module (Parquet).
- **refcat** — Butler dataset type: SPHEREx Reference Catalog.
- **SPHEREx Reference Catalog** — externally/periodically assembled Science-Team catalog of photometric/astrometric calibrators and science-theme sources, providing position/shape priors for Level 3 forced photometry (Yang et al. 2026, in prep).
- **SSO** — Solar System Object (catalog of positions computed via the `kete` orbit-propagation package).
- **Tractor** — probabilistic source-modeling/forced-photometry software (Lang, Hogg & Mykytyn 2016) used for Level 3 photometry.
- **Background2D** — Photutils class used for 2D background estimation (global residual and local modes).
- **HEALPix / NSIDE=64 ("Level 6 HEALPixel")** — sky-tiling scheme used to organize Level 3a scatter-gather processing (~1 sq. deg. per tile).
- **Quantum graph** — DAG describing per-tile Level 2/distortion-map inputs, used to structure Level 3 Slurm jobs at TACC.
- **TAGGED collection** — Butler grouping mechanism for `srccat` inputs by estimated job runtime, used for Level 3 load balancing.
- **HRSC** — High Reliability Source Catalog (SNR>10 in ≥5/102 channels + survey-survey consistency; planned July 2027).
- **All-sky Spectral Catalog** ("Primary All-sky Catalog") — per-exposure, per-source flux/error/wavelength/MJD Parquet catalog.
- **Secondary All-sky Catalog** — per-source spectrum averaged across surveys and interpolated to a fixed wavelength grid, plus variability flags.
- **All-sky Data Cubes** — full-sky mosaics per spectral channel (102 channels), including interpolated flux, variance, zodi/background subtraction info, exposure/coverage, and flags; planned Year 1 (Nov 2026)/Year 2 (Nov 2027) releases.
- **QR1 / QR2** — Quick Release 1 (July 2025, DOI 10.26131/IRSA629) and Quick Release 2 (Oct 2025 release of an Aug–Sep 2025 reprocessing with improved PSF/absolute gain, DOI 10.26131/IRSA652; recommended baseline).
- **DR1 / DR2** — future full reprocessings after Year 1 (surveys 1–2) and Year 2 (surveys 1–4).
- **IRSA** — NASA/IPAC Infrared Science Archive (public data host).
- **Explanatory Supplement** — living, version-tracked companion document at IRSA with full module/flag/calibration implementation detail, not reproduced in this paper.
- **Spectrophotometry / Spectral Image Cutout / Source Discovery / Custom Mosaic / Spectral Cube Cutout** — IRSA-hosted SPHEREx-specific archival analysis tools (Sec. VI).
