# Hidden Monsters with SPHEREx I: A goldmine for heavily reddened quasars at cosmic noon (arXiv:2605.06791)

## Bibliographic info (authors, date, version, journal; one-sentence science goal)

- **Authors**: Matthew Stepney, Manda Banerji, Franz E. Bauer, Roberto J. Assef, Guodong Li.
- **Submitted**: 7 May 2026 (v1, 18:00:19 UTC); revised 1 July 2026 (v2, 12:38:35 UTC).
- **Journal**: Accepted to Astronomy & Astrophysics, 30 June 2026.
- **arXiv category**: astro-ph.GA.
- **One-sentence science goal**: The paper uses SPHEREx spectrophotometry combined with multiwavelength (optical–MIR) photometry to spectroscopically confirm 76 heavily reddened quasars (HRQs) at 1.5 < z < 3.9 and test whether their UV/hot-dust properties support a transient "blow-out" feedback phase.

This is a point-source (quasar) study, not a resolved-galaxy study, but its use of SPHEREx spectrophotometry, the IRSA extraction tool, cross-correlation redshifts, and SED fitting are directly transferable techniques for extracting and validating spectra of compact/marginally-resolved sources.

## SPHEREx data used (release name, product type, dates, number of exposures/objects/pointings, how accessed)

The paper does **not** name a specific data-release version (e.g., QR1/QR2) or cite exposure counts, MEF file structure, or pointing IDs directly. Instead, all SPHEREx spectrophotometry is obtained through **IRSA's Spectrophotometry Tool** (https://irsa.ipac.caltech.edu/applications/spherex/tool-spectrophotometry), described as implementing "a multi-stage data processing pipeline to perform photometric extractions, photometric/wavelength calibrations, and background subtractions of the SPHEREx data in real time" (citing Akeson et al. 2025 — the SPHEREx pipeline paper, not reproduced here). This is the same IRSA-hosted forced-photometry service referenced elsewhere in the SPHEREx literature; the authors treat it as a black box rather than working with raw L1/L2 images or spectral image cubes themselves.

- **Product type**: forced spectrophotometry (source-by-source extracted spectra with per-channel flux + noise), not raw images or cubes.
- **Instrument coverage**: 102 spectral channels spanning 0.75–5.0 μm; resolving power R ≈ 40 in the bluer channels (0.75–3.8 μm; citing Doré et al. 2014); pixel scale 6″.
- **Dates of data used**: "The SPHEREx spectra used in this work were downloaded between January and February 2026." The authors explicitly caution that SPHEREx survey coverage was still accumulating at the time, so "some objects may not have been observed in all spectral channels," which can lower the effective spectral resolution and inflate redshift uncertainties for some targets.
- **Number of objects**: SPHEREx spectra were pulled for the full sample of 404 HRQ candidates (and separately for 9 previously known/confirmed HRQs used for validation, and 500 of the most luminous Quaia control-sample quasars used for redshift-accuracy checks). Of the 76 finally confirmed HRQs, SPHEREx spectra plus SED-fitting constraints were used for 70/76 (6 were excluded because a K-band neighbour lay within 6″, i.e., within one SPHEREx pixel, risking blending).
- **No mention** of exposure counts per source, individual pointing IDs, or a named catalog/table (e.g., no SPHEREx source catalog cross-match is described — targets are pre-selected from NIR/optical surveys, and SPHEREx spectra are queried by coordinates through the tool).

## Target selection and sample properties relevant to extraction (angular sizes, brightness, redshift; resolved vs unresolved)

HRQ candidates are selected from ground-based photometric surveys (not from SPHEREx) using:
- K_AB < 18 mag (brighter cut than the earlier K_AB < 20.3 mag HRQ selection used in prior papers by the same group);
- (J − K)_AB > 1.6;
- (W1 − W2)_Vega > 0.5;
- kclass = −1 (point-source morphology flag in the K/K_S-band photometric catalog).

