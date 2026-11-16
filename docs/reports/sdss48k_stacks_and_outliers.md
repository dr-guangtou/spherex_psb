# Stacked SEDs across the Dn4000-HdeltaA plane, and the strong H-minus bump outliers (SDSS 48k)

Date: 2026-11-16. Data: the student's SDSS 48k aperture photometry
(`/Users/shuang/data/spherex/spherex_sdss48k_phot`) with the corrections and the per-galaxy bump index of the
review (`sdss48k_photometry_review.md`, section 8). The SDSS indices are taken as they are (MPA-JHU DR8
`galSpecIndx`, emission-subtracted Dn4000 and HdeltaA, as in the input catalogue). Scripts:
`scripts/sdss48k_review/stack_sed_and_bump.py`, `investigate_bump_outliers.py`, `make_stack_figures.py`.
Results: `/Users/shuang/data/spherex/results/sdss48k_hminus/` (`stack_*`, `outlier_*`, `sdss_shapes.parquet`).
Figures 9-13 in `docs/figures/sdss48k_review/`.

## 1. Summary

- **The bump follows the sequence, weakly.** In 40 equal-number cells (1,150 galaxies each) of the
  Dn4000-HdeltaA plane the stacked index goes from -0.036/-0.038 mag in the star-forming corner to -0.043/-0.044
  mag among the oldest galaxies; bootstrap errors are 0.0005-0.0007 mag per cell. Most of the change is between
  Dn4000 1.1 and 1.55 (row means -0.0368, -0.0397, -0.0410 mag), then it flattens (-0.042 to -0.043 mag).
- **HdeltaA at fixed Dn4000 adds little.** Within a Dn4000 row the five HdeltaA cells span 0.0004-0.0025 mag.
  At Dn4000 1.55-2.14, the highest-HdeltaA fifth (towards post-starburst) has a bump stronger than the lowest
  fifth by 0.0012 +- 0.0004 mag (five rows combined); in the star-forming row the sign is reversed (+0.0019
  +- 0.0009 mag). These equal-number cells do not isolate true post-starbursts (sections 2.3 and 4).
- **The stacked profile has the shape of the TP-AGB-on model.** Divided by each galaxy's own pseudo-continuum
  and stacked, the 1.44-1.84 um profile has a shoulder at 1.54 um, a dip at 1.58 um and a broad peak at
  1.62-1.72 um at +5 %; a 10 Gyr solar SSP with TP-AGB on, at R = 41, has the same features at the same
  wavelengths, and TP-AGB off a peak half as high (figure 11a). The profile is the same in every cell to about
  1 % and the same in the lowest and highest redshift thirds, so it is in the rest frame.
- **The whole SED changes far more than the bump.** Relative to the stack of all galaxies, star-forming cells
  have up to +57 % more flux at the 3.3 um PAH feature and +43 % at 4.6 um, Pa-alpha and Br-alpha in emission and
  a rise from 2 um; quiescent cells are 15-19 % below the mean at 3.3-4.6 um (figure 10).
- **Strong-bump outliers are mostly noise and contamination, not a population.** Once each galaxy's error and
  the population's intrinsic spread (0.0095 mag) are counted, the significance distribution is close to a
  unit Gaussian (robust sigma 0.96). The 457 galaxies that look like strong-bump outliers (more than 0.06 mag
  above the median) are mirrored by 476 on the weak side, and both groups look the same: 91 % are within
  3 sigma, errors 3.5 times the median, and 35-41 % have a star brighter than the galaxy within 20 arcsec
  (controls: 3 %). The significant tail (s < -3) holds 79 galaxies where a Gaussian gives 63; the weak side
  holds 97.
- **What is left points to systematics.** The significant strong tail is enriched in a positive D3-D2 flux step
  of the galaxy (11.5 % above +5 %, controls 6.6 %; the weak tail is enriched in negative steps; *revised in
  `sdss48k_stack_followups.md`: the step is noise shared with the index, not a mechanism*) and in
  edge-on discs (axis ratio below 0.3: 23 %, controls 13 %). Over the whole sample, galaxies with axis ratio
  below 0.3 have a stronger bump by 0.0028 +- 0.0010 mag, what a dust screen of A_V = 1-2 produces through the
  curvature of the attenuation curve (0.0017-0.0031 mag, measured). No outlier group shows an optical
  signature (BPT class, sSFR, Halpha) different from its controls.

