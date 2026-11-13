"""Reader for the per-exposure cutout bundles written by spherex-retrieval (MIT).

A bundle holds, for one Level 2 exposure and one detector, the cropped IMAGE, FLAGS, VARIANCE and ZODI
arrays, the ePSF planes of the zones overlapping the cutout with their zone table, the per-pixel CWAVE and
CBAND maps from the Spectral WCS calibration product, and the per-pixel solid angle (SAPM). All arrays share
the cutout pixel grid; ``x_orig_lo``/``y_orig_lo`` give the 0-based parent-frame pixel of the cutout origin.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from astropy.io import fits
from astropy.wcs import WCS

SR_PER_ARCSEC2 = (np.pi / 180 / 3600) ** 2
UJY_PER_MJY = 1e12


@dataclass
class Bundle:
    path: Path
    obs_id: str
    detector: int
    collection: str
    release: str
    pipeline_version: str
    mjd: float
    image: np.ndarray
    flags: np.ndarray
    variance: np.ndarray
    zodi: np.ndarray
    cwave: np.ndarray
    cband: np.ndarray
    sapm_arcsec2: np.ndarray
    psf_planes: np.ndarray
    psf_zones: np.ndarray
    psf_oversampling: int
    psf_kind: str
    image_header: fits.Header
    primary_header: fits.Header
    x_orig_lo: int
    y_orig_lo: int

    @property
    def wcs(self) -> WCS:
        return WCS(self.image_header)

    @property
    def shape(self) -> tuple[int, int]:
        return self.image.shape

    def header_flag(self, key: str):
        """R7 exposure-level keywords (HE_AIRGLOW_CONT, AURORA_CONT, SHUTTLE_GLOW_CONT); None if absent."""
        return self.image_header.get(key, self.primary_header.get(key))

    def parent_pixel(self, x_cutout: float, y_cutout: float) -> tuple[float, float]:
        """0-based parent-frame pixel coordinates of a cutout pixel (official recipe, CRPIX1A/2A)."""
        return 1 + x_cutout - self.image_header["CRPIX1A"], 1 + y_cutout - self.image_header["CRPIX2A"]

    def solid_angle_sr(self, x: float, y: float) -> float:
        """Pixel solid angle in steradian at a cutout position (nearest pixel of the SAPM map)."""
        j, i = int(round(y)), int(round(x))
        j = min(max(j, 0), self.sapm_arcsec2.shape[0] - 1)
        i = min(max(i, 0), self.sapm_arcsec2.shape[1] - 1)
        return float(self.sapm_arcsec2[j, i]) * SR_PER_ARCSEC2


def read_bundle(path: str | Path) -> Bundle:
    path = Path(path)
    with fits.open(path, memmap=False) as hdulist:
        primary = hdulist[0].header
        image_header = hdulist["IMAGE"].header
        names = [h.name for h in hdulist]
        for required in ("IMAGE", "FLAGS", "VARIANCE", "ZODI", "PSF", "PSF_ZONES", "CWAVE", "CBAND", "SAPM"):
            if required not in names:
                raise ValueError(f"{path.name}: missing extension {required} (have {names})")
        zones = hdulist["PSF_ZONES"].data
        return Bundle(
            path=path,
            obs_id=str(primary["OBSID"]),
            detector=int(primary["DETECTOR"]),
            collection=str(primary.get("COLLECT", "")),
            release=str(primary.get("COLLECT", "")).replace("spherex_", "").replace("_deep", ""),
            pipeline_version=str(primary.get("VERSION", "")),
            mjd=float(image_header.get("MJD-AVG", image_header.get("MJD-OBS", np.nan))),
            image=np.asarray(hdulist["IMAGE"].data, dtype=np.float64),
            flags=np.asarray(hdulist["FLAGS"].data, dtype=np.int64),
            variance=np.asarray(hdulist["VARIANCE"].data, dtype=np.float64),
            zodi=np.asarray(hdulist["ZODI"].data, dtype=np.float64),
            cwave=np.asarray(hdulist["CWAVE"].data, dtype=np.float64),
            cband=np.asarray(hdulist["CBAND"].data, dtype=np.float64),
            sapm_arcsec2=np.asarray(hdulist["SAPM"].data, dtype=np.float64),
            psf_planes=np.asarray(hdulist["PSF"].data, dtype=np.float64),
            psf_zones=np.array(zones),
            psf_oversampling=int(primary["OVERSAMP"]),
            psf_kind=str(primary.get("PSFKIND", "")),
            image_header=image_header,
            primary_header=primary,
            x_orig_lo=int(round(1 - image_header["CRPIX1A"])),
            y_orig_lo=int(round(1 - image_header["CRPIX2A"])),
        )


def list_bundles(directory: str | Path) -> list[Path]:
    return sorted(Path(directory).glob("cutout_*.fits"))
