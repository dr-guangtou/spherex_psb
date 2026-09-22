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

## Task 2 (next): sample and coverage

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
