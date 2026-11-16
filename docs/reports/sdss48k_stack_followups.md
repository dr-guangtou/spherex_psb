# Stacks of post-starbursts, inclination and detector controls, and the late-epoch models (SDSS 48k)

Date: 2026-11-16. Follows `sdss48k_stacks_and_outliers.md` (its section 4 lists these four items) on the same
data, corrections and stacking method. Scripts in `scripts/sdss48k_review/`: `stack_post_starbursts.py`,
`control_inclination_and_detectors.py`, `compare_stacks_with_models.py`, `inspect_detector_failures.py`,
`make_followup_figures.py` (`stack_sed_and_bump.py` now exposes `stack_groups`, which they share; its own output
is unchanged, checked to be identical). Results: `/Users/shuang/data/spherex/results/sdss48k_hminus/` (`psb_*`,
`control_*`, `model_stack_*`, `detector_scatter*`, `outlier_stars_60arcsec.parquet`,
`outlier_wide_star_metrics.parquet`, `target_45124_exposures.parquet`). Figures 14-17 in
`docs/figures/sdss48k_review/`. Index values are stacked, continuum-normalised indices (mag; negative = bump)
with bootstrap errors over galaxies unless stated.

## 1. Summary

- **Post-starbursts have a weaker bump than their controls.** The 40 young E+A galaxies (Halpha emission
  equivalent width below 3 A in the SDSS fibre, HdeltaA above 4 A, Dn4000 below 1.45) stack to -0.0329 +- 0.0032
  mag, against -0.0384 +- 0.0018 mag for star-forming galaxies at the same Dn4000 and redshift (difference
  +0.0055 +- 0.0037 mag) and -0.0360 +- 0.0021 mag for weak-emission galaxies (+0.0032 +- 0.0038). All 89 E+A
  galaxies: +0.0047 +- 0.0026 mag weaker than their population controls. The paper's TP-AGB-on models at the
  same D4000 and HdeltaA predict -0.055 to -0.067 mag (stack system), 0.022-0.034 mag stronger than measured;
  TP-AGB off predicts -0.003 to -0.009 mag. The young E+A sit half way between. (Model ranges: matched in
  D4000 only, or in D4000 and HdeltaA.)
- **An HdeltaA excess among old galaxies changes nothing.** 872 weak-emission galaxies with HdeltaA more than 2
  robust sigma above the sequence (mostly Dn4000 > 1.75) stack to within 0.0003 +- 0.0009 mag of their
  controls, and so do the 851 of the mirror selection (HdeltaA deficit). At these Dn4000 the excess is mostly
  HdeltaA noise (the two tails are equally populated).
- **The young E+A still have PAH emission in the 12.3 arcsec aperture.** PAH 3.3 um above the local continuum:
  +21 % (young E+A), +28 % (star-forming controls), +8 % (weak-emission controls); old E+A +3 %. The fibre
  selects them as quenched; SPHEREx sees star formation or dust heating in the rest of the galaxy.
- **The D3/D2 step is noise.** The measured step (robust sigma 0.0301, 13.3 % beyond 5 %) is what each
  galaxy's own exposure residuals give when redrawn (0.0284, 12.4 %). Correcting every galaxy by its own step
  nearly doubles the intrinsic spread of the index (0.0095 to 0.0172 mag); removing the median step of each
  redshift bin doubles the redshift trend. Without the overlap exposures 81 % of the significant strong outliers
  stay beyond 3 sigma (with their original errors). No correction is applied; the earlier reading of the step as a mechanism of the strong
  tail is withdrawn (it is the noise the overlap exposures share with the index).
