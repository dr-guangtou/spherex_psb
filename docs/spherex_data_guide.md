# SPHEREx data guide for spherex_psb

Living guide to SPHEREx data usage for this project. Last full revision: 2026-09-22; sections 2, 4 and 5
updated for DR1 on 2026-11-13.
Every claim below is traceable to a note in `docs/reference_notes/` (official IRSA pages,
the Explanatory Supplement v2.0, the tutorial notebooks, and the nine papers listed at the
end) or to a live check against the IRSA archive run on 2026-09-22 (`scripts/`).
When something here disagrees with the current IRSA pages or Explanatory Supplement,
the official source wins; fix this file and add a line to `docs/lessons.md`.

Contents

1. Mission and instrument essentials
2. Data releases, pipeline versions, and what is live in the archive
3. The Level 2 spectral image (MEF layout, headers, flags)
4. Calibration and ancillary products
5. Access methods (SIA, TAP, cutouts, S3, Data Explorer tools)
6. Wavelength handling
7. PSF handling
8. Backgrounds and instrument systematics
9. Official extraction tools and their limits
10. How the literature extracts spectra (data and methods only)
11. Recommended strategy for post-starburst galaxies
12. Pitfall checklist
13. Citation and acknowledgment
14. Source index

---

## 1. Mission and instrument essentials

SPHEREx (Spectro-Photometer for the History of the Universe, Epoch of Reionization and
Ices Explorer) is a NASA MIDEX all-sky spectrophotometric survey. Launched 2025-03-12;
science survey started 2025-05-01; nominal 25-month mission with four all-sky surveys
(Surveys 1 and 2 in the first 12.5 months, Surveys 3 and 4 in the second, the latter
offset by half a spectral channel so that the accumulated spectra are Nyquist sampled).
Two Deep Fields near the ecliptic poles get hundreds of visits per channel.

| Quantity | Value | Source |
|---|---|---|
| Aperture | 0.2 m effective pupil, f/3 off-axis triplet, no diffraction spikes | instrument paper |
| Field of view | 11.3 deg x 3.5 deg, split by a dichroic at 2.42 um into SWIR (bands 1-3) and MWIR (bands 4-6) | instrument paper |
| Detectors | six 2048x2048 H2RG, 18 um pixels, 2040x2040 active pixels delivered | ExpSupp |
| Pixel scale | 6.15 arcsec | ExpSupp, live headers |
| Exposure | XPOSURE = 113.5826 s integration, TELAPSE = 118.1873 s; frame cadence 1.5349 s, sample-up-the-ramp (SUR) on board | live headers, instrument paper |
| Dispersion | linear variable filters (LVF): wavelength is set by detector position, iso-wavelength contours are curved ("smile"); one exposure gives one narrow wavelength per sky pixel per band | all sources |
| Spectral channels | 17 nominal channels per band, 102 in total, 0.75-5.0 um | ExpSupp, map-making paper |
| Read noise / dark | <= 18 e- (SWIR), <= 15 e- (MWIR) CDS; dark <= 0.05 e-/s; well depth ~1e5 e- | instrument paper |
| PSF | deliberately undersampled; use N_eff = 1/sum(p_i^2) rather than FWHM; header PSF_FWHM is a median in arcsec (5.2 arcsec in a QR2 D3 file, 7.4 arcsec in a QR3 D3 file, so do not compare across releases blindly) | instrument paper, live headers |
| Per-exposure depth | 5 sigma ~19.5 AB for 0.75-3.8 um, ~17.5-18.5 AB for 3.8-5 um (as quoted by Rustamkulov et al.); per-exposure limits are also in the TAP column `metrics_maglimit` | ref 2607.00543, live TAP schema |

Band definitions (Explanatory Supplement; the live TAP `energy_resolvingpower` gives 41.4 for D2 and 111.6 for D5):

| Band | Range (um) | R | FPA |
|---|---|---|---|
| 1 | 0.75-1.09 | 39 | SWIR, 62 K |
| 2 | 1.10-1.62 | 41 | SWIR |
| 3 | 1.63-2.41 | 41 | SWIR |
| 4 | 2.42-3.82 | 35 | MWIR, 45 K |
| 5 | 3.83-4.41 | 112 | MWIR |
| 6 | 4.42-5.00 | 128 | MWIR |

Adjacent bands overlap by about a quarter channel. Near the 2.42 um dichroic edge the
effective bandpasses of band 3 (long end) and band 4 (short end) are squeezed and shifted;
those rows are flagged DICHROIC when throughput drops below 50% and their calibration is
explicitly called uncertain.

## 2. Data releases, pipeline versions, and what is live in the archive

Quick Releases (QR) are Level 2 spectral images delivered weekly within ~60 days of
acquisition. Data Releases (DR) are full reprocessings after each survey year and will add
catalogs and all-sky cubes.

| Release | Pipeline | Content and status (verified 2026-09-22) | DOI |
|---|---|---|---|
| QR1 | 6.2.1-6.3.0 | July 2025; retired February 2026, no longer served | 10.26131/IRSA629 |
| QR2 | 6.4.0-6.5.7 | October 2025 to November 2026; superseded by DR1 + QR3. Since the DR1 release QR2 is no longer returned by IRSA or VO searches (TAP/SIA collections `spherex_qr2*` are gone) but stays downloadable from IBE and S3 (`qr2/`) through February 2027 | 10.26131/IRSA652 |
| QR3 | 7.0.x (R7) | Released September 2026; collections `spherex_qr3` (wide) and `spherex_qr3_deep`; files `l2b-v27-2026-224`, VERSION 7.0.5. On 2026-11-13 the reference galaxy (RA 168.145, Dec +12.07) has 45 QR3 exposures | 10.26131/IRSA662 |
| DR1 | 7.0.5 (R7) | Released November 2026 (verified 2026-11-13): reprocessed QR2 spectral images (`l2b-v27-2026-196`), meant to be used with QR3 as one uniformly processed set, plus an all-sky cube (HEALPix order 5 tiles of 512x512 pixels of 12.9 arcsec, 102 channels, visualisation grade, DOI 10.26131/IRSA679). No Level 3 forced-photometry catalogue. Collections `spherex_dr1`, `spherex_dr1_deep`, `spherex_dr1_cube` (SIA) and `spherex_dr1_cal` (TAP per the archive guide). Reference galaxy: 296 DR1 exposures | 10.26131/IRSA678 (images) |
| DR2 | - | Year 2 reprocessing (Surveys 1-4) | - |
| HRSC | - | High Reliability Source Catalog, planned July 2027 | - |

