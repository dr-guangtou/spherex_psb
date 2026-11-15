# Review of the student's SPHEREx photometry of the 48k SDSS galaxies

Date: 2026-11-15. Data reviewed: `/Users/shuang/data/spherex/spherex_sdss48k_phot` (four Parquet files and a
README, made 2026-11-12 on OSC). Code: the student's repository
`/Users/shuang/Dropbox/work/project/otters/spherex_photometry_code` (read only; the local copy is at its first
commit of 2026-11-09 and does not yet hold the `sdss48k/` run folder the README points to, but the production
script `top100k/spx_phot.py` and talltable's `optimal_extract` at commit `6d8ded3` are there). Scripts of this
review: `scripts/sdss48k_review/` (`summarise_catalogue.py`, `compare_with_demo.py`,
`measure_failures_and_errors.py`, `make_figures.py`; for section 8 `measure_hminus_bump.py`,
`summarise_hminus_bump.py`, `make_hminus_figures.py`; for section 8.4 `check_model_comparability.py`,
`make_model_check_figures.py`). Figures: `docs/figures/sdss48k_review/`. Section 8 was added the same day, section
8.4 on 2026-11-16.

## 1. Summary

- **What it is.** Forced photometry at the SDSS positions of all 48,111 galaxies of the MPA-JHU parent catalogue
  (0.03 < z < 0.06, log M* >= 10), on every QR2 and QR3 SPHEREx image that covers them: 16.5 million
  measurements, a median of 345 per galaxy, each one image at one wavelength between 0.735 and 5.025 um.
  Every row carries two fluxes: a point-source (PSF) fit and a 12.3 arcsec aperture sum.
- **Bookkeeping is sound.** The target table is the parent catalogue row for row, every galaxy has
  measurements, and on the same exposures the wavelengths agree with ours to 0.0002 um and the aperture fluxes
  with ours to 1-3 % for isolated galaxies. The image list and footprints can be reused as they are.
- **The PSF flux should not be used for galaxy SEDs, neither for fluxes nor for shapes.** It assumes a point source; on our six demo galaxies it
  recovers 31-92 % of the total flux, by a fraction that changes from detector to detector (so it bends the
  SED shape), and talltable's 4-sigma pixel clipping pushes 8.7 % of all bright measurements to more than 1.5
  times the aperture flux (up to 10-100 times). This is the failure our photometry study of 2026-11-12/13
  predicted from simulations.
- **The aperture flux is the usable product.** It repeats to 3-5 % per exposure in D1-D4, so SED-shape
  measurements over a limited wavelength range can use it directly (section 8). It is not a total flux (56-96 % of our Sersic total on the four isolated demo galaxies, falling by up to 0.1 mag from
  D1 to D6), it has no neighbour subtraction, it sums pixels that the fit masks as bad (2-4 % of exposures are
  gross outliers), and its formal errors are 1.2-1.8 times too small. The run's constant pixel solid angle
  also leaves a 2 % D2/D3 step, removed here with the official solid-angle map.
- **H-minus bump.** The paper's index (Hbump_opt) is measured for 46,504 galaxies with a median error of
  0.016 mag: median -0.041 mag, 66 % of galaxies below zero at more than 2 sigma, and nearly flat against Dn4000
  and HdeltaA (section 8). The paper's model loci need two adjustments before they can be compared with this
  sample (section 8.4): the models quench by 5.9 Gyr after the onset of star formation (the cosmic age at
  z = 1), so only their late epochs apply at z = 0.05, and none of those is star forming; and the SPHEREx
  sampling shifts the index by 0.002 mag (median) and with redshift, which explains most of the redshift trend.
  Matched in this way, the galaxies within the models' range (sSFR < 10^-10.5 per yr, 31,988) sit 0.001-0.007 mag
  weaker than the TP-AGB-on models and 0.022-0.027 mag stronger than TP-AGB off.

## 2. What was done

| Step | How (from the README and `top100k/spx_phot.py`) |
|---|---|
| Targets | `galaxy_summary_48111.csv` (our parent catalogue), RA/Dec only; other columns carried along |
| Images | every QR2 and QR3 L2 image whose TAN-SIP footprint holds a target: 291,205 QR2 + 14,412 QR3, observation weeks 2025W17 to 2026W34 (QR3 weeks W35-W36 missing; DR1 not used) |
| Pixels | read from the public AWS bucket: row bands of IMAGE, FLAGS, VARIANCE for QR2, whole files for QR3; nothing kept on disk |
| Calibration | QR2 pixels mapped to the QR3 calibration with talltable's per-pixel linear table (`qr2_to_qr3.parquet`), non-functional pixels flagged |
| Background | median of unflagged pixels within 1.6 arcmin of the target, one constant per measurement |
| PSF flux | talltable `optimal_extract`: one average PSF per detector (zone nearest the target), pixels within 4 px, linear optimal estimate, iterative rejection of pixels more than 4 sigma from the model (up to 10 iterations); no neighbours fitted |
| Aperture flux | sum of all background-subtracted pixels with centres within 2 px (12.3 arcsec); flagged pixels inside are not excluded |
| Units | pixel solid angle a constant 6.15 x 6.15 arcsec (no solid-angle map) |
| Extinction | SFD E(B-V) x 0.86 per galaxy in `ebv.parquet`; fluxes not corrected |

Note on the `converged` column (99.7 % true): talltable sets it to true when the clipping loop reaches its
iteration limit, so it does not mark failed fits.

## 3. Catalogue and coverage

- 48,111 targets, identical in order to `galaxy_summary_48111.csv` (specobjid by specobjid). 184 pairs of rows
  are the same galaxy with two spectra (within 3 arcsec, |dz| < 0.001), so 47,927 distinct galaxies.
- Images per galaxy 228 / 346 / 441 (p5 / p50 / p95); 0.1 % of (galaxy, image) pairs have no row because every
  pixel was flagged. The distribution is bimodal (figure 3a).
- 95.5 % of the rows come from QR2 images (pipeline before the DR1 reprocessing).
- Per-exposure aperture S/N, p5 / p50 / p95: D1 13 / 33 / 79, D2 20 / 48 / 107, D3 23 / 53 / 114,
  D4 16 / 40 / 90, D5 5 / 14 / 37, D6 2 / 7 / 22 (figure 3b). These are formal; see section 6.
- E(B-V) (0.86 x SFD) 0.009 / 0.025 / 0.062 (p5 / p50 / p95); 613 galaxies above 0.1.

```{figure} ../figures/sdss48k_review/fig3_coverage_and_depth.png
:width: 620px
:alt: Measurements per galaxy and aperture signal-to-noise per detector

Figure 3. (a) Number of measurements per galaxy. (b) Formal aperture S/N per exposure by detector: box
25-75 %, line 5-95 %, circle median (2 million random rows).
```

## 4. Same exposures as the SED demo

All six demo galaxies are in the catalogue. Matching on observation id and detector gives 269-409 common
exposures per galaxy (2,067 after our screening). Ours: DR1 + QR3, forced Sersic model with fixed optical
shape, neighbours fitted jointly, background fitted with the sources. Medians of per-exposure ratios:

| galaxy | run PSF / our total | run aperture / our total | run aperture / our raw 2 px aperture | run PSF / our unclipped point fit |
|---|---|---|---|---|
| g1 reference | 0.68-0.82 | 0.84-0.92 | 0.97-1.02 | 0.97-1.14 |
| g2 compact | 0.85-0.92 | 0.91-0.96 | 0.97-1.00 | 0.96-1.02 |
| g3 large | 0.31-0.40 (D3 2.55) | 0.56-0.61 | 0.97-1.00 | 1.02-1.29 (D3 9.1) |
| g4 close neighbour | 0.77-0.91 | 1.03-1.15 | 1.24-1.33 | 1.21-1.42 |
| g5 outside Legacy Survey | 0.64-0.74 | 0.87-1.09 | 1.17-1.43 | 1.09-1.25 |
| g6 post-starburst-like | 0.58-0.76 | 0.80-0.89 | 0.90-1.01 | 0.97-1.18 |

Ranges are over the six detectors (per-detector medians in the output of `compare_with_demo.py`).

- **Calibration and wavelengths agree.** For the four isolated galaxies the run's aperture equals our raw
  aperture on the same pixels to 1-3 % (D6 lowest, 0.90-0.98), so the QR2-to-QR3 mapping and the DR1 images
  give the same fluxes at this level.
- **Neighbours.** g4 (a companion) and g5 (a crowded low-latitude field) are 17-43 % brighter in the run's
  aperture, because the run does not subtract neighbours.
- **PSF flux is too low and wavelength dependent.** The fraction recovered differs by up to 0.2 between
  detectors of one galaxy (g1: 0.82 in D4, 0.68 in D6; g6: 0.58 in D1, 0.76 in D4), which distorts the SED
  shape by 0.2-0.3 mag between detectors. For g3, D3 is dominated by clipping failures (median 2.55 times our total).
- **Clipping inflates the PSF flux.** Exposures with clipped pixels have PSF fluxes 0-28 % (median per galaxy)
  above our unclipped point fit of the same pixels; those without clipping agree to 1-3 % (g1, g2, g6).
- **Aperture outliers.** 47 of 2,067 run aperture fluxes differ from ours by more than a factor of 2; the
  extreme ones (10-400 times) all have a flagged pixel inside the aperture, which talltable sums.

```{figure} ../figures/sdss48k_review/fig1_demo_galaxies_same_exposures.png
:width: 820px
:alt: Run PSF and aperture fluxes against our Sersic total flux for three demo galaxies

Figure 1. Three demo galaxies on the same exposures: our forced Sersic total flux (black), the run's 12.3 arcsec
aperture flux (grey) and PSF-fit flux (coloured by detector, D1 blue to D6 pink). Lower panels: run / our
total. Points far above the black curve in the upper panels are clipping failures of the PSF fit; a few
aperture fluxes are off scale (flagged pixels inside the aperture).
```

## 5. Clipping failures across the sample

Measurements with aperture S/N > 10 whose PSF flux exceeds the aperture flux (which a correct point-source
fit of a galaxy cannot do by much):

| | D1 | D2 | D3 | D4 | D5 | D6 | all |
|---|---|---|---|---|---|---|---|
| PSF > 1.5 x aperture | 9.4 % | 14.4 % | 13.6 % | 5.4 % | 0.5 % | 0.2 % | 8.7 % |
| PSF > 2 x aperture | 8.7 % | 13.0 % | 11.6 % | 4.4 % | 0.4 % | 0.1 % | 7.6 % |

- The failures follow the number of clipped pixels: 0.4-0.6 % of measurements with up to 5 clipped pixels,
  4.8 % with 6-10, 17 % with 11-20, 39 % with more than 20 (figure 2a). Clipping is the rule, not the
  exception: 86-94 % of D1-D3 measurements have at least one clipped pixel, a median 12-18 % of the fit pixels.
- Per galaxy, the median fraction of exposures affected is 2 %, the 90th percentile 25 %; 14,263 galaxies (30 %)
  have more than 10 % of their exposures affected.
- D5 and D6 are nearly free of it because the S/N there is lower (the clipping mechanism needs bright pixels).

## 6. Repeatability and errors

Pairs of exposures of the same galaxy on the same detector whose wavelengths differ by less than 0.2 of the
local bandwidth see the same spectrum, so their difference measures the real per-exposure scatter (673,154
pairs from 5,000 random galaxies; robust sigma = 1.4826 x MAD):

| | D1 | D2 | D3 | D4 | D5 | D6 |
|---|---|---|---|---|---|---|
| PSF flux scatter per exposure | 11.9 % | 12.3 % | 11.7 % | 9.4 % | 10.2 % | 14.2 % |
| aperture flux scatter per exposure | 4.5 % | 3.6 % | 3.4 % | 4.3 % | 9.0 % | 16.5 % |
| PSF: real scatter / formal error | 2.8 | 3.3 | 3.4 | 2.7 | 1.5 | 1.2 |
| aperture: real scatter / formal error | 1.5 | 1.7 | 1.8 | 1.7 | 1.3 | 1.2 |
| aperture pairs beyond 5 robust sigma | 2.1 % | 1.9 % | 1.9 % | 4.0 % | 3.5 % | 3.9 % |

- The PSF flux of an extended galaxy depends on where its centre falls within a pixel, which with clipping gives
  ~10-12 % scatter where photon noise alone would give a few per cent (our study measured 5-13 % phase scatter in
  simulations without clipping).
- The aperture's 3-5 % in D1-D4 probably includes the hard aperture edge (whole pixels whose centres fall within
  2 px, about 13, so the enclosed light changes with the sub-pixel position); D5 and D6 are noise dominated.