- **Inclination is real and removable by a cut.** Stacked by axis ratio, edge-on galaxies (q < 0.4) have a
  stronger bump than face-on ones (q >= 0.5) by 0.0021-0.0039 mag at Dn4000 below 1.8, and none at Dn4000 above
  1.8 (-0.0006 to +0.0014 mag), as dust would do. Face-on stacks keep the trend along the sequence (row means
  -0.0364 to -0.0435 mag, 0.0071 mag, against 0.0065 mag for all) and the HdeltaA effect at Dn4000 above 1.55
  (-0.0010 +- 0.0004 mag, against -0.0012 +- 0.0004); the flattening at Dn4000 1.55-1.68 was partly dust.
- **Against the late-epoch models, every cell lies between TP-AGB off and on, closer to on.** On the stacks'
  system (R = 41, continuous), cells are 0.001-0.011 mag weaker than the TP-AGB-on population (median 0.004 mag)
  and 0.020-0.026 mag stronger than TP-AGB off. The gap to TP-AGB on is 0.007-0.011 mag in the star-forming
  rows and 0.001-0.004 mag at Dn4000 above 1.7. The models also lie 1.3-1.7 A below the data in HdeltaA at fixed
  broad D4000 (late epochs, after the 0.28 A resolution shift), so only D4000 is used to match them.
- **Target 45124 is a star-contaminated D2 failure.** Its D2 exposures scatter by 43 % (D3: 5.5 %), 8 times the
  median galaxy's D2/D3 ratio; only 8 of 46,504 galaxies exceed a ratio of 3. A saturated SDSS star 4.2 mag
  brighter in z lies 24 arcsec away, just outside the 20 arcsec neighbour search. The blue window, all on D2,
  is 34 % low: the "bump" of -0.24 mag is that.

## 2. Post-starburst candidates

### 2.1 Selection and controls

All 46,504 galaxies with an index outside the Magellanic Clouds (the sparse parts of the plane, removed from the
cells, are kept here). Emission: galSpecLine `H_ALPHA_EQW` (negative for emission), fibre. HdeltaA excess:
HdeltaA minus the median of all galaxies in its Dn4000 bin (0.05), divided by that bin's robust spread (which
contains the HdeltaA measurement error, median 0.73 A).

| Set | Definition | Galaxies | median Dn4000 / HdeltaA / Halpha EW |
|---|---|---|---|
| young E+A | Halpha EW < 3 A, HdeltaA > 4 A, Dn4000 < 1.45 | 40 | 1.37 / 5.1 / 1.1 |
| old E+A | the same, Dn4000 >= 1.45 | 49 | 1.51 / 4.4 / 1.8 |
| HdeltaA excess | Halpha EW < 3 A, excess > 2 sigma, not E+A; 4 Dn4000 bins (edges 1.65, 1.8, 1.9) | 872 | 1.89 / -0.2 / 0.8 |
| HdeltaA deficit | Halpha EW < 3 A, excess < -2 sigma (mirror) | 851 | 1.83 / -3.2 / 0.6 |

Controls: for every candidate the three nearest unused galaxies in (Dn4000 / 0.025, redshift / 0.005) among the
galaxies of no set with abs(excess) < 1, either with Halpha EW < 3 A (`quiescent` controls) or any (`population`
controls). The median Dn4000 and redshift of candidates and controls agree within 0.001, except the quiescent
controls of the old E+A (Dn4000 0.004 higher) and of the young E+A (Dn4000 0.12 and redshift 0.0025 higher: few
weak-emission galaxies exist at Dn4000 1.37). The excess sets' controls are 1.4-2.5 A
lower in HdeltaA, as designed; the young E+A's population controls 1.9 A lower.

### 2.2 Results

```{figure} ../figures/sdss48k_review/fig14_post_starburst_stacks.png
:width: 820px
:alt: Stacked H-minus bump and SEDs of post-starburst candidates against controls

Figure 14. (a) The candidates in the Dn4000-HdeltaA plane over all galaxies (shading: 68, 95, 99.5 %). (b)
Stacked index against the stack's median Dn4000: candidates filled, population controls open circles, quiescent
controls open squares (offset by +-0.012 in Dn4000 for clarity); grey: mean of the five cells of each Dn4000 row
(figure 9). (c) Stacked continuum-normalised profiles of the young E+A and their controls (index in the legend).
(d) Whole-SED stacks of candidates divided by those of their controls.
```

