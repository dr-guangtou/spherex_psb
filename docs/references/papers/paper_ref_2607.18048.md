# Comparing the Near-infrared Spectral Energy Distributions from Different Stellar Population Synthesis Models with SPHEREx Observations (arXiv:2607.18048)

## Bibliographic info

Authors: Jeong Hwan Lee, Minjin Kim, Woong-Seob Jeong, Yujin Yang, Daniel C. Masters, Kyuseok Oh, Bomee Lee, Zhaoyu Huai, Yun-Ting Cheng, Richard M. Feder, Michael Zemcov, Yongjung Kim, Dohyeong Kim, Jong-Hak Woo, Andreas L. Faisst, Howard Hui, Brendan P. Crill, Chi H. Nguyen, Asantha Cooray. Submitted 2026 July 20 (single version, v1, 15:18:49 UTC); submitted to ApJ, classified astro-ph.GA. Science goal in one sentence: the authors extract SPHEREx NIR (0.75–5.0 µm) spectrophotometry for ~3,900 SDSS-selected, spatially compact galaxies and compare the observed rest-frame NIR SEDs (individually and stacked) against predictions from different stellar population synthesis (SPS) models to test which models best reproduce NIR features (e.g., TP-AGB and cool-star contributions).

## SPHEREx data used

- Release/pipeline: **SPHEREx Quick Release 2 (QR2)**, processed with **SPHEREx pipeline version 6.4 or later**.
- Access: **NASA/IPAC Infrared Science Archive (IRSA)**, specifically the **IRSA Spectrophotometry Tool** (the standard/official extraction service, in contrast to the custom SPIFF pipeline of Gagné et al. 2604.22012). Data DOI cited: doi:10.26131/IRSA652.
- Extraction dates: **2026 April 14 – 2026 May 11**.
- Product type: per-object spectrophotometric points across the SPHEREx bands, extracted using a **point-source forced-photometry profile fixed to SDSS catalog coordinates** (i.e., catalog-based forced photometry, not blind detection).
- Sample size: starting from 4,172 compact-galaxy candidates cross-matched to SDSS, narrowing to 4,066 with valid SPHEREx data points, and a final analysis sample of **3,889 compact galaxies** (2,726 non-emission-line galaxies "non-ELGs" and 1,163 emission-line galaxies "ELGs") after quality and cross-calibration cuts.

## Target selection and sample properties relevant to extraction

Targets are deliberately **unresolved (point-source-like) at the SPHEREx pixel scale**, which is the key extraction-relevant design choice of this sample:
- **Compactness cut**: SDSS Petrosian radius <3.1″, explicitly chosen to be smaller than the **SPHEREx pixel scale of 6.15″×6.15″**, so that each galaxy can be treated as a point source for forced photometry (no PSF/aperture debate about resolved structure).
- **Brightness cut**: SDSS i-band fiber magnitude brighter than 20 mag.
- **Redshift**: z>0.01 with SDSS `zWarning == 0` (reliable spectroscopic redshift).
- Sample split into non-ELG and ELG subsets for later stacking-by-property analysis (age, metallicity).
- This is explicitly an **unresolved-galaxy** extraction case study — useful as a direct methodological analog for unresolved/semi-resolved post-starburst galaxies, though the compactness selection (<3.1″) is much smaller than typical low-z PSB angular sizes, so the forced-point-source approach may need modification (PSF+extended-light decomposition) for larger, resolved PSB targets.

## Spectrum / photometry extraction method