This yields 413 (later refined to 404) candidates over ≈20,000 deg². Near-IR photometry comes from UKIDSS-LAS DR10, UHS DR2, and VHS DR5 (2″-diameter aperture magnitudes, 1″ match radius), with WISE profile-fitting magnitudes, DELVE-DR2 and SDSS-DR16 optical photometry (MAG_AUTO, given that some HRQs are morphologically extended in rest-UV, and 1″ match radius). No Galactic-extinction correction is applied to the optical bands because the surveys avoid the Galactic plane.

**Resolved vs. unresolved relative to SPHEREx**: all targets are treated as point sources for SPHEREx purposes — this is a quasar sample, not spatially resolved galaxies. The key extraction-relevant criterion is blending/contamination, not intrinsic angular size: sources are only included in the SPHEREx-based SED fitting if "the nearest K-band neighbour lies at an angular separation greater than 6″" (i.e., greater than one SPHEREx pixel), "thereby minimizing contamination." This step removed 6/76 confirmed HRQs from the SPHEREx analysis, consistent with the ≈10% interloper/contamination rate reported by Davies et al. (2026) for source blending at SPHEREx's coarse pixel scale. There is no discussion of semi-resolved or genuinely extended sources — that regime is outside this paper's scope.

## Spectrum / photometry extraction method (step-by-step)

The paper does not implement its own pixel-level extraction; it relies entirely on the IRSA Spectrophotometry Tool for photometric extraction, wavelength calibration, and background subtraction. The only extraction parameters the authors specify (Section 3.1) are:
1. **Morphology assumption**: "a point-source morphology for the forced photometric extraction," i.e., PSF-fitting photometry (not user-defined aperture photometry) at the known source coordinates. The PSF model itself is internal to the IRSA tool; the paper cites no external PSF model source (e.g., no mention of WebbPSF-style models or specific PSF FITS files).
2. **Background estimation**: "a 15 pixel aperture for background estimation," used by the tool to estimate and subtract local background at each source.
3. **Wavelength/LVF assignment**: no description of how wavelength is assigned to a given pixel via the linear variable filter (LVF) is given beyond noting that the IRSA tool performs "photometric/wavelength calibrations" internally; the physical/geometric LVF-to-wavelength mapping is left entirely to the cited pipeline paper (Akeson et al. 2025) and is not reproduced or independently verified in this paper.
4. **Spectral binning**: none beyond the native 102-channel SPHEREx spectral resolution (R ≈ 40 in the bluer channels); no re-binning of the spectrum is described.
5. **Combination of exposures**: not described — the tool evidently returns a single combined per-source spectrum with an associated per-channel noise array; the paper gives no detail on how multiple exposures/observations at different epochs are co-added or weighted.
6. **Error propagation**: the authors state that "the uncertainties associated with the SPHEREx spectral channels are likely underestimated (Davies et al., 2026)" — i.e., they explicitly flag that the pipeline's quoted per-channel errors may not be reliable, and note their own Monte-Carlo redshift errors are "slightly underestimated" as a consequence.
7. **Bad-pixel handling**: for the redshift cross-correlation, "bad SPHEREx pixels [are] masked beforehand" — this is the only data-quality flagging step mentioned; no specific DQ bit names or flag values are given.
8. **Quality cut for downstream fitting**: in SED fitting with SPHEREx spectra, "only spectral channels with signal-to-noise ratios S/N > 5 are included."