| Set | candidates | population controls | quiescent controls | minus population | minus quiescent |
|---|---|---|---|---|---|
| young E+A | -0.0329 +- 0.0032 (40) | -0.0384 +- 0.0018 | -0.0360 +- 0.0021 | +0.0055 +- 0.0037 | +0.0032 +- 0.0038 |
| old E+A | -0.0396 +- 0.0026 (49) | -0.0426 +- 0.0016 | -0.0374 +- 0.0017 | +0.0031 +- 0.0030 | -0.0022 +- 0.0031 |
| all E+A | -0.0360 +- 0.0022 (89) | -0.0407 +- 0.0013 | -0.0378 +- 0.0016 | +0.0047 +- 0.0026 | +0.0018 +- 0.0028 |
| HdeltaA excess, Dn4000 < 1.65 | -0.0365 +- 0.0051 (16) | -0.0438 +- 0.0028 | -0.0391 +- 0.0024 | +0.0074 +- 0.0059 | +0.0026 +- 0.0057 |
| HdeltaA excess, 1.65-1.8 | -0.0410 +- 0.0020 (127) | -0.0390 +- 0.0011 | -0.0415 +- 0.0011 | -0.0020 +- 0.0023 | +0.0005 +- 0.0023 |
| HdeltaA excess, 1.8-1.9 | -0.0432 +- 0.0012 (338) | -0.0424 +- 0.0006 | -0.0422 +- 0.0007 | -0.0008 +- 0.0014 | -0.0010 +- 0.0014 |
| HdeltaA excess, > 1.9 | -0.0431 +- 0.0010 (391) | -0.0442 +- 0.0005 | -0.0443 +- 0.0005 | +0.0010 +- 0.0011 | +0.0012 +- 0.0012 |
| HdeltaA excess, all | -0.0427 +- 0.0008 (872) | -0.0428 +- 0.0004 | -0.0430 +- 0.0004 | +0.0001 +- 0.0009 | +0.0003 +- 0.0009 |
| HdeltaA deficit, all | -0.0418 +- 0.0008 (851) | -0.0423 +- 0.0004 | -0.0421 +- 0.0004 | +0.0005 +- 0.0009 | +0.0003 +- 0.0009 |

- **The E+A bump is weaker, not stronger.** Every E+A contrast against star-forming galaxies at the same Dn4000
  is positive (weaker bump), at 1.0-1.8 sigma per set; against weak-emission controls the sign is mixed. The
  profile of the young E+A (figure 14c) has the same shoulder, dip and peak as its controls, slightly lower
  across the feature window. Nothing in it looks like the enhancement the TP-AGB-on models give a recently
  quenched population (section 4).
- **The excess and deficit sets agree with their controls.** At Dn4000 above 1.65 the HdeltaA excess and the
  HdeltaA deficit sets are equally numerous (872 and 851) and both stack to their controls within 1 sigma: at
  these ages the excess is dominated by the HdeltaA measurement error, and the real intermediate-age light it
  contains (if any) does not change the bump by more than 0.002 mag.
- **Stellar population or aperture?** The SDSS fibre (3 arcsec) samples the centre; the SPHEREx aperture (12.3
  arcsec radius) the whole galaxy (median Petrosian half-light radius of the E+A: 2.2-2.7 arcsec). The young
  E+A's SED shows PAH 3.3 um at +21 % above the local continuum (population controls +28 %, quiescent controls
  +8 %) and +12 % at 4.6 um over the quiescent controls (figure 14d): within the aperture they are still
  forming stars or have dust heated by young stars. Their SPHEREx light mixes the quenched centre with a
  star-forming outside. The old E+A have little PAH (+3 %).