1. **Aperture/profile choice**: **point-source profile forced photometry**, with source positions **fixed to SDSS coordinates** (no re-centroiding), via the IRSA Spectrophotometry Tool.
2. **Local background**: subtracted using a **15-pixel box** — described as "the default configuration" of the IRSA tool (i.e., the same default local-background box size referenced in the ultracool-dwarf and ISM-mapping papers, suggesting this 15-pixel box is a standard IRSA-tool default rather than a bespoke choice).
3. **Quality/coverage cut**: objects are required to have **at least 10 valid data points in each SPHEREx band** (6 bands); objects failing this are excluded as having insufficient photometric coverage.
4. **Flags used**: only SPHEREx data points with **photometry flag = 0 (no flags)** or **flag = 2097152 (bit 21, "source")** are retained. Explicitly excluded flag bits: **bit 0 (cosmic ray hits)**, **bit 1 (saturation)**, **bit 7 (dichroic mirror transition region between SPHEREx Bands 3 and 4)**. This is the most detailed, explicit quality-flag bitmask description found across the three papers reviewed.
5. **Wavelength assignment / LVF handling**: the authors explicitly note that because SPHEREx uses linear variable filters, "the wavelength information varies with the spatial position in the SPHEREx LVF planes," so **individual extracted spectra have unique, non-standard wavelength sampling** even for sources processed identically. To standardize, they **resample all photometry onto a common grid of 102 wavelength channels** using the standardized SPHEREx filter response curves, interpolating each galaxy's native (irregularly sampled) photometry onto this unified 102-channel grid.
6. **Combining exposures**: implicit in the IRSA tool's forced-photometry output (per-band, coverage ≥10 points per band used as quality gate); explicit per-exposure combination algorithm is not detailed beyond the IRSA tool defaults.
7. **Absolute flux cross-calibration against SDSS**: a **scaling factor** is applied to each galaxy's SPHEREx spectrum, computed as the ratio of the SDSS z-band magnitude to a synthetic z-band magnitude computed by convolving the SPHEREx spectrum with the SDSS z filter (using `pyphot` for synthetic photometry). The median offset found was small: **original SPHEREx fluxes were only ~4% fainter than SDSS z-band fluxes** before this correction.
8. **Outlier rejection at the galaxy level**: galaxies with a SPHEREx-to-SDSS flux offset >20% were excluded from the analysis sample (this and the coverage cut are what reduces 4,066 → 3,889 galaxies); ~95% of the sample has offsets below this threshold.
9. **Aperture-matching correction for SDSS fiber spectra**: because SDSS spectra were taken through 3″-diameter fibers that do not capture all the light of even these compact galaxies, the authors compute the ratio of **SDSS model flux to fiber flux in the r band** and multiply both the SDSS spectrum and the best-fit model SEDs by this ratio to place everything on a consistent total-light scale before comparison to SPHEREx (which, as forced point-source photometry, captures closer to total light within the PSF).
10. **Error propagation / weighting**: in fitting/comparison, weights w_i = 1/σ_i² are used, where σ_i combines the **propagated SPHEREx flux measurement uncertainty** with an assumed **10% uncertainty floor on the modeled fluxes** (i.e., model-uncertainty floor, not purely observational).

## Background and systematics treatment

- **Zodiacal light**: no explicit ZODI extension or dedicated zodiacal model is described; the **15-pixel local background box** (IRSA tool default) is the background-handling mechanism, consistent with the local-background approach seen in the other two papers — SPHEREx L2/L3-derived spectrophotometry products evidently rely on local-box background subtraction by default rather than a delivered ZODI-subtracted flux.
- **Flags**: explicit bitmask exclusions for cosmic rays (bit 0), saturation (bit 1), and the Band 3/4 dichroic transition (bit 7); only flag=0 or flag=2097152 (source bit) points retained. No mention of persistence or stray-light-specific flags.
- **Calibration residuals validated two ways**: (a) internal cross-check against SDSS z-band photometry (median offset ~4%, most objects <20% offset), and (b) external cross-check against **WISE W1 photometry**, where synthetic W1 fluxes from the SPHEREx spectra are only **~3.5% higher than actual WISE W1 fluxes** — cited as evidence of good absolute-calibration agreement for this compact-galaxy sample.
- **No cosmic-ray/persistence discussion beyond the flag bitmask** is provided; no explicit stray-light correction is mentioned.
- **Kinematic validation**: stellar kinematics (redshift, velocity dispersion) derived from full-spectrum fitting (pPXF-based) of the SPHEREx+SDSS combined SEDs are compared to SDSS archival `SpecObjAll` values, yielding median offsets of **8.3 km/s in radial velocity** and **−0.6 km/s in velocity dispersion** — a useful cross-check that the SPHEREx-derived spectral fits are physically consistent with independent SDSS measurements even though SPHEREx's spectral resolution is far coarser than SDSS.

## Stacking or combining multiple objects

Yes — median stacking of rest-frame SEDs is a core part of the analysis (Section V.1, Figures 10 and A1):
- **Redshift handling**: each galaxy's observed-frame SPHEREx SED is shifted to the **rest frame using its SDSS spectroscopic redshift** before stacking.
- **Binning**: stacked rest-frame SEDs are binned onto the **same 102 SPHEREx spectral channel grid** used for individual objects (i.e., rest-frame wavelength binning uses the same standardized channel structure as the observed-frame resampling step).
- **Combination statistic**: described as a **"median stacked"** SED (e.g., "median stacked NIR SEDs of 485 non-ELGs with log Age(yr)<9.5"), implying per-channel median combination across galaxies in a given sample bin, rather than an explicit inverse-variance-weighted mean; the exact per-galaxy weighting scheme for the stack (if any beyond straight median) is not detailed in the extracted text.
- **Sample splits used for stacking**: by stellar population age (intermediate: log Age(yr)<9.5 vs. old: ≥9.5) and by metallicity (metal-poor vs. metal-rich, split at the median E-MILES-model metallicity).
- **Uncertainty representation**: stacked-SED figures show shaded uncertainty bands (likely percentile ranges across the stacked galaxies), but the precise statistical definition of the band (e.g., IQR, 16th–84th percentile, or standard error of the median) is not explicitly stated in the fetched material.

