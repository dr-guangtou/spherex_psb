"""Figures for the review of the student's SDSS 48k SPHEREx photometry (run the other three scripts first).

1. Same exposures, three demo galaxies: our forced Sersic total flux versus the run's PSF and aperture fluxes.
2. Sample-wide: PSF flux / aperture flux versus clipped pixels; per-exposure repeatability per detector.
3. Coverage: measurements per galaxy and per-exposure aperture S/N per detector.
usage: uv run python scripts/sdss48k_review/make_figures.py
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyarrow.dataset as ds
from matplotlib.colors import LogNorm

from spherex_psb.figures.style import (
    DETECTOR_COLOURS,
    DOUBLE_COLUMN_IN,
    NEUTRAL_GREY,
    WAVELENGTH_LABEL,
    apply_style,
    panel_label,
)

RUN_DIR = "/Users/shuang/data/spherex/spherex_sdss48k_phot"
SCRATCH = "/Users/shuang/data/spherex/scratch"
FIGURE_DIR = Path(__file__).resolve().parents[2] / "docs" / "figures" / "sdss48k_review"
apply_style()


def figure_demo_comparison():
    matched = pd.read_parquet(f"{SCRATCH}/sdss48k_demo_match.parquet")
    matched = matched[matched.screen_reason == ""]
    galaxies = {"g1_reference": "reference", "g3_large": "large", "g6_post_starburst": "post-starburst-like"}
    fig, axes = plt.subplots(
        2,
        3,
        figsize=(DOUBLE_COLUMN_IN, 4.2),
        sharex=True,
        gridspec_kw={"height_ratios": [2.2, 1], "hspace": 0.05, "wspace": 0.28},
    )
    for column, (galaxy, label) in enumerate(galaxies.items()):
        block = matched[matched.galaxy == galaxy].sort_values("wv_um")
        top, bottom = axes[0, column], axes[1, column]
        top.plot(
            block.wv_um, block.flux_model_ujy / 1e3, ".", ms=2.2, color="black", label="ours: Sersic total"
        )
        top.plot(
            block.wv_um,
            block.aper_flux_uJy / 1e3,
            ".",
            ms=2.2,
            color=NEUTRAL_GREY,
            label=r"run: 12.3$''$ aperture",
        )
        for detector, part in block.groupby("detector_id"):
            top.plot(
                part.wv_um,
                part.opt_flux_uJy / 1e3,
                ".",
                ms=2.2,
                color=DETECTOR_COLOURS[detector],
                label="run: PSF fit" if detector == 1 else None,
            )
            bottom.plot(
                part.wv_um,
                part.opt_flux_uJy / part.flux_model_ujy,
                ".",
                ms=2.2,
                color=DETECTOR_COLOURS[detector],
            )
        bottom.plot(block.wv_um, block.aper_flux_uJy / block.flux_model_ujy, ".", ms=2.2, color=NEUTRAL_GREY)
        top.set_yscale("log")
        low, high = block.flux_model_ujy.min() / 1e3, block.flux_model_ujy.max() / 1e3
        top.set_ylim(0.25 * low, 12 * high)
        n_beyond = int(
            ((block.aper_flux_uJy / 1e3 > 12 * high) | (block.opt_flux_uJy / 1e3 > 12 * high)).sum()
        )
        if n_beyond:
            top.text(
                0.97,
                0.03,
                f"{n_beyond} off scale",
                transform=top.transAxes,
                ha="right",
                va="bottom",
                fontsize=7,
            )
        bottom.axhline(1, color="black", lw=0.6)
        bottom.set_ylim(0, 1.6)
        bottom.set_xscale("log")
        bottom.set_xticks([0.8, 1, 2, 3, 4, 5], ["0.8", "1", "2", "3", "4", "5"])
        bottom.set_xlabel(WAVELENGTH_LABEL)
        panel_label(top, f"{galaxy.split('_')[0]} ({label})")
        n_off = int((block.opt_flux_uJy / block.flux_model_ujy > 1.6).sum())
        if n_off:
            bottom.text(
                0.97,
                0.9,
                f"{n_off} points above 1.6",
                transform=bottom.transAxes,
                ha="right",
                va="top",
                fontsize=7,
            )
    axes[0, 0].set_ylabel(r"$F_\nu$ [mJy]")
    axes[1, 0].set_ylabel("run / our total")
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        loc="lower center",
        bbox_to_anchor=(0.5, 0.9),
        ncol=3,
        markerscale=2.5,
        handletextpad=0.2,
    )
    fig.savefig(FIGURE_DIR / "fig1_demo_galaxies_same_exposures.png")
    plt.close(fig)


def figure_sample_quality():
    sample = pd.read_parquet(f"{SCRATCH}/sdss48k_quality_sample.parquet")
    sample = sample[sample.snr > 10]
    pairs = pd.read_parquet(f"{SCRATCH}/sdss48k_close_pairs.parquet")
    columns = ["n_pix_outlier", "opt_flux_uJy", "aper_flux_uJy", "aper_flux_uJy_err", "detector_id"]
    subset = (
        ds.dataset(f"{RUN_DIR}/photometry.parquet")
        .to_table(columns=columns)
        .to_pandas()
        .sample(3_000_000, random_state=1)
    )
    subset = subset[subset.aper_flux_uJy / subset.aper_flux_uJy_err > 10]
    ratio = subset.opt_flux_uJy / subset.aper_flux_uJy

    fig, axes = plt.subplots(1, 3, figsize=(DOUBLE_COLUMN_IN, 2.5), gridspec_kw={"wspace": 0.38})
    ax = axes[0]
    ax.hist2d(
        subset.n_pix_outlier,
        np.log10(ratio.clip(1e-2, 1e3)),
        bins=[np.arange(-0.5, 45.5, 1), np.linspace(-1, 2, 90)],
        norm=LogNorm(),
        cmap="Greys",
    )
    ax.axhline(np.log10(1.5), color=DETECTOR_COLOURS[5], lw=0.7, ls="--")
    ax.set_xlabel("clipped pixels")
    ax.set_ylabel(r"$\log_{10}$ (PSF flux / aperture flux)")
    panel_label(ax, "(a)", y=0.97)

    ax = axes[1]
    detectors = np.arange(1, 7)
    above = [(ratio[subset.detector_id == d] > 1.5).mean() for d in detectors]
    ax.bar(detectors, above, color=[DETECTOR_COLOURS[d] for d in detectors])
    ax.set_xticks(detectors, [f"D{d}" for d in detectors])
    ax.set_ylabel("fraction with PSF $>$ 1.5 $\\times$ aperture")
    ax.minorticks_off()
    panel_label(ax, "(b)", x=0.75, y=0.97)

    ax = axes[2]

    def robust_fractional(values):
        values = values[np.isfinite(values)]
        return 1.4826 * np.median(np.abs(values - np.median(values))) / np.sqrt(2)

    psf = [robust_fractional(pairs.psf_fractional_difference[pairs.detector_id == d]) for d in detectors]
    aperture = [
        robust_fractional(pairs.aperture_fractional_difference[pairs.detector_id == d]) for d in detectors
    ]
    ax.plot(detectors, np.array(psf) * 100, "o-", color="black", ms=3.5, label="PSF fit")
    ax.plot(detectors, np.array(aperture) * 100, "s--", color=NEUTRAL_GREY, ms=3.5, label="aperture")
    ax.set_xticks(detectors, [f"D{d}" for d in detectors])
    ax.set_ylabel("per-exposure scatter [\\%]")
    ax.set_ylim(0, 18)
    ax.minorticks_off()
    ax.legend(loc="upper left")
    panel_label(ax, "(c)", x=0.86, y=0.12)
    fig.savefig(FIGURE_DIR / "fig2_clipping_and_repeatability.png")
    plt.close(fig)


def figure_coverage():
    targets = pd.read_parquet(f"{RUN_DIR}/targets.parquet")
    sample = pd.read_parquet(f"{SCRATCH}/sdss48k_quality_sample.parquet")
    columns = ["detector_id", "aper_flux_uJy", "aper_flux_uJy_err"]
    subset = (
        ds.dataset(f"{RUN_DIR}/photometry.parquet")
        .to_table(columns=columns)
        .to_pandas()
        .sample(2_000_000, random_state=2)
    )
    snr = subset.aper_flux_uJy / subset.aper_flux_uJy_err
    fig, axes = plt.subplots(1, 2, figsize=(DOUBLE_COLUMN_IN * 0.75, 2.4), gridspec_kw={"wspace": 0.35})
    ax = axes[0]
    ax.hist(targets.n_meas, bins=np.arange(0, 1000, 10), color=NEUTRAL_GREY)
    ax.set_xlabel("measurements per galaxy")
    ax.set_ylabel("galaxies")
    ax.set_xlim(0, 800)
    panel_label(ax, "(a)", x=0.85)
    ax = axes[1]
    detectors = np.arange(1, 7)
    levels = np.array([np.percentile(snr[subset.detector_id == d], [5, 25, 50, 75, 95]) for d in detectors])
    for d, row in zip(detectors, levels, strict=True):
        ax.plot([d, d], [row[0], row[4]], color=DETECTOR_COLOURS[d], lw=0.8)
        ax.plot([d, d], [row[1], row[3]], color=DETECTOR_COLOURS[d], lw=3.5)
        ax.plot(d, row[2], "o", color="white", mec=DETECTOR_COLOURS[d], ms=3.5)
    ax.set_yscale("log")
    ax.set_xticks(detectors, [f"D{d}" for d in detectors])
    ax.minorticks_off()
    ax.set_ylabel("aperture S/N per exposure")
    panel_label(ax, "(b)", x=0.85)
    fig.savefig(FIGURE_DIR / "fig3_coverage_and_depth.png")
    plt.close(fig)
    del sample


if __name__ == "__main__":
    figure_demo_comparison()
    figure_sample_quality()
    figure_coverage()
    print("figures written to", FIGURE_DIR)
