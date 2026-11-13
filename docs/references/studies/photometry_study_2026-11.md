# Facts carried over from the photometry study of 2026-11-12/13

The study lives in the git-ignored `temp/` folder of the student's repository
`/Users/shuang/Dropbox/work/project/otters/spherex_photometry_code` (read only; never imported). This note
records, with source paths, the facts the SED demo relies on. Section numbers refer to the source files.

Sources (all under `spherex_photometry_code/temp/`):
- `docs/sed_photometry_followup.md` (2026-11-13): tests 12 and 13, DR1 news, recommendation (section 5).
- `docs/galaxy_photometry_options.md` (2026-11-12, corrected 2026-11-13): three probes (own code, hbahk
  stack, official stack), like-for-like comparison, assessment.
- `docs/extended_galaxies.md` (2026-11-12): sample sizes, PSF sizes, point-source losses, clipping failure.
- `docs/lessons.md`, `docs/todo.md`, `docs/test_log.md`.
- Reference scripts (ideas only): `scripts/probe_scratch_galaxy_photometry.py` (164-line forced galaxy
  photometry), `scripts/test_neighbours_joint_versus_mask.py` (SDSS neighbours, Sersic renderer, joint
  linear solve, masks, model-corrected aperture), `scripts/test_sed_shape_robustness.py` (synthetic test over
  all ePSF zones), `scripts/study_common.py` (cached downloads with the 300 MB rule, S3 listing).

## 1. The sample (extended_galaxies.md section 1)

SDSS DR17 SkyServer, class GALAXY, zWarning = 0, 0.03 <= z <= 0.059, MPA-JHU lgm_tot_p50 >= 10: 45,569
spectra, 45,300 unique photometric objects, 65 % with fracDeV_r > 0.5. r-band model R_e (deV if fracDeV > 0.5
else exp): 1.6 / 2.9 / 4.4 / 6.3 / 10.6 arcsec at the 5 / 25 / 50 / 75 / 95 percentiles; Petrosian R50
1.5-7.1, R90 4.1-18.6 arcsec. A point source with the same total z-band flux would have per-exposure S/N
80 / 241 / 955 (p5 / p50 / p95) near 0.9 um (from petroMag_z and the 19.5 AB depth of the data guide).

The demo's parent catalogue (`/Users/shuang/data/mpa/outputs/catalogs/galaxy_summary_48111.csv`) is the
MPA-JHU DR8 selection of the `mpa` repository: quality cuts (RELIABLE = 1, GALAXY, Z_WARNING = 0, Z_ERR > 0),
0.03 < z < 0.06, LGM_TOT_P50 > 10, one spectrum per PHOTOID (highest SN_MEDIAN), 191 index-tail rows removed
(48,460 -> 48,111). Source: `/Users/shuang/data/mpa/docs/sample_design.md` and `docs/summary_catalog.md`.

## 2. PSF sizes (extended_galaxies.md section 2; QR2 average PSF, central zone)

FWHM 4.9-5.0 arcsec (D1-D3), 5.6-6.1 arcsec (D4-D6); EE50 radius 2.7-3.7 arcsec; N_eff 3.1-3.2 (D1-D3),
4.0-4.4 (D4-D6) native pixels. The typical galaxy (R_e 4.4", R90 8.6") is semi-resolved.

## 3. Point-source fit: ruled out (extended_galaxies.md section 3; followup section 3)

- Recovered fraction of an exponential disc, no clipping, D1 / D6: 0.82 / 0.86 at R_e 2", 0.57 / 0.64 at
  R_e 4", 0.30 / 0.36 at R_e 8"; de Vaucouleurs profiles 0.71 / 0.74, 0.54 / 0.58, 0.36 / 0.40.
- Mapped onto the sample: 43 % lose more than half of their light in D1; spurious D1 - D6 colour
  +0.046 / +0.097 / +0.204 mag (p5 / p50 / p95).
