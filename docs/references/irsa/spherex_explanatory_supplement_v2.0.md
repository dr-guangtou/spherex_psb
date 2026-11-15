# SPHEREx Explanatory Supplement v2.0 (2026-08-25), full read

Source: SSDC–DP–017, "SPHEREx Explanatory Supplement," Version 2.0, 2026-08-25 (82 pp). Local PDF:
`/Users/shuang/Dropbox/work/project/otters/spherex_psb/docs/references/sources/external/SPHEREx_Expsupp_QR_2026-09-22.pdf`.
This note supplements a prior partial survey (which already covered: the 3-page archive documentation site,
the FLAGS bitmask Table 16, the PSF header-ordering bug, the Mosaic Tool overview, the Level 3 Tractor
forced-photometry summary, and the QR2/QR3/DR1 release roadmap) with full, quantitative coverage of every
other section, especially payload/survey strategy, header keywords, image anomalies, processing algorithms
(blooming/snowball/halo, variance, persistence, bad pixels, astrometry, source masks/ghosts, outliers, zodi),
photometry, mosaics, and calibrations (ePSF, gain, astrometry, spectral WCS/channels).

## Document metadata and revision history

- Authors: SPHEREx Science Data Center (SSDC) team (Akeson, Dubois-Felsmann, Faisst, Fatahi, Goldina,
  Kwon, Masters, Nelson, Paladini, Torrini, Velicheti) plus SPHEREx Science Team contributors.
- Document generated 2026-09-02 from commit v1.0 of 2025-07-02; the copy read here is nominally dated
  2026-08-25 (Version 2.0).
- Change record (abridged, full list is informative for tracking what changed release-to-release):

| Ver | Date | Key content |
|---|---|---|
| 0.1 | 2025-04-03 | Initial draft |
| 1.0 | 2025-07-02 | Quick-Release (QR1) version release |
| 1.1 | 2025-08-13 | Pipeline version info, IRSA links, L2 DQA corrections |
| 1.2 | 2025-08-29 | Pipeline-version table; clarified role of WCS-WAVE vs. Spectral WCS files |
| 1.2.1 | 2025-10-13 | Photometry flag-usage table |
| 1.3 | 2025-10-13 | QR2 data/calibration updates |
| 1.3.1 | 2025-12-25 | Spectral WCS change for photometry tool |
| 1.4 | 2026-01-23 | Pipeline v6.5: fewer fine-astrometry failures; new blooming/snowball/CR-halo flags; persistence changes; beamsplitter ghost masking; updated nonfunctional-pixel map |
| 1.5 | 2026-03-30 | Pipeline v6.5.6: fixed PSF-layer header ordering bug |
| 1.6 | 2026-05-06 | New Mosaics section (algorithmic description of IRSA Mosaic Tool) |
| **2.0** | **2026-08-25** | **Major update for pipeline R7**: Persistence Masks, Bad Pixel Flagging, Fine Astrometry, Outlier Pixel Detection, Zodi Prediction, Photometric Measurements, PSF, Spectral Channels, header examples all revised |

## 1 Mission overview

**Mission**: SPHEREx (Spectro-Photometer for the History of the Universe, Epoch of Reionization, and Ices
Explorer), NASA MIDEX. Launched 2025-03-12 03:10:12 UTC (Falcon 9, Vandenberg). Science ops began
2025-05-01 after IOC. Nominal mission: 25 months, four complete all-sky surveys, ≈1.4×10¹² spectral-spatial
elements (voxels) per all-sky pass (≈5×10¹² accumulated over the full mission per Fig. 4 caption). Orbit:
sun-synchronous LEO, semi-major axis 7037.41 km, e=0.00034, i=97.951°, MLTAN 06:00, period 98 min.
No onboard propulsion; passive de-orbit within 25 yr of end of mission.

**Payload (Sec. 1.3)**:
- 20 cm effective-aperture, all-aluminum free-form Three Mirror Anastigmat (TMA) telescope, f/3.
- FoV: 2 × (3.5° × 11.3°), split by a dichroic beam splitter (DBS) into SWIR and MWIR paths.
- Wavelength coverage: 0.744–5.002 µm total, across 6 bands with per-band design resolving power:

| Band | λ range (µm) | R (design) |
|---|---|---|
| 1 | 0.744–1.116 | 39 |
| 2 | 1.099–1.651 | 41 |
| 3 | 1.636–2.421 | 41 |
| 4 | 2.423–3.822 | 35 |
| 5 | 3.809–4.420 | 112 |
| 6 | 4.412–5.002 | 128 |

- Detectors: 6× Teledyne H2RG 2k×2k HgCdTe (3× 2.6 µm cutoff for SWIR FPA, 3× 5.3 µm cutoff for MWIR
  FPA), each paired with a Linear Variable Filter (LVF) positioned above the array.
- SWIR FPA: 0.75–2.44 µm (reflection side of DBS), operates at 62 K. MWIR FPA: 2.40–5.01 µm (transmission
  side), operates at 45 K. Cooling is entirely passive (3-stage V-groove radiator + dedicated focal-plane
  radiator).
- Readout: Sample-Up-the-Ramp (SUR). Frame time 1.5349 s. Exposure (integration) time 113.58 s (XPOSURE);
  elapsed time start-to-stop TELAPSE ≈ 118.19 s (includes discarded frames). Pixel scale: 6.15″ × 6.15″.
- Onboard Video8 ASICs perform low-noise readout, real-time photocurrent estimation, onboard compression.

**Survey strategy and spectral accumulation (Sec. 1.4)**: Survey Planning Software (SPS, built by Arizona
State Univ.) plans observations on the fly to satisfy Sun/Earth/Moon/shuttle-glow avoidance while maximizing
sky coverage and science time; also manages SAA outages and downlink pauses. One main target list spans
All-Sky Survey + two Deep Fields, organized into **target groups**: 17 pointings at fixed ecliptic longitude,
spaced by one LVF spectral-channel width in ecliptic latitude — completing a group yields full spatial
coverage in one spectral channel. Target groups tile into latitude rings (with overlap for pointing-error/
distortion mitigation) that together tile the whole sky.

Observatory position angle (PA) alternates 0°/180° with ascending/descending orbit half for solar-panel
illumination, and this PA, together with elapsed mission time, **defines the four Surveys**:
- Survey 1: t=0–12.5 mo, PA=0°
- Survey 2: t=0–12.5 mo, PA=180°
- Survey 3: t=12.5–25 mo, PA=0°
- Survey 4: t=12.5–25 mo, PA=180°

Header keyword `SPS_PA_ECL` (with `SPS_LON_ECL`, `SPS_LAT_ECL`) records the planned boresight pointing and
lets users classify an exposure by survey. Surveys 3/4 target lists are shifted from Surveys 1/2 by **half a
spectral channel** (~6′ on sky per the header-keyword text) to Nyquist-sample the spectrum when data are
combined across the mission.

**Deep Survey**: two fields — north ecliptic pole, and a field near (offset from) the south ecliptic pole to
avoid foregrounds/bright stars — using a separate, highly overlapping tiling pattern generated by a dedicated
tool (not the All-Sky target-group machinery), exploiting the sky rotation seen at the poles from the
sun-synchronous orbit.

**Survey-plan naming**: e.g. `2025W20_2B` = week 20 of 2025, second half of week (`1`/`2`), version letter
(`A`,`B`,…). First plan of the science survey is `2025W17_4B` (note the `4`).

**Science targets/archive yield** (Sec. 1.1): ≳1×10⁹ galaxy spectra, ≳4.5×10⁸ galaxy redshifts, ≳1×10⁶ quasar
spectra, ≳1×10⁸ stellar spectra, ≳6×10⁵ exoplanet target stars, ≳7×10⁵ ice-absorption spectra, ≳1×10⁵
asteroid/comet spectra. Target σ(f_NL) ≤ 1.

## 2.1 Releases and pipeline versions

Calibrated spectral images available at IRSA within **60 days** of acquisition. Full pipeline reprocessing after
Year 1 (Survey 1+2 → **DR1**) and Year 2 (Survey 1–4 → **DR2**). An interim QR2 reprocessing was also done
(without a full-reprocessing plan originally) covering start-of-survey through October 2025, using pipeline
versions **6.4–6.5.6**; users are told not to mix QR1 and QR2 files (file lists differ). DR1/QR3 correspond to
pipeline **R7.0+**; QR3 covers Survey 3/4 data, with the first weeks (2026-05-16 to 2026-07-19) initially
processed with 6.5.6 pending re-release with DR1 (late fall 2026). Caution advised mixing QR2 (old gain) and
QR3 (new gain) — a **Flux Corrections** calibration product (Sec. 4.3.4) gives per-pixel scale factors to
reconcile them.

**Full pipeline version table (Table 4)**:

| Version | Description |
|---|---|
| 6.2.1 | Initial version, calibrations from IOC + early science survey |
| 6.2.2 | Processing-infrastructure changes only, no change to calibrated images |
| 6.2.4 | Updated PSF model |
| 6.3.0 | Updated proper-motion application for astrometry/source masking |
| 6.4.0 | QR2 baseline: updated PSF model, absolute gain, nonfunctional-pixel map, spectral WCS and WAVE-WCS layer, variance map, persistence parameters; added spacecraft position/velocity to header; updated Reference Catalog |
| 6.5.3–6.5.5 | (applies to QR2 data after 2025-12-15) Fewer fine-astrometry failures; new blooming/snowball/CR-halo flags; persistence changes; beamsplitter-ghost masking; updated nonfunctional-pixel map |
| 6.4+psffix1 – 6.5.5+psffix1 | Retroactive fix of PSF FITS-layer header ordering bug |
| 6.5.6 | Native fix of PSF-layer header ordering |
| 7.0–7.2 (**R7**) | Major DR1 update: Persistence Masks, Bad Pixel Flagging, Fine Astrometry, Outlier Pixel Detection, Zodi Prediction, Photometric Measurements, PSF derivation all revised; absolute gain and spectral WCS updated |

