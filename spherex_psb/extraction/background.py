"""Background basis functions for the joint linear fit.

The ZODI model is subtracted before fitting; these bases absorb the residual sky: a constant, optionally a
plane in cutout pixel coordinates, and optionally terms in the per-pixel wavelength CWAVE for exposures near
airglow lines (the LVF maps wavelength onto detector rows, so an airglow line is a band of the image whose
brightness follows CWAVE rather than x or y).
"""

from __future__ import annotations

import numpy as np

BACKGROUND_MODELS = ("constant", "plane", "cwave2", "plane+cwave2")


def background_templates(
    model: str, shape: tuple[int, int], cwave: np.ndarray
) -> list[tuple[str, np.ndarray]]:
    if model not in BACKGROUND_MODELS:
        raise ValueError(f"unknown background model {model!r}; choose from {BACKGROUND_MODELS}")
    ny, nx = shape
    yy, xx = np.indices(shape)
    templates = [("bkg_const", np.ones(shape))]
    if model.startswith("plane"):
        templates.append(("bkg_x", (xx - (nx - 1) / 2) / nx))
        templates.append(("bkg_y", (yy - (ny - 1) / 2) / ny))
    if model.endswith("cwave2"):
        finite = np.isfinite(cwave)
        centre = np.nanmedian(cwave)
        span = max(float(np.nanmax(cwave) - np.nanmin(cwave)), 1e-6)
        u = np.where(finite, (cwave - centre) / span, 0.0)
        templates.append(("bkg_cwave1", u))
        templates.append(("bkg_cwave2", u**2 - np.mean(u[finite] ** 2)))
    return templates
