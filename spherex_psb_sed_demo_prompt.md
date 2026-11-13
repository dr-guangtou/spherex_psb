# Task: a demo of robust SED extraction from SPHEREx for low-redshift SDSS galaxies

You are working in `/Users/shuang/Dropbox/work/project/otters/spherex_psb` (my repository, GPL-3). The goal is a
small demo. For a handful of SDSS galaxies at 0.03 < z < 0.06:
- measure SPHEREx spectrophotometry in every exposure;
- assemble a reliable 0.75-5 um SED (low-resolution spectrum) for each galaxy;
- make QA figures that show whether the SED shape can be trusted.

What matters is the SED shape: relative fluxes versus wavelength, above all across detector boundaries. A
perfect 2-D model of the galaxy is not the goal, and neither is its total flux.

## 0. Ground rules

- Follow both the project and global `CLAUDE.md`.
- Before planning, read `docs/lessons.md`, `docs/SPEC.md`, `docs/todo.md`, and at least sections 2-9 and 12 of
  `docs/spherex_data_guide.md`.
- Create a new branch `feature/sed-demo`. Branch from `feature/spherex-data-learning` (it holds the docs) unless
  `main` already contains its commits. Commit at checkpoints. Do not merge or push without asking.
- Never estimate numbers: measure them, or cite the source.
- Validate on one galaxy and a few exposures (sub-minute runs) before scaling up.
- Permission for this task (record it in SPEC section 3, since it changes the "no third-party tools" rule):
  - You may install, run and read hbahk's `spherex-retrieval` (MIT), `tractor-jax` (GPL-2.0) and
    `tractorjax-spherex` (GPL-3.0).
  - Check licence compatibility before copying any code.
  - Ask before using any other third-party SPHEREx tool.
- `/Users/shuang/Dropbox/work/project/otters/spherex_photometry_code` is a student's repository: read only.
  Never edit it, write into it, or import from it.
- Data:
  - All downloads go under `/Users/shuang/data/spherex` (currently empty).
  - Any single download larger than 300 MB needs my approval.
  - Total budget for the demo: 10 GB.
  - In an earlier study, 36 cutouts plus the ePSF calibration files took about 217 MB. Each DR1/QR3 cutout
    carries the whole EPSF extension. Measure the size of the first cutouts, project the total, and ask me
    before going over budget.
  - Point package caches (e.g. the calibration cache of spherex-retrieval) to that folder or to a scratch
    folder.
  - At the end, move temporary material (clones, scratch caches) to `~/.Trash/<name>_<date>` and report sizes.
- `uv` only. In an earlier probe the hbahk stack installed with one `uv pip install` command and pulled in JAX
  (venv plus uv cache about 1.5 GB).

## 1. What earlier work established (read it, then record it)

An earlier study (2026-11-12/13) tested the methods on one real galaxy and in simulations. It lives in the
git-ignored `temp/` folder of the student's repository, so it is not under our version control. Write the facts
you rely on, with their source paths, into `docs/reference_notes/photometry_study_2026-11.md`.

Read, under `/Users/shuang/Dropbox/work/project/otters/spherex_photometry_code/temp/`:
- `docs/sed_photometry_followup.md`: the latest; its section 5 gives the recommendation.
- `docs/galaxy_photometry_options.md`: probes of the hbahk stack, the official stack and our own code.
- `docs/extended_galaxies.md`: the sample's sizes and why a point-source fit fails.
- `docs/lessons.md`.
- Reference scripts (take ideas, do not import):
  - `scripts/probe_scratch_galaxy_photometry.py`: forced galaxy photometry in 164 lines, from TAP, cutouts
    and the QR3 ePSF.
  - `scripts/test_neighbours_joint_versus_mask.py`: SDSS neighbour catalogue, Sersic renderer, joint linear
    solve, masking, model-corrected aperture.
  - `scripts/test_sed_shape_robustness.py`: synthetic tests over all ePSF zones.

