# SPHEREx Wide-Field Infrared Spectral Mapping of Interstellar Ices and Polycyclic Aromatic Hydrocarbons (arXiv:2603.12390)

## Bibliographic info

Authors: Joseph L. Hora, Jinyoung K. Noh, Gary J. Melnick, Brandon S. Hensley, Roberta Paladini, Jeong-Eun Lee, Matthew L. N. Ashby, Volker Tolls, Jaeyeong Kim, Michael W. Werner, James J. Bock, Sean Bruton, Shuang-Shuang Chen, Tzu-Ching Chang, Yi-Kuan Chiang, Asantha Cooray, Brendan P. Crill, Ari J. Cukierman, Olivier Doré, Andreas L. Faisst, Zhaoyu Huai, Howard Hui, Woong-Seob Jeong, Miju Kang, Phil M. Korngut, Ho-Gyu Lee, Carey M. Lisse, Daniel C. Masters, Giulia Murgia, Chi H. Nguyen, Zafar Rustamkulov, Ji Yeon Seok, Robin Y. Wen, Yujin Yang, Michael Zemcov. Submitted 2026 March 12 (v1); accepted by the Astrophysical Journal (accepted 2026 March 11). Science goal in one sentence: the paper demonstrates SPHEREx's ability to make **wide-field, spatially resolved spectral maps** of solid-state ice absorption (H2O, CO2, CO) and PAH emission features across the Cygnus X star-forming region and North American Nebula, using narrow-wavelength-range image mosaics built directly from L2 exposures plus complementary L3 point-source spectrophotometry.

## SPHEREx data used