- **Numbers.** 40 and 49 galaxies give errors of 0.003 mag; a contrast of 0.005 mag needs about 3 times as many
  galaxies for 3 sigma. A looser selection (HdeltaA > 3 A gives 165 galaxies) or a larger SPHEREx sample would
  reach it.

## 3. Detector step and inclination

### 3.1 The D3/D2 step is noise

```{figure} ../figures/sdss48k_review/fig15_inclination_and_detector_controls.png
:width: 820px
:alt: D3-D2 step against noise nulls, index against redshift, and stacks by inclination

Figure 15. (a) The per-galaxy D3-D2 step (median quadratic-fit residual of D3 minus D2 exposures in observed
1.616-1.668 um) against two nulls with each galaxy's numbers of overlap exposures: Gaussian residuals with its
exposure scatter, and its own residuals outside the overlap drawn with replacement. (b) Median index residual
at fixed Dn4000 against redshift, as measured and after dividing every galaxy's D3 fluxes by (1 + the median
step of its redshift bin); triangles (right axis): that median step. (c) Stacked index of each Dn4000 row split
by SDSS r-band axis ratio q. (d) The 40 cells stacked with face-on galaxies only (q >= 0.5), one line per
HdeltaA fifth; dashed: row means of the cells with all galaxies.
```

| Test | Result |
|---|---|
| robust sigma of the step: measured / Gaussian null / empirical null | 0.0301 / 0.0278 / 0.0284 |
| beyond 5 %: measured / Gaussian / empirical | 13.3 % / 12.2 % / 12.4 % |
| intrinsic spread of the index: as measured / own step removed / shuffled step removed / median step of the redshift bin removed | 0.0095 / 0.0172 / 0.0196 / 0.0099 mag |
| median step against redshift (0.030-0.035 to 0.055-0.060) | +0.0039 to -0.0043 (errors 0.0004-0.0005) |
| median step against Petrosian radius (< 2 to > 5 arcsec) | -0.0038 to +0.0008 |
| index residual against redshift: as measured / median step removed | +0.0026 to -0.0016 / +0.0053 to -0.0026 mag |
| significant strong outliers still beyond 3 sigma without the overlap exposures | 81 % (weak: 55 %) |

- The spread of the per-galaxy step is that of noise from 3-4 exposures per detector; the empirical null
  reproduces the tails. At most a real rms step of about 1 % could hide in the difference of the robust sigmas.
- Removing each galaxy's own step makes every index noisier: the step cannot be measured galaxy by galaxy well
  enough to correct it. The correlation of the step with the index residual in the tails (previous report,
  section 3.3) comes from the D3 overlap exposures that also sit in the feature window (median 1-2 per
  galaxy): their noise enters both. Without them the strong tail survives.
- The population median step does change with redshift (+0.4 % to -0.4 %) and size, but removing it as a gain
  offset doubles the redshift trend of the index instead of reducing it: it is not a gain step. A step that
  moves with redshift at fixed observed wavelength fits a resolution or bandpass difference of D2 and D3 across
  the bump's structure, or the aperture loss with PSF size; neither is tested. Either way it is at most 0.002
  mag of index and is not applied.

### 3.2 Inclination

| Dn4000 row (median) | q < 0.4 | 0.4-0.5 | q >= 0.5 | edge-on minus face-on |
|---|---|---|---|---|
| 1.26 | -0.0391 (1,331) | -0.0356 | -0.0364 (3,665) | -0.0027 +- 0.0007 |
| 1.38 | -0.0415 (1,902) | -0.0385 | -0.0387 (3,091) | -0.0028 +- 0.0006 |
| 1.49 | -0.0423 (2,111) | -0.0412 | -0.0401 (2,888) | -0.0022 +- 0.0006 |
| 1.61 | -0.0445 (2,091) | -0.0427 | -0.0406 (2,888) | -0.0039 +- 0.0006 |
| 1.75 | -0.0436 (1,413) | -0.0407 | -0.0415 (3,610) | -0.0021 +- 0.0007 |
| 1.83 | -0.0422 (1,014) | -0.0425 | -0.0416 (4,049) | -0.0006 +- 0.0007 |
| 1.90 | -0.0426 (733) | -0.0424 | -0.0429 (4,401) | +0.0002 +- 0.0007 |
| 1.97 | -0.0421 (568) | -0.0428 | -0.0435 (4,586) | +0.0014 +- 0.0008 |

