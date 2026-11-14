"""Render unit-flux source templates on the cutout pixel grid.

A Sersic profile is evaluated in sky coordinates (east/north offsets from the WCS, so rotation and parity
come from the image) on the ePSF's oversampled grid, convolved with the ePSF plane of the source's zone and
point-sampled at native pixel centres (the ePSF already includes the pixel response). The template values
are the fraction of the total flux falling in each native pixel; a fitted amplitude is therefore the total
flux per pixel-fraction, i.e. surface brightness (MJy/sr) x 1 pixel, converted with the pixel solid angle.

The light of a steep profile inside the central oversampled pixel is assigned analytically to that pixel
(the sub-sampling cannot follow an n = 4 cusp; study lessons 2026-11-12).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from astropy.wcs import WCS
from scipy.ndimage import map_coordinates
from scipy.signal import fftconvolve
from scipy.special import gamma, gammainc, gammaincinv

PIXEL_SCALE_ARCSEC = 6.15


@dataclass(frozen=True)
class SersicShape:
    """Fixed intrinsic shape. ``position_angle_deg`` is measured from north through east."""

    sersic_index: float
    effective_radius_arcsec: float
    axis_ratio: float
    position_angle_deg: float

    @property
    def is_point(self) -> bool:
        return self.effective_radius_arcsec <= 0


POINT_SOURCE = SersicShape(0.0, 0.0, 1.0, 0.0)


def sky_offsets_arcsec(wcs: WCS, x: np.ndarray, y: np.ndarray, ra0: float, dec0: float):
    """East and north offsets (arcsec) of cutout pixel positions from a reference sky position."""
    ra, dec = wcs.all_pix2world(x, y, 0)
    east = (ra - ra0) * np.cos(np.radians(dec0)) * 3600.0
    north = (dec - dec0) * 3600.0
    return east, north


def sersic_total_flux(shape: SersicShape) -> float:
    """Analytic total flux (arcsec^2 x central-normalised intensity units) of exp(-b [(r/re)^(1/n) - 1])."""
    n, re, q = shape.sersic_index, shape.effective_radius_arcsec, shape.axis_ratio
    b = gammaincinv(2 * n, 0.5)
    return 2 * np.pi * q * n * re**2 * np.exp(b) * b ** (-2 * n) * gamma(2 * n)


CORE_BLOCK_HALF_WIDTH = 3  # oversampled pixels around the centre that are sampled finely
CORE_SUBSAMPLE = 32


def _flux_fraction_on_block(
    wcs: WCS,
    ra: float,
    dec: float,
    x0: float,
    y0: float,
    shape: SersicShape,
    oversampling: int,
    block_half_width: int,
    subsample: int,
) -> np.ndarray:
    """Fraction of the source's total flux in each oversampled pixel of a square block centred on it.

    The profile is point-sampled at ``subsample`` x ``subsample`` points per oversampled pixel; the light
    inside the elliptical core of semi-major axis half a pitch (which lies within the central pixel) is
    assigned to the central pixel analytically.
    """
    pitch = PIXEL_SCALE_ARCSEC / oversampling
    m = 2 * block_half_width + 1
    fine = (np.arange(m * subsample) - (m * subsample - 1) / 2) / (oversampling * subsample)
    gx, gy = np.meshgrid(x0 + fine, y0 + fine)
    east, north = sky_offsets_arcsec(wcs, gx.ravel(), gy.ravel(), ra, dec)
    pa = np.radians(shape.position_angle_deg)
    major = east * np.sin(pa) + north * np.cos(pa)
    minor = east * np.cos(pa) - north * np.sin(pa)
    radius = np.hypot(major, minor / shape.axis_ratio).reshape(gy.shape)
    n_idx, re = shape.sersic_index, shape.effective_radius_arcsec
    b = gammaincinv(2 * n_idx, 0.5)
    profile = np.exp(-b * ((radius / re) ** (1 / n_idx) - 1))
    core_radius = pitch / 2
    fine_image = np.where(
        radius < core_radius, 0.0, profile * (pitch / subsample) ** 2 / sersic_total_flux(shape)
    )
    block = fine_image.reshape(m, subsample, m, subsample).sum(axis=(1, 3))
    block[block_half_width, block_half_width] += gammainc(2 * n_idx, b * (core_radius / re) ** (1 / n_idx))
    return block


def render_source_on_oversampled_grid(
    wcs: WCS,
    ra: float,
    dec: float,
    shape: SersicShape,
    oversampling: int,
    half_width_px: int,
    subsample: int = 4,
) -> tuple[np.ndarray, float, float]:
    """Unit-total-flux image of the source on the oversampled grid centred on its sky position.

    The central block of 2 x CORE_BLOCK_HALF_WIDTH + 1 oversampled pixels is re-sampled CORE_SUBSAMPLE times
    finer: with the default 4 x 4 sampling an n = 4 cusp of R_e = 1" lost 2.3 % of its flux (lessons
    2026-11-13); the fine block brings every tested shape within 0.2 % of a 64 x 64 reference.

    Returns the grid, and the source's cutout pixel position (x0, y0).
    """
    x0, y0 = (float(v) for v in wcs.all_world2pix([[ra, dec]], 0)[0])
    n = 2 * half_width_px * oversampling + 1
    centre = n // 2
    if shape.is_point:
        grid = np.zeros((n, n))
        grid[centre, centre] = 1.0
        return grid, x0, y0
    grid = _flux_fraction_on_block(
        wcs, ra, dec, x0, y0, shape, oversampling, half_width_px * oversampling, subsample
    )
    k = CORE_BLOCK_HALF_WIDTH
    grid[centre - k : centre + k + 1, centre - k : centre + k + 1] = _flux_fraction_on_block(
        wcs, ra, dec, x0, y0, shape, oversampling, k, CORE_SUBSAMPLE
    )
    return grid, x0, y0


def template_on_cutout(
    wcs: WCS,
    ra: float,
    dec: float,
    shape: SersicShape,
    epsf: np.ndarray,
    oversampling: int,
    cutout_shape: tuple[int, int],
    half_width_px: int = 14,
) -> tuple[np.ndarray, float, float, float]:
    """PSF-convolved unit-flux template sampled at the cutout's native pixel centres.

    Returns (template, x0, y0, fraction of the model flux that the oversampled grid captured).
    """
    grid, x0, y0 = render_source_on_oversampled_grid(wcs, ra, dec, shape, oversampling, half_width_px)
    captured = float(grid.sum())
    convolved = (
        fftconvolve(grid, epsf, mode="same") * oversampling**2
    )  # native-spaced samples of the ePSF sum to 1
    n = grid.shape[0]
    yy, xx = np.indices(cutout_shape)
    rows = n // 2 + (yy - y0) * oversampling
    cols = n // 2 + (xx - x0) * oversampling
    template = map_coordinates(convolved, [rows, cols], order=3, mode="constant", cval=0.0)
    return template, x0, y0, captured
