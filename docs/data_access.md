# Data access

How the SPHEREx data are released, where they live, how to find and fetch the exposures that cover a target,
and what we learned while doing that for 2,225 exposures of six galaxies. The archive changes between
releases; every service name below was verified live on the date given.

## Releases and pipeline versions

Quick Releases (QR) are Level 2 spectral images delivered weekly within about 60 days of acquisition, with
periodic recalibration but no reprocessing. Data Releases (DR) are full reprocessings after each survey year
and add new product types.[^overview][^expsupp2]

| Release | Pipeline | Content and status (verified 2026-11-13) | DOI |
|---|---|---|---|
| QR1 | 6.2.1-6.3.0 | July 2025; retired February 2026, no longer served | 10.26131/IRSA629 |
| QR2 | 6.4.0-6.5.7 | October 2025 to November 2026; superseded by DR1 + QR3. Since DR1 appeared, QR2 is no longer returned by IRSA TAP or SIA searches, but stays downloadable from IBE and S3 (`qr2/`) through February 2027 | 10.26131/IRSA652 |
| QR3 | 7.0.x (R7) | released September 2026; collections `spherex_qr3` (wide survey) and `spherex_qr3_deep`; files tagged `l2b-v27-2026-224`, VERSION 7.0.5 | 10.26131/IRSA662 |
| DR1 | 7.0.5 (R7) | released November 2026: the year-1 exposures reprocessed (`l2b-v27-2026-196`), to be used together with QR3 as one uniformly processed set; plus an all-sky visualisation cube (HEALPix order 5 tiles, 512 x 512 pixels of 12.9 arcsec, 102 channels, DOI 10.26131/IRSA679). No forced-photometry catalogue. Collections `spherex_dr1`, `spherex_dr1_deep`, `spherex_dr1_cube` | 10.26131/IRSA678 |
| DR2 | - | year-2 reprocessing of Surveys 1-4; planned | - |
| HRSC | - | High Reliability Source Catalog, planned July 2027 | - |

Rules stated by the project and what we measured:

- Do not combine QR1 with QR2 files; use caution combining QR2 with QR3 because the absolute gain and the
  spectral calibration changed between them. The `l3_flux_corrections_D<n>` product rescales QR2 photometry
  onto the R7 gain scale and applies to QR2 images only; DR1 images are already on the new scale and must
  not be corrected.[^expsupp2]
- DR1 and QR3 share the same calibration files (ePSF `cal-epsf-v1-2026-191`, v2 for D3; Spectral WCS
  `cal-swcs-v5-2026-191`; Solid Angle Pixel Map `cal-sapm-v3-2026-191`).