- Where galaxies are discs with dust (Dn4000 below 1.8) the edge-on ones have a 0.002-0.004 mag stronger bump,
  as the curvature of a dust attenuation curve gives for A_V of about 1-2 (previous report, 3.4); among the old
  galaxies, where q measures intrinsic shape, there is none. The stacks confirm the individual-index result at
  3-6.5 sigma per row.
- **Face-on cells** (q >= 0.5, 63 % of the galaxies, 464-931 per cell, errors 0.0005-0.0009 mag): row means
  -0.0364, -0.0387, -0.0401, -0.0406, -0.0416, -0.0417, -0.0429, -0.0435 mag. The trend along the sequence is
  0.0071 mag and now monotonic; the flattening at Dn4000 1.55-1.68 in the full stacks was the edge-on discs of
  that row. Face-on minus all, per cell: -0.0004 to +0.0024 mag (median +0.0004).
- **HdeltaA at fixed Dn4000, face-on**: highest minus lowest fifth +0.0028, +0.0017, -0.0001, -0.0018, -0.0005,
  -0.0003, -0.0015, -0.0009 mag; above Dn4000 1.55 combined -0.0010 +- 0.0004 mag (all galaxies -0.0012 +-
  0.0004). Unchanged by inclination.
- **Individual indices.** A correction by the median residual of each (Dn4000 row, q bin) relative to face-on
  galaxies (-0.005 to +0.002 mag) lowers the intrinsic spread only from 0.0095 to 0.0094 mag and leaves the
  tails (s < -3: 79 to 77; s > 3: 94 to 98). For population work a face-on cut is simpler than a correction.

## 4. The stacks against the late-epoch models

### 4.1 On the stacks' system

The populations of the H-bump paper give the bump at R = 100. For 264 SSPs of the H-bump project (ages 0.5-13
Gyr, four metallicities, TP-AGB off and on) the index was measured both at R = 100 and as on a stack (R = 41,
averaged on the 0.005 um stack grid, `profile_index`). The difference is a straight line in the R = 100 index
(residual 0.0002 mag): TP-AGB off -0.0016 to +0.0003 mag, TP-AGB on +0.0009 to +0.0055 mag (the strongest bumps
are smoothed most); R = 35 instead of 41 changes it by 0.0002-0.0003 mag. The populations were converted with
these lines, and their HdeltaA lowered by 0.28 A (resolution, review section 8.4).

```{figure} ../figures/sdss48k_review/fig16_stacks_against_late_models.png
:width: 820px
:alt: Stacked bump of cells and E+A against the late-epoch model populations

Figure 16. (a) Stacked index of the cells (covered galaxies; colour by HdeltaA fifth) and of the E+A sets
against broad D4000, with the median of the model populations on the stack system: solid, epochs after 10 Gyr
(band: after 8 and 12 Gyr); dotted, all epochs after 1 Gyr (the paper's population). (b) Cell stack minus the
TP-AGB-on prediction at the galaxies' broad D4000. (c) Broad D4000 and HdeltaA of the data and of the late-epoch
populations (68 and 95 % contours). (d) Index on the stack system minus that at R = 100 for the SSPs, with the
straight lines used to convert the populations.
```

### 4.2 Cells

