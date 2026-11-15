# IRSA SPHEREx official pages (surveyed 2026-09-22)

Survey method: started from the IRSA SPHEREx mission landing page and followed every SPHEREx-related
link found on it and on the pages it links to, using WebFetch (with `curl` fallback where WebFetch failed
or truncated content). The SPHEREx Explanatory Supplement PDF (v2.0, 2026-08-25, 82 pages) was downloaded
and read in full with `pdftotext -layout` (poppler installed locally for this purpose) since no other tool
was available; it is by far the most detailed and load-bearing source in this note.

## Pages visited (URL list with one-line description each)

- [IRSA SPHEREx mission page](https://irsa.ipac.caltech.edu/Missions/spherex.html) — SPHEREx mission landing page at IRSA; links to
  every data product, tool, DOI and documentation page below.
- [IRSA Quick Release overview](https://irsa.ipac.caltech.edu/data/SPHEREx/docs/overview_qr.html) — the authoritative Quick Release (QR)
  overview: release history (QR1/QR2/QR3), DOIs, acknowledgment text, data-access method list.
- [SPHEREx Explanatory Supplement (PDF)](https://irsa.ipac.caltech.edu/data/SPHEREx/docs/SPHEREx_Expsupp_QR.pdf) — v2.0, dated 2026-08-25 (SSDC-DP-017). Full pipeline/data-product/calibration reference.
- [PSF header-ordering erratum](https://irsa.ipac.caltech.edu/data/SPHEREx/docs/psfhdrerr.html) — PSF FITS-layer header-ordering erratum
  page (production URL; a linked staging-domain copy at `irsatest.ipac.caltech.edu` returned HTTP 403).
- [SPHEREx List of Ice Sources (SPLICES)](https://irsa.ipac.caltech.edu/data/SPHEREx/SPLICES/) — target
  catalog overview page.
- [SPHEREx comet 3I/ATLAS data page](https://irsa.ipac.caltech.edu/data/SPHEREx/docs/comet3iatlas/index.html) — SPHEREx observations of
  interstellar comet 3I/ATLAS, a special spectral-image data product.
- [IRSA cloud access page](https://irsa.ipac.caltech.edu/cloud_access/#spherex) — IRSA cloud (AWS Open Data) access page, SPHEREx
  section.
- [SPHEREx Data Explorer](https://irsa.ipac.caltech.edu/applications/spherex) — web app (JavaScript SPA;
  WebFetch could not render app content, only the empty shell/title).
- [SPHEREx cutout tool documentation](https://irsa.ipac.caltech.edu/data/SPHEREx/docs/cutout_tool.html) — cutout-service documentation and
  example URL.
- [SPHEREx spectral calibrations page](https://irsa.ipac.caltech.edu/data/SPHEREx/docs/spherex_spectral_calibrations.html) — page describing the
  normalized spectral transmission-curve products (separate from the pipeline's absolute gain/spectral-WCS
  calibration products).
- [IRSA VO/API index](https://irsa.ipac.caltech.edu/voapi.html) — general IRSA VO/API index page; no SPHEREx-specific text was
  present in the static HTML (menu of Catalogs/Images/Spectra/MOST/IBE APIs; SPHEREx SIA/TAP entries appear
  to be populated by JavaScript at runtime, not visible in the raw HTML fetched via curl).
- [SPHEREx Archive User Guide](https://caltech-ipac.github.io/spherex-archive-documentation/) — MyST/GitHub
  Pages site, dated 2026-02-18, home page.
- [SPHEREx Archive User Guide: Data Access](https://caltech-ipac.github.io/spherex-archive-documentation/spherex-data-access) — Archive User Guide,
  "SPHEREx Data Access" chapter: SIA2 endpoint, collections, IBE paths, cutout syntax, astroquery/PyVO,
  cloud access notes.
- [SPHEREx Archive User Guide: Data Products](https://caltech-ipac.github.io/spherex-archive-documentation/spherex-data-products) — Archive User Guide,
  "SPHEREx Data Products" chapter: product list, filename conventions, MEF structure.
- [AWS Open Data registry: SPHEREx QR](https://registry.opendata.aws/spherex-qr/) — AWS Registry of Open Data entry for the `nasa-irsa-spherex`
  S3 bucket; enumerates every top-level S3 prefix (as of the QR2 processing epoch) with ARNs and example
  AWS CLI commands.
- [arXiv:2511.02985](https://arxiv.org/abs/2511.02985) — Bock et al., "The SPHEREx Satellite Mission" (submitted 2025-11-04,
  published ApJ 999(1):139, March 2026; doi:10.3847/1538-4357/ae2be2).
- [arXiv:2511.15823](https://arxiv.org/abs/2511.15823) — Akeson et al., "The SPHEREx Image and Spectrophotometry Processing
  Pipeline" (submitted 2025-11-19, published ApJS 285(2):67, August 2026; doi:10.3847/1538-4365/ae8843).

Pages named on the landing page but **not separately fetched in depth** (time/priority; content largely
duplicated elsewhere or is a thin wrapper tool page): Spectrophotometry Tool
(`/applications/spherex/tool-spectrophotometry`), Mosaic Tool (`/applications/spherex/tool-mosaic`), Moving
Object Search Tool (`/applications/MOST`), Source Discovery Tool demo notebook, and the three
[IRSA tutorials](https://caltech-ipac.github.io/irsa-tutorials) Python-notebook pages (intro, cutouts, PSF) — these are tutorial
notebooks whose technical content (cutout syntax, PSF-fix code) is already captured from the Explanatory
Supplement and the Archive User Guide.

## Current data releases (names, dates, DOIs, what changed between releases, which are retired)

All release information below is stated verbatim/paraphrased from `overview_qr.html` and Explanatory
Supplement §2.1, cross-checked against each other (they agree).

| Release | First released | Status as of 2026-09-22 | DOI | Pipeline version(s) | Notes |
|---|---|---|---|---|---|
| **QR1** (Quick Release 1) | July 2025 | **Retired February 2026** — "no longer available from IRSA" | `10.26131/IRSA629` | 6.2.1–6.3.0 | Initial calibrations from IOC + early science data. |
| **QR2** (Quick Release 2) | October 2025 | Active (superseded by QR3 as the "primary" release but still archived/citable) | `10.26131/IRSA652` | 6.4.0–6.5.6 | "Substantially improved calibrations" vs QR1; includes reprocessed versions of all QR1 images. PSF-layer header ordering bug present in versions 6.4–6.5.5, fixed in 6.5.6 (files retroactively fixed and suffixed `+psffix1`, corrected as of **2026-03-31**). Spectral WCS (CWAVE/CBAND) files were updated for QR2; images before planning period `2025W25_2A` reference a different (older) WCS file in their header even though the extension content was made consistent. |
| **QR3** (Quick Release 3) | **September 2026** | Active/current at time of survey | `10.26131/IRSA662` | Early QR3 weeks (2026-05-16 to 2026-07-19) processed with pipeline 6.5.6; the QR3/R7 versions of those weeks are to be released alongside DR1 in "late fall 2026" | Explanatory Supplement explicitly warns: **"we advise caution when combining QR2 and QR3 data"** because gain/spectral calibrations changed between them. An `l3_flux_corrections_D<n>` calibration product is provided specifically to let users rescale QR2 photometry (old gains) onto the QR3/DR1 gain scale. |
| **DR1** (Data Release 1, Year‑1 reprocessing) | Not yet released (per-pipeline versions R7.0–R7.2 exist; expected alongside the QR3/R7 re-release, "late fall 2026") | Forthcoming | not assigned in surveyed pages | R7.0–7.2 | Full reprocessing of Survey 1+2 (first 12.5 months) with a major pipeline overhaul: new Persistence Masks, Bad Pixel Flagging, Fine Astrometry, Outlier Pixel Detection, Zodi Prediction, Photometric Measurements, and PSF (ePSF) derivation. Will include additional data product types not yet in QR (see below). |
| **DR2** (Data Release 2, Year‑2 reprocessing) | Not yet released | Planned | — | — | Full reprocessing of Survey 1–4 (25 months). |

Key structural point from the Supplement: **QR = Quick Release spectral images only** (Level 2), released
weekly within 60 days of acquisition, with essentially no reprocessing philosophy beyond periodic recalibration.
**DR = annual Data Release**, a full pipeline reprocessing after each observing Year, which will add new
product types (forced-photometry catalogs at scale, all-sky mosaics/data cubes, Level 4 science products).
The document states: "Due to improved calibrations and their impact on data quality, the exact file list for
QR1 and QR2 is slightly different and science users should NOT combine files from the two releases."

## Data products (product types, file naming, extensions, units, pixel scale)

### 1. Spectral Images (Level 2) — the core QR/DR product
- Produced by the SSDC Level 2 pipeline, one file per sky pointing × detector (6 detectors/bands per
  pointing).
- Released within 60 days of on-orbit acquisition; **no zodiacal-light subtraction is applied** to the
  science IMAGE layer — a model background is provided in a separate ZODI extension for user subtraction.
- **Filename convention** (example): `level2_2025W22_2B_0001_1D3_spx_l2b-v4-2025-152.fits`
  - `2025W22_2B` = Survey Planning Period (week 22 of 2025, second half, version B)
  - `0001` = large-slew counter (starts at 0); `1` = small-slew counter (1–4, up to 4 small slews/large slew)
  - `D3` = detector number (1–6)
  - `l2b-v4-2025-152` = Level-2b pipeline, version 4, processed on day-of-year 152 of 2025
  - Note: the first plan of the science survey uses `2025W17_4B` (a "4" instead of 1/2).
- **File format**: Multi-Extension FITS (MEF), 6 HDUs:
  1. **IMAGE** — calibrated surface brightness, **MJy/sr**, 2040×2040 pixels.
  2. **FLAGS** — per-pixel bitmask (see flags table below), 2040×2040.
  3. **VARIANCE** — per-pixel variance, (MJy/sr)², 2040×2040.
  4. **ZODI** — model zodiacal-light background, MJy/sr, 2040×2040 (NOT subtracted from IMAGE).
  5. **EPSF** — oversampled ePSF cube: 441 rows (21×21 grid) for Detectors 1,2,4,5,6; 451 rows (11×41 grid)
     for Detector 3 (finer sampling along the dispersion direction because of birefringence effects near the
     dichroic). Each ePSF is a 33×33 array at 5× native-pixel oversampling, normalized to unit integral.
  6. **WCS-WAVE** — binary table (3 columns, 1 row), approximate pixel→(wavelength,bandwidth) lookup for
     visualization only (NOT for science; use the standalone Spectral WCS calibration files for science).
- **Pixel scale**: 6.15″ × 6.15″ (native detector pixel).
- **File size**: ≈67 MB per spectral image file.
- **Long-keyword convention**: HIERARCH (ESO convention) used for header keywords exceeding the 8-character
  FITS limit.

### 2. Calibration products (delivered alongside spectral images, also public at IRSA)
- **Absolute Gain Matrix** — FITS image, 2040×2040, units (MJy/sr)/(e⁻/s); one per detector; ≈16 MB/file.
  Combines the traditional "flat field" and "photometric gain" into one product because of SPHEREx's
  wavelength variation across the band.
- **Effective PSF (ePSF) models** — standalone calibration product (same content class as the embedded EPSF
  extension above); FITS binary table, one row per detector zone; ≈8 MB/file. For R7, PSF is now measured
  purely empirically (Anderson & King 2000 ePSF formalism) rather than via optical-model stacking/deconvolution.
- **Dark Current maps** — FITS image, 2040×2040, e⁻/s; ≈16 MB/file.
- **Spectral WCS files** — one FITS file per band with CWAVE (central wavelength, µm) and CBAND (bandwidth,
  µm) extensions; CWAVE is defined as the wavelength where the cumulative per-pixel transmission curve
  reaches 50% of total area. **Use CWAVE/CBAND for science; the WAVE-WCS embedded in spectral images is for
  visualization only.**
- **Spectral Channels file** — `spectral_channels_YYYYMMDD.fits`; one file total (same geometric definition
  applies to all 6 bands): a 2040×2040 integer array assigning each pixel to spectral channel 0–18 (1–17 are
  the 17 nominal channels used for survey stepping; 0 and 18 are off-nominal corner/edge regions). Accompanied
  by a table of per-channel WAVELENGTH, WL_MIN/MAX, BANDWIDTH, R, R_STD.
- **Atmospheric emission-line templates** — `aurora_template*`, `he_template_D<n>*` (bands 1,2), and
  `shuttle_glow_template*` FITS images (2040×2040); fit coefficients are recorded in image headers but the
  emission is NOT subtracted from data.
- **Dichroic-impacted-pixel mask** (`dichroic_D<n>`), **Non-functional-pixel mask** (`nonfunc_D<n>`),
  **Non-linearity parameters** (`nonlinear_pars_D<n>`), **Electronic Gain Factors** (single YAML file,
  32 values/detector), **Read-noise parameters** (`readnoise_pars_D<n>`, two extensions READOUT-1/READOUT-2),
  **Solid Angle Pixel Map** (`solid_angle_pixel_D<n>`, arcsec²), **Initial distortion (SIP)** (`sip_D<n>`),
  **Crosstalk parameters** (ECSV, `xtalk_class<n>`, types 1–2), **Zodi scaling** (ECSV, `zodi_scaling_D<n>`,
  per-band correction to the Kelsall et al. 1998 model), and **Flux Corrections**
  (`l3_flux_corrections_D<n>`, FITS, per-pixel scale factors to bring QR2 photometry onto the QR3/DR1 gain
  scale).

### 3. Catalogs
- **Forced-photometry (Level 3) catalog** — produced by the Tractor-based forced-photometry module (not yet
  a bulk public product in QR; used internally for gain calibration and exposed interactively via the
  Spectrophotometry Tool). Reports source ID, flux + uncertainty, wavelength, (i,j) pixel coords, fit-quality
  metric, and an integer flags bitmask including a summary **CONTAINS_BAD_PIXEL (bit 32)** warning flag.
  Photometric uncertainties are inflated in quadrature by a 3% systematic term:
  `σ_reported² = σ_Tractor² + (0.03·F)²`.
- **SPLICES** (SPHEREx List of Ice Sources) — target list of ~9 million spatially isolated, IR-bright point
  sources selected for likely ice-absorption features; based on Ashby et al. (2023, ApJ) selection.
  DOI `10.26131/IRSA554`. Delivered as a downloadable FITS catalog (3.1 GB) plus Catalog Search Tool and
  Program Interface access; documentation includes separate "Release Notes" and "Column Descriptions" pages.

### 4. Mosaics / data cubes (Mosaic Tool product, IRSA-hosted; all-sky cubes are a DR1/DR2 deliverable)
- Built from L2 images: zodi-subtracted (`IMAGE − ZODI`), bad-pixel masked, reprojected via a fast
  intensity-weighted 2D histogram ("pixel binning," O(N), no smoothing, nearest-neighbor pixel assignment;
  Cukierman et al. 2026).
- Grid: user-specified center/width/height/PA; minimum pixel size 9″; TAN projection; odd pixel dimensions
  so CRPIX sits exactly at the mosaic center.
- Output: 3D FITS spectral cube with extensions PRIMARY, **IMAGE** (N,ny,nx; MJy/sr), **NHITS** (contributing
  pixel counts), **FLAGS** (bitwise-OR of propagated OVERFLOW/SOURCE/OUTLIER flags), **SPECTRAL_CHANNELS**
  (per-channel metadata table), **WCS-WAVE** (spectral lookup table). Uses the FITS `-TAB` algorithm for a
  4-world-axis WCS (RA, Dec, wavelength, bandwidth) despite only 3 pixel axes.
- Currently All-Sky Survey images only (Deep Field images excluded from the initial Mosaic Tool release).
- Known mosaic-specific artifacts: airglow-line striping (esp. He 1.083 µm) and extended-source spectral-line
  striping/moiré patterns from the LVF's spatial–spectral entanglement (see Known Issues below).

### 5. Special/ancillary science data products
- **SPHEREx observations of interstellar comet 3I/ATLAS** — calibrated spectral images from two 2025
  campaigns (August and December, pre-/post-perihelion), distributed through IRSA with VOTable metadata;
  data described as low S/N at many wavelengths and spatially extended (not usable with the
  Spectrophotometry Tool). No DOI found on the page surveyed.

## Access methods (every service: endpoints, collections, tables, cutout syntax, cloud paths)

### SIA (Simple Image Access, v2)
- Endpoint: `https://irsa.ipac.caltech.edu/SIA?` (requires `COLLECTION=` parameter).
- Collections documented in the Archive User Guide "Data Access" chapter (dated for the QR2 epoch; QR3
  equivalents not confirmed live — see Open Questions):
  - `spherex_qr2` — Wide (All-Sky) Survey spectral images
  - `spherex_qr2_deep` — Deep Survey spectral images
  - `spherex_qr2_cal` — calibration files
- Live query of `https://irsa.ipac.caltech.edu/SIA?COLLECTION=spherex_qr2` timed out under curl during this
  survey (see Open Questions); could not independently confirm current collection names/whether `spherex_qr3`
  collections now exist.
- Cloud-access URLs for each record are reportedly returned via a `cloud_access` column in SIA2 query results.
- New data reportedly appear first in the on-premises browsable directories, with SIA2 availability lagging
  by roughly one day.

### IBE (IRSA Batch/Bulk Engine) — direct file access / cutouts
- Root path: [IRSA IBE SPHEREx QR2 directory](https://irsa.ipac.caltech.edu/ibe/data/spherex/qr2/) (QR2 shown; QR3 presumably
  `.../spherex/qr3/`, not independently confirmed — see Open Questions).
- Path structure: `level2/<Planning Period>/l2b-v<Version>-<Processing Date>/<Detector>/<filename>.fits` for
  spectral images; calibration products under sibling directories named for each product
  (`abs_gain_matrix/`, `dark/`, `average_psf/`, `dichroic/`, `gain_factors/`, `nonfunc/`, `nonlinear_pars/`,
  `readnoise_pars/`, `solid_angle_pixel_map/`, `spectral_wcs/`, etc. — matches the S3 prefixes below one-to-one).
- **Cutout syntax**: append query parameters directly to a file's on-premises URL:
  `<file_url>?center=<RA>,<Dec>&size=<degrees>`
  - Example (from official docs): `https://irsa.ipac.caltech.edu/ibe/data/spherex/qr/level2/2025W19_2B/l2b-v11-2025-163/3/level2_2025W19_2B_0073_2D3_spx_l2b-v11-2025-163.fits?center=156.09328159,-41.64466331&size=0.1`
  - Cutouts preserve the full MEF structure/metadata (including the PSF cube) of the original file.
  - No rate limits, max size, or response-time figures were documented on the pages surveyed.

### Astroquery / PyVO
- The `astroquery.ipac.irsa` module (IRSA-specific wrapper) is documented as supporting SPHEREx data access;
  PyVO is documented for standards-based SIA2 image discovery. Exact class/method names were not shown in the
  fetched content (see Open Questions — would need the tutorial notebooks for exact code).

### SPHEREx Data Explorer (GUI)
- URL: [SPHEREx Data Explorer](https://irsa.ipac.caltech.edu/applications/spherex)
- A JavaScript single-page app; WebFetch could only retrieve the page shell/title ("IRSA: SPHEREx"), not its
  functional description. Per the Archive User Guide, it provides interactive search/visualization; it wraps
  the Spectrophotometry Tool (`/applications/spherex/tool-spectrophotometry`) and Mosaic Tool
  (`/applications/spherex/tool-mosaic`) as sub-tools, plus flag-overlay visualization of the FLAGS extension.

### Cloud / AWS S3 access
- Bucket: `nasa-irsa-spherex`, region `us-east-1`, **no AWS account or credentials required**
  (`--no-sign-request` / `anonymous=True`), no egress charges (NASA/AWS Open Data Sponsorship Program).
- Browsable index: [SPHEREx S3 bucket index](https://nasa-irsa-spherex.s3.us-east-1.amazonaws.com/index.html)
- AWS Open Data Registry listing: [SPHEREx QR registry entry](https://registry.opendata.aws/spherex-qr/) — **as surveyed, this registry
  entry only describes the `qr2/` prefix tree** (last updated for the QR2 epoch; does not yet list `qr3/` —
  flagged below as something that may have changed very recently and should be re-checked).
- Enumerated S3 prefixes (ARNs), all under `arn:aws:s3:::nasa-irsa-spherex/qr2/...`:
  - `qr2/level2` — Spectral Images (MEF: IMAGE, FLAGS, VARIANCE, ZODI, PSF/EPSF, WCS-WAVE)
    → `aws s3 ls --no-sign-request s3://nasa-irsa-spherex/qr2/level2/`
  - `qr2/abs_gain_matrix` — Absolute Gain Matrix
  - `qr2/average_psf` — Exposure-Averaged PSF
  - `qr2/dark` — Dark Current
  - `qr2/dichroic` — Dichroic-impacted pixel map
  - `qr2/gain_factors` — per-amplifier electronic gain factors (YAML)
  - `qr2/nonfunc` — Non-functional pixel map
  - `qr2/nonlinear_pars` — Non-linearity correction parameters
  - `qr2/readnoise_pars` — Read-noise maps
  - `qr2/solid_angle_pixel_map` — Solid-angle-per-pixel maps
  - `qr2/spectral_wcs` — Spectral WCS (CWAVE/CBAND) maps
  - (the page listing was truncated during this survey after `spectral_wcs`; additional prefixes such as
    crosstalk/zodi-scaling/flux-corrections likely also exist but were not individually confirmed in the S3
    listing — see Open Questions)
- Citation instructions on the registry page: cite DOI 10.26131/IRSA629 (QR1) or 10.26131/IRSA652 (QR2) plus
  the standard acknowledgment text (QR3's 10.26131/IRSA662 is not yet reflected on this AWS registry page).

### VO API index page
- [IRSA VO/API index page](https://irsa.ipac.caltech.edu/voapi.html) lists IRSA's general API catalog (Catalogs, Images, Spectra,
  Dust Extinction, ZTF Lightcurves, MOST, IBE) but the static HTML fetched via curl contained **zero**
  occurrences of the string "spherex" — the SPHEREx-specific entries visible to a browser are almost
  certainly populated by client-side JavaScript and were not captured by either WebFetch or curl. TAP-specific
  SPHEREx endpoints/table names could not be confirmed from this page (see Open Questions).

## Documentation and explanatory supplement (what documents exist, versions, key contents)

Documents identified:
1. **SPHEREx Explanatory Supplement** (SSDC-DP-017), current version **2.0, dated 2026-08-25**, 82 pages,
   [SPHEREx Explanatory Supplement v2.0 (PDF)](https://irsa.ipac.caltech.edu/data/SPHEREx/docs/SPHEREx_Expsupp_QR.pdf). Authored by the SPHEREx
   Science Data Center team (Akeson, Dubois-Felsmann, Faisst, Fatahi, Goldina, Kwon, Masters, Nelson,
   Paladini, Torrini, Velicheti) with Science Team contributors. This is the primary technical reference; see
   detailed summary below.
2. **SPHEREx Archive User Guide** — [SPHEREx Archive User Guide](https://caltech-ipac.github.io/spherex-archive-documentation/),
   MyST-generated GitHub Pages site, dated 2026-02-18, source at
   [Caltech-IPAC/spherex-archive-documentation](https://github.com/Caltech-IPAC/spherex-archive-documentation). Chapters: "SPHEREx Overview," "SPHEREx
   Data Access," "SPHEREx Data Products." More concise/operational than the Explanatory Supplement; useful
   for exact IBE paths and SIA collection names, but is dated Feb 2026 and pre-dates the September 2026 QR3
   release, so some collection names may be stale.
3. **PSF Extension Header Error erratum page** —
   [PSF header-ordering erratum](https://irsa.ipac.caltech.edu/data/SPHEREx/docs/psfhdrerr.html) (see Known Issues).
4. **QR Overview page** — [IRSA Quick Release overview](https://irsa.ipac.caltech.edu/data/SPHEREx/docs/overview_qr.html), the release/DOI
   authority.
5. Python tutorial notebooks at [IRSA tutorials](https://caltech-ipac.github.io/irsa-tutorials) (intro, cutouts, PSF, source
   discovery tool demo) — not fully surveyed in this pass.
6. Canonical papers: Bock et al. (2026, ApJ 999, 139; arXiv:2511.02985) mission paper; Akeson et al. (2026,
   ApJS 285, 67; arXiv:2511.15823) pipeline paper; both cited throughout the Explanatory Supplement as the
   primary references for instrument and pipeline design, respectively. Also cited: Crill et al. (2020, SPIE,
   doi:10.1117/12.2567224 — instrument overview) and Korngut et al. (2018, SPIE, doi:10.1117/12.2312860 —
   early instrument design; a 2026 Korngut et al. calibration/testing paper, arXiv:2603.29835, is also
   referenced heavily in the Supplement for instrument calibration/testing/performance).

### Detailed Explanatory Supplement summary (v2.0, 2026-08-25)

**Change history** (from the document's own Change Record table) shows the document has evolved continuously
since the April 2025 initial draft, with the two most consequential updates being **v1.5 (2026-03-30)** —
the PSF header-fix update — and **v2.0 (2026-08-25)** — "Major update for pipeline version R7," rewriting the
Persistence Masks, Bad Pixel Flagging, Fine Astrometry, Outlier Pixel Detection, Zodi Prediction, Photometric
Measurements, PSF, and Spectral Channels sections ahead of the DR1 release.

**§1 Mission Overview**: SPHEREx launched **2025-03-12 03:10:12 UTC** (SpaceX Falcon 9, Vandenberg); began
regular science ops **2025-05-01** after In-Orbit Checkout. Nominal 25-month mission, 4 complete all-sky
surveys, ~1.4 trillion spatial-spectral "voxels" per pass. Three science themes: (1) inflation via fNL from
>450M galaxy spectra/redshifts (target σ(fNL) ≤ 1); (2) biogenic ices via >20,000 high-quality ice spectra
of YSOs/protoplanetary disks; (3) galaxy evolution via extragalactic background light (EBL) power spectra at
the ecliptic poles. Archival yield estimates: ≳1 billion galaxy spectra, ≳450M galaxy redshifts, ≳1M quasar
spectra, ≳100M stellar spectra, ≳600,000 exoplanet target stars, ≳700,000 ice-absorption spectra, ≳100,000
asteroid/comet spectra.
- Spacecraft: Ball BCP-100 bus (heritage: IXPE); sun-synchronous LEO, semi-major axis 7037.41 km, inclination
  97.951°, MLTAN 6:00 AM, 98-min period; no propulsion, passive de-orbit within 25 years of end-of-mission.
- Payload: 20 cm effective aperture, f/3, all-aluminum TMA telescope; FoV 2×(3.5°×11.3°) split by dichroic
  beamsplitter; passive 3-stage V-groove radiative cooling (no cryocoolers). 6 detectors (3× H2RG 2.6 µm-cutoff
  SWIR at 62 K, 3× H2RG 5.3 µm-cutoff MWIR at 45 K), Sample-Up-the-Ramp (SUR) readout, frame time 1.5349 s,
  exposure time 113.58 s. **Bands/resolution**: Band 1 0.744–1.116 µm R=39; Band 2 1.099–1.651 µm R=41;
  Band 3 1.636–2.421 µm R=41; Band 4 2.423–3.822 µm R=35; Band 5 3.809–4.420 µm R=112; Band 6 4.412–5.002 µm
  R=128. Pixel scale **6.15″ × 6.15″**. (Note: actual flight performance matches or exceeds pre-launch
  predictions "in all cases other than the helium contaminated 1.083 µm channel.")
- Survey strategy: Survey Planning Software (SPS, developed at ASU) plans on-the-fly to maximize sky/time
  coverage within Sun/Earth/Moon/SAA pointing constraints; target groups of 17 pointings per ecliptic
  longitude; Surveys 1&2 = first 12.5 months (PA=0°/180°), Surveys 3&4 = second 12.5 months, with 3&4 shifted
  by half a spectral channel relative to 1&2 to Nyquist-sample spectra. Two Deep Fields (north and offset
  south ecliptic pole) for EBL science, densely overlapping tiling.
- Naming: survey plans loaded twice weekly, named e.g. `2025W20_2B` (year+week, half-week 1/2, version
  letter); first science plan is `2025W17_4B`.
- **Official acknowledgment text** (quoted below in its own section).

**§2 Data Products**: covers Reprocessing/QR-vs-DR philosophy (already detailed above), Spectral Images
(filename convention, MEF layout, header contents, 67 MB/file size — all captured above), then two large
subsections:
- **§2.3 Image Anomalies and Features** — an extensive, named catalog of real on-sky artifacts (see Known
  Issues section below for the full list, largely quoted).
- **§2.4 Known Limitations** — incorrect source masking (mask size set from Reference-Catalog magnitude,
  can be too big/small) and dichroic-edge pixels (rows at the long-λ edge of Band 3 / short-λ edge of Band 4
  with <50% throughput, flagged DICHROIC).

**§3 Data Processing**: Five pipeline tiers — Level 0 (raw telemetry), Level 1 (engineering units, e⁻/s),
Level 2 (calibrated spectral images/cubes — this is what QR distributes), Level 3 (forced photometry
catalogs), Level 4 (science products: redshifts, ice column densities, mosaics). Detailed algorithmic
subsections for: Source Blooming/Snowball/Transient-Halo flagging (new in R7; defines BLOOM, SNOWBALL, HALO,
SATELLITE_HALO flags with fluence-threshold tables, band-dependent F_over = 50,000 e⁻ for Bands 1–3 and
30,000 e⁻ for Bands 4–6); Nonlinearity correction (quadratic model, Q_nl ≈ 1.4×10⁶ e⁻ Bands 1–3, 0.8×10⁶ e⁻
Bands 4–6, correction factor 1.05–1.08 near saturation); Variance Map (Robberto 2007 SUR-noise formalism plus
an empirically measured excess-noise term; final calibrated VARIANCE layer is 2040×2040 in (MJy/sr)²);
Persistence Masks (multi-exponential decay model, H2RG charge-trapping, Smith et al. 2008); Bad Pixel
Flagging (full flag table — reproduced below); Dark Subtraction; Absolute Gain Correction; Astrometry
(two-step astrometry.net + SCAMP, Gaia-based, RMS <0.3″, <3% failure rate, <1% after R7 retry logic, max
corner distortion ~13 px/~80″); Source Masks; Outlier Pixel Detection (median-filter + ZTF-pipeline-style
streak linking, OUTLIER/STREAK flags); Zodi Prediction (modified Kelsall et al. 1998 model + Tsumura et al.
2013 spectral shape, rescaled per-wavelength against SPHEREx |b|>30° data because Kelsall underestimates ZL
amplitude); Level 2 DQA (11 automated sanity checks — reproduced below); Photometric Measurements (Tractor
forced photometry, full workflow — reproduced above); Mosaics (§3.4, full algorithmic description — captured
above under Data Products).

**§4 Calibrations**: Absolute Gain Matrix, ePSF, Dark Current product definitions; then derivation procedures
— Photometric/Gain calibration (flat-field+dark fit against ~4,000-image groups per detector, restoring
large-scale lab dark-current modes; absolute gain from ~54,000 measurements of 17 CALSPEC primary standards,
PCHIP-interpolated 1D gain solution mapped through the 2D wavelength map; **calibration uncertainty <1%**
relative to HST/CALSPEC reference spectra for the great majority of channels); Astrometric calibration
derivation (described above); PSF Measurement (ePSF formalism, full derivation — captured above, including
the Neff effective-PSF-size metric definition). §4.3 covers Spectral WCS, Spectral Channels, Atmospheric
Templates, and the full list of "Additional Products" (dichroic mask, nonfunc mask, nonlinearity params,
gain factors, readnoise params, solid-angle map, SIP, crosstalk params, zodi scaling, flux corrections — all
captured above under Data Products/Calibration products).

**Appendices**: A — full example spectral-image FITS header keyword table (Table A.35; includes SUR
electronics parameters KOVR_A/R/P, KEN_*, KSN_*, spacecraft position/velocity keywords X_SC/Y_SC/Z_SC etc.,
snowball/bloom-count diagnostic keywords SNWSTRK/NBLMSRCS/SNW7-5CT/etc., and quality counters
L2.N_NONLINEAR/L2.N_PERSIST/L2.N_HOT); B — Absolute Gain Matrix header example; C — Average ePSF header
example; D — List of Acronyms (DR=Data Release, QR=Quick Release, SSDC=SPHEREx Science Data Center,
SST=SPHEREx Science Team, ZL=Zodiacal/Zodi Light, MEF=Multi-Extension FITS, LVF=Linear Variable Filter, etc.)

## Known issues, caveats and systematics (near-verbatim from official pages)

**Image anomalies (optics/detector/particle origin), Explanatory Supplement §2.3:**
- *Frame edge ghost* — triangular scattered-light ghost from sources just outside the FoV at any of the four
  detector edges; can recur across multiple exposures in a small-slew sequence.
- *Linear bright source ghost* — linear ghost from very bright sources off the top/bottom of the detector,
  stronger at longer wavelengths, independent of exact source position.
- *Beam splitter ghost* — ~10′-diameter disk reflection off the dichroic beam splitter for very bright
  sources; most prominent near the Band 3/4 wavelength boundary, present at lower levels in Bands 3–6.
- *8° ghost* — stray-light artifact from very bright stars ~8° from Band 2–6 field centers, in a fraction of
  exposures.
- *Moon stray-light feature* — excess emission at left/right detector edges in Bands 1, 4, 5, 6 attributed to
  Moon illumination of the telescope.
- *Extended cosmic-ray signatures* — most cosmic rays hit one pixel and are removed onboard (>~100
  photoelectron threshold), but many produce neighboring-pixel effects via crosstalk, including "snowballs"
  (very energetic cosmic rays/radioactive decay with an OVERFLOW+TRANSIENT core and an unflagged halo,
  explicitly compared to JWST's snowball artifacts).
- *Cosmic-ray-induced glow* — faint diffuse glow, strongest in Bands 1–2 with a red spectral gradient, weaker
  with a bright detector-edge rim in Bands 4–6.
- *Crosstalk* — three types: (1) negative-image crosstalk displaced ~32 rows (NSKIP row-chopping spacing);
  (2) smeared signal from slow-decaying response in the last-read pixel of the prior row; (3) crosstalk among
  readout channels spaced by multiples of 64 pixels horizontally. First two types flagged in R7.
- *Atmospheric He emission line* (1.083 µm, Bands 1–2) — "varying from a factor few to a factor of 30 greater
  surface brightness than the Zodiacal ... background"; produces spectral leak features near 0.84 µm (Band 1)
  and 1.49/1.25 µm (Band 2); NOT subtracted from data but included in the VARIANCE layer.
- *Auroral emission lines* — mainly N2, seen in Bands 1–2, occasionally fainter in Bands 3–5; correlated with
  solar activity and polar-region observing.
- *Other atmospheric lines* at 0.78, 0.84, 0.93, 1.13, 1.81, 2.63, 2.75, 4.03, 4.64 µm.
- *Shuttle glow* — atomic-oxygen surface excitation in LEO; survey plan limits ram-angle exposure; 1D
  template constructed during commissioning.
- *Diffuse optical transients* — "Roughly 1% of exposures" show ephemeral diffuse features from foreground
  objects/particles.
- *Earth-orbiting satellites* — streaks, flagged onboard as transients (may carry SATELLITE_HALO flag) or by
  the outlier module (STREAK flag); "Fainter satellite streaks near the noise level may not be flagged."

**Known limitations (§2.4):**
- Incorrect source masking when the Reference-Catalog magnitude used to size the mask is wrong (too big or
  too small).
- Dichroic-edge pixels (rows at the Band 3/4 boundary) have degraded throughput/increased noise and "more
  uncertain" photometric calibration; flagged DICHROIC where throughput <50%.

**Mosaic-specific known issues (§3.4.10):**
- Airglow-line striping (especially the 1.083 µm He line) creates scan-correlated banding in coadded mosaics
  because the LVF entangles spatial and spectral information.
- Extended-source spectral-feature striping (e.g., Brackett-α at 4.052 µm) produces sawtooth/moiré artifacts
  under multi-roll-angle coaddition that "do not average down with increased coverage."
- Residual unmasked artifacts: snowball/blooming/halo masking only began with planning period 2025W51_1A
  (December 2025, pipeline 6.5) — **QR2 images from earlier planning periods have these artifacts
  unmasked**; satellite-streak masking is incomplete and crosstalk masking was not implemented at all in QR2
  processing. Full masking is promised only after the Year-1 (DR1) release.

**PSF FITS-layer header ordering erratum** (§2.2 note + dedicated erratum page): in the original QR1/QR2
release, the PSF cube planes are stored in increasing-x order but "the header incorrectly indicates increasing
y-index," causing software that trusts the header to retrieve the wrong PSF plane. "The error is largest in
two of the corners and can result in a photometry error of +/-5%." Fixed for files processed with pipeline
≥6.5.6; older files (6.4–6.5.5) were corrected at IRSA **as of 2026-03-31** and are marked with a `+psffix1`
suffix in the VERSION header keyword. "Note that this issue does not apply to QR3 or DR1 calibrated images."
A Python tutorial notebook provides code to detect the affected version and fix locally cached files.

**Level 2 Data Quality Assessment (DQA) criteria (§3.2.12)** — automated per-image sanity checks: no pixel
corrected >50% for nonlinearity; per-pixel variance within expected range; ≤20% of pixels flagged PERSIST;
≤1% of pixels in the bad-pixel mask; source count within expected range; masked-pixel count <3× the number of
catalog sources; OUTLIER-flagged pixel count within 2× of other flagged pixels; all required MEF layers
present; all NaN/Inf pixels properly flagged; pixel solid-angle median within expected range; FINAST=0.
"If at least half of the eleven checks above are successful, the image is assigned an overall PASS grade."
**Images are only archived at IRSA if:** N_TRANSIENTS < 435,000, not in the SAA, FINAST=0, and L2DQA=PASS —
meaning "some observations will not include all 6 bands in the archive."

**Flag-usage caution for photometry (§3.3)**: the CONTAINS_BAD_PIXEL (bit 32) summary flag in the L3 catalog
"should only be interpreted as a warning and does not necessarily imply that the measurement should be
excluded from scientific analyses."

**Astrometric caveats**: distortion up to ~13 px (~80″) in detector corners; failures concentrated in
crowded Galactic-plane fields; FINAST=1 means "partial" solution (expect corner offsets of a couple of
pixels), any other nonzero value "should not be used."

**QR2/QR3 combination warning**: "we advise caution when combining QR2 and QR3 data" due to gain-calibration
changes; a dedicated `l3_flux_corrections` product exists to rescale QR2 photometry onto the new gain scale.

**Other explicit "should NOT" instruction**: "science users should NOT combine files from the two releases"
(QR1 and QR2), because the exact file lists differ.

## Acknowledgment / citation text and DOIs

**Official acknowledgment text** (Explanatory Supplement §1.6, and repeated on `overview_qr.html` and the
AWS registry page):
> "This publication makes use of data products from the Spectro-Photometer for the History of the Universe,
> Epoch of Reionization and Ices Explorer (SPHEREx), which is a joint project of the Jet Propulsion
> Laboratory and the California Institute of Technology, and is funded by the National Aeronautics and Space
> Administration."

**DOIs for QR products** (cite "the appropriate" one per `overview_qr.html`):
- QR1: `10.26131/IRSA629` (retired dataset, DOI still citable)
- QR2: `10.26131/IRSA652`
- QR3: `10.26131/IRSA662`
- SPLICES catalog: `10.26131/IRSA554` (cite jointly with Ashby et al. 2023, ApJ,
  [doi:10.3847/1538-4357/acc86b](https://iopscience.iop.org/article/10.3847/1538-4357/acc86b))

**Canonical instrument/pipeline papers** to cite alongside DOIs:
- Bock et al. 2026, ApJ 999(1):139, "The SPHEREx Satellite Mission," doi:10.3847/1538-4357/ae2be2
  (arXiv:2511.02985)
- Akeson et al. 2026, ApJS 285(2):67, "The SPHEREx Image and Spectrophotometry Processing Pipeline,"
  doi:10.3847/1538-4365/ae8843 (arXiv:2511.15823)
- Crill et al. 2020, SPIE 11443, doi:10.1117/12.2567224 (early instrument overview)
- Korngut et al. 2018, SPIE, doi:10.1117/12.2312860 (early instrument design)
- Doré et al. 2014, arXiv:1412.4872, doi:10.48550/arXiv.1412.4872 (mission concept)

## Items that differ from a March-2026 understanding

- **QR3 is new**: released **September 2026** (DOI `10.26131/IRSA662`); a March-2026 snapshot would only
  have known about QR1 (retired Feb 2026) and QR2. The Explanatory Supplement explicitly warns against mixing
  QR2 and QR3 data due to a gain-calibration change, and introduces a new `l3_flux_corrections` calibration
  product specifically to reconcile the two.
- **QR1 retirement**: formally retired from IRSA in **February 2026** — no longer downloadable. A March-2026
  understanding might still expect QR1 files to be present.
- **PSF header-ordering erratum and fix**: the bug is described as already present in QR1/QR2 at launch, but
  the **fix and file relabeling (`+psffix1` suffix) only landed 2026-03-31** — right at/just after a
  March-2026 boundary — so notes from before that date could easily be unaware of the fix or the suffix
  convention.
- **Mosaic Tool / all-sky data-cube documentation**: the Explanatory Supplement's mosaic section (§3.4) was
  only added in **v1.6, dated 2026-05-06** — entirely new relative to March 2026.
- **Major pipeline "R7" and Explanatory Supplement v2.0**: the biggest single documentation change is dated
  **2026-08-25**, rewriting Persistence, Bad-Pixel-Flagging, Fine Astrometry, Outlier Detection, Zodi
  Prediction, Photometric Measurements, PSF, and Spectral Channel sections — none of this would exist in a
  March-2026 snapshot (which would correspond to Supplement v1.4/v1.5, dated 2026-01-23/2026-03-30).
- **New flags added in R7**: BLOOM, SNOWBALL, HALO, SATELLITE_HALO (Source Blooming/Snowball/Transient-Halo
  Flagging, §3.2.1) are new relative to the pre-R7 flag set that a March-2026 snapshot would have known.
- **ePSF replacing the optical-PSF model**: "For R7, we no longer attempt to measure the optical PSF with
  stacking and deconvolution. Instead, we measure the effective PSF (ePSF...)." — a fundamental change in
  the PSF product's meaning, new since R7 (mid-2026).
- **DR1/DR2 terminology and forthcoming release**: DR1 (Year 1 reprocessing, pipeline R7.0–7.2) is described
  as imminent ("late fall 2026") but was **not yet released as of this survey (2026-09-22)** — worth
  rechecking IRSA again around November/December 2026.
- **Comet 3I/ATLAS data product**: an interstellar-comet special-target dataset (August and December 2025
  campaigns) is now linked from the mission landing page — a genuinely new, mission-specific "highlight"
  product that would not have existed in a March-2026 snapshot (the December 2025 epoch postdates it, and
  the page itself appears recently added).

## Open questions / things I could not verify

- **Whether SIA/IBE/S3 collection and path names for QR3 mirror the `spherex_qr2*` / `qr2/` naming pattern**
  (e.g., `spherex_qr3`, `qr3/level2`, etc.). The Archive User Guide (dated 2026-02-18) and the AWS Open Data
  registry entry (last confirmed describing only `qr2/...` prefixes) both predate or do not yet reflect the
  September-2026 QR3 release. The IBE cutout example URL in the official cutout-tool documentation itself
  still uses the older, unversioned `qr` (not `qr2`/`qr3`) path segment
  (`.../ibe/data/spherex/qr/level2/...`), which is inconsistent with the `qr2`-prefixed examples shown
  elsewhere in the Archive User Guide and AWS registry — this naming inconsistency across IRSA's own pages
  could not be resolved from static content alone.
- **Live SIA endpoint behavior**: `https://irsa.ipac.caltech.edu/SIA?COLLECTION=spherex_qr2` timed out (both
  a 60-second WebFetch equivalent attempt and a 30-second curl attempt failed to return a response) during
  this survey, so I could not directly enumerate the current, authoritative list of SIA collections,
  confirm whether new QR3/DR1 collections already exist, or capture example query URLs/response schema.
- **TAP endpoint and table names for SPHEREx** (if any exist — e.g. for the SPLICES catalog or a future L3
  photometry catalog) were not found on any page surveyed; the general `voapi.html` page's static HTML
  contained no SPHEREx content at all (likely populated by client-side JS not executed by WebFetch/curl), and
  no dedicated "SPHEREx TAP" page was linked from the mission landing page.
- **SPHEREx Data Explorer (`/applications/spherex`) functional description**: this is a JavaScript
  single-page app; WebFetch could not render its content, so its exact search/collection UI, filter options,
  and displayed release version could not be confirmed from official text (inferred only indirectly via the
  Archive User Guide's brief mention).
- **AWS S3 bucket completeness for `qr2/` and existence of a `qr3/` prefix**: the AWS Open Data Registry
  listing was truncated mid-fetch after 11 of the (likely >15) product prefixes; crosstalk, zodi-scaling, and
  flux-correction products' exact S3 paths were not individually confirmed, and no `qr1/` (retired) or `qr3/`
  prefix listing was seen at all.
- **`irsatest.ipac.caltech.edu` domain**: the mission landing page links the PSF-erratum notice to a URL on
  this staging/test subdomain, which returned **HTTP 403 Forbidden** when fetched. The production URL
  ([PSF erratum page](https://irsa.ipac.caltech.edu/data/SPHEREx/docs/psfhdrerr.html), HTTP 200) was used instead and appears to carry
  the same content, but I could not determine why the landing page itself points to the non-public staging
  URL — possibly a temporary authoring artifact on IRSA's side.
- **DOI for the Comet 3I/ATLAS data product**: none was found on the dedicated product page.
- **Exact astroquery module/class names and TAP/SIA Python code examples**: referenced by the Archive User
  Guide and tutorial notebooks but not captured in detail here since the tutorial notebook pages
  (`caltech-ipac.github.io/irsa-tutorials/...`) were not deep-dived in this pass (time-boxed; flagged as a
  page to revisit for exact Python usage patterns).