- Measured (SED demo, five galaxies with both releases): QR3 / DR1 forced-model fluxes at matched
  wavelengths agree to 1-2 % in every detector with no systematic offset, so the two can be combined without
  a correction (table on the [SED page](sed_extraction.md#dr1-versus-qr3)).
- The R7 pipeline rewrote persistence masking, bad-pixel flagging, fine astrometry, outlier detection, the
  zodiacal-light prediction, photometry and the PSF (now an empirical ePSF).[^expsupp2] QR2 files processed
  with 6.4-6.5.5 had a PSF-cube header-ordering bug (up to 5 % photometric error in two detector corners);
  corrected files carry `+psffix1` in VERSION. Snowball, bloom and halo masking only started with planning
  period 2025W51_1A (pipeline 6.5), so earlier QR2 images are under-flagged.
- Collections appear and disappear without notice (the `spherex_qr2` collections vanished from TAP on
  2026-11-13). Count exposures per collection in every discovery query.

## Where the data are

```{figure} figures/external/akeson2026_PipelineFlow.png
:width: 520px
:alt: Pipeline data flow

*Credit: Akeson et al. 2026 (ApJS 285, 67; arXiv:2511.15823), pipeline flow figure.* From raw downlink through Level 1 (detector corrections), Level 2 (calibrated spectral images, the product that is archived) to Level 3 (forced photometry, mosaics) and Level 4 science products.
```

All public SPHEREx data are served by IRSA (NASA/IPAC Infrared Science Archive) and mirrored in an AWS
Open Data bucket.[^archive]

### Discovery with TAP (preferred: immediate after weekly ingestion)

Endpoint `https://irsa.ipac.caltech.edu/TAP`. Tables verified live on 2026-11-13:

- `spherex.observation`: obsid, `collection` (spherex_dr1, spherex_dr1_deep, spherex_qr3, spherex_qr3_deep),
  intent, metarelease, ipac_pub_date;
- `spherex.plane`: planeid, obsid, productid (D1-D6), `energy_bandpassname` (SPHEREx-D1..D6), `poly`
  (spatial index), time_bounds_lower/upper (MJD), provenance_version, quality_flag, metrics_maglimit,
  metrics_background, energy_resolvingpower, energy_bounds_lower/upper;
- `spherex.artifact`: planeid, `uri` (relative IBE path), contenttype, contentlength;
- `spherex.obscore`: the IVOA ObsCore view (obs_collection, obs_id, s_ra, s_dec, s_region, t_min, t_max,
  access_url);
- `spherex.splices`: the SPLICES ice-target catalogue (about 9 million sources).

The canonical exposure search, from the official cutout notebook:[^tutorials]

```postgresql
SELECT 'https://irsa.ipac.caltech.edu/' || a.uri || '?center={ra},{dec}d&size={size_deg}' AS uri,
       p.time_bounds_lower, p.energy_bandpassname, p.provenance_version, o.collection
FROM spherex.artifact a
JOIN spherex.plane p ON a.planeid = p.planeid
JOIN spherex.observation o ON o.obsid = p.obsid
WHERE 1 = CONTAINS(POINT('ICRS', {ra}, {dec}), p.poly)
  AND o.collection = 'spherex_dr1'
  AND p.energy_bandpassname = 'SPHEREx-D3'
ORDER BY p.time_bounds_lower
```

Measured performance: a `CONTAINS` query against `poly` returns in seconds; `ORDER BY t_min` over a whole
collection in `spherex.obscore` takes minutes; a `GROUP BY` over the full table did not finish in five
minutes. Filter by position or collection first. Footprint queries slowed from about 5 s to about 30 s each
when several of our own jobs queried IRSA at the same time, so archive queries are serialised in our code.

### Discovery with SIA2 (about one day of lag)

```python
from astroquery.ipac.irsa import Irsa

Irsa.list_collections(servicetype="SIA", filter="spherex")
# 2026-11-13: spherex_dr1, spherex_dr1_cube, spherex_dr1_deep, spherex_qr3, spherex_qr3_deep
results = Irsa.query_sia(pos=(coord, 1 * u.arcsec), collection="spherex_qr3")
```

The result carries `access_url`, `energy_bandpassname` and `cloud_access` (JSON with the S3 bucket and key).
The documented `spherex_qr2_cal` collection did not appear in the live list.

### Files and cutouts (IBE)

Root `https://irsa.ipac.caltech.edu/ibe/data/spherex/<dr1|qr3|qr2>/level2/<PlanningPeriod>/l2b-v<ver>-<date>/<det>/<file>.fits`.
Appending `?center=RA,DEC&size=SIZE_DEG` returns a cutout that keeps all extensions; the PSF or ePSF
extension is copied whole (about 4-5 MB per cutout from the IRSA service), and the cutout's position in the
parent frame is recorded in CRPIX1A/CRPIX2A, which is what the ePSF zone selection needs.[^tutorials] Full
frames are about 65-72 MB each; the notebooks set a 120 s remote timeout and retry three times.

### Cloud

Bucket `nasa-irsa-spherex` (us-east-1, anonymous, no egress charge), prefixes `dr1/`, `qr3/`, `qr2/`. In the
Level 2 files IMAGE, VARIANCE and ZODI are uncompressed 2040 x 2040 float32 (HTTP range reads of detector
rows work, 8160 bytes per row per extension); FLAGS is Rice-compressed and must be read whole; the ePSF
table is 3.9 MB. `fits.open('s3://nasa-irsa-spherex/qr3/level2/...', fsspec_kwargs={'anon': True})`
works.[^archive]

### The Data Explorer tools (browser only)

The [SPHEREx Data Explorer](https://irsa.ipac.caltech.edu/applications/spherex) hosts the Spectral Image Search with cutout download,
the Spectrophotometry Tool and the Mosaic Tool. All are job-based (two concurrent jobs per tool, results kept
14 days) and none has a programmatic interface as of 2026-09-22.[^tools] Their algorithms and limits are
described on the [reduction page](reduction_analysis.md#the-official-extraction-tools).

## Calibration products

Per-detector products live under `<release>/<product>/<version-tag>/<det>/` on IBE and in S3. Those that an
extraction needs:[^expsupp4]

| Product | Content | Why |
|---|---|---|
| Spectral WCS `spectral_wcs_D<n>` | CWAVE and CBAND maps (2040 x 2040, um) and the WCS-WAVE table | the science-grade per-pixel wavelength and bandwidth |
| Spectral Channels | the integer channel map and the per-channel table (WAVELENGTH, WL_MIN, WL_MAX, BANDWIDTH, R) | the 102-channel grid of every published spectrum |
| Solid Angle Pixel Map `solid_angle_pixel_map_D<n>` | arcsec^2 per pixel including distortion | converts MJy/sr to flux density; a constant 6.15 arcsec pixel is wrong by -1.7 % to +1.1 % (measured, figure on the reduction page) |
| ePSF `epsf/cal-epsf-v1-2026-191` (v2 for D3) | the zone table with 33 x 33 stamps at 5x oversampling, plus an EPSF_MOSAIC visualisation layer | PSF model; the tutorials use these even for QR2 images |
| `l3_flux_corrections_D<n>` | per-pixel QR2-to-R7 gain scale factors | only for QR2 images |
| `he_template_D<n>`, `aurora_template`, `shuttle_glow_template` | 2040 x 2040 atmospheric emission templates; fit coefficients are in the image headers, the emission is not subtracted | if one models or rejects contaminated exposures |
| `zodi_scaling_v2` | per-band wavelength-dependent rescaling of the Kelsall model | already folded into ZODI; documents the model |
| absolute gain matrix, dark, nonfunc, dichroic, nonlinear_pars, readnoise_pars, gain_factors, sip, xtalk | detector characterisation | already applied or reflected in FLAGS |

## What we actually fetch: cutout bundles with spherex-retrieval

For forced photometry of a galaxy a 41 x 41 pixel cutout (0.07 deg) of every exposure is enough, together
with the six per-detector calibration products. We use hbahk's [spherex-retrieval](https://github.com/hbahk/spherex-retrieval) (MIT licence), which runs the TAP query, downloads the IRSA cutouts,
stops each download after the ePSF extension header, and attaches the calibration ePSF zones, CWAVE, CBAND
and solid-angle cutouts to a small bundle.[^retrieval] Measured in the demo:

| Quantity | Measured |
|---|---|
| bundle size on disk | 0.20 MB (41 x 41 px; 53 x 53 px for the largest galaxy) |
| exposures found per galaxy (DR1 / QR3) | 341 (296/45), 279 (279/0), 418 (283/135), 420 (280/140), 393 (244/149), 374 (259/115) |
| retrieval rate | 2,189 bundles in 5,538 s at two concurrent requests: 2.5 s per cutout (4.4 s in a 36-cutout test) |
| calibration cache | 776 MB once (ePSF, Spectral WCS, Solid Angle Map for six detectors) plus 4 MB for the channel table |
| total for six galaxies | 2,242 bundles, 457 MB |

The limit is the request rate, not the volume. The IRSA cutout service answers 503 under concurrent load, so
concurrency is kept at two with back-off. During the demo IRSA TAP returned 502/503 for about an hour, the
Data Lab TAP (used for the Legacy Survey catalogue) returned a non-VOTable page once, and one cutout
download hung for three hours with no open connection: every network step needs a timeout and a retry, and
an unattended driver must continue with the next target after a failure.

Astropy caches every remote FITS file by default; use `cache=False` for bulk cutouts.

## Third-party software

Twelve public repositories were reviewed in September 2026. Everything written before July 2026 is
hard-coded to the QR2 data model (PSF cube, `MP_*` flag names, seven extensions) and must be checked
against a QR3 file before use; only `spherex-retrieval` and `tractorjax-spherex` dispatch on the PSF kind.
Four repositories have no licence and one is GPL-3; licences are checked before any code is copied. The
public Caltech-IPAC `spherex-pipelines` snapshot (6.5.5) documents the IRSA tool's algorithm but needs the
Rubin Butler middleware to run; it is read as a specification.

## Lessons

- Skills and notes about a live archive rot within months. The `spherex-irsa-access` skill written in
  March 2026 was silent on QR3, the R7 pipeline, the ePSF table, six new flag bits, the flag-keyword scheme,
  the Data Explorer tools and the S3 `qr3/` tree. Re-verify collection names, versions and extension layouts
  against the archive before trusting a note, including these pages.
- The [archive documentation site](https://caltech-ipac.github.io/spherex-archive-documentation/) (dated 2026-02-18)
  lags the Explanatory Supplement by two releases; the Supplement PDF and the IRSA help pages are the primary
  sources. The Data Explorer and the VO API index are JavaScript applications that `curl` cannot read.
- The [Explanatory Supplement v2.1](https://irsa.ipac.caltech.edu/data/SPHEREx/docs/SPHEREx_Expsupp.pdf)
  (2026-11-10) is served without the `_QR` suffix; the older
  [`_QR.pdf` address](https://irsa.ipac.caltech.edu/data/SPHEREx/docs/SPHEREx_Expsupp_QR.pdf) still serves v2.0.
- The official Source Discovery notebook parses flag names from `MP_*` header keywords and breaks on R7
  files; hard-code the flag table ([reduction page](reduction_analysis.md#flags)).
- An untracked file in a Dropbox-synced repository is not safe: a task specification that was moved but not
  committed vanished and reappeared elsewhere. Commit documents with the first checkpoint.
- Python output to a redirected log is block-buffered; use `flush=True` or `python -u` for long jobs.

[^overview]: [IRSA Quick Release overview](https://irsa.ipac.caltech.edu/data/SPHEREx/docs/overview_qr.html)
    and the [IRSA SPHEREx mission page](https://irsa.ipac.caltech.edu/Missions/spherex.html); our [note on the official pages](references/irsa/irsa_spherex_official_pages.md).
[^expsupp2]: SPHEREx Explanatory Supplement v2.0/v2.1, sections 2.1 (releases and pipeline versions) and 4.3.4
    (flux corrections); our [reading note](references/irsa/spherex_explanatory_supplement_v2.0.md).
[^expsupp4]: Explanatory Supplement, section 4 (calibrations) and 4.3.3-4.3.4 (templates and additional
    products).
[^archive]: [SPHEREx Archive User Guide](https://caltech-ipac.github.io/spherex-archive-documentation/), the
    [IRSA cloud access page](https://irsa.ipac.caltech.edu/cloud_access/#spherex) and the
    [AWS Registry of Open Data entry](https://registry.opendata.aws/spherex-qr/); our
    [reading note](references/irsa/spherex_archive_documentation.md). The S3 layout facts were measured on
    2026-09-22 and 2026-11-13.
[^tutorials]: The IRSA SPHEREx tutorial notebooks (introduction, cutouts, PSF, mosaic, source discovery); our
    [reading note](references/irsa/irsa_spherex_tutorials.md).
[^tools]: IRSA Spectrophotometry Tool and Mosaic Tool help pages (saved 2026-09-22 under
    `docs/references/sources/external/`).
[^retrieval]: hbahk, [spherex-retrieval](https://github.com/hbahk/spherex-retrieval) 0.4.0, MIT licence.