Rules stated by the project:
- Do not combine QR1 and QR2 files.
- Use caution combining QR2 and QR3: the absolute gain and spectral calibrations changed.
  A `l3_flux_corrections_D<n>` product (in the `qr3/` and `dr1/` trees, same file
  `cal-flxc-v1-2026-191`) rescales QR2 photometry onto the R7 gain scale. The Explanatory
  Supplement v2.1 (section 4.3.4) says it exists "to allow users to combine QR2 data using the
  previous gains with QR3 data using the new gains": it applies to QR2 images only. DR1 images
  are reprocessed with the new gains and must NOT be corrected. The IRSA Spectrophotometry
  Tool applies the new gains to QR2 data itself.
- Use DR1 + QR3 (and their `_deep` collections) for all current work; count exposures per
  collection in every discovery query, because collections appear and disappear without
  notice (QR2 vanished from TAP on 2026-11-13).
- DR1 and QR3 share the same calibration files: `epsf/cal-epsf-v1-2026-191` (v2 for D3),
  `spectral_wcs/cal-swcs-v5-2026-191`, `solid_angle_pixel_map/cal-sapm-v3-2026-191`.
- Explanatory Supplement v2.1 (2026-11-10) is at
  `https://irsa.ipac.caltech.edu/data/SPHEREx/docs/SPHEREx_Expsupp.pdf` (the `_QR.pdf` URL still
  serves v2.0); it adds section 2.5 on the all-sky cubes.
- QR2 files processed with 6.4-6.5.5 had a PSF-cube header ordering bug (planes stored
  x-fast, header claimed y-fast; up to +/-5% photometric error in two detector corners).
  Files corrected on 2026-03-31 carry `+psffix1` in VERSION; 6.5.6 and later are native
  correct; QR3/DR1 are unaffected because the PSF product changed (Section 7).
- The R7 pipeline (QR3, DR1) rewrote persistence masking, bad-pixel flagging, fine
  astrometry (with retry keywords WCSRETRY, RETRY_WCSMODE, WCSSEED), outlier detection,
  zodi prediction, photometry, and PSF (now an empirical ePSF).
- Snowball/bloom/halo masking only started with planning period 2025W51_1A (December
  2025, pipeline 6.5): QR2 images before that have those artifacts unmasked, satellite
  streak masking is incomplete, and crosstalk masking was absent in QR2. Rustamkulov et al.
  note "at least half" of their QR2 exposures are under-flagged for this reason.

## 3. The Level 2 spectral image

One MEF per pointing per detector (6 per pointing), ~67-72 MB, 2040x2040 pixels, name
`level2_<PlanningPeriod>_<LargeSlew>_<SmallSlew>D<det>_spx_l2b-v<ver>-<yyyy>-<doy>.fits`,
e.g. `level2_2026W31_1B_0205_1D3_spx_l2b-v27-2026-224.fits`. Cutouts (Section 5) keep the
same extensions with IMAGE/FLAGS/VARIANCE/ZODI trimmed and WCS-WAVE remapped.

| HDU | QR2 (v6.x) | QR3 (v7.x) | Notes |
|---|---|---|---|
| 0 PRIMARY | VERSION keyword only | same | check VERSION (string, may carry `+psffix1`) |
| 1 IMAGE | MJy/sr, float32 | same | not zodi-subtracted; full astrometric WCS with SIP; alternate WCS `A` (0-based pixel coords, CRPIX1A/CRPIX2A give cutout offset) and `W` (wavelength lookup) |
| 2 FLAGS | int32 bitmask; bit names in header as `MP_<NAME> = bit` | int32 bitmask; bit names as `MSKN####`/`MSKM####`/`MSKD####` triplets | header keyword scheme changed between releases; hard-code the canonical table below and only use the header for cross-checks |
| 3 VARIANCE | (MJy/sr)^2 | same | Robberto (2007) SUR noise model plus an empirical excess-noise term; airglow lines are included in the variance |
| 4 ZODI | MJy/sr model | same, header ZODIMDL = KEL98_WAVESCL_V1 | not subtracted from IMAGE |
| 5 PSF | ImageHDU cube (121, 101, 101), OVERSAMP = 10, 11x11 zones, XCTR_i/YCTR_i keywords | replaced by EPSF | see Section 7 |
| 5 EPSF | absent | BinTableHDU, 441 rows (21x21 zones) for D1,2,4,5,6 and 451 rows (11x41) for D3; columns BINX, BINY, XCENTER, YCENTER, XWIDTH, YWIDTH, NSTAR, NEFF_MEAN, CWAVE, CBAND, EPSF(33x33); OVSMPX = OVSMPY = 5 | ePSF, Anderson and King formalism, unit integral |
| 6 WCS-WAVE | BinTable 1 row x 3 cols (X, Y, VALUES) | same | WAVE-TAB lookup; visualization grade (~1 nm); use CWAVE/CBAND for science |

Useful IMAGE header keywords (verified live): DETECTOR, OBSID, FINAST (0 = good fine
astrometry; images are only archived with FINAST = 0), L2DQAFLG (`Pass`), PSF_FWHM
(arcsec, median), XPOSURE, TELAPSE, MJD-AVG, and HIERARCH counters `L2 N_<FLAG>` for every
flag plus `L2 SATSTRKS`, `L2 N_XTALK`, `L2 N_HALO`. Level 2 images are only released if
N_TRANSIENTS < 435,000, the exposure is outside the SAA, FINAST = 0 and the 11-check DQA
passes, so some pointings lack some bands.

Canonical FLAGS bit table (Explanatory Supplement v2.0 Table 16, IRSA help page, live headers):

