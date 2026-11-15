# Data reduction and analysis

What is inside a SPHEREx Level 2 spectral image, what has and has not been done to it, and the steps and
caveats of turning a stack of such images into the spectrum of one galaxy. The pipeline paper, the
Explanatory Supplement and the map-making paper are the sources for the products and the official
algorithms; the numbers marked "measured" come from this project's 2,225 exposures of six SDSS galaxies.

```{figure} figures/external/cukierman2026_exp_panel_real_2025W33_2C_0068_1.png
:width: 760px
:alt: A real Level 2 exposure

*Credit: Cukierman et al. 2026 (ApJS 286, 22; arXiv:2603.25790), real exposure panel.* One SPHEREx exposure, all six detectors. The horizontal gradients and stripes are the zodiacal light and the atmospheric emission lines seen through the linear variable filters; the stars and galaxies are the astrophysical content.
```

## The Level 2 image

One multi-extension FITS file per pointing per detector (six per pointing), about 65-72 MB, 2040 x 2040
pixels, named `level2_<PlanningPeriod>_<LargeSlew>_<SmallSlew>D<det>_spx_l2b-v<ver>-<yyyy>-<doy>.fits`.
Cutouts keep the same extensions with IMAGE, FLAGS, VARIANCE and ZODI trimmed and the wavelength table
remapped.[^pipeline][^expsupp22]

| HDU | QR2 (v6.x) | QR3 and DR1 (v7.x) | Notes |
|---|---|---|---|
| 0 PRIMARY | VERSION keyword | same | check VERSION (string; QR2 may carry `+psffix1`) |
| 1 IMAGE | MJy/sr, float32 | same | not zodi-subtracted; astrometric WCS with SIP; alternate WCS `A` gives 0-based parent-frame pixel coordinates (CRPIX1A/CRPIX2A are the cutout offset) and `W` the wavelength lookup |
| 2 FLAGS | int32 bitmask, bit names in header as `MP_<NAME>` | int32 bitmask, bit names as `MSKN####`/`MSKM####`/`MSKD####` triplets | the header scheme changed; hard-code the table below |
| 3 VARIANCE | (MJy/sr)^2 | same | sample-up-the-ramp noise model plus an empirical excess-noise term; airglow lines are included |
| 4 ZODI | MJy/sr model | same, header ZODIMDL = KEL98_WAVESCL_V1 | a model, not subtracted from IMAGE |
| 5 PSF | image cube (121, 101, 101) at 10x oversampling, 11 x 11 zones | replaced by EPSF | see PSF below |
| 5 EPSF | absent | binary table, 441 rows (21 x 21 zones) or 451 rows (11 x 41) for D3; BINX, BINY, XCENTER, YCENTER, XWIDTH, YWIDTH, NSTAR, NEFF_MEAN, CWAVE, CBAND, EPSF (33 x 33); OVSMPX = OVSMPY = 5 | empirical PSF with unit integral |
| 6 WCS-WAVE | one-row table (X, Y, VALUES) | same | wavelength lookup, visualisation grade (about 1 nm); use CWAVE/CBAND for science |

Useful IMAGE header keywords: DETECTOR, OBSID, FINAST (0 = good fine astrometry; only such images are
archived), L2DQAFLG, PSF_FWHM (a per-image median in arcsec), XPOSURE, TELAPSE, MJD-AVG, and the
`L2 N_<FLAG>` counters for every flag plus `L2 SATSTRKS`, `L2 N_XTALK`, `L2 N_HALO`. A Level 2 image is only
released if N_TRANSIENTS < 435,000, the exposure is outside the South Atlantic Anomaly, FINAST = 0 and the
eleven-test data-quality assessment passes (at least 6 of 11), so some pointings lack some bands.[^expsupp3]

What has been done to IMAGE: dark subtraction, flat field and absolute gain (from about 54,000 measurements
of 17 CALSPEC standards), nonlinearity correction, astrometry, flagging. What has not: no background
subtraction of any kind, no airglow subtraction, no PSF matching between bands.[^pipeline]

## Flags

The canonical FLAGS bits (Explanatory Supplement Table 16, the IRSA tool help page, live headers):[^expsupp22]