The late-epoch populations (after 10 Gyr) lie 1.3-1.7 A below the data in HdeltaA at fixed broad D4000 (2.2 A
above D4000 2.2; figure 16c), even after the resolution shift: a match in both indices covers only 16 % of the
galaxies, all on the low-HdeltaA side. Since the model bump at late epochs hardly depends on HdeltaA, each
galaxy is given the median model bump of its broad D4000 bin (0.04), which covers 88 % of the galaxies (all
with broad D4000 above 1.48); each cell is restacked with its covered galaxies only.

| Dn4000 row | broad D4000 | stack (covered) | TP-AGB off | TP-AGB on | stack minus on |
|---|---|---|---|---|---|
| 1.09-1.33 | 1.38-1.44 | -0.0373 to -0.0403 | -0.014 | -0.048 | +0.0075 to +0.0105 (10-21 % covered) |
| 1.33-1.43 | 1.54-1.56 | -0.0394 to -0.0402 | -0.015 | -0.048 | +0.0081 to +0.0089 |
| 1.43-1.55 | 1.66-1.68 | -0.0409 to -0.0413 | -0.016 | -0.049 | +0.0074 to +0.0079 |
| 1.55-1.68 | 1.79-1.82 | -0.0411 to -0.0433 | -0.018 | -0.047 | +0.0038 to +0.0055 |
| 1.68-1.79 | 1.92-1.93 | -0.0410 to -0.0427 | -0.020 | -0.044 | +0.0010 to +0.0026 |
| 1.79-1.87 | 2.01 | -0.0408 to -0.0423 | -0.021 | -0.044 | +0.0016 to +0.0032 |
| 1.87-1.93 | 2.07-2.08 | -0.0422 to -0.0434 | -0.021 | -0.045 | +0.0016 to +0.0029 |
| 1.93-2.14 | 2.14-2.17 | -0.0428 to -0.0441 | -0.020 | -0.047 | +0.0027 to +0.0042 |

- Every cell lies between the two model sets: 0.020-0.026 mag stronger than TP-AGB off, 0.001-0.011 mag weaker
  than TP-AGB on (median 0.004 mag; errors 0.0005-0.0009 mag). On a linear scale from off (0) to on (1), the
  cells of the three youngest rows sit at 0.69-0.78 and the others at 0.81-0.96.
- The shapes differ: the TP-AGB-on model is nearly flat with D4000 (-0.048 to -0.044 mag) and strongest at
  broad D4000 1.5-1.7, while the data strengthen from -0.039 to -0.043 mag towards old galaxies. The largest
  gap is in the youngest rows, where the late-epoch models are quenched populations and the galaxies are
  forming stars, with dust and emission that the models lack: they do not describe the same objects.
- The epoch cut matters little: between epochs after 8, 10 and 12 Gyr the predictions of a cell differ by at
  most 0.006 mag (TP-AGB on) and 0.007 mag (off) (band in figure 16a).

### 4.3 E+A

| Set | broad D4000 | stack | on, after 10 Gyr | on, all epochs after 1 Gyr (D4000 only / D4000 and HdeltaA) | off, all epochs (same) |
|---|---|---|---|---|---|
| young E+A | 1.55 | -0.0329 +- 0.0032 | -0.0485 | -0.0549 / -0.0668 (58 % covered) | -0.0091 / -0.0027 |
| old E+A | 1.74 | -0.0396 +- 0.0026 | -0.0476 | -0.0509 / none covered | -0.0147 / none |

The paper's population (all epochs, including those soon after quenching) predicts its strongest TP-AGB-on bumps
exactly at the young E+A's place in the D4000-HdeltaA plane (-0.067 mag where both indices match). The young E+A
show -0.033 mag: half way between TP-AGB off and on, and weaker than the ordinary galaxies around them. With the
aperture caveat of 2.2 (the SPHEREx light is not all post-starburst), this is the most direct test of the
paper's post-starburst prediction in this sample, and it does not support it. 40 galaxies make it a 1-2 sigma
statement against the controls but a 7-11 sigma one against the TP-AGB-on prediction (stack error only).

