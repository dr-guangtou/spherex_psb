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
}