- Test 12 (synthetic, all 2,656 QR3 ePSF zones, four sub-pixel phases, noise free): SED range over 0.75-5 um
  0.072 / 0.186 / 0.299 mag for R_e 2 / 4.4 / 8", jump at 2.42 um -0.033 / -0.092 / -0.146 mag, per-exposure
  phase scatter 5-13 %.
- talltable's kappa-sigma clipping (kappa 4, 10 iterations) makes most point-source measurements of these
  galaxies wrong by more than 50 % at S/N >= 300 (extended_galaxies.md section 4).

## 4. Forced Sersic photometry with fixed optical shape (followup section 3, test 12)

| Case | D1 / D6 recovered | range (mag) | jump 2.42 um | jump 1.63 um | phase scatter |
|---|---|---|---|---|---|
| exact shape | 1.000 / 1.000 | 0 | 0 | 0 | 0 |
| model R_e 25 % too large | 1.11 / 1.09 | 0.026 | 0.012 | -0.003 | 0.6 % |
| model R_e 20 % too small | 0.87 / 0.89 | 0.028 | -0.013 | 0.003 | 0.5 % |
| exp model, true n = 4 | 0.89 / 0.88 | 0.028 | 0.014 | -0.005 | 1.6 % |
| n = 4 model, true exp | 1.10 / 1.13 | 0.038 | -0.020 | 0.006 | 2.2 % |
| wrong b/a and PA (0.55, 30 deg) | 1.06 / 1.05 | 0.016 | 0.006 | -0.003 | 0.4 % |
| colour gradient (B/T 0.3 -> 0.5, model 0.3) | 1.00 / 1.05 | 0.053 | 0.003 | -0.001 | 0.4 % |

Total flux off by 10-16 %, SED by at most 0.04 mag (0.053 for the colour gradient), jumps <= 0.02 mag.

## 5. Model-corrected aperture flux (followup sections 3-4)