- Formal errors must be scaled (or replaced by the exposure scatter, as in our demo) before any fit or stack.

```{figure} ../figures/sdss48k_review/fig2_clipping_and_repeatability.png
:width: 820px
:alt: Clipping failures and per-exposure repeatability

Figure 2. (a) PSF flux / aperture flux against the number of clipped pixels (aperture S/N > 10; dashed line at
1.5). (b) Fraction of measurements with PSF flux above 1.5 times the aperture flux, by detector. (c) Robust
per-exposure scatter of the PSF and aperture fluxes from close-wavelength pairs.
```

## 7. What can be used now, and what it would take

Usable as is:
- the target-to-image matching (`images.parquet`, `n_images`), the exposure wavelengths and bandwidths, the
  detector positions, and `ebv.parquet`;
- the aperture flux for relative work on isolated galaxies, after removing outlier exposures per galaxy
  (robust clipping along wavelength) and scaling the errors by the factors in section 6.

Usable for SED-shape measurements over a limited wavelength range (colours, spectral indices): the aperture
flux with outlier rejection and the solid-angle correction, as section 8 does for the H-minus bump.

Not usable for galaxy SEDs: `opt_flux_uJy` (point-source flux of extended galaxies, wavelength-dependent
losses that bend the SED shape, clipping failures).

