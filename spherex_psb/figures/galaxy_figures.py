"""Per-galaxy figures of the SED demo: image QA (figure 2), per-exposure diagnostics (figure 3), SED
(figure 4)."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
from astropy.io import fits
from astropy.wcs import WCS
from matplotlib.colors import TwoSlopeNorm
from matplotlib.patches import Circle, Ellipse

from spherex_psb import SCRATCH_ROOT
from spherex_psb.figures.style import (
    AIRGLOW_LINES_UM,
    DETECTOR_COLOURS,
    DOUBLE_COLUMN_IN,
    FLUX_LABEL,
    NEUTRAL_GREY,
    REST_WAVELENGTH_LABEL,
    WAVELENGTH_LABEL,
    apply_style,
    panel_label,
)

PIXEL_SCALE_ARCSEC = 6.15
REST_FEATURES_UM = {
    r"${\rm CaT}$": 0.86,
    r"${\rm CO}\,1.6$": 1.62,
    r"${\rm CO}\,2.29$": 2.29,
    r"${\rm H_2O}$": 1.9,
    r"${\rm PAH}\,3.3$": 3.3,
    r"${\rm CO}\,4.6$": 4.6,
}
REJECT_MARKERS = {
    "cutout_truncated": "x",
    "model_weight_masked": "+",
    "chi2_outlier": "s",
    "cutout_chi2_outlier": "D",
    "wavelength_outlier": "d",
    "airglow": "^",
    "target_outside_cutout": "x",
}


def optical_image(
    ra: float, dec: float, size_arcsec: float, layer: str = "ls-dr10"
) -> tuple[np.ndarray | None, WCS | None, str]:
    """Legacy Survey z-band FITS cutout (0.5 arcsec pixels); falls back to the SDSS JPEG when not covered."""
    cache = SCRATCH_ROOT / "optical_images"
    cache.mkdir(parents=True, exist_ok=True)
    n_pix = int(size_arcsec / 0.5)
    path = cache / f"{layer}_{ra:.5f}_{dec:.5f}_{n_pix}.fits"
    if not path.exists():
        url = f"https://www.legacysurvey.org/viewer/fits-cutout?ra={ra}&dec={dec}&layer={layer}&pixscale=0.5&size={n_pix}&bands=z"
        response = requests.get(url, timeout=180)
        if response.ok and response.content[:6] == b"SIMPLE":
            path.write_bytes(response.content)
    if path.exists():
        with fits.open(path) as hdulist:
            data = np.asarray(hdulist[0].data, dtype=float)
            wcs = WCS(hdulist[0].header)
        if np.isfinite(data).any() and np.nanmax(np.abs(data)) > 0:
            return data, wcs, "Legacy Survey DR10 $z$"
    jpeg = cache / f"sdss_{ra:.5f}_{dec:.5f}_{n_pix}.jpg"
    if not jpeg.exists():
        url = f"https://skyserver.sdss.org/dr17/SkyServerWS/ImgCutout/getjpeg?ra={ra}&dec={dec}&scale=0.5&width={n_pix}&height={n_pix}"
        response = requests.get(url, timeout=180)
        if response.ok:
            jpeg.write_bytes(response.content)
    if jpeg.exists():
        image = plt.imread(jpeg)
        data = image.mean(axis=2)[::-1]  # north up, east left as in a FITS image with the SDSS orientation
        wcs = WCS(naxis=2)
        wcs.wcs.crpix = [n_pix / 2 + 0.5, n_pix / 2 + 0.5]
        wcs.wcs.crval = [ra, dec]
        wcs.wcs.cdelt = [-0.5 / 3600, 0.5 / 3600]
        wcs.wcs.ctype = ["RA---TAN", "DEC--TAN"]
        return data, wcs, "SDSS DR17 colour composite"
    return None, None, "no image"


def figure_image_qa(
    galaxy,
    records: pd.DataFrame,
    neighbours: pd.DataFrame,
    shreds: pd.DataFrame,
    stamps: dict,
    out_path: Path,
    aperture_px: float = 2.0,
    fit_radius_px: float = 5.0,
) -> None:
    """(a) optical image with the model ellipse, neighbours and shreds; (b)-(d) data, model and normalised
    residual of one exposure per detector (columns), with masked pixels and the apertures drawn."""
    apply_style()
    detectors = sorted(stamps)
    n_det = len(detectors)
    fig = plt.figure(figsize=(DOUBLE_COLUMN_IN, 3.45))
    grid = fig.add_gridspec(3, n_det + 2, width_ratios=[3.0, 0.25] + [1] * n_det, wspace=0.06, hspace=0.06)
    ax_image = fig.add_subplot(grid[:, 0])
    size_arcsec = 150.0
    data, wcs, label = optical_image(galaxy.ra, galaxy.dec, size_arcsec)
    if data is not None:
        finite = data[np.isfinite(data)]
        lo, hi = np.percentile(finite, [5, 99.5])
        ax_image.imshow(
            np.arcsinh((data - lo) / max(hi - lo, 1e-9) * 10),
            origin="lower",
            cmap="gray_r",
            interpolation="nearest",
        )
        n_pix = data.shape[0]
        scale = 1 / 0.5  # image pixels per arcsec

        def to_pixel(ra, dec):
            x, y = wcs.all_world2pix(ra, dec, 0)
            return float(x), float(y)

        x0, y0 = to_pixel(galaxy.ra, galaxy.dec)
        shape = galaxy.shape
        ax_image.add_patch(
            Ellipse(
                (x0, y0),
                2 * shape.effective_radius_arcsec * scale * shape.axis_ratio,
                2 * shape.effective_radius_arcsec * scale,
                angle=shape.position_angle_deg,
                fill=False,
                color="#D55E00",
                lw=0.9,
            )
        )
        ax_image.add_patch(
            Circle(
                (x0, y0),
                aperture_px * PIXEL_SCALE_ARCSEC * scale,
                fill=False,
                color="#0072B2",
                lw=0.8,
                ls="--",
            )
        )
        ax_image.add_patch(
            Circle(
                (x0, y0),
                fit_radius_px * PIXEL_SCALE_ARCSEC * scale,
                fill=False,
                color=NEUTRAL_GREY,
                lw=0.6,
                ls=":",
            )
        )
        for row in neighbours.itertuples():
            x, y = to_pixel(row.ra, row.dec)
            if 0 <= x < n_pix and 0 <= y < n_pix:
                radius = max(1.5, 8 - 0.8 * (row.mag_z - galaxy.mag_z)) * scale
                ax_image.add_patch(Circle((x, y), radius, fill=False, color="#009E73", lw=0.6))
        for row in shreds.itertuples():
            x, y = to_pixel(row.ra, row.dec)
            if 0 <= x < n_pix and 0 <= y < n_pix:
                ax_image.plot(x, y, marker="x", color="#CC79A7", ms=5, mew=0.9)
        bar = 30.0 * scale
        ax_image.plot([n_pix * 0.05, n_pix * 0.05 + bar], [n_pix * 0.05, n_pix * 0.05], color="k", lw=1.2)
        ax_image.text(n_pix * 0.05 + bar / 2, n_pix * 0.075, r"$30''$", ha="center", va="bottom", fontsize=7)
    ax_image.set_xticks([])
    ax_image.set_yticks([])
    panel_label(ax_image, f"(a) {label}", y=0.97)

    row_names = ["(b) data", "(c) model", "(d) residual"]
    for k, detector in enumerate(detectors):
        stamp = stamps[detector]
        data_, model, good = stamp["data"], stamp["model"], stamp["good"].astype(bool)
        sigma = np.sqrt(stamp["variance"])
        residual = np.where(good, (data_ - model) / sigma, np.nan)
        x0, y0 = stamp["x0"], stamp["y0"]
        half = 9
        xs, ys = (
            slice(int(round(x0)) - half, int(round(x0)) + half + 1),
            slice(int(round(y0)) - half, int(round(y0)) + half + 1),
        )
        vmax = np.nanpercentile(data_[ys, xs], 99.5)
        vmin = np.nanpercentile(data_[ys, xs], 1)
        panels = [
            (data_[ys, xs], "gray_r", vmin, vmax),
            (model[ys, xs], "gray_r", vmin, vmax),
            (residual[ys, xs], "RdBu_r", -4, 4),
        ]
        for j, (image, cmap, lo, hi) in enumerate(panels):
            ax = fig.add_subplot(grid[j, 2 + k])
            if j == 2:
                ax.imshow(
                    image, origin="lower", cmap=cmap, norm=TwoSlopeNorm(0, lo, hi), interpolation="nearest"
                )
            else:
                ax.imshow(image, origin="lower", cmap=cmap, vmin=lo, vmax=hi, interpolation="nearest")
            masked = ~good[ys, xs]
            if masked.any():
                yy, xx = np.where(masked)
                ax.plot(xx, yy, ls="none", marker="s", mfc="none", mec="#CC79A7", ms=2.0, mew=0.5)
            cx, cy = x0 - xs.start, y0 - ys.start
            ax.add_patch(Circle((cx, cy), aperture_px, fill=False, color="#0072B2", lw=0.7, ls="--"))
            ax.add_patch(Circle((cx, cy), fit_radius_px, fill=False, color=NEUTRAL_GREY, lw=0.5, ls=":"))
            ax.set_xticks([])
            ax.set_yticks([])
            for spine in ax.spines.values():
                spine.set_edgecolor(DETECTOR_COLOURS[detector])
                spine.set_linewidth(1.2)
            if j == 0:
                ax.set_title(f"D{detector} {stamp['cwave']:.2f}" + r"$\,\mu$m", fontsize=7, pad=2)
            if k == 0:
                ax.set_ylabel(row_names[j], fontsize=7.5)
    fig.savefig(out_path)
    plt.close(fig)


def _mark_airglow(ax):
    for name, wavelength in AIRGLOW_LINES_UM.items():
        ax.axvline(wavelength, color=NEUTRAL_GREY, lw=0.6, ls="--")
        ax.text(
            wavelength,
            0.55,
            name,
            transform=ax.get_xaxis_transform(),
            fontsize=6.5,
            ha="right",
            va="center",
            color=NEUTRAL_GREY,
            rotation=90,
        )


def figure_diagnostics(galaxy, records: pd.DataFrame, out_path: Path) -> None:
    apply_style()
    fig, axes = plt.subplots(3, 1, figsize=(DOUBLE_COLUMN_IN, 5.2), sharex=True, gridspec_kw={"hspace": 0.08})
    measured = records[(records.reject_reason == "") & (records.screen_reason == "")]
    rejected = records[(records.reject_reason != "") | (records.screen_reason != "")]
    for detector in sorted(measured.detector.unique()):
        sub = measured[measured.detector == detector]
        colour = DETECTOR_COLOURS[int(detector)]
        axes[0].plot(sub.cwave_um, sub.chi2_dof_near, "o", color=colour, ms=3, label=f"D{int(detector)}")
        axes[0].plot(sub.cwave_um, sub.chi2_dof_near_point, "o", mfc="none", mec=colour, ms=3, mew=0.6)
        axes[1].plot(sub.cwave_um, 1 - sub.model_fraction_fit, "o", color=colour, ms=3)
        axes[2].plot(sub.cwave_um, sub.background_const_mjysr, "o", color=colour, ms=3)
        axes[2].plot(sub.cwave_um, sub.zodi_at_target_mjysr, "s", mfc="none", mec=colour, ms=3, mew=0.6)
    for reason, marker in REJECT_MARKERS.items():
        sub = rejected[(rejected.reject_reason == reason) | (rejected.screen_reason == reason)]
        if len(sub) == 0:
            continue
        wavelength = sub.cwave_um.fillna(np.nan)
        for ax, column in zip(
            axes, ("chi2_dof_near", "model_fraction_fit", "background_const_mjysr"), strict=True
        ):
            y = sub[column] if column in sub else pd.Series(np.nan, index=sub.index)
            if column == "model_fraction_fit":
                y = 1 - y
            y = y.fillna(ax.get_ylim()[1] if ax.get_ylim()[1] > 0 else 1)
            ax.plot(
                wavelength,
                y,
                marker=marker,
                ls="none",
                color="k",
                ms=5,
                mew=0.8,
                label=reason.replace("_", " ") if ax is axes[0] else None,
            )
    axes[0].set_yscale("log")
    axes[0].set_ylabel(r"$\chi^2/{\rm dof}$ (near)")
    axes[0].axhline(1, color=NEUTRAL_GREY, lw=0.5)
    axes[1].set_ylabel("masked model weight")
    axes[2].set_ylabel(r"background [MJy\,sr$^{-1}$]")
    axes[2].set_xlabel(WAVELENGTH_LABEL)
    axes[0].legend(ncol=4, fontsize=6.5, loc="lower center", bbox_to_anchor=(0.5, 1.02))
    for ax in axes:
        _mark_airglow(ax)
    panel_label(axes[0], "(a) filled: galaxy model; open: point-source control")
    panel_label(axes[1], "(b)")
    panel_label(axes[2], "(c) filled: fitted residual; open: ZODI model")
    axes[2].set_xlim(0.7, 5.1)
    fig.savefig(out_path)
    plt.close(fig)


def figure_sed(
    galaxy,
    records: pd.DataFrame,
    binned_model: pd.DataFrame,
    binned_aperture: pd.DataFrame,
    out_path: Path,
    external: pd.DataFrame | None = None,
    aperture_key: str = "2px",
) -> None:
    apply_style()
    fig, (ax, ax_ratio) = plt.subplots(
        2,
        1,
        figsize=(DOUBLE_COLUMN_IN, 4.6),
        sharex=True,
        gridspec_kw={"height_ratios": [3, 1], "hspace": 0.05},
    )
    measured = records[(records.reject_reason == "") & (records.screen_reason == "")]
    aperture_column = f"flux_aperture_{aperture_key}_ujy"
    for detector in sorted(measured.detector.unique()):
        sub = measured[measured.detector == detector]
        colour = DETECTOR_COLOURS[int(detector)]
        ax.errorbar(
            sub.cwave_um,
            sub.flux_model_ujy / 1e3,
            yerr=sub.flux_model_err_ujy / 1e3,
            fmt="o",
            color=colour,
            ms=2.2,
            lw=0.5,
            alpha=0.7,
            label=f"D{int(detector)}",
        )
        ax_ratio.plot(
            sub.cwave_um, sub.flux_model_ujy / sub[aperture_column], "o", color=colour, ms=2.2, alpha=0.7
        )
    ok = binned_model.n_exposures > 0
    ax.errorbar(
        binned_model.wavelength_um[ok],
        binned_model.flux_ujy[ok] / 1e3,
        yerr=binned_model.flux_err_scatter_ujy[ok].fillna(binned_model.flux_err_formal_ujy[ok]) / 1e3,
        fmt="-",
        color="k",
        lw=0.9,
        label="binned, model flux",
    )
    ok_a = binned_aperture.n_exposures > 0
    ax.plot(
        binned_aperture.wavelength_um[ok_a],
        binned_aperture.flux_ujy[ok_a] / 1e3,
        ls="--",
        color=NEUTRAL_GREY,
        lw=0.9,
        label=f"binned, aperture {aperture_key.replace('px', ' px')}",
    )
    if external is not None and len(external):
        ax.errorbar(
            external.wavelength_um,
            external.flux_ujy / 1e3,
            yerr=external.flux_err_ujy / 1e3,
            fmt="D",
            color="k",
            mfc="white",
            ms=4,
            lw=0.8,
            label="external photometry",
        )
    ratio = binned_model.flux_ujy / binned_aperture.flux_ujy
    ax_ratio.plot(binned_model.wavelength_um[ok], ratio[ok], "-", color="k", lw=0.9)
    ax_ratio.axhline(1, color=NEUTRAL_GREY, lw=0.5)
    ax_ratio.set_ylim(0.85, 1.15)
    ax_ratio.set_ylabel("model / aperture")
    ax_ratio.set_xlabel(WAVELENGTH_LABEL)
    ax.set_ylabel(FLUX_LABEL)
    ax.set_xlim(0.7, 5.1)
    ax.legend(ncol=2, fontsize=6.5, loc="upper right")
    _mark_airglow(ax)
    top = ax.secondary_xaxis(
        "top", functions=(lambda w: w / (1 + galaxy.redshift), lambda w: w * (1 + galaxy.redshift))
    )
    top.set_xlabel(REST_WAVELENGTH_LABEL)
    for name, rest in REST_FEATURES_UM.items():
        observed = rest * (1 + galaxy.redshift)
        if 0.75 < observed < 5.0:
            ax.axvline(observed, color="#CC79A7", lw=0.5, ls=":")
            ax.text(
                observed,
                0.03,
                name,
                transform=ax.get_xaxis_transform(),
                fontsize=6,
                ha="left",
                va="bottom",
                color="#CC79A7",
                rotation=90,
            )
    panel_label(ax, f"(a) {galaxy.name.replace('_', ' ')}, $z={galaxy.redshift:.4f}$")
    panel_label(ax_ratio, "(b)")
    fig.savefig(out_path)
    plt.close(fig)
