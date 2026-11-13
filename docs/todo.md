# spherex_psb todo

## Task 1: SPHEREx data learning session (2026-09-22)

Goal: build a comprehensive, current picture of the SPHEREx mission, instrument, data
products, pipeline, access, and the methods used in the literature to extract galaxy
spectra, with emphasis on systematics and backgrounds.

- [x] Per-source reference notes in `docs/reference_notes/`
  - [x] IRSA SPHEREx mission page and linked pages
  - [x] SPHEREx archive documentation site
  - [x] SPHEREx Explanatory Supplement v2.0 (full read; PDF saved in `external/`)
  - [x] IRSA SPHEREx tutorial notebooks (sources saved in `irsa_tutorial_sources/`)
  - [x] IRSA online help for the Spectrophotometry and Mosaic tools (text in `external/`)
  - [x] Pipeline paper (arXiv:2511.15823)
  - [x] Spectral map making paper (arXiv:2603.25790)
  - [x] Instrument paper (arXiv:2603.29835)
  - [x] Method references 2604.22012, 2603.12390, 2607.18048, 2607.00543, 2605.06791, 2603.10135
- [x] Synthesized guide `docs/spherex_data_guide.md`
- [x] `docs/SPEC.md` v0.1
- [x] `docs/lessons.md` seeded
- [x] Live validation against IRSA: TAP tables and columns, SIA collections, QR2 and QR3
      cutout layouts and headers, S3 prefixes (`scripts/`)
- [x] Update external skill `spherex-irsa-access`

### Review

- The single most important operational facts: IMAGE is not zodi-subtracted; per-pixel
  wavelengths must come from CWAVE/CBAND; QR3 (R7) changed the PSF product to an ePSF
  table and the flag header convention; the IRSA Spectrophotometry Tool supports point
  and Sersic (Re < 20 arcsec) sources but has no API and a 20-source limit; resolved
  galaxies need our own per-exposure extraction.
- Gaps that remain: no official recipe for extended-source photometry or spectral
  stacking; per-channel error budgets await Ashby et al. (2026); DR1 (late fall 2026)
  will change calibrations again.

## Task 1b: review of existing SPHEREx software (2026-09-23)

- [x] Review the eight user-suggested repos plus GitHub/arXiv search (16 notes in
      `docs/reference_notes/tools/`, synthesis in `docs/spherex_tools_review.md`)
- [ ] Read Bahk et al. 2026 (arXiv:2606.19875) extended-source validation
- [ ] Test-build `tractor-spherex` in the uv environment (astrometry.net utils, SWIG)
- [ ] Decide on vendoring `hbahk/spherex-retrieval` for retrieval and PSF preparation

### Review

- No existing tool does extended-source forward modeling with free shapes, explicit zodi
  handling for photometry, rest-frame stacking, or (outside the hbahk repos) QR3 support.
  The plan is a thin pipeline of ours on top of spherex-retrieval (MIT) and
  tractor-spherex (official fork), copying specific MIT/BSD functions from SPIFF,
  spxquery, spexpi and spherex-pipelines, and re-implementing GPL-3 ideas.

## Task 4: SED demo for low-z SDSS galaxies (2026-11-13, branch feature/sed-demo)

Spec: `docs/sed_demo_task.md`. Facts from the earlier study: `docs/reference_notes/photometry_study_2026-11.md`.

Before coding
- [x] Branch `feature/sed-demo`; task spec moved to `docs/sed_demo_task.md`
- [x] Study note with sources; archive re-verified (DR1 collections, S3 `dr1/` tree, file layout, Supplement v2.1);
      guide sections 2, 4, 5 updated; SPEC sections 3, 6, 7 updated
- [x] hbahk stack installed with `uv add` (venv 0.94 GB); parent selection reproduced on SkyServer with shapes
- [x] spherex-retrieval tested on one DR1 and one QR3 cutout (works; collections passed explicitly)
- [x] Legacy Survey DR10 access route recorded (Data Lab TAP, RA/Dec box in the WHERE clause; q3c and the viewer do not work)

Sample (figure 1 first)
- [x] Candidate pools and SPHEREx coverage per detector; galaxies 2-6 chosen; figure 1

Checkpoint A (stop and show)
- [x] Measurement layer: cutouts, ePSF zone, Sersic renderer, neighbours, background, joint solve, two estimators
- [x] Galaxy 1 with 6 exposures per detector; figures 2-4; cutout size and projected download

Checkpoint B (2026-11-14)
- [x] All exposures of the six galaxies (2,225 exposures, 2,104 used); validation 1-7; all figures;
      `docs/demo_sed_report.md`
- [x] Lessons, todo review, guide update, disk report, Trash moves

Review (2026-11-14)
- Delivered: `spherex_psb/{archive,products,extraction,spectra,validation,figures}`, `scripts/sed_demo/`
  (sample, measure, figures, validate, drivers, summary), 22 figures, the report, the IRSA tool input table.
- What worked: cutout bundles from spherex-retrieval (0.2 MB each, 2,242 in 1.5 h of requests); the joint
  linear solve with fixed shapes; the quadratic CWAVE background; the three-estimator design (the point-source
  control catches what the model would hide); the cross-code check (it found the 2 % renderer bias).
- What did not: the first renderer core sampling (fixed); the QA-stamp choice (fixed); the log filter;
  network steps without timeouts (fixed with retries and the per-galaxy driver); the task spec never
  committed (restored and committed now).
- Open for the user: D3/D4 step is the CO bandhead plus a residual calibration term of 0-0.10 mag that the
  stars in the same cutouts do not pin down; which "total flux" convention to adopt; pulls 1.1-1.4 in D1-D4
  at S/N > 30 (a fractional error floor of 0.7-2.4 % per exposure for the three n = 4 galaxies, none
  detectable for the n = 1 galaxies) and 1.5-2.2 in D1-D3 for the compact and the neighbour galaxy.
- Next (not started): decide the flux convention; a position-jitter test for compact galaxies; the IRSA tool
  submission with `results/irsa_spectrophotometry_tool_input.csv`; then the full post-starburst sample.

## Task 2 (superseded by Task 4): sample and coverage

- [ ] Define the post-starburst sample (parent catalog, redshift range, sizes) with the user
- [ ] Cross-match with SPHEREx coverage via TAP; record per-object exposure counts per band
- [ ] Choose one unresolved, one semi-resolved, one resolved test galaxy

## Task 3 (next): prototype extraction

- [ ] Submit the three test galaxies to the IRSA Spectrophotometry Tool (point and Sersic)
- [ ] Implement cutout retrieval with provenance and a reader that handles QR2 and QR3 layouts
- [ ] Implement per-exposure aperture photometry with CWAVE/CBAND wavelengths, ZODI plus
      local background, flag masks, VARIANCE propagation, ePSF aperture corrections
- [ ] Compare with the tool output and with 2MASS/WISE synthetic photometry
- [ ] Prototype rest-frame stacking with bootstrap errors