Key measured results:
- **Point-source fit: ruled out.** For R_e 2-8" it distorts the SED by 0.07-0.30 mag over 0.75-5 um. It also
  puts a -0.03 to -0.15 mag fake step at the D3/D4 boundary (2.42 um). In the parent sample (DR17 selection,
  45,300 galaxies), the r-band R_e is 1.6", 4.4" and 10.6" at the 5th, 50th and 95th percentiles.
- **Forced photometry with a PSF-convolved Sersic model at fixed optical shape: robust for an SED.**
  - Model errors tested: size off by 25 %, wrong Sersic index, wrong b/a or PA.
  - These change the total flux by up to 10-16 %, but the SED by at most 0.04 mag, and the detector jumps by
    at most 0.02 mag.
  - An assumed colour gradient (bulge fraction rising with wavelength) tilted the SED by 0.053 mag.
- **Model-corrected aperture flux: even more robust.**
  - Definition: the sum, inside a 2 px (12.3") aperture, of the data minus the fitted neighbours, divided by
    the model's predicted fraction in the same pixels.
  - It was 2-5 times less sensitive to the same model errors (at most 0.012 mag).
  - On the real galaxy, this and the model flux agreed to 0.965-1.025 (median per detector).
- **Neighbours.**
  - Ignoring two faint stars (z 18.0 and 17.5, against 14.9 for the galaxy; 1.9 px and 4.3 px away) raised the
    galaxy's model flux by 0.8-1.6 %, almost evenly at all wavelengths.
  - It also raised χ²/dof in D1-D4 from 1.1-1.5 to 2.0-3.2.
  - Fitting galaxy and neighbours jointly removed the χ² excess and raised the errors by only 1-2 %.
  - A 1 px mask around faint, separated neighbours gave the same flux. A 1.5 px mask removed 15-22 % of the
    galaxy's model weight.
  - Close companions need a joint fit.
- **The largest real-data errors are channel-specific:**
  - background near airglow lines: the 1.10 um exposure next to He I 1.083 um had χ²/dof 12-29;
  - pixels flagged DICHROIC at the D3/D4 edge;
  - isolated bad exposures: one 4.75 um exposure came out at about 5 % of its neighbours' flux in two
    independent codes.

  These matter more than shape or neighbour effects.
- **Two codes agree.** Our 164-line code matched tractorjax-spherex to about 1 % (median) on the same
  exposures. Watch two things in tractorjax-spherex: it fits DICHROIC pixels, and it silently dropped 2 of 36
  cutouts that the detector edge had cut short.
- **Formal errors are too small.**
  - Pixel noise / sqrt(VARIANCE) on unflagged pixels was 1.18 and 1.36 in two real files.
  - For Gaia stars, χ²/dof rose from 1.4-1.8 at S/N 10-30 to 16-18 at S/N 300-1000.
  - These galaxies are bright: a point source with the same total z-band flux would have a median per-exposure
    S/N of about 240.
  - So calibrate the errors on the data.
- **Pixel solid angle.** A constant 6.15" pixel is wrong by -1.7 % to +1.1 % across the detectors. Use the
  Solid Angle Pixel Map.
- **ePSF conventions.**
  - The stamps sum to 1 on the 5x grid, so the samples at native pixel spacing sum to 1/25.
  - Choose the zone in parent-frame coordinates (CRPIX1A/2A).
  - Check the orientation keywords (OVSMPX, DETCOORD) against the official PSF tutorial, especially for D4-D6.

## 2. Archive state: re-verify, it changed on 2026-11-13

- **DR1 is out (November 2026).** It holds reprocessed QR2 images (`l2b-v27-2026-196`, pipeline 7.0.5), meant
  to be used together with QR3 as one uniformly processed set. It also has an all-sky spectral cube, which
  IRSA says is for visualisation only. There is no Level 3 forced-photometry catalogue.
- **TAP collections.** These are now `spherex_dr1`, `spherex_dr1_deep`, `spherex_dr1_cal`, `spherex_qr3` and
  `spherex_qr3_deep`. `spherex_qr2` is no longer listed (S3 still has `qr2/`). Use DR1 + QR3.
- **Count everything.** Print per-collection counts in every discovery step, and check for duplicate
  exposures.
- **Same ePSF files.** `dr1/epsf/` is identical to `qr3/epsf/` (same ETags).
- **Open question.** `l3_flux_corrections` exists under `dr1/`. Do DR1 images need it? Answer from official
  documentation before applying it.
- **Update the guide.** Record what you verify in sections 2 and 5 of `docs/spherex_data_guide.md`; it still
  lists the QR2 collections. If you think the external skill `spherex-irsa-access` needs updating, propose the
  change instead of editing it.

## 3. Demo sample

- **Parent catalogue:** `/Users/shuang/data/mpa/outputs/catalogs/galaxy_summary_48111.csv`. Its columns are
  `specobjid`, `ra_deg`, `dec_deg`, `redshift`, `log_stellar_mass_msun`, `dn4000_emission_subtracted` and
  `h_delta_a_emission_subtracted_angstrom`. It is based on SDSS DR8. Do not process the whole sample.
- **Six galaxies**, each with a role fixed before looking at any SPHEREx data:
  1. **Reference galaxy** from the earlier study: SDSS objID 1237661812804550732, RA 168.14539,
     Dec +12.072366, z 0.0458, exponential R_e 4.38", b/a 0.77, PA 101.7 deg. If it is not in the parent
     catalogue, include it anyway as an extra regression case.
  2. A compact galaxy (R_e about 2" or less).
  3. A large galaxy (R_e about 8-10" or more).
  4. A galaxy with a close neighbour of comparable brightness, or a bright star, within about 2 px (12").
  5. A galaxy outside the Legacy Survey footprint, so that only SDSS priors exist.
  6. A post-starburst-like spectrum: high HδA and low Dn4000.
- **Constraints:** covered by the DR1 + QR3 wide survey with exposures in all six detectors; not in a deep
  field, to keep downloads small.
- **Figure first:** make the sample figure (section 8, item 1), then proceed.

## 4. Shape priors and neighbour catalogue

- **SDSS (all targets).**
  - Cross-match by position and check the redshift. Do not rely on `specobjid` formats across SDSS releases.
  - Use `astroquery.sdss` (SkyServer SQL) to get: deV/exp radii, axis ratios and position angles, fracDeV,
    modelMag, and the deblending flags.
- **Legacy Survey DR10 or DR9 (where covered).**
  - Get the Tractor catalogue: `type`, `shape_r`, `shape_e1`/`shape_e2`, `sersic`, the fluxes, and the WISE
    W1/W2 forced photometry. Note the large-galaxy (SGA) entries.
  - Find a straightforward access route (`astroquery`, an anonymous NOIRLab Data Lab query, or the Legacy
    Survey viewer catalogue endpoint) and record which one works.
- **Neighbours.**
  - Take every catalogue source inside the fit region plus a margin, down to a depth set relative to the
    target's brightness, and render each with its own shape.
  - Clamp unphysical shapes of faint galaxies: SDSS gave b/a = 0.05 for some, and b/a >= 0.2 was used before.
- **Shredding check.** Some catalogue entries inside the target's light are really parts of it (bulge, knots,
  HII regions). Remove them, or the fit will split the galaxy's light among them. Show the removed entries in
  the image QA figure.

## 5. Per-exposure measurement

Design:
- Write our own small, transparent measurement layer, using only the parts of the SPEC section 4 package
  layout that the demo needs.
- Run tractorjax-spherex on the same exposures with the same catalogue as an independent cross-check.

Steps:
- **Pixels.** Use IRSA cutouts or S3 (`nasa-irsa-spherex`, anonymous access).
  - Cutouts took about 9 s each at 2 concurrent requests, and the service sometimes answers 503: retry with
    back-off.
  - Check whether S3 range reads work on DR1/QR3 files. The student's code used them only on QR2-layout files.
- **spherex-retrieval (optional).** It may handle retrieval, the spectral WCS, the Solid Angle Pixel Map and
  calibration. It predates DR1, so test it on one DR1 file and one QR3 file before relying on it.
- **Background.**
  - Subtract ZODI from IMAGE.
  - Then fit a local background jointly with the sources: at least a constant. Test a plane, and a term that
    depends on the pixel wavelength (CWAVE) near airglow lines; tractorjax-spherex has such an airglow model to
    read.
  - Use the R7 header keywords (`HE_AIRGLOW_CONT` and the others) for exposure screening.
- **Mask.**
  - Exclude the IRSA tool's flag set plus TRANSIENT, OVERFLOW and DICHROIC (see the data guide).
  - Remove NaN pixels from the fit altogether: giving them zero weight still poisons weighted sums.
- **Model.**
  - Render each Sersic profile in sky coordinates on the ePSF's 5x grid, with a sub-sampled centre.
  - Convolve with the nearest ePSF zone and sample at native pixels.
  - Weight by VARIANCE and solve linearly for the amplitudes of the target, the neighbours and the background.
  - Positions and shapes stay fixed.
- **Estimators.**
  - (a) Forced-model flux.
  - (b) Model-corrected aperture flux. Keep the aperture fixed in arcsec at all wavelengths; 2 px worked for
    R_e 4.4", so test 1.5-3 px against galaxy size. Fill flagged pixels with the model.
  - (c) Point-source fit, only as a negative control.
- **Wavelength.** Take CWAVE and CBAND at the target position from the spectral WCS, not the zone CWAVE of the
  ePSF.
- **Units.** Convert MJy/sr to flux density with the Solid Angle Pixel Map.
- **Records.** Write Parquet (add `pyarrow` with `uv`), one row per exposure, holding:
  - provenance: release, collection, pipeline version, `obs_id`, detector, MJD;
  - wavelength: CWAVE, CBAND, ePSF zone;
  - fluxes and errors of both estimators;
  - fit diagnostics: χ²/dof, number of pixels, fraction of model weight masked, background parameters, number
    of neighbours;
  - a quality or rejection code.
- **Screening.** Every rejected exposure gets an explicit reason code; nothing is dropped silently. Reasons:
  cutout cut short by the detector edge, too much model weight masked, χ² outlier, airglow flag, outlier
  against nearby wavelengths.

## 6. SED assembly

- Keep the per-exposure points. Also build a binned spectrum: choose the grid (DR1's 102 channels or constant
  resolution) and justify it.
- **Combining.** Use a robust combination. Take errors from the calibrated per-exposure errors and from the
  scatter between exposures.
- **No pixel clipping.** Do not use kappa-sigma clipping at pixel level: the student's production clipping
  badly biased bright extended sources.
- **Galactic extinction.** It tilts the SED across 0.75-5 um. Get E(B-V) from the IRSA dust service, correct
  for it, and record it.
- **Wavelength axes.** Give both observed- and rest-frame wavelengths.

## 7. Validation: what "reliable" means here

1. **Detector-boundary test.**
   - Detector overlaps from the ePSF CWAVE ranges: D1/D2 1.096-1.115, D2/D3 1.624-1.651, D3/D4 2.417-2.426,
     D4/D5 3.805-3.823 and D5/D6 4.408-4.420 um.
   - In each overlap, compute the flux ratio between the two detectors, per galaxy.
   - The science features fall here at z = 0.03-0.06: the 2.29 um CO bandheads at 2.36-2.43 um (D3/D4) and the
     1.6 um bump at 1.65-1.70 um (D2/D3).
2. **Estimator consistency.** The ratio of model flux to corrected-aperture flux should be flat with
   wavelength.
3. **Negative control.** The point-source fit on the same data must show the step that simulations predict.
   This proves the test can detect a step.
4. **Injection and recovery.**
   - Inject a synthetic galaxy of known shape and SED into the real cutouts, on blank sky near the target.
   - Run the full pipeline and recover the SED shape.
5. **External photometry.**
   - Compute synthetic broadband fluxes from the SPHEREx SED.
   - Compare them with SDSS z, 2MASS J/H/Ks (`astroquery.ipac.irsa`) and WISE W1/W2. Prefer the Legacy Survey
     forced WISE photometry, which uses the same model approach.
   - Compare colours where the apertures differ.
6. **Cross-code check.** Run tractorjax-spherex on the same exposures and catalogue, with the `linear` or
   `eigfloor` solver and DICHROIC pixels excluded.
7. **Error calibration.**
   - Use repeat measurements at nearly the same wavelength from different visits.
   - Make per-detector pull distributions, and report the error scale factor or floor.
8. **IRSA Spectrophotometry Tool (optional).** The tool's Sersic mode runs only in the browser, takes R_e up to
   20" and 20 sources per job. Prepare the input table so that I can submit it.

## 8. Figures: PNG only, suitable for a journal

**Style:**
- One shared style module.
- Fonts: `text.usetex = True` (TeX is installed under `/Library/TeX/texbin`), Computer Modern serif.
- Size: two-column journal widths (single column about 3.4 in, double about 7.0 in), 8-9 pt text, 300 dpi.
- Ticks: inward on all four sides, with minor ticks.
- Colours: a colour-blind-safe palette, with one fixed colour per detector D1-D6 in every figure.
- Units in LaTeX, e.g. `$\lambda_{\rm obs}\ [\mu{\rm m}]$` and `$F_\nu\ [{\rm mJy}]$`.
- No titles inside figures. Use panel labels, and put captions in the report.

**Required figures:**
1. **Sample.** The parent catalogue in the redshift-mass plane and the Dn4000-HδA plane, plus the R_e
   distribution, with the demo galaxies marked.
2. **Per-galaxy image QA.**
   - An optical image with the target's ellipse, the neighbours and any removed shreds.
   - For one exposure per detector: data, model and normalised residual stamps, with the mask and the aperture
     drawn on.
3. **Per-exposure diagnostics.**
   - χ²/dof, masked fraction and background level against wavelength.
   - Mark airglow lines, and mark rejected exposures with their reasons.
4. **SED per galaxy.**
   - Per-exposure points coloured by detector, the binned SED, both estimators and the external photometry.
   - A rest-frame top axis with the features marked.
   - A lower panel showing the ratio of the two estimators.
5. **Detector-boundary test** across the demo sample, including the point-source negative control.
6. **Injection-recovery test** and **error calibration** (pull distributions).
7. **All demo SEDs together** in the rest frame, normalised at a common rest-frame wavelength.

Look at every PNG before reporting it.

## 9. Checkpoints and deliverables

- **Before coding:**
  - Update `docs/SPEC.md`: the demo's scope, the tool permission, and the answered open questions (the sample
    is low-z SDSS; the first-pass approach).
  - Add the task list to `docs/todo.md`.
- **Checkpoint A: stop and show me.**
  - Run galaxy 1 end to end, with 6 exposures per detector, and make figures 2-4.
  - Report the measured size per cutout and the projected download for the full demo.
- **Checkpoint B.**
  - Measure every exposure of the six galaxies.
  - Run validation items 1-7 and make all figures.
  - Write the report `docs/demo_sed_report.md`.
- **When to ask me:**
  - downloads that would exceed the budget;
  - changes of scope;
  - findings that need my judgement, such as a systematic difference between DR1 and QR3.
- **At the end:**
  - Update lessons, add the todo review, and update the data guide.
  - Report the disk used in `/Users/shuang/data/spherex`, and what was moved to the Trash.
- **Out of scope:** the full sample, stacking, SED or stellar-population fitting, and mosaics.
