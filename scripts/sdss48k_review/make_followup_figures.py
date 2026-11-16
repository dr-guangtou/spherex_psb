"""Figures 14-17 of the SDSS 48k review: post-starburst stacks, inclination and detector controls, the stacks
against the late-epoch models, and the exposures of target 45124.
Run `stack_post_starbursts.py`, `control_inclination_and_detectors.py`, `compare_stacks_with_models.py` and
`inspect_detector_failures.py` first.
usage: uv run python scripts/sdss48k_review/make_followup_figures.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Circle

sys.path.insert(0, str(Path(__file__).resolve().parent))
from compare_stacks_with_models import LATE_EPOCH_GYR, load_population  # noqa: E402
from investigate_bump_outliers import significance  # noqa: E402
from make_hminus_figures import FIGURE_DIR, HDELTA_LABEL, density_contours  # noqa: E402
from make_stack_figures import (  # noqa: E402
    DN4000_LABEL,
    FEATURES_UM,
    HDELTA_COLOURS,
    INDEX_LABEL,
    MODEL_COLOURS,
    shade_windows,
)
from measure_hminus_bump import FIT_RANGE_UM, OUT_DIR, WINDOWS_UM  # noqa: E402
from stack_sed_and_bump import N_HDELTA_BINS, load_galaxies  # noqa: E402

from spherex_psb.figures.galaxy_figures import optical_image  # noqa: E402
from spherex_psb.figures.style import (  # noqa: E402
    DETECTOR_COLOURS,
    DOUBLE_COLUMN_IN,
    NEUTRAL_GREY,
    REST_WAVELENGTH_LABEL,
    WAVELENGTH_LABEL,
    apply_style,
    panel_label,
)

apply_style()
PSB_STYLES = {
    "e_plus_a_young": ("young E+A", "#D55E00", "o"),
    "e_plus_a_old": ("old E+A", "#E69F00", "D"),
    "balmer_excess": (r"H$\delta_{\rm A}$ excess", "#0072B2", "s"),
    "balmer_deficit": (r"H$\delta_{\rm A}$ deficit", "#56B4E9", "v"),
}
ROLE_STYLES = {
    "candidate": "candidate",
    "population": "population controls",
    "quiescent": "quiescent controls",
}
BROAD_D4000_LABEL = r"broad D4000 (MPA-JHU)"


def set_of(name: str) -> str:
    for key in PSB_STYLES:
        if name.startswith(key):
            return key
    return name


def row_means(cells: pd.DataFrame, column: str = "stack_continuum_index") -> pd.DataFrame:
    per_cell = cells[cells.cell >= 0].copy()
    per_cell["row"] = per_cell.cell // N_HDELTA_BINS
    return per_cell.groupby("row").agg(dn4000=("dn4000_median", "median"), index=(column, "mean"))


def figure_post_starbursts(stacks, profiles, members, galaxies, cells):
    fig, axes = plt.subplots(2, 2, figsize=(DOUBLE_COLUMN_IN, 5.8))
    ax = axes[0, 0]
    density_contours(
        ax,
        galaxies.d4000_n_sub,
        galaxies.lick_hd_a_sub,
        (1.0, 2.35),
        (-5.5, 8.5),
        [0.68, 0.95, 0.995],
        filled=True,
        colour="0.5",
    )
    candidates = members[members.role == "candidate"].copy()
    candidates["set"] = candidates.group.map(set_of)
    for key, (label, colour, marker) in PSB_STYLES.items():
        chosen = candidates[candidates.set == key]
        size = 7 if key.startswith("e_plus_a") else 2.5
        ax.scatter(
            chosen.d4000_n_sub,
            chosen.lick_hd_a_sub,
            s=size,
            color=colour,
            marker=marker,
            lw=0,
            label=f"{label} ({len(chosen)})",
            zorder=3,
        )
    ax.set_xlim(1.05, 2.3)
    ax.set_ylim(-5.5, 8.5)
    ax.set_xlabel(DN4000_LABEL)
    ax.set_ylabel(HDELTA_LABEL)
    ax.legend(loc="upper right", fontsize=6, markerscale=1.5, handletextpad=0.2)
    ax.text(1.08, -5.0, r"all: H$\alpha$ emission EW $<$ 3 \AA", fontsize=6.5)
    panel_label(ax, "(a)", x=0.04, y=0.93)

    ax = axes[0, 1]
    rows = row_means(cells)
    ax.plot(rows.dn4000, rows["index"], "-", color=NEUTRAL_GREY, lw=1.0, label="cell rows (fig. 9)", zorder=1)
    by_set = stacks[~stacks.set.str.endswith("_all")]
    offsets = {"candidate": 0.0, "population": -0.012, "quiescent": 0.012}
    for _, row in by_set.iterrows():
        label, colour, marker = PSB_STYLES[set_of(row.set)]
        filled = row.role == "candidate"
        ax.errorbar(
            row.dn4000_median + offsets[row.role],
            row.stack_continuum_index,
            row.stack_continuum_index_err,
            fmt=marker if filled else ("o" if row.role == "population" else "s"),
            ms=4.5 if filled else 3.5,
            color=colour,
            mfc=colour if filled else "white",
            mew=0.8,
            elinewidth=0.7,
            capsize=0,
            zorder=3 if filled else 2,
        )
    handles = [Line2D([], [], color=NEUTRAL_GREY, lw=1.0, label="cell rows (fig. 9)")]
    handles += [
        Line2D([], [], ls="", marker=m, color=c, ms=4.5, label=label) for label, c, m in PSB_STYLES.values()
    ]
    handles += [
        Line2D([], [], ls="", marker="o", mfc="white", color="0.3", ms=3.5, label="population controls"),
        Line2D([], [], ls="", marker="s", mfc="white", color="0.3", ms=3.5, label="quiescent controls"),
    ]
    ax.legend(handles=handles, loc="lower left", fontsize=5.6, ncol=2, handletextpad=0.2, columnspacing=0.6)
    ax.set_xlabel(DN4000_LABEL + " (median of the stack)")
    ax.set_ylabel(INDEX_LABEL)
    ax.set_ylim(-0.052, -0.026)
    ax.invert_yaxis()
    panel_label(ax, "(b)", x=0.04, y=0.93)

    ax = axes[1, 0]
    centres = profiles["bump_centres_um"]
    shade_windows(ax)
    for role, colour, lw in (
        ("candidate", "#D55E00", 1.2),
        ("population", "0.25", 0.9),
        ("quiescent", "#0072B2", 0.9),
    ):
        key = f"e_plus_a_young__{role}"
        profile, error = profiles[f"{key}_bump_continuum"], profiles[f"{key}_bump_continuum_err"]
        ax.fill_between(centres, profile - error, profile + error, color=colour, alpha=0.2, lw=0)
        row = stacks.set_index("group").loc[key]
        ax.plot(
            centres,
            profile,
            color=colour,
            lw=lw,
            label=f"{ROLE_STYLES[role]} ({row.n_galaxies}): {row.stack_continuum_index:+.4f}",
        )
    ax.set_xlim(*FIT_RANGE_UM)
    ax.set_ylim(0.93, 1.08)
    ax.set_xlabel(REST_WAVELENGTH_LABEL)
    ax.set_ylabel(r"$F_\lambda / F_{\rm c}$, stacked")
    ax.legend(loc="lower center", fontsize=5.6, title="young E+A", title_fontsize=6, ncol=1)
    panel_label(ax, "(c)", x=0.9, y=0.93)

    ax = axes[1, 1]
    sed_centres = profiles["sed_centres_um"]
    for key, reference, colour, label in (
        ("e_plus_a_young", "population", "#D55E00", "young E+A / population controls"),
        ("e_plus_a_young", "quiescent", "#CC79A7", "young E+A / quiescent controls"),
        ("e_plus_a_old", "population", "#E69F00", "old E+A / population controls"),
        ("balmer_excess_all", "quiescent", "#0072B2", r"H$\delta_{\rm A}$ excess / quiescent controls"),
    ):
        ratio = profiles[f"{key}__candidate_sed"] / profiles[f"{key}__{reference}_sed"]
        ax.plot(sed_centres, ratio, color=colour, lw=0.9, label=label)
    ax.axhline(1, color=NEUTRAL_GREY, lw=0.5)
    for name, wave in FEATURES_UM.items():
        ax.axvline(wave, color="0.6", lw=0.4, ls=":")
        ax.text(wave, 1.31, name, fontsize=6, ha="center", va="top", rotation=90)
    ax.set_xscale("log")
    ax.set_xticks([0.8, 1, 1.5, 2, 3, 4])
    ax.set_xticklabels(["0.8", "1", "1.5", "2", "3", "4"])
    ax.set_xlim(0.72, 4.9)
    ax.set_ylim(0.62, 1.32)
    ax.set_xlabel(REST_WAVELENGTH_LABEL)
    ax.set_ylabel("stacked SED ratio")
    ax.legend(loc="lower left", fontsize=5.6)
    panel_label(ax, "(d)", x=0.9, y=0.06)
    fig.tight_layout(h_pad=0.6, w_pad=0.6)
    fig.savefig(FIGURE_DIR / "fig14_post_starburst_stacks.png")
    plt.close(fig)


def figure_controls(control_galaxies, control_summary, control_stacks, cells):
    fig, axes = plt.subplots(2, 2, figsize=(DOUBLE_COLUMN_IN, 5.6))
    ax = axes[0, 0]
    bins = np.linspace(-0.15, 0.15, 61)
    for column, label, colour, style in (
        ("d3_minus_d2_step", "measured", "0.1", "-"),
        ("null_step_draw", "Gaussian null", "#0072B2", "--"),
        ("empirical_null_step_draw", "empirical null", "#D55E00", ":"),
    ):
        values = control_galaxies[column].dropna()
        ax.hist(values, bins=bins, histtype="step", color=colour, ls=style, lw=1.0, label=label)
    step = control_summary["step"]
    ax.text(
        0.72,
        0.76,
        "robust $\\sigma$\nmeasured {:.4f}\nGaussian {:.4f}\nempirical {:.4f}".format(
            step["robust_sigma_measured"],
            step["robust_sigma_null_draws"],
            step["robust_sigma_empirical_null_draws"],
        ),
        transform=ax.transAxes,
        fontsize=6,
        va="top",
    )
    ax.set_yscale("log")
    ax.set_xlabel("D3 $-$ D2 step (fractional)")
    ax.set_ylabel("galaxies")
    ax.legend(loc="upper right", fontsize=6)
    panel_label(ax, "(a)", x=0.04, y=0.93)

    ax = axes[0, 1]
    trend = control_summary["residual_by_redshift"]
    by_z = control_summary["step_by_redshift"]
    centres = [float(k.strip("(]").split(",")[0]) + 0.0025 for k in by_z]
    ax.plot(centres, list(trend["hminus_bump_mag"].values()), "o-", color="0.1", ms=3.5, label="as measured")
    ax.plot(
        centres,
        list(trend["index_step_population"].values()),
        "s--",
        color="#D55E00",
        ms=3.5,
        label="median step of the redshift bin removed",
    )
    ax.axhline(0, color=NEUTRAL_GREY, lw=0.5)
    ax.set_xlabel("redshift")
    ax.set_ylabel(r"median index residual at fixed D$_n$4000 [mag]")
    twin = ax.twinx()
    twin.errorbar(
        centres,
        [v["median"] for v in by_z.values()],
        [v["err"] for v in by_z.values()],
        fmt="^",
        color="#009E73",
        ms=3.5,
        elinewidth=0.7,
        capsize=0,
    )
    twin.set_ylabel("median D3 $-$ D2 step", color="#009E73")
    twin.tick_params(axis="y", colors="#009E73")
    twin.set_ylim(-0.012, 0.012)
    ax.set_ylim(-0.006, 0.006)
    ax.legend(loc="lower left", fontsize=5.8)
    panel_label(ax, "(b)", x=0.9, y=0.93)

    ax = axes[1, 0]
    rows = control_stacks[control_stacks.group.str.contains("_row")].copy()
    for subset, colour, marker, label in (
        ("edgeon", "#D55E00", "v", r"$q < 0.4$"),
        ("middle", "#E69F00", "D", r"$0.4 \leq q < 0.5$"),
        ("faceon", "#0072B2", "o", r"$q \geq 0.5$"),
    ):
        chosen = rows[rows.subset == subset].sort_values("dn4000_bin")
        ax.errorbar(
            chosen.dn4000_median,
            chosen.stack_continuum_index,
            chosen.stack_continuum_index_err,
            fmt=marker + "-",
            color=colour,
            ms=3.5,
            lw=0.8,
            elinewidth=0.7,
            capsize=0,
            label=label,
        )
    ax.set_xlabel(DN4000_LABEL)
    ax.set_ylabel(INDEX_LABEL)
    ax.invert_yaxis()
    ax.legend(loc="lower right", fontsize=6, title="SDSS r-band axis ratio", title_fontsize=6)
    panel_label(ax, "(c)", x=0.04, y=0.93)

    ax = axes[1, 1]
    face = control_stacks[control_stacks.group.str.startswith("faceon_cell")].copy()
    face["cell"] = face.cell.astype(int)
    for h_bin in range(N_HDELTA_BINS):
        chosen = face[face.cell % N_HDELTA_BINS == h_bin].sort_values("cell")
        ax.errorbar(
            chosen.dn4000_median,
            chosen.stack_continuum_index,
            chosen.stack_continuum_index_err,
            fmt="o-",
            color=HDELTA_COLOURS[h_bin],
            ms=3,
            lw=0.8,
            elinewidth=0.6,
            capsize=0,
            label=f"H$\\delta_{{\\rm A}}$ fifth {h_bin + 1}",
        )
    all_rows = row_means(cells)
    ax.plot(all_rows.dn4000, all_rows["index"], "--", color="0.2", lw=1.0, label="all galaxies, row mean")
    ax.set_xlabel(DN4000_LABEL)
    ax.set_ylabel(INDEX_LABEL + r", $q \geq 0.5$")
    ax.set_ylim(-0.0308, -0.0455)
    ax.legend(loc="lower left", fontsize=5.6, ncol=2, handletextpad=0.2, columnspacing=0.5)
    panel_label(ax, "(d)", x=0.9, y=0.06)
    fig.tight_layout(h_pad=0.6, w_pad=0.6)
    fig.savefig(FIGURE_DIR / "fig15_inclination_and_detector_controls.png")
    plt.close(fig)


def model_curve(label: str, fit: dict, epoch: float, edges: np.ndarray) -> pd.Series:
    models = load_population(label, fit, epoch)
    grouped = models.groupby(pd.cut(models.d4000, edges), observed=True).bump
    medians = grouped.median()[grouped.size() >= 20]
    return pd.Series(medians.to_numpy(), index=[interval.mid for interval in medians.index])


def figure_models(model_cells, model_psb, ssp, summary, galaxies):
    fits = summary["ssp_conversion_fits"]
    edges = np.arange(1.30, 2.45, 0.05)
    fig, axes = plt.subplots(2, 2, figsize=(DOUBLE_COLUMN_IN, 5.8))
    ax = axes[0, 0]
    for label in ("off", "on"):
        curves = {epoch: model_curve(label, fits[label], epoch, edges) for epoch in (8.0, 10.0, 12.0)}
        joined = pd.concat(curves, axis=1).dropna()
        ax.fill_between(
            joined.index, joined.min(axis=1), joined.max(axis=1), color=MODEL_COLOURS[label], alpha=0.2, lw=0
        )
        ax.plot(
            curves[10.0].index,
            curves[10.0].to_numpy(),
            color=MODEL_COLOURS[label],
            lw=1.0,
            label=f"TP-AGB {label}, epochs $>$ 8/10/12 Gyr",
        )
        early = model_curve(label, fits[label], 1.0, edges)
        ax.plot(
            early.index,
            early.to_numpy(),
            color=MODEL_COLOURS[label],
            lw=0.8,
            ls=":",
            label=f"TP-AGB {label}, all epochs $>$ 1 Gyr",
        )
    for h_bin in range(N_HDELTA_BINS):
        chosen = model_cells[model_cells.hdelta_bin == h_bin]
        ax.errorbar(
            chosen.d4000_broad_median,
            chosen.covered_stack_index,
            chosen.covered_stack_index_err,
            fmt="o",
            color=HDELTA_COLOURS[h_bin],
            ms=2.8,
            elinewidth=0.6,
            capsize=0,
        )
    for name in ("e_plus_a_young", "e_plus_a_old"):
        row = model_psb.set_index("set").loc[name]
        label, colour, marker = PSB_STYLES[name]
        ax.errorbar(
            row.d4000_broad_median,
            row.stack_continuum_index,
            row.stack_continuum_index_err,
            fmt=marker,
            color=colour,
            mec="black",
            mew=0.5,
            ms=5,
            elinewidth=0.8,
            capsize=0,
            label=label,
        )
    ax.set_xlim(1.3, 2.35)
    ax.set_ylim(-0.075, 0.0)
    ax.invert_yaxis()
    ax.set_xlabel(BROAD_D4000_LABEL)
    ax.set_ylabel(INDEX_LABEL + " (stack system)")
    ax.legend(loc="upper right", fontsize=5.4, ncol=1, handletextpad=0.3)
    panel_label(ax, "(a)", x=0.9, y=0.06)

    ax = axes[0, 1]
    covered = model_cells.dropna(subset=["covered_minus_on"])
    for h_bin in range(N_HDELTA_BINS):
        chosen = covered[covered.hdelta_bin == h_bin]
        ax.errorbar(
            chosen.dn4000_median,
            chosen.covered_minus_on,
            chosen.covered_stack_index_err,
            fmt="o",
            color=HDELTA_COLOURS[h_bin],
            ms=3,
            elinewidth=0.6,
            capsize=0,
            label=f"H$\\delta_{{\\rm A}}$ fifth {h_bin + 1}",
        )
    ax.axhline(0, color=MODEL_COLOURS["on"], lw=0.8)
    ax.set_xlabel(DN4000_LABEL)
    ax.set_ylabel(f"stack $-$ TP-AGB on ($>${LATE_EPOCH_GYR:g} Gyr) [mag]")
    ax.legend(loc="upper right", fontsize=5.6, ncol=2, handletextpad=0.2, columnspacing=0.5)
    ax.set_ylim(-0.002, 0.014)
    panel_label(ax, "(b)", x=0.04, y=0.93)

    ax = axes[1, 0]
    density_contours(
        ax,
        galaxies.d4000_sub,
        galaxies.lick_hd_a_sub,
        (1.2, 2.5),
        (-5.5, 8.5),
        [0.68, 0.95],
        filled=True,
        colour="0.5",
    )
    for label in ("off", "on"):
        models = load_population(label, fits[label], LATE_EPOCH_GYR)
        density_contours(
            ax,
            models.d4000,
            models.hdelta_a,
            (1.2, 2.5),
            (-5.5, 8.5),
            [0.68, 0.95],
            filled=False,
            colour=MODEL_COLOURS[label],
        )
    ax.set_xlim(1.25, 2.4)
    ax.set_ylim(-5.5, 7.0)
    ax.set_xlabel(BROAD_D4000_LABEL)
    ax.set_ylabel(HDELTA_LABEL)
    ax.legend(
        handles=[
            Line2D([], [], color="0.6", lw=4, label="SDSS 48k"),
            Line2D([], [], color=MODEL_COLOURS["off"], label=f"TP-AGB off, $>${LATE_EPOCH_GYR:g} Gyr"),
            Line2D([], [], color=MODEL_COLOURS["on"], label=f"TP-AGB on, $>${LATE_EPOCH_GYR:g} Gyr"),
        ],
        loc="upper right",
        fontsize=6,
    )
    panel_label(ax, "(c)", x=0.04, y=0.06)

    ax = axes[1, 1]
    for label in ("off", "on"):
        chosen = ssp[ssp.tp_agb == label]
        shift = chosen.index_stack_r41 - chosen.index_r100
        ax.scatter(
            chosen.index_r100, shift, s=5, color=MODEL_COLOURS[label], lw=0, label=f"SSPs, TP-AGB {label}"
        )
        grid = np.linspace(chosen.index_r100.min(), chosen.index_r100.max(), 10)
        fit = fits[label]
        ax.plot(grid, fit["slope"] * grid + fit["intercept"], color=MODEL_COLOURS[label], lw=0.8)
    ax.axhline(0, color=NEUTRAL_GREY, lw=0.5)
    ax.set_xlabel(r"model index at $R$ = 100 [mag]")
    ax.set_ylabel(r"stack system ($R$ = 41) $-$ $R$ = 100 [mag]")
    ax.legend(loc="lower left", fontsize=6)
    panel_label(ax, "(d)", x=0.9, y=0.93)
    fig.tight_layout(h_pad=0.6, w_pad=0.6)
    fig.savefig(FIGURE_DIR / "fig16_stacks_against_late_models.png")
    plt.close(fig)


def figure_target(exposures, scatter, galaxy, star):
    fig, axes = plt.subplots(2, 2, figsize=(DOUBLE_COLUMN_IN, 5.4))
    ax = axes[0, 0]
    for detector, group in exposures.groupby("detector_id"):
        ax.plot(
            group.wv_um,
            group.aper_flux_uJy / 1e3,
            "o",
            ms=2.2,
            color=DETECTOR_COLOURS[int(detector)],
            label=f"D{int(detector)}",
        )
    z = galaxy.redshift
    for name, (low, high) in WINDOWS_UM.items():
        colour = "#D55E00" if name == "feature" else "#56B4E9"
        ax.axvspan(low * (1 + z), high * (1 + z), color=colour, alpha=0.15, lw=0)
    ax.set_xscale("log")
    ax.set_xticks([0.8, 1, 1.5, 2, 3, 4, 5])
    ax.set_xticklabels(["0.8", "1", "1.5", "2", "3", "4", "5"])
    ax.set_xlabel(WAVELENGTH_LABEL)
    ax.set_ylabel(r"aperture $F_\nu$ [mJy]")
    ax.set_ylim(0, 6.5)
    ax.legend(loc="upper right", fontsize=6, ncol=3, handletextpad=0.1, columnspacing=0.5)
    panel_label(ax, "(a)", x=0.04, y=0.93)

    ax = axes[0, 1]
    window = exposures.dropna(subset=["fit_residual"])
    shade_windows(ax)
    norm = window.flux_lambda[window.kept.astype(bool) & (window.detector_id == 3)].median()
    for detector, group in window.groupby("detector_id"):
        kept = group.kept.astype(bool)
        colour = DETECTOR_COLOURS[int(detector)]
        ax.plot(
            group.rest_um[kept],
            group.flux_lambda[kept] / norm,
            "o",
            ms=3,
            color=colour,
            label=f"D{int(detector)}",
        )
        ax.plot(group.rest_um[~kept], group.flux_lambda[~kept] / norm, "x", ms=3.5, color=colour)
    ax.set_xlim(*FIT_RANGE_UM)
    ax.set_ylim(0.3, 1.3)
    ax.set_xlabel(REST_WAVELENGTH_LABEL)
    ax.set_ylabel(r"$F_\lambda$ / median of D3")
    ax.text(
        0.03,
        0.06,
        f"index {galaxy.hminus_bump_mag:+.3f} $\\pm$ {galaxy.hminus_bump_err_mag:.3f} mag, "
        f"$s$ = {galaxy.significance:.1f}\ncrosses: rejected by the quadratic screen",
        transform=ax.transAxes,
        fontsize=6,
    )
    ax.legend(loc="upper right", fontsize=6)
    panel_label(ax, "(b)", x=0.04, y=0.93)

    ax = axes[1, 0]
    bins = np.logspace(np.log10(0.3), np.log10(10), 50)
    ax.hist(scatter.d2_over_d3.dropna(), bins=bins, histtype="step", color="0.2", label="all galaxies")
    strong = scatter[scatter.significance < -3]
    ax.hist(
        strong.d2_over_d3.dropna(),
        bins=bins,
        histtype="stepfilled",
        color="#0072B2",
        alpha=0.6,
        label=r"strong, $s<-3$",
    )
    target_ratio = float(scatter.loc[scatter.target == galaxy.target, "d2_over_d3"].iloc[0])
    ax.axvline(target_ratio, color="#D55E00", lw=1.0)
    ax.text(target_ratio * 0.93, 300, "45124", color="#D55E00", fontsize=6.5, ha="right", rotation=90)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("D2 / D3 exposure scatter")
    ax.set_ylabel("galaxies")
    ax.legend(loc="upper right", fontsize=6)
    panel_label(ax, "(c)", x=0.04, y=0.93)

    ax = axes[1, 1]
    image, _, source = optical_image(galaxy.ra_deg, galaxy.dec_deg, 60.0)
    if image is not None:
        finite = image[np.isfinite(image)]
        low, high = np.percentile(finite, [5, 99.7])
        ax.imshow(np.arcsinh((image - low) / (high - low) * 10), origin="lower", cmap="Greys")
        centre = (image.shape[1] / 2 - 0.5, image.shape[0] / 2 - 0.5)
        ax.add_patch(Circle(centre, 12.3 / 0.5, fill=False, color="#D55E00", lw=0.8))
        ax.add_patch(Circle(centre, 20.0 / 0.5, fill=False, color="#D55E00", lw=0.5, ls=":"))
    ax.set_xlabel(
        f"SDSS star {-star['wide_star_relative_mag']:.1f} mag brighter (z), "
        f"{star['wide_star_sep_arcsec']:.0f} arcsec away (saturated)\n"
        f"circles: 12.3 and 20 arcsec; {source}",
        fontsize=6.5,
    )
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title(
        f"target 45124, $z$ = {galaxy.redshift:.3f}, $q$ = {galaxy.axis_ratio_r:.2f}, "
        f"D$_n$4000 {galaxy.d4000_n_sub:.2f}, H$\\delta_{{\\rm A}}$ {galaxy.lick_hd_a_sub:.1f}",
        fontsize=6.5,
    )
    panel_label(ax, "(d)", x=0.04, y=0.93)
    fig.tight_layout(h_pad=0.6, w_pad=0.6)
    fig.savefig(FIGURE_DIR / "fig17_target_45124.png")
    plt.close(fig)


def main():
    galaxies = load_galaxies()
    galaxies = galaxies[~galaxies.in_magellanic.astype(bool)].reset_index(drop=True)
    cells = pd.read_parquet(OUT_DIR / "stack_cells.parquet")

    stacks = pd.read_parquet(OUT_DIR / "psb_stacks.parquet")
    profiles = dict(np.load(OUT_DIR / "psb_profiles.npz"))
    members = pd.read_parquet(OUT_DIR / "psb_galaxies.parquet")
    figure_post_starbursts(stacks, profiles, members, galaxies, cells)

    control_galaxies = pd.read_parquet(OUT_DIR / "control_galaxies.parquet")
    with open(OUT_DIR / "control_summary.json") as handle:
        control_summary = json.load(handle)
    control_stacks = pd.read_parquet(OUT_DIR / "control_stacks.parquet")
    figure_controls(control_galaxies, control_summary, control_stacks, cells)

    with open(OUT_DIR / "model_stack_summary.json") as handle:
        model_summary = json.load(handle)
    figure_models(
        pd.read_parquet(OUT_DIR / "model_stack_cells.parquet"),
        pd.read_parquet(OUT_DIR / "model_stack_psb.parquet"),
        pd.read_parquet(OUT_DIR / "model_stack_ssp.parquet"),
        model_summary,
        galaxies,
    )

    with_significance, _ = significance(galaxies)
    shapes = pd.read_parquet(OUT_DIR / "outlier_population.parquet", columns=["target", "axis_ratio_r"])
    target = with_significance.merge(shapes, on="target").query("target == 45124").iloc[0]
    figure_target(
        pd.read_parquet(OUT_DIR / "target_45124_exposures.parquet"),
        pd.read_parquet(OUT_DIR / "detector_scatter.parquet"),
        target,
        json.load(open(OUT_DIR / "detector_scatter_summary.json"))["wide_stars"]["target"],
    )
    print("figures 14-17 written to", FIGURE_DIR)


if __name__ == "__main__":
    main()