## 2. Stacks across the Dn4000-HdeltaA plane

### 2.1 Sample and cells

| Step | Choice |
|---|---|
| Galaxies | 46,504 with a measured bump index; 465 (1 %) in the sparsest parts of the plane removed (smoothed 2-D histogram, density below its 1st percentile); 46,039 stacked |
| Cells | Dn4000 cut at its octiles; within each Dn4000 bin HdeltaA cut at its own quintiles; 40 cells of 1,150-1,151 galaxies. The HdeltaA fifths run from below to above the sequence at each Dn4000 |
| Exposures | aperture flux with the solid-angle correction (review, section 8.1), corrected for Galactic extinction (run's `ebv`, Gordon et al. 2023 curve, R_V = 3.1, at the observed wavelength); F_lambda = F_nu / lambda^2; 15.8 million exposures |

The cells follow the sequence that MPA-JHU's sSFR traces (figure 9a): median log sSFR -10.0 per yr and 89 %
BPT star forming in the lowest Dn4000 row, -12.3 per yr and 8 % in the highest.

### 2.2 Two stacks, as asked

1. **Whole SED.** Each galaxy normalised by the median F_lambda of its exposures at rest 1.10-1.25 um (no strong
   lines: Pa-gamma 1.094 and [Fe II] 1.257 um are outside); per galaxy the mean in each rest bin (ln lambda step
   0.01, 0.70-4.90 um); per cell and bin the mean over galaxies after clipping galaxies more than 5 robust sigma
   from the bin median. The bump index of this stack is measured on a 0.005 um grid built the same way.
2. **Bump only.** Each galaxy's exposures at rest 1.44-1.84 um screened exactly as for its own index
   (quadratic, 5 robust sigma) and divided by its own straight-line pseudo-continuum (band means of the blue and
   red windows); the ratios stacked on the 0.005 um grid. The index of this stack uses the pseudo-continuum of
   the stacked profile.

For both, the index is measured on the stacked profile with every grid bin weighted equally in wavelength:
the galaxies' exposures fall at different rest wavelengths, so the stack is close to continuous sampling at
the SPHEREx resolution, not the irregular sampling of one galaxy. Errors: bootstrap over galaxies (300 draws).

```{figure} ../figures/sdss48k_review/fig9_stacks_on_dn4000_hdelta_plane.png
:width: 820px
:alt: Stacked H-minus bump index in cells of the Dn4000-HdeltaA plane

Figure 9. (a) The 40 cells in the Dn4000-HdeltaA plane, coloured by the median MPA-JHU sSFR of their galaxies;
contours: 68 and 95 % of the galaxies. (b) The same cells coloured by the stacked bump index (continuum-normalised
stack; stronger bump darker). (c) Stacked index against the cell's median Dn4000, one line per HdeltaA fifth;
dotted: all galaxies. (d) The two other estimates minus the continuum-normalised stack: the index of the stacked
whole SED, and the mean of the galaxies' own indices, with their errors.
```

### 2.3 The bump across the plane

Stacked index of the continuum-normalised profile (mag; bootstrap errors 0.0005-0.0007 mag):

| Dn4000 | median HdeltaA (lowest to highest fifth) | median log sSFR | lowest | 2nd | 3rd | 4th | highest HdeltaA |
|---|---|---|---|---|---|---|---|
| 1.09-1.33 | 2.9 to 5.8 | -10.0 | -0.0383 | -0.0370 | -0.0366 | -0.0358 | -0.0364 |
| 1.33-1.43 | 1.5 to 4.7 | -10.2 | -0.0397 | -0.0398 | -0.0401 | -0.0398 | -0.0392 |
| 1.43-1.55 | 0.3 to 3.6 | -10.5 | -0.0410 | -0.0408 | -0.0412 | -0.0408 | -0.0413 |
| 1.55-1.68 | -0.9 to 2.1 | -10.9 | -0.0419 | -0.0411 | -0.0431 | -0.0420 | -0.0433 |
| 1.68-1.79 | -2.0 to 0.5 | -11.6 | -0.0415 | -0.0410 | -0.0418 | -0.0427 | -0.0425 |
| 1.79-1.87 | -2.4 to -0.5 | -12.0 | -0.0409 | -0.0422 | -0.0419 | -0.0423 | -0.0422 |
| 1.87-1.93 | -2.7 to -1.1 | -12.1 | -0.0422 | -0.0423 | -0.0433 | -0.0429 | -0.0434 |
| 1.93-2.14 | -2.9 to -1.5 | -12.3 | -0.0428 | -0.0431 | -0.0441 | -0.0428 | -0.0439 |

- **Along Dn4000.** Row means -0.0368, -0.0397, -0.0410, -0.0423, -0.0419, -0.0419, -0.0428, -0.0433 mag: the bump
  strengthens by 0.0042 mag from the star-forming row to Dn4000 1.43-1.55 and by another 0.0023 mag to the
  oldest row. The same trend as the individual indices (review, figure 4), now with errors 20-30 times smaller.
- **Along HdeltaA at fixed Dn4000.** The five cells of a row agree within 0.0004-0.0025 mag (chi-square for a
  constant 0.5-10 for 4 degrees of freedom). Highest minus lowest HdeltaA fifth: +0.0019, +0.0005, -0.0003,
  -0.0014, -0.0010, -0.0013, -0.0012, -0.0011 mag (errors 0.0007-0.0009 mag) from the youngest to the oldest row:
  above Dn4000 1.55 the high-HdeltaA side has the stronger bump by 0.0012 +- 0.0004 mag combined; in the
  star-forming row the high-HdeltaA side (the most star-forming cells, Halpha equivalent width up to 35 A) has
  the weaker one.
- **Not from sampling or redshift.** The mean SPHEREx sampling bias of the TP-AGB-on template is 0.0018-0.0021
  mag in every Dn4000 row and the median redshift 0.047-0.049, so neither drives the trends. For the three
  redshift thirds of the whole sample (median z 0.037, 0.049, 0.056) the stacked index is -0.0407, -0.0418,
  -0.0413 mag, a spread of 0.0011 mag, against 0.0022 mag for the mean of the individual indices: the stack's
  near-continuous sampling removes most of the redshift trend that section 8.4 of the review traced to sampling.
- **The three estimates agree.** The index of the stacked whole SED is 0.0015 mag stronger to 0.0004 mag weaker
  than the continuum-normalised stack; the mean of the galaxies' own indices differs by -0.0031 to +0.0010 mag,
  with larger errors because it is not clipped (figure 9d).
- **What the cells are.** Equal-number cells place the top HdeltaA fifth at Dn4000 1.43-1.68 at median HdeltaA
  2.1-3.6 A and median sSFR 10^-10.5 to 10^-10.9 per yr: the upper edge of the sequence, mostly galaxies with
  ongoing star formation, not the post-starbursts that sit several angstroms above it. A test of the
  post-starburst phase needs a selection by emission lines and an HdeltaA excess (todo).

```{figure} ../figures/sdss48k_review/fig11_stacked_bump_profiles.png
:width: 820px
:alt: Stacked continuum-normalised H-minus bump profiles

Figure 11. Stacked profiles F_lambda / F_c, each galaxy divided by its own pseudo-continuum. (a) All 46,039
galaxies (grey band: bootstrap error), the lowest and highest redshift thirds, and a 10 Gyr solar SSP of the
H-bump project at R = 41 with TP-AGB off and on, divided by its pseudo-continuum in the same way (its index in
brackets). (b)-(i) The five HdeltaA fifths of each Dn4000 bin, colours as in figure 10. Blue: pseudo-continuum
windows; orange: feature window.
```

**The profile.** All galaxies: a shoulder at 1.54 um (+2 %), a dip at 1.58 um, a broad peak at 1.62-1.72 um
(+5 %) and a fall through the red window. The 10 Gyr TP-AGB-on SSP has the same three features at the same
wavelengths and almost the same amplitude (index -0.046 mag at R = 41 against -0.041 mag for the stack); TP-AGB
off has a peak of +3 % and a deeper dip (index -0.021 mag). The lowest and highest redshift thirds keep the
shoulder and the dip at the same rest wavelength (an observed-frame feature would move by 0.03 um between them);
they differ by up to 1 % at 1.69-1.74 um. Across the 40 cells the profiles agree to about 1 %, which is why the
index changes so little.

### 2.4 The whole SED

```{figure} ../figures/sdss48k_review/fig10_stacked_seds.png
:width: 820px
:alt: Stacked SPHEREx SEDs in cells of the Dn4000-HdeltaA plane

Figure 10. (a) Stacked SED of all galaxies, F_lambda normalised at 1.17 um (band: bootstrap error; shading: the
bump windows). (b)-(i) Each cell's stack divided by the stack of all galaxies, one panel per Dn4000 bin, colour
by HdeltaA fifth. Dotted: Pa-alpha 1.875, CO 2.29, PAH 3.29 and Br-alpha 4.05 um.
```

Cell stack divided by the stack of all galaxies (bootstrap error about 0.5 % at 3.3 um):

| Dn4000 | HdeltaA fifth | 2.2 um | 3.29 um | PAH above local continuum | 4.6 um |
|---|---|---|---|---|---|
| 1.09-1.33 | lowest / highest | 0.99 / 1.03 | 1.21 / 1.57 | +0.17 / +0.41 | 1.18 / 1.43 |
| 1.43-1.55 | lowest / highest | 1.03 / 1.06 | 1.07 / 1.20 | +0.02 / +0.09 | 1.08 / 1.20 |
| 1.55-1.68 | lowest / highest | 1.01 / 1.06 | 0.96 / 1.10 | -0.04 / +0.01 | 0.98 / 1.12 |
| 1.93-2.14 | lowest / highest | 1.00 / 0.99 | 0.84 / 0.84 | -0.12 / -0.12 | 0.83 / 0.84 |

- Over 1.0-1.8 um every cell agrees with the mean to 3.6 % or better (median cell 1.2 %). At 0.75 um the
  star-forming cells are 6 % above the mean and the oldest 2-3 % below it (bluer and redder optical-NIR colours,
  after normalisation at 1.17 um).
- In the star-forming rows the high-HdeltaA side has the strongest PAH 3.3 um feature, the strongest Br-alpha and
  Pa-alpha and a continuum rising from 2 um (hot dust); the dip of the quiescent cells at 3.3 and 4.05 um is the
  mean's PAH and Br-alpha, which they lack.
- At Dn4000 1.55-1.68 the highest HdeltaA fifth has a smooth red excess (+6 % at 2.2 um, +12 % at 4.6 um) with
  almost no PAH (+0.01): the clearest SED difference along the HdeltaA direction outside the star-forming rows.
  What it is (hot dust, intermediate-age populations, aperture effects) is not tested.
- The aperture flux is not a total flux and its aperture correction changes with wavelength and galaxy size
  (review, section 7); the ratios to the mean cancel the part common to all cells, not the size differences
  between cells.

## 3. Strong-bump outliers among the individual measurements

### 3.1 Definitions

Residual: a galaxy's index minus the running median at its Dn4000 (bins of 0.05). Significance s: residual
divided by the quadrature sum of the galaxy's error and the intrinsic spread of the population, 0.0095 mag (robust
spread of the residuals minus the median error in quadrature). Sets, each with its mirror on the weak side as
the reference for noise and symmetric systematics:

| Set | Definition | Strong side | Weak side |
|---|---|---|---|
| apparent | residual beyond 0.06 mag (about 1 % per side) | 457 | 476 |
| significant | s beyond 3 | 79 | 97 |
| controls | three per strong outlier, abs(s) < 2, same redshift (0.0025) and Dn4000 (0.1) cell | 1,479 | |

Tails against a unit Gaussian (46,504 galaxies; expected per side 63 / 1.5 / 0.01):

| abs(s) > | strong side | weak side |
|---|---|---|
| 3 | 79 | 97 |
| 4 | 5 | 8 |
| 5 | 1 | 3 |

```{figure} ../figures/sdss48k_review/fig12_bump_outliers.png
:width: 820px
:alt: Diagnostics of the strong H-minus bump outliers

Figure 12. (a) Significance of all galaxies against a unit Gaussian. (b) Residual against the index error;
dashed: the apparent limit (0.06 mag), solid: s = 3. (c) Median residual against the SDSS r-band axis ratio, all
galaxies. (d) Fraction of each set with: a star brighter than the galaxy within 20 arcsec; neighbours with more
than 10 % of the galaxy's z-band flux within 20 arcsec; per-exposure scatter above 6 %; abs(s) < 2 after removing
one visit; a D3-D2 flux step above +5 % or below -5 %; axis ratio below 0.3. (e) Stacked continuum-normalised
profiles of the significant sets and the controls; dotted: the strong set stacked in the observed frame (at
its median redshift). (f) Fraction of galaxies with s < -3 and s > +3 against axis ratio; dashed: Gaussian.
```