## 5. Target 45124 and failed detectors

```{figure} ../figures/sdss48k_review/fig17_target_45124.png
:width: 820px
:alt: Exposures of target 45124, the per-detector scatter of all galaxies, and its optical image

Figure 17. Target 45124. (a) Aperture flux of all 402 exposures against observed wavelength by detector;
shading: the index windows in the observed frame. (b) Exposures in the fit window, F_lambda divided by the
median of its D3 exposures, against rest wavelength (crosses: rejected by the quadratic screen). (c) D2/D3
exposure scatter (median absolute difference of consecutive exposures of one detector) of all galaxies and of
the significant strong tail. (d) Legacy Survey DR10 z band, 60 arcsec; circles 12.3 and 20 arcsec.
```

- **What the exposures show.** D3 (feature and red windows): 3.5-4.0 mJy, scatter 5.5 %. D2 (blue window and
  below): 0.7-4.4 mJy, scatter 43 %, two branches, and exposures of the same day differing by a factor of 3.
  D1 and D4 scatter by 8 %. The two blue-window exposures average 2.56 mJy against 3.89 (feature) and 3.79 mJy
  (red window): the index is the D2 deficit, not a feature.
- **Why.** A saturated SDSS star (z 12.3 or brighter, the galaxy z 16.4) lies 24 arcsec to the north-east,
  outside the 20 arcsec neighbour search of the outlier study. With no neighbour subtraction in the aperture
  flux, its PSF wings and the background estimate around it depend on the detector and the position;
  on D2 they fail. The galaxy itself (Dn4000 1.26, HdeltaA 4.7 A, q 0.30) has nothing unusual.
- **How rare.** D2/D3 scatter ratio: median 1.06, 99.9th percentile 2.5; 45124 has 7.9. Only 8 galaxies exceed
  3 (one in the strong tail: 45124), and 3 have D2 more than 3 times the other inner detectors. The significant
  strong tail has a ratio above 2 no more often than all galaxies (1.3 % against 1.0 %).
- **Bright stars at 20-60 arcsec** (SDSS stars with z < 18, the brighter of PSF and model magnitude):

| Set | star brighter than the galaxy within 60 arcsec | star 2 mag brighter at 20-60 arcsec |
|---|---|---|
| apparent strong / weak | 61 % / 61 % | 12.0 % / 11.1 % |
| significant strong / weak | 38 % / 49 % | 8.9 % / 13.4 % |
| controls | 28 % | 6.7 % |

  Bright stars beyond 20 arcsec enter both tails, more the weak one: they add scatter, not strong bumps. A
  flag for a bright star within 60 arcsec and a per-detector scatter test would remove 45124-like cases.

## 6. Reading

- Along the star-forming to quiescent sequence the bump strengthens by 0.007 mag in face-on galaxies; it sits
  0.69-0.96 of the way from TP-AGB-off to TP-AGB-on late-epoch populations, closest to TP-AGB on for old
  galaxies.
- The post-starburst phase, where the TP-AGB-on models are most distinctive, shows the opposite of their
  prediction in the 89 E+A galaxies: a bump weaker than that of comparable galaxies and far weaker than the
  models'. The fibre-selected E+A are not post-starburst over the whole SPHEREx aperture (PAH), which dilutes
  but cannot reverse a 0.02-0.03 mag model enhancement unless the outer star-forming light dominates the
  aperture at 1.6 um.
- The index needs a face-on cut (or a dust term) for population comparisons; the D3/D2 step needs no correction;
  bright stars to 60 arcsec and per-detector failures should be flagged.
- Open: a larger post-starburst sample (looser HdeltaA cut, other SPHEREx data); aperture-matched optical
  indices (or SPHEREx indices within a fibre-sized aperture, not possible with the student's run); dust in the
  model comparison; the redshift dependence of the mean D3/D2 step.