To turn the aperture flux into total-flux SEDs (each item is a decision for the owner):
1. **Aperture correction per galaxy and detector** from the optical shape convolved with the SPHEREx PSF, as in
   our model-corrected aperture (study section 5; demo section of `docs/sed_extraction.md`). Without it the
   SED shape carries the size-dependent D1-D6 drift (up to 0.1 mag in the demo galaxies).
2. **Neighbour flag or subtraction**: at least flag galaxies with SDSS or Legacy Survey sources within ~25 arcsec;
   g4 and g5 show 17-43 % contamination.
3. **Bad pixels in the aperture**: cannot be fixed from the catalogue (the number of flagged pixels inside the
   aperture is not stored); outlier rejection along wavelength is the only remedy without re-measuring.
4. Solid angle: the constant 6.15 arcsec pixel is off by -1.7 % to +1.1 % depending on the detector position,
   which makes a 2 % flux step between D2 and D3 where they overlap (section 8). The official Solid Angle Pixel
   Map at `xpix_fulldet`, `ypix_fulldet` removes it without re-measuring.
5. The missing QR3 weeks and the DR1 images are smaller effects.

The alternative is to re-measure with the demo's forced Sersic photometry. The student's infrastructure (exact
footprints, row-band reads from S3, sharded resumable runs) is the part worth keeping; only the measurement
step would change. The cost of such a run has not been measured.

