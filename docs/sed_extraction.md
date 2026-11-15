# SED extraction for SDSS galaxies

The demonstration that this project ran in November 2026: forced Sersic photometry of six SDSS galaxies at
0.03 < z < 0.06 on every DR1 and QR3 wide-survey exposure that covers them, assembled into spectral energy
distributions (SEDs) and validated eight ways. This page gives the method, the numbers that matter and the
questions that remain.

:::{admonition} Outcome
:class: tip
2,225 exposures measured, 2,104 (95 %) used; all 102 channels of every galaxy filled; per-exposure
chi2/dof 0.9-2.3; forced-model and aperture estimators agree to 0.98-1.03 with no trend over 0.75-5 um;
injected galaxies recovered at 1.00-1.02; QR3 and DR1 agree at 1-2 %; a cross-code check against
tractorjax-spherex reproduces the expected 1.5 % (n = 1) and 6 % (n = 4) flux-convention offsets.
Open: the D1/D2 and D3/D4 detector steps, the total-flux convention, and the error floor of compact
galaxies.
:::

## Why forced photometry on exposures

Typical SDSS galaxies at these redshifts have r-band effective radii of 1.6 / 4.4 / 10.6 arcsec at the
5th / 50th / 95th percentiles of the parent sample (45,569 galaxies with log M* >= 10), against a 6.15 arcsec
pixel and a PSF with N_eff of 3-5 pixels: they are semi-resolved.[^study] A point-source fit, the mode in
which the IRSA Spectrophotometry Tool and most published work operate, recovers only 0.57-0.64 of an
exponential disc with R_e = 4 arcsec and 0.30-0.36 at 8 arcsec, with a wavelength dependence that
imprints a spurious colour of +0.05 to +0.2 mag between D1 and D6 (noise-free simulations over all ePSF
zones).[^study] A Sersic model with the shape fixed from optical imaging, fitted to each exposure with the
exposure's own ePSF, removes this; mosaics would instead smear the PSF by 1.3-1.6x and bin away the
per-exposure wavelength ([reduction page](reduction_analysis.md#mosaics-versus-exposures)).

```{figure} figures/sed_demo/fig1_sample.png
:width: 820px
:alt: Parent sample and the six galaxies

Figure 1. The parent sample (SDSS DR17 SkyServer, class GALAXY, zWarning = 0, 0.03 <= z <= 0.059, MPA-JHU log M* >= 10; 45,569 galaxies) in (a) the redshift-stellar-mass plane and (b) the Dn4000-HdA plane, and (c) the distribution of the r-band effective radius with the 6.15 arcsec SPHEREx pixel marked; the six demonstration galaxies are the coloured symbols used throughout.
```

## The six galaxies

Chosen to span the cases the full sample will present: a reference disc, a compact de Vaucouleurs galaxy, a
large disc, a galaxy with a bright neighbour, a galaxy outside the Legacy Survey footprint (SDSS catalogue
only), and a post-starburst galaxy.

| Galaxy | z | Profile (from SDSS) | Exposures found (DR1 / QR3) | Used | Rejected | Screened | chi2/dof per detector D1-D6 | Point-source / model flux |
|---|---|---|---|---|---|---|---|---|
| g1 reference | 0.046 | n = 1, R_e = 4.4" | 341 (296/45) | 316 | 13 | 12 | 1.1/1.4/1.5/1.6/1.1/1.0 | 0.65-0.74 |
| g2 compact | 0.058 | n = 4, R_e = 1.1" | 279 (279/0) | 265 | 9 | 5 | 1.1/1.2/1.2/1.3/1.1/1.0 | 0.88-0.90 |
| g3 large | 0.033 | n = 1, R_e = 12.4" | 418 (283/135) | 395 | 12 | 11 | 1.3/1.7/2.0/1.7/1.1/1.0 | 0.26-0.33 |
| g4 neighbour | 0.033 | n = 4, R_e = 1.9" | 420 (280/140) | 407 | 10 | 3 | 1.4/2.3/2.1/1.7/1.0/0.9 | 0.59-0.63 |
| g5 no legacy | 0.052 | n = 4, R_e = 4.8" | 393 (244/149) | 371 | 15 | 7 | 1.3/1.9/2.0/1.4/0.9/0.9 | 0.57-0.59 |
| g6 post-starburst | 0.052 | n = 1, R_e = 5.4" | 374 (259/115) | 350 | 13 | 11 | 1.2/1.3/1.5/1.1/1.0/1.0 | 0.56-0.64 |

Rejections before the fit are `model_weight_masked` (every target pixel flagged, mostly the DICHROIC
exposures at 2.416-2.426 um), `cutout_truncated` and `target_outside_cutout`; screening after the fit
removes chi2 outliers (near-target chi2/dof above 5 times the detector median), whole-cutout chi2 outliers
and exposures whose CWAVE lies outside the detector's range. The point-source control recovers 26-90 % of
the model flux, as the simulations predicted, with chi2/dof of 3-20 in D1-D4 where the galaxies are
resolved: the test can see an under-fitted profile.

## Method

Per exposure, on a 41 x 41 pixel cutout bundle (53 x 53 for the large galaxy) from spherex-retrieval
([data access](data_access.md#what-we-actually-fetch-cutout-bundles-with-spherex-retrieval)):

1. Sources: the target with its SDSS shape (n, R_e, b/a, position angle), and every Legacy Survey DR10
   Tractor source within 1.1 arcmin down to z = 21 (SDSS PhotoPrimary where DR10 is unavailable), with their
   catalogue shapes; shreds of the target are removed; an axis ratio below 0.2 is clipped to 0.2.
2. Templates: each Sersic profile rendered on the 5x oversampled ePSF grid of the zone chosen in
   parent-frame coordinates, convolved with that ePSF, integrated onto the native pixels. The core is
   sampled 32 x 32 per oversampled pixel in a 7 x 7 block around the centre; every tested shape is within
   0.2 % of a 64 x 64 brute-force total (the earlier 4 x 4 sampling lost up to 2.3 % of an n = 4 profile and
   made the loss depend on the cutout orientation).
3. Background: ZODI subtracted, then a basis of constant + CWAVE + CWAVE^2 across the cutout fitted jointly
   with the sources. This repairs the exposures next to the He I 1.083 um line (chi2/dof 5-9 to 1-2, fluxes
   changed by 5-9 %), which a plane in x and y cannot.
4. Mask: the IRSA tool's exclusion flags plus TRANSIENT, OVERFLOW and DICHROIC; NaN pixels removed; weights
   from VARIANCE.
5. Solve: one weighted linear least-squares solve for all source amplitudes and the background within a fit
   radius; the galaxy's wavelength is CWAVE at its pixel; MJy/sr to uJy with the Solid Angle Pixel Map.
6. Estimators: the forced-model flux; the model-corrected aperture flux at 1.5, 2, 2.5 and 3 pixels (data
   minus the fitted neighbours inside the aperture, flagged pixels filled with the model, divided by the
   model's fraction in those pixels); and a point-source fit as the negative control.
7. SED: exposures assigned to the nearest nominal channel of their detector; the channel flux is the
   error-weighted mean and its error the exposure-to-exposure scatter (with the formal error as fallback);
   Galactic extinction corrected with the Schlafly and Finkbeiner E(B-V).

```{figure} figures/sed_demo/g1_reference_fig2_image_qa.png
:width: 820px
:alt: Image QA for the reference galaxy

Figure 2 (reference galaxy). (a) Legacy Survey DR10 z image, 150 arcsec wide, with the target's model ellipse (orange), the fitted neighbours (green circles scaled by brightness), the 2 pixel aperture (blue dashed) and the fit radius (grey dotted). (b)-(d) For one typical exposure per detector (chi2/dof at the detector median): data, model and residual / sigma in a 19 x 19 pixel window, with masked pixels in pink.
```

```{figure} figures/sed_demo/g1_reference_fig3_diagnostics.png
:width: 820px
:alt: Per-exposure diagnostics of the reference galaxy

Figure 3 (reference galaxy). Per exposure against wavelength: (a) chi2/dof within the fit radius for the galaxy model (filled) and the point-source control (open); (b) the fraction of the target template's weight on masked pixels; (c) the fitted residual background (filled) and the ZODI model (open). Rejected and screened exposures are black symbols keyed by reason; the He I 1.083 um line is marked.
```

The whole pipeline ran unattended in 1 h 52 min for the six galaxies: 552-1,702 s of measurement per galaxy
(1.3-4.1 s per exposure; the galaxy with 141 sources in its model is the slowest) and 144-301 s of
validation. The code is `spherex_psb/extraction/` and `scripts/sed_demo/`.

## Results

```{figure} figures/sed_demo/g6_post_starburst_fig4_sed.png
:width: 820px
:alt: SED of the post-starburst galaxy

Figure 4 (post-starburst galaxy). (a) The model flux of every used exposure, coloured by detector, with formal errors; the binned model SED (black, error = channel scatter) and the binned corrected 2 pixel aperture SED (grey dashed); external photometry of the same convention (SDSS z model, 2MASS XSC total, Legacy Survey forced W1/W2) as open diamonds; rest-frame axis on top with the CaT, 1.6 um CO, 1.9 um water, 2.29 um CO, 3.3 um PAH and 4.6 um CO positions. (b) The ratio of the two estimators per exposure and binned.
```

```{figure} figures/sed_demo/fig7_all_seds_rest_frame.png
:width: 820px
:alt: All six rest-frame SEDs

Figure 7. The six binned model SEDs, corrected for Galactic extinction, in the rest frame, normalised at 1.6 um. All share the 1.6 um bump, the 1.9 um water band and the CO drop beyond 2.3 um; the three star-forming or post-starburst galaxies show the 3.3 um PAH feature and a flatter 3.5-5 um continuum.
```

The other galaxies' figures 2-4 are in `docs/figures/sed_demo/` and listed in the report.

## Validation

### Estimator consistency

Median model / corrected-aperture (2 pixel) flux of 0.975-1.034 per galaxy, with a change of at most
0.02 mag over 0.75-5 um and a scatter of 0.010-0.034. The two estimators share the shape prior, so this tests
the pixel-level fit, not the prior; the largest offset and trend belong to the two galaxies with the most
light outside the fit radius.

### Detector boundaries

For each of the five boundaries the exposures of both detectors within a window (0.12 / 0.15 / 0.20 / 0.12 /
0.10 um) are fitted jointly with ln F = p0 + p1 x + p2 x^2 + s [detector B]; the step s is
-2.5 log10(F_B / F_A), positive when the redder detector is fainter. No exposure sits in an overlap: the
overlaps are 0.01-0.03 um wide and the D3/D4 one is DICHROIC-flagged.

```{figure} figures/sed_demo/fig5_detector_boundaries.png
:width: 820px
:alt: Detector boundary steps

Figure 5. The step at the five boundaries for the six galaxies, for (a) the model flux, (b) the corrected 2 pixel aperture flux and (c) the point-source control.
```

| Boundary | Galaxies, model flux (weighted mean) | Isolated bright stars in the same cutouts | Reading |
|---|---|---|---|
| D1/D2 1.106 um | +0.030 +- 0.006 mag (chi2 13/5) | 0.00 +- 0.013 (two stars); +0.04 to +0.09 for three others, two blended with a galaxy | a model-shape term of a few per cent that differs between D1 and D2 is the simplest explanation; a calibration offset of the same size is not excluded |
| D2/D3 1.638 um | -0.019 +- 0.005 (7/5); per galaxy -0.031 to +0.016 | +0.023 +- 0.015, -0.001 +- 0.013, -0.006 +- 0.013 | consistent with zero within 0.02; the 1.6 um bump is inside the window and the quadratic absorbs it; matters for the [H-minus index](spectral_indices.md) |
| D3/D4 2.422 um | +0.114 +- 0.008 (21/5); per galaxy +0.06 to +0.17, rising with redshift | -0.003 +- 0.032, +0.002 +- 0.026; stars blended with a galaxy +0.07 to +0.14 | the 2.29 um CO bandhead sits at 2.37-2.43 um observed, inside the window, and an edge cannot be absorbed by a quadratic: mostly the feature, no detectable point-source offset at 0.03 mag |
| D4/D5 3.814 um | -0.009 +- 0.015 | within errors | zero |
| D5/D6 4.414 um | -0.049 +- 0.028 | within errors | zero; limited by S/N 2-10 per exposure in D6 |

### Injection and recovery

A galaxy with the target's shape rotated by 45 deg and the target's binned SED is injected 12 pixels from
the target on the least crowded of twelve position angles, into 36 exposures per galaxy, and measured with
the target and the neighbours in the model: recovered / injected = 0.997-1.018 (model; MAD 0.011-0.027),
0.998-1.012 (aperture), 0.31-0.90 (point source). Pooled: 1.002 +- 0.016 at 0.7-2.5 um, 1.000 +- 0.015 at
2.5-3.8 um, 1.025 +- 0.061 at 3.8-5.1 um. The injection uses our own renderer, so it cannot see a renderer
bias; the cross-code check did.

```{figure} figures/sed_demo/fig6_injection_and_errors.png
:width: 820px
:alt: Injection recovery and repeat-pair pulls

Figure 6. (a) Recovered / injected flux of the synthetic galaxies against wavelength, model (filled) and corrected aperture (open). (b) Pull distributions of repeat pairs per detector with their robust widths; dashed: a unit Gaussian.
```

### Cross-code check

tractorjax-spherex (hbahk, GPL-3.0) on the same 36 exposures per galaxy with the same catalogue and a linear
solver gives ours / tractorjax = 1.015, 1.054, 1.015, 1.066, 1.069, 1.017 for g1-g6. tractor and
tractor-jax normalise the Hogg and Lang mixture-of-Gaussians amplitudes to unit sum although the mixture
matches the profile only out to about 8 R_e (de Vaucouleurs, 94.3 % of the analytic total) or 4 R_e
(exponential, 99.1 %), so the expected ratios are 1.060 (n = 4) and 1.009 (n = 1); measured medians 1.062
and 1.0155. The first run gave 1.077 for the compact galaxy, which is how the 2.3 % core-sampling loss was
found. SDSS model magnitudes are truncated at 7 R_e as well.

### Error calibration from repeat pairs

Pairs of exposures of the same detector from different observations within 0.012 um of each other give
pulls (F1 - F2) / sqrt(s1^2 + s2^2) with pooled robust widths of 1.13, 1.39, 1.24, 1.24, 1.14, 1.03 for
D1-D6. Where the S/N per exposure is below about 20 (D5, D6, the neighbour galaxy) the formal errors are
right; at S/N 30-80 the widths are 1.0-2.2, a fractional floor of 0.7-2.4 % per exposure for the three n = 4
galaxies (largest for the two with R_e <= 1.9 arcsec, so most likely astrometric or ePSF-zone jitter of a cusp
against the pixels) and none for the n = 1 galaxies. The SED tables carry both the formal and the
scatter-based error; the project adds a 1.5 % floor in quadrature for n = 4 galaxies.

### DR1 versus QR3

Inverse-variance-weighted mean of QR3 / DR1 at matched wavelengths, per detector, for the five galaxies with
both releases: 0.95-1.09, all within 1-2 % of unity and consistent with their errors (the few 2-3 sigma
values go both ways). The two releases are combined without correction.

### External photometry

Synthetic fluxes from the binned SED (speclite filter curves) divided by the catalogue flux:

| Galaxy | SDSS z model | Legacy forced W1 (Tractor) | 2MASS XSC total J / H / Ks | AllWISE W1 (elliptical) |
|---|---|---|---|---|
| g1 reference | 0.95 | 1.11 | 1.08 / 1.06 / 1.19 | 1.70 |
| g2 compact | 1.07 | 1.10 | 0.97 / 1.01 / 1.18 | - |
| g3 large | 1.00 | 1.10 | 1.11 / 1.14 / 1.05 | 1.66 |
| g4 neighbour | 1.08 | 1.11 | 1.23 / 1.04 / 0.87 | 1.29 |
| g5 no legacy | 1.05 | - | 1.31 / 1.34 / 1.26 | 1.41 |
| g6 post-starburst | 0.95 | 1.07 | 1.41 / 1.41 / 1.52 | - |

SDSS z model fluxes (the same truncated-profile convention as the prior) agree within 8 %; Legacy Survey
forced W1 gives 1.07-1.11, of which the 1.06 truncation factor explains most for n = 4 and a 4-7 % residual
remains unexplained for all; 2MASS XSC "total" and AllWISE magnitudes are 0-70 % low for extended galaxies
and are only usable for colours (SPHEREx minus 2MASS colours agree within 1.4 sigma). W2 is not computed
because the SED ends at 5.0 um inside the W2 curve.

### IRSA tool input

The six galaxies with their shapes are written to `results/irsa_spectrophotometry_tool_input.csv` for a
browser run of the Spectrophotometry Tool in Sersic mode (all R_e below the tool's 20 arcsec limit). Not
yet submitted.

## Questions open after the demonstration

1. D3/D4 step. The galaxy steps track the CO bandhead and the isolated stars show none, but a residual of up
   to about 0.05 mag cannot be excluded with this sample. Options: accept; add a z > 0.09 galaxy or a
   continuum source; fit the step with a CO template instead of a quadratic.
2. Total-flux convention. Our fluxes are analytic Sersic totals; tractor-based catalogues and SDSS model
   magnitudes are truncated totals, 5.7 % (n = 4) or 0.9 % (n = 1) lower. Which convention should the project
   adopt, and should the records carry both?
3. Error floor of compact galaxies. Before stacking, is a per-exposure position-jitter test worth adding, or
   is a floor in quadrature enough?
4. D1/D2 step of +0.03 +- 0.006 mag for galaxies and 0.00 for isolated stars: accept as a model-shape term,
   or investigate (PSF zone, chromatic PSF) before the full sample? The D2/D3 step matters in the same way for
   any index straddling 1.64 um.

## Reproduction

```
uv run python scripts/sed_demo/run_remaining.py g1_reference ... g6_post_starburst   # measure + figures 2-4
bash scripts/sed_demo/run_validation.sh                                             # validation, figures 5-7
uv run python scripts/sed_demo/summarise_demo.py                                    # the report tables
uv run python scripts/sed_demo/measure_galaxy.py <galaxy> --stamps-only             # QA stamps only
```

Data under `/Users/shuang/data/spherex/`: cutout bundles (457 MB), calibration cache (780 MB), results
(18 MB: per-exposure records, screened records, binned SEDs, validation tables, QA stamps).

[^study]: An unpublished photometry study by the group (2026-11-12/13): noise-free simulations of
    point-source and Sersic fits over all ePSF zones, and the size distribution of the SDSS parent sample.