### 3.2 The apparent outliers: noisy, contaminated photometry

What stands out in a plot of the individual indices is noise. Of the 457 apparent strong outliers, 91 % are
within 3 sigma and 60 % within 2 sigma of the median given their own errors (median error 0.057 mag, against
0.016 for all galaxies). The weak side is their mirror image in every diagnostic:

| | apparent strong | apparent weak | controls |
|---|---|---|---|
| median error (mag) | 0.057 | 0.049 | 0.016 |
| per-exposure scatter above 6 % | 73 % | 68 % | 8 % |
| star brighter than the galaxy within 20 arcsec | 35 % | 41 % | 3 % |
| neighbours above 10 % of the galaxy's flux within 20 arcsec | 66 % | 70 % | 23 % |
| ecliptic latitude within 10 deg | 25 % | 28 % | 18 % |

(Neighbours: SDSS DR17 PhotoPrimary objects, z-band model magnitudes, from SkyServer; aperture radius 12.3
arcsec.) The aperture flux has no neighbour subtraction (review, section 7): a star near the aperture adds a
variable fraction of its flux, exposure by exposure as the PSF and the pixel phase change, which the error
budget partly captures (large errors) and which goes both ways.

### 3.3 The significant outliers

| | strong (s < -3) | weak (s > +3) | controls |
|---|---|---|---|
| galaxies | 79 | 97 | 1,479 |
| median residual (mag) | -0.062 | +0.061 | 0.000 |
| median error (mag) | 0.015 | 0.016 | 0.016 |
| per-exposure scatter above 6 % | 8 % | 10 % | 8 % |
| star brighter than the galaxy within 20 arcsec | 4 % | 26 % | 3 % |
| neighbours above 10 % within 20 arcsec | 22 % | 40 % | 23 % |
| abs(s) < 2 after removing the most influential visit | 9 % | 7 % | |
| median abs(s) after removing it | 2.5 | 2.7 | |
| D3-D2 step above +5 % / below -5 % | 11.5 % / 2.6 % | 4.2 % / 13.5 % | 6.6 % / 7.6 % |
| axis ratio below 0.3 | 23 % | 16 % | 13 % |
| BPT star forming (classes 1-2) | 38 % | 44 % | 43 % |

