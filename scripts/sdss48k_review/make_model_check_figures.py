"""Figures 7-8 of the SDSS 48k review: whether the H-bump paper's model loci can be compared with the data
(optical resolution, SPHEREx sampling, star-formation histories), and the comparison restricted to model
epochs a z = 0.03-0.06 galaxy can have. Run `measure_hminus_bump.py` and `check_model_comparability.py` first.
usage: uv run python scripts/sdss48k_review/make_model_check_figures.py
"""

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from astropy.io import fits
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_hminus_figures import (  # noqa: E402
    BUMP_LABEL,
    BUMP_RANGE,
    FIGURE_DIR,
    HDELTA_LABEL,
    MODEL_COLOURS,
    MODEL_ROOT,
    MODELS,
    RESULT_DIR,
    density_contours,
    running_median,
    typical_error,
)

from spherex_psb.figures.style import DOUBLE_COLUMN_IN, panel_label  # noqa: E402

LATE_EPOCH_GYR = 10.0
BIAS_TEMPLATES = {"TP-AGB off": "bias_off_5gyr", "TP-AGB on": "bias_on_5gyr"}
DN4000_EDGES = np.array([1.1, 1.3, 1.5, 1.7, 1.9, 2.1])
REDSHIFT_EDGES = np.linspace(0.03, 0.06, 7)


def load():
    data = pd.read_parquet(RESULT_DIR / "hminus_bump_indices.parquet")
    data = data[np.isfinite(data.hminus_bump_mag)]
    data = data.merge(
        pd.read_parquet(RESULT_DIR / "model_check_sampling_bias.parquet").drop(columns="redshift")
    )
    with fits.open("/Users/shuang/data/mpa/galSpecExtra-dr8.fits", memmap=True) as hdul:
        raw = hdul[1].data
        extra = pd.DataFrame(
            {
                "specobjid": pd.to_numeric(
                    pd.Series(raw["SPECOBJID"]).astype(str).str.strip(), errors="coerce"
                ),
                "log_ssfr": np.asarray(raw["SPECSFR_TOT_P50"]).astype(np.float64),
            }
        ).dropna(subset=["specobjid"])
    extra = extra.astype({"specobjid": np.int64}).drop_duplicates("specobjid")
    data = data.merge(extra, on="specobjid", how="left")
    data.loc[data.log_ssfr < -50, "log_ssfr"] = np.nan
    return data


def load_model(name, epoch_min):
    directory, key = MODELS[name]
    with np.load(f"{MODEL_ROOT}/{directory}/indices.npz") as model:
        keep = model["epoch_gyr"] >= epoch_min
        return {
            "d4000": model[f"d4000_{key}"][keep],
            "hdelta_a": model[f"hdelta_a_{key}"][keep],
            "bump": model[f"h_minus_bump_r100_{key}"][keep],
            "log_ssfr": np.log10(np.clip(model["ssfr_0_100_myr"][keep], 1e-30, None)) - 9.0,
        }


def residual_against_dn4000(data, values):
    """Index minus the median of its Dn4000 bin, to show the redshift dependence at fixed Dn4000."""
    bins = np.digitize(data.dn4000_emission_subtracted, DN4000_EDGES)
    medians = pd.Series(values).groupby(bins).transform("median").to_numpy()
    inside = (bins > 0) & (bins < len(DN4000_EDGES))
    return np.where(inside, values - medians, np.nan)


def binned(x, y, edges):
    centres, medians, errors = [], [], []
    for low, high in zip(edges[:-1], edges[1:], strict=True):
        values = y[(x >= low) & (x < high) & np.isfinite(y)]
        centres.append(0.5 * (low + high))
        medians.append(np.median(values))
        errors.append(1.2533 * 1.4826 * np.median(np.abs(values - np.median(values))) / np.sqrt(len(values)))
    return np.array(centres), np.array(medians), np.array(errors)


