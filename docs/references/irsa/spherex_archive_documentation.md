# SPHEREx archive documentation site (surveyed 2026-09-22)

Scope note: the site at `https://caltech-ipac.github.io/spherex-archive-documentation/` is a **very small, 3-page MyST/mystmd book** (theme: `book-theme`). It is deliberately a thin "User Guide" that itself defers almost all quantitative technical detail (FLAGS bit table, catalogs, systematics, mosaics, absolute-calibration accuracy, acknowledgment text) to one external PDF, the **SPHEREx Explanatory Supplement**, linked from every page: `https://irsa.ipac.caltech.edu/data/SPHEREx/docs/SPHEREx_Expsupp_QR.pdf`. To fulfil the requested section list I fetched that PDF too (it is the official, IRSA-hosted primary reference the site itself points to) and I also fetched two directly-linked official IRSA pages (`psfhdrerr.html`, `cloud_access`). Everything below is tagged by source:
- **[SITE]** = one of the 3 pages of the documentation site itself.
- **[ExpSupp vX.Y]** = the linked SPHEREx Explanatory Supplement PDF (I fetched the copy live at the URL above on 2026-09-22; its internal version/date metadata says **Version 2.0, 2026-08-25**, "document generated on September 2, 2026 from commit v1.0 of 2025-07-02").
- **[IRSA:psfhdrerr]** / **[IRSA:cloud_access]** = other official IRSA pages linked directly from the site.

This means the Explanatory Supplement I read is noticeably **newer** than the documentation site (site: dated 2026-02-18, last GitHub commit 2026-05-08) — the PDF has already been updated through pipeline version R7 / DR1 planning, which the site text does not mention at all. This version skew is itself an important finding (see "Items that look new" and "Open questions" below).

## Site map (every page URL with one-line description)

Confirmed complete via `sitemap.xml` (`https://caltech-ipac.github.io/spherex-archive-documentation/sitemap.xml`) and the `toc:` list in `myst.yml` (source: `github.com/Caltech-IPAC/spherex-archive-documentation`, file `myst.yml`) — there are **exactly three content pages**, no additional subpages, no search/genindex pages, no versioned URL variants:

1. `https://caltech-ipac.github.io/spherex-archive-documentation/` (source: `documentation/index.md`) — "SPHEREx Archive at IRSA User Guide": document purpose/scope, one-paragraph mission overview, links to the archive, project website, and Explanatory Supplement.
2. `https://caltech-ipac.github.io/spherex-archive-documentation/spherex-data-access` (source: `documentation/spherex_data_access.md`) — "SPHEREx Data Access": browsable directories, SIA2 API, cutout service, PyVO/Astroquery, SPHEREx Data Explorer GUI.
3. `https://caltech-ipac.github.io/spherex-archive-documentation/spherex-data-products` (source: `documentation/spherex_data_products.md`) — "SPHEREx Data Products at IRSA": Level 2 Spectral Image MEF description, cutout PSF-selection recipe, and all calibration/ancillary product filename conventions.

Site metadata (`myst.yml`): title "SPHEREx Archive at IRSA", author "Caltech/IPAC-IRSA", `date: 2026-02-18`, license `BSD-3-Clause`, GitHub repo `https://github.com/Caltech-IPAC/spherex-archive-documentation`. Rendered HTML confirms a BSD-3-Clause "content license" badge on every page (this is a license for the *documentation text*, not a data-citation policy). Git history (via GitHub API) shows the repo's most recent commits are, in order: "Add column names and links to cloud_access examples" and "Add curl example" (2026-04-13), "Add warning about PSF error" (2026-04-13), "Clarify 0- vs 1-based indexing" (2026-04-08), "Remove references to QR1" (2026-02-18), "Adding licence to the rendered pages" (2026-02-17), up through "Fix up version number" / "FIX: passing through BASE_URL" (2026-05-06 to 2026-05-08, the latest commit as of this survey).

No 404s were encountered on any of the 3 site pages.

## Mission and survey overview as described

**[SITE]** (`index.md`): SPHEREx is "a NASA Astrophysics Medium Explorer mission that launched in March 2025." Planned **two-year mission**, obtaining **0.75–5 micron spectroscopy over the entire sky**, "with deeper data in the SPHEREx Deep Fields." IRSA began releasing SPHEREx Spectral Image data weekly in **July 2025**. Science goals as listed verbatim: (1) "constrain the physics of inflation by measuring its imprints on the three-dimensional large-scale distribution of matter," (2) "trace the history of galactic light production through a deep multi-band measurement of large-scale clustering," (3) "investigate the abundance and composition of water and biogenic ices in the early phases of star and planetary disk formation." The site explicitly says more detail is in the "Mission Overview" section of the Explanatory Supplement, and does not itself give pixel scale, FoV, resolution, or cadence numbers.

**[ExpSupp v2.0]** fills in the numbers the site omits:
- Focal plane: two Focal Plane Assemblies (FPAs), each with three Teledyne **H2RG HgCdTe 2k×2k** detector arrays, split by a dichroic beam splitter. **SWIR FPA**: 0.75–2.44 µm (in reflection), operates at **62 K**. **MWIR FPA**: 2.40–5.01 µm (in transmission), operates at **45 K**. Each detector sits behind a Linear Variable Filter (LVF) so each pixel samples a narrow, position-dependent bandpass; full spectra are built up from multiple exposures/pointings.
- 6 spectral bands and resolving powers (same table reproduced in Level 2 product section below): Band 1 R≈39, Band 2 R≈41, Band 3 R≈41, Band 4 R≈35, Band 5 R≈112, Band 6 R≈128.
- Pixel scale: **≈6.15 arcsec/pixel** (stated as "1 px ∼ 6.15″" in the astrometry-distortion discussion; consistent with the PSF calibration product statement that its 10× oversampled pixels correspond to a spectral-image pixel of 0.615 arcsec, i.e. 10 × 0.615″ = 6.15″).
- Example PSF FWHM value quoted in a sample header: `PSF_FWHM 8.672612363488842 arcsec` (median).
- Survey strategy: a Survey Planning Software (SPS) plans observations on the fly (not a fixed repeating scan). A "target group" = 17 pointings at the same ecliptic longitude, spaced by one spectral-channel width in ecliptic latitude; a full target group gives full coverage in one spectral channel; target groups are tiled in latitude rings around the whole sky, with overlap for redundancy. Position angle alternates 0°/180° between ascending/descending orbit halves for solar-panel illumination, and this **defines the four "Surveys"**: Survey 1 = first 12.5 months, PA=0°; Survey 2 = first 12.5 months, PA=180°; Survey 3 = second 12.5 months, PA=0°; Survey 4 = second 12.5 months, PA=180°. Surveys 3/4 are shifted by half a spectral channel relative to 1/2 to Nyquist-sample the spectra. Total planned mission accumulation: **≈5×10¹² spatial-spectral elements**.
- Deep Survey: two Deep Fields, one at the north ecliptic pole, one near (but offset from) the south ecliptic pole to avoid foregrounds/bright stars; a highly overlapping repeated-tiling pattern (not the same target-group geometry as the All-Sky Survey) to build up depth for the galaxy-formation/EBL science case.