## Validation and quoted uncertainties

- SPHEREx-to-SDSS z-band offset: median ~4%, with the 20% cut retaining ~95% of candidate galaxies.
- SPHEREx-to-WISE W1 offset: synthetic W1 from SPHEREx is ~3.5% higher than real WISE W1 photometry — used as an independent, non-SDSS calibration check.
- Kinematic cross-validation vs. SDSS: median offsets of 8.3 km/s (radial velocity) and −0.6 km/s (velocity dispersion).
- Model-fitting uncertainty floor: a flat **10% uncertainty floor is imposed on modeled (SPS-predicted) fluxes** when computing fit weights, separate from (and typically larger than) the propagated SPHEREx measurement errors — implying the SPHEREx photometric errors themselves are smaller than 10% for this bright, compact sample, though the paper does not quote a single headline SPHEREx calibration-uncertainty percentage the way the ultracool-dwarf paper does (no explicit "X% error floor" statement for SPHEREx itself is given in the fetched text).
- Software used: NumPy, Matplotlib, SciPy, Astropy, **pPXF** (penalized pixel-fitting for kinematics/population synthesis fitting) and **pyphot** (synthetic photometry).

## Lessons and reusable techniques for extracting spectra of nearby galaxies

- **A simple, well-defined SPHEREx-vs-SDSS/WISE flux cross-calibration recipe** (synthetic photometry via `pyphot` in a matched band, compute median offset, apply as a single multiplicative scale factor per object, then reject >20% outliers) is directly reusable for validating/calibrating SPHEREx spectra of PSB host galaxies against existing SDSS/2MASS/WISE photometry.
- **Explicit, documented quality-flag bitmask** (flag=0 or 2097152 only; reject bits 0, 1, 7) is the clearest, most reusable flag-selection recipe among the three papers and should be adopted as a starting point for any SPHEREx photometric extraction pipeline for galaxies.
- **Aperture/fiber-matching correction** (scaling SDSS fiber spectra and models by the model/fiber flux ratio in a reference band before comparing to SPHEREx) is an important, generalizable step whenever comparing fiber-based optical spectroscopy to larger-aperture or PSF-based NIR photometry — directly relevant since many PSB galaxies have SDSS or other fiber/slit spectra that will need similar aperture correction before joint SED/kinematic fitting with SPHEREx.
- **Resampling irregular per-object LVF-driven wavelength sampling onto a common 102-channel grid via interpolation using the standardized filter response curves** is the standard approach across papers and should be the default step before any stacking or cross-object comparison.
- **Median stacking in the rest frame after individual per-galaxy background/flag/calibration cleaning** is a straightforward, reusable stacking recipe for building composite PSB spectra from multiple objects at different redshifts, though the paper's lack of a fully specified weighting scheme suggests this is an area to define more rigorously (e.g., inverse-variance weighting) if stacking small, heterogeneous PSB samples where per-object S/N varies substantially.
- The compactness pre-selection (<3.1″, well within one SPHEREx pixel) is a reminder that **forced point-source photometry is only strictly valid for genuinely unresolved sources**; for larger/resolved PSB galaxies, a PSF+aperture or PSF+extended-profile decomposition (as hinted at in the ultracool-dwarf paper's PSF-fitting approach, or the ISM paper's custom aperture tool) will be needed instead of simple forced point-source photometry.

## Caveats the authors state

- SPHEREx's LVF design causes **non-standard, position-dependent wavelength sampling per object**, requiring an explicit resampling/interpolation step before any cross-object comparison or stacking — treated as a a necessary correction, not just a minor detail.
- ~5% of candidate galaxies show SPHEREx-to-SDSS flux discrepancies >20% and are excluded, implying occasional bad extractions/contamination/mismatches even after flag-based cleaning — no root cause is isolated in the fetched text (possible blending, background galaxies, or catalog position errors).
- Photometric coverage requirement (≥10 valid points per band) implies a non-trivial fraction of forced-photometry attempts yield insufficient usable data per band, a practical data-completeness caveat for any SPHEREx-based galaxy study.
- No single explicit "systematic error floor" percentage is stated for SPHEREx absolute calibration in this paper (contrast with the ultracool-dwarf paper's stated 8% floor); the 10% floor discussed is for **model** fluxes in the fitting weights, not a SPHEREx observational-calibration floor, so readers should not conflate the two.
