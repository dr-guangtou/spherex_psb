# spherex_psb todo

## Task 1: SPHEREx data learning session (2026-09-22)

Goal: build a comprehensive, current picture of the SPHEREx mission, instrument, data
products, pipeline, access, and the methods used in the literature to extract galaxy
spectra, with emphasis on systematics and backgrounds.

- [x] Per-source reference notes in `docs/references/`
  - [x] IRSA SPHEREx mission page and linked pages
  - [x] SPHEREx archive documentation site
  - [x] SPHEREx Explanatory Supplement v2.0 (full read; PDF saved in `external/`)
  - [x] IRSA SPHEREx tutorial notebooks (sources saved in `irsa_tutorial_sources/`)
  - [x] IRSA online help for the Spectrophotometry and Mosaic tools (text in `external/`)
  - [x] Pipeline paper (arXiv:2511.15823)
  - [x] Spectral map making paper (arXiv:2603.25790)
  - [x] Instrument paper (arXiv:2603.29835)
  - [x] Method references 2604.22012, 2603.12390, 2607.18048, 2607.00543, 2605.06791, 2603.10135
- [x] Synthesized guide `docs/spherex_data_guide.md` (retired 2026-11-14 into the site pages)
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
      `docs/references/tools/`, synthesis in `docs/reports/spherex_tools_review.md`)
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

Spec: `docs/reports/sed_demo_task.md`. Facts from the earlier study: `docs/references/studies/photometry_study_2026-11.md`.

Before coding
- [x] Branch `feature/sed-demo`; task spec moved to `docs/reports/sed_demo_task.md`
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
      `docs/reports/demo_sed_report.md`
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

## H-minus bump feasibility (2026-11-14)

- [x] Evaluate the Hbump_opt index of the H-bump paper on the six demo SEDs: resolution test on the
      cached FSPS grid, exposure counts per window, bootstrap errors, D2/D3 step bias, recovery simulation
      with the real sampling (`docs/reports/hminus_bump_feasibility.md`, figure 8).
- [ ] Settle the D2/D3 step at the 0.3 % level (many field stars, or point-source control per ePSF zone)
      before using any index that straddles 1.64 um observed.
- [ ] Forward-model index estimator over 1.4-2.0 um using every exposure and its bandpass; validate on
      injected FSPS spectra with the real sampling.
- [ ] Decide whether the index sample should sit at z > 0.1 (whole index on D3) or accept the
      D2/D3 calibration term.

### Review

The index is feasible at the 0.01 mag level per galaxy with today's coverage and 0.005 mag with stacks or
the four-survey mission, once the D2/D3 step and the estimator bias are handled; the five normal galaxies
show indices in the TP-AGB-on range and the post-starburst galaxy the weakest bump, neither of which can
be interpreted before those two systematics are removed.

## Documentation site (2026-11-14)

- [x] First site version (MkDocs + Material) with index, primer, data access, reduction and analysis, SED
      extraction and spectral index pages; project pages and reference notes in the navigation; GitHub Pages
      workflow. Replaced the same day by the note-style conversion below.
- [x] docs/ reorganised: references/{irsa,papers,studies,tools,sources}, reports/, figures/{sed_demo,site,external}.
- [x] Site figures from calibration products and records (`scripts/site_figures.py`); paper figures with credits.
- [ ] Enable GitHub Pages (source: GitHub Actions) in the repository settings after the branch is merged.
- [ ] Propose the matching updates to the external `spherex-irsa-access` skill (not edited from here).
- [ ] Add a page for the full-sample pipeline once it exists; keep one page per reader question.

## note-style conversion (2026-11-14)

- [x] Adopt the `note-style` skill for Claude Code (symlink in `~/.claude/skills/`), copy its rule book to
      `docs/html_documentation_guide.md`, and make note-style the only documentation standard in `CLAUDE.md`.
- [x] Convert the site to Sphinx + MyST + customised Furo: starter assets and bundled MathJax copied, Material
      syntax (admonitions, figure blocks, grid cards) translated, toctrees with short titles, strict build clean.
- [x] Untrack the two Explanatory Supplement PDFs that the folder move had let into git (they stay on disk).
- [x] Fonts: Source Sans 3 and Source Code Pro self-hosted (skill starter and project); index cards with
      sphinx-design; SQL blocks highlighted with the `postgresql` lexer (rule book 0.4). Card grids made
      part of the standard with the title as a larger link-coloured heading (rule book 0.5, 2026-11-15).
- [ ] Check the light-mode switch, saved preference and Firefox/Safari rendering on the deployed site.
- [ ] The two PDFs remain in the pushed history of `main` (60 MB); decide whether to rewrite history or accept.

### Review

The conversion kept every page, figure, footnote and link (the strict build with `nitpicky` verifies them);
the only content changes are four two-image figures split into pairs and one SQL block typed as text.

## Publication scope and links (2026-11-15)

- [x] Internal pages (specification, to do, lessons, SED demo task, rule-book copy, photometry study note)
      excluded from the public site and built separately for review (`-t internal`, `docs/_build/internal`).
- [x] Public pages no longer link to internal ones (primer, index, SED page and report reworded).
- [x] Printed web addresses in published pages replaced by descriptive hyperlinks.
- [x] Third-party tool notes and review, and the SED demo and H-minus reports, made internal (owner's
      decision 2026-11-15); local paths in public pages accepted for now.
- [x] Aligned with note-style 0.6: shared CSS (table wrapping, responsive images, card-link-text reset),
      font provenance notice, rule-book copy, locked fresh build as the gate; redundant project CSS removed.

## Review of the student's SDSS 48k photometry (2026-11-15, feature/sdss48k-review)

- [x] Read the run's README, the production script and talltable's `optimal_extract` (read only).
- [x] Catalogue and coverage summary; same-exposure comparison with the six demo galaxies; sample-wide
      clipping failures; repeatability of close-wavelength pairs; figures 1-3; internal report
      `docs/reports/sdss48k_photometry_review.md`.
- [x] H-minus bump index (Hbump_opt) for 46,504 galaxies from the aperture fluxes, with the solid-angle
      correction; against Dn4000, HdeltaA and the H-bump paper's models; figures 4-6; report section 8.
- [ ] Bump of quiescent and post-starburst galaxies at fixed D4000 (MPA-JHU emission lines to separate them).
- [ ] Settle the 0.004-0.005 mag redshift trend of the index (sampling estimator, aperture size).
- [ ] Owner's decision: use the aperture flux with corrections (aperture correction from optical shape,
      neighbour flag, outlier rejection, error scaling), or re-measure with forced Sersic photometry.
- [ ] Ask the student to push the `sdss48k/` run folder; ask whether aperture-flagged pixel counts and
      sub-pixel positions can be stored.

### Review

The run's bookkeeping (targets, footprints, wavelengths, calibration) agrees with ours; its PSF flux is not
usable for these galaxies, as the photometry study predicted; its aperture flux repeats to 3-5 % in D1-D4 but
is not a total flux and has unsubtracted neighbours and bad-pixel outliers.