## Data releases (names, dates, versions, differences, retired releases, DOIs)

**[SITE]** (`spherex-data-products.md`, `spherex-data-access.md`): only two releases are ever mentioned on the site itself:
- **QR1 (Quick Release 1)**: weekly releases beginning **July 2025**. Site text as of the current (2026-05-08 commit) version has had explicit QR1 references *removed* ("Remove references to QR1" commit, 2026-02-18), i.e. the current site text no longer describes QR1 in detail, it is only implied as the earlier/retired release that QR2 supersedes.
- **QR2 (Quick Release 2)**: "distribution started October 2025 with improved calibrations; supersedes QR1 and includes reprocessed data from mission start." QR2 is what the site's directory layout, SIA2 collections (`spherex_qr2`, `spherex_qr2_deep`, `spherex_qr2_cal`), and on-prem root path (`.../qr2`) all refer to. No explicit DOI is given anywhere on the site for QR1 or QR2 data products themselves.

**[ExpSupp v2.0]** gives a fuller, and notably more current, release roadmap **not present on the site**:
- QR2 corresponds to pipeline versions **6.4 through 6.5.6**; QR1 and QR2 file lists differ and users are explicitly told "science users should NOT combine files from the two releases."
- **DR1 (Data Release 1)** = the Year 1 reprocessing (Survey 1 + Survey 2), using a major pipeline update, versions **R7.0 and up** (also referred to as "pipeline version R7").
- **QR3** = Survey 3 and Survey 4 data processed with the same R7 pipeline; "the first several weeks of survey 3 and 4 data (May 16, 2026 to July 19, 2026) were initially processed with pipeline version 6.5.6 and the QR3/R7 versions will be released in the archive with the DR1 data in **late fall 2026**." Users are advised: "we advise caution when combining QR2 and QR3 data" (different calibrations).
- **DR2 (Data Release 2)** = the Year 2 reprocessing (Survey 1 through Survey 4), planned after Year 2 completes.
- Processing/release cadence: calibrated spectral images are produced within days of acquisition and available at IRSA **within 60 days of observation**; full reprocessing happens after Year 1 and Year 2.
- Document revision history (from ExpSupp change log) shows the pipeline evolving weekly/monthly: v1.0 (2025-07-02, QR release), v1.3 (2025-10-13, QR2), v1.4 (2026-01-23, pipeline 6.5), v1.5 (2026-03-30, pipeline 6.5.6, PSF header fix), v1.6 (2026-05-06, new Mosaics section/Mosaic Tool), **v2.0 (2026-08-25, major R7/DR1 update)**.
- No data-product DOI is given anywhere I could verify (neither on the site nor in the Explanatory Supplement text I searched); the only DOIs present in the ExpSupp are bibliographic (journal-article) DOIs in its reference list, e.g. the SPHEREx mission paper (Korngut et al., *ApJ*, 999(1):139, March 2026, doi:10.3847/...).

## Level 2 spectral image product (complete description)

**[SITE]**, `spherex-data-products.md`, "Main Science Data Product: Spectral Image Multi-Extension FITS Files (MEF)" — this is the section that is closest to verbatim on the actual site itself (little PDF supplementation needed except the FLAGS table):

- One Spectral MEF per detector per sky pointing → **6 MEFs per pointing** (1 per detector, detectors numbered 1–6). Because per-band data-quality assessments can fail, "some observations will not include all 6 bands in the archive." File size ≈70 MB.
- **Filename format**: `level2_[Observation ID]D[Detector]_spx_l2b_v[Version]_[Processing Date].fits`, e.g. `level2_2025W18_2B_0001_1D1_spx_l2b-v12-2025-164.fits`.
- Filenaming vocabulary (site definitions): `Planning Period` = the ~3.5-day survey-plan block uploaded to the spacecraft, e.g. `2025W18_2B`. `Observation ID` = planning period + large-slew counter (e.g. `0001`) + small-slew counter (1–4, since each large slew has ≤4 small slews). `Detector` = integer 1–6. `Version` = pipeline/file version string (e.g. `l2`). `Processing Date` = year + day-of-year, e.g. `2025-164`.

**6 spectral bands** (units µm, resolving power R as stated on the site):
| Band | λ range (µm) | R |
|---|---|---|
| 1 | 0.75 – 1.09 | 39 |
| 2 | 1.10 – 1.62 | 41 |
| 3 | 1.63 – 2.41 | 41 |
| 4 | 2.42 – 3.82 | 35 |
| 5 | 3.83 – 4.41 | 112 |
| 6 | 4.42 – 5.00 | 128 |