## 8. The H-minus bump index from the aperture fluxes

The index only needs the shape of the SED between 1.49 and 1.79 um (rest), so the aperture flux can be used
without a total-flux correction. Definition: Hbump_opt of the H-bump paper (rest-frame vacuum windows blue
1.494-1.539, feature 1.570-1.734, red 1.746-1.791 um; straight-line pseudo-continuum through the band means of
F_lambda; I = -2.5 log10 mean(F_lambda / F_c); negative = bump present), measured with the irregular-sampling
estimator of the demo feasibility study (`docs/reports/hminus_bump_feasibility.md`). Relative calibration
between exposures is taken as correct.

### 8.1 Measurement

| Step | Choice |
|---|---|
| Galaxies | 47,927 (one row per repeat group) |
| Exposures | aperture flux, rest 1.44-1.84 um; 1.79 million exposures |
| Solid angle | each flux multiplied by SAPM / (6.15 arcsec)^2 at the galaxy's detector position (official map, R7 pipeline, from the spherex-retrieval cache; equal to the demo's per-exposure solid angles to better than 10^-5) |
| Outliers | quadratic in wavelength fitted per galaxy; exposures beyond 5 robust sigma rejected (median 0, p84 1 per galaxy) |
| Requirement | >= 2 exposures in each side window and >= 5 in the feature window |
| Error | per-exposure scatter around the quadratic (median 3.2 %) propagated to the index; a bootstrap over exposures for 485 random galaxies agrees (median ratio 0.98, figure 6c) |
| Optical indices | MPA-JHU DR8 `galSpecIndx`, joined by specobjid: Dn4000 and HdeltaA as in the input catalogue (identical values), and the broad D4000 (`D4000_SUB`) that the paper's models use; their errors |

Result: an index for 46,504 galaxies (97 %); the others lack exposures in one window (blue 681, red 918,
feature 668). Exposures per window: blue 2 / 4 / 7, feature 9 / 14 / 23, red 2 / 3 / 6 (p5 / p50 / p95).
Index error 0.010 / 0.016 / 0.035 mag (p5 / p50 / p95).

