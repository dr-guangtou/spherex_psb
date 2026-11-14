"""Shape priors and neighbour catalogues: SDSS DR17 (SkyServer) and Legacy Survey DR10 (NOIRLab Data Lab TAP).

Access routes verified 2026-11-13:
- SkyServer SqlSearch (anonymous, CSV): ``dbo.fGetNearbyObjEq`` joined to ``PhotoPrimary``.
- Data Lab TAP (anonymous): ``ls_dr10.tractor`` and ``sga2020.ellipse`` with a RA/Dec box in the WHERE clause
  (``q3c_radial_query`` and ADQL CONTAINS are rejected; the viewer ``cat.json`` endpoint returns HTML).

Unified catalogue columns: ra, dec, source_type ('star' or 'galaxy'), sersic_index, r_e_arcsec, axis_ratio,
position_angle_deg (north through east), mag_z, origin, catalogue_id.
"""

from __future__ import annotations

import io
import time

import numpy as np
import pandas as pd
import requests

SKYSERVER = "https://skyserver.sdss.org/dr17/SkyServerWS/SearchTools/SqlSearch"
DATALAB_TAP = "https://datalab.noirlab.edu/tap"
MINIMUM_AXIS_RATIO = 0.2
MAXIMUM_SERSIC_INDEX = 6.0


def _skyserver(query: str, attempts: int = 4) -> pd.DataFrame:
    for attempt in range(attempts):
        response = requests.get(
            SKYSERVER, params={"cmd": " ".join(query.split()), "format": "csv"}, timeout=300
        )
        if response.ok and not response.text.lstrip().startswith("<"):
            break
        time.sleep(5 * (attempt + 1))
    response.raise_for_status()
    text = response.text
    if text.startswith("#"):
        text = text.split("\n", 1)[1]
    return pd.read_csv(io.StringIO(text)) if text.strip() else pd.DataFrame()


def _datalab(query: str, attempts: int = 5) -> pd.DataFrame:
    """Data Lab TAP with retries: the service answers with HTML or 5xx now and then."""
    import pyvo

    for attempt in range(attempts):
        try:
            return pyvo.dal.TAPService(DATALAB_TAP).search(query).to_table().to_pandas()
        except Exception as error:  # noqa: BLE001
            if attempt == attempts - 1:
                raise
            print(f"Data Lab attempt {attempt + 1} failed ({str(error)[:80]}); retrying", flush=True)
            time.sleep(60 * (attempt + 1))
    raise RuntimeError("unreachable")


def sdss_neighbours(ra: float, dec: float, radius_arcmin: float, faint_limit_z: float) -> pd.DataFrame:
    query = f"""
    SELECT p.objID, p.ra, p.dec, p.type, p.modelMag_r, p.modelMag_z, p.fracDeV_r,
           p.expRad_r, p.expAB_r, p.expPhi_r, p.deVRad_r, p.deVAB_r, p.deVPhi_r, p.flags,
           n.distance * 60 AS sep_arcsec
    FROM dbo.fGetNearbyObjEq({ra}, {dec}, {radius_arcmin}) n JOIN PhotoPrimary p ON p.objID = n.objID
    WHERE p.modelMag_z < {faint_limit_z}"""
    table = _skyserver(query)
    if table.empty:
        return pd.DataFrame(
            columns=[
                "ra",
                "dec",
                "source_type",
                "sersic_index",
                "r_e_arcsec",
                "axis_ratio",
                "position_angle_deg",
                "mag_z",
                "origin",
                "catalogue_id",
            ]
        )
    galaxy = table["type"] == 3
    de_vaucouleurs = table.fracDeV_r > 0.5
    out = pd.DataFrame(
        {
            "ra": table.ra,
            "dec": table.dec,
            "source_type": np.where(galaxy, "galaxy", "star"),
            "sersic_index": np.where(galaxy & de_vaucouleurs, 4.0, 1.0),
            "r_e_arcsec": np.where(galaxy, np.where(de_vaucouleurs, table.deVRad_r, table.expRad_r), 0.0),
            "axis_ratio": np.where(de_vaucouleurs, table.deVAB_r, table.expAB_r).clip(
                MINIMUM_AXIS_RATIO, 1.0
            ),
            "position_angle_deg": np.where(de_vaucouleurs, table.deVPhi_r, table.expPhi_r),
            "mag_z": table.modelMag_z,
            "mag_r": table.modelMag_r,
            "origin": "sdss_dr17",
            "catalogue_id": table.objID.astype(str),
            "sep_arcsec": table.sep_arcsec,
        }
    )
    return out.sort_values("sep_arcsec").reset_index(drop=True)