**MEF extensions (HDUs), all image extensions are 2040 × 2040 unless noted**:
- **HDU 1 — IMAGE**: "Calibrated surface brightness flux density in units of MJy/sr." **No zodiacal-light subtraction is applied.**
- **HDU 2 — FLAGS**: "Bitmap of per-pixel status and processing flags." Site text says definitions are "provided in Table 10 of the SPHEREx Explanatory Supplement" — **this table is not reproduced on the site itself**. I located it in the live ExpSupp PDF, where (as of Version 2.0, 2026-08-25) it is numbered **Table 16**, "Image pixel flags used in spectral images at Level 2" (the site's citation to "Table 10" is stale relative to the current PDF numbering — see "Open questions"). Verbatim bit table, reproduced from the ExpSupp:

  | Symbolic name | Bit # | Description | Note |
  |---|---|---|---|
  | `TRANSIENT` | 0 | Transient (e.g. cosmic-ray hit) detected during SUR. Transients in the first 10 s of exposure may not be flagged. Can also indicate charge spillover (bloom) from very bright neighboring sources. | Determined onboard (Level 0) |
  | `OVERFLOW` | 1 | Overflow threshold reached during SUR; threshold ≈ half of full-well saturation. | |
  | `SUR_ERROR` | 2 | `chksum_error` bit from onboard processing; alone = data-handling error in onboard SUR algorithm. Combined with `TRANSIENT`/`OVERFLOW` signals early transient (first half of exposure) or early overflow (first ~5 s). | |
  | `NONFUNC` | 6 | Static pre-flight assessment: pixel permanently unusable/dead. May be updated during mission. Unusable for any purpose. | Static |
  | `DICHROIC` | 7 | "Dark corner" pixels of Bands 3/4 where the "smile" effect gives incompatible bandpass for that side of the dichroic; low expected throughput, not usefully calibratable/photometric. | |
  | `MISSING_DATA` | 9 | Onboard data lost before ingest at SSDC (e.g. corrupted/non-retransmitted downlink packets); no data available for this pixel. | Set by Level 1 pipeline |
  | `HOT` | 10 | Hot pixel — noisy/spurious signal, determined per exposure; permanently hot pixels are `NONFUNC`. Not usable for science. | |
  | `COLD` | 11 | Unresponsive/anomalously low signal in this exposure; permanently dead pixels are `NONFUNC`. Not usable for science. | |
  | `FULLSAMPLE` | 12 | Pixel in the rotating 8×32 full-readout region (full sample history available). Not usable for science, informational only. | |
  | `PHANMISS` | 14 | Cannot be corrected due to missing phantom pixels. | |
  | `NONLINEAR` | 15 | Reliable nonlinearity correction could not be determined; poor photometric accuracy — exclude from most science. | Set by Level 2 pipeline |
  | `PERSIST` | 17 | Affected by persistent charge above the Level 2 threshold. | |
  | `OUTLIER` | 19 | Flagged by the "Detect Outlier Pixels" module. | |
  | `CROSSTALK` | 20 | Affected by "ordinary" crosstalk. | |
  | `SOURCE` | 21 | Pixel mapped to a known source. | |
  | `GHOST` | 22 | Affected by an optical ghost from a bright source inside the exposure frame. | |
  | `GHOST_FPA` | 23 | Affected by an optical ghost from a bright source on another detector in the FPA. Currently unused (subsumed into `GHOST_EXT`); will be removed in Year 2 processing. | |
  | `GHOST_EXT` | 24 | Affected by an optical ghost from a bright source outside the field of view. Currently in development. | |
  | `STREAK` | 25 | Affected by a streak (presumably an Earth-orbit object). | |
  | `BLOOM` | 26 | Affected by source blooming. | |
  | `SNOWBALL` | 27 | Affected by a "snowball" event (very large charge release). | |
  | `HALO` | 28 | Affected by the halo of a transient; caution recommended in science use. | |
  | `SATELLITE_HALO` | 29 | Affected by the halo of a satellite streak; not recommended for science use. | |

  Bits 3, 4, 5, 8, 13, 16, 18 are not defined in the table as extracted (may be reserved/unused).

- **HDU 3 — VARIANCE**: "Variance of calibrated surface brightness flux in units of (MJy/sr)^2." **[ExpSupp]** adds: derived per-pixel from the downlinked ramp/flux images using the statistical framework of Robberto (2007) for non-destructive-readout infrared detectors; combines Poisson + electronic-noise contributions; propagated through subsequent calibration steps as those are applied.
- **HDU 4 — ZODI**: "Modeled zodiacal light background flux in units of MJy/sr." "This has not been subtracted from the IMAGE extension." **[ExpSupp §3.2.11]**: this is a **median estimate of the Zodiacal Light (ZL) spectrum**, built from a modified Kelsall et al. (1998) model (updated with Planck data) combined with Tsumura et al. (2013) spectral measurements (see Crill et al. 2025), then rescaled by a **per-wavelength scaling factor** derived by cross-correlating the model against actual SPHEREx Year-1 high-Galactic-latitude (|b|>30°) exposures (because the raw Kelsall model was found to correctly track ZL spatial/temporal variation but **underestimate its amplitude**). The scaling factor itself is distributed as a separate calibration file ("zodi scaling", named `zodi_scaling_D[n]...`, one per band).
- **HDU 5 — PSF**: "121 Point-spread functions (PSFs); each PSF is represented as a 101 x 101 image and all 121 are assembled together into a cube." **Warning (verbatim, [SITE]):** "SPHEREx Quick Release data products released before March 31, 2026 contained an error in the header description of the PSF" — see the dedicated PSF-error subsection below.
- **HDU 6 — WCS-WAVE**: Spectral WCS FITS lookup table mapping pixel coordinates to central wavelength + bandwidth. Structure: **1 row, 3 columns (X, Y, VALUES)**; X and Y are arrays of grid control-point coordinates in spectral-image pixel space; VALUES is an array of two-element `[central wavelength, bandwidth]` pairs at each control point. Site note (verbatim): "Adopted to support the unique nature of the SPHEREx LVF filters, this rarely-used part of the FITS standard has yet to be implemented by all readers." If a FITS client doesn't parse it, users are told to bilinearly interpolate among the four nearest control points, "accurate to within approximately 1 nm." **Explicit guidance: "For science analysis, use the CWAVE and CBAND extensions in the Spectral WCS calibration product [not WCS-WAVE], the fidelity of the WCS-WAVE lookup table is intended for visualization purposes."**

### Spectral Image MEF cutouts (`products-spectral-image-cutouts`)

**[SITE]**: The IRSA Cutout Service returns cutout MEFs with the same 6 HDUs. `IMAGE`, `FLAGS`, `VARIANCE`, `ZODI` are trimmed to the cutout footprint; `WCS-WAVE` is re-mapped for the cutout; **`PSF` is copied unmodified from the parent full-frame image** (i.e. you must map cutout pixel coordinates back to the parent frame yourself to pick the right PSF plane). Steps (verbatim procedure):
1. Get 0-based pixel coords of the position of interest in the cutout `IMAGE` HDU (e.g. via Astropy `world_to_pixel()`, which returns 0-based).
2. Convert to 0-based coordinates in the *original* Spectral Image using header keywords `CRPIX1A`/`CRPIX2A` (1-based FITS convention):
   ```
   xpix_orig = 1 + xpix_cutout - CRPIX1A
   ypix_orig = 1 + ypix_cutout - CRPIX2A
   ```
3. Identify the PSF cube plane by comparing `(xpix_orig, ypix_orig)` against the PSF-HDU header keywords `XCTR_i`/`YCTR_i` for `i = 1…121` (these are 0-based pixel coordinates in the original image). Find the nearest `i`; the correct cube plane is index **`i − 1`** (because the keyword suffix is 1-based but the FITS cube array is 0-indexed).

Explicit note on the 1-based vs. 0-based mismatch: "SPHEREx FITS header keywords follow the FITS 1-based pixel convention (first pixel = 1), while Python tools such as Astropy return 0-based pixel coordinates (first pixel = 0)."
Tutorial: "Understanding and Extracting the PSF Extension in a SPHEREx Cutout" at `https://caltech-ipac.github.io/irsa-tutorials/spherex-psf/` (not fetched — third-party tutorial repo, out of scope per task instructions, but the URL is given verbatim by the site).

### PSF header error / "psffix" ([SITE] + [IRSA:psfhdrerr] + [ExpSupp])

Full, exact description from `https://irsa.ipac.caltech.edu/data/SPHEREx/docs/psfhdrerr.html` (linked directly from the site, official IRSA page):
- **Nature of the bug**: the PSF cube's 121 planes (an 11×11 grid of detector zones) are *stored* in order of increasing **x**-index, but the FITS header incorrectly claims they are stored in order of increasing **y**-index. Correct mapping for zero-indexed grid coords (x, y), grid origin (0,0) at the bottom-left corner containing FITS pixel (1,1): `i_plane = y × n_cols + x + 1`. The **incorrect** (buggy) header-implied mapping was `i_plane = x × n_cols + y + 1`.
- **Impact**: software that trusts the header to pick a PSF plane for a given detector location may retrieve the wrong plane. Impact scales with source location and how much the PSF varies across the detector; **largest in two detector corners**, producing **photometric errors up to ±5%** relative to using the correct PSF. Affects the stand-alone Exposure-Averaged PSF calibration product, the PSF extension embedded in individual Spectral Image MEFs, and results from the SPHEREx Spectrophotometry Tool.
- **Fix and versioning**: corrected **on March 31, 2026**. Spectral image files processed with pipeline versions **6.4 through 6.5.5** that were subsequently corrected can be identified by a `VERSION` header keyword suffix **`+psffix1`**. Files processed with **pipeline version 6.5.6 and later were never affected** (natively correct). Updated stand-alone PSF calibration products are also available at IRSA, **but** the calibration-reference string embedded in the spectral-image FITS headers was **not** retroactively updated (i.e. you cannot rely on that header string alone to tell whether the *linked* PSF calibration product version is post-fix). **[ExpSupp]** additionally states: "this issue does not apply to QR3" (i.e., the R7-pipeline QR3/DR1 products were built with the corrected PSF ordering natively).
- The Python tutorial "Understanding and Extracting the PSF Extension in a SPHEREx Cutout" was updated to (a) check the pipeline version to see if the header needs correcting and (b) provide a function to patch the header locally.
- Illustrative worked example from the page (4×4 sub-grid of the real 11×11 grid): correct plane numbering increases left-to-right then bottom-to-top in x first (1,2,3,4 / 5,6,7,8 / 9,10,11,12 / 13,14,15,16 reading bottom row first), the buggy header-implied numbering instead increases bottom-to-top within each column (1,5,9,13 / 2,6,10,14 / 3,7,11,15 / 4,8,12,16).

## Other products (catalogs / source tables / mosaics / calibration / quick-look)

**[SITE]**, `spherex-data-products.md` — only **calibration and ancillary detector-characterization products** are described on the site (no catalogs, no mosaics, no Level-3/4 products are mentioned there at all). Each is a per-detector product; filenames follow the same `Planning-Period`/`Detector`/`Version`/`Processing-Date` vocabulary defined above.

| Product | Size (per detector) | Dimensions | Units | Filename format | Example |
|---|---|---|---|---|---|
| Absolute Gain Matrix | ~16 MB | 2040×2040 | (MJy/sr)/(e⁻/s) | `abs_gain_matrix_D[Detector]_spx_cal-agm-v[Version]-[Processing Date].fits` | `abs_gain_matrix_D1_spx_cal-agm-v4-2025-161.fits` |
| Exposure-Averaged PSF | ~6 MB | 101×101×121 | dimensionless (10 PSF px = 1 image px = 0.615″) | `average_psf_D[Detector]_spx_cal-psf-v[Version]-[Processing Date].fits` | `average_psf_D1_spx_cal-psf-v4-2025-161.fits` |
| Dark Current | ~16 MB | 2040×2040 | electron/s | `dark_D[Detector]_spx_cal-drk-v[Version]-[Processing Date].fits` | `dark_D1_spx_cal-drk-v4-2025-161.fits` |
| Dichroic mask | ~16 MB | 2040×2040 | 0/1 flag (1 = ≥50% attenuation; only Bands 3 & 4 have nonzero) | `dichroic_D[Detector]_spx_base-[Processing Date].fits` | `dichroic_D1_spx_base-2025-158.fits` |
| Electronic Gain Factors | single YAML | — | 32 gain values/detector + provenance | `gain_factors_spx_base-[Processing Date].yaml` | `gain_factors_spx_base-2025-158.yaml` |
| Nonfunctional Pixels | ~32 MB | 2040×2040 | 0/1 flag (1 = permanently dead) | `nonfunc_D[Detector]_spx_base-[Processing Date].fits` | `nonfunc_D1_spx_base-2025-158.fits` |
| Nonlinearity Parameters | ~79 MB (MEF, 5 ext.) | 2040×2040 each | extensions `Q_nl`, `b1`, `b2`, `b3`, `Qmax` | `nonlinear_pars_D[Detector]_spx_base-[Processing Date].fits` | `nonlinear_pars_D1_spx_base-2025-158.fits` |
| Read Noise Parameters | ~48 MB (MEF, 2 ext.) | 2040×2040 each | electrons; extensions `READNOISE-1`, `READNOISE-2` | `readnoise_pars_D[Detector]_spx_base-[Processing Date].fits` | `readnoise_pars_D1_spx_base-2025-158.fits` |
| Solid Angle Pixel Map | ~16 MB | 2040×2040 | arcsec² | `solid_angle_pixel_map_D[Detector]_spx_cal-sapm-v[Version]-[Processing Date].fits` | `solid_angle_pixel_map_D4_spx_cal-sapm-v2-2025-164.fits` |
| Spectral WCS | ~32 MB (MEF, 3 ext.) | 2040×2040 (CWAVE, CBAND); table 3-col/1-row (WCS-WAVE) | CWAVE = microns; CBAND = microns | `spectral_wcs_D[Detector]_spx_cal-wcs-v[Version]-[Processing Date].fits` | `spectral_wcs_D1_spx_cal-wcs-v4-2025-254.fits` |

For the Spectral WCS product, the site is explicit: **"For science analysis, use the values in the CWAVE and CBAND layers, not the WCS-WAVE which is intended for visualization."** CWAVE = central wavelength (µm) per pixel; CBAND = bandwidth (µm) per pixel; WCS-WAVE = the same 3-column/1-row lookup table as HDU 6 of the Level 2 MEF.

### Products described in the Explanatory Supplement but **absent from the site** (important gap)

These exist as official SPHEREx/IRSA products but are **not mentioned anywhere in the 3-page documentation site** as of this survey (2026-09-22):

- **Data processing-level hierarchy** [ExpSupp]: Level 0 (raw telemetry) → Level 1 (photocurrent, e⁻/s) → **Level 2 (the calibrated Spectral Image MEFs described above; this is what "QR data products" means)** → **Level 3 (forced photometry at predefined reference positions, yielding catalogs)** → Level 4 (future high-level products: galaxy redshifts, ice column densities, deep image mosaics). "The pipeline described in this document includes Levels 1 to 3."
- **Level 3 Forced Photometry catalog** [ExpSupp §on Forced Photometry Module, Table 24]: inputs = spectral images, source list/positions, ePSF model, variance map, pixel solid-angle map, flag map. Algorithm = the **Tractor** software package (`http://thetractor.org`, `https://github.com/dstndstn/tractor`) run in **forced-photometry mode** (source positions fixed, not floated) using maximum-likelihood generative modeling; optionally accepts **intrinsic galaxy morphology** for the generative model (i.e., it is not strictly point-source-only). Output catalog columns (as described, not a literal FITS column list): source ID (from input catalog), measured flux + uncertainty, corresponding wavelength, (i,j) pixel coordinates, fit-quality flags, and a goodness-of-fit metric from the model-vs-data residual. Background handling: a **global spectral background** is computed from non-source, non-bad pixels and removed first; then a **local background** (from a 15×15-pixel region around the cutout, after masking known sources) is fit *simultaneously* with source flux in the Tractor optimization. Flux uncertainty correction: Tractor's statistical uncertainty is inflated in quadrature by a **3% systematic term**, i.e. `σ_reported = sqrt(σ_Tractor² + (0.03·F)²)` — this correction is applied only to catalog-reported uncertainties, not to the image VARIANCE layer itself.
- **Reference Catalog** [ExpSupp]: an internal source list (cross-matched to Gaia/WISE/2MASS) used to drive astrometric calibration, source masking, and (presumably) Level 3 forced photometry; QR2 uses **Reference Catalog v0.73**; sources carry a `spherex_class` bit value (masking applied to sources with `spherex_class` ≤ 7).
- **Mosaic Tool / Spectral Channels product** [ExpSupp §3.4, added in doc v1.6 dated 2026-05-06 — i.e. genuinely new since March 2026]: the IRSA **Mosaic Tool** combines multiple L2 images into a co-added mosaic per spectral channel. Workflow: (1) query/load L2 images covering the target region; (2) **zodi-subtract**: `data = IMAGE − ZODI`; (3) mask bad pixels via FLAGS (specific excluded-flag list: `TRANSIENT, SUR_ERROR, NONFUNC, DICHROIC, MISSING_DATA, HOT, COLD, PHANMISS, NONLINEAR, PERSIST, CROSSTALK, GHOST, GHOST_FPA, GHOST_EXT, STREAK, BLOOM, SNOWBALL, HALO, SATELLITE_HALO`; flags *propagated but not excluded*: `OVERFLOW, SOURCE, OUTLIER`); (4) assign each pixel to 1 of **17 standard spectral sub-channels per detector array** using a pre-defined "spectral channel template" (a 2D integer array, values 1–17 = channel number, 0/18 = outside any standard channel — edges/corners); (5) reproject to a common output grid; (6) accumulate weighted contributions; (7) produce final averaged mosaic. Per-channel statistics (`WAVELENGTH`, `WL_MIN`, `WL_MAX`, `R`, `R_STD`, `BANDWIDTH`) are pre-computed and stored in a `SPECTRAL_CHANNELS` calibration-product extension. **Explicit caveat: "For science applications requiring precision photometry, we recommend using the L2 spectral images directly" (not the mosaics), and "for the initial release of the Mosaic Tool, only L2 images from the All-Sky Survey are included; images from Deep Field Surveys are excluded."**
- The Level 4 tier (galaxy redshifts, ice column densities, deep-field mosaics) is described only as a future/planned product category, not yet delivered.

None of this Level-3/Level-4/Mosaic-Tool material appears on the actual documentation site pages — a PSB-galaxy-spectra user relying only on the 3-page site would not learn that a forced-photometry catalog tool or a mosaic tool exist at all.

## Access methods and services

**[SITE]**, `spherex-data-access.md` — IRSA describes **4 layered access methods**, all reproduced here essentially verbatim:

1. **Browsable directories** (on-prem + AWS mirror). Root: `https://irsa.ipac.caltech.edu/ibe/data/spherex/qr2`. Subdirectory scheme (`[Detector]` = 1–6):
   - Absolute Gain Matrix: `abs_gain_matrix/cal-agm-v[Version]-[Processing Date]/[Detector]/`
   - Exposure-Averaged PSFs: `average_psf/cal-psf-v[Version]-[Processing Date]/[Detector]/`
   - Dark Current: `dark/cal-drk-v[Version]-[Processing Date]/[Detector]/`
   - Dichroic: `dichroic/base-[Processing Date]/[Detector]/`
   - Electronic Gain Factors: `gain_factors/base-[Processing Date]/`
   - Spectral Image MEFs: `level2/[Planning Period]/l2b-v[Version]-[Processing Date]/[Detector]/`
   - Nonfunctional Pixels: `nonfunc/base-[Processing Date]/[Detector]/`
   - Nonlinearity Parameters: `nonlinear_pars/base-[Processing Date]/[Detector]/`
   - Read Noise Parameters: `readnoise_pars/base-[Processing Date]/[Detector]/`
   - Solid Angle Pixel Map: `solid_angle_pixel_map/cal-sapm-v[Version]-[Processing Date]/[Detector]/`
   - Spectral WCS: `spectral_wcs/cal-wcs-v[Version]-[Processing Date]/[Detector]/`

2. **APIs — IVOA SIA2** (Simple Image Access v2, `https://ivoa.net/documents/SIA/20151223/`). Generic endpoint: **`https://irsa.ipac.caltech.edu/SIA?`**. Requires a `COLLECTION` parameter; the 3 SPHEREx collections:
   - `COLLECTION=spherex_qr2` — **Wide (All-Sky) Survey** Spectral Image MEFs ("more uniform coverage across the entire sky", ignores deep-field extra coverage)
   - `COLLECTION=spherex_qr2_deep` — **Deep Survey** Spectral Image MEFs
   - `COLLECTION=spherex_qr2_cal` — **Calibration files**

   Returned table includes an `access_url` column (on-prem retrieval URL for `wget`/`curl`) and a `cloud_access` column (cloud-hosted data access info). Example queries, verbatim:
   ```
   wget -O spherex-example1.html "https://irsa.ipac.caltech.edu/SIA?COLLECTION=spherex_qr2&POS=circle+127.69444+-39.17760+0.01&RESPONSEFORMAT=HTML"
   ```
   ```
   curl -o spherex-example2.html "https://irsa.ipac.caltech.edu/SIA?COLLECTION=spherex_qr2&POS=circle+127.69444+-39.17760+0.01&RESPONSEFORMAT=HTML"
   ```
   Additional IRSA SIA2 docs: `https://irsa.ipac.caltech.edu/ibe/sia.html`.
   **Ingestion-lag note (verbatim):** "SPHEREx data are ingested on a weekly basis. Due to the nature of the ingestion process, new SPHEREx data will first be available in the browsable directories, the SPHEREx Data Explorer GUI, and certain TAP queries... Availability via SIA2 will lag on the order of a day."

3. **Cutout service**: append `center=` and `size=` query params to an on-prem `access_url`. Parameter docs: `https://irsa.ipac.caltech.edu/ibe/cutouts.html`. Verbatim example:
   ```
   curl -o cutout.fits "https://irsa.ipac.caltech.edu/ibe/data/spherex/qr2/level2/2025W19_2B/l2b-v20-2025-247/3/level2_2025W19_2B_0073_2D3_spx_l2b-v20-2025-247.fits?center=156.09328159,-41.64466331&size=0.1"
   ```
   Also invoked by the SPHEREx Data Collection Explorer's "Spectral Image Search" cutout-download option, and demonstrated in the tutorial "Download a collection of SPHEREx Spectral Image cutouts as a multi-extension FITS file" (`https://caltech-ipac.github.io/irsa-tutorials/spherex-cutouts/`).

4. **Python packages** — `pyvo` (`https://pyvo.readthedocs.io/en/latest/`) and `astroquery` (`https://astroquery.readthedocs.io/en/latest/ipac/irsa/irsa.html`). Named example notebooks (URLs given by the site, not fetched — third-party tutorial repo, out of task scope): "Introduction to SPHEREx Spectral Images" (Astroquery/SIA2), "Download a collection of SPHEREx Spectral Image cutouts..." (PyVO/**TAP**, this is the *only* place a TAP example is referenced on the whole site — **no literal TAP endpoint URL is given on the site itself**), "Understanding and Extracting the PSF Extension in a SPHEREx Cutout" (PSF selection demo), "IRSA Cloud Access Introduction" and "SPHEREx Source Discovery Tool" (demonstrate using the `cloud_access` column from SIA2 results).

5. **SPHEREx Data Explorer** (web GUI): `https://irsa.ipac.caltech.edu/applications/spherex`. Described only as providing "context-sensitive help"; site gives no further detail on its query interface, filters, or output formats.

### AWS / cloud access [IRSA:cloud_access — linked but not part of the 3-page site]

The site's only cloud-access statement is "SPHEREx data products are also available on the cloud via AWS. Please see our instructions for accessing on-cloud SPHEREx data: `https://irsa.ipac.caltech.edu/cloud_access/#spherex`." Fetching that linked page (official IRSA, not part of the documentation-site repo) gives exact details not present on the documentation site itself:
- **S3 bucket name**: `nasa-irsa-spherex`, region **`us-east-1`**.
- Browsable index: `https://nasa-irsa-spherex.s3.us-east-1.amazonaws.com/index.html`.
- AWS Open Data Registry page: `https://registry.opendata.aws/spherex-qr/`.
- Anonymous access required (e.g. `--no-sign-request` / `anonymous=True`).
- S3 key prefixes for QR2 (mirrors the on-prem directory scheme): `qr2/level2` (Spectral Images, 6-extension MEF as above, organized by planning period), `qr2/abs_gain_matrix`, `qr2/average_psf`, `qr2/dark`, `qr2/dichroic`, `qr2/gain_factors`, `qr2/nonfunc`, `qr2/nonlinear_pars`, `qr2/readnoise_pars`, `qr2/solid_angle_pixel_map`, `qr2/spectral_wcs`.

## Calibration, systematics and known issues

**[SITE]**: essentially nothing beyond what is captured in the Level 2/calibration-product sections above (units, dimensions, the PSF header bug, and "no zodi subtraction applied"). The site does not discuss flat fields as a separate concept, gain/linearity/persistence physics, cosmic rays, stray light, sky background modeling in prose, or quantitative astrometric/photometric accuracy numbers — all of the following is **[ExpSupp v2.0]** only:

- **"Flat field" is merged with gain** — SPHEREx has no separate flat-field product: "the traditional flat field and photometric gain products are combined into the Absolute Gain Matrix... due to the wavelength variations across the band." The Absolute Gain Matrix (units (MJy/sr)/(e⁻/s)) is applied to the dark-subtracted Level-1 image to bring it to MJy/sr; it "encodes pixel-to-pixel response variations within spectral channels as well as the absolute gain conversion for each spectral channel."
- **Dark subtraction**: dark current (e⁻/s) estimated simultaneously with the flat-field/gain response derivation; subtracted from the active 2040×2040 region before absolute-gain multiplication.
- **Nonlinearity**: corrected with a quadratic model parameterized by `Qnl` (and `b1,b2,b3,Qmax` in the calibration MEF); pixels with unreliable correction get the `NONLINEAR` flag (bit 15). Level 2 DQA check: "No pixel in the image has a measured flux corrected by more than 50%."
- **Persistence**: modeled with "a parameterized analytic model to estimate the level of persistent flux in each pixel based on the cumulative exposure history of the survey," arising from charge traps in the detector diode depletion region; downstream modules use this to set the `PERSIST` flag (bit 17) and to distinguish persistence from blooming/snowball artifacts. Central regions of Snowballs and large Cosmic Ray events "produce excess persistence" in subsequent images.
- **Cosmic rays / transients**: `TRANSIENT` (bit 0) set onboard during SUR; large events (snowballs) produce a core flagged `OVERFLOW`+`TRANSIENT` plus an unflagged halo in earlier pipeline versions — as of the pipeline update referenced in ExpSupp §3.2.1, additional flags `BLOOM`, `SNOWBALL`, `HALO`, `SATELLITE_HALO` were added specifically to capture blooming sources, snowball events, transient halos, and satellite-track halos (see FLAGS table above). "Very early cosmic ray" events can escape flagging if the transient occurs prior to the algorithm's flagging window.
- **Stray light**: two named artifacts — an "8° ghost," "a stray light artifact produced by very bright stars approximately 8° from [the source]," and a "Moon stray light feature at detector edge," affecting a fraction of exposures in **Bands 1, 4, 5, and 6**, showing "excess emission at the left or right edges."
- **Dichroic edge effect**: the `DICHROIC` flag (bit 7) marks pixels in the "dark corners" of Bands 3 and 4 where the dichroic "smile" gives an incompatible bandpass for that side of the split; throughput <50% there.
- **Astrometric accuracy**: refined per-exposure using AstroPy + Astrometry.net + SCAMP + the WISE astrometry pipeline, calibrated against Gaia DR3 (cross-matched to WISE/2MASS for predicted SPHEREx flux), requiring calibrators with Gaia `astrometric_params_solved ≥ 31`, S/N>10 (not saturated) in Gaia RP, izy, JHKs, WISE W1/W2, and no contaminating source within 2 SPHEREx pixels brighter than 10% of the calibrator flux. Result: **RMS < 0.3″** in RA/Dec for a representative detector, no significant degradation toward detector corners; maximum geometric distortion in the corners ≈**13 px (~80″)**. A `FINAST` header flag records astrometric quality (0 = good, higher = partial/poor); pipeline R7+ adds `WCSRETRY`, `RETRY_WCSMODE`, `WCSSEED`, `WCSSEEDOBS` keywords describing whether/how an astrometry "retry" mode was used.
- **Absolute photometric/flux calibration accuracy**: calibrated against **HST/CALSPEC** standard stars (A stars, white dwarfs, F/G stars) after applying the final gain matrices; "the absolute flux calibration is determined to an accuracy of **<1%**" for the great majority of channels, dominated by CALSPEC systematic uncertainty (itself ~1% or less averaged over stars). Reference to Ashby et al. 2026 (in prep) for more detail.
- **Zodiacal light**: see ZODI HDU description above — modeled (modified Kelsall+1998 + Tsumura+2013), wavelength-dependent scaling derived from Year-1 |b|>30° data, distributed as a separate `zodi_scaling` calibration file, and (again) **never subtracted from the science IMAGE**, only provided as a separate model layer.
- **Flags to exclude for science / stacking**, as explicitly enumerated by the Mosaic Tool's masking step (a good default "science-safe" exclusion list): `TRANSIENT, SUR_ERROR, NONFUNC, DICHROIC, MISSING_DATA, HOT, COLD, PHANMISS, NONLINEAR, PERSIST, CROSSTALK, GHOST, GHOST_FPA, GHOST_EXT, STREAK, BLOOM, SNOWBALL, HALO, SATELLITE_HALO`. Flags that are informational/propagated rather than automatically exclusionary: `OVERFLOW, SOURCE, OUTLIER`.

## Guidance relevant to extracting galaxy spectra

Nothing on the 3-page site itself addresses photometry/PSF-fitting/extended-source methodology — this entire section is **[ExpSupp v2.0]**, from the Level 3 Forced Photometry Module description (the closest official analogue to what a PSB-spectral-extraction pipeline would need):

- The official **Level 3 forced-photometry algorithm uses the Tractor package** (generative/forward modeling, maximum-likelihood fit of a scene model to the observed image + variance map), run in forced-photometry mode with **fixed source positions**. Crucially: **"While not required, intrinsic galaxy morphology can be supplied for the generative modeling"** — i.e., the official pipeline is explicitly designed to support extended (non-point) sources, not just point sources, if a morphological model is provided as a prior.
- **PSF used**: the position-dependent **ePSF calibration product** (Sect. 4.1.2, the same family as the Exposure-Averaged PSF product), selected per detector location — same "which PSF zone am I in" problem as described in the cutout PSF-selection recipe above.
- **Background subtraction is two-stage**: (1) a **global spectral background**, computed once per image from pixels that are not flagged bad and don't contain source flux, is removed first; (2) a **local background** term (estimated initially from a 15×15-pixel region around the source cutout, after masking known sources) is then fit *simultaneously* with the source flux(es) as part of the same generative-model optimization — i.e. local background is not simply subtracted beforehand, it's a joint free parameter.
- **Flux units**: Tractor-fit fluxes are converted to physical units (µJy) using the **local pixel solid-angle map** (the Solid Angle Pixel Map calibration product), which itself incorporates the optical distortion.
- **Uncertainty**: statistical uncertainty from Tractor is corrected upward by an empirically-derived **3% systematic floor added in quadrature** (`σ_reported = sqrt(σ_Tractor² + (0.03·F)²)`), calibrated against repeated-measurement scatter of stars not fully explained by the propagated variance map; this correction is applied to the catalog error column only, not to the VARIANCE image itself.
- **Wavelength assignment per measurement**: because of the LVF's spatially-varying bandpass, the wavelength associated with any given flux measurement depends on exactly where on the detector the source (or the relevant part of an extended source) falls — the pipeline explicitly threads position-dependent wavelength through the photometry step rather than assuming a single nominal band wavelength (consistent with the CWAVE/CBAND guidance for the Spectral WCS product above).
- **Quality control per source**: flagged pixels affecting an object are checked and propagated to the output catalog; additional photometry-specific flags are set for issues like strong nonlinearity or saturation; a **goodness-of-fit metric** is computed from the residual between model and data in an aperture around each source.
- **Mosaic caveat directly relevant to extended/stacked-galaxy work**: the IRSA Mosaic Tool explicitly recommends against precision photometry on its coadds ("For science applications requiring precision photometry, we recommend using the L2 spectral images directly") and, as of the initial Mosaic Tool release, **excludes the Deep Field Surveys entirely** — so any deep-field PSB galaxy work must presently be done from individual L2 exposures, not a pre-built mosaic.
- No explicit discussion (on the site or found in the ExpSupp sections I searched) of extended-source aperture photometry, isophotal photometry, or galaxy-specific PSF-matching guidance beyond the "morphology can be supplied to Tractor" statement above — this is a real gap for someone doing resolved/extended post-starburst galaxy spectral extraction and likely means building custom extraction code (as e.g. the SPIFF pipeline in Gagné et al. 2026 did for point sources) is currently the norm rather than using an official extended-source tool.

## Acknowledgment and citation

**[SITE]**: no acknowledgment or citation-format text of any kind appears on any of the 3 site pages. The only "citation-adjacent" element found in the rendered HTML is a **content license badge** ("Content License: BSD 3-Clause 'New' or 'Revised' License (BSD-3-Clause)," linking to `https://github.com/Caltech-IPAC/spherex-archive-documentation/blob/main/LICENSE`), which licenses the *documentation text itself*, not a data-usage/citation policy. No DOI, no "please cite" boilerplate, and no data-citation guidance is given anywhere on the site.

**[ExpSupp v2.0]** *does* contain the mission's official acknowledgment text (§1.6 "Acknowledgments"), verbatim:
> "If you use data from SPHEREx in a publication, please include the following acknowledgment: This publication makes use of data products from the Spectro-Photometer for the History of the Universe, Epoch of Reionization and Ices Explorer (SPHEREx), which is a joint project of the Jet Propulsion Laboratory and the California Institute of Technology, and is funded by the National Aeronautics and Space Administration."

This acknowledgment text is **not reproduced or linked from the documentation site itself** — a user who only reads the 3-page site would not find it there; they would need to go into the Explanatory Supplement PDF.

## Items that look new since ~March 2026

Cross-referencing the site's GitHub commit history (last commit 2026-05-08) against the Explanatory Supplement's own change log (up to v2.0, 2026-08-25) and against the site's actual rendered text:
- **PSF header-ordering bug fix** (fixed 2026-03-31; site commit "Add warning about PSF error" 2026-04-13) — now documented on the site as a warning box, with the fuller mechanism only on the separate `psfhdrerr.html` IRSA page.
- **0-based vs. 1-based pixel-indexing clarification** for the cutout PSF-selection recipe (site commit 2026-04-08).
- **`curl` cutout example and `cloud_access` column documentation** added to the data-access page (site commits 2026-04-13).
- **License badge added to rendered pages** (site commit 2026-02-17).
- **"Remove references to QR1"** — the site's data-products text was trimmed to stop describing QR1 in detail (site commit 2026-02-18), even though QR1 files remain downloadable per the ExpSupp.
- **Not yet reflected on the site at all, but present in the linked Explanatory Supplement** (all "new" relative to the site's Feb 2026 snapshot): the **Mosaic Tool / Mosaics section** (ExpSupp v1.6, 2026-05-06); the **major R7 pipeline update** covering Persistence Masks, Bad Pixel Flagging, Fine Astrometry, Outlier Pixel Detection, Zodi Prediction, Photometric Measurements, PSF, and Spectral Channels (ExpSupp v2.0, 2026-08-25); the **QR3** release (Survey 3/4 data) and **DR1** (Year-1 reprocessing of Survey 1/2) release names, both explicitly slated for "late fall 2026"; the **Level 3 Forced Photometry** module/Tractor-based catalog description; and the **Reference Catalog v0.73** used for astrometry/masking.
- Given "today" is 2026-09-22 and DR1/QR3 are described as arriving "late fall 2026," these releases are **imminent but (per the fetched pages) not yet reflected anywhere in the actual documentation site text** — worth rechecking the site again once that release lands, since file-naming, collection names, and possibly new FLAGS bits (Fine Astrometry retry-mode keywords, updated flag set) will likely require documentation updates that haven't happened yet.

## Open questions / things I could not verify

- **No literal TAP endpoint URL is given anywhere on the documentation site.** TAP is only referenced indirectly ("certain TAP queries," pointing to the PyVO cutouts tutorial notebook, which I did not fetch per the task's "no third-party GitHub tools" instruction). The exact TAP service URL/table names for SPHEREx at IRSA were not found in the pages I was instructed to survey.
- **Data Explorer GUI internals** (search fields, output formats, exact catalog/table browsing capability) are not documented beyond "context-sensitive help" — I could not verify what tables/columns it exposes.
- **FLAGS table numbering mismatch**: the live documentation site text says the flag definitions are in **"Table 10"** of the Explanatory Supplement; in the copy of the Explanatory Supplement I fetched (**Version 2.0, 2026-08-25**) the equivalent table is **Table 16**. This is most likely simple table-renumbering drift as the Supplement has grown (v1.0 → v2.0) without the site's cross-reference being updated, but I could not confirm this against an older (e.g. v1.0 or v1.5) copy of the PDF, since only the current version is hosted at the given URL.
- **No data-product DOI was found** for QR1/QR2/QR3/DR1/DR2 (as opposed to journal-article DOIs cited in the Explanatory Supplement's bibliography). It's unclear whether IRSA/SPHEREx mints DOIs for quick-release data at all, or only plans to for the annual Data Releases — not stated anywhere I checked.
- **Bits 3, 4, 5, 8, 13, 16, and 18 of the FLAGS bitmask** are not defined in the extracted table — could be reserved for future use, could be an extraction gap on my part (the PDF table spans a page break and I did not cross-check against a second independently-rendered copy).
- I did **not** fetch or read the full 82-page Explanatory Supplement end-to-end — only the sections directly relevant to the requested outline (FLAGS/Table 16, ZODI, VARIANCE, PSF/psffix, Mosaics, Level 3 photometry, calibration/systematics, acknowledgments, release-version history). There is likely additional relevant material in unread sections (e.g., full Level 1 pipeline description, detailed calibration-derivation math, complete header-keyword dictionary in its Appendix A "Table A.35").
- I did not fetch the SPHEREx project website (`https://spherex.caltech.edu/`) or the general SPHEREx mission page (`https://irsa.ipac.caltech.edu/Missions/spherex.html`) that the landing page links to as "Additional Resources" — these were treated as outside the documentation-site scope.
- Pages that failed to load: **none**. All 3 site pages, the `psfhdrerr.html` IRSA page, and the `cloud_access` IRSA page loaded successfully (HTTP 200) via `curl`; one `WebFetch` call to `psfhdrerr.html` timed out and was retried successfully via `curl`.
