#!/usr/bin/env python3
"""Sample-level figures of the SED demo: detector-boundary test (figure 5), injection-recovery and error
calibration (figure 6), all SEDs in the rest frame (figure 7); plus the input table for the IRSA
Spectrophotometry Tool (Sersic mode).

usage: uv run python scripts/sed_demo/make_sample_figures.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sample_definition import DEMO_GALAXIES  # noqa: E402

from spherex_psb import RESULTS_ROOT  # noqa: E402
from spherex_psb.figures.style import (  # noqa: E402
    DETECTOR_COLOURS,
    DOUBLE_COLUMN_IN,
    NEUTRAL_GREY,
    REST_WAVELENGTH_LABEL,
    apply_style,
    panel_label,
)
from spherex_psb.validation.boundary import BOUNDARIES_UM  # noqa: E402

FIGURE_ROOT = Path(__file__).resolve().parents[2] / "docs" / "figures" / "sed_demo"
GALAXY_MARKERS = {
    "g1_reference": ("*", "#D55E00"),
    "g2_compact": ("s", "#0072B2"),
    "g3_large": ("D", "#009E73"),
    "g4_neighbour": ("^", "#E69F00"),
    "g5_no_legacy": ("v", "#CC79A7"),
    "g6_post_starburst": ("P", "#56B4E9"),
}
NORMALISATION_REST_UM = 1.6


def available(name: str) -> list[str]:
    return [g for g in DEMO_GALAXIES if (RESULTS_ROOT / g / "validation" / name).exists()]


def figure_boundaries(out_path: Path) -> pd.DataFrame:
    apply_style()
    galaxies = available("boundary_ratios.parquet")
    table = pd.concat(
        [pd.read_parquet(RESULTS_ROOT / g / "validation" / "boundary_ratios.parquet") for g in galaxies]
    )
    fig, axes = plt.subplots(1, 3, figsize=(DOUBLE_COLUMN_IN, 2.4), sharey=True, gridspec_kw={"wspace": 0.08})
    columns = [
        ("flux_model_ujy", "(a) model flux"),
        ("flux_aperture_2px_ujy", "(b) corrected 2 px aperture"),
        ("flux_point_ujy", "(c) point-source control"),
    ]
    names = list(BOUNDARIES_UM)
    for ax, (column, label) in zip(axes, columns, strict=True):
        for k, galaxy in enumerate(galaxies):
            sub = table[(table.galaxy == galaxy) & (table.flux_column == column)]
            marker, colour = GALAXY_MARKERS[galaxy]
            x = np.array([names.index(b) for b in sub.boundary]) + (k - len(galaxies) / 2) * 0.09
            err = sub.ratio_mag_err
            ax.errorbar(
                x,
                sub.ratio_mag,
                yerr=err,
                fmt=marker,
                color=colour,
                ms=5,
                mec="k",
                mew=0.4,
                lw=0.6,
                label=galaxy[3:].replace("_", " "),
            )
        ax.axhline(0, color=NEUTRAL_GREY, lw=0.6)
        ax.set_xticks(range(len(names)))
        ax.set_xticklabels(names)
        panel_label(ax, label)
    axes[0].set_ylabel(r"$-2.5\log_{10}(F_{\rm B}/F_{\rm A})$ at the boundary [mag]")
    axes[0].set_ylim(-0.35, 0.35)
    axes[2].legend(fontsize=6, loc="lower right", ncol=2)
    fig.savefig(out_path)
    plt.close(fig)
    return table


def figure_injection_and_pulls(out_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    apply_style()
    galaxies_i = available("injection_recovery.parquet")
    galaxies_p = available("repeat_pairs.parquet")
    injection = (
        pd.concat(
            [
                pd.read_parquet(RESULTS_ROOT / g / "validation" / "injection_recovery.parquet")
                for g in galaxies_i
            ]
        )
        if galaxies_i
        else pd.DataFrame()
    )
    pairs = (
        pd.concat(
            [pd.read_parquet(RESULTS_ROOT / g / "validation" / "repeat_pairs.parquet") for g in galaxies_p]
        )
        if galaxies_p
        else pd.DataFrame()
    )
    fig, (ax_inj, ax_pull) = plt.subplots(
        1, 2, figsize=(DOUBLE_COLUMN_IN, 2.6), gridspec_kw={"wspace": 0.28, "width_ratios": [1.6, 1]}
    )
    if len(injection):
        good = injection[injection.reject_reason == ""]
        for galaxy in galaxies_i:
            sub = good[good.galaxy == galaxy]
            marker, colour = GALAXY_MARKERS[galaxy]
            ax_inj.plot(
                sub.injected_cwave_um,
                sub.flux_model_recovered_ratio,
                marker,
                color=colour,
                ms=4,
                mec="k",
                mew=0.3,
                ls="none",
                label=galaxy[3:].replace("_", " "),
            )
            ax_inj.plot(
                sub.injected_cwave_um,
                sub.flux_aperture_2px_recovered_ratio,
                marker,
                color=colour,
                ms=4,
                mfc="none",
                mew=0.6,
                ls="none",
            )
        ax_inj.axhline(1, color=NEUTRAL_GREY, lw=0.6)
        ax_inj.set_xlabel(r"$\lambda_{\rm obs}\ [\mu{\rm m}]$")
        ax_inj.set_ylabel("recovered / injected flux")
        ax_inj.set_ylim(0.8, 1.2)
        ax_inj.legend(fontsize=6, ncol=3, loc="upper right")
        panel_label(ax_inj, "(a) filled: model; open: corrected aperture")
    if len(pairs):
        bins = np.linspace(-5, 5, 41)
        for detector in sorted(pairs.detector.unique()):
            pull = pairs[pairs.detector == detector].pull
            pull = pull[np.isfinite(pull)]
            robust_sigma = 1.4826 * np.median(np.abs(pull - np.median(pull)))
            ax_pull.hist(
                pull,
                bins=bins,
                histtype="step",
                color=DETECTOR_COLOURS[int(detector)],
                lw=0.9,
                label=f"D{int(detector)}, $\\sigma_{{\\rm rob}}={robust_sigma:.2f}$",
            )
        x = np.linspace(-5, 5, 200)
        ax_pull.plot(
            x,
            len(pairs)
            / len(pairs.detector.unique())
            * (bins[1] - bins[0])
            * np.exp(-0.5 * x**2)
            / np.sqrt(2 * np.pi),
            color="k",
            lw=0.6,
            ls="--",
        )
        ax_pull.set_xlabel(r"pull $(F_1-F_2)/\sqrt{\sigma_1^2+\sigma_2^2}$")
        ax_pull.set_ylabel("repeat pairs")
        ax_pull.legend(fontsize=5.5, loc="upper left")
        panel_label(ax_pull, "(b)", x=0.85)
    fig.savefig(out_path)
    plt.close(fig)
    return injection, pairs


def figure_all_seds(out_path: Path) -> None:
    apply_style()
    fig, ax = plt.subplots(figsize=(DOUBLE_COLUMN_IN, 3.4))
    for galaxy, definition in DEMO_GALAXIES.items():
        path = RESULTS_ROOT / galaxy / "sed_model.parquet"
        if not path.exists():
            continue
        sed = pd.read_parquet(path)
        sed = sed[sed.n_exposures > 0]
        rest = sed.wavelength_um / (1 + definition.redshift)
        flux = sed.flux_ujy_dered if "flux_ujy_dered" in sed else sed.flux_ujy
        norm = np.interp(NORMALISATION_REST_UM, rest, flux)
        marker, colour = GALAXY_MARKERS[galaxy]
        err = sed.flux_err_scatter_ujy.fillna(sed.flux_err_formal_ujy) / norm
        ax.errorbar(
            rest,
            flux / norm,
            yerr=err,
            fmt="-",
            marker=marker,
            color=colour,
            ms=3,
            mec="k",
            mew=0.3,
            lw=0.8,
            label=f"{galaxy[3:].replace('_', ' ')} ($z={definition.redshift:.3f}$)",
        )
    ax.axvline(NORMALISATION_REST_UM, color=NEUTRAL_GREY, lw=0.5, ls=":")
    ax.set_xlabel(REST_WAVELENGTH_LABEL)
    ax.set_ylabel(r"$F_\nu / F_\nu(1.6\,\mu{\rm m})$")
    ax.set_xlim(0.7, 4.8)
    ax.legend(fontsize=6.5, loc="upper right")
    fig.savefig(out_path)
    plt.close(fig)


def irsa_tool_table(out_path: Path) -> None:
    rows = []
    for galaxy, definition in DEMO_GALAXIES.items():
        shape = definition.shape
        rows.append(
            {
                "name": galaxy,
                "ra": definition.ra,
                "dec": definition.dec,
                "sersic_index": shape.sersic_index,
                "axis_ratio": shape.axis_ratio,
                "position_angle_deg_east_of_north": shape.position_angle_deg,
                "effective_radius_arcsec": min(shape.effective_radius_arcsec, 19.9),
                "note": "Re capped at 19.9 arcsec (tool limit)"
                if shape.effective_radius_arcsec >= 20
                else "",
            }
        )
    pd.DataFrame(rows).to_csv(out_path, index=False)


def main() -> None:
    FIGURE_ROOT.mkdir(parents=True, exist_ok=True)
    boundaries = figure_boundaries(FIGURE_ROOT / "fig5_detector_boundaries.png")
    pd.set_option("display.width", 220)
    print(
        boundaries.pivot_table(index=["galaxy", "boundary"], columns="flux_column", values="ratio_mag")
        .round(3)
        .to_string()
    )
    figure_injection_and_pulls(FIGURE_ROOT / "fig6_injection_and_errors.png")
    figure_all_seds(FIGURE_ROOT / "fig7_all_seds_rest_frame.png")
    irsa_tool_table(RESULTS_ROOT / "irsa_spectrophotometry_tool_input.csv")
    print("figures written to", FIGURE_ROOT)


if __name__ == "__main__":
    main()