| Bit | Name | Meaning | Science use |
|---|---|---|---|
| 0 | TRANSIENT | transient (cosmic ray, satellite, bloom spill) during SUR; first ~10 s not always caught | exclude |
| 1 | OVERFLOW | half-well overflow threshold reached | exclude for photometry (Lee et al.), propagated only by the mosaic tool |
| 2 | SUR_ERROR | on-board checksum/processing error | exclude |
| 4 | PHANTOM | phantom pixel (QR2 header only) | not sky |
| 5 | REFERENCE | reference pixel (QR2 header only) | not sky |
| 6 | NONFUNC | permanently dead | exclude |
| 7 | DICHROIC | band 3/4 dichroic corner, throughput < 50% | exclude; calibration uncertain |
| 9 | MISSING_DATA | lost on-board data | exclude |
| 10 | HOT | hot in this exposure | exclude |
| 11 | COLD | anomalously low | exclude |
| 12 | FULLSAMPLE | rotating 8x32 full-readout region | exclude |
| 13 | SUR_MISMATCH | listed on the tool help page; not in the public table | treat as bad |
| 14 | PHANMISS | phantom correction not applied | exclude |
| 15 | NONLINEAR | nonlinearity correction unreliable | exclude |
| 16 | VAR_UNDER | listed on the tool help page; not in the public table | caution |
| 17 | PERSIST | persistent charge above threshold | exclude |
| 18 | PERSIST_UNK | listed on the tool help page; not in the public table | caution |
| 19 | OUTLIER | Detect Outlier Pixels module | exclude for photometry; mosaic tool propagates only |
| 20 | CROSSTALK | electrical crosstalk (R7) | exclude |
| 21 | SOURCE | pixel mapped to a Reference Catalog source | informational; the target itself is flagged |
| 22 | GHOST | optical ghost from a bright source in the frame | exclude |
| 23 | GHOST_FPA | ghost from another detector; currently unused | - |
| 24 | GHOST_EXT | ghost from a source outside the FOV; in development | exclude |
| 25 | STREAK | satellite/asteroid streak | exclude |
| 26 | BLOOM | charge bloom from a bright source (R7, and QR2 from 2025W51) | exclude |
| 27 | SNOWBALL | large charge-release event | exclude |
| 28 | HALO | halo of a transient | exclude |
| 29 | SATELLITE_HALO | halo of a satellite streak | exclude |
| 32 | CONTAINS_BAD_PIXEL | Spectrophotometry tool output only: some pixel in the fit had a flag | warning |
| 33 | FIT_ERROR | Spectrophotometry tool output only: Tractor did not converge | exclude |

A measurement with flags = 0 or flags = 2097152 (SOURCE only) used only nominal pixels.
The set the official tools drop from fits is SUR_ERROR, NONFUNC, MISSING_DATA, HOT, COLD,
NONLINEAR, PERSIST, BLOOM, SNOWBALL, HALO, SATELLITE_HALO; the mosaic tool additionally
drops TRANSIENT, DICHROIC, PHANMISS, CROSSTALK, GHOST*, STREAK and propagates OVERFLOW,
SOURCE, OUTLIER. Lee et al. (compact galaxies) keep only flags 0 or 2097152 and reject
bits 0, 1 and 7.

## 4. Calibration and ancillary products

Per-detector products live under `<release>/<product>/<version-tag>/<det>/` on IRSA IBE
and in S3 (`s3://nasa-irsa-spherex/`). Live S3 prefixes on 2026-09-22:

- `qr2/`: abs_gain_matrix, average_psf, dark, dichroic, gain_factors, level2, nonfunc,
  nonlinear_pars, readnoise_pars, sip, solid_angle_pixel_map, spectral_channels,
  spectral_wcs.
- `qr3/`: abs_gain_matrix, aurora_template, dark, dichroic, epsf, gain_factors,
  he_template, l3_flux_corrections, level2, nonfunc_v2, nonlinear_pars, readnoise_pars,
  shuttle_glow_template, sip, solid_angle_pixel_map, spectral_channels, spectral_wcs,
  xtalk_class1, xtalk_class2, zodi_scaling_v2.

Products that matter for spectrum extraction:

| Product | Content | Why we need it |
|---|---|---|
| Spectral WCS (`spectral_wcs_D<n>`) | CWAVE and CBAND 2040x2040 maps (um) plus WCS-WAVE table | the science-grade per-pixel wavelength and bandwidth; CWAVE is the 50% point of the cumulative per-pixel transmission, CBAND = CWAVE/R |
| Spectral Channels (`spectral_channels_<date>.fits`) | 2040x2040 integer map assigning pixels to the 17 nominal channels (0 and 18 = off-nominal corners) plus a table of per-channel WAVELENGTH, WL_MIN, WL_MAX, BANDWIDTH, R, R_STD | defines the standard 102-channel grid used by the mosaic tool and by every published spectrum |
| Solid Angle Pixel Map (`solid_angle_pixel_map_D<n>`) | arcsec^2 per pixel, includes distortion | converts MJy/sr to flux density; the official tools use it instead of a constant 6.15^2 |
| ePSF (`qr3/epsf/…`) or Exposure-Averaged PSF (`qr2/average_psf/…`) | standalone copies of the PSF products, the ePSF file adds an EPSF_MOSAIC visualization layer | the tutorial uses the QR3 ePSF files even for QR2 images and tells users not to use the old QR2 PSF |
| Absolute Gain Matrix | (MJy/sr)/(e-/s), combined flat field and gain, wavelength dependent | provenance only; already applied |
| Dark, nonfunc, dichroic, nonlinear_pars, readnoise_pars, gain_factors, sip | detector characterization | already applied or already reflected in FLAGS |
| zodi_scaling_v2 (ECSV) | per-band wavelength-dependent rescaling of the Kelsall model | already folded into the ZODI extension; useful to understand the model |
| aurora_template, he_template (bands 1-2), shuttle_glow_template | 2040x2040 atmospheric emission templates; fit coefficients are in image headers but emission is not subtracted | needed if we model or reject airglow-contaminated exposures ourselves |
| l3_flux_corrections_D<n> | per-pixel scale factors from the QR2 gains to the R7 (QR3/DR1) gains | apply to QR2 images only, never to DR1 or QR3 |
| xtalk_class1/2 (ECSV) | crosstalk parameters | provenance |

## 5. Access methods

### 5.1 Discovery with TAP (immediate after weekly ingestion, preferred)

Endpoint `https://irsa.ipac.caltech.edu/TAP`. Tables verified live:

