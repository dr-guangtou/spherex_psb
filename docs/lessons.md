# Lessons

Record mistakes, surprises, and the rationale behind decisions. Read at session start.

## 2026-09-22 SPHEREx learning session

Process lessons
- The `spherex-irsa-access` skill (v1.0.0, dated 2026-03-30) was wrong or silent on: the
  QR3 release and `spherex_qr3*` collections, the R7 pipeline, the EPSF binary-table
  extension replacing the PSF cube, the new flag bits (CROSSTALK, STREAK, BLOOM, SNOWBALL,
  HALO, SATELLITE_HALO), the header keyword scheme for flags, the Spectrophotometry and
  Mosaic tools, the S3 `qr3/` tree, and the retirement of QR1. Skills about live archives
  rot within months; always re-verify collection names, versions and extension layouts
  against the archive before trusting a skill.
- The archive documentation site (caltech-ipac.github.io/spherex-archive-documentation)
  is three pages dated 2026-02-18 and lags the Explanatory Supplement (v2.0, 2026-08-25)
  by two releases. The Supplement PDF and the IRSA online help pages are the primary
  sources; the Data Explorer and VO API index are JavaScript apps that curl cannot read.
- Reading twelve long sources in parallel with one subagent per source and a fixed note
  template worked well; the synthesis still required live checks because the sources
  disagreed on time-sensitive facts (e.g. whether QR3 was already served).
- TAP queries on `spherex.obscore` without a spatial constraint (`ORDER BY t_min` or
  `GROUP BY obs_collection` over the whole table) take minutes or time out; constrain by
  `CONTAINS(POINT, p.poly)` or by `obs_id`/`t_min` ranges first.

Data lessons (verified live)
- `IMAGE` is not zodi-subtracted; `ZODI` is a rescaled Kelsall model (ZODIMDL =
  KEL98_WAVESCL_V1). The IRSA Spectrophotometry Tool ignores ZODI and fits a local
  background; the Mosaic Tool subtracts IMAGE - ZODI.
- QR2 (VERSION 6.x) FLAGS headers name bits with `MP_<NAME>`; QR3 (VERSION 7.x) uses
  `MSKN####/MSKM####/MSKD####` and omits unused planes. The official Source Discovery
  notebook's `MP_*` parsing breaks on QR3. Hard-code the canonical flag table.
- QR2 files carry a `PSF` image cube (121 x 101 x 101, 10x oversampled); QR3 files carry
  an `EPSF` binary table (451 rows for D3, 441 otherwise; 33 x 33 at 5x). Code must
  branch on VERSION.
- `PSF_FWHM` in the header is a per-image median in arcsec and differs systematically
  between the QR2 optical PSF (5.2 arcsec in one D3 file) and the QR3 ePSF (7.4 arcsec in
  one D3 file). Use NEFF_MEAN from the ePSF table, not FWHM, for aperture decisions.
- On 2026-09-22 the `spherex_qr3` collection contains only 2026W30 to 2026W32
  (2026-07-20 to 2026-08-10); the May 16 to July 19 2026 Survey 3/4 data are still in
  `spherex_qr2` with VERSION 6.5.7 until DR1.
- R7 headers add `HE_AIRGLOW_CONT`, `AURORA_CONT`, `SHUTTLE_GLOW_CONT` booleans and the
  corresponding correlation coefficients; QR2 headers lack them.
- The `spherex_qr2_cal` SIA collection documented on the archive site is not returned by
  `Irsa.list_collections(servicetype='SIA', filter='spherex')`.
- Cutout URLs accept both `center=RA,DEC` and `center=RA,DECd`; the PSF/EPSF extension is
  copied whole into cutouts, so zone selection must use parent-frame coordinates via
  CRPIX1A/CRPIX2A.

## 2026-09-23 software review

- Third-party SPHEREx tools written before July 2026 are all hard-coded to the QR2 data
  model (PSF cube, MP_* flag names, seven extensions). Any tool must be checked against a
  QR3 file before use; only hbahk/spherex-retrieval and hbahk/tractorjax-spherex dispatch
  on the PSF kind.
- The public Caltech-IPAC/spherex-pipelines snapshot (6.5.5) is the ground truth for the
  IRSA tool's algorithm, but its tasks need the Rubin Butler middleware; only spx_data and
  spx_utils are usable standalone. Read the task code as a specification.
- Check licenses before copying: four of the reviewed repos have no license and one is
  GPL-3.
- A personal repo by an SSDC member (SPHERExSpecPhot) is not evidence of official status;
  it is a simple aperture tool unrelated to the IRSA Spectrophotometry Tool.

## 2026-11-13 SED demo, checkpoint A

- The exposure-level `HE_AIRGLOW_CONT` keyword is True for every D1 and D2 exposure (it marks the detectors
  the He I 1.083 um line can reach, not the exposures it affects), so it cannot screen exposures. A background
  basis quadratic in the per-pixel CWAVE across the cutout does the job: on the 1.097 um exposure of the
  reference galaxy it lowers chi2/dof (near) from 8.9 to 1.8-2.3 and the whole-cutout chi2/dof from 114 to
  1.7, and changes the galaxy flux by -5 % (1.097 um) and +9 % (1.060 um). A plane in x, y does not help
  (the airglow band follows the LVF iso-wavelength curves). Decide the default background model from the
  full-sample comparison, not from one exposure.