Definition: sum inside a 2 px (12.3") aperture of data minus the fitted neighbours (flagged pixels filled with
the model), divided by the model's predicted fraction in the same pixels. Test 12: range 0.006 / 0.008 / 0.012
mag for the R_e x1.25, wrong-index and colour-gradient cases, jumps <= 0.003 mag, phase scatter 0.1-0.3 %.
Total-flux offset constant with wavelength (0.84-1.04). On the real galaxy, 2 px aperture / model agreed to
0.965-1.025 (median per detector), D5 and D6 furthest from 1. The 5 px (31") aperture is a poor check
(~78 pixels; 1 % background error is several % of the galaxy flux at 4-5 um).

## 6. Neighbours (followup section 4, test 13; real DR1 + QR3 exposures)

Reference galaxy SDSS 1237661812804550732 (z 14.9); SDSS PhotoPrimary z < 21 within 2.2': 51 sources, 7
inside the 9 px joint region, including stars at 11.9" (1.9 px, z 18.0) and 26.2" (4.3 px, z 17.5).
- Ignoring them raises the galaxy's model flux by 0.8-1.6 % (median per detector 0.986-0.993 joint / alone),
  almost the same at all wavelengths, and raises chi2/dof in D1-D4 from 1.1-1.5 to 2.0-3.2.
- Joint fit removes the chi2 excess; errors rise 1-2 %.
- 1 px mask around faint separated neighbours gives the same flux (0.997-1.007 of joint); 1.5 px mask removes
  15-22 % of the galaxy's model weight and raises errors 5-10 %. Close companions need a joint fit.
- tractorjax-spherex fits every catalogue source per 15 px tile (3 px halo) jointly; catalogue shredding
  (knots or bulge listed as separate sources) splits the galaxy's light; clean the catalogue first.
- SDSS b/a of faint galaxies can be unphysical (0.05 at r 22); b/a >= 0.2 was used.

## 7. Channel-specific real-data errors (followup sections 4-5; options section 4b)

- Background near airglow: the 1.10 um exposure next to He I 1.083 um had chi2/dof 12 (alone) to 29 (joint),
  5 px aperture / model 0.63, and 0.81 of the hbahk flux with a constant annulus background.
- DICHROIC: the 2.413-2.416 um exposure has every fit pixel flagged; our code rejects it, tractorjax-spherex
  fits it.
- Isolated bad exposure: one 4.749 um exposure gave 0.11-0.17 mJy in both codes where neighbours give
  ~2.3 mJy (chi2/dof 4.2 and 30.7).
- These matter more than shape or neighbour effects.

## 8. Two codes agree (options section 4b, test 11)

On 33 common exposures, our 164-line code / tractorjax-spherex Sersic flux (same QR2 -> R7 flux correction
and solid-angle ratio applied): median 1.011 (D1-D5 1.009-1.018, D6 0.972), 16-84 % 0.989-1.025; point-source
1.002-1.008. tractorjax-spherex silently dropped 2 of 36 cutouts truncated by the detector edge.

## 9. Formal errors are too small (options sections 3-4; study findings)

Pixel noise / sqrt(VARIANCE) on unflagged pixels 1.18 and 1.36 in two real files; for Gaia stars chi2/dof
1.4-1.8 at S/N 10-30 rising to 16-18 at S/N 300-1000. Errors must be calibrated on the data.

## 10. Conventions (options section 3; lessons)

- Solid angle: a constant 6.15" pixel is wrong by -1.7 % to +1.1 % across the detectors; use the Solid Angle
  Pixel Map.
- QR3/DR1 ePSF stamps sum to 1 on the 5x grid, so native-spaced samples sum to 1/25; choose the zone in
  parent-frame coordinates (CRPIX1A/2A); check OVSMPX and DETCOORD against the official PSF tutorial.
- NaN pixels must be indexed out, not given zero weight (NaN * 0 = NaN).
- Point-sampling an n = 4 profile puts ~35 % of the flux in the central sample at R_e = 2" on a 0.12" grid;
  check rendered sums against the analytic enclosed light.
- The IRSA cutout service answers 503 under concurrent load; back off and retry; keep concurrency at ~2.
- Cutouts took ~9 s each at 2 concurrent requests (36 cutouts in 336 s).

## 11. Archive state found on 2026-11-13 (followup section 0)

DR1 at IRSA: reprocessed QR2 images (`l2b-v27-2026-196`, pipeline 7.0.5) to be used with QR3 as one set;
all-sky cube for visualisation; no Level 3 catalogue. TAP collections `spherex_dr1`, `spherex_dr1_deep`,
`spherex_dr1_cal`, `spherex_qr3`, `spherex_qr3_deep`; `spherex_qr2` dropped (S3 keeps `qr2/`). Reference
galaxy: 296 DR1 + 45 QR3 images (326 QR2 the day before). `dr1/epsf/` identical to `qr3/epsf/` (ETags).
Open: whether DR1 images need `l3_flux_corrections` (present under `dr1/`).

## 12. hbahk stack (options section 4)

spherex-retrieval 0.4.0 (`0eb2ae8`, MIT; fixed QR3 wide/deep duplicates and a CRPIX1A/2A sign error),
tractor-jax 0.3.1 (`816a5c3`, GPL-2.0), tractorjax-spherex 0.3.3 (`9266a19`, GPL-3.0; per-visit fit_chi2,
mask_frac, quality_flag; catalogue input). Installed with one `uv pip install` in 56 s; 1.9 GB including uv
cache and venv. Photometry 4.7 s for 34 exposures (Sersic). Catalogue expected: Legacy Survey DR10 via Data
Lab (credentials) or a supplied table; one-row catalogue built by hand with `shape_r`, `sersic`,
`shape_e1/e2` (orientation convention read from the code, not tested). DICHROIC pixels are fitted; flag bits
hard-coded; errors formal only.