- `spherex.observation` (obsid, `collection` = spherex_dr1 / spherex_dr1_deep / spherex_qr3 / spherex_qr3_deep as of 2026-11-13 (the spherex_qr2 collections were removed when DR1 appeared), observationid, intent, metarelease, ipac_pub_date)
- `spherex.plane` (planeid, obsid, productid = D1..D6, `energy_bandpassname` = SPHEREx-D1..D6, `poly` spatial index, time_bounds_lower/upper (MJD), provenance_version (pipeline version), quality_flag, metrics_maglimit, metrics_background, position_resolution, energy_resolvingpower, energy_bounds_lower/upper)
- `spherex.artifact` (planeid, `uri` relative IBE path, contenttype, contentlength)
- `spherex.obscore` (IVOA ObsCore view: obs_collection, obs_id, s_ra, s_dec, s_region, t_min, t_max, obs_publisher_did, access_url = DataLink)
- `spherex.splices` (SPLICES ice-target catalog, ~9 M sources, DOI 10.26131/IRSA554)

Canonical exposure search (from the official cutout notebook, verified live):

```sql
SELECT 'https://irsa.ipac.caltech.edu/' || a.uri || '?center={ra},{dec}d&size={size_deg}' AS uri,
       p.time_bounds_lower, p.energy_bandpassname, p.provenance_version, o.collection
FROM spherex.artifact a
JOIN spherex.plane p ON a.planeid = p.planeid
JOIN spherex.observation o ON o.obsid = p.obsid
WHERE 1 = CONTAINS(POINT('ICRS', {ra}, {dec}), p.poly)
  AND o.collection = 'spherex_qr2'
  AND p.energy_bandpassname = 'SPHEREx-D3'
ORDER BY p.time_bounds_lower
```

Performance notes from the live checks: `CONTAINS` against `poly` returns in seconds;
`ORDER BY t_min` over a whole collection in `spherex.obscore` takes minutes; `GROUP BY`
over the full table did not complete within 5 minutes. Filter by position or collection
first.

### 5.2 Discovery with SIA2 (about one day lag)

```python
from astroquery.ipac.irsa import Irsa

Irsa.list_collections(servicetype="SIA", filter="spherex")
# 2026-11-13: spherex_dr1, spherex_dr1_cube, spherex_dr1_deep, spherex_qr3, spherex_qr3_deep
results = Irsa.query_sia(pos=(coord, 1 * u.arcsec), collection="spherex_qr3")
```

Result columns include `access_url`, `energy_bandpassname`, `cloud_access` (JSON with the
S3 bucket and key). The documented `spherex_qr2_cal` collection did not appear in the live
list. Raw endpoint: `https://irsa.ipac.caltech.edu/SIA?COLLECTION=spherex_qr3&POS=circle+RA+DEC+RADIUS`.

### 5.3 Direct files and cutouts (IBE)

Root `https://irsa.ipac.caltech.edu/ibe/data/spherex/<dr1|qr3|qr2>/level2/<PlanningPeriod>/l2b-v<ver>-<date>/<det>/<file>.fits` (DR1: `l2b-v27-2026-196`; QR3: `l2b-v27-2026-224`).
Append `?center=RA,DEC&size=SIZE_DEG` (the notebooks write `center=RA,DECd`) for a cutout.
Cutouts preserve all six HDUs; the PSF/EPSF extension is copied whole, so map cutout
pixels back to the parent frame with CRPIX1A/CRPIX2A before choosing a PSF zone. Full
frames take long enough that the notebooks set `astropy.utils.data.conf.remote_timeout = 120`
and wrap `fits.open` in a 3-attempt retry; use `cache=False` for large batches.

### 5.4 Cloud

Bucket `nasa-irsa-spherex`, region us-east-1, anonymous access, no egress charge. Top-level prefixes `dr1/`, `qr3/`, `qr2/`. In DR1 and QR3 L2 files IMAGE, VARIANCE and ZODI are uncompressed 2040x2040 float32 (HTTP range reads of detector rows work, 8160 bytes per row per extension); FLAGS is RICE-compressed (11.5 MB, read whole); EPSF is a 3.9 MB table; a file is ~65 MB. The IRSA cutout service returns ~4-5 MB per cutout because it copies EPSF whole; spherex-retrieval avoids that by closing the stream after the EPSF header.
`fits.open('s3://nasa-irsa-spherex/qr3/level2/...', fsspec_kwargs={'anon': True})` works;
the AWS registry page still only documents the `qr2/` tree. The official Source Discovery
notebook is the reference for the S3 pattern and for the NASA Fornax platform setup.

### 5.5 SPHEREx Data Explorer (GUI only)

`https://irsa.ipac.caltech.edu/applications/spherex` hosts three tools, all job-based with
a Job Monitor that keeps results 14 days and a limit of two concurrent jobs per tool:

- Spectral Image Search with cutout download.
- Spectrophotometry Tool (`/applications/spherex/tool-spectrophotometry`), Section 9.
- Mosaic Tool (`/applications/spherex/tool-mosaic`), Section 9.

There is no programmatic API for either tool as of 2026-09-22 (the mosaic notebook says so
explicitly; the spectrophotometry help describes manual upload of at most 20 targets).
Jobs are UWS jobs, so a URL exists per job, but batch submission is not documented.

## 6. Wavelength handling

- Every detector pixel has its own central wavelength and bandwidth. The wavelength at
  which a galaxy is measured is set by where it falls on the detector in each exposure, so
  a resolved galaxy is measured at slightly different wavelengths across its own extent in
  one exposure, and at different wavelengths in different exposures.
- For science use the CWAVE/CBAND maps from the Spectral WCS product (per band); QR3
  EPSF rows also carry CWAVE/CBAND per zone. The in-file WCS-WAVE table (alternate WCS key
  `W`) is a bilinear approximation good to ~1 nm and is fine for bookkeeping. When loading
  it with astropy, pass the HDUList (`WCS(header, fobj=hdulist, key='W')`) and set
  `wcs.sip = None` (astropy issue 13105), then `pixel_to_world(x, y)` returns
  (wavelength, bandwidth).
- The wavelength progression within a band is exponential in the position along the
  filter so that R is constant; residuals of the lab calibration are 0.26% (1 sigma),
  worst near the 2.42 um dichroic edge.