def legacy_dr10_neighbours(ra: float, dec: float, radius_arcmin: float, faint_limit_z: float) -> pd.DataFrame:
    """Legacy Survey DR10 Tractor sources; empty table when the position is outside the footprint."""

    half = radius_arcmin / 60.0
    cos_dec = np.cos(np.radians(dec))
    query = f"""SELECT ls_id, ra, dec, type, shape_r, shape_e1, shape_e2, sersic, flux_z, flux_r,
        flux_w1, flux_w2,
        flux_ivar_w1, flux_ivar_w2, maskbits, fitbits, ref_cat, ref_id, fracflux_z
        FROM ls_dr10.tractor WHERE ra BETWEEN {ra - half / cos_dec} AND {ra + half / cos_dec}
        AND dec BETWEEN {dec - half} AND {dec + half}"""
    table = _datalab(query)
    if table.empty:
        return table
    flux_z = table.flux_z.to_numpy(dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        mag_z = 22.5 - 2.5 * np.log10(np.where(flux_z > 0, flux_z, np.nan))
    e = np.hypot(table.shape_e1, table.shape_e2)
    axis_ratio = (1 - e) / (1 + e)
    position_angle = np.degrees(
        0.5 * np.arctan2(table.shape_e2, table.shape_e1)
    )  # Legacy convention: north through east
    source_type = table.type.str.strip()
    sersic_index = np.select(
        [
            source_type == "PSF",
            source_type == "REX",
            source_type == "EXP",
            source_type == "DEV",
            source_type == "SER",
            source_type == "DUP",
        ],
        [0.0, 1.0, 1.0, 4.0, table.sersic.to_numpy(dtype=float), 0.0],
        default=1.0,
    )
    sep = np.hypot((table.ra - ra) * cos_dec, table.dec - dec) * 3600
    out = pd.DataFrame(
        {
            "ra": table.ra,
            "dec": table.dec,
            "source_type": np.where(source_type == "PSF", "star", "galaxy"),
            "sersic_index": np.clip(sersic_index, 0.0, MAXIMUM_SERSIC_INDEX),
            "r_e_arcsec": np.where(source_type == "PSF", 0.0, table.shape_r),
            "axis_ratio": np.where(source_type == "REX", 1.0, axis_ratio).clip(MINIMUM_AXIS_RATIO, 1.0),
            "position_angle_deg": np.where(source_type == "REX", 0.0, position_angle),
            "mag_z": mag_z,
            "flux_w1_nmgy": table.flux_w1,
            "flux_w2_nmgy": table.flux_w2,
            "flux_ivar_w1": table.flux_ivar_w1,
            "flux_ivar_w2": table.flux_ivar_w2,
            "ref_cat": table.ref_cat.str.strip(),
            "ref_id": table.ref_id,
            "fracflux_z": table.fracflux_z,
            "origin": "ls_dr10",
            "catalogue_id": table.ls_id.astype(str),
            "sep_arcsec": sep,
        }
    )
    out = out[(out.sep_arcsec <= radius_arcmin * 60) & (out.mag_z < faint_limit_z)]
    return out.sort_values("sep_arcsec").reset_index(drop=True)


def sga_entries(ra: float, dec: float, radius_arcmin: float) -> pd.DataFrame:

    half = radius_arcmin / 60.0
    query = f"""SELECT sga_id, galaxy, ra, dec, d26, pa, ba, sma_moment, mag_leda, pgc FROM sga2020.ellipse
        WHERE ra BETWEEN {ra - half / np.cos(np.radians(dec))} AND {ra + half / np.cos(np.radians(dec))}
        AND dec BETWEEN {dec - half} AND {dec + half}"""
    return _datalab(query)


def remove_shreds(
    catalogue: pd.DataFrame,
    target_ra: float,
    target_dec: float,
    target_shape,
    target_mag_z: float,
    k_radius: float = 1.5,
    min_delta_mag: float = 1.0,
):
    """Split a neighbour catalogue into kept neighbours and entries that are parts of the target.

    A shred is an entry inside ``k_radius`` effective radii (elliptical) of the target centre that is at least
    ``min_delta_mag`` fainter than the target in z. The target's own entry (within 1.5 arcsec) is removed too.
    """
    cos_dec = np.cos(np.radians(target_dec))
    east = (catalogue.ra - target_ra) * cos_dec * 3600
    north = (catalogue.dec - target_dec) * 3600
    pa = np.radians(target_shape.position_angle_deg)
    major = east * np.sin(pa) + north * np.cos(pa)
    minor = east * np.cos(pa) - north * np.sin(pa)
    elliptical_radius = np.hypot(major, minor / target_shape.axis_ratio)
    is_self = np.hypot(east, north) < 1.5
    is_shred = (
        (~is_self)
        & (elliptical_radius < k_radius * target_shape.effective_radius_arcsec)
        & (catalogue.mag_z > target_mag_z + min_delta_mag)
    )
    kept = catalogue[~is_self & ~is_shred].reset_index(drop=True)
    shreds = catalogue[is_shred].reset_index(drop=True)
    return kept, shreds