- **Not a single bad visit.** Exposures were grouped by observing day; removing the visit that moves the index
  most towards the median leaves 91 % of the strong outliers beyond 2 sigma. Splitting each galaxy's visits
  alternately into two halves, the halves agree (no strong outlier with the halves more than 3 sigma apart;
  only 41 % have enough exposures in both halves). The excess is spread over the visits.
- **Not contamination.** Neighbours and stars occur as often as in the controls (the weak tail, by contrast, has
  more bright stars: 26 %).
- **Not an observed-frame artefact.** Stacked at the median redshift in the observed frame the strong set's
  excess is as sharp as in the rest frame (figure 12e); with 79 galaxies at z 0.03-0.06 this test is weak.
- **A per-galaxy detector step.** The index compares the blue window, which falls on D2, with the feature and red
  windows, which fall on D3 (for the median galaxy every blue exposure is D2 and every feature exposure D3). A
  galaxy whose D3 aperture flux is high relative to D2 has a stronger bump. Where both detectors observe the
  same wavelength (observed 1.616-1.668 um) the strong outliers have a mean step of +1.3 % (controls -0.2 %,
  weak outliers -1.6 %), and the tails are enriched in large steps of the matching sign. The step is measured
  from a few exposures per galaxy, so it identifies the mechanism but cannot correct galaxy by galaxy.
  *Revised (`sdss48k_stack_followups.md`, section 3.1): the step's spread is that of noise, and the D3
  overlap exposures also sit in the feature window, so their noise enters both; without them 81 % of the strong
  tail remains. The step is not the mechanism.*
- **Edge-on discs.** 23 % of the strong outliers have axis ratio below 0.3 (controls 13 %); four of the six most
  significant are edge-on or strongly inclined (figure 13). See 3.4.
- **Optical properties** (BPT class, sSFR, Halpha, Dn4000, HdeltaA) are those of the controls: the strong
  outliers are not a distinct kind of galaxy.

