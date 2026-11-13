"""The demo galaxies with their roles. Roles were fixed before looking at SPHEREx pixels; shapes come from the
SDSS r-band model fits (exp if fracDeV_r <= 0.5, else deV) unless noted. Galaxies 2-6 are filled in by
scripts/sed_demo/select_sample.py from the candidate pools and recorded here.
"""

from __future__ import annotations

from dataclasses import dataclass

from spherex_psb.extraction.render import SersicShape


@dataclass(frozen=True)
class DemoGalaxy:
    name: str
    role: str
    sdss_objid: str
    specobjid: str
    ra: float
    dec: float
    redshift: float
    shape: SersicShape
    mag_z: float
    catalogue: str = "ls"  # 'ls' (Legacy Survey DR10, SDSS fallback) or 'sdss'
    cutout_size_deg: float = 0.07
    fit_radius_px: float = 5.0
    notes: str = ""


DEMO_GALAXIES: dict[str, DemoGalaxy] = {
    "g1_reference": DemoGalaxy(
        name="g1_reference",
        role="reference galaxy of the 2026-11 study",
        sdss_objid="1237661812804550732",
        specobjid="1806085614093756416",
        ra=168.14539,
        dec=12.072366,
        redshift=0.0458,
        shape=SersicShape(1.0, 4.38, 0.77, 101.7),
        mag_z=14.95,
        notes="exponential, fracDeV_r 0.12; stars at 11.9 and 26.2 arcsec",
    ),
    "g2_compact": DemoGalaxy(
        name="g2_compact",
        role="compact galaxy, R_e about 1 arcsec",
        sdss_objid="1237660412112076899",
        specobjid="1342183509195778048",
        ra=135.687027,
        dec=6.524568,
        redshift=0.05831,
        shape=SersicShape(4.0, 1.05, 0.807, 129.7),
        mag_z=15.22,
        notes="deV, fracDeV_r 1.00; 279 wide exposures; nearest SDSS neighbour 23 arcsec",
    ),
    "g3_large": DemoGalaxy(
        name="g3_large",
        role="large galaxy, R_e about 12 arcsec",
        sdss_objid="1237662661600739637",
        specobjid="1855517184537683968",
        ra=226.404175,
        dec=31.163822,
        redshift=0.03342,
        shape=SersicShape(1.0, 12.39, 0.537, 70.4),
        mag_z=14.33,
        cutout_size_deg=0.09,
        fit_radius_px=7.0,
        notes="exp, fracDeV_r 0.03; 418 wide exposures; nearest SDSS neighbour 32 arcsec",
    ),
    "g4_neighbour": DemoGalaxy(
        name="g4_neighbour",
        role="star of comparable brightness 12.6 arcsec (2.1 px) away",
        sdss_objid="1237665533333799238",
        specobjid="2477075517577127936",
        ra=240.817825,
        dec=17.632015,
        redshift=0.03334,
        shape=SersicShape(4.0, 1.92, 0.891, 66.7),
        mag_z=15.39,
        notes="deV, fracDeV_r 0.97; 420 wide exposures; star 12.6 arcsec away, 0.21 mag fainter in z",
    ),
    "g5_no_legacy": DemoGalaxy(
        name="g5_no_legacy",
        role="outside the Legacy Survey footprint (SDSS priors only)",
        sdss_objid="1237660979045007610",
        specobjid="1875860345654896640",
        ra=49.585045,
        dec=42.745113,
        redshift=0.05183,
        shape=SersicShape(4.0, 4.77, 0.562, 97.7),
        mag_z=14.72,
        catalogue="sdss",
        notes="deV, fracDeV_r 1.00; 393 wide exposures; no DR9/DR10 Tractor sources within 72 arcsec; "
        "stars 9.1 arcsec (1.0 mag fainter) and 10.4 arcsec (2.8 mag fainter) away",
    ),
    "g6_post_starburst": DemoGalaxy(
        name="g6_post_starburst",
        role="post-starburst-like spectrum: HdA 6.5 A, Dn4000 1.34",
        sdss_objid="1237665373870686401",
        specobjid="3340648454601861120",
        ra=241.060226,
        dec=20.142387,
        redshift=0.05167,
        shape=SersicShape(1.0, 5.39, 0.607, 187.1),
        mag_z=15.67,
        notes="exp, fracDeV_r 0.00; 374 wide exposures; nearest SDSS neighbour 34 arcsec",
    ),
}
