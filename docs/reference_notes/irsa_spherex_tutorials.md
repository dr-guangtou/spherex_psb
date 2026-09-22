# IRSA SPHEREx tutorial notebooks (surveyed 2026-09-22)

Sources consulted: the rendered MyST site at
`https://caltech-ipac.github.io/irsa-tutorials/spherex/` (and its sub-pages) and the
**only** GitHub repository permitted for this survey, the official
`Caltech-IPAC/irsa-tutorials` repo, specifically the MyST-markdown notebook sources under
`tutorials/spherex/` and `tutorials/techniques-and-tools/`. All rendered HTML pages were
confirmed to reflect the same code as the `.md` (jupytext MyST) sources; the `.md` sources
were used as the verbatim record because they are not subject to any client-side
truncation. Local copies of every source file are saved under
`docs/reference_notes/irsa_tutorial_sources/` (paths given per-notebook below).

---

## Notebook inventory

| # | Title | Rendered URL | Source file (local copy) | Last updated (as stated in notebook) | One-line purpose |
|---|-------|--------------|---------------------------|----------------------------------------|------------------|
| 0 | SPHEREx Tutorial Notebooks (landing/gallery page) | https://caltech-ipac.github.io/irsa-tutorials/spherex | `irsa_tutorial_sources/spherex.md` | n/a (index page) | Gallery listing the 5 notebooks below via `{notebook-gallery}` directive. |
| 1 | Introduction to SPHEREx Spectral Images | https://caltech-ipac.github.io/irsa-tutorials/spherex-intro | `irsa_tutorial_sources/spherex_intro.md` | 5 March 2026 | Query SIA for Spectral Image MEFs, open one with astropy, tour every FITS extension (IMAGE/FLAGS/VARIANCE/ZODI/PSF/WCS-WAVE), spatial+spectral WCS basics, Firefly visualization. |
| 2 | Download a collection of SPHEREx Spectral Image cutouts as a MEF | https://caltech-ipac.github.io/irsa-tutorials/spherex-cutouts | `irsa_tutorial_sources/spherex_cutouts.md` | 5 March 2026 | TAP query for all exposures overlapping a position + bandpass, download cutouts (serial and parallel), assemble a new multi-extension cutout-collection FITS file with a wavelength/URL summary table. |
| 3 | Understanding and Analyzing SPHEREx Mosaic Cubes | https://caltech-ipac.github.io/irsa-tutorials/spherex-mosaic | `irsa_tutorial_sources/spherex_mosaic.md` | 8 May 2026 | Load a pre-built Mosaic-Tool (x,y,λ) cube, extract a quick-look spectrum with `photutils` aperture photometry + annulus background subtraction, build a PAH 3.3 µm emission-line map, reproject and overlay a GALEX FUV image. **Most directly relevant notebook for resolved/semi-resolved galaxy spectroscopy.** |
| 4 | Understanding and Extracting the ePSF Extension in a SPHEREx Cutout | https://caltech-ipac.github.io/irsa-tutorials/spherex-psf | `irsa_tutorial_sources/spherex_psf.md` | 17 September 2026 (newest of the core set) | Map cutout pixels back to the parent LVF image, read the (e)PSF extension/calibration product depending on image version, pick the correct spatial PSF zone, and use `photutils.psf.ImagePSF` to render a native-resolution PSF stamp for forward modeling (e.g. Tractor). |
| 5 | SPHEREx Source Discovery Tool IRSA Demo | https://caltech-ipac.github.io/irsa-tutorials/spherex-source-discovery-tool-demo | `irsa_tutorial_sources/spherex_source_discovery/spherex_source_discovery_tool_demo.md` (+ `README.md`, `conda-spherex_sdt.yml`, and the `spherex_source_discovery_tool/` package) | 18 February 2026 | End-to-end demo of the standalone `spherex_source_discovery_tool` package: cloud (S3) image access, surface-brightness→flux-density conversion via solid-angle-pixel maps, background subtraction (`sep`), two-band image subtraction/reprojection to find red sources, `SExtractor` source extraction, interactive Firefly/bokeh source selection, and full aperture-photometry spectrum assembly with flags + variance propagation. |
| 6 | MOST (Moving Object Search Tool) queries — SPHEREx section | https://caltech-ipac.github.io/irsa-tutorials/techniques (techniques-and-tools) | `irsa_tutorial_sources/techniques-and-tools/MOST_queries.md` | not dated in text; "Support for SPHEREx in MOST was added in June 2026" | Tangential: shows `Most.query_object(..., catalog="spherex")` to find SPHEREx images intersecting a moving object's orbital path, and cutout retrieval from those images. Not about galaxy spectroscopy; included only because it is a genuine SPHEREx-touching notebook outside the `spherex/` folder, per task instructions. |