- Adjacent nominal spectral channels overlap by up to 0.018 um (Spectral Channels product); binning by
  "CWAVE within [WL_MIN, WL_MAX]" puts one exposure into two channels. Assign each exposure to the nearest
  channel centre of its detector.
- spherex-retrieval stops each cutout download after the EPSF header and attaches the calibration ePSF,
  so a 41 x 41 pixel bundle with CWAVE/CBAND/SAPM is 0.2 MB on disk (36 cutouts: 7.4 MB, 157 s at two
  workers); the per-detector calibration cache is 445 MB once. The 10 GB budget is not a constraint;
  IRSA request rate is (about 4.4 s per cutout).
- IRSA TAP footprint queries slow from ~5 s to ~30 s each when several of my own jobs query IRSA
  concurrently; serialise archive queries.
- Python prints to a redirected log are block-buffered: use `flush=True` (or `python -u`) for long jobs,
  or the log stays empty until the end.
- Legacy Survey DR10 forced WISE photometry (Tractor model) agrees with the SPHEREx model flux of the
  reference galaxy at W1/W2 within a few per cent, while AllWISE profile-fit magnitudes are 35-40 % low and
  2MASS XSC "total" magnitudes 15-20 % low: compare like with like (model-based total fluxes).

## 2026-11-13 SED demo, checkpoint B