**The solid-angle correction matters.** D2 and D3 both cover observed 1.616-1.668 um. As delivered, D3 fluxes
there are 2.06 % below D2 (median per galaxy); the official map gives solid angles of 0.990 (D2) and 1.010 (D3)
times the constant pixel at those positions, which predicts the step, and after the correction the median step
is -0.19 % (figure 6a). The D2/D3 boundary falls between the blue and red windows, so the correction deepens the
index by 0.010 mag (median; 0.007-0.012 for 90 % of galaxies). On the six demo galaxies the corrected index agrees
with the demo study's model-flux index within the errors (differences -0.019 to +0.011 mag; the uncorrected one
is 0.006-0.023 mag shallower; figure 6d).

### 8.2 Against Dn4000 and HdeltaA

```{figure} ../figures/sdss48k_review/fig4_hminus_bump_vs_optical_indices.png
:width: 820px
:alt: H-minus bump index against Dn4000 and HdeltaA for 46,504 SDSS galaxies

Figure 4. The H-minus bump index of individual galaxies against (a) Dn4000 and (b) HdeltaA from the input
catalogue (MPA-JHU, emission-subtracted). Grey: smoothed density enclosing 68, 95 and 99.5 % of the galaxies;
black: running median with its error. The bump axis is inverted as in the H-bump paper (stronger bump up).
The cross is the median error of one galaxy.
```

- Median index -0.041 mag; p5 / p95 -0.076 / -0.007. 66 % of galaxies are below zero at more than 2 sigma, 39 %
  at more than 3 sigma; 0.07 % are above zero at 2 sigma.
- Observed spread 0.019 mag (robust sigma) against a median error of 0.016 mag: the intrinsic spread is
  ~0.010 mag, and ~0.009 mag in the 9,037 galaxies with errors below 0.012 mag (spread 0.014, error 0.011).
- The trends are weak (Spearman rank correlation -0.09 with Dn4000, +0.08 with HdeltaA). The median index goes
  from -0.035 at Dn4000 1.1-1.2 to -0.044 at 2.0-2.1, and from -0.043 at HdeltaA -4 to -0.037 at HdeltaA 5-6:
  galaxies with older light have a slightly stronger bump.

### 8.3 Against the H-bump paper's models

```{figure} ../figures/sdss48k_review/fig5_hminus_bump_with_models.png
:width: 820px
:alt: H-minus bump index against D4000 and HdeltaA with TP-AGB-off and TP-AGB-on model populations

Figure 5. As figure 4, against (a) the broad D4000 (MPA-JHU `D4000_SUB`, the definition the models use) and
(b) HdeltaA, with the model populations of the H-bump paper: exponential-quench star-formation histories, all
epochs after 1 Gyr, TP-AGB off (C3K templates, agb = 0, blue) and TP-AGB on (LW02 templates, agb = 2, vermilion),
68 and 95 % contours; models are noiseless and dust-free.
```

Median index in bins of the broad D4000 (models: median and 16-84 % range):

| D4000 | galaxies | data | TP-AGB off | TP-AGB on |
|---|---|---|---|---|
| 1.3-1.4 | 2,095 | -0.037 | -0.002 (-0.006, +0.003) | -0.059 (-0.064, -0.054) |
| 1.5-1.6 | 4,810 | -0.040 | -0.009 (-0.013, -0.005) | -0.057 (-0.068, -0.051) |
| 1.7-1.8 | 4,219 | -0.042 | -0.014 (-0.017, -0.009) | -0.053 (-0.061, -0.046) |
| 1.9-2.0 | 6,439 | -0.042 | -0.017 (-0.021, -0.012) | -0.049 (-0.055, -0.043) |
| 2.1-2.2 | 5,410 | -0.043 | -0.017 (-0.021, -0.013) | -0.052 (-0.054, -0.046) |

(All bins from 1.1 to 2.6 are in the output of `summarise_hminus_bump.py`.)

- **Level.** (All model epochs after 1 Gyr, as in the paper; section 8.4 restricts them to the epochs a
  z = 0.05 galaxy can have.) At every D4000 the data median lies between the two model loci; over D4000 1.3-2.4 it is
  0.026-0.035 mag stronger than TP-AGB off and 0.006-0.022 mag weaker than TP-AGB on, closer to TP-AGB on. With TP-AGB off, the models do not
  reach the median of the data at any D4000 or HdeltaA.