def figure_checks(data, summary):
    fig, axes = plt.subplots(
        2, 2, figsize=(DOUBLE_COLUMN_IN, 5.2), gridspec_kw={"hspace": 0.42, "wspace": 0.28}
    )

    axis = axes[0, 0]
    optical = pd.read_parquet(RESULT_DIR / "model_check_optical_resolution.parquet")
    sigma_values = np.sort(optical.total_sigma_km_s.unique())
    ages = np.sort(optical.age_gyr.unique())
    shades = plt.cm.viridis(np.linspace(0.1, 0.85, 4))
    for shade, target_age in zip(shades, (1.0, 2.0, 4.0, 8.0), strict=True):
        age = ages[np.argmin(np.abs(ages - target_age))]
        rows = optical[(optical.age_gyr == age)].groupby("total_sigma_km_s").hdelta_a_minus_sigma300.median()
        axis.plot(
            rows.index, rows.to_numpy(), color=shade, lw=1.1, marker="o", ms=2.5, label=f"{target_age:g} Gyr"
        )
    lower, upper = (
        summary["data_v_disp_percentiles_5_50_95"][0],
        summary["data_v_disp_percentiles_5_50_95"][2],
    )
    axis.axvspan(lower, upper, color="0.88", zorder=0)
    axis.axhline(0, color="0.5", lw=0.6)
    axis.text(
        0.5 * (lower + upper), -0.52, r"sample $\sigma_\star$" + "\n" + r"5--95\%", ha="center", fontsize=6.5
    )
    axis.set_xlim(sigma_values[0] - 10, 310)
    axis.set_ylim(-0.6, 0.1)
    axis.set_xlabel(r"total broadening $\sigma$ [km\,s$^{-1}$]")
    axis.set_ylabel(r"H$\delta_{\rm A}(\sigma) - $H$\delta_{\rm A}(300)$ [\AA]")
    axis.legend(title="SSP age, solar", loc="lower right", fontsize=6.5, title_fontsize=6.5, frameon=False)
    panel_label(axis, "(a)")

    axis = axes[0, 1]
    bins = np.linspace(-0.03, 0.035, 66)
    for name, column in BIAS_TEMPLATES.items():
        axis.hist(data[column], bins=bins, histtype="step", color=MODEL_COLOURS[name], lw=1.1, label=name)
        resolution_only = summary["resolution_only_r41_minus_r100_mag"][column.replace("bias_", "")]
        axis.axvline(resolution_only, color=MODEL_COLOURS[name], lw=0.8, ls=":")
    axis.axvline(0, color="0.5", lw=0.6)
    axis.set_xlabel(r"sampled index $-$ R\,=\,100 index [mag]")
    axis.set_ylabel("galaxies")
    axis.legend(title="5 Gyr SSP, solar", loc="upper right", fontsize=6.5, title_fontsize=6.5, frameon=False)
    axis.text(
        0.03, 0.45, r"dotted:" + "\n" + r"R\,=\,41 alone", transform=axis.transAxes, fontsize=6.5, va="top"
    )
    panel_label(axis, "(b)")

    axis = axes[1, 0]
    redshift = data.redshift.to_numpy()
    raw = residual_against_dn4000(data, data.hminus_bump_mag.to_numpy())
    corrected = residual_against_dn4000(data, (data.hminus_bump_mag - data.bias_on_5gyr).to_numpy())
    for values, colour, marker, label in (
        (raw, "black", "o", "measured"),
        (corrected, "0.55", "s", r"minus sampling bias (TP-AGB on)"),
    ):
        centres, medians, errors = binned(redshift, values, REDSHIFT_EDGES)
        axis.errorbar(
            centres, medians, yerr=errors, color=colour, marker=marker, ms=3, lw=1.0, capsize=0, label=label
        )
    for name, column in BIAS_TEMPLATES.items():
        centres, medians, _ = binned(redshift, data[column].to_numpy(), REDSHIFT_EDGES)
        axis.plot(centres, medians - np.median(data[column]), color=MODEL_COLOURS[name], lw=1.0, ls="--")
    axis.axhline(0, color="0.5", lw=0.6)
    axis.set_ylim(0.004, -0.004)
    axis.yaxis.set_major_formatter(plt.FuncFormatter(lambda value, _: f"${value:.3f}$"))
    axis.set_xlabel("redshift")
    axis.set_ylabel(r"index $-$ median at its D$_{\rm n}$4000 [mag]")
    handles, labels = axis.get_legend_handles_labels()
    handles.append(Line2D([], [], color="0.3", ls="--", lw=1.0))
    labels.append("sampling bias of the models")
    axis.legend(handles, labels, loc="upper left", bbox_to_anchor=(0.08, 1.0), fontsize=6.5, frameon=False)
    panel_label(axis, "(c)")

    axis = axes[1, 1]
    edges = np.linspace(1.1, 2.6, 61)
    axis.hist(data.d4000_sub, bins=edges, density=True, color="0.8", label="SDSS galaxies")
    model_all = load_model("TP-AGB on", 1.0)["d4000"]
    model_late = load_model("TP-AGB on", LATE_EPOCH_GYR)["d4000"]
    axis.hist(
        model_all,
        bins=edges,
        density=True,
        histtype="step",
        color="black",
        lw=1.0,
        label=r"models, epochs $\geq 1$ Gyr",
    )
    axis.hist(
        model_late,
        bins=edges,
        density=True,
        histtype="step",
        color="black",
        lw=1.0,
        ls="--",
        label=rf"models, epochs $\geq {LATE_EPOCH_GYR:g}$ Gyr",
    )
    axis.set_xlim(1.1, 2.6)
    axis.set_ylim(0, 2.9)
    axis.set_xlabel("D4000")
    axis.set_ylabel("density")
    axis.legend(loc="upper right", fontsize=6.5, frameon=False)
    panel_label(axis, "(d)")
    fig.savefig(FIGURE_DIR / "fig7_model_comparability_checks.png")
    plt.close(fig)