Pipeline version is recorded in the `VERSION` header keyword.

## 2.2 Spectral images

**Filename convention** (Table 3), e.g. `level2_2025W22_2B_0001_1D3_spx_l2b-v4-2025-152.fits`:
`Observation ID` = `SurveyPlanningPeriod_LargeSlewCounter_SmallSlewCounter` (large slew starts at 0000, up to
4 small slews per large slew, small slew starts at 1) + `Detector#` (1–6) + `ProcessingTime` (day-of-year).

**Data format**: Multi-Extension FITS (MEF), 6 HDUs = 5 image extensions + 1 binary table, each 2040×2040
unless noted:
- `IMAGE`: calibrated surface brightness, **MJy/sr**.
- `FLAGS`: per-pixel bitmask (Sects. 3.2.5, 3.2.9, 3.2.10; Table 16).
- `VARIANCE`: per-pixel variance, **(MJy/sr)²** (Sect. 3.2.3).
- `ZODI`: model-estimated zodiacal light background, **MJy/sr** (Sect. 3.2.11). **Not subtracted** from IMAGE.
- `EPSF`: oversampled ePSF cube, 441 rows (21×21 grid) for Detectors 1,2,4,5,6; 451 rows (11×41 grid) for
  Detector 3; normalized to unit integral, dimensionless (Sect. 4.2.3).
- `WCS-WAVE`: binary table (3 cols, 1 row), approximate pixel→(central wavelength, bandwidth) lookup;
  suitable for visualization only — use the standalone Spectral WCS files (Sect. 4.3.1) for science.

File size ≈ **67 MB** per spectral image.

**PSF header-ordering bug** (context, already covered by prior survey but restated for completeness): PSF cube
planes stored in increasing-x order but header claimed increasing-y order; up to ±5% photometry error at
worst (corners). QR2 files corrected as of 2026-03-31 (suffix `+psffix1` for pipeline 6.4–6.5.5; native fix at
6.5.6+). Does not affect QR3/DR1.

**Key header content** (see Appendix A table below for the itemized dictionary): observation ID, detector
number, product creation time, exposure start (UTC) and duration, WCS + SIP distortion, calibration-product
IDs used, approximate pixel↔wavelength map, spacecraft/telescope temperatures, planned boresight pointing
(`SPS_LON_ECL`, `SPS_LAT_ECL`, `SPS_PA_ECL` — same across all 6 bands of an observation), calibrated
`CRVAL1`/`CRVAL2` (RA/Dec), and full processing-module/software-version history. Long keywords use the
**HIERARCH** convention (ESO-origin) to exceed the FITS 8-char limit.

## 2.3 Image anomalies and features

### Anomalies (optics/detector/particle-driven)
- **Frame edge ghost**: sources focused into a narrow "frame edge" region just outside the FoV scatter light
  into the active area; roughly triangular, can appear from any of the 4 detector edges; left/right-edge
  ghosts can recur across a sequence of small slews due to precise repositioning.
- **Linear bright source ghost**: very bright sources off the top/bottom of the detector produce linear
  ghosts; stronger at longer wavelengths; independent of exact source position.
- **Beam splitter (DBS) ghost**: very bright sources reflect off the DBS, producing a ~10′-diameter disk;
  strongest near the Band 3/4 wavelength boundary (the DBS transition), but present at lower level in Bands
  3–6.
- **8° ghost**: stray-light artifact from very bright stars ~8° from field center, seen in a fraction of
  exposures in Bands 2–6.
- **Moon stray light at detector edge**: excess emission at left/right edges in a fraction of Band 1, 4, 5, 6
  exposures, attributed to Moon illumination of the telescope assembly.
- **Extended cosmic-ray (CR) signatures**: essentially every image has CR hits; most affect 1 pixel and are
  removed onboard above ~100 photoelectrons via transient detection. Neighboring-pixel effects arise from
  electrical crosstalk or (rarer) grazing/high-energy/shower events. **Snowballs**: large round CR/particle
  events with a flagged core (OVERFLOW+TRANSIENT) and an extended *unflagged* halo — addressed by new R7
  flags (Sec. 3.2.1).
- **Cosmic-ray-induced glow**: faint diffuse glow correlated with transient fraction; strongest in Bands 1–2
  with a spectral gradient (more on long-λ side); weak in Bands 4–6 but with a brighter rim at the 4 detector
  edges.
- **Crosstalk** (3 types, Fazar et al. 2026): (1) negative image of a bright source displaced ~32 rows (slow/
  row direction, matches NSKIP row-chopping parameter); (2) smear from slowly decaying response to a bright
  pixel at end of prior row; (3) crosstalk between readout channels spaced by multiples of 64 pixels
  (horizontal/fast-read direction). R7 flags types 1 and 2 (`CROSSTALK` bit); type 3 masking is defined but
  **not implemented** in R7.

### Features (atmospheric/non-astrophysical)
- **Atmospheric He line** at 1.083 µm (Bands 1–2): surface brightness factor few to ×30 above ZL; varies over
  orbit/time; astrophysical sources remain visible through it; strong enough to produce weak spectral-leak
  features in Band 1 (~0.84 µm) and Band 2 (~1.49, 1.25 µm). Amplitude/fit recorded in header (`HE_AG_*`
  keywords) but **not subtracted** from IMAGE (though it *is* removed from images used to build the flat
  field).
- **Auroral emission lines** (mainly Bands 1–2, occasionally 3/4/5): from excited N₂ etc.; stronger near
  poles/high solar activity; generally fainter than He line but up to a few × ZL.
- **Other atmospheric lines** at 0.78, 0.84, 0.93, 1.13, 1.81, 2.63, 2.75, 4.03, 4.64 µm (variable amplitude).
- **Shuttle glow**: atomic-oxygen ram-direction surface excitation glow; mitigated by survey-plan ram-angle
  limits; 1D template built during commissioning (correlated only for Band 5 in R7).
- **Diffuse optical transients**: ~1% of exposures show diffuse ephemeral features (foreground objects/
  particles transiting near FoV).
- **Earth-orbiting satellites**: streaks; brightest ones flagged onboard as transients and may carry
  `SATELLITE_HALO`; fainter streaks flagged by outlier module as `STREAK`; near-noise streaks may be
  unflagged.