| Bit | Name | Meaning | Science use |
|---|---|---|---|
| 0 | TRANSIENT | charge jump during the ramp (cosmic ray, satellite, bloom spill); the first ~10 s are not always caught | exclude |
| 1 | OVERFLOW | half-well overflow threshold reached | exclude for photometry; the mosaic tool only propagates it |
| 2 | SUR_ERROR | on-board checksum or processing error | exclude |
| 4, 5 | PHANTOM, REFERENCE | phantom and reference pixels (QR2 header only) | not sky |
| 6 | NONFUNC | permanently dead | exclude |
| 7 | DICHROIC | band 3/4 dichroic region, throughput below 50 % | exclude; calibration uncertain |
| 9 | MISSING_DATA | lost on-board data | exclude |
| 10, 11 | HOT, COLD | hot or anomalously low in this exposure | exclude |
| 12 | FULLSAMPLE | rotating 8 x 32 full-readout region | exclude |
| 13 | SUR_MISMATCH | on the tool help page, not in the public table | treat as bad |
| 14 | PHANMISS | phantom correction not applied | exclude |
| 15 | NONLINEAR | nonlinearity correction unreliable | exclude |
| 16 | VAR_UNDER | on the tool help page, not in the public table | caution |
| 17 | PERSIST | persistent charge above threshold | exclude |
| 18 | PERSIST_UNK | on the tool help page, not in the public table | caution |
| 19 | OUTLIER | outlier-pixel module | exclude for photometry; the mosaic tool only propagates it |
| 20 | CROSSTALK | electrical crosstalk (R7 only) | exclude |
| 21 | SOURCE | pixel mapped to a Reference Catalog source | informational; the target itself is flagged |
| 22, 23, 24 | GHOST, GHOST_FPA, GHOST_EXT | optical ghosts (in frame; from another detector, unused; from outside the field, in development) | exclude |
| 25 | STREAK | satellite or asteroid streak | exclude |
| 26 | BLOOM | charge bloom from a bright source (R7, and QR2 from 2025W51) | exclude |
| 27, 28, 29 | SNOWBALL, HALO, SATELLITE_HALO | large charge-release event; halo of a transient; halo of a streak | exclude |
| 32, 33 | CONTAINS_BAD_PIXEL, FIT_ERROR | Spectrophotometry Tool output only | warning; exclude |

A measurement with flags = 0 or flags = 2097152 (SOURCE only) used only nominal pixels. The official tools
drop SUR_ERROR, NONFUNC, MISSING_DATA, HOT, COLD, NONLINEAR, PERSIST, BLOOM, SNOWBALL, HALO and
SATELLITE_HALO from their fits; the mosaic tool also drops TRANSIENT, DICHROIC, PHANMISS, CROSSTALK, the
GHOST bits and STREAK, and propagates OVERFLOW, SOURCE and OUTLIER. Lee et al. keep only flags 0 or 2097152
and reject bits 0, 1 and 7.[^lee] Our demo excludes the tool set plus TRANSIENT, OVERFLOW and DICHROIC.

```{figure} figures/site/flag_statistics.png
:width: 820px
:alt: Flag frequencies in the demo cutouts

Fraction of pixels carrying each flag in the 2,242 cutouts (41 x 41 or 53 x 53 pixels, 4.2 million pixels) of the six demonstration galaxies, per detector; flags that never occur are omitted (measured). SOURCE covers 31-53 % of the pixels around a bright galaxy; HALO and OUTLIER 1.3-2.1 %; DICHROIC 2.6-2.8 % of D3 and D4 pixels; TRANSIENT 0.6-0.9 %; everything else below 1 %. Made by `scripts/site_figures.py`.
```

Two points about SOURCE: the target is itself flagged SOURCE, so masks must not use that bit; and source
masks are sized from Reference Catalog magnitudes (faint limit 19 AB) and only unresolved or compact
sources (`spherex_class` <= 7) are masked, so large resolved galaxies are not source-masked and a pipeline
background that treats unflagged pixels as empty sky will include a resolved target's outskirts.[^expsupp3]

## Wavelength handling