def figure_late_models(data):
    late = {name: load_model(name, LATE_EPOCH_GYR) for name in MODELS}
    ssfr_limit = max(np.percentile(model["log_ssfr"], 99) for model in late.values())
    covered = data[(data.log_ssfr < ssfr_limit)]
    shifts = {name: float(np.median(data[column])) for name, column in BIAS_TEMPLATES.items()}
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
    for axis, (column, error_column, model_key, label, x_range, edges, tag) in zip(axes, panels, strict=True):
        density_contours(
            axis, data[column], data.hminus_bump_mag, x_range, BUMP_RANGE, [0.95, 0.68], True, None
        )
        for name, model in late.items():
            density_contours(
                axis,
                model[model_key],
                model["bump"] + shifts[name],
                x_range,
                BUMP_RANGE,
                [0.95, 0.68],
                False,
                MODEL_COLOURS[name],
                bins=120,
                smooth=1.2,
            )
        running_median(axis, covered[column].to_numpy(), covered.hminus_bump_mag.to_numpy(), edges)
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
        Line2D(
            [],
            [],
            color="black",
            marker="o",
            ms=2.8,
            label=rf"median, sSFR $< 10^{{{ssfr_limit:.1f}}}$ yr$^{{-1}}$",
        ),
        Line2D(
            [],
            [],
            color=MODEL_COLOURS["TP-AGB off"],
            lw=1.1,
            label=rf"TP-AGB off, epochs $\geq {LATE_EPOCH_GYR:g}$ Gyr",
        ),
        Line2D(
            [],
            [],
            color=MODEL_COLOURS["TP-AGB on"],
            lw=1.1,
            label=rf"TP-AGB on, epochs $\geq {LATE_EPOCH_GYR:g}$ Gyr",
        ),
    ]
    fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, 0.93), ncol=2, frameon=False)
    fig.savefig(FIGURE_DIR / "fig8_hminus_bump_with_late_models.png")
    plt.close(fig)

    numbers = {
        "ssfr_limit_log_yr": round(float(ssfr_limit), 2),
        "n_covered": int(len(covered)),
        "model_shift_mag": shifts,
    }
    d4000_bins = pd.cut(covered.d4000_sub, np.arange(1.5, 2.41, 0.15))
    numbers["covered_median_by_d4000"] = (
        covered.groupby(d4000_bins, observed=True).hminus_bump_mag.median().round(4).to_dict()
    )
    for name, model in late.items():
        model_bins = pd.cut(pd.Series(model["d4000"]), np.arange(1.5, 2.41, 0.15))
        numbers[f"model_median_by_d4000_{name}"] = (
            (pd.Series(model["bump"]) + shifts[name])
            .groupby(model_bins, observed=True)
            .median()
            .round(4)
            .to_dict()
        )
    numbers["covered_median"] = round(float(covered.hminus_bump_mag.median()), 4)
    numbers["covered_spearman_d4000"] = round(
        float(covered[["d4000_sub", "hminus_bump_mag"]].corr("spearman").iloc[0, 1]), 3
    )
    return numbers


def main():
    summary = json.loads((RESULT_DIR / "model_check_summary.json").read_text())
    data = load()
    figure_checks(data, summary)
    numbers = figure_late_models(data)
    for key, value in numbers.items():
        print(key, {str(k): v for k, v in value.items()} if isinstance(value, dict) else value)


if __name__ == "__main__":
    main()