- **Shape.** The TP-AGB-on models have the strongest bump at D4000 1.3-1.6 (where the paper's fiducial tracks
  are 0.5-1 Gyr after quenching) and
  at high HdeltaA; the data have their weakest bump there. In the data, low D4000 and high HdeltaA are mostly
  star-forming galaxies, whose emission lines (Paschen and Brackett lines, [Fe II] 1.644 um inside the feature
  window) and dust are not in the models; the rapid-quenching galaxies the models single out are a small
  subset that this plot does not isolate. The models' peak also comes from early epochs (every TP-AGB-on
  epoch with a bump below -0.06 mag is before 9.5 Gyr; section 8.4): a z = 0.05 galaxy cannot be at those
  epochs under the paper's prior.
- The model contours describe where the models can lie, not a predicted distribution: the paper's grid of
  star-formation histories is not weighted to the SDSS population.

### 8.4 Are the models comparable with the data?

Three differences between the paper's models and these measurements, each measured
(`check_model_comparability.py`, figures 7 and 8).

```{figure} ../figures/sdss48k_review/fig7_model_comparability_checks.png
:width: 820px
:alt: Checks of resolution, SPHEREx sampling and model epochs

Figure 7. (a) HdeltaA of solar C3K SSPs broadened to a total sigma, minus its value at 300 km/s (the models'
product); grey band: the sample's stellar velocity dispersion (MPA-JHU `V_DISP`, 5-95 %), to which the SDSS
instrument adds in quadrature. (b) Per galaxy: the model index measured through that galaxy's own SPHEREx
exposures with the data estimator, minus the model's R = 100 index, for a 5 Gyr solar SSP with TP-AGB off and on;
dotted: a continuous spectrum at R = 41 alone. (c) Measured index minus the median of its Dn4000 bin, against
redshift (black), and the same after subtracting each galaxy's sampling bias (grey); dashed: the median sampling
bias of the models against redshift, offset to zero mean. (d) Broad D4000 of the sample and of the TP-AGB-on
model population at all epochs after 1 Gyr (the paper's figure 1) and at epochs after 10 Gyr.
```

**1. Optical indices: resolution.** The models give D4000 and HdeltaA on a sigma = 300 km/s product. MPA-JHU
measures them on the SDSS spectra ("values measured off the unmodified spectrum", MPA-JHU DR7 raw-data page; no
page I read states a dispersion correction), so their broadening is the instrument plus the galaxy's own
dispersion, 53 / 112 / 212 km/s (p5 / p50 / p95) for the latter. Measured on the H-bump project's native C3K SSPs
(ages 1-13 Gyr, four metallicities) broadened to 70-250 km/s instead of 300 km/s:

| Index | change from 300 km/s to 70-250 km/s | data median error |
|---|---|---|
| broad D4000 (the models' D4000) | -0.001 to +0.006 | 0.02 |
| Dn4000 (figure 4 only, no models) | +0.000 to +0.030 | |
| HdeltaA | -0.81 to +0.03 A; at 100-150 km/s, solar: -0.07 to -0.08 (1 Gyr), -0.20 to -0.24 (2 Gyr), -0.28 to -0.33 (4 Gyr), -0.36 to -0.42 A (8 Gyr) | 0.73 A |

D4000 is unaffected. The model HdeltaA would be 0.1-0.4 A lower at the SDSS resolution, more for older light: a
shift to the left in figures 5b and 8b, smaller than one galaxy's error. Not applied in the figures.

**2. The bump: SPHEREx resolution and sampling.** The models give the bump at R = 100 on a continuous spectrum;
the data index uses each galaxy's own exposures (median R = 35-41 in D1-D4, from `wv_um / wv_width_um`) at the rest
wavelengths its redshift and the survey give. For every galaxy the model spectra (solar SSPs of 1, 2, 3, 5, 10
Gyr, TP-AGB off and on, as in the paper) were integrated over its exposures (Gaussian response with the exposure's
equivalent width) and passed through the data estimator:

| Effect | TP-AGB off | TP-AGB on |
|---|---|---|
| resolution alone (continuous R = 41 minus R = 100) | -0.0012 to -0.0011 mag | -0.0001 to +0.0020 mag |
| sampling and estimator, median over galaxies | -0.0004 to +0.0003 mag | +0.0017 to +0.0044 mag |
| same, p5 / p95 (5 Gyr) | -0.009 / +0.009 mag | -0.009 / +0.013 mag |
| median at z 0.030-0.035 and 0.055-0.060 (5 Gyr) | +0.0015 and -0.0013 mag | +0.0034 and +0.0005 mag |

(positive = the data system shows a weaker bump than the model at R = 100.) The resolution is not the issue
(as the feasibility study found); the irregular sampling is. On average it moves the TP-AGB-on locus by 0.002 mag
towards weaker bumps, galaxy by galaxy it scatters the index by 0.005-0.007 mag (standard deviation), and it changes by 0.003 mag
across the redshift range. This explains most of the redshift trend of 8.5: at fixed Dn4000 the index at
z 0.05-0.06 minus that at z 0.03-0.04 is -0.0030 to -0.0042 mag as measured and -0.0005 to -0.0014 mag after
subtracting each galaxy's sampling bias (TP-AGB-on template; -0.0007 to -0.0022 mag with the TP-AGB-off one;
figure 7c). The same subtraction lowers the intrinsic spread from 0.010 to 0.008 mag (0.009 to 0.007 mag in
the galaxies with errors below 0.012 mag).

