"""ePSF zone selection and sampling conventions (R7 effective PSF, QR3 and DR1).

Conventions verified on 2026-11-12/13 (docs/references/studies/photometry_study_2026-11.md section 10):
each ePSF plane sums to 1 on its 5x oversampled grid, so samples at native pixel spacing sum to 1/25; the
ePSF already contains the pixel response, so a model is convolved on the oversampled grid and then sampled
(not integrated) at native pixel centres. The zone is chosen in parent-frame pixel coordinates.
"""

from __future__ import annotations

import numpy as np

from spherex_psb.products.bundle import Bundle


def select_zone(bundle: Bundle, x_cutout: float, y_cutout: float) -> int:
    """Index into ``bundle.psf_planes`` of the zone whose centre is nearest to the cutout position."""
    x_orig, y_orig = bundle.parent_pixel(x_cutout, y_cutout)
    zones = bundle.psf_zones
    distance = np.hypot(zones["x"] - x_orig, zones["y"] - y_orig)
    row = int(np.argmin(distance))
    return int(zones["plane_idx"][row])


def zone_record(bundle: Bundle, plane: int) -> dict:
    zones = bundle.psf_zones
    row = int(np.where(zones["plane_idx"] == plane)[0][0])
    record = {
        "epsf_zone_id": int(zones["zone_id"][row]),
        "epsf_zone_x": float(zones["x"][row]),
        "epsf_zone_y": float(zones["y"][row]),
    }
    if "neff" in zones.dtype.names:
        record["epsf_neff"] = float(zones["neff"][row])
    return record


def epsf_plane(bundle: Bundle, plane: int) -> np.ndarray:
    """The oversampled ePSF plane, normalised to unit sum on the oversampled grid."""
    stamp = np.asarray(bundle.psf_planes[plane], dtype=np.float64)
    total = stamp.sum()
    if not np.isfinite(total) or total <= 0:
        raise ValueError(f"{bundle.path.name}: ePSF plane {plane} has sum {total}")
    return stamp / total