- The Spectral Channels template is a geometric survey-planning channelization, not a
  wavelength solution; its per-channel table gives median lambda_c, [lambda_min,
  lambda_max] and R per band and channel (Explanatory Supplement Tables 29-34; edge
  channels 0 and 18 have anomalous R). R7 shifted the band 5 and 6 wavelength solution
  from on-sky calibration, so do not mix band 5/6 channel definitions across pipeline
  versions. The Spectrophotometry Tool switched to the QR2 CWAVE values on 2025-12-17.
- Standard grid: the 102 nominal channels from the Spectral Channels product. Published
  spectra are placed on this grid by error-weighted averaging of all measurements whose
  CWAVE falls in a channel (Gagne et al.), or by interpolating each object's irregular
  sampling onto the grid (Lee et al.). Bands 5-6 have about three times finer sampling
  than bands 1-4, so cross-detector rebinning is needed before joint fitting.
- With one survey per year-half, a given position has of order one measurement per
  channel per survey outside the deep fields; the Explanatory Supplement notes that
  Surveys 3-4 are offset by half a channel to reach Nyquist sampling.
- The He I 1.083 um airglow line sits in bands 1-2 and is 3-30 times brighter than the
  zodiacal light; it also leaks to features near 0.84 um (band 1) and 1.25/1.49 um (band 2).
  Published map work drops the four affected channels.

## 7. PSF handling

- QR2 (VERSION 6.x): `PSF` ImageHDU cube of 121 stamps (11x11 zones), 101x101 at 10x
  oversampling (0.615 arcsec per oversampled pixel). Zone centres are keywords XCTR_i,
  YCTR_i (i = 1..121, 0-based parent-frame pixels); the plane index is i-1. Files with
  VERSION 6.4-6.5.5 without `+psffix1` need the header-order fix (planes are x-fast). The
  September 2026 tutorial advises not to use these PSFs at all and to take the QR3 ePSF
  calibration files from S3 instead (`qr3/epsf/cal-epsf-v1-2026-191/<det>/epsf_D<n>_spx_cal-epsf-v1-2026-191.fits`, v2 for D3).
- QR3 (VERSION 7.x): `EPSF` binary table, one row per zone (21x21 for most detectors,
  11x41 for D3 because of birefringence near the dichroic), each stamp 33x33 at 5x
  oversampling, unit integral, with XCENTER/YCENTER/XWIDTH/YWIDTH, NSTAR, NEFF_MEAN,
  CWAVE, CBAND. Pick the row whose (XCENTER, YCENTER) is nearest to the parent-frame pixel
  position of the target; header keyword ORDERING = 'x-fast then y'. DETCOORD = 'sky'
  means MWIR stamps are flipped in x to match the SWIR view.
- The ePSF is empirical (Anderson and King), so it already includes inter-pixel
  capacitance and pixel response. For forward modeling (Tractor style) it must be shifted
  to the sub-pixel phase of the source, integrated onto native pixels, and renormalized;
  passing the oversampled stamp directly gives wrong widths and normalizations. The
  tutorial does this with `photutils.psf.ImagePSF(data, oversampling=(OVSMPY, OVSMPX))`.
- Image quality is quantified with N_eff, which grows with wavelength and depends on the
  sub-pixel phase; PSF wings are stronger than pre-launch optical models, so bright
  sources need larger masks. Reprojection in mosaics widens the effective PSF by ~1.6x
  (0.9 um) to ~1.3x (4.7 um) for binning.
- The cutout service does not trim the PSF/EPSF extension; the target position in the
  parent frame is `x_orig = 1 + x_cutout - CRPIX1A` (0-based astropy pixels).

## 8. Backgrounds and instrument systematics

Everything in this section is present in the delivered IMAGE unless stated otherwise.

Zodiacal light (ZL)
- Dominant background and the dominant noise term at all wavelengths. Live medians of the
  ZODI extension: 0.084 MJy/sr in a band 3 image near M101 (ecliptic latitude ~ +60 deg)
  and 0.35 MJy/sr in a band 3 image at ecliptic latitude ~ 0 deg.
- The ZODI extension is a modified Kelsall et al. (1998) model with the Tsumura et al.
  (2013) spectral shape, rescaled per wavelength against SPHEREx |b| > 30 deg data because
  the raw model underestimates the amplitude (`zodi_scaling_v2`; header ZODIMDL =
  KEL98_WAVESCL_V1). It tracks spatial and temporal variation but is a model, not a fit to
  the image.
- It is NOT subtracted from IMAGE. The Spectrophotometry Tool does not use it at all: it
  subtracts a local background from a 15-pixel box around each source (masking known
  sources) and, in the Level 3 pipeline, first a global spectral background then a local
  15x15 background fitted simultaneously with the flux. The mosaic tool subtracts
  IMAGE - ZODI before coadding. The map-making paper prefers a "contour filter" (mean
  subtraction within thin LVF iso-wavelength bins ~1 pixel high) or a mosaic-level fit of a
  scaled zodi template plus monopole.
- For a galaxy smaller than a few arcminutes, a local annulus or 2D background
  (photutils Background2D, sep) around the object is what all published extractions do.
  Subtracting ZODI first reduces the dynamic range and removes the smooth spectral shape
  of the zodi, but a residual local sky must still be fitted.

Atmospheric emission (present, not subtracted, included in VARIANCE)
- He I 1.083 um airglow in every exposure (bands 1-2), with leak features.
- Auroral N2 lines (bands 1-2, sometimes 3-5), correlated with solar activity and polar
  passes.
- Other lines listed at 0.78, 0.84, 0.93, 1.13, 1.81, 2.63, 2.75, 4.03, 4.64 um.
- Shuttle glow (atomic oxygen on baffle paint) peaking near 3.0 and 4.5 um, RAM-angle
  dependent; survey now keeps RAM < 70 deg but residuals remain and the recommended
  mitigation is rejecting affected exposures using redundancy. Templates are provided
  (`shuttle_glow_template`, `aurora_template`, `he_template`) with fit coefficients in
  the headers.
- Earthshine at LZA > 24 deg, measured at 0.05 e-/s at LZA = 42 deg, ~40x below ZL,
  short-wavelength weighted.

