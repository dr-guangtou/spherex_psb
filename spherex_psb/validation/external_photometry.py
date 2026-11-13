"""External broadband photometry for validation: SDSS z (SkyServer), 2MASS XSC/PSC and AllWISE (IRSA),
Legacy Survey DR10 forced WISE W1/W2 (Data Lab), and synthetic photometry of the SPHEREx SED with speclite.

Zero points: SDSS and Legacy fluxes are AB (3631 Jy; Legacy nanomaggies = 3.631 uJy); 2MASS Vega zero points
1594, 1024, 666.7 Jy (Cohen et al. 2003); WISE Vega zero points 309.54, 171.787 Jy (Jarrett et al. 2011).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

VEGA_ZERO_POINT_JY = {"J": 1594.0, "H": 1024.0, "Ks": 666.7, "W1": 309.54, "W2": 171.787}
FILTERS = {
    "z": "sdss2010-z",
    "J": "twomass-J",
    "H": "twomass-H",
    "Ks": "twomass-Ks",
    "W1": "wise2010-W1",
    "W2": "wise2010-W2",
}
NANOMAGGY_UJY = 3.631


def vega_to_ujy(mag: float, err: float, band: str) -> tuple[float, float]:
    flux = VEGA_ZERO_POINT_JY[band] * 10 ** (-0.4 * mag) * 1e6
    return flux, flux * 0.4 * np.log(10) * err


def ab_to_ujy(mag: float, err: float) -> tuple[float, float]:
    flux = 3631e6 * 10 ** (-0.4 * mag)
    return flux, flux * 0.4 * np.log(10) * err


def query_external(
    ra: float, dec: float, sdss_objid: str | None = None, legacy: pd.DataFrame | None = None
) -> pd.DataFrame:
    """One row per band: band, origin, aperture description, flux_ujy, flux_err_ujy, wavelength_um."""
    import astropy.units as u
    from astropy.coordinates import SkyCoord
    from astroquery.ipac.irsa import Irsa

    from spherex_psb.extraction.catalog import _skyserver

    rows = []
    coord = SkyCoord(ra, dec, unit="deg")
    xsc = Irsa.query_region(coord, catalog="fp_xsc", spatial="Cone", radius=15 * u.arcsec)
    if len(xsc):
        row = xsc[0]
        for band, column in (("J", "j_m_k20fe"), ("H", "h_m_k20fe"), ("Ks", "k_m_k20fe")):
            if not np.ma.is_masked(row[column]):
                flux, err = vega_to_ujy(float(row[column]), float(row[column.replace("_m_", "_msig_")]), band)
                rows.append(
                    dict(
                        band=band,
                        origin="2MASS XSC",
                        aperture="K20 isophotal",
                        flux_ujy=flux,
                        flux_err_ujy=err,
                    )
                )
        for band, column in (("J", "j_m_ext"), ("H", "h_m_ext"), ("Ks", "k_m_ext")):
            if column in xsc.colnames and not np.ma.is_masked(row[column]):
                flux, err = vega_to_ujy(float(row[column]), float(row[column.replace("_m_", "_msig_")]), band)
                rows.append(
                    dict(
                        band=band, origin="2MASS XSC", aperture="total (ext)", flux_ujy=flux, flux_err_ujy=err
                    )
                )
    psc = Irsa.query_region(coord, catalog="fp_psc", spatial="Cone", radius=6 * u.arcsec)
    if len(psc):
        row = psc[0]
        for band, column in (("J", "j_m"), ("H", "h_m"), ("Ks", "k_m")):
            if not np.ma.is_masked(row[column]):
                flux, err = vega_to_ujy(
                    float(row[column]), float(row[column.replace("_m", "_msigcom")] or 0.05), band
                )
                rows.append(
                    dict(
                        band=band,
                        origin="2MASS PSC",
                        aperture="point-source profile",
                        flux_ujy=flux,
                        flux_err_ujy=err,
                    )
                )
    wise = Irsa.query_region(coord, catalog="allwise_p3as_psd", spatial="Cone", radius=6 * u.arcsec)
    if len(wise):
        row = wise[0]
        for band, column in (("W1", "w1mpro"), ("W2", "w2mpro")):
            if not np.ma.is_masked(row[column]):
                flux, err = vega_to_ujy(
                    float(row[column]), float(row[column.replace("mpro", "sigmpro")]), band
                )
                rows.append(
                    dict(
                        band=band,
                        origin="AllWISE",
                        aperture="profile fit (mpro)",
                        flux_ujy=flux,
                        flux_err_ujy=err,
                    )
                )
        for band, column in (("W1", "w1gmag"), ("W2", "w2gmag")):
            if column in wise.colnames and not np.ma.is_masked(row[column]):
                flux, err = vega_to_ujy(float(row[column]), float(row[column.replace("gmag", "gerr")]), band)
                rows.append(
                    dict(
                        band=band,
                        origin="AllWISE",
                        aperture="elliptical (gmag)",
                        flux_ujy=flux,
                        flux_err_ujy=err,
                    )
                )
    if sdss_objid:
        table = _skyserver(
            "SELECT modelMag_z, modelMagErr_z, petroMag_z, petroMagErr_z, cModelMag_z, cModelMagErr_z, "
            "extinction_z "
            f"FROM PhotoObj WHERE objID = {sdss_objid}"
        )
        if len(table):
            row = table.iloc[0]
            for label, column in (
                ("model", "modelMag_z"),
                ("Petrosian", "petroMag_z"),
                ("cmodel", "cModelMag_z"),
            ):
                flux, err = ab_to_ujy(float(row[column]), float(row[column.replace("Mag", "MagErr")]))
                rows.append(
                    dict(band="z", origin="SDSS DR17", aperture=label, flux_ujy=flux, flux_err_ujy=err)
                )
    if legacy is not None and len(legacy):
        target = legacy.iloc[int(np.argmin(legacy.sep_arcsec))]
        if target.sep_arcsec < 2.0:
            for band in ("W1", "W2"):
                flux = float(target[f"flux_{band.lower()}_nmgy"]) * NANOMAGGY_UJY
                ivar = float(target[f"flux_ivar_{band.lower()}"])
                err = NANOMAGGY_UJY / np.sqrt(ivar) if ivar > 0 else np.nan
                rows.append(
                    dict(
                        band=band,
                        origin="Legacy DR10 forced",
                        aperture="Tractor model",
                        flux_ujy=flux,
                        flux_err_ujy=err,
                    )
                )
    table = pd.DataFrame(rows)
    if len(table):
        table["wavelength_um"] = [effective_wavelength_um(b) for b in table.band]
    return table


def effective_wavelength_um(band: str) -> float:
    import speclite.filters as sf

    return float(sf.load_filter(FILTERS[band]).effective_wavelength.to("um").value)


def synthetic_photometry(
    wavelength_um: np.ndarray, flux_ujy: np.ndarray, bands=("z", "J", "H", "Ks", "W1", "W2")
) -> pd.DataFrame:
    """Synthetic AB-system fluxes (uJy) of an F_nu SED through the named filters; NaN where the SED does not
    cover the filter. The SED is interpolated linearly in wavelength on the filter's grid."""
    import astropy.units as u
    import speclite.filters as sf

    rows = []
    order = np.argsort(wavelength_um)
    w = np.asarray(wavelength_um)[order]
    f = np.asarray(flux_ujy)[order]
    for band in bands:
        filt = sf.load_filter(FILTERS[band])
        grid = np.asarray(filt.wavelength) / 1e4  # speclite stores wavelength in Angstrom
        if grid.min() < w.min() or grid.max() > w.max():
            rows.append(dict(band=band, flux_ujy=np.nan, wavelength_um=effective_wavelength_um(band)))
            continue
        f_nu = np.interp(grid, w, f)  # uJy
        f_lambda = (
            (f_nu * u.uJy)
            .to(u.erg / u.s / u.cm**2 / u.AA, equivalencies=u.spectral_density(grid * u.um))
            .value
        )
        response = np.asarray(filt.response)
        numerator = np.trapezoid(f_lambda * response * grid * 1e4, grid * 1e4)
        denominator = np.trapezoid(response * grid * 1e4, grid * 1e4)
        f_lambda_mean = numerator / denominator
        pivot_um = filt.effective_wavelength.to("um").value
        f_nu_mean = (
            (f_lambda_mean * u.erg / u.s / u.cm**2 / u.AA)
            .to(u.uJy, equivalencies=u.spectral_density(pivot_um * u.um))
            .value
        )
        rows.append(dict(band=band, flux_ujy=float(f_nu_mean), wavelength_um=pivot_um))
    return pd.DataFrame(rows)