- The Sersic renderer point-sampled the profile 4 x 4 times per oversampled (1.23") pixel outside an
  analytic core of half a pitch. For n = 4 cusps this lost up to 2.3 % of the flux (R_e = 1", the compact
  galaxy), and the loss changed with the orientation of the cutout grid, so it also inflated the exposure-to-
  exposure scatter of the de Vaucouleurs galaxies. Found only through the cross-code check (ours / tractorjax
  was 1.06-1.08 for n = 4 against 1.015 for n = 1). Fix: a 7 x 7 oversampled-pixel core block sampled 32 x 32
  (every tested shape within 0.2 % of a 64 x 64 brute-force reference; 30 ms per template, unchanged).
  Lesson: validate a renderer's integrated flux against a brute-force reference for every profile class
  before trusting absolute fluxes; an injection test with the same renderer cannot see this.
- tractor (and tractor-jax, and therefore the Legacy Survey catalogues) normalises the Hogg & Lang
  mixture-of-Gaussians amplitudes to unit sum, although the mixture only matches the profile out to ~8 R_e
  (deV) or ~4 R_e (exp). An analytic Sersic total is therefore 1/0.943 = 1.060 (deV) and 1/0.991 (exp) times
  the tractor "total" for the same image; SDSS deV model magnitudes are truncated at 7 R_e as well. State
  which total is meant when comparing fluxes between codes and catalogues.
- The run-log filter `grep -v "^  "` (meant for astropy warning continuation lines) also removed every
  indented line of the printed tables and JSON summaries. Filter on the warning text, never on indentation.
- IRSA TAP returned 502/503 for about an hour, Data Lab TAP returned a non-VOTable page once, and one
  spherex-retrieval download hung for three hours with no open connection. Every network step needs a
  timeout and a retry, and an unattended driver must continue with the next galaxy after a failure
  (scripts/sed_demo/run_remaining.py).
- The detector-boundary test around D3/D4 (2.42 um) is not a pure calibration test for 0.03 < z < 0.06
  galaxies: the CO bandhead (2.29 um rest) falls at 2.37-2.43 um observed, inside the 0.2 um window, and a
  quadratic in log flux cannot absorb an edge. Stars fitted jointly in the same cutouts give the
  calibration-only step (per-source fluxes are now stored in the records for this).
- The QA stamps (figure 2) were taken from the first cutout file per detector in alphabetical order, which
  for two galaxies was an exposure later screened out (a satellite streak; a D6 frame with a bad fit). Pick
  the exposure whose chi2/dof is closest to the detector median after screening, so that the figure shows a
  typical fit (`measure_galaxy.py --stamps-only` rebuilds the stamps from the records).
- A stamp display stretch from percentiles of all pixels is set by masked hot pixels; take the percentiles
  of the unmasked pixels only.
- The task spec `docs/reports/sed_demo_task.md` was moved into `docs/` at the start of the session but never
  committed, and it was gone from the working tree at the end (an untracked copy had reappeared at the
  repository root, probably through Dropbox sync). Commit the task spec with the first checkpoint; an
  untracked file in a Dropbox-synced repository is not safe.
- Comparing SPHEREx synthetic fluxes with external catalogues only works like with like: SDSS z model
  fluxes agree within 5 % (0.95-1.08), Legacy Survey forced W1 within 10 % (1.07-1.11, which includes the
  1.06 factor between an analytic Sersic total and the tractor mixture total for n = 4), 2MASS XSC "total"
  magnitudes are 0-50 % low for the fainter galaxies, and AllWISE profile-fit and elliptical magnitudes are
  30-70 % low. Treat 2MASS XSC and AllWISE as lower limits for extended galaxies.

## H-minus bump feasibility (2026-11-14)

- "Spectral resolution" was the wrong worry for a 0.3 um wide continuum feature: degrading FSPS spectra
  from R = 100 to the SPHEREx R = 41.4 (Gaussian or top-hat of equivalent width lambda / R) changes
  Hbump_opt by < 0.002 mag over the whole SSP grid. The real limits are the number of exposures inside the
  0.045 um sidebands (2-7 per galaxy today, 0.011-0.020 mag bootstrap error) and the D2/D3 detector
  boundary, which sits inside the index windows for every galaxy at z < 0.096 and converts a 1 % detector
  step into 0.003-0.007 mag of index. Check where detector boundaries fall in the rest frame before
  defining any index for SPHEREx.
- Band means over irregularly sampled exposures are biased (up to 0.008 mag here) when the exposures
  cluster at one end of a window; a forward-model fit over all exposures is the right estimator for
  SPHEREx indices.
- A loop variable named like a function argument (`name`) silently relabelled a whole output table;
  ruff does not catch shadowing. Use distinct names in loops that build records.
- The SPHEREx response-profile shape (Hui et al. 2026) is not tabulated in the paper; R is defined with
  the equivalent width of the normalised response, not the FWHM. When only R is known, test both a
  Gaussian and a top-hat of the same equivalent width and report the difference.

## Documentation site (2026-11-14)

- A 600-line monolithic guide was the wrong shape for a growing knowledge base: it mixed instrument facts,
  archive state, pitfalls and project results, and could not be read by topic. Splitting it into pages by
  reader question (what is the instrument, how do I get data, what must I handle in the data, what did we
  measure) with cited footnotes and credited figures took one session; keep that structure and add a page
  per new topic rather than a section to an old one.
- Figures from arXiv e-print tarballs are the original files (PNG/PDF) and carry no watermark; download
  them to the data area, convert with pdftoppm, downscale with sips, and keep only the chosen ones in the
  repository with a credit line. A paper that is served as PDF only (no source) can still yield figures
  by rendering the page at 200 dpi and cropping.
- zsh does not word-split unquoted variables: `for f in $FILES` runs once with the whole list. Pipe
  `grep -l` into `while read -r f` instead. A patch script that asserts every replacement before writing
  is the right discipline, but after `ruff format` has rewrapped a file the asserted strings no longer
  match; re-read the file before patching it.
- The SAPM calibration files name their detector in the IMAGE extension header (DETECTOR as a string),
  not in the primary header; the CWAVE files do not name it at all and must be identified by their
  wavelength range.
- Measured while making the site figures: the ZODI model under-predicts the local background by 4-12 % at
  ecliptic latitudes below 10 deg and by 11-34 % at 24-46 deg (16th-84th percentiles of the fitted residual
  over ZODI); the SOURCE flag covers 31-53 % of the pixels in a 41 x 41 cutout around a bright galaxy; HALO
  and OUTLIER each flag 1.3-2.1 % of pixels and DICHROIC 2.6-2.8 % of D3/D4 pixels.

## note-style conversion (2026-11-14)

- A `.gitignore` pattern names a path: when a folder is moved (`docs/reference_notes/external/` to
  `docs/references/sources/external/`), the pattern must move with it, or the next `git add` commits what
  it used to exclude. Two 30 MB PDFs reached GitHub this way; check `git ls-files` sizes after any move.
- Sphinx only reports a warning when it re-reads the source, so a strict build that "passes" after an
  incremental run proves nothing; use `-E` (fresh environment) for the build that gates a commit.
- Pygments treats `{ra}` placeholders inside a `sql` fence as an error and Sphinx turns that into a warning
  under `-W`; type such templates as `text`.
- Furo sets `overflow-wrap: break-word` on the article, so table cells in a narrow column split words
  ("Us ed"); and a MyST `:width:` is an absolute width, so an 820 px figure overflows a 390 px screen.
  Both are fixed in the project stylesheet, not in the shared note-style files.
- Side-by-side image pairs have no MyST figure equivalent; two consecutive figures with their own credit
  lines read better on narrow screens anyway.
- A font that is only named in a CSS stack is not a font choice: the note-style starter named Source Sans 3
  without shipping it, so macOS rendered the pages in PingFang. The old site looked better because Material
  loaded Source Sans 3 and Source Code Pro from Google Fonts; they are now bundled (316 KB of WOFF2) in
  the skill and the project, which also removes the third-party request.
- Pygments' generic `sql` lexer rejects `{ra}` placeholders; the `postgresql` lexer accepts them, so SQL
  blocks keep their highlighting without relaxing `-W`.
- On this machine `rm` and `cp` are aliased (trash and interactive copy); inside `&&` chains use
  `/bin/rm` and `/bin/cp -f`, otherwise the chain stops silently at an "overwrite?" prompt.
