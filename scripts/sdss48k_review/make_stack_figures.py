"""Figures 9-13 of the SDSS 48k review: stacks across the Dn4000-HdeltaA plane and the strong-bump outliers.
Run `stack_sed_and_bump.py` and `investigate_bump_outliers.py` first.
usage: uv run python scripts/sdss48k_review/make_stack_figures.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import Normalize
from matplotlib.patches import Circle, Rectangle
from scipy.stats import norm

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_model_comparability import kernel_table, model_spectra  # noqa: E402
from make_hminus_figures import FIGURE_DIR, HDELTA_LABEL, density_contours  # noqa: E402
from measure_hminus_bump import FIT_RANGE_UM, OUT_DIR, WINDOWS_UM  # noqa: E402
from stack_sed_and_bump import N_DN4000_BINS, N_HDELTA_BINS, load_galaxies, profile_index  # noqa: E402

from spherex_psb.figures.galaxy_figures import optical_image  # noqa: E402
from spherex_psb.figures.style import (  # noqa: E402
    DETECTOR_COLOURS,
    DOUBLE_COLUMN_IN,
    NEUTRAL_GREY,
    REST_WAVELENGTH_LABEL,
    apply_style,
    panel_label,
)

apply_style()
DN4000_LABEL = r"D$_n$4000"
INDEX_LABEL = r"stacked H$^{-}$ bump [mag]"
HDELTA_COLOURS = plt.get_cmap("viridis")(np.linspace(0.0, 0.9, N_HDELTA_BINS))
MODEL_COLOURS = {"off": "#0072B2", "on": "#D55E00"}
SET_STYLES = {
    "strong_apparent": ("apparent strong", "#D55E00"),
    "weak_apparent": ("apparent weak", "#E69F00"),
    "strong_significant": (r"strong, $s<-3$", "#0072B2"),
    "weak_significant": (r"weak, $s>+3$", "#56B4E9"),
    "control": ("controls", "0.3"),
}
FEATURES_UM = {r"Pa$\alpha$": 1.875, "CO": 2.29, "PAH": 3.29, r"Br$\alpha$": 4.05}


def load():
    cells = pd.read_parquet(OUT_DIR / "stack_cells.parquet")
    membership = pd.read_parquet(OUT_DIR / "stack_membership.parquet")
    profiles = dict(np.load(OUT_DIR / "stack_profiles.npz"))
    galaxies = load_galaxies().merge(membership[["target", "cell"]], on="target", how="inner")
    return cells, galaxies, profiles


def cell_rectangles(galaxies: pd.DataFrame) -> dict[int, tuple[float, float, float, float]]:
    """Edges of each cell: Dn4000 quantile edges of its strip, HdeltaA quantile edges within the strip."""
    rectangles = {}
    strips = galaxies.groupby("cell").d4000_n_sub.agg(["min", "max"])
    heights = galaxies.groupby("cell").lick_hd_a_sub.agg(["min", "max"])
    for cell in strips.index:
        d_bin, h_bin = divmod(int(cell), N_HDELTA_BINS)
        x0 = strips.loc[[d_bin * N_HDELTA_BINS + k for k in range(N_HDELTA_BINS)], "min"].min()
        x1 = strips.loc[[d_bin * N_HDELTA_BINS + k for k in range(N_HDELTA_BINS)], "max"].max()
        rectangles[int(cell)] = (x0, x1, heights.loc[cell, "min"], heights.loc[cell, "max"])
    return rectangles


def plane_map(axis, galaxies, cells, rectangles, values, cmap, label, vmin, vmax):
    density_contours(
        axis,
        galaxies.d4000_n_sub,
        galaxies.lick_hd_a_sub,
        (1.0, 2.35),
        (-5.5, 8.5),
        [0.68, 0.95],
        filled=False,
        colour="0.2",
        zorder=3,
    )
    normaliser = Normalize(vmin, vmax)
    colours = plt.get_cmap(cmap)
    for cell, value in zip(cells.cell, values, strict=True):
        x0, x1, y0, y1 = rectangles[cell]
        axis.add_patch(
            Rectangle(
                (x0, y0), x1 - x0, y1 - y0, facecolor=colours(normaliser(value)), edgecolor="white", lw=0.4
            )
        )
    axis.set_xlim(1.05, 2.3)
    axis.set_ylim(-5.0, 8.6)
    axis.set_xlabel(DN4000_LABEL)
    axis.set_ylabel(HDELTA_LABEL)
    mappable = plt.cm.ScalarMappable(norm=normaliser, cmap=cmap)
    bar = plt.colorbar(mappable, ax=axis, pad=0.02, fraction=0.05)
    bar.set_label(label)
    return bar


def figure_plane(cells, galaxies):
    per_cell = cells[cells.cell >= 0].reset_index(drop=True)
    rectangles = cell_rectangles(galaxies)
    fig, axes = plt.subplots(2, 2, figsize=(DOUBLE_COLUMN_IN, 5.6))
    ax = axes[0, 0]
    plane_map(
        ax,
        galaxies,
        per_cell,
        rectangles,
        per_cell.log_ssfr_median,
        "RdYlBu",
        r"median log sSFR [yr$^{-1}$]",
        -12.4,
        -9.8,
    )
    for text, x, y in (("star forming", 1.09, 7.75), ("post-starburst", 1.45, 6.6), ("quiescent", 1.86, 2.6)):
        ax.text(x, y, text, fontsize=7.5)
    panel_label(ax, "(a)", x=0.88)
    ax = axes[0, 1]
    bar = plane_map(
        ax,
        galaxies,
        per_cell,
        rectangles,
        per_cell.stack_continuum_index,
        "magma",
        INDEX_LABEL,
        -0.045,
        -0.035,
    )
    bar.ax.invert_yaxis()
    panel_label(ax, "(b)", x=0.88)

    ax = axes[1, 0]
    for h_bin in range(N_HDELTA_BINS):
        rows = per_cell[per_cell.hdelta_bin == h_bin]
        ax.errorbar(
            rows.dn4000_median + 0.006 * (h_bin - 2),
            rows.stack_continuum_index,
            yerr=rows.stack_continuum_index_err,
            color=HDELTA_COLOURS[h_bin],
            marker="o",
            ms=3,
            lw=0.9,
            capsize=0,
            label=["lowest", "2nd", "3rd", "4th", "highest"][h_bin] + r" H$\delta_{\rm A}$ fifth",
        )
    whole = cells[cells.group == "all"].iloc[0]
    ax.axhline(whole.stack_continuum_index, color=NEUTRAL_GREY, ls=":", lw=0.8)
    ax.set_xlabel(DN4000_LABEL + " (cell median)")
    ax.set_ylabel(INDEX_LABEL)
    ax.set_ylim(-0.0335, -0.0475)
    ax.legend(loc="lower right", fontsize=6.5, ncol=1)
    panel_label(ax, "(c)")

    ax = axes[1, 1]
    reference = per_cell.stack_continuum_index
    ax.errorbar(
        reference,
        per_cell.stack_sed_index - reference,
        yerr=per_cell.stack_sed_index_err,
        fmt="o",
        ms=3,
        color="#0072B2",
        lw=0.7,
        label="stacked whole SED (normalised at 1.17 $\\mu$m)",
    )
    ax.errorbar(
        reference + 0.0002,
        per_cell.individual_index_mean - reference,
        yerr=per_cell.individual_index_mean_err,
        fmt="s",
        ms=3,
        mfc="none",
        color="#D55E00",
        lw=0.7,
        label="mean of individual indices",
    )
    ax.axhline(0, color=NEUTRAL_GREY, lw=0.6)
    ax.set_xlabel("stacked continuum-normalised profile [mag]")
    ax.set_ylabel("other estimate minus it [mag]")
    ax.set_ylim(-0.006, 0.006)
    ax.legend(loc="upper left", fontsize=6.5)
    panel_label(ax, "(d)", x=0.88, y=0.12)
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "fig9_stacks_on_dn4000_hdelta_plane.png")
    plt.close(fig)


def dn4000_title(cells, d_bin):
    rows = cells[cells.dn4000_bin == d_bin]
    return rf"D$_n$4000 {rows.dn4000_range.str[0].min():.2f}--{rows.dn4000_range.str[1].max():.2f}"


def figure_seds(cells, profiles):
    centres = profiles["sed_centres_um"]
    whole, whole_err = profiles["all_sed"], profiles["all_sed_err"]
    fig, axes = plt.subplots(3, 3, figsize=(DOUBLE_COLUMN_IN, 6.4), sharex=True)
    ax = axes[0, 0]
    ax.fill_between(centres, whole - whole_err, whole + whole_err, color="k", lw=0)
    ax.plot(centres, whole, color="k", lw=0.8)
    for low, high in [WINDOWS_UM["blue"], WINDOWS_UM["red"]]:
        ax.axvspan(low, high, color="#56B4E9", alpha=0.3, lw=0)
    ax.axvspan(*WINDOWS_UM["feature"], color="#D55E00", alpha=0.2, lw=0)
    ax.set_ylabel(r"$F_\lambda / F_\lambda(1.17\,\mu{\rm m})$")
    ax.set_yscale("log")
    ax.set_ylim(0.03, 1.6)
    panel_label(ax, "(a) all, 46,039", x=0.45)
    per_cell = cells[cells.cell >= 0]
    for d_bin in range(N_DN4000_BINS):
        ax = axes.flat[d_bin + 1]
        for h_bin in range(N_HDELTA_BINS):
            key = f"cell{d_bin * N_HDELTA_BINS + h_bin:02d}"
            ratio = profiles[f"{key}_sed"] / whole
            ax.plot(centres, ratio, color=HDELTA_COLOURS[h_bin], lw=0.7)
        ax.axhline(1, color=NEUTRAL_GREY, lw=0.5)
        ax.set_ylim(0.76, 1.65)
        ax.set_yscale("log")
        ax.set_yticks([0.8, 1.0, 1.25, 1.6])
        ax.set_yticklabels(["0.8", "1", "1.25", "1.6"])
        ax.minorticks_off()
        panel_label(ax, f"({'bcdefghi'[d_bin]}) " + dn4000_title(per_cell, d_bin), y=0.95)
        if d_bin % 3 == 2:
            ax.set_ylabel("cell / all")
    for name, wave in FEATURES_UM.items():
        for ax in axes.flat[1:]:
            ax.axvline(wave, color=NEUTRAL_GREY, lw=0.4, ls=":")
        axes.flat[1].text(wave, 0.78, name, fontsize=6, ha="right", va="bottom", rotation=90)
    for ax in axes.flat:
        ax.set_xscale("log")
        ax.set_xlim(0.72, 4.85)
        ax.set_xticks([0.8, 1, 1.5, 2, 3, 4])
        ax.set_xticklabels(["0.8", "1", "1.5", "2", "3", "4"])
    for ax in axes[2]:
        ax.set_xlabel(REST_WAVELENGTH_LABEL)
    handles = [plt.Line2D([], [], color=HDELTA_COLOURS[k], lw=1) for k in range(N_HDELTA_BINS)]
    labels = [r"lowest H$\delta_{\rm A}$ fifth", "2nd", "3rd", "4th", "highest"]
    axes[0, 0].legend(handles, labels, loc="lower left", fontsize=6, ncol=1)
    fig.tight_layout(h_pad=0.4, w_pad=0.4)
    fig.savefig(FIGURE_DIR / "fig10_stacked_seds.png")
    plt.close(fig)


def model_profiles(centres: np.ndarray, age_gyr: float = 10.0) -> dict[str, np.ndarray]:
    """Solar SSP at R = 41, divided by its pseudo-continuum, on the stack grid (as the data profile)."""
    out = {}
    for name, (wave_a, flux_nu, _) in model_spectra().items():
        label, age = name.split("_")
        if age != f"{age_gyr:g}gyr":
            continue
        log_wave, table = kernel_table(wave_a, flux_nu, np.array([41.0]))
        wave_um = log_wave / 1e4
        flux_lambda = np.interp(centres, wave_um, table[0] / wave_um**2)
        member = {key: (centres >= lo) & (centres <= hi) for key, (lo, hi) in WINDOWS_UM.items()}
        blue, red = flux_lambda[member["blue"]].mean(), flux_lambda[member["red"]].mean()
        blue_mid, red_mid = (0.5 * sum(WINDOWS_UM[key]) for key in ("blue", "red"))
        fraction = (centres - blue_mid) / (red_mid - blue_mid)
        out[label] = flux_lambda / (blue * (1 - fraction) + red * fraction)
    return out


def shade_windows(ax):
    for low, high in [WINDOWS_UM["blue"], WINDOWS_UM["red"]]:
        ax.axvspan(low, high, color="#56B4E9", alpha=0.25, lw=0)
    ax.axvspan(*WINDOWS_UM["feature"], color="#D55E00", alpha=0.12, lw=0)
    ax.axhline(1, color=NEUTRAL_GREY, lw=0.5)


def figure_bump_profiles(cells, profiles):
    centres = profiles["bump_centres_um"]
    models = model_profiles(centres)
    fig, axes = plt.subplots(3, 3, figsize=(DOUBLE_COLUMN_IN, 6.2), sharex=True, sharey=True)
    ax = axes[0, 0]
    shade_windows(ax)
    whole, whole_err = profiles["all_bump_continuum"], profiles["all_bump_continuum_err"]
    ax.fill_between(centres, whole - whole_err, whole + whole_err, color="0.6", lw=0)
    ax.plot(centres, whole, color="k", lw=0.9, label="all galaxies")
    for k, style in zip((1, 3), ("-.", ":"), strict=True):
        rows = cells[cells.group == f"redshift{k}"].iloc[0]
        ax.plot(
            centres,
            profiles[f"redshift{k}_bump_continuum"],
            color="0.35",
            lw=0.7,
            ls=style,
            label=f"z {['lowest', '', 'highest'][k - 1]} third (median {rows.redshift_median:.3f})",
        )
    for label, profile in models.items():
        index = float(profile_index(centres, profile))
        ax.plot(
            centres,
            profile,
            color=MODEL_COLOURS[label],
            ls="--",
            lw=0.9,
            label=f"10 Gyr SSP, TP-AGB {label} ({index:+.3f})",
        )
    ax.legend(loc="lower center", fontsize=5.5, handlelength=1.6)
    panel_label(ax, "(a)")
    per_cell = cells[cells.cell >= 0]
    for d_bin in range(N_DN4000_BINS):
        ax = axes.flat[d_bin + 1]
        shade_windows(ax)
        for h_bin in range(N_HDELTA_BINS):
            key = f"cell{d_bin * N_HDELTA_BINS + h_bin:02d}"
            ax.plot(centres, profiles[f"{key}_bump_continuum"], color=HDELTA_COLOURS[h_bin], lw=0.7)
        panel_label(ax, f"({'bcdefghi'[d_bin]}) " + dn4000_title(per_cell, d_bin))
    for ax in axes.flat:
        ax.set_xlim(*FIT_RANGE_UM)
        ax.set_ylim(0.935, 1.065)
    for ax in axes[:, 0]:
        ax.set_ylabel(r"$F_\lambda / F_{\rm c}$")
    for ax in axes[2]:
        ax.set_xlabel(REST_WAVELENGTH_LABEL)
    fig.tight_layout(h_pad=0.3, w_pad=0.3)
    fig.savefig(FIGURE_DIR / "fig11_stacked_bump_profiles.png")
    plt.close(fig)


def stacked_ratio(exposures, targets, column, edges):
    rows = exposures[exposures.target.isin(targets)]
    centres = 0.5 * (edges[1:] + edges[:-1])
    bins = np.digitize(rows[column], edges) - 1
    per_galaxy = rows.assign(bin=bins).groupby(["target", "bin"]).ratio_to_continuum.mean().unstack()
    per_galaxy = per_galaxy.reindex(columns=range(len(centres)))
    mean = per_galaxy.mean().to_numpy()
    error = (per_galaxy.std() / np.sqrt(per_galaxy.notna().sum())).to_numpy()
    return centres, mean, error


def figure_outliers(galaxies_all, outliers, exposures, shape_dependence):
    fig, axes = plt.subplots(2, 3, figsize=(DOUBLE_COLUMN_IN, 4.9))
    ax = axes[0, 0]
    edges = np.arange(-7, 7.01, 0.25)
    ax.hist(
        galaxies_all.significance, bins=edges, histtype="step", color="k", lw=0.9, label="46,504 galaxies"
    )
    grid = np.linspace(-7, 7, 400)
    ax.plot(
        grid,
        len(galaxies_all) * 0.25 * norm.pdf(grid),
        color="#D55E00",
        lw=0.8,
        ls="--",
        label="unit Gaussian",
    )
    ax.set_yscale("log")
    ax.set_ylim(0.5, 2e4)
    ax.axvline(-3, color=NEUTRAL_GREY, lw=0.5, ls=":")
    ax.axvline(3, color=NEUTRAL_GREY, lw=0.5, ls=":")
    ax.set_xlabel(r"$s$ = residual / $\sqrt{\sigma^2 + \sigma_{\rm int}^2}$")
    ax.set_ylabel("galaxies per 0.25")
    ax.legend(loc="upper left", fontsize=5.5)
    ax.text(0.03, 0.72, r"$\leftarrow$ stronger bump", transform=ax.transAxes, fontsize=5.5)
    panel_label(ax, "(a)", x=0.84)

    ax = axes[0, 1]
    ax.hexbin(
        galaxies_all.hminus_bump_err_mag,
        galaxies_all.index_residual,
        gridsize=70,
        bins="log",
        cmap="Greys",
        extent=(0, 0.12, -0.25, 0.25),
        mincnt=1,
        linewidths=0,
    )
    error_grid = np.linspace(0, 0.12, 100)
    for sign in (-1, 1):
        ax.plot(error_grid, sign * 3 * np.hypot(error_grid, 0.0095), color="#0072B2", lw=0.8)
        ax.axhline(sign * 0.06, color="#D55E00", lw=0.8, ls="--")
    ax.set_xlim(0, 0.12)
    ax.set_ylim(0.25, -0.25)
    ax.set_xlabel("index error [mag]")
    ax.set_ylabel(r"residual from D$_n$4000 median [mag]")
    ax.text(0.115, -0.225, r"$|{\rm residual}| > 0.06$", color="#D55E00", fontsize=5.5, ha="right")
    ax.text(0.115, -0.19, r"$|s| > 3$", color="#0072B2", fontsize=5.5, ha="right")
    panel_label(ax, "(b)", x=0.05, y=0.1)

    shape = shape_dependence["axis_ratio_r"]
    centres_q = np.array([0.15, 0.35, 0.45, 0.55, 0.65, 0.75, 0.85, 0.95])
    ax = axes[0, 2]
    ax.errorbar(
        centres_q,
        [v["residual_median"] for v in shape.values()],
        yerr=[v["residual_median_err"] for v in shape.values()],
        fmt="o-",
        ms=3,
        color="k",
        lw=0.8,
    )
    ax.axhline(0, color=NEUTRAL_GREY, lw=0.5)
    ax.invert_yaxis()
    ax.set_xlabel("SDSS $r$ axis ratio")
    ax.set_ylabel("median residual [mag]")
    panel_label(ax, "(c)", x=0.84)

    ax = axes[1, 2]
    for key, (label, colour) in (
        ("fraction_strong_significant", SET_STYLES["strong_significant"]),
        ("fraction_weak_significant", SET_STYLES["weak_significant"]),
    ):
        ax.plot(
            centres_q, [100 * v[key] for v in shape.values()], "o-", ms=3, color=colour, lw=0.8, label=label
        )
    ax.axhline(100 * norm.sf(3), color=NEUTRAL_GREY, lw=0.6, ls="--", label="Gaussian")
    ax.set_xlabel("SDSS $r$ axis ratio")
    ax.set_ylabel(r"galaxies with $|s|>3$ [\%]")
    ax.legend(loc="upper right", fontsize=5.5)
    panel_label(ax, "(f)")

    ax = axes[1, 0]
    tests = {
        "bright star": outliers.brightest_star_relative_mag < 0,
        "neighbours $>10\\%$": (
            outliers.neighbour_flux_ratio_annulus + outliers.neighbour_flux_ratio_aperture
        )
        > 0.1,
        "scatter $>6\\%$": outliers.exposure_scatter > 0.06,
        "visit removed": outliers.significance_without_worst_visit.abs() < 2,
        "D3$-$D2 $>+5\\%$": outliers.d3_minus_d2_step > 0.05,
        "D3$-$D2 $<-5\\%$": outliers.d3_minus_d2_step < -0.05,
        "$q < 0.3$": outliers.axis_ratio_r < 0.3,
    }
    width = 0.17
    for k, (name, (label, colour)) in enumerate(SET_STYLES.items()):
        members = outliers[name]
        rates = [float(test[members].mean()) for test in tests.values()]
        if name == "control":
            rates[3] = np.nan
        ax.bar(np.arange(len(tests)) + (k - 2) * width, rates, width, color=colour, label=label)
    ax.set_xticks(np.arange(len(tests)))
    ax.set_xticklabels(list(tests), fontsize=5.5, rotation=40, ha="right", rotation_mode="anchor")
    ax.minorticks_off()
    ax.set_ylabel("fraction of the set")
    ax.set_ylim(0, 1.15)
    ax.legend(loc="upper center", fontsize=5, ncol=2, columnspacing=0.6, handlelength=1.2)
    panel_label(ax, "(d)", x=0.86, y=0.75)

    ax = axes[1, 1]
    rest_edges = np.arange(1.44, 1.8401, 0.01)
    shade_windows(ax)
    for name in ("strong_significant", "weak_significant", "control"):
        label, colour = SET_STYLES[name]
        centres, mean, error = stacked_ratio(
            exposures, set(outliers.target[outliers[name]]), "rest_um", rest_edges
        )
        ax.fill_between(centres, mean - error, mean + error, color=colour, alpha=0.25, lw=0)
        ax.plot(centres, mean, color=colour, lw=0.9, label=label)
    strong = set(outliers.target[outliers.strong_significant])
    median_z = outliers.loc[outliers.strong_significant, "redshift"].median()
    centres, mean, _ = stacked_ratio(exposures, strong, "observed_um", rest_edges * (1 + median_z))
    ax.plot(centres / (1 + median_z), mean, color="#0072B2", lw=0.8, ls=":", label="strong, observed")
    ax.set_xlim(*FIT_RANGE_UM)
    ax.set_ylim(0.86, 1.17)
    ax.set_xlabel(REST_WAVELENGTH_LABEL)
    ax.set_ylabel(r"$F_\lambda / F_{\rm c}$")
    ax.legend(loc="lower center", fontsize=5, ncol=2, columnspacing=0.6, handlelength=1.2)
    panel_label(ax, "(e)")
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "fig12_bump_outliers.png")
    plt.close(fig)


def gallery_caption(galaxy) -> str:
    index = f"{galaxy.hminus_bump_mag:+.3f} $\\pm$ {galaxy.hminus_bump_err_mag:.3f}"
    index += f", $s$ = {galaxy.significance:.1f}"
    optical = f"D$_n$4000 {galaxy.d4000_n_sub:.2f}, H$\\delta_{{\\rm A}}$ {galaxy.lick_hd_a_sub:.1f}"
    return f"{index}\n{optical}, $q$ {galaxy.axis_ratio_r:.2f}, $z$ {galaxy.redshift:.3f}"


def figure_gallery(outliers, exposures):
    significant = outliers[outliers.strong_significant].sort_values("significance").head(6)
    apparent = outliers[outliers.strong_apparent & (outliers.significance > -2)]
    apparent = apparent.sort_values("brightest_star_relative_mag").head(3)
    chosen = pd.concat([significant, apparent])
    fig, axes = plt.subplots(3, 3, figsize=(DOUBLE_COLUMN_IN, 6.6), sharex=True)
    for ax, (_, galaxy) in zip(axes.flat, chosen.iterrows(), strict=True):
        rows = exposures[exposures.target == galaxy.target]
        shade_windows(ax)
        for detector, group in rows.groupby("detector_id"):
            ax.plot(
                group.rest_um,
                group.ratio_to_continuum,
                "o",
                ms=2.5,
                color=DETECTOR_COLOURS[int(detector)],
                label=f"D{int(detector)}",
            )
        ax.set_ylim(0.75, 1.4)
        ax.text(
            0.03,
            0.95,
            gallery_caption(galaxy),
            transform=ax.transAxes,
            fontsize=5.3,
            va="top",
        )
        image, wcs, _ = optical_image(galaxy.ra_deg, galaxy.dec_deg, 60.0)
        if image is not None:
            inset = ax.inset_axes([0.62, 0.05, 0.36, 0.36])
            finite = image[np.isfinite(image)]
            low, high = np.percentile(finite, [5, 99.7])
            inset.imshow(np.arcsinh((image - low) / (high - low) * 10), origin="lower", cmap="Greys")
            centre = (image.shape[1] / 2 - 0.5, image.shape[0] / 2 - 0.5)
            inset.add_patch(Circle(centre, 12.3 / 0.5, fill=False, color="#D55E00", lw=0.6))
            inset.add_patch(Circle(centre, 20.0 / 0.5, fill=False, color="#D55E00", lw=0.4, ls=":"))
            inset.set_xticks([])
            inset.set_yticks([])
    axes[0, 0].legend(loc="lower left", fontsize=5.5, ncol=2, handletextpad=0.1, columnspacing=0.4)
    for ax in axes[:, 0]:
        ax.set_ylabel(r"$F_\lambda / F_{\rm c}$")
    for ax in axes[2]:
        ax.set_xlabel(REST_WAVELENGTH_LABEL)
        ax.set_xlim(*FIT_RANGE_UM)
    fig.tight_layout(h_pad=0.3, w_pad=0.3)
    fig.savefig(FIGURE_DIR / "fig13_bump_outlier_gallery.png")
    plt.close(fig)


def main():
    cells, galaxies, profiles = load()
    figure_plane(cells, galaxies)
    figure_seds(cells, profiles)
    figure_bump_profiles(cells, profiles)
    from investigate_bump_outliers import significance

    galaxies_all = load_galaxies()
    galaxies_all, _ = significance(galaxies_all[~galaxies_all.in_magellanic.astype(bool)])
    outliers = pd.read_parquet(OUT_DIR / "outlier_galaxies.parquet")
    exposures = pd.read_parquet(OUT_DIR / "outlier_exposures.parquet")
    with open(OUT_DIR / "outlier_summary.json") as handle:
        shape_dependence = json.load(handle)["shape_dependence"]
    figure_outliers(galaxies_all, outliers, exposures, shape_dependence)
    figure_gallery(outliers, exposures)


if __name__ == "__main__":
    main()