The excess over a Gaussian is 16 galaxies on the strong side and 34 on the weak side; both tails are slightly
heavier than Gaussian, the weak one more so and with more stars nearby. There is no evidence for a population of
galaxies with an anomalously strong bump.

### 3.4 Inclination and dust (all galaxies)

SDSS r-band axis ratio (exponential or de Vaucouleurs fit by fracDeV) of the spectrum's photometric object, from
SkyServer for 46,238 galaxies:

| axis ratio | galaxies | median residual (mag) | s < -3 | s > +3 |
|---|---|---|---|---|
| < 0.3 | 5,626 | -0.0028 +- 0.0010 | 0.32 % | 0.27 % |
| 0.3-0.4 | 5,725 | -0.0003 +- 0.0006 | 0.21 % | 0.10 % |
| 0.4-0.6 | 11,457 | +0.0003 to +0.0005 | 0.15-0.18 % | 0.27-0.36 % |
| 0.6-1.0 | 23,430 | +0.0003 to +0.0008 | 0.10-0.17 % | 0.03-0.19 % |

(Gaussian: 0.13 % per side.) Edge-on galaxies have a stronger bump by about 0.003 mag at fixed Dn4000, and their
strong tail is 2-3 times the rate of round ones. Dust can do this: a foreground screen with the Gordon et al.
(2023) curve deepens the index by 0.0009 / 0.0017 / 0.0031 mag for A_V = 0.5 / 1 / 2 (Calzetti curve: 0.0010 /
0.0017 / 0.0026 mag), through the curvature of the attenuation curve across 1.49-1.79 um that a straight
pseudo-continuum does not remove. The index is therefore not dust-free at the 0.001-0.003 mag level; the
models of the H-bump paper are dust-free. Size does not matter (Petrosian half-light radius: Spearman -0.003).

```{figure} ../figures/sdss48k_review/fig13_bump_outlier_gallery.png
:width: 820px
:alt: The most significant strong-bump outliers and three apparent outliers

Figure 13. Top two rows: the six most significant strong-bump galaxies; bottom row: three apparent outliers
(large residual, small significance) with the brightest nearby stars. Points: kept exposures divided by the
galaxy's pseudo-continuum, coloured by detector. Inset: Legacy Survey DR10 z band (SDSS where not covered),
60 arcsec; solid circle: the 12.3 arcsec aperture, dotted: 20 arcsec. Text: index and error, s, Dn4000, HdeltaA,
axis ratio q, redshift.
```

The most significant galaxy (s = -5.6, index -0.237 +- 0.034 mag) is a faint, inclined star-forming disc
(Dn4000 1.26, HdeltaA 4.7 A, q 0.30) whose excess (20-35 %) peaks at 1.59 um and falls through the red window, a
shape unlike the stacked bump; it remains beyond 4.8 sigma without its most influential visit. It is unexplained
and worth a look at the exposures. *Explained in `sdss48k_stack_followups.md`, section 5: its D2 photometry
fails (scatter 43 %) next to a saturated star 24 arcsec away; the blue window is 34 % low.* In the next five the D2 points lie below the D3 points, the per-galaxy step
of 3.3. The three apparent outliers carry saturated stars within 20 arcsec.

## 4. Reading and next steps

- The 1.6 um bump changes by 0.0065 mag along the star-forming to quiescent sequence, mostly where Dn4000 rises
  from 1.1 to 1.55, and very little with HdeltaA at fixed Dn4000; its profile has the shape of the TP-AGB-on
  models everywhere. The SED beyond 2 um changes by tens of per cent across the same plane.
- The index carries 0.001-0.003 mag of dust (inclination) and a per-galaxy D3/D2 term; both are larger than the
  HdeltaA effect at fixed Dn4000 and comparable with the Dn4000 trend. Before reading the trend as stellar
  populations, control for inclination (axis ratio cut or a dust term) and for the D3/D2 step.
- Next: select post-starburst candidates by HdeltaA excess and weak emission (galSpecLine) and stack them against
  Dn4000-matched controls; repeat the stacks for face-on galaxies (axis ratio above 0.6); compare each cell with
  the late-epoch model populations on the same continuous-sampling system (R = 41) rather than with single SSPs.
  *Done in `sdss48k_stack_followups.md` (face-on cut at axis ratio 0.5).*
