# SED demo report

Branch `feature/sed-demo`; task spec `docs/sed_demo_task.md`; facts from the earlier study in
`docs/reference_notes/photometry_study_2026-11.md`. Figures in `docs/figures/sed_demo/`.

## Checkpoint A (2026-11-13): galaxy 1 end to end

Setup
- Data: DR1 + QR3 wide-survey exposures (IRSA TAP via spherex-retrieval); 341 exposures cover the
  reference galaxy (DR1 296: D1-D6 49/42/56/50/43/56; QR3 45: 9/9/5/9/9/4); 6 per detector selected,
  spread in time (30 DR1 + 6 QR3).
- Cutouts: 0.07 deg (41 x 41 px) bundles from spherex-retrieval with the R7 ePSF zones, CWAVE/CBAND and
  SAPM attached; 36 bundles = 7.4 MB on disk (0.20 MB each), 157 s at two concurrent requests
  (4.4 s per cutout); calibration cache 445 MB (ePSF, Spectral WCS, SAPM for six detectors, once).
- Catalogue: Legacy Survey DR10 Tractor sources within 1.1' down to z = 21 (119 neighbours; target shape
  from SDSS: exponential, R_e 4.38", b/a 0.77, PA 101.7). No shreds flagged. Neighbours are fitted
  jointly with the target.
- Model: PSF-convolved Sersic templates on the ePSF 5x grid (zone chosen in parent-frame pixels), point-
  sampled at native pixels; ZODI subtracted; constant background; flags = IRSA tool set + TRANSIENT,
  OVERFLOW, DICHROIC; NaN pixels removed; weighted linear solve for all amplitudes.
- Estimators: forced-model flux; model-corrected aperture flux at 1.5, 2, 2.5, 3 px; point-source fit as
  the negative control. Wavelength = CWAVE at the target pixel; MJy/sr to uJy with the SAPM.

Results (figures `g1_reference_fig2_image_qa.png`, `g1_reference_fig3_diagnostics.png`,
`g1_reference_fig4_sed.png`)
- 35 of 36 exposures measured; the 2.416 um D3 exposure is rejected (all pixels near the target flagged
  DICHROIC, reason `model_weight_masked`); the 1.097 um D2 exposure next to He I 1.083 um is screened as
  a chi2 outlier (chi2/dof 8.9 against a detector median of 1.3).
- chi2/dof near the target: median 1.1 (D1), 1.4 (D2), 1.5 (D3), 1.6 (D4), 1.0 (D5), 1.0 (D6) for the
  galaxy model; 3-15 for the point-source control in D1-D4.
- Point-source flux / model flux: 0.60-0.74 (D1-D4), 0.66-0.78 (D5-D6), as the simulations predicted.
- Model / 2 px aperture: 0.99-1.02 in D1-D4, 0.95-1.06 in D5-D6.
- Projected full demo (six galaxies, every wide-survey exposure, ~300-450 per galaxy): ~2,200 cutouts,
  ~0.45 GB on disk, ~2.7 h of IRSA requests at two workers.

Found while testing
- A background basis quadratic in CWAVE repairs the He I exposures (chi2/dof 8.9 -> 1.8) and moves their
  fluxes by 5-9 %; a plane in x, y does not. Default background model to be chosen on the full sample.
- One D4 exposure (3.32 um) has chi2/dof ~50 over the whole cutout but 3 near the target; to be inspected.

## Checkpoint B (2026-11-14): every exposure of six galaxies, validation 1-8, figures 1-7

### Summary

- 2,225 DR1 + QR3 wide-survey exposures of six galaxies were measured; 2,104 (95 %) enter the SEDs. All
  102 channels of every galaxy are filled. Per-exposure chi2/dof near the target is 0.9-2.3 (median per
  detector), against 3-20 for the point-source control in D1-D4.
- The forced-model flux and the model-corrected 2 px aperture flux agree to 0.98-1.03 with no trend over
  0.75-5 um (|change| <= 0.02 mag). Injected galaxies are recovered at 1.000-1.018 (model) and
  0.998-1.012 (aperture). Our flux / tractorjax-spherex = 1.015 (n = 1) and 1.062 (n = 4), the ratio
  expected from the two "total flux" conventions (next section). QR3 and DR1 agree at the 1-2 % level
  with no systematic offset.