A curated list of heavily contaminated images is maintained at
[SPHEREx anomalous images list](https://spherex.caltech.edu/page/anomalyimages).

## 2.4 Known limitations

- **Incorrect source masking**: mask size is set from the Reference Catalog magnitude; if that estimate is
  wrong the mask is too large or too small.
- **Pixels at the dichroic edge**: rows on the long-λ side of Band 3 and short-λ side of Band 4 have reduced
  sensitivity/altered spectral response from the DBS. Pixels with throughput <50% get the `DICHROIC` flag
  (Table 16). Gain calibration accounts for reduced throughput, but noise is higher and photometric
  calibration less certain there — caution advised for sources in these regions.

## 3 Processing steps

Pipeline levels: **L0** (raw telemetry ingest/decompression/QA) → **L1** (engineering units, e⁻/s) → **L2**
(photometrically + astrometrically calibrated spectral images = QR products) → **L3** (forced photometry
catalogs at reference positions) → **L4** (redshifts, ice columns, deep mosaics — SST-developed). This
document covers L1–L3 plus calibration derivation.

**L0/L1 (Sec. 3.1)**: onboard warm electronics compute per-pixel slopes, compress/packetize; downlinked via
Ka-band (~5×/day) through NASA NSN; SSDC ingests via DAPHNE (science, Ka) and GDS (engineering/nav, S-band).
Coarse astrometry from survey plan + geometric offsets, accurate to **2′–10′** (few-degree rotation), later
refined by Fine Astrometry (Sec. 3.2.8). An 8×34-pixel subregion is extracted each exposure to validate SUR
noise performance. ADU→e⁻/s conversion. Some pixels set to NaN at L1 if the onboard error bit + early-overflow
or SUR_ERROR flags are set. Amplifier-chain-drift correction using reference/phantom pixels. Atmospheric
line templates (He, aurora, shuttle glow) are cross-correlated with the image at L1 and the fit results stored
in the L2 header (**not subtracted** from the data, except He line is removed before flat-field construction).

### 3.2.1 Source Blooming, Snowball and Transient Halo Flagging

**Physical picture**: blooming = charge spillover from a saturated pixel into neighbors, changing their slope,
causing early transient flags to cascade outward (Bands 1–3 especially). Snowballs/large CRs = sudden,
large, roughly circular charge deposits (radioactive decay or energetic CR); also trigger excess photocurrent
in neighboring pixels below the detection threshold (crosstalk/IPC). Bright satellite streaks similarly
saturate pixels and generate a glow/halo around the track. Both blooming and snowball/CR-shower cores also
produce **excess persistence current** in subsequent images (Sec. 3.2.4); ordinary smaller CRs/satellite
tracks do not.

**Inputs**: L1 flag layer, slope-fit image, header keywords `DETECTOR`, `TELAPSE`. Fluence = slope (e⁻/s) ×
TELAPSE (s). Band-dependent overflow-fluence thresholds F_over (Table 5): **50,000 e⁻** (Bands 1–3), **30,000
e⁻** (Bands 4–6). `TRANS_FRAC` = `N_TRANSIENT` / (2040×2040).

**Output flags** (4 new): `BLOOM`, `SNOWBALL`, `HALO`, `SATELLITE_HALO`.

**Algorithm — Step 1 (identify Blooming/Snowball)**: only uses functional (non-`NONFUNC`) pixels in the
2040×2040 active region. Flag-combination labels (Table 6): NON_FLAG(000), EARLY_TRANSIENT(TRANSIENT=1,
SUR_ERROR=1), LATE_TRANSIENT(TRANSIENT=1 only), ONLY_OVERFLOW(OVERFLOW=1), EARLY_OVERFLOW(OVERFLOW=1,
SUR_ERROR=1), LG_EARLY_TRANS(all 3=1), LG_LATE_TRANS(TRANSIENT=1,OVERFLOW=1). Contiguous saturated **CORE**
pixels identified first, then **MANTLE** pixels found by outward search:
- CORE_BLOOM_PIXELS (Table 7): ONLY_OVERFLOW ≥ F_over; EARLY_OVERFLOW (any); LG_EARLY_TRANS ≥ F_over.
- MANTLE_BLOOM_PIXELS (Table 8): ONLY_OVERFLOW ≥ F_over; EARLY_TRANSIENT ≥ 0.2×F_over; LATE_TRANSIENT ≥
  0.1×F_over.
- Blooming sources: circular shape, decreasing signal outward, larger than background.
- Snowball sources (Table 9, 4 types by core/mantle label combination): CORE_SNOW_PIXELS + MANTLE_SNOW_PIXELS
  of the same type; typically approach background level outside the transient region.
- For `TRANS_FRAC > 0.1` (`HIGH_TRANS` images), extra restrictions apply (circularity, fluence-range and/or
  radius limits, currently capped at **25 pixels**) — can still occasionally yield square bloom regions and
  inflated predicted persistence in these edge cases.

**Step 2 (Non-Overflow Bloom Flagging)**: catches TRANSIENT-only pixels without OVERFLOW (sub-pixel jitter,
variable star, brighter-fatter pre-saturation charge repulsion). Searches remaining pixels for contiguous
EARLY+LATE TRANSIENT groups (Table 10: type 1 EARLY_TRANSIENT ≥0.5 F_over; type 2 EARLY_TRANSIENT ≥0.1
F_over; type 3 LATE_TRANSIENT ≥0.1 F_over), prioritizing greatest fluence; `HIGH_TRANS` images and
`NONFUNCT`/already-`BLOOM`/`SNOWBALL` pixels excluded.

**Step 3 (Transient Halo Flagging)**: three cases —
1. *Snowball halo*: for a group of n_SNOW pixels, centroid of OVERFLOW-flagged pixels found; halo (excess
   current >0.1 e/s) extends to radius **r_HALO = √(2 × n_SNOW)** (Eq. 1); all pixels within radius →
   `HALO`.
2. *Saturating satellite halo*: if the centroid-to-furthest-pixel distance exceeds r_HALO from case 1, treat
   as a saturating satellite track: compute skeleton of overflow track, distance map to nearest track edge
   r_edge(s) along the skeleton, and apply a halo proportional to cross-skeleton distance → `SATELLITE_HALO`.
3. *Remaining transient flagging*: for any pixel with TRANSIENT set that is not BLOOM/SNOWBALL, flag its 4
   edge-adjacent neighbors `HALO`.

### 3.2.2 Nonlinearity Correction

Charge accumulation reduces gain (declining response) as an H2RG pixel fills. SUR is designed so slope fits
use only samples below the Overflow threshold (~half full well). In that range the response is quadratic:
Q_observed = Q_collected (1 − Q_collected/Q_nl) (Eq. 2). Typical **Q_nl = 1.4×10⁶ e⁻ (Bands 1–3)**, **0.8×10⁶
e⁻ (Bands 4–6)**; correction factor **1.05–1.08** for full-length exposures reaching Overflow at the end. The
corrected photocurrent F is solved from Eq. 3 (involves T_fr≈1.53 s [frame time], SURDLY=3 [first used
frame], N [last used frame, up to SURLIM=77 for uninterrupted SUR]). For overflow-interrupted SUR, N is
solved iteratively (Eq. 4). If `SUR_ERROR` is set, **no correction applied** (F=F′). If `TRANSIENT` is set,
N is estimated. Pixels with low-confidence NL correction get the `NONLINEAR` flag.

### 3.2.3 Variance Map

Based on Robberto (2007) SUR variance framework. Inputs: L1 image (2072×2176, includes phantom pixels +
repeated reference-row samples, e⁻/s), a 2048×2048 per-pixel electronic-noise map (e⁻, from CDS noise +
measured excess readout noise; **dark-current shot noise excluded** — dark not subtracted at this stage), and
accompanying flag map. Output: variance map, same 2072×2176 shape, units (e⁻/s)²; final calibrated
`VARIANCE` layer delivered to users is 2040×2040, **(MJy/sr)²**.

**Formula** (Eq. 6, replacing the theoretical Eq. 5 readout term with the lab-measured per-pixel variance):

Var = σ²_det(i,j,N) + [6(N²+1) / (5(N²−1))] · F · T_int(N)

where σ²_det(i,j,N) is measured per-pixel electronic noise variance for N reads, F is measured slope, T_int(N)
is integration time for N reads. To get slope variance, divide the *total-signal* variance (Eq. 5/6 form)
by T_int(N)².

Special cases:
- **Overflow**: N inferred from measured flux + overflow threshold; substituted into the Poisson term;
  electronic-noise term neglected since photon noise dominates.
- **Transient interruption**: actual usable-read count unknown → conservatively use the per-pixel electronic
  variance for the *minimum* possible N.
- If both `OVERFLOW` and `TRANSIENT` set: use the overflow prescription (photon noise dominates).

### 3.2.4 Persistence Masks

Physical model: H2RG persistence from charge traps in the diode depletion region (Smith et al. 2008),
releasing charge slowly after reset. Persistence current modeled as sum of exponentials (Eq. 7):

I_p(t) = Σ_n A_n C_n e^(−t/τ_n), typically **6–8 terms**, with C_n chosen so ΣC_n (A_n=1) ≈ 1/(t+1).

Coefficient A_nm for exposure m (Eq. 9) sums decayed contributions from exposures m−1 and m−2 via lookup
functions B_n, B_n′ of prior fluence and elapsed time, recursively updated exposure-to-exposure (Eq. 10). The
predicted persistence current for exposure m is evaluated at the exposure's temporal midpoint t_m =
t_slew(1→0) + ½t_int (Eqs. 11–12).

B_n(F) piecewise (Eq. 13): 0 for F<0; **r×F** for 0≤F≤F₁; **r₁×F + F₁(r−r₁)** for F₁≤F≤F_sat; **I_sat** for
F>F_sat — i.e. zero / linear / approaching-saturation / saturated regions, band-dependent rate r and
saturation level I_sat.

**Flag-driven fluence overrides** (Table 14) — important because fluence = flux×elapsed-time is often wrong
for saturated/transient pixels:

| OVERFLOW | SUR_ERROR | TRANSIENT | SRC_BLOOM | SNOWBALL | Interpretation | Overwrite F with F_sat? |
|---|---|---|---|---|---|---|
| 1 | 1 | 0 | 0/1 | 0/1 | Early Overflow | YES |
| 1 | 1 | 1 | 1 | 0 | Early Bloom | YES |
| 1 | 1 | 1 | 0 | 1 | Early CR Center | YES |
| 1 | 0 | 1 | 0 | 1 | Late CR Center | YES |
| 1 | 0 | 0 | 1 | 0 | Source Overflow | NO |
| 1 | 0 | 0 | 0 | 1 | Very Early CR center | YES |
| 0 | 1 | 1 | 1 | 0 | Source Blooming | NO |

Diagnostics generated: total pixels flagged persistent per frame; cross-correlation with previous exposure
(with/without mask applied); auto-correlation of current exposure (to detect residual bright-source
artifacts from before integration started).

### 3.2.5 Bad Pixel Flagging

Per-exposure, per-detector coded flag map (not a simple binary mask) — see full **Table 16** flag dictionary
already captured in the prior survey; key additions/clarifications from this pass:
- `NONFUNC` (bit 6): static pre-flight dead-pixel map, periodically updated, unusable for any purpose.
- `DICHROIC` (bit 7): dark-corner pixels in Bands 3/4 with incompatible bandpass for their side of the DBS
  ("smile" effect); low throughput, not usefully calibratable.
- `MISSING_DATA` (bit 9): onboard data lost before SSDC ingest (e.g. uncorrected corrupted downlink packets).
- `HOT`/`COLD` (bits 10/11): per-exposure noisy/anomalously-low pixels (permanent versions are `NONFUNC`).
- `FULLSAMPLE` (bit 12): informational only, part of rotating 8×32 full-readout region.
- `PHANMISS` (bit 14): missing phantom pixels prevent correction.
- `NONLINEAR` (bit 15): unreliable NL correction — exclude from most science.
- `PERSIST` (bit 17): persistent charge above L2 threshold.
- `OUTLIER` (bit 19), `CROSSTALK` (bit 20), `SOURCE` (bit 21), `GHOST`/`GHOST_FPA`/`GHOST_EXT` (bits 22/23/24
  — `GHOST_FPA` unused in R7, subsumed into `GHOST_EXT`, to be removed Year 2), `STREAK` (bit 25),
  `BLOOM`/`SNOWBALL`/`HALO`/`SATELLITE_HALO` (bits 26–29).

### 3.2.6 Dark Subtraction

Dark current (e⁻/s), derived jointly with the flat-field response (Sec. 4.2.1), is subtracted from the
2040×2040 active region of the L1 image prior to the gain multiply.

### 3.2.7 Absolute Gain Correction

Dark-subtracted L1 image × Absolute Gain Matrix (2040×2040, units **(MJy/sr)/(e⁻/s)**, Sec. 4.1.1) →
MJy/sr. Note SPHEREx **combines flat-field and photometric gain into one product** (no separate flat file)
because of within-band wavelength variation.

### 3.2.8 Astrometry

**Inputs**: spectral images (coarse WCS from L1, accurate to a few arcmin), a prior distortion map (ground-
test-derived for the first pipeline run; from R6.5+ the **median of hundreds of empirically measured
distortion maps**), and the proper-motion-corrected **Gaia DR3** catalog with predicted SPHEREx fluxes (via
matching to WISE/2MASS photometry). Calibrator pre-selection: non-saturated, high-S/N, spatially isolated.

**Output**: refined WCS/SIP coefficients per detector + `FINAST` flag (0=good, 1=partial [corner offsets of
a couple pixels from a degraded distortion fit], >1=poor/unusable).

**Algorithm (Fig. 15 pipeline)**: (1) initialize with L1 coarse WCS + prior SIP; (2) run Astrometry.net
`solve-field` on `sep`-extracted sources (100σ threshold) with SIP order-3 polynomial, CRPIX=(1020.5,1020.5),
using 4100/5200 index files (Gaia DR3 + 2MASS) → ~arcsec accuracy; (3) select N=2,000–10,000 brightest
calibrators (adaptive magnitude limit) requiring: `astrometric_params_solved ≥ 31` in Gaia, S/N>10 but not
saturated in Gaia RP, izy, JHKs, WISE W1/W2, and no neighbor within 2 SPHEREx pixels brighter than 10% of the
calibrator flux; (4) SExtractor source extraction on the image, iterated to match calibrator density within
20%; (5) **scamp** run iteratively on calibrator+SExtractor LDAC catalogs to derive final WCS+TPV distortion,
converging on contrast parameter + RMS RA/Dec (good <1″), or max-iteration cutoff; (6) TPV→SIP conversion via
`wcs-sip2pv`; (7) write final WCS+SIP + `FINAST` to header.

**R7 astrometry retry module**: runs for images with `FINAST≠0` (≈1–3% of all main-module outputs). Seeds
chosen by priority: (i) same detector, adjacent small slew; (ii) dichroic detector pairs in same small slew
(1/4, 2/5, 3/6); (iii) any detector, same small slew. Focal plane treated as rigid body to transfer astrometric
priors + distortion from seed to failed image; main module rerun. Reduces failure rate to **sub-percent**.
New header keywords: `WCSRETRY`, `RETRY_WCSMODE`, `WCSSEED`, `WCSSEEDOBS`.

**Performance**: RMS <0.3″ (Fig. 20, Detector 3, excluding SAA and images with >300,000 `N_TRANSIENT`
pixels), no significant center-vs-corner degradation. Max distortion in corners ~13 px (~80″); 1 px≈6.15″.
Large-distortion corrections up to 15 px (~90″) in image corners overall.

### 3.2.9 Source Masks

**Inputs**: spectral image + WCS, a mini-catalog (from Reference Catalog + Solar System object catalog)
including sources within **0.5° of array boundaries** (for edge/ghost sources), SUR flags. **Output**: binary
mask array, folded into the FLAGS layer.

**Unresolved-source masking**: only sources with `spherex_class` bit value ≤7 are masked (stars/compact
galaxies); **resolved objects (large nearby galaxies, planetary nebulae) are NOT masked** — directly relevant
to PSB extraction. Radius r(m) modeled as a smoothly-blended double-exponential (Eqs. 14–15) with
detector-dependent fit parameters (Table 19: a1,b1,a2,b2,m0,w per band). Pixels with ≥20% area inside the
circular region get `SOURCE`. **Default faint masking limit: 19 AB mag** (fainter sources not masked).

**Electrical crosstalk masking**: Type 1 (row-chopping vertical ghost, SWIR only, threshold **0.3 e⁻ s⁻¹**)
and Type 2 (channel-coupling horizontal ghost, all arrays, threshold **0.3 e⁻ s⁻¹**) implemented via
calibration lookup tables → `CROSSTALK` bit. Type 3 (channel-boundary streak, MWIR) defined but not yet
implemented in R7.

**DBS ghost masking**: reflections from bright sources (**≥100 Jy**) modeled via a linear-transform geometric
model (Eqs. 16–18: x_g = x_s + α_xx x_s + α_xy y_s + α_ox, similarly for y), evaluated per band/region:
- **Band 3**: edge-region ghosts only (near DBS discontinuity), ROI −52<x_s<2092, −250<y_s<175; B=100 Jy in
  H-band; (α_xx,α_xy,α_ox,α_yx,α_yy,α_oy,r) = (−0.0051, 0.0013, −5, 0, 0, 225, **52**) — Table 21.
- **Band 4**: both main-field (ROI −52<x<2092, 52<y<2261; B=3000 Jy H-band; r=52 — Table 22) and edge-region
  ghosts (ROI −52<x_s<2092, 1760<y_s<2040, uses Table 21 model); plus for B>3000 Jy an entire strip
  −52<x<2092, y>1920 is masked for an optical-bleeding effect.
- **Band 5, 6**: main-field ghosts only, very brightest sources (**B=10,000 Jy** H-band), ROI −52<x<2092,
  52<y<2265, r=52 (Table 22).
- **Bands 1, 2**: no DBS ghosts.
- Ghost from a source on the same array → `GHOST`; ghost from a source on a different array (or outside FoV)
  → `GHOST_EXT`.

**Frame-edge-ghost masking** (Table 20): source brightness threshold **m_AB ≤ 11**; mask length =
11[25,000·10^(−m_AB/2.5)] + 24 pixels; mask width = 2[4[25,000·10^(−m_AB/2.5)]+1] pixels.

### 3.2.10 Outlier Pixel Detection

**Inputs**: spectral image, `SOURCE` mask, bad-pixel mask, variance. **Algorithm**: median-filter the image
to suppress mean/low-frequency structure; apply SOURCE + bad-pixel masks; among remaining pixels, flag
isolated statistical outliers (`OUTLIER`) directly, and separately find streak seeds (lower sigma threshold
than isolated outliers, to catch marginal tracks) using a ZTF-pipeline-like approach (Laher et al. 2014):
group neighboring seeds, fit linear model for length/width/aspect/orientation, keep elongated line-like
groups as streak fragments, then link co-linear adjacent fragments into tracks → `STREAK`.

### 3.2.11 Zodi Prediction

`ZODI` layer = per-image **median** ZL estimate, MJy/sr, **not subtracted** from IMAGE. First-guess model:
modified Kelsall et al. (1998) interplanetary-dust model (updated with Planck data), combined with Tsumura et
al. (2013) spectral measurements (details in Crill et al. 2025). **The Kelsall model captures the spatial/
temporal ZL variation well but systematically underestimates amplitude.** A **wavelength-dependent scaling
factor** was derived by cross-correlating model predictions against actual SPHEREx measurements at |b|>30°
(Year-1 data, where sky is assumed ZL-dominated modulo DGL/IGL contributions); a **median scaling factor per
wavelength** across all such exposures is applied, and the resulting per-wavelength all-sky calibration is
what is baked into the `ZODI` layer. The scaling factor itself is separately available as the `zodi_scaling`
calibration product (ECSV, one file per band; Sec. 4.3.4) — this is the artifact to consult if one wants to
back out the raw Kelsall prediction or apply a different scaling.

### 3.2.12 Level 2 DQA

Automated per-image sanity checks (11 tests): Nonlinearity (no pixel corrected >50%), Variance (in expected
range), Persistence (≤20% of pixels `PERSIST`), Bad-Pixel Mask (≤1% flagged), Source Count (in expected
range), Source Mask (masked-pixel count <3× source count), Outlier Pixels (`OUTLIER` count within factor 2 of
already-flagged total), LVF layers (all present/attached), Missing-Value Pixels (all NaN/Inf flagged),
Distortion (median pixel solid angle in range), Astrometry (`FINAST=0`). **PASS grade requires ≥6/11
successful.**

**Archive inclusion criteria** (all three required): `N_TRANSIENTS < 435,000`; not within defined SAA
boundaries; `FINAST = 0`; `L2DQA = PASS`. Because DQA is per-band, some observations lack all 6 bands in the
archive.

## 3.3 Photometric measurements

Used both to derive the absolute gain matrix (Sec. 4.1.1) and to power the IRSA **Spectrophotometry Tool**.

**Method**: **Tractor**-based (Lang/Hogg/Marbach; [Tractor website](http://thetractor.org)) generative/forward modeling,
maximum-likelihood forced photometry (positions fixed, not floated), analogous in spirit to xID (Hurley et
al. 2017) and T-PHOT (Merlin et al. 2016). Statistical/optimization framework: Hogg et al. (2010) + `emcee`
(Foreman-Mackey et al. 2013).

**Inputs**: spectral images (WCS, dark-subtracted/flat-fielded, MJy/sr), source info (positions; **intrinsic
galaxy morphology optional but supported** for the generative model), ePSF model (position-dependent,
Sec. 4.1.2), variance map, pixel solid-angle map (from distortion), flag maps. A sub-pixel response map is
foreseen but not yet implemented.

**Background handling**: (1) a **global** spectral background computed per full image from unflagged,
source-free pixels and removed first; (2) in the Tractor cutout, a **local** background term is included in
the generative model and fit **simultaneously** with source fluxes.

**Step-by-step algorithm**:
1. Load catalog (positions, flags, optional morphology).
2. Convert RA/Dec → detector (i,j).
3. Build cutout around source(s).
4. Estimate initial local background from a **15×15** region around the cutout, masking known sources.
5. Retrieve position-dependent ePSF for that detector region.
6. Build generative model (positions + morphology + local ePSF + local background).
7. Fit fluxes + local background jointly using cutout data + variance map.
8. Convert Tractor flux → µJy using local pixel solid angle (from distortion map).
9. Record flux, uncertainty, wavelength per source.
10. Inflate uncertainty for irreducible scatter (Note 1, below).
11. Check flagged pixels near each source; propagate flags; add photometry-specific flags (e.g. strong NL,
    saturation).
12. Compute fit-quality metric (Note 2).

**Note 1 — 3% uncertainty floor** (Eq. 19):
σ_reported = √(σ_Tractor² + (0.03·F)²)
— a 3% systematic term added in quadrature, dominant at high S/N; the *image* variance map itself is
unchanged, only the catalog-reported uncertainty.

**Note 2 — fit-quality metric** (Eq. 20): for pixels k within a **2.5-SPHEREx-pixel radius CirclePixelRegion**
of the source, fit_quality = ⟨|p_k − m_k|/σ_k⟩ (p=data, m=model, σ=per-pixel uncertainty); should be ≈1 for a
good fit, larger if something is wrong.

**Flag usage for photometry** (explicit lists given in the text, beyond the general Table 16):
- Flags masking pixels **for background estimation**: OVERFLOW, SUR_ERROR, NONFUNC, MISSING_DATA, HOT, COLD,
  NONLINEAR, PERSIST, OUTLIER, SOURCE, TRANSIENT, BLOOM, SNOWBALL, HALO, SATELLITE_HALO.
- Flags masking pixels **for the photometric fit itself** (note: SOURCE, TRANSIENT, OVERFLOW, OUTLIER are
  *not* in this second list, since the fit needs source pixels and transient/overflow pixels get separate
  handling): SUR_ERROR, NONFUNC, MISSING_DATA, HOT, COLD, NONLINEAR, PERSIST, BLOOM, SNOWBALL, HALO,
  SATELLITE_HALO.
- Output catalog carries a summary warning bit **`CONTAINS_BAD_PIXEL` (bit 32)**: set if any pixel within 2.5
  SPHEREx-pixel radius of the source has any of TRANSIENT, OVERFLOW, SUR_ERROR, NONFUNC, DICHROIC,
  MISSING_DATA, HOT, COLD, NONLINEAR, CROSSTALK, GHOST, GHOST_FPA, GHOST_EXT, STREAK, PERSIST, BLOOM,
  SNOWBALL, HALO, SATELLITE_HALO. It is a conservative warning, not automatic exclusion — use the underlying
  flag bitmask for custom selection rules.

## 3.4 Mosaics

Builds co-added images per spectral channel from L2 images taken at different times/orientations. Powers the
IRSA **Mosaic Tool** and the Year 1/2 all-sky data-cube releases. **The IRSA Photometry Tool does NOT use
mosaics — it uses L2 images directly, and precision photometry should also use L2 images directly.**

**High-level steps**: (1) query/load L2 images covering the region; (2) subtract ZODI; (3) bad-pixel-mask via
FLAGS; (4) per spectral channel, extract pixels via channel template; (5) reproject to common output grid;
(6) accumulate weighted contributions; (7) produce final averaged mosaic. Only **All-Sky Survey** images used
in the initial release; **Deep Field images excluded**.

**3.4.3 Data loading**: `data = IMAGE − ZODI`. Pixels with any of these flags → NaN, excluded:
TRANSIENT, SUR_ERROR, NONFUNC, DICHROIC, MISSING_DATA, HOT, COLD, PHANMISS, NONLINEAR, PERSIST, CROSSTALK,
GHOST, GHOST_FPA, GHOST_EXT, STREAK, BLOOM, SNOWBALL, HALO, SATELLITE_HALO. Propagated (bitwise-OR'd) flags:
OVERFLOW, SOURCE, OUTLIER.

**3.4.4 Spectral channel definition**: each detector divided into **17 standard spectral sub-channels**
(same geometric template for all 6 bands, each band covering a different λ range); contour boundaries follow
iso-wavelength lines (curved, from LVF fabrication) but are **geometric survey-planning coordinates**, not
the exact calibrated wavelength solution. Template array values: **1–17** = channel number; **0 and 18** =
outside nominal channels (edges/corners, non-rectangular excess detector area) — still spectrally
characterized for calibration/QA use. Per (array, subchannel), precomputed stats: WAVELENGTH (median),
WL_MIN/WL_MAX (3σ-clipped min/max), R (median), R_STD, BANDWIDTH (median) — stored in the SPECTRAL_CHANNELS
extension of the calibration product.

**3.4.5 Mosaic grid**: user specifies center RA/Dec, width/height, pixel size (**min 9″**), PA. Output WCS:
odd pixel dimensions both axes (so CRPIX falls exactly at center), CRPIX at FITS 1-based geometric center,
negative CDELT1 (RA increases left), TAN projection. n_x=floor(W·3600/p)|odd, similarly n_y; CRPIX=(n_x/2+0.5,
n_y/2+0.5).

**3.4.6 Reprojection**: histogram-based (Cukierman et al. 2026 §4), i.e. intensity-weighted 2D histogram /
"pixel binning" — each input pixel maps to exactly **one** output pixel (nearest-neighbor rounding after
input-pixel→sky→output-pixel transform), accumulated via `np.bincount`. Properties: O(N) speed, no smoothing,
integer `NHITS`, no induced noise correlation between output pixels, but can leave **gaps** where coverage is
sparse. `mosaic = accumulator/nhits` where nhits>0, else NaN.

**3.4.7 Building process**: file-centric — each L2 file opened once, all 17 channels processed before moving
on (17× less I/O than channel-centric). Accumulation: per file, load image+flags, NaN-mask bad pixels, extract
channel-mask pixels, map to output grid, accumulate `acc_data`/`nhits` for valid pixels and bitwise-OR
`acc_flags` for all (including NaN) pixels; finalize `mosaic = acc_data/nhits`. Implemented with **Numba JIT**
outside the GIL for multi-threaded file loading.

**3.4.8 Output file**: 3D spectral cube FITS with extensions `PRIMARY` (version metadata), `IMAGE` (N,ny,nx;
MJy/sr), `NHITS` (N,ny,nx), `FLAGS` (N,ny,nx; bitwise-OR), `SPECTRAL_CHANNELS` (table, N rows: DETECTOR,
SUBCHAN, WAVELENGTH, WL_MIN, WL_MAX, BANDWIDTH, R, R_STD), `WCS-WAVE` (table, 1 row). Uses FITS `-TAB`
algorithm for non-uniform spectral sampling; WCS has **4 world axes** (RA, Dec, wavelength, bandwidth) though
the image array has only 3 pixel axes.

**3.4.9 Flagging**: bad-flagged pixels → NaN before reprojection, excluded from accumulation and NHITS.
OVERFLOW/SOURCE/OUTLIER propagated by bitwise-OR across contributing images. FLAGS extension header carries
`MP_<FLAG NAME>` keywords giving each propagated flag's bit position (IPAC Firefly visualization convention).

**3.4.10 Known issues** (directly relevant to PSB work using mosaics):
- **Airglow striping**: He line at 1.083 µm creates a bright horizontal band in all Band 1 mosaics (LVF maps
  λ→detector position → fixed-position stripe); temporal/spatial variation across exposures → scan-correlated
  banding in the coadd; can overwhelm faint sources at these wavelengths without mitigation.
- **Extended-source spectral-feature striping**: strong emission/absorption features in extended sources
  (e.g. Brackett-α at 4.052 µm) create analogous horizontal stripes; because scan PA rotates between visits,
  coadding different roll angles produces sawtooth/moiré interference patterns for sharp spectral features
  that **do not average down with more coverage** — fundamental to the LVF's spatial/spectral entanglement.
- **Residual masking incompleteness**: snowball/blooming/halo masking only introduced starting planning
  period 2025W51_1A (Dec 2025, pipeline 6.5) — QR2 images from before that are unmasked for these features.
  Satellite-streak masking incomplete and crosstalk masking absent in QR2 processing. Both promised complete
  after the Year 1 (DR1) release.

## 4 Calibrations

### 4.1.1 Absolute Gain Matrix
FITS image, 2040×2040 per detector, units **(MJy/sr)/(e⁻/s)**, encodes per-pixel gain within a spectral
channel plus inter-channel relative gain. ~16 MB/file. Input to Sec. 3.2.7.

### 4.1.2 ePSF models
No longer measures the "optical PSF" via stacking/deconvolution (pre-R7 method); **R7 measures the effective
PSF (ePSF)** directly, following Anderson & King (2000). Grid: **21×21 zones** for Detectors 1,2,4,5,6;
**11×41 zones** for Detector 3 (finer along dispersion direction — captures birefringence-driven rapid
spatial variation from the DBS). Each ePSF: **33×33 array at 5× oversampling** relative to native pixels,
normalized to unit total flux. Built from stacks of bright, isolated stars over many exposures (stable with
time). Delivered as FITS binary table, one row per zone (grid indices, zone center/extent, N_star, mean
effective-pixel count, representative wavelength, normalized 33×33 image). ~8 MB/file.

### 4.2.1 Absolute gain derivation
**Flat-field/dark**: derived jointly by fitting per-pixel response (e⁻/s) against the reference flux from the
**median brightness in the pixel's spectral channel** across many images (**510 nominal spectral channels per
detector** used for this fit — note: distinct from the 17-subchannel mosaic-template count), plus a linear
tilt per channel for zodiacal-background changes with solar elongation. Only pixels without significant
source flux used. Slope → flat field; intercept → dark current (e⁻/s). Derived independently from 4 groups
of survey exposures (~4,000 images/detector/group) spanning the observing period; found stable; combined into
one final solution. An additional step restores **large-scale modes from lab dark-current measurements**
into the flight-derived dark maps (regression removes broad modes resembling the spectral-channel
decomposition) while preserving flight-derived small-scale S/N.

**Absolute gain**: from repeated observations of primary spectrophotometric calibrators. For each
observation: invert the *previous* gain matrix + local pixel solid angle to recover measured detector count
rate; predicted flux from CALSPEC stellar model integrated through the SPHEREx transmission profile (Eq. 22)
converted to surface brightness via detector-average pixel solid angle; ratio gives G_meas = I_ν,pred /
(e⁻,s⁻¹)_meas (Eq. 21). **~54,000 individual measurements of 17 primary calibration stars** compared against
updated HST/JWST stellar models (**CALSPEC**: Bohlin et al. 2014, 2017, 2022). Measurements grouped by
wavelength, running median computed, adaptively smoothed, fit with a **monotonic piecewise cubic (PCHIP)**
interpolator, evaluated on the detector wavelength map → 2D gain solution; divided by flat-field response →
final absolute gain matrix. Near the dichroic transition (rapid gain change with λ), only DICHROIC-flagged
measurements are retained with a more local interpolation.

**Calibrator saturation/SNR criteria** (Table 25, AB mag / µJy per band):

| Band | λ range (µm) | Saturation mag (Flux µJy) | 50σ threshold mag (Flux µJy) |
|---|---|---|---|
| 1 | 0.75–1.11 | 11.50 (91,200) | 14.74 (4,610) |
| 2 | 1.11–1.64 | 11.50 (91,200) | 14.79 (4,410) |
| 3 | 1.64–2.42 | 11.30 (109,600) | 14.61 (5,200) |
| 4 | 2.42–3.82 | 11.71 (75,200) | 14.85 (4,170) |
| 5 | 3.82–4.42 | 10.19 (304,800) | 13.46 (15,000) |
| 6 | 4.42–5.00 | 9.75 (457,100) | 13.17 (19,600) |

**Standard star set** (Table 26): 17 stars total — 3 primary HST white-dwarf calibrators (BD+29 2091,
1802271, Feige110 are listed among the set; text calls out "three primary HST calibrators...all white dwarfs,
very blue" — G191B2B, GD71, GD153 explicitly the classic CALSPEC trio), JWST Cycle-1 NEP EBL-field targets,
and others; systematic uncertainty per star **1% to 2–4%** depending on star.

**Calibration uncertainty**: dominant systematic is the HST/CALSPEC standards' own systematics, ~**1% or
less** averaged over stars. For most SPHEREx channels, **absolute flux calibration accurate to <1%** relative
to these references (Ashby et al. 2026, in prep, for full detail).

### 4.2.2 Astrometric calibration derivation
(Largely duplicative of Sec. 3.2.8 but with historical context.) Coarse pointing extrapolated from Detector 5
grid using an average focal-distortion map; R6.5+ added shift/rotation corrections from true pointing,
**>2× better coarse-astrometry accuracy** than pre-6.5. Iterative calibrator/extraction approach handles
star-density variation of **100–1000×** between galactic bulge and extragalactic fields, giving **<3%
failure rate**; most failures from excessive transient-flagged pixels. R6.5+ improvements: more efficient/
more iterations for failed exposures, plus an added loop applying transient flagging + brightest-star
restriction for still-failed cases → 2× reduction in failures (mostly galactic-plane). R7 retry module
(seed-based) → sub-percent failure level.

### 4.2.3 PSF measurement
Adopted **ePSF over reconstructed optical PSF** after testing showed systematically lower forced-photometry
fit residuals with ePSF, and demonstrated time-stability across independent planning periods.

**Inputs**: L2 LVF exposures (2040×2040, MJy/sr), Fine Astrometry solutions, Gaia DR3 candidate stars (bright,
isolated, high-S/N, proper motions known, not affected by nonlinearity; flagged-pixel measurements rejected).
A local background from a Tractor-model fit to each cutout is subtracted before reconstruction (found to
significantly affect ePSF fidelity). Several hundred clean stellar measurements per zone across many spectral
images. Iterative ePSF builder (photutils `EPSFBuilder`, based on Anderson & King 2000 formalism): initial
oversampled model estimated from ensemble → evaluated at each star's measured position → compared to native
pixel data → model updated → repeat to convergence/iteration limit. **No explicit deconvolution of the
detector-pixel response** (unlike the old optical-PSF method) — the ePSF directly represents Eq. 24: D_j = F·
P_eff(x_j−x⋆, y_j−y⋆) + B_j + N_j.

**Effective size N_eff** (Eq. 25/26): N_eff = 1/Σ P_j² for a unit-normalized model — an empirical PSF-size
metric, directly tied to expected PSF-weighted photometric uncertainty. Reported as `NEFF_MEAN`, averaged
over Monte Carlo realizations at random sub-pixel positions (since native-pixel flux distribution depends on
sub-pixel centroid). `NSTAR` also recorded per zone. Values vary by detector/zone/wavelength (Fig. 21); no
single FWHM number is tabulated in the main text besides the header-example `PSF_FWHM` = **8.67″** (median,
for that one example exposure/detector — not a general calibration constant; treat as illustrative only).

### 4.3.1 Spectral WCS
Standalone per-band FITS files: `CWAVE` extension = central wavelength per pixel (where cumulative
transmission reaches 50% of total area — i.e. the *median* of each pixel's transmission curve, not simply
its peak); `CBAND` extension = bandwidth = CWAVE / measured spectral resolution. **These CWAVE/CBAND
extensions are what should be used for science analysis** — the in-image `WCS-WAVE` lookup table (WAVE-TAB
WCS, piecewise-bilinear compact model) is for visualization only. QR2 files after planning period 2025W25_2A
list a consistent spectral-WCS reference; the spectrophotometry tool switched to the QR2 CWAVE values on
2025-12-17. Table 28 in the doc gives the full FITS header keyword set for these files (WCSNAME='Approximated
per-pixel wavelength and bandpass', CTYPE1/2='WAVE-TAB', PS1_0/PS2_0='WCS-WAVE' lookup extension, etc.).

### 4.3.2 Spectral Channels calibration product
`spectral_channels_YYYMMDD.fits`: 2040×2040 per-pixel channel-index array (**geometric survey-planning
definition**, not exact wavelength — curvature from LVF fabrication), values 0–18 (1–17 nominal, 0/18 =
edge/corner excess area), same template for all 6 detectors (**one file for all bands**), plus a table of
median band center λ_c, [λ_min, λ_max] (3σ-clipped), and median R per (band, channel). **R7 updated Bands 5
and 6** based on on-sky calibration (wavelength shift). Full reproduced tables (Tables 29–34), channel 0/18 =
corner regions outside nominal design coverage:

**Band 1** (λ 0.741–1.117 µm, R≈37–43): channels 0→18, λ_c from 0.741 to 1.117 µm, R decreasing from 43±1.2
(ch.0) to 37±0.4 (ch.17), rising slightly to 37±0.5 at ch.18.

**Band 2** (λ 1.094–1.654 µm, R≈41–43): λ_c 1.094→1.654 µm; R fairly flat 41–43.

**Band 3** (λ 1.629–2.423 µm, R≈40–42 nominal, but ch.18 R=61±8.6 — edge artifact): λ_c 1.629→2.423 µm.

**Band 4** (λ 2.414–3.831 µm, R≈34–36 nominal, ch.0 anomalous R=55±3.1): λ_c 2.414→3.831 µm.

**Band 5** (λ 3.809–4.429 µm, R≈107–117, notably higher R than Bands 1–4): λ_c 3.809→4.429 µm.

**Band 6** (λ 4.412–5.011 µm, R≈124–135, highest R of all bands): λ_c 4.412→5.011 µm.

(Full per-channel λ_c/[λ_min,λ_max]/R values for all 6 bands × 19 rows [ch 0–18] are captured verbatim in the
source PDF Tables 29–34, pp. 61–64, and can be pulled directly if a machine-readable per-channel table is
needed — not fully reproduced here for brevity, but the envelope numbers above bound each band.)

### 4.3.3 Atmospheric Templates
Three template products, fit at L1, results in L2 header, **not subtracted from data**:
- **Auroral line template** (Band 1 only in R7): FITS image, 2040×2040, filename `aurora_template*`.
- **He emission template** (Bands 1 and 2): two FITS images, filenames `he_template_D<n>*`.
- **Shuttle glow template** (Band 5 only in R7, despite generic description mentioning Bands 1/2 file naming
  quirk in the text): FITS image, filename `shuttle_glow_template*`.

### 4.3.4 Additional Products (calibration/reference files at IRSA)
- **Dichroic-impacted pixels**: bitmask, 1=throughput attenuation ≥50% (matches `DICHROIC` flag); nonzero
  only in Bands 3/4; `dichroic_D<n>*`.
- **Nonfunctional pixels**: bitmask matching `NONFUNC`; `nonfunc_D<n>*`.
- **Non-linearity parameters**: `Q_nl` HDU has the Eq. 2 values used; other HDUs currently unused;
  `nonlinear_pars_D<n>*`.
- **Electronic Gain Factors**: YAML, 32 gain values per detector (per amplifier channel), ADU→e⁻/s;
  `gain_factors*`.
- **Read noise parameters**: per-pixel electronic noise (e⁻) used in Sec. 3.2.3; two extensions `READOUT-1`
  (N=1 read) and `READOUT-2` (N=71 reads); `readnoise_pars_D<n>*`.
- **Solid Angle Pixel Map**: not used in L2 pipeline itself but used by the photometry tool; arcsec²;
  `solid_angle_pixel_D<n>*`.
- **Initial Distortion (SIP)**: prior distortion used by Fine Astrometry, one file/band; `sip_D<n>*`.
- **Crosstalk parameters**: ECSV, one per crosstalk type; Type 1 has files for Bands 1–3, Type 2 for all 6
  bands; `xtalk_class<n>*`.
- **Zodi scaling**: ECSV, one per band, the wavelength-dependent Kelsall-model correction used in `ZODI`;
  `zodi_scaling_D<n>*`.
- **Flux Corrections**: per-pixel scale factors to reconcile QR2 (old gain) with QR3/DR1 (new gain);
  `l3_flux_corrections_D<n>*`.

## Appendix: header keyword dictionary highlights

From Table A.35 (spectral image header, worked example) and Tables B.1/C.1:

**Identification / timing**: `DETECTOR` (1–3 SWIR, 4–6 MWIR), `OBSID`, `EXPIDN`, `DATE` (HDU creation UTC),
`DATE-OBS`/`MJD-OBS`, `DATE-BEG`/`MJD-BEG`, `DATE-AVG`/`MJD-AVG`, `DATE-END`/`MJD-END`, `XPOSURE` (scientific
exposure time, s — the time actually contributing to photocurrent), `TELAPSE` (elapsed start-to-stop, s,
**includes discarded frames**, ends at MJD-END but starts prior to MJD-BEG).

**Onboard SUR/electronics parameters**: `TSAMP` (frame interval, 1.5349 s), `KOVR_A/R/P` (overflow limits,
active/ref/phantom, ADU), `OVRDLY`, `SURLIM` (=77, max frames), `SURDLY` (=3, first summed frame), `TRANDLY`
(=7, transient-detection start frame), `TCUT` (=38, early/late transient boundary frame index), `KEN_A/R/P`
and `KSN_A/R/P` (transient white-noise / shot-noise thresholds, ADU²/ADU — feed Eq. 27), `NSKIP` (=32, rows
skipped after full-row read — matches crosstalk Type-1 spacing), `NVISITROW`/`NVISITCOL`, `MPHAN`,
`NCHANNEL` (=32 readout channels), `WCHANNEL` (=64 cols/channel — matches crosstalk Type-2 spacing), `JREF`/
`KREF` (8 physical ref rows/cols), `JACTIVE`/`KACTIVE` (2040×2040).

**Survey planning**: `SPS_TARGET`, `SPS_FLAGS`, `OBS_IN_SBAND`, `NON_SURVEY`, `SGT_LAT_MIDPT`/`SGT_LON_MIDPT`
(ground-track lat/lon at midpoint), `SGT_MIN_GCD2SAA` (closest ground-track distance to SAA), `SPS_ELON`/
`SPS_ELAT`/`SPS_EPA` (planned boresight ecliptic lon/lat/PA — same across 6 bands, used to classify Survey
1–4), `DETCOORD` (MWIR X-flip flag to match SWIR view), `L1DQAFLG`.

**Spacecraft ephemeris**: `X/Y/Z_SC_START`, `VX/VY/VZ_SC_START`, same at MID and END, `XYZ_SC_SYSTEM`/
`VXYZ_SC_SYSTEM` (=GEOCENTER).

**Blooming/snowball counts**: `SNWSTRK`, `NBLMSRCS`, `SNW7-5CT`/`SNW3-1CT`/`SNW2-5CT`/`SNW6-5CT` (early/late/
very-early snowball counts by frame range), `NSNOWSRC`, `NBLM5SCS`.

**Persistence/quality counters (per-image, all `L2.N_*` prefixed)**: `L2.N_NONLINEAR`, `PSTHRESH` (=0.1
electron/s, persistence threshold), `L2.N_PERSIST`, `L2.N_HOT`, `L2.N_COLD`, `L2.N_TRAN_NB` (transient, not
otherwise-bad), `L2.N_PERS_NB`, `L2.N_SOURCE`, `L2.N_XTALK`, `L2.N_GHOST`, `L2.N_GHOST_FPA`, `L2.N_GHOST_EXT`,
`L2.N_BLOOM_NS` (bloom, not source), `L2.N_SNOW_NS`, `L2.N_OUTLIER`, `L2.SATSTRKS_PXS`, `L2.SATSTRKS`,
`L2.N_TRANSIENT`, `L2.N_OVERFLOW`, `L2.N_SUR_ERROR`, `L2.N_NONFUNC`, `L2.N_DICHROIC`, `L2.N_MISSING`,
`L2.N_FULLSAMPLE`, `L2.N_PHANMISS`, `L2.N_SNOWBALL`, `L2.N_BLOOM`, `L2.N_HALO`, `L2.N_SAT_HALO`.

**Geometry**: `OMEGA_MEDIAN`/`OMEGA_STDDEV` (pixel solid angle, arcsec²), `FINAST` (astrometry quality flag),
`WCSAXES`, `CRPIX1/2`, `PC1_1..PC2_2`, `CDELT1/2`, `CTYPE1/2` = `RA---TAN-SIP`/`DEC--TAN-SIP`, `CRVAL1/2`,
`LONPOLE`/`LATPOLE`, `A_ORDER`/`A_i_j`, `B_ORDER`/`B_i_j` (SIP forward distortion, detector→sky), `AP_ORDER`/
`AP_i_j`, `BP_ORDER`/`BP_i_j` (SIP inverse, sky→detector) — order 3 in the example.

**Photometry/masking counters**: `PXSRCMSK` (% pixels with `SOURCE` flag — 47.6% in the worked example, a
crowded field), `CONTRAST`, `MATCH_NSTARS`, `QS_NMATCH_VAR`, `ASTRONETSOLVED`, `PSF_FWHM` (arcsec, per-image
median — example value 8.67″).

**Airglow/aurora fit diagnostics**: `HE_AG_MODL`, `HE_AG_AMPL`, `HE_AG_XSLOPE`, `HE_AG_CHI2R`, `HE_AG_RMS_PK`,
`HE_AG_BKG_MED`, `HE_AG_BKG_MOD`, `HE_AG_BKG_DEG`, `HE_AG_BKG_COEFF`, `HE_AG_BKG_C*_*`, `AURORA_CORR`,
`SHUTTLE_GLOW_CORR`, `HE_AIRGLOW_CONT` (bool, true only for Detectors 1/2), `SHUTTLE_GLOW_CONT` (true if corr
>0.2), `AURORA_CONT` (true if corr >0.2) — **useful selection keywords to flag/exclude images contaminated by
airglow before stacking**.

**L2DQAFLG**: overall DQA pass/fail summary for the image.

**Alternate/WAVE WCS**: `WCSAXESA/CRPIX*A/...` (0-based active-pixel coordinate system), `WCSAXESW`,
`WCSNAMEW`, `CNAME1W`='Wavelength', `CNAME2W`='Bandwidth', `CTYPE1W`/`CTYPE2W`='WAVE-TAB', `PV1_3W`/`PV2_3W`,
`PS1_0W`/`PS2_0W`='WCS-WAVE', `PS1_1W`/`PS2_1W`='VALUES', `PS1_2W`/`PS2_2W`='X'/'Y' (indexing columns for the
in-file WAVE-TAB lookup — visualization only, per Sec. 4.3.1).

**Processing history**: `HISTORY` lines record each pipeline module + version (e.g. `SSDC-MS-002` Image
Association v2.1.1, `SSDC-MS-025` L2 DQA v1.4) and `[CALIB]` lines record the calibration-product UUIDs used
(dichroic, gain factors, initial distortion, nonfunc map, spectral WCS, abs gain matrix, dark, epsf, sip,
xtalk, zodi scaling, etc.) — this is the definitive per-file provenance trail.

**ePSF file header** (Table C.1): `OVSMPX`/`OVSMPY`=5 (oversampling), `MAXIT`=10, `SMOOTH`='quartic',
`ORDERING`='x-fast then y' (the corrected convention, post PSF-header-bug-fix), table columns `BINX`/`BINY`
(zone grid indices), `XCENTER`/`YCENTER`/`XWIDTH`/`YWIDTH` (pixel units), `NSTAR`, `NEFF_MEAN`, `CWAVE`/
`CBAND` (µm), `EPSF` (TDIM=(33,33), 1089 = 33² values).

**Transient-detection formula (Appendix A.1, Eq. 27)**: for frame index i,
(2y_i − 2y_{i−1} − y_{i−2} + y_{i−4})² > 4×KEN + KSN×(y_{i−1} − y_{i−4} − 3m)
where y is in ADU (~1 ADU ≈ 1 e⁻), m = amplifier drift rate from prior exposure. Applied starting at the 7th
readout frame (`TRANDLY`). For the example `KEN_A`=20000, detection threshold ≈ **141 ADU ≈ 100 e⁻**
(√(4×KEN)/√... per the text, ~12·√(4×KEN)... — reproduced as stated: "≥12√(4×KEN)=141 ADU≈100 e⁻"). If a
transient is caught before frame index `TCUT`(=38), `SUR_ERROR` is also set ("early" transient/overflow).

## Synthesis for galaxy spectrum extraction

**Background subtraction**: `ZODI` layer is *not* subtracted in L2 files — always subtract it explicitly
(`data = IMAGE − ZODI`), exactly as the Mosaic Tool does. The `ZODI` estimate is a **median per-image**
Kelsall-1998-based prediction, empirically rescaled per-wavelength from Year-1 high-latitude data; treat this
as a smooth large-scale background model, not a per-pixel fit to the true instantaneous zodi — for very deep
stacks or low-surface-brightness (LSB) work, consider whether the `zodi_scaling` product's calibration
(rather than the baked-in ZODI layer) should be reapplied/refit locally, since the scaling was derived from
an all-sky, |b|>30° average and may not perfectly represent a specific field or epoch. Also note that
He/aurora/shuttle-glow atmospheric-line contamination is **never subtracted** from IMAGE — it is only fit and
recorded in header diagnostics (`HE_AG_*`, `AURORA_CORR`, `SHUTTLE_GLOW_CORR`, and the boolean `*_CONT`
flags). For any stack, **screen/downweight exposures with `HE_AIRGLOW_CONT`, `AURORA_CONT`, or
`SHUTTLE_GLOW_CONT` = True**, especially in Bands 1–2 (He/aurora) and Band 5 (shuttle glow in R7).

**What to mask before extraction/stacking** (mirroring the pipeline's own background-estimation and
photometry-fit flag lists in Sec. 3.3, and the mosaic bad-pixel list in Sec. 3.4.3): at minimum exclude
TRANSIENT, OVERFLOW, SUR_ERROR, NONFUNC, MISSING_DATA, HOT, COLD, NONLINEAR, PERSIST, BLOOM, SNOWBALL, HALO,
SATELLITE_HALO from any per-pixel photometric measurement; additionally exclude CROSSTALK, GHOST,
GHOST_FPA/GHOST_EXT, STREAK, DICHROIC, PHANMISS when mosaicking or doing precision surface-photometry. The
pipeline's own list for *background estimation* additionally excludes SOURCE and OUTLIER pixels — use the
same when estimating a local sky level around a target galaxy.

**Ghosts and stray light are a first-order systematic for PSB host-galaxy work**, because PSB hosts are often
found near or in groups/clusters with bright neighboring stars/galaxies: watch for (1) DBS ghosts (Bands
3–6, strongest at the Band3/4 boundary, from sources ≥100 Jy — rare for typical targets but relevant near
bright stars); (2) frame-edge and linear bright-source ghosts from sources just outside the FoV or off the
top/bottom of a detector; (3) the 8° stray-light ghost and Moon-edge stray light, which are exposure-level
(not localized) contaminants best handled by exposure vetting rather than pixel masking.

**Wavelength/channel choice**: for science analysis use the **CWAVE/CBAND extensions of the standalone
Spectral WCS files** (Sec. 4.3.1), not the in-image `WCS-WAVE`/WAVE-TAB lookup (visualization only, coarser).
For mosaicking or any per-channel stacking, use the **17-subchannel spectral-channel template** (Sec. 3.4.4/
4.3.2) — note this is a **geometric/survey-planning** channelization, not an exact wavelength solution, so
for precise per-pixel wavelength, still fall back to CWAVE/CBAND. Be aware that R7 shifted the Band 5/6
wavelength solution based on on-sky calibration — **do not mix Band 5/6 channel definitions across pre-/post-
R7 pipeline versions** without reconciling via the wavelength tables.

**PSF for extended sources**: SPHEREx delivers an **effective PSF (ePSF)**, not a deconvolved optical PSF —
it inherently includes detector-pixel response and is evaluated at native-pixel sampling (33×33 array, 5×
oversampled, 21×21 zones for most detectors / 11×41 for Detector 3). The **Tractor-based photometry module
explicitly supports supplying intrinsic galaxy morphology** as a prior for the generative model (Sec. 3.3) —
this is the natural hook for resolved/semi-resolved PSB galaxy photometry, since the framework is built for
exactly this (point-source *and* extended-morphology forced photometry, à la T-PHOT). For fully **resolved**
large nearby galaxies, note the **source-masking module explicitly does NOT mask them** (only `spherex_class`
≤7 unresolved/compact objects are masked) — so resolved-galaxy flux is present but uncorrected for whatever
default background estimate assumes "source-free" pixels; a custom background/aperture strategy is needed for
resolved target galaxies rather than relying on pipeline defaults tuned for point sources.

**Uncertainty**: apply (or expect already-applied, if using L3 catalogs) the **3% systematic floor added in
quadrature** to the Tractor statistical uncertainty (Eq. 19) — this matters most for bright, high-S/N
galaxies where photon/read noise alone would otherwise imply unrealistically small errors, and should be
propagated explicitly in any custom photometry code re-implementing this measurement.

**Low-surface-brightness (LSB) / systematics that matter most for PSB hosts**:
1. Zodiacal light (dominant smooth background at all latitudes; needs the ZODI layer subtracted and possibly
   the zodi_scaling recalibrated for the specific field/epoch);
2. Airglow (He 1.083 µm, aurora, other atmospheric lines) — not subtracted, must be screened via header
   diagnostics or explicitly modeled/removed using the atmospheric templates (Sec. 4.3.3) if not excluding
   affected exposures outright;
3. Persistence — a moving target (predicted analytically, not measured) whose accuracy is untested/
   unquantified in this document; for LSB features near recently-imaged bright sources, treat PERSIST-flagged
   regions with caution even below the hard PERSIST threshold (0.1 e⁻/s in the worked-example header);
4. Ghosts/crosstalk — localized but can masquerade as diffuse structure (e.g. crosstalk Type 1's "negative
   image" 32 rows below a bright source, or the ~10′ DBS ghost disk);
5. Dichroic-edge pixels (Band 3 long-λ / Band 4 short-λ rows) — elevated noise and calibration uncertainty,
   worth excluding or down-weighting near band edges even if not hard-flagged;
6. Mosaic-specific striping (airglow- and extended-source-spectral-feature-driven) does **not** average down
   with more coverage for sharp spectral features — if replicating mosaic-style coaddition for PSB spectra,
   this needs explicit modeling/masking rather than assuming more exposures solves it.

**What the Mosaic Tool does that a custom PSB pipeline could replicate**: (1) explicit ZODI subtraction before
any other step; (2) a clean, enumerated bad-pixel exclusion list per Sec. 3.4.3 (broader than the photometry
module's list — includes DICHROIC, PHANMISS, GHOST_FPA/EXT, STREAK, CROSSTALK); (3) the 17-subchannel
geometric template + precomputed per-channel WAVELENGTH/WL_MIN/WL_MAX/R/R_STD/BANDWIDTH statistics, reusable
directly from the `spectral_channels` calibration product rather than recomputing; (4) a simple, fast,
noise-uncorrelated histogram/pixel-binning reprojection (nearest-neighbor assignment + `np.bincount`
accumulation) that is easy to reimplement and reason about, at the cost of leaving coverage gaps and no PSF
homogenization; (5) bitwise-OR flag propagation into the coadd so downstream users can still make per-pixel
quality cuts on a stacked product.

## Open questions

- The full per-channel Spectral Channels tables (Tables 29–34, this note's envelope summary) give R and
  λ_c/[λ_min,λ_max] at 19 rows (ch. 0–18) per band; if exact per-channel values are needed for pipeline
  reimplementation, pull them directly from PDF pp. 61–64 or the `spectral_channels_YYYMMDD.fits` product
  itself rather than from this note's summary.
- The document gives **no single, general PSF FWHM number**; `PSF_FWHM` (8.67″ in the one worked example) is
  per-image/per-detector and Fig. 21's `NEFF_MEAN` maps are the authoritative empirical PSF-size diagnostic —
  need to pull actual `NEFF_MEAN` values from the ePSF calibration product for our specific bands/detectors
  rather than relying on any single quoted number.
- Absolute calibration accuracy is quoted as "<1% for the great majority of channels" with details deferred
  to "Ashby et al. 2026 (in prep)" — that paper should be checked once available for band-by-band systematic
  budgets relevant to a stacking analysis.
- Persistence-model *accuracy* (as opposed to its functional form) is not quantified anywhere in this
  document — no RMS/validation numbers are given for how well Eq. 7–13 actually predicts on-sky residual
  charge; worth flagging as a gap if PSB targets are frequently observed shortly after bright-source
  exposures.
- Type 3 crosstalk (channel-boundary streak in MWIR) has a defined-but-unimplemented masking prescription in
  R7 — for Bands 4–6 galaxy photometry, this systematic is currently **unmasked** in the data and needs an
  independent check/removal strategy.
- It's unclear from this document alone whether the QR2 PSF header-ordering bug fix and R7 ePSF replacement
  are fully independent (i.e., whether QR2 "+psffix1" files use the old optical-PSF-reconstruction product or
  effectively become obsolete once QR3/DR1 ePSF products are adopted) — worth clarifying before mixing QR2
  and QR3/DR1 PSF products in one analysis.