- Every pixel has its own central wavelength and bandwidth. The wavelength at which a galaxy is measured
  in an exposure is set by where it falls on the detector, so a resolved galaxy is measured at slightly
  different wavelengths across its extent in one exposure, and at different wavelengths in different
  exposures ([primer](primer.md#linear-variable-filters-wavelength-is-position)).
- For science use CWAVE and CBAND from the Spectral WCS product (per band); the ePSF zone rows carry CWAVE
  and CBAND per zone too. The in-file WCS-WAVE table (alternate WCS key `W`) is a bilinear approximation
  good to about 1 nm and is fine for bookkeeping. To use it with astropy pass the HDU list
  (`WCS(header, fobj=hdulist, key='W')`), set `wcs.sip = None` (astropy issue 13105), and `pixel_to_world`
  returns (wavelength, bandwidth).
- The Spectral Channels product is a geometric survey-planning channelisation, not a wavelength solution;
  its per-channel table gives the median wavelength, the limits and R for the 17 channels of each band
  (Explanatory Supplement Tables 29-34; edge channels 0 and 18 have anomalous R). R7 shifted the band 5 and
  6 wavelength solution from on-sky calibration, so channel definitions for those bands must not be mixed
  across pipeline versions. The Spectrophotometry Tool switched to CWAVE values on 2025-12-17.[^expsupp4]
- Adjacent nominal channels overlap by up to 0.018 um (measured from the channel table); binning by
  "CWAVE within [WL_MIN, WL_MAX]" puts an exposure into two channels. Assign each exposure to the nearest
  channel centre of its detector.
- Published spectra are placed on the 102-channel grid by error-weighted averaging of the measurements whose
  CWAVE falls in a channel (Gagne et al.) or by interpolating the irregular sampling onto the grid (Lee et
  al.). Bands 5 and 6 have about three times finer sampling than bands 1-4, so joint fits across detectors
  need a common rebinning.[^gagne][^lee]

## Units and the pixel solid angle

IMAGE is a surface brightness in MJy/sr. The flux density of a source is the sum of its pixels times the
pixel solid angle; the official tools use the Solid Angle Pixel Map, which includes the optical distortion,
rather than a constant (6.15 arcsec)^2.[^expsupp4]

```{figure} figures/site/solid_angle_maps.png
:width: 760px
:alt: Solid angle pixel maps

The DR1/QR3 Solid Angle Pixel Map of each detector divided by the nominal (6.15 arcsec)^2. The pixel solid angle ranges from 0.989 to 1.017 of nominal (37.41-38.48 arcsec^2); using a constant pixel area would therefore mis-scale fluxes by up to 1.7 % depending on where the source lands (measured). Made by `scripts/site_figures.py`.
```

A useful conversion for aperture sums: 1 MJy/sr over one 6.15 arcsec pixel is 23.5045 x 6.15^2 / 1000 =
0.889 mJy (the official mosaic notebook's formula).[^tutorials]

## The point spread function

- QR2 (VERSION 6.x): a `PSF` image cube of 121 stamps (11 x 11 zones), 101 x 101 pixels at 10x oversampling
  (0.615 arcsec per oversampled pixel); zone centres in the keywords XCTR_i, YCTR_i. Files with VERSION
  6.4-6.5.5 without `+psffix1` need the header-order fix (planes stored x-fast). The September 2026
  tutorial advises not to use these PSFs at all and to take the QR3 ePSF files instead.[^tutorials]
- QR3 and DR1 (VERSION 7.x): an `EPSF` binary table, one row per zone (21 x 21 for most detectors, 11 x 41
  for D3 because of birefringence near the dichroic), each stamp 33 x 33 at 5x oversampling with unit
  integral, plus XCENTER/YCENTER/XWIDTH/YWIDTH, NSTAR (median 320-700 stars per zone, measured), NEFF_MEAN,
  CWAVE and CBAND. Pick the row nearest to the target's parent-frame pixel position; ORDERING is
  'x-fast then y'; DETCOORD = 'sky' means the mid-wave stamps are flipped in x to match the short-wave
  view.[^expsupp4]
- The ePSF is empirical (Anderson and King), so it already includes inter-pixel capacitance and the pixel
  response. For forward modelling it must be shifted to the sub-pixel phase of the source, integrated onto
  native pixels and renormalised; passing the oversampled stamp directly gives wrong widths and
  normalisations. The tutorial does this with `photutils.psf.ImagePSF(data, oversampling=(OVSMPY, OVSMPX))`.
  Because the stamps sum to one on the 5x grid, native-spaced samples sum to 1/25.
- The cutout service does not trim the PSF extension; the target position in the parent frame is
  `x_parent = 1 + x_cutout - CRPIX1A` (0-based astropy pixels), and the zone must be chosen with those
  coordinates, not the cutout's.
- N_eff grows with wavelength (3.3 to 4.9 pixels from D1 to D6, zone medians, measured; figure on the
  [primer](primer.md#the-point-spread-function)) and depends on the sub-pixel phase; PSF wings are stronger
  than the pre-launch optical model, so bright sources need larger masks.[^cukierman] Reprojection into
  mosaics widens the effective PSF by about 1.6x at 0.9 um and 1.3x at 4.7 um for binning.

## Backgrounds

Everything in this section is present in the delivered IMAGE unless stated otherwise.

### Zodiacal light

The zodiacal light (ZL) is the dominant background and the dominant noise term at all
wavelengths.[^korngut] The ZODI extension is a modified Kelsall et al. (1998) interplanetary-dust model with
the Tsumura et al. (2013) spectral shape; because the raw model underestimates the amplitude, a
wavelength-dependent scaling factor was derived against SPHEREx data at |b| > 30 deg and applied as a median
per wavelength (the `zodi_scaling` product; header ZODIMDL = KEL98_WAVESCL_V1). It tracks the spatial and
temporal variation well but it is a model, not a fit to the image, and it is not subtracted.[^expsupp3]

```{figure} figures/site/background_levels.png
:width: 820px
:alt: Zodiacal light, residual background and S/N in the demo

(a) The ZODI model at the position of each demonstration galaxy against wavelength; the legend gives the ecliptic latitude. At 1 um the model is 0.13-0.30 MJy/sr for latitudes 46 to 6 deg, and 0.31-0.57 MJy/sr at 5 um where the thermal emission of the dust rises. (b) The local background that our joint fit finds after subtracting ZODI, divided by ZODI: +4 to +12 % for the two galaxies at low ecliptic latitude and +11 to +34 % for the four at 24-46 deg (16th-84th percentiles), so ZODI alone is not a sky subtraction and the model's scaling is latitude dependent at the 10-20 % level. (c) The per-exposure signal-to-noise ratio of the forced model flux of the six galaxies (SDSS z = 14.3-15.7): 40-90 at 1-3.5 um, about 10 at 5 um (measured). Made by `scripts/site_figures.py`.
```

What the various extractions do about it: the Spectrophotometry Tool ignores ZODI and subtracts a local
background from a 15-pixel box around each source with known sources masked; the Level 3 pipeline first fits
a global spectral background and then a local 15 x 15 background simultaneously with the flux; the Mosaic
Tool subtracts IMAGE - ZODI before coadding; the map-making paper prefers a "contour filter", the mean
subtracted within thin iso-wavelength bins about one pixel high, or a mosaic-level fit of a scaled zodi
template plus a monopole.[^pipeline][^cukierman] For a galaxy smaller than a few arcminutes a local annulus
or two-dimensional background around the object is what every published extraction does; subtracting ZODI
first reduces the dynamic range and removes the smooth spectral shape of the zodiacal light, but a residual
local sky must still be fitted (panel b above).

```{figure} figures/external/cukierman2026_filter_panel_2025W49_1A_0130_1.png
:width: 760px
:alt: Contour filter

*Credit: Cukierman et al. 2026, contour-filter panel.* An exposure before and after the contour filter, which subtracts the mean within thin bins that follow the curved iso-wavelength contours of the filter: the zodiacal gradient and the He I airglow stripe are removed at the cost of any real structure larger than the field of view.
```

```{figure} figures/external/cukierman2026_deproj_fullsky_a1_sc1.png
:width: 820px
:alt: Zodi deprojection of a full-sky map

*Credit: Cukierman et al. 2026, full-sky deprojection panel.* A full-sky channel map at 0.76 um before and after fitting and subtracting a scaled zodiacal-light template with a monopole: the ecliptic S-curve is removed while the Galactic structure stays.
```

### Atmospheric emission

All of these are present in IMAGE, not subtracted, and included in VARIANCE:[^expsupp23][^korngut]

- The He I 1.083 um line from metastable helium in the thermosphere appears in every exposure of bands 1
  and 2 at a few to 30 times the zodiacal surface brightness, varying over the orbit. It is strong enough to
  produce weak spectral-leak features near 0.84 um (band 1) and 1.25 and 1.49 um (band 2) through the
  percent-level out-of-band response of those filters. It makes the 1.083 um channel the one place where
  the mission falls short of its sensitivity projection; published map work drops the four affected
  channels. Its amplitude is fitted at Level 1 and recorded in the header (`HE_AG_*`) but not removed.
- Auroral lines (excited N2 and others), mainly in bands 1-2, sometimes 3-5, stronger near the poles and
  during high solar activity, up to a few times the zodiacal light.
- Other lines at 0.78, 0.84, 0.93, 1.13, 1.81, 2.63, 2.75, 4.03 and 4.64 um with variable amplitude.
- Shuttle glow: fluorescence of atomic oxygen on the baffle paint, peaking near 3.0 and 4.5 um and strongest
  at low ram angle. The survey now keeps the ram angle below 70 deg, but residuals remain and the
  recommended mitigation is to reject affected exposures using redundancy.
- Earthshine at local zenith angles above 24 deg, measured at 0.05 e-/s at 42 deg, about 40 times fainter
  than the zodiacal light and short-wavelength weighted.

```{figure} figures/external/korngut2026_ShuttleRamPhil.png
:width: 380px
:alt: Shuttle glow versus ram angle

*Credit: Figure 24 of Korngut et al. 2026 (arXiv:2603.29835).* The 4.5 um shuttle-glow intensity against ram angle, with the 70 deg survey limit.
```

```{figure} figures/external/korngut2026_Moonshine_meas_lbl.png
:width: 420px
:alt: Moonshine measurement

*Credit: Figure 21 of Korngut et al. 2026.* Band-2 photocurrent during the lunar stray-light experiment, with the Moon at decreasing separations: the off-axis response is asymmetric across the field.
```

Templates (`he_template_D<n>` for bands 1-2, `aurora_template` for band 1, `shuttle_glow_template` for
band 5 in R7) are provided with fit coefficients in the headers. R7 headers also carry the booleans
`HE_AIRGLOW_CONT`, `AURORA_CONT` and `SHUTTLE_GLOW_CONT` and the corresponding correlation coefficients
(threshold 0.2); QR2 headers do not.[^expsupp4]

Measured in the SED demo: `HE_AIRGLOW_CONT` is True for every D1 and D2 exposure, so it marks the detectors
the line can reach, not the exposures it affects, and cannot screen anything. With ZODI subtracted and a
constant local background, the exposures within 0.02 um of He I had chi2/dof of 5-9 around a bright
galaxy; a background basis quadratic in the per-pixel CWAVE across the cutout (fitted jointly with the
sources) brought them to 1-2 and changed their fluxes by 5-9 %, after which only 1-3 exposures per galaxy
needed screening. A plane in x and y does not help, because the airglow band follows the curved
iso-wavelength contours. The galaxy's per-exposure diagnostics on the [SED page](sed_extraction.md) show the
effect.

### The dichroic boundary

The dichroic beamsplitter transition at 2.42 um sits inside the band 3/4 overlap. Its reflectivity and
transmission change steeply there, so the effective passbands of the long end of band 3 and the short end
of band 4 are squeezed and shifted (blueward for band 3, redward for band 4); the wavelength calibration
residuals are largest there, the noise is higher and the photometric calibration is explicitly called less
certain. Pixels whose throughput is below 50 % carry the DICHROIC flag (also distributed as the
`dichroic_D<n>` bitmask).[^korngut][^expsupp24] A beam-splitter ghost, a disk of about 10 arcmin from very
bright sources, is strongest near this boundary.

Measured: in 2,225 exposures of six galaxies, every exposure with CWAVE between 2.417 and 2.426 um was
rejected because all target pixels were flagged (2.6-2.8 % of D3 and D4 cutout pixels in all). There is
therefore no usable overlap between D3 and D4, and a detector-to-detector comparison there must use
exposures on both sides over a window of about 0.2 um. For 0.03 < z < 0.06 galaxies the 2.29 um CO
bandhead falls inside that window, which is why our boundary test found galaxy steps of +0.06 to +0.17 mag
growing with redshift while bright stars in the same cutouts gave 0.00 +- 0.03 mag
([SED page](sed_extraction.md#detector-boundaries)).

### Optical and electronic artefacts

From the Explanatory Supplement section 2.3 and the pipeline paper:[^expsupp23][^pipeline]

- Ghosts: triangular frame-edge ghosts from sources just outside the field; linear ghosts from very bright
  sources above or below the detector (stronger at long wavelengths); the beam-splitter disk (bands 3-6);
  an "8 degree ghost" from very bright stars about 8 deg away (bands 2-6); Moon stray light at the left and
  right edges in bands 1, 4, 5 and 6. Ghost masking is modelled only for very bright producers (above
  100 Jy at the band-3 edge, 3000 Jy in band 4, 10,000 Jy in bands 5-6; frame-edge ghosts only for
  m_AB <= 11); GHOST and GHOST_EXT are still in development.
- Cosmic rays: single-pixel hits are removed on board; extended hits, snowballs (an OVERFLOW + TRANSIENT core
  with an unflagged halo until R7), halos and a faint cosmic-ray-induced glow (a red gradient in bands 1-2,
  an edge rim in 4-6) remain. About 1 % of exposures show diffuse optical transients. Satellite streaks
  near the noise level may be unflagged.
- Crosstalk: a negative image displaced 32 rows (the row-chopping readout), a smear at the end of the
  previous row, and channel crosstalk at multiples of 64 columns (types 1 and 2 flagged from R7, type 3
  not yet).
- Persistence: a multi-exponential charge-trap model; snowballs and large cosmic rays leave excess
  persistence; exposures within 5 deg of the Moon were avoided during commissioning for this reason.
- Blooming around bright stars triggers early-transient flags over a larger footprint than expected;
  ZEROSLOPEON is disabled in flight so those pixels keep their pre-trigger slope rather than zero.
- Astrometry: RMS below 0.3 arcsec for FINAST = 0; distortion up to about 13 pixels (80 arcsec) in the
  corners, captured by the SIP terms; about 3 % of images failed fine astrometry before R7, below 1 %
  after, with failures clustered in crowded fields.
- Rice compression quantises pixel values at half the expected noise; harmless for aperture sums but worth
  knowing. A curated list of heavily contaminated images is kept on the
  [SPHEREx anomalous-images page](https://spherex.caltech.edu/page/anomalyimages).

## Calibration accuracy

The absolute gain is derived from about 54,000 measurements of 17 CALSPEC standards and the Explanatory
Supplement quotes better than 1 % relative to CALSPEC for most channels.[^expsupp4] Users report larger
effective floors: a gain reliability of 3 % (bands 1-4) and 5 % (bands 5-6) plus a 3 % visit-to-visit RMS
added in quadrature (Rustamkulov et al.; the Level 3 pipeline adds the same 3 %), an 8 % absolute floor from
a JWST comparison (Gagne et al.), a 4 % median offset against SDSS z and 3.5 % against WISE W1 for compact
galaxies (Lee et al.); two papers find the tool uncertainties underestimated (Davies et al., Stepney et
al.).[^rustamkulov][^gagne][^lee] Measured in the demo: repeat exposures of the same galaxy at the same
wavelength scatter 1.0-1.4 times the formal error in every detector, with a 0.7-2.4 % fractional floor per
exposure for compact n = 4 galaxies and none for n = 1 galaxies; pixel noise is 1.2-1.4 times
sqrt(VARIANCE) on unflagged pixels of two real files; and Gaia stars give chi2/dof of 1.4-1.8 at S/N 10-30
rising to 16-18 at S/N 300-1000. Errors must be calibrated on the data.

## The official extraction tools

Spectrophotometry Tool (IRSA help page):[^tools]

- Tractor forced photometry at user positions; only the flux amplitude is fitted. Two morphologies: point
  source, or a Sersic profile with fixed n (0.5-6), axis ratio, position angle (east of north) and R_e
  (1-20 arcsec; below 1 arcsec is treated as a point source). Larger galaxies cannot be modelled.
- Inputs IMAGE, FLAGS, VARIANCE, PSF or EPSF, Solid Angle Pixel Map; ZODI is not used. Background: a local
  estimate from a 15-pixel box with known sources masked, subtracted before the fit and returned as
  `flux_bkg`, documented as occasionally problematic (look for jumps between adjacent wavelengths).
- Output: wavelength, flux (uJy), flux_err, lambda_width, flags (including bits 32 and 33), fit_ql (mean
  |data - model| / sigma within 2.5 pixels; about 1 is good), flux_bkg, lvf_id, det_id, deep_flg, mjd,
  data_collection, x_image, y_image. DICHROIC and FIT_ERROR points should be discarded.
- Throttles: 20 sources per job, 2 concurrent jobs, about 1.67 s per image plus 50 s; companions must be
  listed to be deblended. Used as the engine by Lee et al., Rustamkulov et al., Stepney et al. and Davies et
  al.; Gagne et al. built their own equivalent (SPIFF) to let the position float and sample posteriors.

Mosaic Tool: a cube of the 102 nominal channels (or a subrange) over up to 5 x 5 deg, pixels of at least
6.15 arcsec (default 9), TAN projection, all-sky-survey images only. It subtracts IMAGE - ZODI, masks the
exclusion flags, assigns pixels to channels with the Spectral Channels template, reprojects by
intensity-weighted binning and averages; output HDUs IMAGE, NHITS, FLAGS plus the channel and wavelength
tables. The Explanatory Supplement recommends the Level 2 images, not mosaics, for precision photometry,
because striping from airglow lines and from sharp spectral features under multi-roll coaddition does not
average down.[^tools][^expsupp34]

Source Discovery notebook: the only official code that builds a flux + variance + flag spectrum from many
cutouts with aperture photometry at several radii and a 7-16 pixel annulus; it reads flag names from the
QR2 `MP_*` keywords and breaks on R7 headers.[^tutorials]

## Mosaics versus exposures

```{figure} figures/external/cukierman2026_coadd_panel_heart_a5_sc3.png
:width: 760px
:alt: LVF gradient in a coadd

*Credit: Cukierman et al. 2026, coaddition panel (Heart and Soul Nebula, 3.9 um).* A channel mosaic with, per map pixel, the hit count and the mean central wavelength of the contributing detector pixels: under sparse coverage the wavelength gradient within a channel survives into the map.
```

```{figure} figures/external/cukierman2026_interp_panel_helix_a6_sc8_00S9.png
:width: 820px
:alt: Banding near an emission line and spectral interpolation

*Credit: Cukierman et al. 2026, spectral-interpolation panel (Helix Nebula, H2 line at 4.69 um).* Near a sharp emission line the within-channel wavelength gradient produces "banding" in a mosaic; interpolating narrow sub-channel mosaics to a common wavelength suppresses but does not remove it.
```

The map-making paper's lessons carry over to any per-exposure extraction:[^cukierman] the two
dichroic-adjacent channels and the four helium channels are routinely dropped; the mean wavelength of what
went into a measurement must be tracked; near sharp features the sampling in wavelength matters as much as
the noise; and there is no universal per-pixel variance, so uncertainties are best estimated empirically
(survey-to-survey differences, repeat pairs, scatter of blank apertures).

## How the literature extracts spectra

| Paper | Targets | Data path | Extraction | Background | Combination and errors |
|---|---|---|---|---|---|
| Gagne et al. 2026 (2604.22012, SPIFF)[^gagne] | 6003 ultracool dwarfs, point sources | QR2 cutouts 20 x 20 px via SIA2 and S3 | own PSF fit with the calibration PSF shifted and box-summed to native pixels; position free; scipy then ultranest posteriors; aperture photometry at 18 radii | median in a 15-pixel box with bad pixels and known stars masked; no ZODI | wavelength evaluated at the fitted position; error-weighted mean into the 102 channels; 8 % absolute floor from a JWST prism comparison |
| Hora et al. 2026 (2603.12390, Cygnus X ices)[^hora] | extended ISM | QR2 images; 50-150 exposures per position | slice each image by per-pixel wavelength into narrow windows, reproject, sigma-clip average; Tractor forced photometry for compact sources | local only; no ZODI | LVF "banding" corrected with JWST-calibrated simulations; peak depths underestimated at R = 35-130 |
| Lee et al. 2026 (2607.18048, compact SDSS galaxies)[^lee] | 3889 galaxies with Petrosian r < 3.1 arcsec | Spectrophotometry Tool, point-source mode, SDSS positions | keep flags 0 or 2097152; reject bits 0, 1, 7; at least 10 valid points per band; resample to the 102 channels | tool default 15-pixel box | scale each spectrum to SDSS z (median 4 % offset); fibre-to-model aperture correction on the SDSS side; rest-frame median stacks; 10 % model floor |
| Rustamkulov et al. 2026 (2607.00543, brown dwarfs)[^rustamkulov] | 37 point sources | Spectrophotometry Tool with the corrected PSF, QR2 | point-source Tractor; reject any flag but SOURCE; 4 sigma clip from a running median | tool box | 3 % visit-to-visit RMS in quadrature; gain reliability 3-5 %; half the data under-flagged |
| Stepney et al. 2026 (2605.06791, reddened quasars)[^stepney] | 404 point sources | Spectrophotometry Tool | S/N > 5 channels; median-filter continuum; cross-correlation redshifts | tool | drop targets with a K-band neighbour within 6 arcsec; tool errors "likely underestimated" |
| Davies et al. 2026 (2603.10135, z > 4 quasars)[^davies] | about 4900 candidates | Spectrophotometry Tool in batches of 20 | point-source Tractor; deblend with CatWISE positions within 25 arcsec; Galactic extinction correction | tool | rebin D1-D4 and D5-D6 onto a common grid; negative fluxes for close blends |
| Cukierman et al. 2026 (2603.25790, map making)[^cukierman] | diffuse and resolved | images with FINAST = 0 | binning reprojection, hit count and mean wavelength per pixel, sub-channel cubes with spline interpolation | contour filter or zodi template deprojection | no universal variance; survey-1 vs survey-2 difference maps |
| Akeson et al. 2026 (2511.15823, pipeline)[^pipeline] | - | - | Level 3: Tractor forced photometry in 15 x 15 boxes at Reference Catalog positions, blend-covariance errors, Solid Angle map to uJy | global spectral zodi fit plus a 2D background | catalogues averaged over surveys on a fixed grid |

## Strategy for resolved galaxies

Three regimes, decided per object from the optical image (effective radius against the 6.15 arcsec pixel
and the wavelength-dependent PSF):

1. Unresolved (R_e below about 3 arcsec, no neighbour within about 20 arcsec): the Spectrophotometry Tool in
   point-source mode is the baseline (keep flags 0 / 2097152, drop DICHROIC and FIT_ERROR points, inspect
   `flux_bkg`, add a 3 % visit-to-visit term, apply a 3-8 % absolute floor against models, validate with
   synthetic 2MASS/WISE/SDSS photometry as Lee et al. did), reproduced locally once the sample outgrows
   batches of 20.
2. Semi-resolved (R_e of 3-20 arcsec): forced Sersic photometry with the shape fixed from optical imaging,
   neighbours fitted jointly, ZODI subtracted and a local background fitted, the exclusion flag list above,
   VARIANCE propagated through the Solid Angle map, and an aperture-based estimator with model-based
   corrections as a check. This is what the [SED demonstration](sed_extraction.md) does.
3. Resolved (R_e above 20 arcsec): the tool cannot be used. Per-exposure aperture or isophotal photometry
   on cutouts with each pixel assigned its own wavelength and binned into channels (Hora et al. style), with
   PSF matching or ePSF-based aperture corrections across bands; Mosaic Tool cubes for quick looks and
   morphology, not for fluxes; an own map maker only if needed.

Cross-cutting rules: the wavelength of a measurement is CWAVE at the source position, never the nominal
channel; subtract or fit a local background in every exposure; screen exposures (FINAST = 0, L2DQAFLG =
Pass, low artefact counts, no star brighter than 3 AB within about 8 deg for bands 2-6, no outlying local
background); track the pipeline version per exposure and never mix QR2 with R7 data without the flux
corrections; drop the dichroic-edge and helium channels unless a feature demands them; propagate each
measurement's bandpass (CBAND) into model comparisons rather than treating channels as delta functions.

## Pitfall checklist

- Assuming IMAGE is sky-subtracted (it is not; ZODI is a model extension).
- Reading flag names from the header with the QR2 `MP_*` scheme on an R7 file; hard-code the table.
- Using the QR2 PSF cube without checking VERSION for `+psffix1` or 6.5.6 and later; better, use the ePSF.
- Passing an oversampled ePSF to a forward model without shifting, integrating and renormalising.
- Choosing the PSF zone with cutout pixel coordinates instead of parent-frame coordinates (CRPIX1A/2A).
- Treating WCS-WAVE as the science wavelength solution, or binning exposures into channels by their
  overlapping [WL_MIN, WL_MAX] ranges.
- Mixing QR1, QR2 and R7 files without the flux corrections; applying the corrections to DR1 images.
- Trusting the tool's `flux_err` or the VARIANCE extension as a full error budget.
- Using a constant pixel area instead of the Solid Angle Pixel Map (up to 1.7 %).
- The same angular aperture in all bands without a wavelength-dependent aperture correction (N_eff grows
  from 3.3 to 4.9 pixels).
- Masking the target because it carries the SOURCE flag.
- Forgetting that some pointings lack some bands and that early-mission coverage has single-epoch channels.
- Screening airglow exposures with `HE_AIRGLOW_CONT` (True for every D1/D2 exposure); fit a background that
  follows the iso-wavelength contours instead.
- Point-sampling a Sersic profile on the 1.23 arcsec ePSF grid: an n = 4 cusp with R_e = 1 arcsec loses 2 %
  of its flux, and the loss changes with the cutout orientation; integrate the core and validate against a
  brute-force reference.
- Comparing analytic Sersic totals with tractor or SDSS model totals without the truncation factor (6 %
  for n = 4, 1 % for n = 1).
- Reading a detector-boundary step as calibration when a spectral edge (CO 2.29 um at z < 0.06) or a broad
  feature (the 1.6 um bump) sits in the window.
- Astropy caching every remote FITS file; long TAP queries without a spatial constraint.

[^pipeline]: Akeson et al. 2026, "The SPHEREx Image and Spectrophotometry Processing Pipeline", ApJS 285, 67,
    arXiv:2511.15823; our [reading note](references/papers/paper_pipeline_2511.15823.md).
[^expsupp22]: SPHEREx Explanatory Supplement v2.0 (2026-08-25), section 2.2 (spectral images) and Table 16
    (flags); our [reading note](references/irsa/spherex_explanatory_supplement_v2.0.md).
[^expsupp23]: Explanatory Supplement, section 2.3 (image anomalies and features).
[^expsupp24]: Explanatory Supplement, section 2.4 (known limitations) and 4.3.4 (dichroic bitmask).
[^expsupp3]: Explanatory Supplement, section 3 (processing steps: source masks 3.2.9, zodi prediction 3.2.11,
    Level 2 data-quality assessment 3.2.12).
[^expsupp34]: Explanatory Supplement, section 3.4 (mosaics).
[^expsupp4]: Explanatory Supplement, section 4 (calibrations: absolute gain 4.2.1, PSF 4.2.3, spectral WCS
    4.3.1, spectral channels 4.3.2, atmospheric templates 4.3.3, additional products 4.3.4).
[^korngut]: Korngut et al. 2026, arXiv:2603.29835, sections 3 (dichroic), 9.5-9.6 (stray light, Earthshine,
    shuttle glow) and 9.7 (He I airglow); our [reading note](references/papers/paper_instrument_2603.29835.md).
[^cukierman]: Cukierman et al. 2026, ApJS 286, 22, arXiv:2603.25790, sections 3-5; our
    [reading note](references/papers/paper_mapmaking_2603.25790.md).
[^tutorials]: IRSA SPHEREx tutorial notebooks; our [reading note](references/irsa/irsa_spherex_tutorials.md).
[^tools]: IRSA Spectrophotometry Tool and Mosaic Tool help pages, saved 2026-09-22; summarised in the
    [official pages note](references/irsa/irsa_spherex_official_pages.md).
[^gagne]: Gagne et al. 2026, arXiv:2604.22012; [note](references/papers/paper_ref_2604.22012.md).
[^hora]: Hora et al. 2026, arXiv:2603.12390; [note](references/papers/paper_ref_2603.12390.md).
[^lee]: Lee et al. 2026, arXiv:2607.18048; [note](references/papers/paper_ref_2607.18048.md).
[^rustamkulov]: Rustamkulov et al. 2026, arXiv:2607.00543; [note](references/papers/paper_ref_2607.00543.md).
[^stepney]: Stepney et al. 2026, arXiv:2605.06791; [note](references/papers/paper_ref_2605.06791.md).
[^davies]: Davies et al. 2026, arXiv:2603.10135; [note](references/papers/paper_ref_2603.10135.md).