- Detector boundaries: D2/D3, D4/D5 and D5/D6 steps are consistent with zero (-0.02 +- 0.005,
  -0.01 +- 0.015, -0.05 +- 0.03 mag). D1/D2 shows +0.03 +- 0.006 mag. D3/D4 shows +0.06 to +0.17 mag,
  correlated with redshift: the 2.29 um CO bandhead falls inside the window, so this is not a pure
  calibration test; stars in the same cutouts give 0.00 +- 0.03 mag (two isolated bright stars) to
  +0.13 mag (stars blended with the galaxy).
- Repeat exposures at the same wavelength scatter 1.0-1.4 times the formal error in every detector
  (pooled robust widths 1.13, 1.39, 1.24, 1.24, 1.14, 1.03 for D1-D6), with a fractional floor of
  0.7-2.4 % per exposure for the three n = 4 galaxies and none detectable for the three n = 1 galaxies.
- The rest-frame SEDs (figure 7) share the 1.6 um bump, the 1.9 um water band and the CO drop; the three
  star-forming or post-starburst galaxies show the 3.3 um PAH feature and a flatter 3.5-5 um continuum.
- Three findings need the user's judgement (section "Questions for the user" below): the D3/D4 step, the
  total-flux convention, and the error floor of compact galaxies.

### Data and run

| item | value |
|---|---|
| exposures found (DR1 / QR3) | 341 (296/45), 279 (279/0), 418 (283/135), 420 (280/140), 393 (244/149), 374 (259/115) |
| cutout bundles on disk | 2,242 files, 457 MB (0.20 MB each; 41 x 41 px, 53 x 53 px for the large galaxy) |
| cutout retrieval | 2,189 bundles in 5,538 s of IRSA requests at two workers (2.5 s per cutout; one 3 h hang excluded) |
| measurement (run 2, fixed renderer) | 552-1,702 s per galaxy (1.3-4.1 s per exposure for reading, rendering every source and solving; the neighbour galaxy with 141 sources is the slowest) |
| validation | 144-301 s per galaxy (tractorjax on 36 exposures, injection on 36, external queries) |
| whole pipeline, unattended | 1 h 52 min for six galaxies (22:49 to 00:42) |
| calibration cache | 780 MB (spherex-retrieval ePSF/SWCS/SAPM cache 776 MB, spectral channels 4 MB) |

Changes to the method since checkpoint A, all applied to every galaxy:
- Background: constant + quadratic in CWAVE (`cwave2`), chosen at checkpoint A because it repairs the He I
  1.083 um exposures. The HE_AIRGLOW_CONT basis was dropped (no effect).
- Renderer: the Sersic core is sampled 32 x 32 per oversampled pixel in a 7 x 7 block around the centre
  (the earlier 4 x 4 sampling lost up to 2.3 % of an n = 4 profile with R_e = 1" and made the loss
  depend on the cutout orientation). Every tested shape is within 0.2 % of a 64 x 64 brute-force total.
