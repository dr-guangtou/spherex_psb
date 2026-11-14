#!/usr/bin/env python3
"""Feasibility of the 1.6 um H-minus bump index (Hbump_opt of the H-bump paper) on the demo SEDs.

Part 1 (data): for each demo galaxy, count the usable exposures inside the three index windows, measure the
index from the per-exposure fluxes and from the 102-channel SED, bootstrap the error, and quantify the bias
from the measured D2/D3 detector step.

Part 2 (models): take the FSPS CSP tracks and SSP grid of the H-bump project (TP-AGB on and off), degrade
them to the SPHEREx resolving power with two bandpass shapes of equal equivalent width (CBAND = lambda / R,
Hui et al. 2026 eq. 4), and compare the index with the R = 100 convention of the paper. Then sample the
degraded spectra at the real rest-frame exposure wavelengths of each demo galaxy with the measured
exposure-to-exposure scatter and recover the index with the same estimator as the data.

usage: uv run python scripts/sed_demo/hminus_bump_feasibility.py [--realisations 1000]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.ndimage import gaussian_filter1d, uniform_filter1d

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sample_definition import DEMO_GALAXIES  # noqa: E402

from spherex_psb import RESULTS_ROOT  # noqa: E402
from spherex_psb.figures.style import (  # noqa: E402
    DETECTOR_COLOURS,
    DOUBLE_COLUMN_IN,
    NEUTRAL_GREY,
    apply_style,
    panel_label,
)

HBUMP_PROJECT = Path("/Users/shuang/Dropbox/work/project/luandun/stellar_pop/fsps_agb")
sys.path.insert(0, str(HBUMP_PROJECT))
from spectral_indices import H_MINUS_BANDS_A, h_minus_bump  # noqa: E402

FIGURE_ROOT = Path(__file__).resolve().parents[2] / "docs" / "figures" / "sed_demo"
OUT_DIR = RESULTS_ROOT / "hminus_bump"
SPEED_OF_LIGHT_KM_S = 299792.458
RESOLVING_POWER_SWIR = 41.4  # Hui et al. 2026 table 1, bands 1-3
R_PAPER = 100.0  # instrumental resolution adopted for the index in the H-bump paper
VELOCITY_STEP_KM_S = 30.0  # log-wavelength step of the sigma300 products
WINDOWS_UM = {key: (lo / 1e4, hi / 1e4) for key, (lo, hi) in H_MINUS_BANDS_A.items()}
DEFINITIONS_UM = {  # rest-frame vacuum windows, table 3 of the H-bump paper
    "Hbump_opt": WINDOWS_UM,
    "Hbump_Lu26": {"blue": (1.400, 1.500), "feature": (1.500, 1.800), "red": (1.800, 2.000)},
    "Hbump_Verro22": {"blue": (1.450, 1.470), "feature": (1.610, 1.670), "red": (1.765, 1.785)},
}
GALAXY_MARKERS = {
    "g1_reference": ("*", "#D55E00"),
    "g2_compact": ("s", "#0072B2"),
    "g3_large": ("D", "#009E73"),
    "g4_neighbour": ("^", "#E69F00"),
    "g5_no_legacy": ("v", "#CC79A7"),
    "g6_post_starburst": ("P", "#56B4E9"),
}


# ----------------------------------------------------------------------------------------------------------
# estimator shared by data and simulations
def index_from_samples(
    rest_um: np.ndarray, flux_nu: np.ndarray, weights: np.ndarray | None = None, windows: dict = WINDOWS_UM
) -> float:
    """H-minus bump index from irregular samples: band means of F_lambda in the blue and red windows,
    straight-line pseudo-continuum through the band midpoints, mean of F_lambda / F_c over the feature
    samples."""
    if weights is None:
        weights = np.ones_like(flux_nu)
    flux_lambda = flux_nu / rest_um**2
    means = {}
    for key, (lo, hi) in windows.items():
        inside = (rest_um >= lo) & (rest_um <= hi)
        if inside.sum() == 0:
            return np.nan
        means[key] = np.average(flux_lambda[inside], weights=weights[inside])
    blue_mid = 0.5 * sum(windows["blue"])
    red_mid = 0.5 * sum(windows["red"])
    lo, hi = windows["feature"]
    inside = (rest_um >= lo) & (rest_um <= hi)
    fraction = (rest_um[inside] - blue_mid) / (red_mid - blue_mid)
    continuum = means["blue"] * (1 - fraction) + means["red"] * fraction
    ratio = np.average(flux_lambda[inside] / continuum, weights=weights[inside])
    return float(-2.5 * np.log10(ratio))


def bootstrap_index(rest_um, flux_nu, weights, rng, n: int, windows: dict = WINDOWS_UM) -> np.ndarray:
    """Resample exposures with replacement inside each window separately."""
    members = {key: np.flatnonzero((rest_um >= lo) & (rest_um <= hi)) for key, (lo, hi) in windows.items()}
    values = np.empty(n)
    for k in range(n):
        picks = np.concatenate([rng.choice(idx, size=len(idx), replace=True) for idx in members.values()])
        values[k] = index_from_samples(rest_um[picks], flux_nu[picks], weights[picks], windows)
    return values


# ----------------------------------------------------------------------------------------------------------
# part 1: the six demo galaxies
def measure_galaxy(name: str, rng, n_boot: int) -> tuple[dict, pd.DataFrame]:
    galaxy = DEMO_GALAXIES[name]
    z = galaxy.redshift
    records = pd.read_parquet(RESULTS_ROOT / name / "records_screened.parquet")
    usable = records[(records.reject_reason == "") & (records.screen_reason == "")].copy()
    usable["rest_um"] = usable.cwave_um / (1 + z)
    usable["rest_band_um"] = usable.cband_um / (1 + z)
    lo = min(d["blue"][0] for d in DEFINITIONS_UM.values())
    hi = max(d["red"][1] for d in DEFINITIONS_UM.values())
    window = usable[(usable.rest_um >= lo) & (usable.rest_um <= hi)].copy()
    flux = window.flux_model_ujy_dered.to_numpy()
    err = window.flux_model_err_ujy_dered.to_numpy()
    rest = window.rest_um.to_numpy()
    weights = 1 / err**2

    # exposure-to-exposure fractional scatter around the channel median (the error the SED uses)
    sed = pd.read_parquet(RESULTS_ROOT / name / "sed_model.parquet")
    sed = sed[sed.n_exposures > 0]
    channel_flux = np.interp(window.cwave_um, sed.wavelength_um, sed.flux_ujy_dered)
    in_opt = (rest >= WINDOWS_UM["blue"][0]) & (rest <= WINDOWS_UM["red"][1])
    residual = (flux / channel_flux - 1)[in_opt]
    scatter = 1.4826 * np.median(np.abs(residual - np.median(residual)))

    row = {
        "galaxy": name,
        "redshift": z,
        "n_blue": int(((rest >= WINDOWS_UM["blue"][0]) & (rest <= WINDOWS_UM["blue"][1])).sum()),
        "n_feature": int(((rest >= WINDOWS_UM["feature"][0]) & (rest <= WINDOWS_UM["feature"][1])).sum()),
        "n_red": int(((rest >= WINDOWS_UM["red"][0]) & (rest <= WINDOWS_UM["red"][1])).sum()),
        "n_d2": int(((window.detector == 2) & in_opt).sum()),
        "n_d3": int(((window.detector == 3) & in_opt).sum()),
        "boundary_rest_um": 1.6375 / (1 + z),
        "median_frac_err_formal": float(np.median(err / flux)),
        "exposure_frac_scatter": float(scatter),
    }
    row["index_exposures_mag"] = index_from_samples(rest, flux, weights)
    boot = bootstrap_index(rest, flux, weights, rng, n_boot)
    row["index_exposures_err_boot"] = float(np.std(boot))
    row["index_exposures_err_boot_16_84"] = float(0.5 * np.diff(np.percentile(boot, [16, 84]))[0])

    # channel estimator: interpolate the 102-channel SED and apply the paper's code
    rest_channels = sed.wavelength_um.to_numpy() / (1 + z)
    fine = np.linspace(1.45, 1.85, 2000)
    flux_fine = np.interp(fine, rest_channels, sed.flux_ujy_dered)
    row["index_channels_mag"] = float(h_minus_bump(fine * 1e4, flux_fine))
    err_channel = sed.flux_err_scatter_ujy_dered.fillna(sed.flux_err_formal_ujy_dered).to_numpy()
    draws = np.empty(n_boot)
    for k in range(n_boot):
        noisy = sed.flux_ujy_dered.to_numpy() + rng.normal(0, err_channel)
        draws[k] = h_minus_bump(fine * 1e4, np.interp(fine, rest_channels, noisy))
    row["index_channels_err_mc"] = float(np.std(draws))

    # bias from the D2/D3 step measured on this galaxy (model flux)
    boundary = pd.read_parquet(RESULTS_ROOT / name / "validation" / "boundary_ratios.parquet")
    step = boundary[(boundary.boundary == "D2/D3") & (boundary.flux_column == "flux_model_ujy")].iloc[0]
    row["d2d3_ratio_b_over_a"] = float(step.ratio_b_over_a)
    row["d2d3_ratio_err"] = float(step.ratio_err)
    corrected = np.where(window.detector == 3, flux / step.ratio_b_over_a, flux)
    row["index_after_d2d3_correction"] = index_from_samples(rest, corrected, weights)
    row["d2d3_bias_mag"] = row["index_exposures_mag"] - row["index_after_d2d3_correction"]
    # the same with a generic 1 % step, for scaling
    generic = np.where(window.detector == 3, flux / 1.01, flux)
    row["bias_per_percent_step_mag"] = row["index_exposures_mag"] - index_from_samples(rest, generic, weights)
    for definition, windows in DEFINITIONS_UM.items():
        if definition == "Hbump_opt":
            continue
        inside = {key: ((rest >= lo) & (rest <= hi)).sum() for key, (lo, hi) in windows.items()}
        row[f"{definition}_n_blue_feature_red"] = f"{inside['blue']}/{inside['feature']}/{inside['red']}"
        row[f"{definition}_index_mag"] = index_from_samples(rest, flux, weights, windows)
        row[f"{definition}_err_boot"] = float(
            np.std(bootstrap_index(rest, flux, weights, rng, n_boot, windows))
        )
        row[f"{definition}_bias_per_percent_step"] = row[f"{definition}_index_mag"] - index_from_samples(
            rest, generic, weights, windows
        )

    sample = pd.DataFrame(
        {
            "galaxy": name,
            "rest_um": rest,
            "rest_band_um": window.rest_band_um.to_numpy(),
            "detector": window.detector.to_numpy(),
            "flux_ujy": flux,
            "frac_err_formal": err / flux,
        }
    )
    return row, sample


# ----------------------------------------------------------------------------------------------------------
# part 2: models
def smooth_log_grid(flux_nu: np.ndarray, sigma_km_s: float | None = None, tophat_km_s: float | None = None):
    """Gaussian or top-hat smoothing of F_nu on the uniform log-wavelength grid (velocity units)."""
    if sigma_km_s is not None:
        return gaussian_filter1d(flux_nu, sigma_km_s / VELOCITY_STEP_KM_S, axis=-1, mode="nearest")
    size = max(int(round(tophat_km_s / VELOCITY_STEP_KM_S)), 1)
    return uniform_filter1d(flux_nu, size, axis=-1, mode="nearest")


def kernels() -> dict[str, dict]:
    """Smoothing kernels: the paper's R = 100 Gaussian (FWHM convention) and SPHEREx-like kernels whose
    equivalent width equals lambda / R (CBAND), as a Gaussian and as a top-hat; plus a Gaussian with
    FWHM = lambda / R as the broadest plausible case."""
    width = SPEED_OF_LIGHT_KM_S / RESOLVING_POWER_SWIR
    return {
        "R100 (paper)": {"sigma_km_s": SPEED_OF_LIGHT_KM_S / (2.3548 * R_PAPER)},
        "SPHEREx Gaussian, EW": {"sigma_km_s": width / np.sqrt(2 * np.pi)},
        "SPHEREx top-hat, EW": {"tophat_km_s": width},
        "SPHEREx Gaussian, FWHM": {"sigma_km_s": width / 2.3548},
    }


def model_tracks() -> dict:
    out = {}
    for agb in (0, 2):
        data = np.load(HBUMP_PROJECT / "output" / "single_csp_lw02" / f"spectra_sigma300_agb{agb}.npz")
        out[f"agb{agb}"] = {
            "wave_a": data["wave_a"],
            "flux_nu": data["flux_nu"],
            "epoch_gyr": data["epoch_gyr"],
        }
    return out


def degrade_and_measure(wave_a, flux_nu) -> dict[str, np.ndarray]:
    results = {}
    for label, kernel in kernels().items():
        smoothed = smooth_log_grid(flux_nu, **kernel)
        results[label] = np.array([h_minus_bump(wave_a, row) for row in smoothed])
    return results


def simulate_recovery(
    wave_a, flux_nu_spherex, samples: pd.DataFrame, scatter: float, step_ratio: float, rng, n: int
) -> dict:
    """Sample one degraded spectrum at the real rest wavelengths of a galaxy's exposures, add the galaxy's
    measured exposure-to-exposure scatter, and recover the index with the data estimator."""
    rest = samples.rest_um.to_numpy()
    detector = samples.detector.to_numpy()
    truth_fnu = np.interp(rest * 1e4, wave_a, flux_nu_spherex)
    noiseless = index_from_samples(rest, truth_fnu)
    values = np.empty(n)
    values_step = np.empty(n)
    for k in range(n):
        noisy = truth_fnu * (1 + rng.normal(0, scatter, size=len(rest)))
        values[k] = index_from_samples(rest, noisy)
        values_step[k] = index_from_samples(rest, np.where(detector == 3, noisy * step_ratio, noisy))
    return {
        "noiseless_sampled": noiseless,
        "mean": float(values.mean()),
        "std": float(values.std()),
        "mean_with_step": float(values_step.mean()),
    }


# ----------------------------------------------------------------------------------------------------------
def continuum_ratio(rest_um, flux_nu, windows: dict = WINDOWS_UM):
    """F_lambda divided by the straight-line pseudo-continuum through the blue and red band means."""
    flux_lambda = flux_nu / rest_um**2
    means = {}
    for key in ("blue", "red"):
        lo, hi = windows[key]
        inside = (rest_um >= lo) & (rest_um <= hi)
        means[key] = flux_lambda[inside].mean()
    blue_mid = 0.5 * sum(windows["blue"])
    red_mid = 0.5 * sum(windows["red"])
    fraction = (rest_um - blue_mid) / (red_mid - blue_mid)
    return flux_lambda / (means["blue"] * (1 - fraction) + means["red"] * fraction)


def figure(summary: pd.DataFrame, samples: pd.DataFrame, tracks: dict, indices: dict, out_path: Path) -> None:
    apply_style()
    fig, axes = plt.subplots(
        2, 2, figsize=(DOUBLE_COLUMN_IN, 5.2), gridspec_kw={"wspace": 0.28, "hspace": 0.4}
    )
    band_colours = {"blue": "#0072B2", "feature": "#E69F00", "red": "#D55E00"}
    track = tracks["agb2"]
    k_on = int(np.argmin(np.abs(track["epoch_gyr"] - 4.0)))
    k_off = int(np.argmin(np.abs(tracks["agb0"]["epoch_gyr"] - 4.0)))
    wave_um = track["wave_a"] / 1e4
    keep = (wave_um > 1.42) & (wave_um < 1.87)

    # (a) one TP-AGB-on spectrum at the paper's resolution and at the SPHEREx resolving power
    ax = axes[0, 0]
    for label, kernel, colour, ls in (
        ("$R=100$ (paper)", kernels()["R100 (paper)"], "k", "-"),
        ("SPHEREx, Gaussian", kernels()["SPHEREx Gaussian, EW"], DETECTOR_COLOURS[3], "-"),
        ("SPHEREx, top-hat", kernels()["SPHEREx top-hat, EW"], DETECTOR_COLOURS[2], "--"),
    ):
        sm = smooth_log_grid(track["flux_nu"][k_on], **kernel)
        f_lambda = sm / wave_um**2
        norm = np.interp(1.6, wave_um[keep], f_lambda[keep])
        ax.plot(wave_um[keep], f_lambda[keep] / norm, color=colour, ls=ls, lw=0.9, label=label)
    for key, (lo, hi) in WINDOWS_UM.items():
        ax.axvspan(lo, hi, color=band_colours[key], alpha=0.12, lw=0)
    ax.set_xlabel(r"$\lambda_{\rm rest}\ [\mu{\rm m}]$")
    ax.set_ylabel(r"$F_\lambda / F_\lambda(1.6\,\mu{\rm m})$")
    ax.set_xlim(1.42, 1.87)
    ax.set_ylim(0.58, 1.2)
    ax.legend(fontsize=6, loc="lower left", frameon=False)
    panel_label(ax, "(a)")

    # (b) index along the CSP tracks
    ax = axes[0, 1]
    t = track["epoch_gyr"]
    for label, colour in (
        ("$R=100$ (paper)", "k"),
        ("SPHEREx, Gaussian", DETECTOR_COLOURS[3]),
        ("SPHEREx, top-hat", DETECTOR_COLOURS[2]),
    ):
        key = {"$R=100$ (paper)": "R100 (paper)", "SPHEREx, Gaussian": "SPHEREx Gaussian, EW"}.get(
            label, "SPHEREx top-hat, EW"
        )
        ax.plot(t - 3.0, indices["agb2"][key], color=colour, lw=0.9, label=label + ", TP-AGB on")
        ax.plot(tracks["agb0"]["epoch_gyr"] - 3.0, indices["agb0"][key], color=colour, lw=0.9, ls=":")
    ax.plot([], [], color=NEUTRAL_GREY, ls=":", lw=0.9, label="dotted: TP-AGB off")
    ax.axvline(0, color=NEUTRAL_GREY, lw=0.5)
    ax.set_xlabel(r"$t - t_q$ [Gyr]")
    ax.set_ylabel(r"$I_{\rm mag}$ (Hbump\_opt) [mag]")
    ax.set_xlim(-1, 6)
    ax.set_ylim(0.012, -0.085)
    ax.legend(fontsize=5.5, loc="center right", bbox_to_anchor=(1.0, 0.42), frameon=False)
    panel_label(ax, "(b)")

    # (c) the exposures of two galaxies relative to their pseudo-continuum, with the two models
    ax = axes[1, 0]
    for offset, name in ((0.0, "g1_reference"), (0.18, "g6_post_starburst")):
        sub = samples[samples.galaxy == name]
        rest = sub.rest_um.to_numpy()
        ratio = continuum_ratio(rest, sub.flux_ujy.to_numpy())
        for detector in (2, 3):
            pick = sub.detector.to_numpy() == detector
            ax.errorbar(
                rest[pick],
                ratio[pick] + offset,
                yerr=(ratio * sub.frac_err_formal.to_numpy())[pick],
                fmt="o",
                ms=2.5,
                color=DETECTOR_COLOURS[detector],
                mec="none",
                lw=0.5,
                label=f"D{detector}" if offset == 0 else None,
            )
        ax.axhline(1 + offset, color=NEUTRAL_GREY, lw=0.5)
        ax.text(1.86, 1.06 + offset, name[3:].replace("_", " "), ha="right", va="bottom", fontsize=6)
    for agb, k, ls, label in (("agb2", k_on, "-", "TP-AGB on"), ("agb0", k_off, ":", "TP-AGB off")):
        degraded = smooth_log_grid(tracks[agb]["flux_nu"][k], **kernels()["SPHEREx Gaussian, EW"])
        model_ratio = continuum_ratio(wave_um[keep], degraded[keep])
        ax.plot(wave_um[keep], model_ratio, color="k", ls=ls, lw=0.7, label=f"{label}, $t-t_q=1$ Gyr")
    for key, (lo, hi) in WINDOWS_UM.items():
        ax.axvspan(lo, hi, color=band_colours[key], alpha=0.12, lw=0)
    ax.set_xlabel(r"$\lambda_{\rm rest}\ [\mu{\rm m}]$")
    ax.set_ylabel(r"$F_\lambda / F_{\rm c}$ (+ offset)")
    ax.set_xlim(1.42, 1.87)
    ax.set_ylim(0.88, 1.44)
    ax.legend(fontsize=5.5, loc="upper left", frameon=False, ncol=2)
    panel_label(ax, "(c)", x=0.9)

    # (d) measured indices against the model range at the SPHEREx resolving power
    ax = axes[1, 1]
    for i, row in summary.reset_index().iterrows():
        marker, colour = GALAXY_MARKERS[row.galaxy]
        ax.errorbar(
            i,
            row.index_exposures_mag,
            yerr=row.index_exposures_err_boot,
            fmt=marker,
            color=colour,
            ms=5,
            mec="k",
            mew=0.4,
            lw=0.7,
        )
        ax.plot(i + 0.25, row.index_channels_mag, marker, color=colour, ms=4, mfc="none", mew=0.6)
        ax.plot(i - 0.25, row.index_after_d2d3_correction, marker, color=NEUTRAL_GREY, ms=4, mec="k", mew=0.3)
    ax.plot([], [], "o", color="w", ms=4, mec="k", mew=0.6, label="open: 102-channel SED")
    ax.plot([], [], "o", color=NEUTRAL_GREY, ms=4, mec="k", mew=0.3, label="grey: D2/D3 step removed")
    agb2 = indices["agb2"]["SPHEREx Gaussian, EW"]
    agb0 = indices["agb0"]["SPHEREx Gaussian, EW"]
    late = t > 3.0
    ax.axhspan(
        agb2[late].min(),
        agb2[late].max(),
        color=DETECTOR_COLOURS[3],
        alpha=0.15,
        lw=0,
        label="TP-AGB on, $t>t_q$",
    )
    ax.axhspan(
        agb0[late].min(), agb0[late].max(), color=NEUTRAL_GREY, alpha=0.25, lw=0, label="TP-AGB off, $t>t_q$"
    )
    ax.set_xticks(range(len(summary)))
    labels = [g[3:].replace("_", " ") for g in summary.galaxy]
    ax.set_xticklabels(labels, rotation=35, ha="right", rotation_mode="anchor")
    ax.set_xlim(-0.6, len(summary) - 0.4)
    ax.set_ylabel(r"$I_{\rm mag}$ (Hbump\_opt) [mag]")
    ax.set_ylim(0.03, -0.1)
    ax.legend(fontsize=5.5, loc="upper right", frameon=False)
    panel_label(ax, "(d)")
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--realisations", type=int, default=1000)
    args = parser.parse_args()
    rng = np.random.default_rng(20261114)
    OUT_DIR.mkdir(exist_ok=True)

    rows, samples = [], []
    for name in DEMO_GALAXIES:
        if not (RESULTS_ROOT / name / "records_screened.parquet").exists():
            continue
        row, sample = measure_galaxy(name, rng, args.realisations)
        rows.append(row)
        samples.append(sample)
    summary = pd.DataFrame(rows)
    samples = pd.concat(samples)
    summary.to_csv(OUT_DIR / "galaxy_index_measurements.csv", index=False)
    samples.to_parquet(OUT_DIR / "window_exposures.parquet", index=False)
    pd.set_option("display.width", 250)
    print("=== data: Hbump_opt on the demo galaxies")
    print(summary.round(4).T.to_string())

    print("\n=== models: index along the t_q = 3, tau_q = 0.3 Gyr track")
    tracks = model_tracks()
    indices = {agb: degrade_and_measure(track["wave_a"], track["flux_nu"]) for agb, track in tracks.items()}
    table = []
    for agb in indices:
        t = tracks[agb]["epoch_gyr"]
        for label, values in indices[agb].items():
            late = t >= 3.0
            table.append(
                {
                    "track": agb,
                    "kernel": label,
                    "index_at_tq_minus_1": float(np.interp(2.0, t, values)),
                    "index_at_tq_plus_0.5": float(np.interp(3.5, t, values)),
                    "index_at_tq_plus_1": float(np.interp(4.0, t, values)),
                    "index_at_tq_plus_2": float(np.interp(5.0, t, values)),
                    "index_at_tq_plus_5": float(np.interp(8.0, t, values)),
                    "strongest_after_tq": float(values[late].min()),
                    "epoch_of_strongest": float(t[late][np.argmin(values[late])]),
                }
            )
    track_table = pd.DataFrame(table)
    track_table.to_csv(OUT_DIR / "model_track_indices.csv", index=False)
    print(track_table.round(4).to_string(index=False))

    print("\n=== the three window definitions on the track at SPHEREx resolution (Gaussian, EW)")
    rows_def = []
    for name, windows in DEFINITIONS_UM.items():
        per_track = {}
        for agb in ("agb2", "agb0"):
            wave_um = tracks[agb]["wave_a"] / 1e4
            degraded = smooth_log_grid(tracks[agb]["flux_nu"], **kernels()["SPHEREx Gaussian, EW"])
            per_track[agb] = np.array([index_from_samples(wave_um, row, None, windows) for row in degraded])
        t = tracks["agb2"]["epoch_gyr"]
        late = t >= 3.0
        rows_def.append(
            {
                "definition": name,
                "agb2_at_tq_minus_1": float(np.interp(2.0, t, per_track["agb2"])),
                "agb2_strongest_after_tq": float(per_track["agb2"][late].min()),
                "agb2_at_tq_plus_5": float(np.interp(8.0, t, per_track["agb2"])),
                "agb0_at_tq_plus_1": float(np.interp(4.0, t, per_track["agb0"])),
                "agb2_at_tq_plus_1": float(np.interp(4.0, t, per_track["agb2"])),
                "on_minus_off_at_tq_plus_1": float(
                    np.interp(4.0, t, per_track["agb2"]) - np.interp(4.0, t, per_track["agb0"])
                ),
            }
        )
    definition_table = pd.DataFrame(rows_def)
    definition_table.to_csv(OUT_DIR / "model_track_definitions.csv", index=False)
    print(definition_table.round(4).to_string(index=False))
    check = index_from_samples(tracks["agb2"]["wave_a"] / 1e4, tracks["agb2"]["flux_nu"][100])
    print(
        "estimator check (dense grid vs paper code, Hbump_opt, one spectrum):",
        round(check, 5),
        round(float(h_minus_bump(tracks["agb2"]["wave_a"], tracks["agb2"]["flux_nu"][100])), 5),
    )

    # resolution-only differences across the whole SSP grid (solar and all Z, both agb weights)
    grid = np.load(HBUMP_PROJECT / "output" / "ssp_grid_lw02" / "sigma300.npz")
    wave_a = grid["wave_a"]
    log_age = grid["log_age_yr"]
    keep_age = (log_age >= 8.0) & (log_age <= 10.1)
    flux = grid["flux_nu"][:, :, keep_age, :].reshape(-1, wave_a.size)
    ssp = degrade_and_measure(wave_a, flux)
    diff = {k: ssp[k] - ssp["R100 (paper)"] for k in ssp if k != "R100 (paper)"}
    print("\n=== SSP grid (ages 0.1-12.6 Gyr, 4 Z, agb 0/1): index(kernel) - index(R100), mag")
    ssp_stats = {
        k: {
            "median": float(np.median(v)),
            "min": float(v.min()),
            "max": float(v.max()),
            "range_R100": [float(ssp["R100 (paper)"].min()), float(ssp["R100 (paper)"].max())],
        }
        for k, v in diff.items()
    }
    print(json.dumps(ssp_stats, indent=1))
    slope = {}
    for k in diff:
        p = np.polyfit(ssp["R100 (paper)"], ssp[k], 1)
        slope[k] = [float(p[0]), float(p[1])]
    print("linear relation index(kernel) = a * index(R100) + b:", json.dumps(slope, indent=1))

    print("\n=== recovery with the real sampling and scatter of each galaxy (SPHEREx Gaussian, EW)")
    recovery = []
    for name in summary.galaxy:
        sub = samples[samples.galaxy == name]
        info = summary[summary.galaxy == name].iloc[0]
        for agb in ("agb2", "agb0"):
            t = tracks[agb]["epoch_gyr"]
            for epoch in (2.0, 3.5, 4.0, 5.0, 8.0):
                k = int(np.argmin(np.abs(t - epoch)))
                degraded = smooth_log_grid(tracks[agb]["flux_nu"][k], **kernels()["SPHEREx Gaussian, EW"])
                truth = float(h_minus_bump(tracks[agb]["wave_a"], degraded))
                res = simulate_recovery(
                    tracks[agb]["wave_a"],
                    degraded,
                    sub,
                    info.exposure_frac_scatter,
                    info.d2d3_ratio_b_over_a,
                    rng,
                    args.realisations,
                )
                recovery.append(
                    {"galaxy": name, "track": agb, "t_minus_tq": epoch - 3.0, "truth_spherex": truth, **res}
                )
    recovery = pd.DataFrame(recovery)
    recovery["bias_sampling"] = recovery.noiseless_sampled - recovery.truth_spherex
    recovery["bias_noise"] = recovery["mean"] - recovery.noiseless_sampled
    recovery["bias_step"] = recovery.mean_with_step - recovery["mean"]
    recovery.to_csv(OUT_DIR / "model_recovery.csv", index=False)
    print(recovery.round(4).to_string(index=False))
    figure(summary, samples, tracks, indices, FIGURE_ROOT / "fig8_hminus_bump_feasibility.png")
    print("figure written to", FIGURE_ROOT / "fig8_hminus_bump_feasibility.png")


if __name__ == "__main__":
    main()
