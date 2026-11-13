"""Injection and recovery: a synthetic galaxy of known shape and SED is added to the real cutouts on blank
sky near the target and measured with the full pipeline (real neighbours and the real target in the model).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from spherex_psb.extraction.fit import FitSettings, Source, measure_exposure
from spherex_psb.extraction.render import SersicShape, template_on_cutout
from spherex_psb.products.bundle import UJY_PER_MJY, Bundle
from spherex_psb.products.epsf import epsf_plane, select_zone


def injection_position(
    bundle: Bundle,
    target_ra: float,
    target_dec: float,
    sources: list[Source],
    offset_px: float = 12.0,
    exclusion_px: float = 3.0,
    minimum_delta_mag: float = 4.0,
    target_mag_z: float = 15.0,
):
    """Sky position ``offset_px`` from the target where no catalogue source brighter than target + 4 mag lies
    within ``exclusion_px``; tries 12 position angles and returns the one with the least neighbour light."""
    wcs = bundle.wcs
    x0, y0 = (float(v) for v in wcs.all_world2pix([[target_ra, target_dec]], 0)[0])
    ny, nx = bundle.shape
    best = None
    for angle in np.linspace(0, 2 * np.pi, 12, endpoint=False):
        x, y = x0 + offset_px * np.cos(angle), y0 + offset_px * np.sin(angle)
        if x < 6 or y < 6 or x > nx - 7 or y > ny - 7:
            continue
        ra, dec = (float(v) for v in wcs.all_pix2world([[x, y]], 0)[0])
        crowding = 0.0
        blocked = False
        for source in sources:
            sx, sy = (float(v) for v in wcs.all_world2pix([[source.ra, source.dec]], 0)[0])
            distance = np.hypot(sx - x, sy - y)
            if (
                np.isfinite(source.mag_z)
                and source.mag_z < target_mag_z + minimum_delta_mag
                and distance < exclusion_px
            ):
                blocked = True
                break
            if np.isfinite(source.mag_z):
                crowding += 10 ** (-0.4 * (source.mag_z - target_mag_z)) / max(distance, 0.5) ** 2
        if blocked:
            continue
        if best is None or crowding < best[0]:
            best = (crowding, ra, dec)
    if best is None:
        raise RuntimeError("no clean injection position found")
    return best[1], best[2]


def inject_and_measure(
    bundle: Bundle, sources: list[Source], injected: Source, sed_ujy_at, settings: FitSettings
) -> dict:
    """Add the injected galaxy (flux ``sed_ujy_at(cwave)`` in uJy) to the image; measure it as the target."""
    wcs = bundle.wcs
    x0, y0 = (float(v) for v in wcs.all_world2pix([[injected.ra, injected.dec]], 0)[0])
    plane = select_zone(bundle, x0, y0)
    epsf = epsf_plane(bundle, plane)
    template, _, _, _ = template_on_cutout(
        wcs,
        injected.ra,
        injected.dec,
        injected.shape,
        epsf,
        bundle.psf_oversampling,
        bundle.shape,
        settings.half_width_px,
    )
    j, i = int(round(y0)), int(round(x0))
    cwave = float(bundle.cwave[j, i])
    flux_ujy = float(sed_ujy_at(cwave))
    to_ujy = bundle.solid_angle_sr(x0, y0) * UJY_PER_MJY
    amplitude = flux_ujy / to_ujy
    bundle.image = bundle.image + amplitude * template
    bundle.variance = bundle.variance + np.abs(amplitude * template) * np.nanmedian(
        bundle.variance / np.maximum(np.abs(bundle.image), 1e-6)
    )
    model_sources = [Source(s.name, s.ra, s.dec, s.shape, s.mag_z, False) for s in sources]
    model_sources.append(Source("injected", injected.ra, injected.dec, injected.shape, injected.mag_z, True))
    result = measure_exposure(bundle, model_sources, settings)
    record = result.record
    record["injected_flux_ujy"] = flux_ujy
    record["injected_cwave_um"] = cwave
    for key in ("flux_model_ujy", "flux_aperture_2px_ujy", "flux_point_ujy"):
        if key in record:
            record[key.replace("_ujy", "_recovered_ratio")] = record[key] / flux_ujy
    return record


def injected_shape_like(shape: SersicShape) -> SersicShape:
    """The injected galaxy mirrors the target's shape with a different orientation, so that its recovery is a
    test of the method and not of one particular pixel alignment."""
    return SersicShape(
        shape.sersic_index,
        shape.effective_radius_arcsec,
        shape.axis_ratio,
        (shape.position_angle_deg + 45.0) % 180,
    )


def smooth_sed(binned: pd.DataFrame):
    """Interpolator of the galaxy's binned SED (uJy versus observed wavelength), extended flat at the ends."""
    ok = binned.n_exposures > 0
    w = binned.wavelength_um[ok].to_numpy()
    f = binned.flux_ujy[ok].to_numpy()
    order = np.argsort(w)
    return lambda x: np.interp(x, w[order], f[order])