- Release/pipeline version: **SPHEREx Science Data Center (SSDC) pipeline, QR2 version** — "the same version currently available on the IRSA archive."
- Product types: **Level 2 (L2) images** (individual calibrated exposures, used to build custom narrow-band spectral-feature mosaics) and **Level 3 (L3) spectrophotometry** (point-source forced photometry via a Tractor-based pipeline) for compact sources.
- Access: L2 images are **publicly available via the IRSA SPHEREx site** (https://irsa.ipac.caltech.edu/Missions/spherex.html).
- Observation dates/exposure counts: Cygnus mosaics were built from two observing windows, **2025 April 26 – 2025 July 5** and **2025 October 10 – 2025 November 2**, with an **average of 148 individual exposures** per mosaic pixel/wavelength range. For the LDN 935 field, data span **2025 May 9 – 2025 July 5** and **2025 October 23 – 2025 November 18**, with an average of **52 exposures** per wavelength range. All individual integrations use the standard SPHEREx exposure time of **113.5826 s**.
- For most fully covered regions in this dataset, roughly **100 spectral samples** per sky position are available from the L2 images (i.e., each sky location is revisited enough times across the six SPHEREx bands/detectors to build a coarse spectral map).

## Target selection and sample properties relevant to extraction

This is a diffuse/extended-emission mapping paper (Galactic ISM), not a discrete-galaxy extraction paper, but the extended-source and mosaicking methodology is directly relevant for resolved/semi-resolved nearby galaxies:
- Fields are large, extended, spatially structured (molecular cloud complexes: Cygnus X, North American Nebula/LDN 935), i.e., **fully resolved** at the SPHEREx pixel scale, unlike point-source or compact-galaxy cases.
- Because coverage is still single-epoch at this early mission stage, **spatial coverage is non-uniform** with overlap only at scan edges, directly affecting how many independent samples exist per sky position (driving the "~100 samples" figure and associated need for sigma-clipping).
- The L3 catalog-based point-source extraction (Tractor + PSF) is applied in parallel for compact/embedded sources within the same fields, giving a useful contrast between the paper's two methods: pixel/mosaic-based diffuse extraction vs. PSF-based point-source extraction.

## Spectrum / photometry extraction method

Two parallel extraction approaches are used.

**(A) Narrow-band spectral-feature mosaics (diffuse/extended emission):**
1. **Pixel/wavelength selection** — custom Python scripts examine, for every pixel of every L2 exposure, the **wavelength of peak transmission at that pixel's exact location** (since SPHEREx uses linear variable filters, the effective wavelength depends on detector position, not just nominal band). If that wavelength falls within a pre-defined range of interest (e.g., centered on an ice or PAH feature, or a line-free continuum window), the pixel is retained.
2. **Slicing** — each L2 image is sliced into separate sub-images per defined wavelength range, using the wavelength coverage of each of SPHEREx's six bands/detectors.
3. **Wavelength range design** — narrow ranges are centered on individual emission/absorption features (with adjacent line-free continuum ranges on both sides for baseline subtraction); for broad features like the H2O ice band, wider ranges are used to maximize coverage/redundancy given the single-epoch data.
4. **Reprojection and combination** — the wavelength-sliced sub-images from many exposures are reprojected onto a common world coordinate system (WCS) and then **averaged pixel-by-pixel** to build a mosaic for each wavelength range.
5. **Outlier rejection** — where ≥3 independent samples exist at a given pixel, **sigma-rejection** removes outliers (attributed mainly to cosmic rays, satellite tracks, non-responsive pixels, or unflagged artifacts) before averaging.
6. **Continuum and optical depth** — at each absorption-line center, the continuum flux F_λC is estimated by **linear interpolation** between the nearby line-free continuum-range mosaics; optical depth is computed as **τ = ln(F_λC / F_λI)**, where F_λI is the observed in-line flux. For PAH emission, the continuum is likewise obtained by linear interpolation between nearby continuum-wavelength mosaics, and the feature strength is derived after continuum subtraction.
7. **LVF banding artifact correction** — because a given nominal "wavelength range" is sampled by different actual central wavelengths at different detector/pixel positions (i.e., the true wavelength walks across the pixel response curve depending on where on the array the source position falls), absorption depth/feature strength appears to systematically vary across the mosaic, producing curved "banding" stripes. The authors correct for this using **JWST NIRSpec spectra of 12 reference sources** to build average absorption-line profiles, then run **simulated SPHEREx observations (the "Ices SPHEREx simulator")** to derive per-pixel correction factors. Quoted correction factors: H2O center/maximum = 1.01/1.13; CO2 = 1.44/2.99; PAH = 1.95/4.24. The correction is applied to **difference images built from individual L2 exposures** before mosaicking the corrected differences.

**(B) L3 point-source spectrophotometry (compact/embedded sources):**
- Uses **The Tractor** image-modeling code to perform **forced photometry at fixed catalog positions**, using a **model of the SPHEREx PSF derived from flight data** (not a synthetic/instrument-model PSF), applied to each L2 image.

**(C) Custom aperture photometry tool (extended sources, alternative to mosaics):**
- Rather than a fixed sky annulus, **the user manually selects a nearby background region** representative of the local sky for each source, given the high source density and complex extended emission in these fields; a median of that region is subtracted from the on-source aperture flux.
- Any photometric sample for which the source aperture overlaps a pixel flagged as bad in a given L2 slice is discarded entirely from that spectral point (rather than being corrected or down-weighted).

No explicit combined error-propagation formula for per-pixel mosaic uncertainties is given in the extracted text.

## Background and systematics treatment

- **No zodiacal-light (ZODI) model or extension is used or mentioned** — background handling is purely **local**: median subtraction over a user- or algorithm-selected nearby region (aperture photometry) or continuum interpolation between adjacent wavelength mosaics (feature mapping). This is notable for a resolved-galaxy/PSB use case: SPHEREx L2/L3 products evidently leave zodiacal subtraction/local background as an extraction-time choice rather than delivering a per-pixel ZODI-subtracted product baked in (at least as described here).
- **Flags**: no formal bitmask is quoted; bad pixels are simply excluded from apertures, and sigma-clipping across multiple independent L2 samples removes cosmic rays, satellite tracks, and other unflagged artifacts during mosaicking.
- **Calibration**: no explicit absolute or relative flux calibration uncertainty percentage is quoted for SPHEREx in this paper (in contrast to Gagné et al. 2604.22012's 8% floor). The only calibration uncertainty discussed concerns the ancillary Herschel-SPIRE dust maps, which the authors note are absolutely calibrated via Planck ancillary data.
- **LVF wavelength-position banding artifact** (described above) is the dominant, paper-specific systematic and is explicitly modeled/corrected via simulation-derived correction factors calibrated against JWST spectra.
- **Coverage/epoch caveat**: at this early stage of the mission most fields have only single-epoch coverage with small overlaps at scan edges, so mosaics show visible artifacts (undefined-value pixels) that the authors expect to improve once SPHEREx completes ~4 full-sky scans, enabling better outlier rejection.
- **Unresolved-line bias**: SPHEREx's spectral resolving power (R≈35–130) is too coarse to resolve narrow lines (e.g., atomic/molecular H lines, and notably the CO2/CO ice features), so **peak optical depths are systematically underestimated** and cannot simply be summed to get integrated optical depth/column density. A correction framework using simulated observations of known-optical-depth spectra is under development for a future "Ices investigation pipeline" paper, but **no correction factors are applied in this paper** — quoted optical depths are explicitly stated to be lower limits.
- **Saturated absorption floor effect**: when the background flux passing through a cloud at a line center falls below the SPHEREx detection limit, the measured "flux" is set by foreground emission rather than by the true absorbing column, so **optical depth cannot be reliably determined in the deepest absorption regions regardless of true ice column**.

## Stacking or combining multiple objects

Not a multi-galaxy stack. The relevant combination is spatial: many overlapping/dithered L2 exposures (average 52–148 per field) are averaged pixel-by-pixel per wavelength-range slice to build each mosaic, with sigma-rejection when ≥3 samples exist per pixel. This is directly analogous to what a resolved-galaxy pipeline would need to do to build a 2D narrow-band or spectral-feature map from many dithered SPHEREx exposures.

## Validation and quoted uncertainties

- Ice/PAH maps are compared (Spearman correlation) against independent tracers: H2O ice vs. ¹³CO (FCRAO, ρ=0.461), vs. 2MASS NICEST A_J extinction (ρ=0.388), vs. Herschel-derived N(H2) column density (ρ=0.272); PAH emission vs. dust temperature (ρ=0.834).
- Dust temperature/column density derived from Herschel-SPIRE via pixel-by-pixel single-temperature grey-body SED fitting, κ_ν = 0.1(ν/1000 GHz)^β cm² g⁻¹ with β=2 (used only for cross-validation, not for SPHEREx calibration).
- No 2MASS/WISE photometric spectral cross-check is performed on the SPHEREx spectra themselves (2MASS is used only as an extinction map, not a flux calibration check).
- No explicit numerical absolute-flux-calibration uncertainty is quoted for SPHEREx in the fetched material.

## Lessons and reusable techniques for extracting spectra of nearby galaxies

- **Wavelength assignment must be done per-pixel, at the actual detector position sampled, not from a nominal band/channel table** — this is the central technical lesson repeated across all SPHEREx papers and is essential for resolved-galaxy work where different parts of a galaxy fall on different detector positions in different exposures.
- **LVF banding/position-dependent bandpass artifacts are real and must be corrected**, especially for narrow spectral features; the simulate-and-calibrate-against-a-higher-resolution-spectrograph approach (JWST here) is a reusable validation strategy that could be mirrored using existing ground-based/archival galaxy spectra for post-starburst targets.
- **Sigma-clipped averaging across many dithered/revisit exposures** is the primary noise/artifact mitigation tool at this stage of the mission (single-epoch coverage); pipelines for resolved PSB galaxies should budget for a comparable number of independent revisits (tens to ~100) per sky position to get robust pixel-level combination.
- **No baked-in ZODI subtraction is evident in these products** — any galaxy pipeline should plan its own local-background/ZODI handling explicitly rather than assuming SPHEREx L2/L3 already removes it.
- **Continuum estimation via interpolation between adjacent narrow-band images** is a simple, effective technique for isolating absorption/emission features and could be adapted to isolate stellar continuum vs. line/dust features in galaxy spectra extracted the same way.
- Two extraction philosophies are demonstrated side by side — **custom pixel-selection/mosaicking for extended/diffuse sources** vs. **Tractor-based PSF forced photometry for compact sources** — which maps directly onto the "resolved vs. semi-resolved vs. unresolved" spectrum extraction problem for PSB galaxies at different distances.

## Caveats the authors state

- Single-epoch coverage at this early mission stage produces visible mosaic artifacts (undefined pixels); expected to improve after ~4 full-sky scans.
- LVF-driven banding artifacts in narrow-feature mosaics require simulation-based correction; correction factors are large for compact features (up to ~3–4× for CO2/PAH).
- SPHEREx's coarse spectral resolution (R≈35–130) systematically underestimates peak optical depths of narrow lines (H2, CO2, CO); no correction is applied in this paper, so quoted values are explicit lower limits.
- Deep/saturated absorption cannot be reliably measured because line-center flux can fall below the SPHEREx detection floor, decoupling measured optical depth from true ice column.
- A dedicated "Ices investigation pipeline" paper with quantitative optical-depth correction factors (from simulated observations) is announced as forthcoming/in-progress, not yet available.