**Redshift determination (Section 3.2)** is the paper's main custom spectral-analysis method:
- Pseudo-continuum defined via a median filter (29-channel window, empirically optimized) applied to the SPHEREx spectrum, with the spectrum reflected at both ends before filtering to suppress edge effects.
- A synthetic quasar template is generated with the **qsogen** Python package (https://github.com/MJTemple/qsogen; Temple et al. 2021b), an empirically-motivated parametric quasar-SED simulator, using default parameters to reproduce an average SDSS quasar SED. The template is resampled onto the SPHEREx spectral resolution and continuum-subtracted the same way as the data.
- Cross-correlation (following the Hewett & Wild 2010 method, later refined by Rankine et al. 2020 and Stepney et al. 2023) is computed between template and continuum-subtracted spectrum with redshift as a free parameter, stepped in Δz = 0.01 increments.
- Redshift uncertainty is estimated by perturbing each spectrum with Gaussian noise drawn from its noise array and repeating the cross-correlation 100 times (Monte Carlo), taking the mean and standard deviation of the resulting z estimates.
- Acceptance criteria: cross-correlation coefficient cc(z) ≥ 0.5 (a stricter threshold than Hewett & Wild's cc ≥ 0.2) and z ≥ 1.5.

**SED fitting** uses qsogen plus **emcee** (https://github.com/dfm/emcee; Goodman & Weare 2010 affine-invariant ensemble sampler) to fit a two-component model (dust-attenuated quasar continuum + scattered-light component) to combined broad-band photometry and, for 70/76 sources, the SPHEREx spectrum itself, using Gaussian priors informed by the broad-band-only fit and restricting to S/N > 5 channels. Cross-matching used **TOPCAT v4.10-5** and the **NOIRlab Astro Data Lab** service.

## Background and systematics treatment

- **Zodiacal light**: not discussed at all in the paper — no ZODI extension, no zodiacal model, no local-sky-annulus description. Background subtraction is entirely delegated to the IRSA Spectrophotometry Tool as an internal, unspecified step ("background subtractions of the SPHEREx data in real time").
- **Stray light**: not mentioned.
- **Data-quality flags**: only "bad SPHEREx pixels masked beforehand" is stated; no flag bit definitions, DQ extension names, or specific flag values are given.
- **Cosmic rays**: not discussed.
- **Persistence**: not discussed.
- **Flat-field / calibration residuals**: not discussed directly, but the authors flag that per-channel uncertainties from the pipeline are "likely underestimated (Davies et al., 2026)," an indirect acknowledgment of unresolved calibration/noise-model issues.
- **How they validated calibration**: the primary validation is redshift-based, not flux-calibration-based — cross-correlating SPHEREx spectra of 9 previously spectroscopically confirmed HRQs against ground-based (Gemini-GNIRS, VLT-SINFONI) redshifts, finding ⟨Δz⟩ ≈ 0.011, consistent with their Monte-Carlo redshift uncertainties (⟨Δz⟩ ≈ 0.006 for the full sample). A second check uses 500 luminous Quaia quasars with Gaia QSOC redshifts, finding ⟨Δz⟩ = 0.08 and |Δz| < 0.2 (|Δz/(1+z)| ≲ 0.1) for 95% of the sample.

## Stacking or combining multiple objects (if done)

**No spectral stacking is performed.** Every SPHEREx spectrum is analyzed individually — per-source redshift cross-correlation and per-source SED fitting. There is no normalization, weighted co-addition, deredshifting-and-stacking, or composite-spectrum construction anywhere in the paper. The closest analog is the SED-fitting comparison of the 76 HRQs as a population against a separately constructed "luminous blue quasar" control sample (drawn from Quaia, the Gaia-unWISE quasar catalog), but that comparison is done parameter-by-parameter (e.g., distributions of E(B−V), hot-dust amplitude), not via spectral stacking.

## Validation and quoted uncertainties

- Redshift accuracy vs. ground-based spectroscopy (9 sources): ⟨Δz⟩ ≈ 0.011.
- Internal Monte-Carlo redshift uncertainty for the full confirmed sample: ⟨Δz⟩ ≈ 0.006 (explicitly noted as likely a slight underestimate, given underestimated per-channel pipeline noise).
- Redshift accuracy vs. Gaia QSOC redshifts (500 luminous Quaia quasars): ⟨Δz⟩ = 0.08; |Δz| < 0.2 for 95% of the sample.
- SED-fit goodness of fit: median reduced χ² = 1.6 for the 76 HRQs (vs. 1.9 for the parent HRQ sample in Stepney et al. 2026); median reduced χ² = 1.4 for the Quaia control-sample fits.
- Hot-dust amplitude precision from adding SPHEREx MIR photometric anchors: ΔL_Dust/L_Disk|2μm = 0.25 at 1.5 < z < 2.7 (via W2, 4.6 μm, average uncertainty 0.028 mag) and the same precision at 3.2 < z < 4.0 (via W3, 12 μm, average uncertainty 0.054 mag); combining SPHEREx spectra with broadband photometry improved hot-dust amplitude constraints by "a factor of seven" relative to broadband alone.
- No comparison to 2MASS is made; WISE is used as photometry (not as an independent spectral check) and Quaia/Gaia redshifts serve as the external calibration standard for the control sample.

## Lessons and reusable techniques for extracting spectra of nearby galaxies (synthesis)

1. **The IRSA Spectrophotometry Tool is usable as a turnkey forced-photometry engine**, returning calibrated per-channel spectra with noise arrays for point-source-like targets given only coordinates; this paper demonstrates it works well enough to derive redshifts to ⟨Δz⟩ ≈ 0.01 accuracy for AGN continua, but the authors do not vet its internal background/PSF/wavelength-calibration choices — anyone using it for extended/nearby galaxies should independently verify those steps (e.g., against the pipeline paper) since this paper treats them as a black box.
2. **Explicitly discard sources with neighbours within one SPHEREx pixel (6″)** before attempting SED/spectral analysis; this simple angular-separation cut, applied here for point sources, is directly reusable as a blending/contamination screen for compact or marginally-resolved galaxies too.
3. **Treat pipeline-reported per-channel uncertainties as a lower bound, not ground truth.** The authors flag pipeline errors as "likely underestimated" and validate this by comparing Monte-Carlo redshift scatter to independent ground-truth redshifts rather than trusting the noise array alone — a good general practice: always calibrate SPHEREx noise arrays against an external, independent measurement when precision matters.
4. **Median-filter continuum removal with edge-reflection padding** (their 29-channel window) is a simple, reusable technique for building a smooth pseudo-continuum from a low-resolution (R≈40) SPHEREx spectrum before any line- or feature-based analysis (e.g., before searching for stellar absorption/emission features in post-starburst galaxies).
5. **Cross-correlation redshifting against a template resampled to SPHEREx's native resolution** (rather than trying to fit high-resolution features) is an efficient way to extract redshifts/velocity information from R≈40 spectra; the same machinery (template generation, resampling, masked cross-correlation, Monte Carlo error estimation) could be adapted with a galaxy template (e.g., an SSP or post-starburst template) instead of qsogen.
6. **Restrict quantitative fitting to S/N > 5 channels** — a simple, explicit per-channel quality cut used before any SED or line fitting, easily reused for galaxy spectra.
7. **Always cross-check SPHEREx-derived redshifts/velocities against any available higher-resolution reference spectra** (ground-based spectroscopy or a well-calibrated external redshift catalog); the paper's two independent validation checks (9 known HRQs; 500 Quaia quasars) is a reusable two-tier validation pattern: an accuracy check against a small, high-confidence subset, and a precision check against a larger but coarser reference sample.

## Caveats the authors state

- Some SPHEREx targets may lack full spectral-channel coverage because the survey was still accumulating data as of the January–February 2026 download window, which can locally reduce spectral resolution and inflate redshift uncertainties for specific objects.
- Per-channel SPHEREx uncertainties are "likely underestimated," per Davies et al. (2026), which the authors say explains why their own Monte-Carlo redshift errors are somewhat underestimated too.
- SPHEREx's low spectral resolution in the bluer channels (R ≈ 40 at 0.75–3.8 μm) makes robust Hα-derived black-hole mass measurements infeasible at the redshifts probed, so such measurements are not attempted.
- No Milky Way Galactic-extinction correction is applied to the optical photometry (because the parent surveys avoid the Galactic plane); the authors judge this a secondary source of uncertainty compared to photometric-extraction errors and the simplicity of their two-component SED model.
- Sources with a K-band neighbour within 6″ (one SPHEREx pixel) are excluded from SPHEREx-based analysis to limit blending/contamination, consistent with a ~10% interloper/contamination rate reported elsewhere (Davies et al. 2026) for SPHEREx forced photometry at this pixel scale — implying blending remains a residual risk even after the cut.
- The rest-UV excess seen in many HRQs is degenerate between "scattered quasar light" and "ongoing star formation in the host galaxy"; the authors state a host-galaxy UV contribution cannot be ruled out with their current data/method.
