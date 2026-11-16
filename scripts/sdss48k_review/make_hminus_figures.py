"""Figures 4-6 of the SDSS 48k review: the H-minus bump index (Hbump_opt) of individual galaxies against the
SDSS optical indices, against the H-bump paper's model populations, and the checks behind it.
Run `measure_hminus_bump.py` first.
usage: uv run python scripts/sdss48k_review/make_hminus_figures.py
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from scipy.ndimage import gaussian_filter

from spherex_psb import RESULTS_ROOT
from spherex_psb.figures.style import DOUBLE_COLUMN_IN, NEUTRAL_GREY, apply_style, panel_label

RESULT_DIR = RESULTS_ROOT / "sdss48k_hminus"
MODEL_ROOT = "/Users/shuang/Dropbox/work/project/luandun/stellar_pop/fsps_agb/output"
FIGURE_DIR = Path(__file__).resolve().parents[2] / "docs" / "figures" / "sdss48k_review"
BUMP_LABEL = r"H$^{-}$ bump, Hbump$_{\rm opt}$ [mag]"
HDELTA_LABEL = r"H$\delta_{\rm A}$ [\AA]"
BUMP_RANGE = (0.035, -0.115)  # inverted: a stronger bump is higher, as in the H-bump paper
MODEL_COLOURS = {"TP-AGB off": "#0072B2", "TP-AGB on": "#D55E00"}
MODELS = {"TP-AGB off": ("population", "agb0"), "TP-AGB on": ("population_lw02", "agb2")}
DEMO_STUDY_INDEX = {
    1806085614093756416: ("g1", -0.057, 0.017),
    1342183509195778048: ("g2", -0.028, 0.020),
    1855517184537683968: ("g3", -0.050, 0.013),
    2477075517577127936: ("g4", -0.055, 0.033),
    1875860345654896640: ("g5", -0.040, 0.011),
    3340648454601861120: ("g6", -0.018, 0.015),
}
apply_style()


def load_data():
    data = pd.read_parquet(RESULT_DIR / "hminus_bump_indices.parquet")
    return data[np.isfinite(data.hminus_bump_mag)]


def load_model(name):
    directory, key = MODELS[name]
    with np.load(f"{MODEL_ROOT}/{directory}/indices.npz") as model:
        keep = model["epoch_gyr"] >= 1.0
        return {
            "d4000": model[f"d4000_{key}"][keep],
            "hdelta_a": model[f"hdelta_a_{key}"][keep],
            "bump": model[f"h_minus_bump_r100_{key}"][keep],
        }


def density_contours(axis, x, y, x_range, y_range, fractions, filled, colour, bins=80, smooth=1.5, **kwargs):
    """Contours of a smoothed 2-D histogram at the levels enclosing the given fractions of the points."""
    low_y, high_y = sorted(y_range)
    counts, x_edges, y_edges = np.histogram2d(x, y, bins=bins, range=[list(x_range), [low_y, high_y]])
    counts = gaussian_filter(counts, smooth)
    flat = np.sort(counts.ravel())[::-1]
    cumulative = np.cumsum(flat) / flat.sum()
    levels = sorted({float(flat[np.searchsorted(cumulative, f)]) for f in fractions})
    centres_x, centres_y = 0.5 * (x_edges[1:] + x_edges[:-1]), 0.5 * (y_edges[1:] + y_edges[:-1])
    if filled:
        shades = [str(v) for v in np.linspace(0.85, 0.55, len(levels))]
        axis.contourf(
            centres_x, centres_y, counts.T, levels=levels + [counts.max() * 1.01], colors=shades, **kwargs
        )
        axis.contour(centres_x, centres_y, counts.T, levels=levels, colors="0.45", linewidths=0.5, **kwargs)
    else:
        axis.contour(
            centres_x,
            centres_y,
            counts.T,
            levels=levels,
            colors=colour,
            linewidths=[0.8, 1.3][: len(levels)],
            **kwargs,
        )


def running_median(axis, x, y, edges, minimum=50):
    centres, medians, errors = [], [], []
    for low, high in zip(edges[:-1], edges[1:], strict=True):
        inside = (x >= low) & (x < high)
        if inside.sum() < minimum:
            continue
        values = y[inside]
        centres.append(np.median(x[inside]))
        medians.append(np.median(values))
        errors.append(1.2533 * 1.4826 * np.median(np.abs(values - np.median(values))) / np.sqrt(inside.sum()))
    axis.errorbar(
        centres, medians, yerr=errors, color="black", marker="o", ms=2.8, lw=1.0, capsize=0, zorder=5
    )


def typical_error(axis, x_error, y_error, x_position, y_position):
    axis.errorbar(
        [x_position],
        [y_position],
        xerr=[x_error],
        yerr=[y_error],
        color="black",
        lw=0.9,
        capsize=1.5,
        zorder=6,
    )
    axis.text(x_position - 1.6 * x_error, y_position, "typical error", ha="right", va="center", fontsize=6.5)


def figure_data_planes(data):
    fig, axes = plt.subplots(1, 2, figsize=(DOUBLE_COLUMN_IN, 3.0), sharey=True, gridspec_kw={"wspace": 0.06})
    panels = [
        (
            "d4000_n_sub",
            "d4000_n_sub_err",
            r"D$_{\rm n}$4000",
            (1.05, 2.25),
            np.arange(1.1, 2.21, 0.05),
            "(a)",
        ),
        ("lick_hd_a_sub", "lick_hd_a_sub_err", HDELTA_LABEL, (-5, 8.5), np.arange(-4.5, 8.01, 0.5), "(b)"),
    ]
    bump = data.hminus_bump_mag.to_numpy()
    for axis, (column, error_column, label, x_range, edges, tag) in zip(axes, panels, strict=True):
        x = data[column].to_numpy()
        density_contours(axis, x, bump, x_range, BUMP_RANGE, [0.995, 0.95, 0.68], True, None)
        running_median(axis, x, bump, edges)
        typical_error(
            axis,
            np.median(data[error_column]),
            np.median(data.hminus_bump_err_mag),
            x_range[0] + 0.85 * (x_range[1] - x_range[0]),
            0.020,
        )
        axis.set_xlim(x_range)
        axis.set_xlabel(label)
        panel_label(axis, tag)
    axes[0].set_ylim(BUMP_RANGE)
    axes[0].set_ylabel(BUMP_LABEL)
    handles = [
        Patch(
            facecolor="0.7", edgecolor="0.45", lw=0.5, label=f"{len(data):,} SDSS galaxies (68, 95, 99.5\\%)"
        ),
        Line2D([], [], color="black", marker="o", ms=2.8, label="running median"),
    ]
    fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, 0.93), ncol=2, frameon=False)
    fig.savefig(FIGURE_DIR / "fig4_hminus_bump_vs_optical_indices.png")
    plt.close(fig)


def figure_model_planes(data):
    models = {name: load_model(name) for name in MODELS}
    fig, axes = plt.subplots(1, 2, figsize=(DOUBLE_COLUMN_IN, 3.0), sharey=True, gridspec_kw={"wspace": 0.06})
    panels = [
        ("d4000_sub", "d4000_sub_err", "d4000", "D4000", (1.1, 2.6), np.arange(1.15, 2.51, 0.05), "(a)"),
        (
            "lick_hd_a_sub",
            "lick_hd_a_sub_err",
            "hdelta_a",
            HDELTA_LABEL,
            (-6, 8.5),
            np.arange(-4.5, 8.01, 0.5),
            "(b)",
        ),
    ]
    bump = data.hminus_bump_mag.to_numpy()
    for axis, (column, error_column, model_key, label, x_range, edges, tag) in zip(axes, panels, strict=True):
        x = data[column].to_numpy()
        density_contours(axis, x, bump, x_range, BUMP_RANGE, [0.95, 0.68], True, None)
        for name, model in models.items():
            density_contours(
                axis,
                model[model_key],
                model["bump"],
                x_range,
                BUMP_RANGE,
                [0.95, 0.68],
                False,
                MODEL_COLOURS[name],
                bins=120,
                smooth=1.2,
            )
        running_median(axis, x, bump, edges)
        typical_error(
            axis,
            np.median(data[error_column]),
            np.median(data.hminus_bump_err_mag),
            x_range[0] + 0.85 * (x_range[1] - x_range[0]),
            -0.098,
        )
        axis.set_xlim(x_range)
        axis.set_xlabel(label)
        panel_label(axis, tag)
    axes[0].set_ylim(BUMP_RANGE)
    axes[0].set_ylabel(BUMP_LABEL)
    handles = [
        Patch(facecolor="0.7", edgecolor="0.45", lw=0.5, label="SDSS galaxies (68, 95\\%)"),
        Line2D([], [], color="black", marker="o", ms=2.8, label="running median"),
        Line2D([], [], color=MODEL_COLOURS["TP-AGB off"], lw=1.1, label="models, TP-AGB off (68, 95\\%)"),
        Line2D([], [], color=MODEL_COLOURS["TP-AGB on"], lw=1.1, label="models, TP-AGB on (68, 95\\%)"),
    ]
    fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, 0.93), ncol=2, frameon=False)
    fig.savefig(FIGURE_DIR / "fig5_hminus_bump_with_models.png")
    plt.close(fig)


def figure_checks(data):
    checks = pd.read_parquet(RESULT_DIR / "bootstrap_check.parquet")
    fig, axes = plt.subplots(
        2, 2, figsize=(DOUBLE_COLUMN_IN, 5.0), gridspec_kw={"wspace": 0.3, "hspace": 0.38}
    )

    axis = axes[0, 0]
    bins = np.linspace(-0.12, 0.12, 61)
    axis.hist(
        data.d3_minus_d2_step_uncorrected.dropna() * 100,
        bins=bins * 100,
        histtype="step",
        color=NEUTRAL_GREY,
        lw=1.0,
        label=r"as delivered (6.15$''$ pixel)",
    )
    axis.hist(
        data.d3_minus_d2_step.dropna() * 100,
        bins=bins * 100,
        histtype="step",
        color="black",
        lw=1.0,
        label="solid-angle map",
    )
    for values, colour in [
        (data.d3_minus_d2_step_uncorrected, NEUTRAL_GREY),
        (data.d3_minus_d2_step, "black"),
    ]:
        axis.axvline(np.nanmedian(values) * 100, color=colour, ls="--", lw=0.8)
    axis.set_xlabel(r"D3 $-$ D2 flux step in the overlap [\%]")
    axis.set_ylabel("galaxies")
    axis.set_ylim(0, axis.get_ylim()[1] * 1.3)
    axis.legend(loc="upper left", fontsize=6.5)
    panel_label(axis, "(a)", x=0.9)

    axis = axes[0, 1]
    redshift_edges = np.linspace(0.03, 0.06, 7)
    centres = 0.5 * (redshift_edges[1:] + redshift_edges[:-1])
    dn_bins = [(1.0, 1.4), (1.4, 1.7), (1.7, 1.9), (1.9, 2.5)]
    shades = ["#56B4E9", "#009E73", "#E69F00", "#D55E00"]
    for (low, high), colour in zip(dn_bins, shades, strict=True):
        part = data[(data.d4000_n_sub >= low) & (data.d4000_n_sub < high)]
        medians, errors = [], []
        for z_low, z_high in zip(redshift_edges[:-1], redshift_edges[1:], strict=True):
            values = part.hminus_bump_mag[(part.redshift >= z_low) & (part.redshift < z_high)]
            medians.append(values.median())
            errors.append(
                1.2533 * 1.4826 * np.median(np.abs(values - values.median())) / np.sqrt(len(values))
            )
        axis.errorbar(
            centres,
            medians,
            yerr=errors,
            color=colour,
            marker="o",
            ms=2.8,
            lw=1.0,
            capsize=0,
            label=rf"D$_{{\rm n}}$4000 {low:.1f}--{high:.1f}",
        )
    axis.set_ylim(-0.030, -0.0465)
    axis.yaxis.set_major_locator(plt.MultipleLocator(0.005))
    axis.yaxis.set_major_formatter(plt.FuncFormatter(lambda value, _: f"${value:.3f}$"))
    axis.set_xlabel("redshift")
    axis.set_ylabel(r"median H$^{-}$ bump [mag]")
    axis.legend(loc="lower right", fontsize=6.5, ncol=2)
    panel_label(axis, "(b)")

    axis = axes[1, 0]
    axis.loglog(checks.analytic_err_mag, checks.bootstrap_err_mag, ".", ms=2.5, color="black", alpha=0.6)
    limits = [0.005, 0.1]
    axis.plot(limits, limits, color=NEUTRAL_GREY, lw=0.8)
    axis.set_xlim(limits)
    axis.set_ylim(limits)
    axis.set_xlabel("analytic error [mag]")
    axis.set_ylabel("bootstrap error [mag]")
    ratio = np.median(checks.bootstrap_err_mag / checks.analytic_err_mag)
    axis.text(
        0.95,
        0.06,
        f"{len(checks)} galaxies, median ratio {ratio:.2f}",
        transform=axis.transAxes,
        ha="right",
        fontsize=6.5,
    )
    panel_label(axis, "(c)")

    axis = axes[1, 1]
    for specobjid, (name, study, study_error) in DEMO_STUDY_INDEX.items():
        row = data[data.specobjid == specobjid].iloc[0]
        axis.errorbar(
            study,
            row.hminus_bump_mag,
            xerr=study_error,
            yerr=row.hminus_bump_err_mag,
            color="black",
            marker="o",
            ms=3,
            lw=0.8,
            capsize=0,
        )
        axis.plot(study, row.hminus_bump_uncorrected_mag, "o", mfc="white", mec=NEUTRAL_GREY, ms=3)
        axis.annotate(
            name,
            (study, row.hminus_bump_mag),
            xytext={"g3": (-12, 4), "g6": (-12, 4)}.get(name, (5, 2)),
            textcoords="offset points",
            fontsize=6.5,
        )
    limits = [0.02, -0.14]
    axis.plot(limits, limits, color=NEUTRAL_GREY, lw=0.8)
    axis.set_xlim(limits)
    axis.set_ylim(limits)
    axis.set_xticks([0.0, -0.05, -0.10])
    axis.set_yticks([0.0, -0.05, -0.10])
    axis.set_xlabel(r"demo study (forced Sersic, DR1 + QR3) [mag]")
    axis.set_ylabel("this run (aperture) [mag]")
    axis.legend(
        handles=[
            Line2D([], [], color="black", marker="o", ms=3, lw=0, label="solid-angle map applied"),
            Line2D([], [], color=NEUTRAL_GREY, marker="o", mfc="white", ms=3, lw=0, label="as delivered"),
        ],
        loc="lower right",
        fontsize=6.5,
    )
    panel_label(axis, "(d)")
    fig.savefig(FIGURE_DIR / "fig6_hminus_bump_checks.png")
    plt.close(fig)


if __name__ == "__main__":
    data = load_data()
    figure_data_planes(data)
    figure_model_planes(data)
    figure_checks(data)
    print("figures written to", FIGURE_DIR)