Optical and electronic artifacts (Explanatory Supplement 2.3)
- Frame-edge triangular ghosts from sources just outside the FOV; linear ghosts from very
  bright sources above/below the detector (stronger at long wavelengths); ~10 arcmin
  beam-splitter ghost disks from very bright sources (bands 3-6, strongest near the 3/4
  boundary); an "8 degree ghost" from very bright stars ~8 deg away (bands 2-6); Moon
  stray light at left/right edges in bands 1, 4, 5, 6. GHOST/GHOST_EXT flags are still in
  development.
- Cosmic rays: single-pixel hits are removed on board; extended hits, snowballs (core
  OVERFLOW+TRANSIENT plus halo), halos and a faint cosmic-ray-induced glow (red gradient
  in bands 1-2, edge rim in 4-6) remain. About 1% of exposures show diffuse optical
  transients. Satellite streaks near the noise level may be unflagged.
- Crosstalk: negative images displaced 32 rows, smearing in the last-read pixel of the
  previous row, and channel crosstalk at multiples of 64 columns (flagged from R7 only).
- Persistence: multi-exponential charge-trap model; PERSIST flag; snowballs and large
  cosmic rays leave excess persistence. Exposures within 5 deg of the Moon were avoided
  during commissioning for this reason.
- Blooming around bright stars triggers early-transient flags over a larger footprint than
  expected; ZEROSLOPEON is disabled in flight so those pixels keep their pre-trigger slope.
- Source masks are sized from Reference Catalog magnitudes (double-exponential radius
  versus magnitude, faint limit 19 AB) and can be too large or too small (listed as a
  known limitation). Only unresolved or compact sources (Reference Catalog
  `spherex_class` <= 7) are masked; large resolved galaxies are NOT source-masked, so a
  pipeline background estimate that assumes SOURCE-free pixels are empty sky will include
  the outskirts of a resolved target.
- Exposure-level atmospheric diagnostics exist only in R7 (QR3) headers, verified live:
  `HE_AIRGLOW_CONT` (True for detectors 1-2), `AURORA_CORR` and `AURORA_CONT` (True if the
  correlation with the aurora template exceeds 0.2), `SHUTTLE_GLOW_CORR` and
  `SHUTTLE_GLOW_CONT` (same 0.2 threshold). QR2 headers do not carry them. Also present in
  both: `SGT_MIN_GCD2SAA` (ground-track distance to the SAA), L1DQAFLG, L2DQAFLG.
- Ghost masking thresholds: DBS ghosts are modelled only for sources above 100 Jy
  (band 3 edge region), 3000 Jy (band 4 main field) and 10,000 Jy (bands 5-6);
  frame-edge ghosts only for m_AB <= 11. Fainter ghost producers are not masked.
- Astrometry: RMS < 0.3 arcsec for FINAST = 0; distortion up to ~13 pixels (80 arcsec) in
  corners, captured by the SIP terms; ~3% of images failed fine astrometry before R7, < 1%
  after the retry logic; failures cluster in crowded fields.

Calibration accuracy
- Absolute gain is derived from ~54,000 measurements of 17 CALSPEC standards; the
  Explanatory Supplement quotes < 1% relative to CALSPEC for most channels. Users report
  larger effective floors: QR2 gain reliability of <= 3% (bands 1-4) and <= 5% (bands
  5-6) plus a 3% visit-to-visit RMS added in quadrature (Rustamkulov et al.; the Level 3
  pipeline adds the same 3% in quadrature to catalog errors); an 8% absolute floor
  recommended by Gagne et al. from a JWST comparison; ~4% median offset versus SDSS z and
  3.5% versus WISE W1 for compact galaxies (Lee et al.). Two papers state that tool
  uncertainties look underestimated (Davies et al., Stepney et al.).
- The 3/4 dichroic channels and the four He-contaminated channels are routinely dropped.
- Rice compression quantizes pixel values at half the expected noise; irrelevant for
  aperture sums but worth knowing.

## 9. Official extraction tools and their limits

Spectrophotometry Tool (IRSA help page saved in `docs/reference_notes/external/`)
- Tractor forced photometry at user positions; only the flux amplitude is fitted. Two
  morphologies: point source, or Sersic profile with fixed n (0.5-6), b/a, PA (east of
  north) and Re (1-20 arcsec; below 1 arcsec is treated as a point source). Larger galaxies
  cannot be modelled.
- Inputs: IMAGE, FLAGS, VARIANCE, PSF/EPSF, Solid Angle Pixel Map. ZODI is not used.
  Background: local estimate from a 15-pixel box with known sources masked, subtracted
  before the fit; returned as `flux_bkg` and documented as occasionally problematic (look
  for jumps between adjacent wavelengths).
- Output table: wavelength, flux (uJy), flux_err, lambda_width, flags (bitmask including
  bits 32 and 33), fit_ql (mean |data - model|/sigma within 2.5 pixels; ~1 is good),
  flux_bkg, lvf_id, det_id, deep_flg, mjd, data_collection (qr2 or qr3), x_image, y_image.
  Pixels with SUR_ERROR, NONFUNC, MISSING_DATA, HOT, COLD, NONLINEAR, PERSIST, BLOOM,
  SNOWBALL, HALO, SATELLITE_HALO are ignored in the fit. DICHROIC and FIT_ERROR points
  should be discarded.
- Throttles: 20 sources per job, 2 concurrent jobs, run time ~1.67 s per image + 50 s;
  sources near the ecliptic poles can have ~2e4 measurements. Deep Field frames are
  optional. Companions must be supplied explicitly to be deblended (sources within the
  15-pixel background box are known to the tool and need not be listed).
- Used as the extraction engine by Lee et al. (compact SDSS galaxies), Rustamkulov et al.
  (brown dwarfs), Stepney et al. and Davies et al. (quasars). Gagne et al. built their own
  equivalent (SPIFF) to allow the position to float and to sample posteriors.

Mosaic Tool
- Cube of the 102 nominal channels (or a subrange) over up to 5x5 deg, pixel >= 6.15
  arcsec (default 9), TAN projection, all-sky-survey images only (Deep Field frames
  excluded for now). Steps: IMAGE - ZODI, mask the exclusion flag list, assign pixels to
  channels with the Spectral Channels template, reproject by intensity-weighted binning,
  average. Output HDUs IMAGE (MJy/sr), NHITS, FLAGS (OR of OVERFLOW/OUTLIER/SOURCE), plus
  SPECTRAL_CHANNELS and WCS-WAVE tables. The Explanatory Supplement recommends the L2
  images, not mosaics, for precision photometry; striping from airglow lines and from
  sharp spectral features under multi-roll coaddition does not average down.