- Screening after measurement: `chi2_outlier` (near-target chi2/dof > 5 x the detector median),
  `cutout_chi2_outlier` (whole-cutout chi2), `wavelength_outlier` (CWAVE outside the detector's range).
- QA stamps come from the exposure with chi2/dof closest to the detector median after screening.

### Sample and per-exposure measurement (figures 2-4)

| galaxy | z | profile | exposures | used | rejected | screened | chi2/dof D1-D6 | point / model D1-D6 | E(B-V) |
|---|---|---|---|---|---|---|---|---|---|
| g1 reference | 0.046 | n=1, Re=4.4" | 341 | 316 | 13 | 12 | 1.1/1.4/1.5/1.6/1.1/1.0 | 0.65/0.68/0.68/0.74/0.72/0.71 | 0.016 |
| g2 compact | 0.058 | n=4, Re=1.1" | 279 | 265 | 9 | 5 | 1.1/1.2/1.2/1.3/1.1/1.0 | 0.88/0.88/0.89/0.90/0.89/0.89 | 0.054 |
| g3 large | 0.033 | n=1, Re=12.4" | 418 | 395 | 12 | 11 | 1.3/1.7/2.0/1.7/1.1/1.0 | 0.26/0.29/0.28/0.33/0.30/0.30 | 0.017 |
| g4 neighbour | 0.033 | n=4, Re=1.9" | 420 | 407 | 10 | 3 | 1.4/2.3/2.1/1.7/1.0/0.9 | 0.63/0.62/0.62/0.63/0.62/0.59 | 0.037 |
| g5 no legacy | 0.052 | n=4, Re=4.8" | 393 | 371 | 15 | 7 | 1.3/1.9/2.0/1.4/0.9/0.9 | 0.57/0.58/0.59/0.59/0.59/0.58 | 0.159 |
| g6 post starburst | 0.052 | n=1, Re=5.4" | 374 | 350 | 13 | 11 | 1.2/1.3/1.5/1.1/1.0/1.0 | 0.56/0.59/0.62/0.64/0.64/0.63 | 0.060 |

Rejections (before the fit) are `model_weight_masked` (every pixel of the target flagged, mostly the
DICHROIC exposures at 2.416-2.426 um), `cutout_truncated` (target within the fit radius of the cutout
edge) and `target_outside_cutout`. The point-source control recovers 26-90 % of the model flux, as the
simulations predicted (lower for larger galaxies), and its chi2/dof is 3-20 in D1-D4 where the galaxies
are resolved; the test can therefore see an under-fitted profile.

### Validation 2: estimator consistency

| galaxy | n | median model / aperture (2 px) | change 0.75-5 um [mag] | scatter (MAD) |
|---|---|---|---|---|
| g1 reference | 316 | 1.009 | 0.000 | 0.012 |
| g2 compact | 265 | 0.987 | 0.004 | 0.018 |
| g3 large | 395 | 0.975 | 0.017 | 0.016 |
| g4 neighbour | 407 | 1.034 | 0.000 | 0.034 |
| g5 no legacy | 371 | 0.993 | -0.004 | 0.010 |
| g6 post starburst | 350 | 0.999 | 0.021 | 0.019 |

The two estimators share the shape prior (the aperture correction comes from the same template), so the
test checks the pixel-level fit, not the prior. The largest offset (g3, 0.975) and trend (g3, g6, 0.02 mag)
belong to the two galaxies with the largest fraction of light outside the fit radius.

### Validation 1 and 3: detector boundaries (figure 5)

Joint fit of ln F = p0 + p1 x + p2 x^2 + s [detector B] to the exposures of both detectors within a window
around the boundary (0.12 / 0.15 / 0.20 / 0.12 / 0.10 um); the step s is -2.5 log10(F_B / F_A), positive
when the redder detector is fainter. The overlaps themselves are 0.01-0.03 um wide and the D3/D4 overlap
is DICHROIC-flagged, so no exposure sits in an overlap.

Model flux:

| galaxy | z | D1/D2 1.106 | D2/D3 1.638 | D3/D4 2.422 | D4/D5 3.814 | D5/D6 4.414 |
|---|---|---|---|---|---|---|
| g1 reference | 0.046 | +0.053 +- 0.013 | -0.031 +- 0.010 | +0.169 +- 0.019 | +0.020 +- 0.029 | -0.043 +- 0.054 |
| g2 compact | 0.058 | +0.025 +- 0.012 | -0.001 +- 0.011 | +0.128 +- 0.019 | +0.014 +- 0.028 | -0.001 +- 0.071 |
| g3 large | 0.033 | +0.048 +- 0.012 | -0.024 +- 0.011 | +0.060 +- 0.016 | -0.011 +- 0.036 | -0.131 +- 0.054 |
| g4 neighbour | 0.033 | -0.023 +- 0.028 | +0.016 +- 0.027 | +0.064 +- 0.052 | -0.151 +- 0.092 | -0.341 +- 0.223 |
| g5 no legacy | 0.052 | +0.005 +- 0.013 | -0.026 +- 0.009 | +0.125 +- 0.016 | -0.050 +- 0.032 | +0.033 +- 0.058 |
| g6 post starburst | 0.052 | +0.027 +- 0.023 | -0.007 +- 0.016 | +0.117 +- 0.034 | -0.036 +- 0.054 | -0.068 +- 0.100 |
| weighted mean | | +0.030 +- 0.006 (chi2 13/5) | -0.019 +- 0.005 (7/5) | +0.114 +- 0.008 (21/5) | -0.009 +- 0.015 (6/5) | -0.049 +- 0.028 (7/5) |

Point-source control (same exposures, point template):

| galaxy | D1/D2 | D2/D3 | D3/D4 | D4/D5 | D5/D6 |
|---|---|---|---|---|---|
| g1 reference | +0.154 +- 0.014 | -0.005 +- 0.011 | +0.275 +- 0.020 | +0.087 +- 0.030 | -0.077 +- 0.056 |
| g2 compact | +0.051 +- 0.012 | +0.004 +- 0.011 | +0.106 +- 0.020 | +0.022 +- 0.028 | -0.029 +- 0.071 |
| g3 large | -0.001 +- 0.018 | +0.111 +- 0.015 | +0.101 +- 0.022 | +0.001 +- 0.046 | -0.162 +- 0.070 |
| g4 neighbour | +0.089 +- 0.027 | +0.010 +- 0.027 | +0.060 +- 0.052 | -0.181 +- 0.093 | -0.334 +- 0.218 |
| g5 no legacy | +0.083 +- 0.014 | -0.007 +- 0.009 | +0.194 +- 0.016 | -0.028 +- 0.033 | +0.043 +- 0.060 |
| g6 post starburst | -0.057 +- 0.026 | -0.038 +- 0.017 | +0.166 +- 0.039 | -0.075 +- 0.057 | -0.075 +- 0.104 |
| weighted mean | +0.068 +- 0.007 (chi2 78/5) | +0.007 +- 0.005 (56/5) | +0.169 +- 0.009 (54/5) | +0.014 +- 0.015 (15/5) | -0.058 +- 0.030 (7/5) |

Stars fitted jointly in the same cutouts (point templates; z <= 16.5, within 60", >= 100 exposures), the
calibration-only version of the test:

| galaxy | star | sep ["] | z | D1/D2 | D2/D3 | D3/D4 | D4/D5 | D5/D6 |
|---|---|---|---|---|---|---|---|---|
| g4 neighbour | n029 | 57.6 | 15.06 | -0.006 +- 0.013 | +0.023 +- 0.015 | -0.003 +- 0.032 | +0.004 +- 0.060 | -0.039 +- 0.119 |
| g5 no legacy | n013 | 33.4 | 14.64 | -0.004 +- 0.013 | -0.001 +- 0.013 | +0.002 +- 0.026 | +0.104 +- 0.066 | -0.056 +- 0.115 |
| g6 post starburst | n007 | 33.8 | 15.13 | +0.041 +- 0.015 | -0.006 +- 0.013 | +0.073 +- 0.032 | -0.093 +- 0.057 | -0.134 +- 0.122 |
| g5 no legacy | n007 | 27.5 | 15.82 | -0.001 +- 0.024 | -0.013 +- 0.016 | +0.078 +- 0.035 | +0.017 +- 0.082 | -0.103 +- 0.146 |
| g4 neighbour | n002 (12.6" from the galaxy) | 13.2 | 15.45 | +0.053 +- 0.013 | -0.024 +- 0.013 | +0.134 +- 0.025 | -0.019 +- 0.037 | -0.080 +- 0.072 |
| g5 no legacy | n000 (9.1" from the galaxy) | 9.1 | 15.75 | +0.089 +- 0.025 | +0.026 +- 0.019 | +0.144 +- 0.043 | -0.056 +- 0.104 | +0.108 +- 0.199 |

(the full list of eleven stars is printed by `scripts/sed_demo/summarise_demo.py`).

Reading of the boundary test:
- D2/D3 (1.6 um bump inside the window), D4/D5 and D5/D6: the galaxy steps are consistent with zero
  within 0.02-0.05 mag; the quadratic absorbs the bump. D5/D6 is limited by the S/N of 2-10 per
  exposure in D6.
- D1/D2: +0.030 +- 0.006 mag for the galaxies, with scatter between galaxies (chi2 13/5), and 0.00 for
  the two best-measured isolated stars, +0.04 to +0.09 for three other stars (two of them blended with
  the galaxy). The point-source
  control gives a larger step (+0.068), as expected when a point template is fitted to a resolved galaxy
  with a detector-dependent PSF. A model-shape term (PSF or profile mismatch that differs between D1 and
  D2) of a few per cent is the simplest explanation; a calibration offset of the same size is not excluded.
- D3/D4: +0.06 to +0.17 mag for the galaxies, increasing with redshift (0.033: +0.06; 0.046: +0.17;
  0.052: +0.12; 0.058: +0.13). The CO bandhead at 2.29 um rest lies at 2.37-2.43 um observed, that is,
  on the D3 side of the window for z <= 0.052 and at the boundary for z = 0.058, and an edge cannot be
  absorbed by a quadratic. The isolated stars n029 and n013 give 0.00 +- 0.03 at D3/D4, the stars
  blended with a galaxy +0.07 to +0.14 (their fluxes are correlated with the galaxy's). So the data show
  no detector offset for point sources at the 0.03 mag level, and the galaxy step is, at least mostly,
  the CO bandhead. The residual that a calibration term could still hide is not separable with this
  sample because every galaxy has the feature in the window; a galaxy at z > 0.09 (CO beyond 2.5 um) or a
  pure-continuum source would settle it.

### Validation 4: injection and recovery (figure 6a)

A galaxy with the target's shape rotated by 45 deg and the target's binned SED is injected 12 px from the
target on the least crowded of twelve position angles, into 36 exposures per galaxy (6 per detector), and
measured with the target and the neighbours in the model.

| galaxy | n | model (median) | model MAD | aperture 2 px | point |
|---|---|---|---|---|---|
| g1 reference | 35 | 1.002 | 0.020 | 1.002 | 0.692 |
| g2 compact | 36 | 0.997 | 0.018 | 1.001 | 0.896 |
| g3 large | 35 | 1.018 | 0.019 | 1.012 | 0.310 |
| g4 neighbour | 35 | 1.000 | 0.025 | 0.998 | 0.788 |
| g5 no legacy | 34 | 1.005 | 0.011 | 1.006 | 0.623 |
| g6 post starburst | 32 | 0.998 | 0.027 | 1.000 | 0.605 |

Pooled: 1.002 +- 0.016 (MAD) at 0.7-2.5 um, 1.000 +- 0.015 at 2.5-3.8 um, 1.025 +- 0.061 at 3.8-5.1 um
(the D5/D6 scatter is the S/N). The injection uses our own renderer, so it cannot see a renderer bias
(the cross-code check did).

### Validation 5: external photometry (figure 4 diamonds)

Synthetic fluxes from the binned model SED (speclite filter curves) divided by the catalogue flux:

| galaxy | SDSS z model | SDSS z cmodel | 2MASS XSC total J / H / Ks | Legacy forced W1 (Tractor) | AllWISE W1 gmag |
|---|---|---|---|---|---|
| g1 reference | 0.95 | 0.84 | 1.08 / 1.06 / 1.19 | 1.11 | 1.70 |
| g2 compact | 1.07 | 1.08 | 0.97 / 1.01 / 1.18 | 1.10 | - |
| g3 large | 1.00 | 1.02 | 1.11 / 1.14 / 1.05 | 1.10 | 1.66 |
| g4 neighbour | 1.08 | 1.06 | 1.23 / 1.04 / 0.87 | 1.11 | 1.29 |
| g5 no legacy | 1.05 | 1.10 | 1.31 / 1.34 / 1.26 | - (outside DR10) | 1.41 |
| g6 post starburst | 0.95 | 0.90 | 1.41 / 1.41 / 1.52 | 1.07 | - |

- SDSS z model fluxes agree within 8 %; the model magnitude is the same profile convention as our prior
  (truncated deV at 7 R_e for n = 4), so the n = 4 galaxies come out 5-8 % brighter in SPHEREx, the n = 1
  galaxies 0-5 % fainter. cmodel differs where the single-profile fit is poor (g1 0.84).
- Legacy Survey forced W1 (Tractor model, the same approach) gives 1.07-1.11. For n = 4 (g2, g4:
  1.10-1.11) the 1.06 factor between an analytic Sersic total and the tractor mixture total accounts for
  most of it; the remaining 4-7 % (all galaxies) is not explained by this demo (candidates: the unWISE
  zero point and bandpass convention, the unWISE PSF model; not tested).
- 2MASS XSC "total" magnitudes are low by 0-50 % for the fainter galaxies, AllWISE elliptical and
  profile-fit magnitudes by 30-70 %: both are aperture-limited for extended sources and are lower limits
  here, not calibration checks. W2 synthetic fluxes are not computed because the SED ends at 5.0 um
  inside the W2 curve; the W2 catalogue points are plotted in figure 4 only.
- Colours: SPHEREx synthetic minus 2MASS XSC total colours are -0.02 to +0.04 mag (J-H) and -0.19 to
  +0.17 mag (H-Ks) with 2MASS errors of 0.09-0.28 mag, every difference within 1.4 sigma of zero; for g5
  and g6 the three 2MASS bands are low by the same factor (1.3, 1.4), so the colours agree while the
  normalisation does not.

### Validation 6: cross-code check with tractorjax-spherex

tractorjax-spherex (hbahk, GPL-3.0) run on the same 36 exposures per galaxy with the same catalogue,
linear solver, and its MASKBITS extended by DICHROIC, TRANSIENT and OVERFLOW:

| galaxy | n | ours / tractorjax (median) | 16-84 % | per detector D1-D6 |
|---|---|---|---|---|
| g1 reference (n=1) | 34 | 1.015 | 1.008-1.025 | 1.010 1.012 1.014 1.020 1.016 1.023 |
| g2 compact (n=4) | 34 | 1.054 | 1.046-1.060 | 1.055 1.051 1.052 1.050 1.057 1.050 |
| g3 large (n=1) | 36 | 1.015 | 1.006-1.031 | 1.022 1.014 1.014 1.024 1.008 1.005 |
| g4 neighbour (n=4) | 35 | 1.066 | 1.047-1.077 | 1.067 1.061 1.063 1.071 1.055 1.037 |
| g5 no legacy (n=4) | 36 | 1.069 | 1.062-1.076 | 1.075 1.063 1.066 1.070 1.069 1.063 |
| g6 post starburst (n=1) | 35 | 1.017 | 1.005-1.029 | 1.016 1.012 1.014 1.027 1.029 0.985 |

tractor-jax (like tractor and therefore the Legacy Survey catalogues) normalises the Hogg & Lang
mixture-of-Gaussians amplitudes to unit sum, although the mixture matches the profile only out to ~8 R_e
(deV, 94.3 % of the analytic total) or ~4 R_e (exp, 99.1 %). The expected ratios analytic / tractor are
1.060 (n = 4) and 1.009 (n = 1); measured: 1.062 and 1.015. The first run (before the renderer fix) gave
1.077 for the compact galaxy, which is how the 2.3 % sampling loss was found. The remaining 0.5 % (n = 1)
is within the two codes' different background models (ours: joint quadratic in CWAVE; tractorjax:
photutils background per tile) and tile-based solving.

### Validation 7: error calibration from repeat pairs (figure 6b)

Pairs of exposures of the same detector from different observations with |delta lambda| < 0.012 um;
pull = (F1 - F2) / sqrt(s1^2 + s2^2); robust width (1.4826 MAD) per galaxy and detector, with the number of
pairs and the median S/N:

| galaxy | D1 | D2 | D3 | D4 | D5 | D6 |
|---|---|---|---|---|---|---|
| g1 reference | 1.15 (77, 38) | 1.16 (36, 50) | 1.20 (41, 64) | 1.24 (15, 49) | 1.00 (20, 21) | 1.06 (45, 13) |
| g2 compact | 1.82 (47, 37) | 1.27 (37, 52) | 2.15 (33, 63) | 1.07 (9, 52) | 0.94 (34, 19) | 1.09 (28, 10) |
| g3 large | 1.01 (143, 51) | 1.08 (46, 62) | 0.81 (49, 68) | 1.23 (35, 53) | 0.93 (35, 20) | 0.92 (74, 10) |
| g4 neighbour | 1.25 (69, 19) | 1.52 (168, 25) | 1.60 (36, 26) | 0.44 (6, 17) | 1.13 (147, 5) | 0.95 (47, 2) |
| g5 no legacy | 1.18 (134, 44) | 1.59 (73, 70) | 1.20 (20, 76) | 1.42 (31, 55) | 1.20 (56, 19) | 0.96 (31, 11) |
| g6 post starburst | 0.88 (68, 26) | 1.15 (63, 35) | 1.05 (18, 39) | 0.85 (9, 30) | 1.28 (48, 10) | 0.89 (35, 7) |
| pooled | 1.13 (538) | 1.39 (423) | 1.24 (197) | 1.24 (105) | 1.14 (340) | 1.03 (260) |

- Where the S/N per exposure is below ~20 (D5, D6, and the neighbour galaxy everywhere) the formal
  errors are right (widths 0.9-1.3).
- At S/N 30-80 (D1-D4) the widths are 1.0-2.2, which means a fractional floor per exposure of 0.7-2.4 %
  for g2, g4 and g5 (largest: g2 D1 2.4 %, g4 D3 2.4 %); none is detectable for g1, g3, g6. The floor is
  largest for the two galaxies with R_e <= 1.9", so it is most likely the astrometric or ePSF-zone jitter of
  a cusp against the 6.2" pixels, not the flux calibration. The renderer fix did not change these widths.
- Recommended use: add a 1.5 % fractional floor in quadrature for n = 4 galaxies, or scale by the
  per-detector pooled widths; the SED tables already carry both the formal and the exposure-scatter error.

### DR1 versus QR3

Inverse-variance-weighted mean of QR3 / DR1 at matched wavelengths (|delta lambda| < 0.012 um), per detector:

| galaxy | D1 | D2 | D3 | D4 | D5 | D6 |
|---|---|---|---|---|---|---|
| g1 reference | 1.016 +- 0.013 (9) | 0.983 +- 0.009 (9) | 1.014 +- 0.011 (4) | 0.983 +- 0.013 (5) | 1.026 +- 0.024 (9) | 0.999 +- 0.056 (4) |
| g3 large | 0.999 +- 0.007 (17) | 0.992 +- 0.005 (18) | 0.999 +- 0.005 (19) | 1.024 +- 0.014 (4) | 0.996 +- 0.017 (18) | 0.995 +- 0.026 (25) |
| g4 neighbour | 1.036 +- 0.018 (18) | 1.012 +- 0.010 (32) | 0.982 +- 0.014 (15) | 1.011 +- 0.092 (1) | 1.092 +- 0.052 (32) | 1.036 +- 0.191 (17) |
| g5 no legacy | 0.999 +- 0.006 (31) | 1.008 +- 0.005 (20) | 0.995 +- 0.005 (17) | - | 0.969 +- 0.019 (14) | 1.023 +- 0.030 (17) |
| g6 post starburst | 0.979 +- 0.013 (17) | 0.991 +- 0.012 (13) | 0.996 +- 0.010 (14) | 0.953 +- 0.045 (1) | 0.992 +- 0.041 (11) | 1.011 +- 0.057 (17) |

The compact galaxy has no QR3 exposures. All ratios are within 1-2 % of unity and consistent with their
errors (the few 2-3 sigma values go both ways), so the two releases are combined without correction.

### Validation 8: IRSA Spectrophotometry Tool input

`/Users/shuang/data/spherex/results/irsa_spectrophotometry_tool_input.csv` holds the six galaxies with
name, RA, Dec, Sersic index, axis ratio, position angle (east of north) and R_e; all R_e are below the
tool's 20" limit (the large galaxy has 12.4"). Not submitted (browser only).

### Figures

All figures are in `docs/figures/sed_demo/`, PNG, 300 dpi, Computer Modern, one colour per detector
(D1 dark blue, D2 light blue, D3 green, D4 yellow, D5 orange, D6 pink) in every figure.

- Figure 1 (`fig1_sample.png`). The parent sample (SDSS DR17 SkyServer, class GALAXY, zWarning = 0,
  0.03 <= z <= 0.059, MPA-JHU log M* >= 10; 45,569 galaxies) in (a) the redshift-stellar-mass plane and (b) the Dn4000-HdA plane as grey density, and
  (c) the distribution of the SDSS r-band effective radius with the 6.2" SPHEREx pixel marked; the six demo
  galaxies are the coloured symbols used throughout.
- Figure 2 (`<galaxy>_fig2_image_qa.png`, six files). (a) Legacy Survey DR10 z image (SDSS DR17 for the
  galaxy outside the DR10 footprint), 150" wide, with the target's model ellipse (orange), the fitted
  neighbours (green circles), removed shreds (pink crosses), the 2 px aperture (blue
  dashed) and the fit radius (grey dotted); the circle radius scales with the neighbour's z magnitude
  relative to the target. (b)-(d) For one typical exposure per detector (chi2/dof at the
  detector median): data, model and residual / sigma (+-4) in a 19 x 19 px window, with masked pixels (pink
  squares) and the same two circles.
- Figure 3 (`<galaxy>_fig3_diagnostics.png`). Per exposure against observed wavelength: (a) chi2/dof
  within the fit radius for the galaxy model (filled) and the point-source control (open); (b) the fraction
  of the target template's weight on masked pixels; (c) the fitted residual background (filled) and the ZODI
  model at the target (open). Exposures rejected or screened are black symbols keyed by reason; the He I
  1.083 um airglow line is marked.
- Figure 4 (`<galaxy>_fig4_sed.png`). (a) Model flux of every used exposure, coloured by detector, with
  formal errors; the binned model SED (black, error = scatter in the channel) and the binned corrected
  2 px aperture SED (grey dashed); external photometry of the same convention (SDSS z model, 2MASS XSC
  total, Legacy Survey forced W1/W2 or AllWISE elliptical) as open diamonds. Rest-frame axis on top; the
  CaT, 1.6 um CO, 1.9 um water, 2.29 um CO, 3.3 um PAH and 4.6 um CO positions marked. (b) The ratio of
  the two estimators per exposure and binned.
- Figure 5 (`fig5_detector_boundaries.png`). The detector-boundary step -2.5 log10(F_B / F_A) at the five
  boundaries for the six galaxies, for (a) the model flux, (b) the corrected 2 px aperture flux and (c) the
  point-source control; error bars from the joint quadratic-plus-step fit.
- Figure 6 (`fig6_injection_and_errors.png`). (a) Recovered / injected flux of the synthetic galaxies
  against wavelength, model (filled) and corrected aperture (open). (b) Pull distributions of repeat pairs
  per detector with the robust widths; dashed: a unit Gaussian with the mean number of pairs per detector.
- Figure 7 (`fig7_all_seds_rest_frame.png`). The six binned model SEDs (Galactic extinction corrected) in
  the rest frame, normalised at 1.6 um.

### Questions for the user

1. D3/D4 step. The galaxies show +0.06 to +0.17 mag (redder detector fainter) that tracks the redshift and
   hence the position of the CO bandhead, while the two isolated bright stars show 0.00 +- 0.03 mag. I read
   this as the CO feature with no detectable calibration offset, but a residual of up to ~0.05 mag cannot be
   excluded with this sample. Options: accept; add a z > 0.09 galaxy or a continuum source to the demo;
   or fit the step with a CO template instead of a quadratic.
2. Total-flux convention. Our fluxes are analytic Sersic totals; tractor-based catalogues (Legacy Survey,
   tractorjax) and SDSS model magnitudes are truncated totals, 5.7 % (n = 4) or 0.9 % (n = 1) lower. Which
   convention should the project adopt, and should the records carry both?
3. Error floor of compact galaxies. The repeat-pair widths are 1.5-2.2 in D1-D3 for the two galaxies with
   R_e <= 1.9", with a 1-2.4 % fractional floor per exposure. Before stacking, is a per-exposure
   position-jitter test (fit x, y offsets, or marginalise over them) worth adding, or is a floor in
   quadrature enough?
4. D1/D2 step of +0.03 +- 0.006 mag for galaxies (0.00 for isolated stars): accept as a model-shape term
   or investigate (PSF zone, chromatic PSF) before the full sample?

### Disk use and temporary material

| location | size |
|---|---|
| `/Users/shuang/data/spherex` total | 1.3 GB |
| `calibration/` (spherex-retrieval cache 776 MB, spectral channels 4 MB) | 780 MB |
| `cutouts/` (2,242 bundles) | 457 MB |
| `results/` (records, SEDs, validation, stamps) | 18 MB |
| `sample/` (SkyServer parent catalogue, candidate pools, coverage) | 23 MB |
| `scratch/` (run logs, optical image cache) | 2.3 MB |
| project `.venv` (hbahk stack with JAX) | 974 MB |
| `~/.cache/uv` (all projects) | 11 GB |

Moved to the Trash at the end of the session: `~/.Trash/spherex_results_run1_2026-11-14` (the first-run
results, 6.9 MB), `~/.Trash/spherex_scratch_run1_2026-11-14` (first-run logs and early test files,
0.5 MB) and `~/.Trash/spherex_psb_prompt_duplicate_2026-11-14` (a duplicate of the task spec that had
reappeared at the repository root). Kept: the calibration cache, the cutouts (needed to re-run), the
current run logs and the optical image cache (1.8 MB).

### Reproduction

```
uv run python scripts/sed_demo/run_remaining.py g1_reference ... g6_post_starburst   # measure + figures 2-4
bash scripts/sed_demo/run_validation.sh                                             # validation, figures 5-7
uv run python scripts/sed_demo/summarise_demo.py                                    # the tables above
uv run python scripts/sed_demo/measure_galaxy.py <galaxy> --stamps-only             # QA stamps only
```