**3. Star-formation histories and epochs.** The paper's population draws the quenching time t_q uniformly in
1-5.9 Gyr after the onset of star formation (H-bump project `sfh_model.py`; 5.85 Gyr is the cosmic age at z = 1,
Planck 2018) and keeps every epoch to 13 Gyr; the paper compares it with quiescent galaxies at z = 1-2. A galaxy
at z = 0.03-0.06 is 12.96-13.36 Gyr after the Big Bang, so it can only be at late model epochs.

| Model epochs | before quenching | D4000 p1 / p50 | sSFR p99 (log per yr) | SDSS below D4000 p1 | SDSS above sSFR p99 |
|---|---|---|---|---|---|
| >= 1 Gyr (figure 5) | 20.7 % | 1.17 / 1.75 | -8.7 | 0.1 % | 0 % |
| >= 8 Gyr | 0 % | 1.48 / 2.05 | -10.2 | 13 % | 16 % |
| >= 10 Gyr | 0 % | 1.58 / 2.10 | -10.5 | 23 % | 30 % |
| >= 12 Gyr | 0 % | 1.67 / 2.16 | -10.7 | 32 % | 37 % |

(SDSS sSFR: MPA-JHU `SPECSFR_TOT_P50`.) At the epochs that apply, the model population has no star-forming and
no recently quenched galaxies: a quarter to a third of the sample lies outside it. The regions of figure 5
where the TP-AGB-on models are most distinctive come from early epochs: every epoch with a bump below -0.06 mag
is before 9.5 Gyr (median 4.6 Gyr, 1.3 Gyr after quenching), and every epoch with HdeltaA above 4 A is before
8.4 Gyr (more than half of them still star forming). At z = 0.05 the same spectra would need a t_q of about
10-13 Gyr, which the prior does not draw. The bump of the
late epochs barely depends on the epoch: median -0.018 / -0.019 / -0.020 mag (TP-AGB off) and -0.050 / -0.049 /
-0.048 mag (TP-AGB on) after 8 / 10 / 12 Gyr.

```{figure} ../figures/sdss48k_review/fig8_hminus_bump_with_late_models.png
:width: 820px
:alt: H-minus bump index against D4000 and HdeltaA with the late-epoch model populations

Figure 8. As figure 5, with the model populations restricted to epochs after 10 Gyr and shifted by their median
SPHEREx sampling bias (+0.0001 mag TP-AGB off, +0.0020 mag TP-AGB on). The running median is for the 31,988
galaxies within the models' sSFR range (MPA-JHU sSFR below 10^-10.5 per yr); grey contours: all galaxies.
```

**Matched comparison** (figure 8; galaxies with sSFR < 10^-10.5 per yr, models after 10 Gyr with the sampling
shift, median index in broad-D4000 bins):

| D4000 | data | TP-AGB off | TP-AGB on |
|---|---|---|---|
| 1.50-1.65 | -0.041 | -0.015 | -0.048 |
| 1.65-1.80 | -0.042 | -0.016 | -0.048 |
| 1.80-1.95 | -0.042 | -0.019 | -0.043 |
| 1.95-2.10 | -0.042 | -0.021 | -0.043 |
| 2.10-2.25 | -0.043 | -0.019 | -0.047 |
| 2.25-2.40 | -0.043 | -0.018 | -0.048 |