- The official mosaic notebook extracts a quick-look spectrum with photutils circular
  aperture and sigma-clipped annulus, converting MJy/sr to mJy with
  23.5045 x (pixel scale in arcsec)^2 / 1000, and states it does not compute errors.

Spectral Image Cutouts, Source Discovery notebook, MOST
- Cutouts: Section 5.3. Source Discovery (`spherex_source_discovery_tool` in the tutorial
  repo) is the only official code that builds a flux+variance+flag spectrum from many
  cutouts with aperture photometry at several radii and a 7-16 pixel annulus, reading the
  flag names from the QR2 `MP_*` header keywords (this will break on QR3 headers). MOST
  supports SPHEREx for moving objects since June 2026.

## 10. How the literature extracts spectra (data and methods only)

| Paper | Targets | Data path | Extraction | Background | Combination and errors |
|---|---|---|---|---|---|
| Gagne et al. 2026 (2604.22012, SPIFF) | 6003 ultracool dwarfs, point sources, high proper motion | QR2 cutouts 20x20 px via SIA2 and S3 | own PSF fit with calibration PSF shifted and box-summed to native pixels; position free; scipy then ultranest posteriors; also aperture photometry at 18 radii | median in a 15-pixel box with bad pixels and known stars masked; no ZODI | wavelength evaluated at the fitted position; error-weighted mean into the 102 channels; templates by median with chi2 rescaling; 8% absolute floor from a JWST prism comparison |
| Hora et al. 2026 (2603.12390, Cygnus X ices/PAH) | extended ISM | QR2 L2 images; ~50-150 exposures per position | slice each L2 image by per-pixel wavelength into narrow windows, reproject, sigma-clip average (>= 3 samples), interpolate continuum between line-free windows; Tractor forced photometry for compact sources; custom aperture tool with hand-picked sky region | local only; no ZODI | LVF "banding" corrected with JWST-calibrated simulations; peak depths underestimated at R ~ 35-130 |
| Lee et al. 2026 (2607.18048, compact SDSS galaxies vs SPS models) | 3889 galaxies with Petrosian r < 3.1 arcsec, i_fiber < 20 | IRSA Spectrophotometry Tool, point-source mode, positions fixed to SDSS, QR2 pipeline >= 6.4, extracted 2026-04/05 | keep flags 0 or 2097152; reject bits 0, 1, 7; require >= 10 valid points per band; resample to the 102-channel grid with the standard response curves | tool default 15-pixel box | scale each spectrum to SDSS z via synthetic photometry (median 4% offset, reject > 20%); fiber-to-model aperture correction on the SDSS side; rest-frame median stacks by age and metallicity; 10% model floor in fit weights; kinematics agree with SDSS to ~8 km/s |
| Rustamkulov et al. 2026 (2607.00543, brown dwarfs) | 37 point sources | Spectrophotometry Tool with the corrected PSF (April 2026), QR2 | point-source Tractor; reject any flag other than SOURCE; 4 sigma clip from a running median; reject targets with contaminators within 3 pixels or extended appearance | tool local box, global fallback | 3% visit-to-visit RMS added in quadrature; gain reliability <= 3% (bands 1-4), <= 5% (5-6); half the data under-flagged |
| Stepney et al. 2026 (2605.06791, reddened quasars) | 404 candidates, point sources | Spectrophotometry Tool, point source, 15-pixel background | mask bad pixels; S/N > 5 channels only; median-filter continuum (29 channels) with edge reflection; cross-correlation redshifts | tool | drop targets with a K-band neighbour within 6 arcsec; tool errors "likely underestimated" |
| Davies et al. 2026 (2603.10135, z > 4 quasars) | ~4900 Gaia/CatWISE candidates | Spectrophotometry Tool in batches of 20 | point-source Tractor; deblend with CatWISE positions within 25 arcsec; Galactic extinction correction (SF11 map, F99 curve) | tool | rebin D1-D4 and D5-D6 onto a common grid; negative fluxes for close blends at short wavelengths; errors "show indications of being underestimated" |
| Cukierman et al. 2026 (2603.25790, map making) | diffuse and resolved | L2 images with FINAST = 0 | binning reprojection, per-pixel hit count and mean wavelength, narrowband sub-channel cubes with monotonic cubic spline interpolation to suppress banding, linear continuum subtraction from flanking channels | contour filter (mean per LVF wavelength bin) or mosaic-level zodi template deprojection | no universal variance; survey-1 vs survey-2 difference maps; aperture spectra with random-sky-aperture scatter as the error (Cat's Eye Nebula) |
| Akeson et al. 2026 (2511.15823, pipeline) | - | - | Level 3: Tractor forced photometry in 15x15 boxes at Reference Catalog positions, blend-covariance errors, Solid Angle map to uJy; optional galaxy morphology | global spectral zodi fit + Background2D (or local 15x15 near the plane) | Secondary catalog = average over surveys on a fixed grid; HRSC needs S/N > 10 in >= 5 channels |

## 11. Recommended strategy for post-starburst galaxies

Three regimes, decided per object from the optical image (Petrosian or effective radius
versus the 6.15 arcsec pixel and the wavelength-dependent PSF):

1. Unresolved (Re < ~3 arcsec, no neighbour within ~20 arcsec). Use the Spectrophotometry
   Tool in point-source mode as the baseline (20 targets per job, 2 jobs at a time), keep
   flags 0 / 2097152, drop DICHROIC and FIT_ERROR points, inspect flux_bkg for jumps, add
   a 3% visit-to-visit term in quadrature, apply an absolute floor of 3-8% when comparing
   to models, and validate against 2MASS/WISE/SDSS synthetic photometry as Lee et al. did.
   Reproduce the same Tractor fit locally on cutouts (SPIFF-style) once the sample grows
   beyond what manual batches of 20 allow, so the method scales and the position can float.
2. Semi-resolved (Re ~ 3-20 arcsec). Run the tool in Sersic mode with n, b/a, PA and Re
   fixed from optical imaging, and in parallel do our own aperture photometry on cutouts
   with (a) per-pixel wavelengths from CWAVE/CBAND, (b) a local sky annulus or
   Background2D after subtracting ZODI, (c) the exclusion flag list of Section 3, (d)
   VARIANCE propagated through the Solid Angle map, (e) wavelength-dependent aperture
   corrections from the ePSF (N_eff grows with wavelength, so a fixed aperture loses more
   light in bands 4-6). Compare the two; disagreement points to PSF or background issues.
3. Resolved (Re > 20 arcsec, e.g. nearby galaxies of arcminute size). The tool cannot be
   used. Options in order of preference: (a) per-exposure aperture or isophotal photometry
   on cutouts, assigning each pixel its own wavelength and binning into the 102 channels
   (Hora et al. style), with elliptical apertures matched across bands after PSF matching
   or at least aperture corrections from the ePSF; (b) a Mosaic Tool cube (9 arcsec pixels,
   ZODI already subtracted) for quick looks and morphology, not for final fluxes; (c) our
   own map maker only if (a) proves too noisy, following the binning and contour-filter
   recipes of the map-making paper.

Cross-cutting rules
- Wavelength per measurement comes from CWAVE at the source position (or per pixel for
  resolved work), never from the nominal channel.
- Subtract or fit a local background in every exposure; ZODI alone is not a sky
  subtraction.
- Screen exposures: FINAST = 0, L2DQAFLG = Pass, low `L2 N_*` artifact counts, no bright
  star (m_AB < 3) within ~8 deg for bands 2-6, and reject exposures whose local background
  is an outlier (airglow, shuttle glow, Moon).
- Track pipeline version per exposure (`provenance_version`, VERSION); apply
  `l3_flux_corrections` before mixing QR2 and QR3; re-run everything on DR1.
- Drop the two dichroic-edge channels and the He-contaminated channels unless a specific
  feature demands them.
- Stacking: normalize each object (median flux in a clean window or synthetic 2MASS Ks),
  shift to rest frame with the spectroscopic redshift, place on a common rest-frame grid
  at slightly coarser sampling than 102 channels, combine with a median or a
  sigma-clipped inverse-variance mean, and use bootstrap over objects for the error.
  Because per-object sampling is irregular and R changes at 3.8 um, propagate each
  object's bandpass (CBAND) into the model comparison rather than treating channels as
  delta functions.
- Validation: synthetic photometry against 2MASS J/H/Ks and WISE W1/W2 for every object;
  survey-to-survey repeatability once Surveys 3-4 land; comparison with any existing
  NIR spectra.

## 12. Pitfall checklist

- Assuming IMAGE is sky-subtracted (it is not; ZODI is a model extension).
- Reading flag names from the header with the QR2 `MP_*` scheme on a QR3 file (QR3 uses
  `MSKN/MSKM/MSKD`); hard-code the table.
- Using the QR2 PSF cube without checking VERSION for `+psffix1` or >= 6.5.6; better, use
  the ePSF products.
- Passing an oversampled ePSF to a forward model without shifting, integrating and
  renormalizing.
- Choosing the PSF zone with cutout pixel coordinates instead of parent-frame coordinates.
- Treating WCS-WAVE as the science wavelength solution.
- Mixing QR1/QR2/QR3 files without the flux corrections.
- Trusting the tool's `flux_err` as a full error budget.
- Aperture photometry with the same angular aperture in all bands without a
  wavelength-dependent aperture correction.
- Ignoring the SOURCE flag on the target itself when building masks (the target is
  flagged SOURCE; do not mask it).
- Forgetting that some pointings lack some bands and that early-mission coverage is
  single-epoch with gaps in specific channels.
- Astropy caches every remote FITS by default; use `cache=False` for bulk cutouts.
- Long TAP queries without a spatial constraint time out.

## 13. Citation and acknowledgment

Include: "This publication makes use of data products from the Spectro-Photometer for the
History of the Universe, Epoch of Reionization and Ices Explorer (SPHEREx), which is a
joint project of the Jet Propulsion Laboratory and the California Institute of
Technology, and is funded by the National Aeronautics and Space Administration."

Cite the release DOI(s) used (QR2 10.26131/IRSA652, QR3 10.26131/IRSA662), Bock et al.
2026 (ApJ 999, 139, mission), Akeson et al. 2026 (ApJS 285, 67, pipeline), Korngut et al.
2026 (instrument, arXiv:2603.29835), Hui et al. 2026 (spectral response,
arXiv:2602.09139) and, for mosaics, Cukierman et al. 2026 (ApJS 286, 22).

## 14. Source index

Software review: `docs/spherex_tools_review.md` and `docs/reference_notes/tools/`.

Official
- `docs/reference_notes/irsa_spherex_official_pages.md` (mission page, QR overview, DOIs, cloud page, cutout tool page, spectral calibration page, comet 3I/ATLAS, SPLICES)
- `docs/reference_notes/spherex_archive_documentation.md` (Archive User Guide site plus the Explanatory Supplement sections it links)
- `docs/reference_notes/spherex_explanatory_supplement_v2.0.md` (full read of the Supplement; PDF in `external/`)
- `docs/reference_notes/irsa_spherex_tutorials.md` (five notebooks; sources in `irsa_tutorial_sources/`)
- `docs/reference_notes/external/irsa_onlinehelp_sp_2026-09-22.txt` and `irsa_onlinehelp_mosaic_2026-09-22.txt` (tool help pages)

Key papers
- `paper_pipeline_2511.15823.md`, `paper_mapmaking_2603.25790.md`, `paper_instrument_2603.29835.md`

Method references
- `paper_ref_2604.22012.md` (SPIFF ultracool dwarfs), `paper_ref_2603.12390.md` (Cygnus X ices), `paper_ref_2607.18048.md` (compact galaxies vs SPS), `paper_ref_2607.00543.md` (brown dwarfs), `paper_ref_2605.06791.md` (reddened quasars), `paper_ref_2603.10135.md` (z > 4 quasars)

Live checks (2026-09-22)
- `scripts/probe_irsa_spherex_tables.py`, `scripts/inspect_cutout_layout.py`; S3 prefix listing and QR3 header dump recorded in `docs/lessons.md`.