No SPHEREx notebooks were found under `simulated-data/`, `cloud-access-intro.md`, `irsa-hats-with-lsdb.md`, `Parallelize_Convolution.md`, or `SEDs_in_Firefly.md` (checked by grep on the raw source for "spherex", zero hits in all but `MOST_queries.md`). There is no separate "cloud-access" SPHEREx notebook; cloud (S3) access is instead demonstrated inline inside the Source Discovery Tool demo (#5).

---

## For each notebook: detailed walkthrough

### 1. `spherex_intro.md` — Introduction to SPHEREx Spectral Images

**Goal.** Query, open, and understand the structure of a single SPHEREx Level-2 Spectral Image MEF (multi-extension FITS), including its two WCS systems.

**Packages (no versions pinned anywhere in this repo's notebooks — all `pip install` lines are unpinned):**
```python
# Uncomment the next line to install dependencies if needed.
# %pip install numpy matplotlib astropy astroquery firefly-client
```
Imports:
```python
import http.client
import time
import urllib.error

import numpy as np
import matplotlib.pyplot as plt

from astropy.io import fits
from astropy.wcs import WCS
from astropy.table import Table
from astropy import units as u
from astropy.coordinates import SkyCoord

from astroquery.ipac.irsa import Irsa

from firefly_client import FireflyClient

# The time it takes to read SPHEREx files can exceed
# astropy's default timeout limit. Increase it.
from astropy.utils.data import conf

conf.remote_timeout = 120
```

**Data release / collections used.** States the notebook works with **QR3 and QR2**. Four SIA collections are enumerated:
- `spherex_qr3` — QR3 Wide Survey
- `spherex_qr3_deep` — QR3 Deep Survey
- `spherex_qr2` — QR2 Wide Survey
- `spherex_qr2_deep` — QR2 Deep Survey

Documented at "SPHEREx Data Access: APIs" (`https://caltech-ipac.github.io/spherex-archive-documentation/spherex-data-access#application-program-interfaces-apis`).

**Service endpoints / query pattern.**
```python
ra_deg = 304.693508808
dec_deg = 42.4436872991
coord = SkyCoord(ra_deg, dec_deg, unit="deg")
search_radius = 1 * u.arcsec

results = Irsa.query_sia(pos=(coord, search_radius), collection="spherex_qr2")
```
Tip given in text: list SPHEREx SIA collections dynamically with
```python
Irsa.list_collections(servicetype="SIA", filter="spherex")
```
**Gotcha (stated explicitly):** *"SPHEREx data are ingested on a weekly basis. Due to the nature of the ingestion process, availability via SIA will lag on the order of a day. To avoid this delay, users can access data through the browsable directories or the SPHEREx Data Explorer GUI ... or do a TAP query as shown in {ref}`spherex-cutouts`."*

**Retry pattern for transient read errors** (used identically across all notebooks that open FITS by URL):
```python
max_retries = 3
for attempt in range(max_retries):
    try:
        hdulist = fits.open(spectral_image_url)
        break
    except (TimeoutError, urllib.error.HTTPError, http.client.IncompleteRead):
        if attempt == max_retries - 1:
            raise
        time.sleep(10 * (attempt + 1))
```

**MEF extension list (verbatim from notebook text), 1-indexed:**
1. IMAGE — calibrated flux, MJy/sr, 2040×2040
2. FLAGS — per-pixel bitmap of status/processing flags
3. VARIANCE — per-pixel variance, (MJy/sr)^2
4. ZODI — modeled zodiacal light background, MJy/sr, **not subtracted from IMAGE**
5. PSF — 121-plane cube of oversampled PSFs on an 11×11 spatial grid, 101×101 px each, 10 oversampled px per 1 spectral-image px (0.615 arcsec)
6. WCS-WAVE — binary table lookup for spectral WCS (WAVE-TAB convention)

Detector bandpasses (Bands 1–6):
```
Band 1: 0.75–1.09 µm; R=39
Band 2: 1.10–1.62 µm; R=41
Band 3: 1.63–2.41 µm; R=41
Band 4: 2.42–3.82 µm; R=35
Band 5: 3.83–4.41 µm; R=112
Band 6: 4.42–5.00 µm; R=128
```

**Firefly visualization:**
```python
fc = FireflyClient.make_client(url="https://irsa.ipac.caltech.edu/irsaviewer")
fc.reinit_viewer()
fc.show_fits_image(file_input=spectral_image_url, plot_id="spectral_image", Title="Spectral Image")
```

**Spatial WCS.**
```python
wcs = WCS(spectral_image_header)
ra, dec = wcs.wcs.crval
x, y = wcs.world_to_pixel(SkyCoord(ra=ra, dec=dec, unit="deg"))
```

**Spectral WCS (WAVE-TAB, alternate WCS key "W").**
```python
spectral_wcs = WCS(header=hdulist["IMAGE"].header, fobj=hdulist, key="W")
spectral_wcs.sip = None  # must turn off SIP for the spectral WCS
wl, bw = spectral_wcs.pixel_to_world(x, y)
```
**Gotcha (explicit, cites an astropy issue):** loading the "W" WCS triggers an astropy INFO printout because SIP distortion coefficients from the main WCS are (ambiguously) carried into the alternate WCS; SIP must be manually disabled for the spectral WCS because wavelength-per-pixel is a property of the detector/filter and is independent of telescope optical distortion. Reference: `astropy/astropy#13105`.

**Per-pixel wavelength map:**
```python
(y, x) = np.indices(spectral_image.shape)
spectral_coords = spectral_wcs.pixel_to_world(x, y)
wavelength, bandwidth = spectral_coords
plt.imshow(wavelength.value, origin="lower", cmap="gray")
```

**WCSNAME keys:** the header has `WCSNAME*` — primary WCS (astrometric + SIP distortion), `WCSNAMEA` (zero-indexed pixel coords), `WCSNAMEW` (spectral: Wavelength+Bandwidth, references WCS-WAVE lookup table).

**Flags.** `spectral_image_header['L2 N_*']` shows 14 flag types; most pixels flagged as SOURCE. Full flag bit table is in Table 8 of the SPHEREx Explanatory Supplement PDF (`https://irsa.ipac.caltech.edu/data/SPHEREx/docs/SPHEREx_Expsupp_QR.pdf`). Flag definitions are also directly embedded in the FLAGS extension header: `flags_header['MP*']`.

**Runtime:** ~30 seconds.

---

### 2. `spherex_cutouts.md` — Download a collection of SPHEREx Spectral Image cutouts as a MEF

**Goal.** For one position on the sky, find *every* SPHEREx exposure (across time/detector), fetch a cutout from each, and repackage all cutouts into one summary + per-exposure MEF FITS file — i.e., this is the "assemble many exposures into one file" building block for spectrum extraction.

**Packages:**
```python
# !pip install numpy astropy pyvo matplotlib
import concurrent.futures
import http.client
import time
import urllib.error

import astropy.units as u
import matplotlib.pyplot as plt
import numpy as np
import pyvo
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy.table import Table
from astropy.wcs import WCS

import logging

logging.getLogger("astropy").setLevel(logging.ERROR)

from astropy.utils.data import conf

conf.remote_timeout = 120
```

**TAP endpoint and query — this is the canonical "find all exposures covering a position" pattern used across the notebook set.**
```python
service = pyvo.dal.TAPService("https://irsa.ipac.caltech.edu/TAP")

query = f"""
SELECT
    'https://irsa.ipac.caltech.edu/' || a.uri || '?center={ra.value},{dec.value}d&size={size.value}' AS uri,
    p.time_bounds_lower
FROM spherex.artifact a
JOIN spherex.plane p ON a.planeid = p.planeid
WHERE 1 = CONTAINS(POINT('ICRS', {ra.value}, {dec.value}), p.poly)
        AND p.energy_bandpassname = '{bandpass}'
ORDER BY p.time_bounds_lower
"""
results = service.search(query)
```
Table names: `spherex.artifact` (has `uri`, `planeid`), `spherex.plane` (has `planeid`, `poly`, `energy_bandpassname`, `time_bounds_lower`, `time_bounds_upper`, `provenance_version`, `em_min`, `em_max` — the last two are used elsewhere in `get_lambda_range`). Cutout access is via a query-string suffix on the base access URL: `?center={ra},{dec}d&size={size}` (degrees).

Bandpass values follow the pattern `'SPHEREx-D2'` (dash before the detector number), e.g. `bandpass = 'SPHEREx-D2'`.

**Stated advantage over SIA (explicit callout):** *"SPHEREx data are also available via SIA which can provide a simpler interface for many queries... An advantage of the method shown above is that it provides access to data immediately after ingestion (which occurs weekly) and is not subject to the same ~1 day delay as SIA."*

**Per-cutout processing function (computes wavelength at the cutout center and collects HDUs, renaming EXTNAME per cutout index so many cutouts can coexist in one MEF):**
```python
def process_cutout(row, ra, dec, cache):
    with fits.open(row["uri"], cache=cache) as hdulist:
        header = hdulist[1].header
        spatial_wcs = WCS(header)
        x, y = spatial_wcs.world_to_pixel(SkyCoord(ra=ra, dec=dec, unit="deg", frame="icrs"))
        spectral_wcs = WCS(header, fobj=hdulist, key="W")
        spectral_wcs.sip = None
        wavelength, bandwidth = spectral_wcs.pixel_to_world(x, y)
        row["central_wavelength"] = wavelength.to(u.micrometer).value
        hdus = []
        for hdu in hdulist[1:]:  # skip the primary header
            hdu.header["EXTNAME"] = f"{hdu.header['EXTNAME']}{row['cutout_index']}"
            hdus.append(hdu.copy())
        row["hdus"] = hdus
```
Wrapped with error handling that simply skips failed cutouts (row["hdus"] = None) on `TimeoutError`, `urllib.error.HTTPError`, `http.client.IncompleteRead` — text explicitly says: *"For science use cases, users may instead want to implement their own retry logic or error handling strategy."*

**Serial vs. parallel download (`ThreadPoolExecutor`).**
```python
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    futures = [
        executor.submit(process_cutout_with_error_handling, row, ra, dec, False)
        for row in results_table_parallel
    ]
    concurrent.futures.wait(futures)
```
**Timing gotchas (explicit):** serial ≈ 5–7 minutes for 700 images of cutout size 0.01°; parallel is "significantly faster." Tip: "A good value for the maximum number of workers is between 7 and 12 for a machine with 8 cores."

**Cache warning (explicit, repeated in multiple notebooks):** `fits.open(..., cache=True)` speeds up repeat runs but caches to `~/.astropy/cache/` and can accumulate a large volume if many cutouts are created — prefer `cache=False` for large cutout sets.

**Assembling the final MEF:**
```python
cols = fits.ColDefs(
    [
        fits.Column(name="cutout_index", format="J", array=results_table_parallel["cutout_index"], unit=""),
        fits.Column(
            name="observation_date", format="D", array=results_table_parallel["time_bounds_lower"], unit="d"
        ),
        fits.Column(
            name="central_wavelength",
            format="D",
            array=results_table_parallel["central_wavelength"],
            unit="um",
        ),
        fits.Column(name="access_url", format="A200", array=results_table_parallel["uri"], unit=""),
    ]
)
table_hdu = fits.BinTableHDU.from_columns(cols)
table_hdu.header["EXTNAME"] = "CUTOUT_INFO"

primary_hdu = fits.PrimaryHDU()
hdulist_list = [primary_hdu, table_hdu]
hdulist_list.extend(hdu for fits_hdulist in results_table_parallel["hdus"] for hdu in fits_hdulist)
combined_hdulist = fits.HDUList(hdulist_list)
combined_hdulist.writeto(output_filename, overwrite=True)
```

**Example target:** M101 (Pinwheel Galaxy), RA=210.80227°, Dec=54.34895°, size=0.1°, bandpass='SPHEREx-D2'.

**Runtime:** "about 3 minutes... on a machine with 8GB RAM and 4 CPU" (updated 5 March 2026).

---

### 3. `spherex_mosaic.md` — Understanding and Analyzing SPHEREx Mosaic Cubes ⭐ (most relevant for extended-source spectroscopy)

**Goal.** Open a pre-built SPHEREx mosaic cube (x, y, λ) generated by the **IRSA SPHEREx Mosaic Tool GUI** (no programmatic API exists for this tool as of the survey date), extract a quick-look spectrum from an aperture with background subtraction using `photutils`, build a narrow-band emission-line (PAH 3.3 µm) map by continuum subtraction, and cross-correlate with a reprojected GALEX FUV image.

**Packages:**
```python
# !pip install astropy matplotlib numpy photutils reproject astroquery
import copy
import numpy as np
from astropy.io import fits
from astropy.table import Table, vstack, hstack
from astropy.stats import sigma_clipped_stats, SigmaClip
from astropy.wcs import WCS
from astropy.coordinates import SkyCoord
from astropy.nddata import Cutout2D
import astropy.units as u
from photutils.aperture import CircularAperture, CircularAnnulus, ApertureStats, aperture_photometry
from astroquery.ipac.irsa import Irsa
from reproject import reproject_exact
import matplotlib.pyplot as plt
import matplotlib as mpl
```

**Data source and tool.** The cube itself is **not fetched via any API** — it was pre-generated with the [IRSA SPHEREx mosaic tool](https://irsa.ipac.caltech.edu/applications/spherex/tool-mosaic) GUI and is hosted at a static demo URL:
```python
fn_spherex = "https://irsa.ipac.caltech.edu/data/demos/notebooks/spherex/M101_irsa.fits"
```
Reproduction instructions given in text: enter "M101" in `Output Mosaic Center`, size = 30 arcmin × 30 arcmin, output pixel scale = 9 arcsec. **Explicit gotcha:** "Because the IRSA SPHEREx mosaic tool does not have an API, we have created and downloaded the mosaic already."

**Cube FITS layers (as described in text):** `IMAGE` (x,y,λ cube), `NHITS` (number of input images combined per pixel), `FLAGS` (outlier/overflow pixel flags), `SPECTRAL_CHANNELS` (binary table summarizing spectral channels used per plane), `WCS-WAVE` (binary table, wavelength info per plane). Final cube: **102 wavelength layers, 0.75–5 µm**.

**Unit conversion MJy/sr → mJy (explicit formula):**
$$[\rm{mJy}] = [\rm{MJy/sr}] \times 23.5045 \times (\rm{pixel\ scale})^2 / 1000$$
```python
with fits.open(fn_spherex) as hdul:
    hdul.info()
    wave_tab_tmp = Table(hdul["WCS-WAVE"].data)
    cube_hdr = hdul["IMAGE"].header
    pixscale_mosaic = np.abs(cube_hdr["CDELT1"] * 3600)  # arcsec/px
    cube_img = hdul["IMAGE"].data * 23.5045 * (pixscale_mosaic) ** 2 / 1e3  # MJy/sr -> mJy
    cube_hdr["BUNIT"] = "mjy"
    cube_wcs = WCS(cube_hdr, fobj=hdul).celestial  # 2D spatial WCS only, drop spectral axis
```
**Gotcha (explicit note):** pass `fobj=hdul` when building the WCS so astropy can resolve auxiliary lookup-table data (needed whenever a WAVE-TAB-style spectral WCS is present, even implicitly).

**Wavelength lookup table construction:**
```python
wave_tab = Table(
    [
        wave_tab_tmp["PLANE"][0],
        np.asarray([ww[0] for ww in wave_tab_tmp["WAVELENGTHS"][0]]),
        np.asarray([ww[0] for ww in wave_tab_tmp["BANDWIDTHS"][0]]),
    ],
    names=["plane", "wavelengths", "bandwidths"],
    dtype=[int, float, float],
)
```

**Quick-look spectrum extraction function — aperture photometry + annulus background subtraction per plane, i.e. the core "spectrum from a cube" recipe:**
```python
def measure_aperture_photometry_cube(cube, *, r_aperture_px=20, r_inner_px=60, r_outer_px=100, makeplot=True):
    def apphot_helper(img, position, aperture, annulus_aperture):
        sigclip = SigmaClip(sigma=3.0, maxiters=10)
        aperstats = ApertureStats(img, annulus_aperture, sigma_clip=sigclip)
        bkg_mean = aperstats.mean
        aperture_area = aperture.area_overlap(img)
        total_bkg = bkg_mean * aperture_area
        phot_table = aperture_photometry(img, aperture)
        phot_table["aperture_sum_bkgsub"] = phot_table["aperture_sum"] - total_bkg
        return phot_table

    position = (cube.shape[1] // 2, cube.shape[2] // 2)
    aperture = CircularAperture(position, r=r_aperture_px)
    annulus_aperture = CircularAnnulus(position, r_in=r_inner_px, r_out=r_outer_px)

    phot_all = vstack(
        [apphot_helper(cube[ii, :, :], position, aperture, annulus_aperture) for ii in range(cube.shape[0])]
    )
    phot_all["id"] = np.arange(cube.shape[0]) + 1
    phot_all.rename_column("id", "plane")
    ...
    return phot_all
```
**Explicit caveat in text:** "This function provides a very simple aperture photometry with background subtraction. The method can be extended. For example the function does not calculate photometric errors." (i.e., **no error propagation is implemented** in this notebook's spectrum extraction — a real gap for science use.)

**Explicit note about missing data:** "Note that there are some NaN values in that table. This is because of missing data for these specific planes. As the SPHEREx mission progresses, these missing data will be filled in."

**Redshift-aware emission-line plane selection (PAH 3.3 µm example, generalizes to any target redshift):**
```python
z = 0.0  # redshift of target
pah_obs = 3.3 * (1 + z)  # observed PAH wavelength in microns
pah_idx = np.argmin(np.abs(wave_tab["wavelengths"] - pah_obs))
planes_feature = [wave_tab["plane"][pah_idx]]
planes_continuum = list(wave_tab["plane"][[pah_idx - 2, pah_idx - 1, pah_idx + 1, pah_idx + 2]])
```
Line-map function (feature minus median continuum):
```python
def make_map(cube, planes_feature=[63], planes_continuum=[61, 62, 64, 65]):
    img_map = np.nansum(cube[np.asarray(planes_feature) - 1, :, :], axis=0) - np.nanmedian(
        cube[np.asarray(planes_continuum) - 1, :, :], axis=0
    )
    return img_map
```
**Gotcha:** plane IDs are 1-indexed; explicit warning to check for line contamination in continuum-plane selection by eye on the spectrum plot for other emission lines.

**GALEX cross-match / reprojection (for star-formation context, not SPHEREx-specific but shows the reproject workflow):**
```python
im_table = Irsa.query_sia(pos=(pos, 1 * u.arcsec), collection="spitzer_lvl")
sel = np.where(
    (im_table["dataproduct_subtype"] == "science")
    & (im_table["instrument_name"] == "GALEX")
    & (im_table["energy_bandpassname"] == "FUV")
)[0]
...
galex_cutout = Cutout2D(hdul[0].data, position=pos, size=size, wcs=WCS(hdul[0].header), mode="partial")
...
img_galex_rep, fp = reproject_exact(input_data=(img_galex, hdr_galex), output_projection=cube_wcs)
```
Collection used here: `spitzer_lvl` (Spitzer Local Volume Legacy Survey, hosts the GALEX ancillary images at IRSA). GALEX AB zero points hardcoded: `{"fuv":18.82, "nuv":20.08}`.

**Runtime:** "about 20 seconds ... on a machine with 32GB RAM and 8 CPU" (updated 8 May 2026).

---

### 4. `spherex_psf.md` — Understanding and Extracting the ePSF Extension in a SPHEREx Cutout

**Goal.** Correctly identify and extract the spatially-varying PSF (or ePSF) corresponding to a source position, across the version transition from the old "PSF" extension to the new "ePSF" binary-table extension, and prepare a native-resolution PSF stamp suitable for PSF-fitting/forward-modeling photometry (Tractor-style), which matters for resolved/point-source galaxy photometry.

**Explicit note: "This notebook is not intended for use of QR-1 data."**

**Packages:**
```python
# !pip install astropy matplotlib numpy pyvo photutils
import http.client
import glob
import re
import time
import urllib.error
import copy
from packaging.version import Version

import astropy.units as u
import matplotlib.pyplot as plt
import numpy as np
import pyvo
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy.table import Table
from astropy.wcs import WCS

from photutils.psf import ImagePSF

from astropy.utils.data import conf

conf.remote_timeout = 120
```

**TAP query (same pattern as notebook 2, no bandpass filter this time):**
```python
service = pyvo.dal.TAPService("https://irsa.ipac.caltech.edu/TAP")
query = f"""
SELECT
    'https://irsa.ipac.caltech.edu/' || a.uri || '?center={ra.value},{dec.value}d&size={size.value}' AS uri,
    p.time_bounds_lower, p.energy_bandpassname, p.time_bounds_lower, p.time_bounds_upper, p.provenance_version
FROM spherex.artifact a
JOIN spherex.plane p ON a.planeid = p.planeid
WHERE 1 = CONTAINS(POINT('ICRS', {ra.value}, {dec.value}), p.poly)
ORDER BY p.time_bounds_lower
"""
```
Adds `p.provenance_version` to the SELECT list — this is the field used downstream to decide the PSF-handling branch.

**Determine image pipeline version:**
```python
def parse_version(v):
    modifier = None
    base = v
    if "+" in v:
        base, modifier = v.split("+", 1)
    base_version = Version(base)
    if modifier is None:
        return (0, base_version, 0)
    m = re.search(r"\d+", modifier)
    modnum = int(m.group()) if m else 0
    return (1, base_version, modnum)


this_version = parse_version(image_hdul["PRIMARY"].header["VERSION"])
```

**Map cutout pixel → parent-image pixel (needed because the PSF is spatially variable over the *parent* LVF image, not the cutout):**
```python
wcs = WCS(cutout_header)
xpix_cutout, ypix_cutout = wcs.world_to_pixel(SkyCoord(ra=ra, dec=dec))

crpix1a = cutout_header["CRPIX1A"]
crpix2a = cutout_header["CRPIX2A"]
xpix_orig = 1 + xpix_cutout - crpix1a
ypix_orig = 1 + ypix_cutout - crpix2a
```

**Version-dependent PSF extension (key gotcha of this whole notebook):**
- Versions **< 7.0** (QR-1, QR-2): old `PSF` layer only. **"We advise the users not to use the older PSFs."**
- Versions **≥ 7.0** (QR-3, DR1): new `EPSF` binary-table layer directly in the image FITS. **"We advise the users to only use the new ePSF for scientific analyses."**

For old-version images, the ePSF calibration product must instead be pulled from the SPHEREx AWS S3 bucket, keyed by detector:
```python
ePSF_calibs = {
    "1": "https://nasa-irsa-spherex.s3.us-east-1.amazonaws.com/qr3/epsf/cal-epsf-v1-2026-191/1/epsf_D1_spx_cal-epsf-v1-2026-191.fits",
    "2": "https://nasa-irsa-spherex.s3.us-east-1.amazonaws.com/qr3/epsf/cal-epsf-v1-2026-191/2/epsf_D2_spx_cal-epsf-v1-2026-191.fits",
    "3": "https://nasa-irsa-spherex.s3.us-east-1.amazonaws.com/qr3/epsf/cal-epsf-v2-2026-191/3/epsf_D3_spx_cal-epsf-v2-2026-191.fits",
    "4": "https://nasa-irsa-spherex.s3.us-east-1.amazonaws.com/qr3/epsf/cal-epsf-v1-2026-191/4/epsf_D4_spx_cal-epsf-v1-2026-191.fits",
    "5": "https://nasa-irsa-spherex.s3.us-east-1.amazonaws.com/qr3/epsf/cal-epsf-v1-2026-191/5/epsf_D5_spx_cal-epsf-v1-2026-191.fits",
    "6": "https://nasa-irsa-spherex.s3.us-east-1.amazonaws.com/qr3/epsf/cal-epsf-v1-2026-191/6/epsf_D6_spx_cal-epsf-v1-2026-191.fits",
}
```
Base bucket index: `https://nasa-irsa-spherex.s3.us-east-1.amazonaws.com/index.html`; calibration products live under `<release>/<dataset_type>/<version-tag>/<detector>/`. The calibration file additionally contains an `EPSF_MOSAIC` layer (a full-detector PSF-zone mosaic image), **not present in the per-exposure LVF images**, useful for quickly visualizing all zones on a detector.

**Format of the ePSF binary table:** columns include `BINX`, `BINY` (0-indexed zone IDs), `XCENTER`, `YCENTER` (zone center in parent-image pixels), `NEFF_MEAN` (PSF effective area), `CWAVE` (center wavelength of the zone), and `EPSF` (a 2D-array-valued column, the oversampled PSF stamp itself). Header keywords: `OVSMPX`, `OVSMPY` (oversampling factors), `TDIM11` (oversampled PSF stamp shape), `NAXIS2` (total number of zones).

**Nearest-zone lookup:**
```python
dist = np.sqrt((xpix_orig - epsf_bintable["XCENTER"]) ** 2 + (ypix_orig - epsf_bintable["YCENTER"]) ** 2)
sel_zone = np.where(dist == np.min(dist))[0][0]
bin_x = epsf_bintable["BINX"][sel_zone]
bin_y = epsf_bintable["BINY"][sel_zone]
sel = np.where((epsf_bintable["BINX"] == bin_x) & (epsf_bintable["BINY"] == bin_y))[0][0]
epsf = epsf_bintable["EPSF"][sel]
```

**Forward-modeling section (Tractor use case) — explicit, detailed warning:**
> "The PSF returned by this notebook is oversampled relative to the native SPHEREx detector pixel grid... Tools such as Tractor do not expect an oversampled PSF directly. Instead, they require a PSF that is pixel-integrated at the native detector resolution and evaluated at the correct sub-pixel phase of the source. If you pass the oversampled PSF directly into Tractor without resampling, the effective PSF width and normalization will be incorrect, which can lead to systematic differences relative to the SPHEREx Spectrophotometry Tool."

Required steps stated: (1) shift the oversampled PSF to the source's sub-pixel position, (2) downsample/integrate onto the native pixel grid, (3) normalize before passing to Tractor. Uses `photutils.psf.ImagePSF` (text notes: "in later versions of photutils this is changed to the `ImagePSF` class" from the older `EPSFModel`).
```python
from photutils.psf import ImagePSF

ovs = (int(epsf_header.get("OVSMPY", 1)), int(epsf_header.get("OVSMPX", 1)))
epsf_model = ImagePSF(data=epsf, oversampling=ovs)


def render_epsf_stamp_centered(
    epsf: ImagePSF, x0: float, y0: float, stamp_size: int = 11, unit_flux: bool = True
):
    x0 = float(x0)
    y0 = float(y0)
    half = (stamp_size - 1) / 2.0
    x_ll = int(np.floor(x0 - half))
    y_ll = int(np.floor(y0 - half))
    x_centers = x_ll + np.arange(stamp_size)
    y_centers = y_ll + np.arange(stamp_size)
    Y, X = np.meshgrid(y_centers, x_centers, indexing="ij")
    psf_stamp = epsf.evaluate(X, Y, flux=1.0, x_0=x0, y_0=y0)
    if unit_flux:
        s = psf_stamp.sum()
        if s > 0 and np.isfinite(s):
            psf_stamp /= s
    return psf_stamp, x_ll, y_ll
```

**Runtime:** ~30 seconds. **Updated 17 September 2026 — the most recently updated notebook in the whole set** (5 days before this survey).

---

### 5. `spherex_source_discovery_tool_demo.md` (+ package) — SPHEREx Source Discovery Tool IRSA Demo

**Goal.** Full pipeline demo of a standalone package (`spherex_source_discovery_tool`, shipped in the same repo directory) for: cloud-native (S3) SPHEREx image access, radiometric calibration to physical flux density, background estimation, two-color image differencing to flag red sources, `SExtractor`-based source extraction, interactive Firefly/bokeh source selection, and — critically — **complete aperture-photometry spectrum assembly with flag and variance propagation across many exposures**, i.e. the closest thing in this notebook set to "extract a reliable calibrated spectrum with uncertainties for a chosen source."

**Environment.** Not `pip install` lines but a full conda env file `conda-spherex_sdt.yml` (verbatim, **no version pins on any package**):
```yaml
name: spherex_sdt
channels:
  - conda-forge
dependencies:
  - astromatic-source-extractor
  - astropy
  - astroquery
  - bokeh
  - ipykernel
  - ipywidgets
  - numpy
  - pandas
  - photutils
  - pip
  - regions
  - reproject
  - scipy
  - sep
  - tqdm
  - pip:
    - firefly-client
```
Includes explicit setup instructions for both local machines and the **NASA Fornax Science Console**, the only mention of a specific cloud/science-platform anywhere in the SPHEREx notebook set (Fornax requires `conda-*.yml` naming convention and `setup-conda-env --user`).

**Imports (full list, including the local package modules):**
```python
import concurrent.futures
import copy
import json
import os
import io
import pickle
import time
from concurrent.futures import as_completed

import numpy as np
import pyvo
import sep
import astropy.units as u
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy.nddata import Cutout2D
from astropy.table import Table
from astropy.units import Unit
from astropy.wcs import WCS
from astroquery.ipac.irsa import Irsa
from bokeh.io import output_notebook
from bokeh.resources import INLINE
from firefly_client import FireflyClient
from reproject import reproject_exact, reproject_interp

from spherex_source_discovery_tool.aperture_photometry import build_phot_table, grab_star
from spherex_source_discovery_tool.bokeh_viz import (
    plot_apertures,
    plot_spectrum,
    plot_subtracted_trio,
    plot_overlap_trio,
)
from spherex_source_discovery_tool.firefly_viz import preview_query
from spherex_source_discovery_tool.sdt_utils import (
    format_extracted,
    get_filename,
    get_exp_id,
    get_obs_id,
    results_summary,
    get_lambda_range,
)
from spherex_source_discovery_tool.source_extraction import run_sextractor, get_sextractor_file
```

**Time-sensitivity caveat, called out explicitly (`{attention}` directive):**
> "The query parameters below are valid as of **February 2026**, but will need to be updated as the mission proceeds. Specifically, the ephemeral query parameters *will* change for future SPHEREx data releases."
```python
data_release = "qr2"
sia_collection = f"spherex_{data_release}"

dataset_type = "solid_angle_pixel_map"
sapm_collection = "cal-sapm-v2-2025-164"
sapm_s3 = [
    f"nasa-irsa-spherex/{data_release}/{dataset_type}/{sapm_collection}/{k}/"
    f"{dataset_type}_D{k}_spx_{sapm_collection}.fits"
    for k in range(1, 7)
]
```

**SIA search + collection filtering by detector/bandpass:**
```python
coord = SkyCoord(150.7817877, 3.3502204, unit="deg")  # near COSMOS field
search_radius = 50 * u.arcsec
results = Irsa.query_sia(pos=(coord, search_radius), collection=sia_collection)

d2_result = results[results["energy_bandpassname"] == "SPHEREx-D2"][0]
results_by_detector = results.group_by("energy_bandpassname")
d4_result = results_by_detector.groups[3][0]
```

**Cloud (S3) direct access — the only place in the notebook set that reads SPHEREx FITS directly from AWS S3 rather than over HTTPS from IRSA:**
```python
def get_s3_fpath(cloud_access):
    cloud_info = json.loads(cloud_access)  # SIA result's 'cloud_access' column, a JSON string
    bucket_name = cloud_info["aws"]["bucket_name"]
    key = cloud_info["aws"]["key"]
    return f"{bucket_name}/{key}"


s3_fpath_d2 = get_s3_fpath(d2_result["cloud_access"])
with fits.open(f"s3://{s3_fpath_d2}", fsspec_kwargs={"anon": True}) as hdul2:
    img_hdu2 = hdul2["IMAGE"].copy()
    ...
```
Explicit fallback note: to download from IPAC instead of the cloud, simply `fits.open(d2_result['access_url'])`.

**Radiometric calibration — surface brightness → flux density using the Solid Angle Pixel Map (SAPM) calibration product (also fetched from S3):**
```python
img_data2 = (
    (img_data2 * Unit(img_hdr2["BUNIT"])).to(u.uJy / u.arcsec**2) * (sapm_data2 * Unit(sapm_hdr2["BUNIT"]))
).value
img_hdu2.header["BUNIT"] = "uJy"
```

**Background subtraction with `sep`, with an explicit byte-order gotcha:**
```python
# WARNING: sep only supports native byte order arrays.
img.astype(img.dtype.newbyteorder("="))

bkg2 = sep.Background(img_data2.astype(img_data2.dtype.newbyteorder("=")), bw=64, bh=64, fw=11, fh=11)
img_data2 = img_data2 - bkg2
```

**Flag-based masking, with the exact flag bit used for "good" pixels:**
```python
mask2 = np.zeros(flags_data2.shape) * np.nan
mask2[(flags_data2 == 2097152) | (flags_data2 == 2) | (flags_data2 == 0)] = 1
```
Text explains: `2097152` = bit 21 = pixels *not* contaminated by errors/transients/cosmic rays; explicitly says they ignore the OVERFLOW flag because it is coincident with SUR_ERROR. Full flag bit reference: `https://irsa.ipac.caltech.edu/onlinehelp/spherex/spherex/sp.html#explorebitflags`.

**Two-detector reprojection for differencing, with explicit warnings on method choice/cost:**
```python
# WARNING:
# - reproject_exact conserves total flux but is slower (2-3 min for this cell).
# - reproject_interp (bilinear) conservatively extends single-pixel NaNs into multi-pixel NaN regions.
img_data2_reproj, footprint = reproject_exact(input_data=(img_data2, img_hdr2), output_projection=img_hdr4)
mask2_reproj, _ = reproject_interp(input_data=(mask2, img_hdr2), output_projection=img_hdr4)
```

**SExtractor invocation (via the local `spherex_source_discovery_tool` package), requiring absolute paths:**
```python
sxt_config = get_sextractor_file("default_sdt.sex", package="spherex_source_discovery_tool")
sxt_params = get_sextractor_file("default_sdt.param", package="spherex_source_discovery_tool")
sxt_nnw = get_sextractor_file("default.nnw", package="spherex_source_discovery_tool")
sxt_conv = get_sextractor_file("default.conv", package="spherex_source_discovery_tool")
run_sextractor(
    os.path.realpath(subtracted_cut_path), sxt_config, sxt_params, subtracted_cat, sxt_nnw, sxt_conv
)
```
Catalog columns `ALPHA_J2000`/`DELTA_J2000` renamed to `ra`/`dec` — "especially important for Firefly to be able to read the table out of the box."

**Full spectrum-assembly pipeline (the payoff of this notebook) — `build_phot_table()` in `aperture_photometry.py`, called per selected source over *all* TAP-matched cutouts:**
```python
service = pyvo.dal.TAPService("https://irsa.ipac.caltech.edu/TAP")
size = 0.1 * u.degree
query = f"""
SELECT
    'https://irsa.ipac.caltech.edu/' || a.uri || '?center={matched_stars["ra"][0]},{matched_stars["dec"][0]}d&size={size.value}' AS uri,
    p.time_bounds_lower
FROM spherex.artifact a
JOIN spherex.plane p ON a.planeid = p.planeid
WHERE 1 = CONTAINS(POINT('ICRS', {matched_stars["ra"][0]}, {matched_stars["dec"][0]}), p.poly)
ORDER BY p.time_bounds_lower
"""
...
aperture_radii = [3.0, 4.0, 5.0]  # pixels
build_phot_table(results_table, matched_stars, aperture_radii, phot_path, sapm_s3)
```
Inside `build_phot_table` (full code saved locally; key excerpts):
- Converts `IMAGE` [MJy/sr] → [mJy/pix] using a `sa_mjy_scale_map()` derived from the solid-angle pixel map (falls back to a constant `6.15²` arcsec²/pix if no SAPM is available for that detector).
- Propagates `VARIANCE` the same way: `var_mjy2_pix2 = var_(MJy/sr)^2 * scale_map^2`.
- Per-pixel wavelength/bandpass grids from the spectral WCS, then bilinearly interpolated to each source's exact (non-integer) pixel position (`interp2d_like`).
- Per-exposure flag masks built from the FLAGS extension header's `MP_*` keyword dictionary (flag-name → bit number), each expanded into a boolean image via `(flags & (1 << bit)) > 0`.
- `extract_photometry()` does circular-aperture photometry (`method='subpixel', subpixels=5`) at **multiple radii simultaneously** with a **circular-annulus** background (default `annulus_rad_in=7, annulus_rad_out=16` px, sigma-clipped median), and `extract_dqf()` sums each flag's pixel count within each aperture (so downstream code can reject or QA points with contaminated apertures).
- AB magnitude conversion with a 3631 Jy zero point: `ab = -2.5*log10(f_jy/3631.0)`.
- Result is serialized to a pickle (`phot_path`) as a per-source `obs_log` list of dicts (one dict per exposure: wavelength, bandwidth, per-aperture background-subtracted flux, variance sum, AB mag, per-flag bad-pixel counts, image_id, mjd_center).

**Final spectrum retrieval, with flag filtering and formal AB-magnitude error propagation:**
```python
bad_flags = [
    "TRANSIENT",
    "OVERFLOW",
    "SUR_ERROR",
    "PHANTOM",
    "REFERENCE",
    "NONFUNC",
    "DICHROIC",
    "MISSING_DATA",
    "HOT",
    "COLD",
    "FULLSAMPLE",
    "PHANMISS",
    "NONLINEAR",
    "PERSIST",
    "OUTLIER",
]
ap_rad = 3.0
wvl, bdw, abmags, abmag_errs, flx, var, n_bad = grab_star(
    obs_log_entry=all_stars_band_phot["obs_log"][targ], ap_rad=ap_rad, bad_flags=bad_flags
)
```
In `grab_star` (verbatim error formula):
```python
_AB_DMAG_FACTOR = 2.5 / np.log(10)  # 1.0857362047581296
ab_errs = _AB_DMAG_FACTOR * (np.sqrt(np.maximum(variances, 0.0)) / fluxes)
```
This is the **only notebook in the whole set that propagates photometric uncertainty into the final spectrum** (the mosaic-cube notebook explicitly does not).

**Runtime:** ~5 minutes. **Updated 18 February 2026** (oldest of the core notebooks; predates the ePSF notebook's 7 September update and the mosaic notebook's May update, and states its own query parameters are already time-sensitive).

**Attribution note:** "The Source Discovery Tool aperture photometry functions are adapted from code by Zafar Rustamkulov." DOI cited for QR2 data: `10.26131/IRSA629`.

---

### 6. `MOST_queries.md` — SPHEREx section (tangential)

Not about galaxy spectroscopy, included for completeness per task scope. Key snippet:
```python
most_output = Most.query_object(
    output_mode="Regular",
    obj_name="20000004",
    obs_begin="2025-08-01",
    obs_end="2025-08-31",
    catalog="spherex",
)
```
Text states: "Support for SPHEREx in MOST was added in June 2026... SPHEREx images can be obtained in much the same way as the WISE examples shown above by setting the `'catalog'` argument to `"spherex"`... A cutout can be produced in much the same way as before, although minor changes are needed as the headers of the SPHEREx images differ from those of WISE." Full instructions link: `https://irsa.ipac.caltech.edu/applications/MOST/instructions.html`.

---

## Cross-cutting patterns

**Finding all exposures covering a position.** Two equivalent, both-demonstrated methods:
1. `astroquery.ipac.irsa.Irsa.query_sia(pos=(coord, radius), collection='spherex_qr2'/'spherex_qr3'/..._deep)` — simple, but SIA lags ingestion by ~1 day (stated explicitly, twice, in notebooks 1 and 2/4).
2. Direct TAP/ADQL query against `pyvo.dal.TAPService("https://irsa.ipac.caltech.edu/TAP")` on tables `spherex.artifact` (joined via `planeid`) and `spherex.plane`, filtering with `CONTAINS(POINT('ICRS', ra, dec), p.poly)` and optionally `p.energy_bandpassname = 'SPHEREx-Dn'`. This is preferred whenever near-real-time ingestion access matters, and is the pattern reused in notebooks 2, 4, and 5's photometry step. The TAP `uri` column is transformed into a cutout access URL by string-concatenating a `?center=ra,decd&size=sized` query string onto the artifact URI.

**Building a spectrum from many exposures.** Two distinct strategies appear:
- **Mosaic-cube approach** (notebook 3): pre-combine many exposures into a wavelength-ordered cube offline via the GUI-only Mosaic Tool, then do aperture photometry plane-by-plane with `photutils` (`CircularAperture`+`CircularAnnulus`, sigma-clipped background). Simple but has **no error propagation** and depends on a tool with no programmatic API.
- **Per-exposure aperture-photometry approach** (notebooks 2 and 5): query/download every individual exposure cutout covering the source, extract flux + variance + flags per exposure at the source's exact pixel position, and assemble a scatter "spectrum" (wavelength vs. flux) point-by-point across exposures/detectors. This is more laborious but is the only approach with formal uncertainty propagation and per-exposure QA flagging (notebook 5).

**Spectral WCS handling.** Universally handled via the WAVE-TAB FITS convention, loaded as an alternate WCS with key `"W"`: `WCS(header, fobj=hdulist, key="W")`, always followed by `spectral_wcs.sip = None` to strip inherited SIP distortion coefficients (an astropy quirk, cited to `astropy/astropy#13105`). `pixel_to_world(x, y)` returns a `(wavelength, bandwidth)` tuple/Quantity pair. This exact recipe is repeated verbatim in notebooks 1, 2, 4, and 5.

**PSF zone handling.** Only notebook 4 covers this in depth. Two eras: old `PSF` cube extension (pre-v7.0 pipeline, QR-1/QR-2, discouraged) vs. new `EPSF` binary-table extension (v7.0+, QR-3/DR1, recommended) with per-zone metadata (`BINX`/`BINY`/`XCENTER`/`YCENTER`/`NEFF_MEAN`/`CWAVE`) and an oversampled 2D PSF array per zone. Zone selection is nearest-neighbor in parent-image pixel space (Euclidean distance to `(XCENTER, YCENTER)`). For old-version images, the ePSF must be retrieved from static per-detector S3 calibration files rather than the image itself; these files additionally carry an `EPSF_MOSAIC` full-detector visualization layer absent from science images.

**Flags/variance handling.** VARIANCE is a per-pixel plane, propagated by the SAPM-derived scale-map squared in notebook 5's `build_phot_table`, but *not at all* in the mosaic notebook. FLAGS is a bitmask; flag-name→bit mapping is read directly from the FLAGS header's `MP_*` keywords (`{key[3:]: header[key] for key in header if key.startswith('MP_')}`) rather than hardcoded, which is the most robust pattern shown. Notebook 5 sums bad-flag pixel counts per aperture per flag and exposes them for downstream QA filtering (`bad_flags` list, 15 named flags including TRANSIENT, OVERFLOW, SUR_ERROR, HOT, COLD, NONLINEAR, PERSIST, OUTLIER, etc.).

**ZODI extension.** Only described, never used quantitatively, anywhere in the notebook set: notebook 1 states it is a modeled zodiacal-light background in MJy/sr and explicitly **not subtracted** from IMAGE. No notebook demonstrates zodiacal-light subtraction, modeling, or use in flux/spectrum extraction.

**Photometry: point vs. extended sources.** All quantitative photometry shown is **simple circular-aperture photometry with an annulus background** (`photutils.aperture`), applied identically whether the target is effectively a point source (SExtractor-detected sources in notebook 5) or an extended galaxy (M101 in notebook 3). No notebook demonstrates elliptical/Sérsic apertures, isophotal photometry, or PSF-matched multi-band extended-source photometry. The only PSF-aware modeling shown (notebook 4) is for point-source forward modeling (Tractor) via `photutils.psf.ImagePSF`, explicitly not extended to galaxies.

**Catalogs / forced photometry products.** None of the official notebooks query or use a pre-built SPHEREx source catalog or forced-photometry table; source discovery is always done "from scratch" per notebook (SExtractor in notebook 5) rather than by querying an IRSA catalog service. No mention of any released SPHEREx point-source or galaxy catalog table in the TAP schema beyond `spherex.artifact`/`spherex.plane` (image/exposure metadata, not photometric source catalogs).

**Cloud data.** Only notebook 5 reads data directly from the SPHEREx AWS S3 bucket (`nasa-irsa-spherex.s3.us-east-1.amazonaws.com`, `fits.open('s3://...', fsspec_kwargs={"anon": True})`), using the `cloud_access` JSON column returned by `Irsa.query_sia()`. It is also the only notebook mentioning a specific science platform (**NASA Fornax Science Console**) with concrete setup instructions. Notebook 4 references the same S3 bucket for static calibration products (ePSF, and by extension solid-angle-pixel-map files) but not for science images.

---

## What the notebooks do NOT cover (gaps relevant to extracting galaxy spectra and stacking)

- **No formal spectrum-extraction / stacking utility for extended, resolved galaxies.** The mosaic-cube notebook's aperture-photometry function is described by its own authors as "very simple" and explicitly does not compute photometric errors. There is no shown method for spatially resolved (spaxel-by-spaxel) spectral extraction across a galaxy, no PSF-matching across the cube's wavelength-dependent PSF, and no handling of the fact that SPHEREx's native PSF/resolution varies strongly with wavelength within the same "cube" (0.75–5 µm, R≈35–128) — this directly matters for post-starburst galaxy work where central/nuclear vs. extended emission must be separated.
- **No programmatic access to the Mosaic Tool.** Cube generation for arbitrary targets requires manual GUI interaction; there is no shown API/CLI to batch-generate cubes for a sample of galaxies, which is a hard blocker for any sample-based post-starburst-galaxy study.
- **No error propagation in the cube-based quick-look spectrum**, only in the per-exposure aperture-photometry pipeline (notebook 5), and that pipeline in turn has no cube/mosaic capability — the two approaches are not unified.
- **No PSF-matched or elliptical/Kron aperture photometry for extended sources**; PSF handling (notebook 4) is scoped entirely to point-source forward modeling.
- **No demonstrated combination of multiple individual exposures into a single higher-S/N mosaic/coadd via a documented Python API** (only the GUI Mosaic Tool, or ad hoc per-exposure cutout stacking as in notebooks 2/5, which stop short of true image coaddition — they only collect/organize cutouts, they do not average/coadd overlapping pixels).
- **No zodiacal-light subtraction workflow**, despite the ZODI extension being provided and explicitly not pre-subtracted — a nontrivial background component for faint/extended low-surface-brightness galaxy light.
- **No treatment of source blending / deblending** for galaxies close to other sources (SExtractor deblending parameters exist in `default_sdt.sex`/`default_sdt.param` but are not discussed in the narrative text).
- **No worked example of a SPHEREx-based galaxy SED/spectrum being compared to or calibrated against ancillary spectroscopy** (e.g., no redshift-fitting, no cross-check against SDSS/other spectra) beyond the qualitative PAH-vs-GALEX correlation in notebook 3.
- **No discussion of confusion/crowding** in the SPHEREx beam (~6.2 arcsec pixels, PSF FWHM comparable to or larger than many nearby-galaxy angular sizes) for semi-resolved sources — directly relevant to "semi-resolved" post-starburst targets, and not addressed anywhere.
- **No unpinned-vs-pinned dependency guidance**: every `pip`/`conda` environment spec in the repo is unpinned (`environment.yml`/`%pip install` list bare package names), so exact reproducibility of a given notebook run is not guaranteed by the source alone.
- **No spectral-response / bandpass-transmission-curve product usage** (i.e., no example folding a model SED through the actual per-pixel LVF transmission curve rather than treating each pixel as a delta-function wavelength+bandwidth pair).

---

## Items that look new since ~March 2026

- **`spherex_psf.md`** (ePSF notebook) — **updated 17 September 2026**, only 5 days before this survey; the newest core notebook, and the only one incorporating the **QR-3/DR1 `EPSF` binary-table extension** and its `packaging.version`-based version-detection logic, the v7.0 PSF/ePSF pipeline cutover, and the Tractor forward-modeling section with detailed oversampling/downsampling guidance.
- **`spherex_mosaic.md`** — updated **8 May 2026**; introduces the Mosaic Tool cube workflow, the PAH 3.3 µm line-map recipe with redshift-aware plane selection, and the GALEX cross-correlation — none of this existed in the March baseline (`spherex_intro.md`/`spherex_cutouts.md` were both "Updated: 5 March 2026").
- **QR3 collections** (`spherex_qr3`, `spherex_qr3_deep`) and the **QR2→QR3 pipeline version 7.0 cutover** are both post-March additions reflected across the "intro" and "psf" notebooks; the source-discovery-tool demo (18 February 2026) still hardcodes `data_release = "qr2"` and its own text flags this as ephemeral/soon-to-be-outdated.
- **MOST support for SPHEREx** — added June 2026 per the `MOST_queries.md` text, i.e., after the March baseline, though this is a moving-object tool, not relevant to galaxy spectral extraction.
- All five core SPHEREx notebooks now live in a single gallery page (`spherex.md`) with a `{notebook-gallery}` MyST directive referencing a `notebook_metadata.yml` file (not independently fetched in this survey; its presence suggests the tutorial site tracks structured per-notebook metadata, e.g., for search/indexing, that could be queried directly if needed later).

---

## Open questions

1. Does the SPHEREx archive provide (or plan to provide) a **programmatic API for the Mosaic Tool**, so that cube generation for a sample of galaxies (rather than one GUI-driven cube at a time) becomes feasible? None of the notebooks address this, and it is explicitly stated as a current gap.
2. Is there a documented, science-team-endorsed method for **coadding/stacking multiple SPHEREx exposures at the same wavelength** (beyond simply collecting per-exposure cutouts), and if so, does it propagate variance and flags consistently? Not shown in any tutorial.
2a. Related: is a variance-weighted or inverse-variance stacking recipe for the per-exposure spectrum-assembly approach (notebook 5) documented anywhere in the SPHEREx Explanatory Supplement, which was referenced repeatedly but not itself fetched in this survey (`https://irsa.ipac.caltech.edu/data/SPHEREx/docs/SPHEREx_Expsupp_QR.pdf`)?
3. What is the actual, current **`spherex.plane`/`spherex.artifact` TAP schema** in full (all column names, not just the subset used in these queries)? A full schema dump (e.g., `TAP_SCHEMA.columns` for the `spherex` schema) was not fetched in this survey and would clarify whether additional columns (depth, PSF FWHM per plane, S/N estimates) exist that could simplify galaxy-spectrum QA.
4. Does IRSA provide any **forced-photometry or pre-extracted source catalog** for SPHEREx (as opposed to only image/exposure-level metadata via TAP/SIA)? None of the tutorials reference one, but this was not independently confirmed against the archive's catalog holdings outside the notebooks.
5. For post-starburst galaxies at typical redshifts, will nuclear vs. extended (semi-resolved) light separation require PSF-matched multi-wavelength apertures — and if so, is there an official recommended approach beyond the point-source Tractor guidance in `spherex_psf.md`, e.g. in the SPHEREx Explanatory Supplement or forthcoming tutorials?
6. Should the zodiacal light (ZODI extension) be subtracted for faint/extended galaxy photometry, and if so, is there an official recipe? The notebooks state it is not pre-subtracted but do not say whether/how users should subtract it themselves.

---

*All source `.md` files consulted are saved verbatim under `docs/reference_notes/irsa_tutorial_sources/` (see file tree: `spherex.md`, `spherex_intro.md`, `spherex_cutouts.md`, `spherex_mosaic.md`, `spherex_psf.md`, `spherex_source_discovery/README.md`, `spherex_source_discovery/conda-spherex_sdt.yml`, `spherex_source_discovery/spherex_source_discovery_tool_demo.md`, `spherex_source_discovery/spherex_source_discovery_tool/{aperture_photometry,bokeh_viz,firefly_viz,sdt_utils,source_extraction}.py`, `techniques-and-tools/MOST_queries.md`).*
