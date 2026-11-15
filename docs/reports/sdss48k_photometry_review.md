# Review of the student's SPHEREx photometry of the 48k SDSS galaxies

Date: 2026-11-15. Data reviewed: `/Users/shuang/data/spherex/spherex_sdss48k_phot` (four Parquet files and a
README, made 2026-11-12 on OSC). Code: the student's repository
`/Users/shuang/Dropbox/work/project/otters/spherex_photometry_code` (read only; the local copy is at its first
commit of 2026-11-09 and does not yet hold the `sdss48k/` run folder the README points to, but the production
script `top100k/spx_phot.py` and talltable's `optimal_extract` at commit `6d8ded3` are there). Scripts of this
review: `scripts/sdss48k_review/` (`summarise_catalogue.py`, `compare_with_demo.py`,
`measure_failures_and_errors.py`, `make_figures.py`). Figures: `docs/figures/sdss48k_review/`.

## 1. Summary

- **What it is.** Forced photometry at the SDSS positions of all 48,111 galaxies of the MPA-JHU parent catalogue
  (0.03 < z < 0.06, log M* >= 10), on every QR2 and QR3 SPHEREx image that covers them: 16.5 million
  measurements, a median of 345 per galaxy, each one image at one wavelength between 0.735 and 5.025 um.
  Every row carries two fluxes: a point-source (PSF) fit and a 12.3 arcsec aperture sum.
- **Bookkeeping is sound.** The target table is the parent catalogue row for row, every galaxy has
  measurements, and on the same exposures the wavelengths agree with ours to 0.0002 um and the aperture fluxes
  with ours to 1-3 % for isolated galaxies. The image list and footprints can be reused as they are.
- **The PSF flux should not be used for galaxy SEDs.** It assumes a point source; on our six demo galaxies it
  recovers 31-92 % of the total flux, by a fraction that changes from detector to detector (so it bends the
  SED shape), and talltable's 4-sigma pixel clipping pushes 8.7 % of all bright measurements to more than 1.5
  times the aperture flux (up to 10-100 times). This is the failure our photometry study of 2026-11-12/13
  predicted from simulations.
- **The aperture flux is the usable product, after corrections.** It repeats to 3-5 % per exposure in D1-D4,
  but it is not a total flux (56-96 % of our Sersic total on the four isolated demo galaxies, falling by up to 0.1 mag from
  D1 to D6), it has no neighbour subtraction, it sums pixels that the fit masks as bad (2-4 % of exposures are
  gross outliers), and its formal errors are 1.2-1.8 times too small.

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

Not usable for SED science: `opt_flux_uJy` (point-source flux of extended galaxies, wavelength-dependent
losses, clipping failures).

To turn the aperture flux into total-flux SEDs (each item is a decision for the owner):
1. **Aperture correction per galaxy and detector** from the optical shape convolved with the SPHEREx PSF, as in
   our model-corrected aperture (study section 5; demo section of `docs/sed_extraction.md`). Without it the
   SED shape carries the size-dependent D1-D6 drift (up to 0.1 mag in the demo galaxies).
2. **Neighbour flag or subtraction**: at least flag galaxies with SDSS or Legacy Survey sources within ~25 arcsec;
   g4 and g5 show 17-43 % contamination.
3. **Bad pixels in the aperture**: cannot be fixed from the catalogue (the number of flagged pixels inside the
   aperture is not stored); outlier rejection along wavelength is the only remedy without re-measuring.
4. Solid angle (constant 6.15 arcsec pixel, -1.7 % to +1.1 % by detector in our study) and the missing QR3 weeks
   and DR1 images are smaller effects.

The alternative is to re-measure with the demo's forced Sersic photometry. The student's infrastructure (exact
footprints, row-band reads from S3, sharded resumable runs) is the part worth keeping; only the measurement
step would change. The cost of such a run has not been measured.

## 8. Questions for the student

- Push the `sdss48k/` run folder (job scripts, `targets.csv`, logs) to the repository; the local copy ends at
  2026-11-09.
- Could the run store, per measurement, the number of flagged pixels inside the aperture and the sub-pixel
  position? Both would let the aperture outliers and the phase scatter be handled without re-measuring.