The data are 0.001-0.007 mag weaker than TP-AGB on and 0.022-0.027 mag stronger than TP-AGB off, and flat in
D4000 (Spearman -0.03), as the late TP-AGB-on models nearly are (-0.043 to -0.048 mag). In the HdeltaA plane the late models lie at
HdeltaA below 1.6 A (99 %; maximum 3.0 A) while the data reach 6 A; the 0.1-0.4 A resolution shift of item 1 does not close that gap, which
is the star-forming and recently quenched light the late models lack.

### 8.5 Systematics not yet controlled

1. **Redshift trend.** At fixed Dn4000 the median index deepens by 0.004-0.005 mag from z = 0.033 to 0.057 in
   every Dn4000 bin (figure 6b). Most of it is the exposure sampling (section 8.4, item 2): after subtracting
   each galaxy's sampling bias, 0.0005-0.0022 mag remain between z 0.03-0.04 and 0.05-0.06. The remainder may come
   from the fixed 12.3 arcsec aperture, whose radius is 7.4 kpc at z = 0.03 and 14.3 kpc at z = 0.06 (flat
   LambdaCDM, H0 = 70, Omega_m = 0.3); not tested.
2. **Residual D2/D3 calibration.** Field stars constrain the detector step to +-1.3 % (feasibility study), i.e.
   +-0.004-0.009 mag on the index, the same for all galaxies at one redshift.
3. **Different apertures.** The optical indices come from the 3 arcsec SDSS fibre, the bump from a 12.3 arcsec
   aperture; radial gradients enter the comparison.
4. **Emission lines and dust** are in the data, not in the models (see 8.3); the matched comparison of 8.4
   uses galaxies with sSFR < 10^-10.5 per yr, where both are smaller.

```{figure} ../figures/sdss48k_review/fig6_hminus_bump_checks.png
:width: 820px
:alt: Checks of the H-minus bump measurement

Figure 6. (a) Flux step between D3 and D2 where they overlap (observed 1.616-1.668 um), per galaxy, as delivered
(constant pixel solid angle) and after the solid-angle map; dashed: medians. (b) Median index against redshift
in four Dn4000 bins, with the error of the median. (c) Bootstrap against analytic index errors for 485 random
galaxies. (d) The six demo galaxies: this run's aperture-flux index against the demo study's forced-Sersic
index (DR1 + QR3), with and without the solid-angle correction.
```

### 8.6 Reading

The 1.6 um bump is measured in individual galaxies at 0.016 mag per galaxy. Compared with the paper's models at
the epochs a z = 0.05 galaxy can have, and on the same system (SPHEREx sampling applied to the models), the
galaxies within the models' range sit on the TP-AGB-on locus to 0.001-0.007 mag and 0.022-0.027 mag away from
TP-AGB off. That offset is larger than every systematic measured so far: the sampling bias (0.002 mag median,
0.003 mag across the redshift range), the residual D2/D3 calibration (+-0.004-0.009 mag) and the resolution terms
(<= 0.002 mag); the fibre-aperture mismatch is not quantified. The flat trend with D4000 is what the late models
predict too. What figure 5 seemed to show, that the data lack the models' age dependence, does not test the
paper: the models' strong-bump region comes from epochs a low-redshift galaxy cannot have under the paper's prior.

To test the paper's prediction at low redshift the models need histories that quench late (t_q up to ~13 Gyr) and
star-forming histories, which is a change to the H-bump project's population, not to this measurement. Next steps
on our side:

- separate quiescent and post-starburst galaxies from star-forming ones with the MPA-JHU emission lines
  (`galSpecLine-dr8.fits` is local) and compare the bump at fixed D4000;
- apply the sampling bias per galaxy with a template matched to its own index (forward-model estimator of the
  feasibility study), instead of one template;
- stack galaxies in Dn4000-HdeltaA cells to reach 0.003-0.005 mag per cell and see the bump profile itself.

## 9. Questions for the student

- Push the `sdss48k/` run folder (job scripts, `targets.csv`, logs) to the repository; the local copy ends at
  2026-11-09.
- Could the run store, per measurement, the number of flagged pixels inside the aperture and the sub-pixel
  position? Both would let the aperture outliers and the phase scatter be handled without re-measuring.
