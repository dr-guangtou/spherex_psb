#!/usr/bin/env python3
"""Figures for the documentation site that are made from SPHEREx calibration products and from the SED
demo's own measurements (docs/figures/site/).

usage: uv run python scripts/site_figures.py
"""

from __future__ import annotations

import glob
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from astropy.coordinates import SkyCoord
from astropy.io import fits

sys.path.insert(0, str(Path(__file__).resolve().parent / "sed_demo"))
from sample_definition import DEMO_GALAXIES  # noqa: E402

from spherex_psb import CUTOUT_ROOT, RESULTS_ROOT  # noqa: E402
from spherex_psb.figures.style import (  # noqa: E402
    DETECTOR_COLOURS,
    DOUBLE_COLUMN_IN,
    NEUTRAL_GREY,
    apply_style,
    panel_label,
)
from spherex_psb.products.flags import FLAG_BITS  # noqa: E402

FIGURE_ROOT = Path(__file__).resolve().parents[1] / "docs" / "figures" / "site"
CACHE = Path("/Users/shuang/data/spherex/calibration/spherex_retrieval_cache")
# Explanatory Supplement v2.0 section 1.3 (design values)
BANDS_UM = {
    1: (0.744, 1.116),
    2: (1.099, 1.651),
    3: (1.636, 2.421),
    4: (2.423, 3.822),
    5: (3.809, 4.420),
    6: (4.412, 5.002),
}
RESOLVING_POWER = {1: 39, 2: 41, 3: 41, 4: 35, 5: 112, 6: 128}
BOUNDARIES_UM = [1.1055, 1.6375, 2.4215, 3.814, 4.414]
DICHROIC_GAP_UM = (2.417, 2.426)  # every demo exposure with CWAVE in this range was DICHROIC-flagged
HE_I_UM = 1.083
HE_LEAK_UM = [0.84, 1.25, 1.49]  # Explanatory Supplement section 2.3
OTHER_AIRGLOW_UM = [0.78, 0.84, 0.93, 1.13, 1.81, 2.63, 2.75, 4.03, 4.64]
SHUTTLE_GLOW_UM = [3.0, 4.5]
REST_FEATURES_UM = {
    "CaT 0.86": 0.86,
    "He I leak 1.49 (obs)": None,
    r"H$^-$ bump windows": (1.494, 1.791),
    r"Pa$\alpha$ 1.875": 1.875,
    "H$_2$O 1.9": 1.9,
    "CO 2.29": 2.29,
    "PAH 3.3": 3.3,
    "CO 4.6": 4.6,
}
GALAXY_MARKERS = {
    "g1_reference": ("*", "#D55E00"),
    "g2_compact": ("s", "#0072B2"),
    "g3_large": ("D", "#009E73"),
    "g4_neighbour": ("^", "#E69F00"),
    "g5_no_legacy": ("v", "#CC79A7"),
    "g6_post_starburst": ("P", "#56B4E9"),
}


def cache_files() -> dict:
    """Locate the full-frame calibration products in the spherex-retrieval cache by content."""
    found: dict = {"cwave": {}, "sapm": {}, "epsf": {}}
    for path in sorted(CACHE.glob("*.fits")):
        with fits.open(path) as hdul:
            names = [h.name for h in hdul]
            if "CWAVE" in names:
                low = float(np.nanmin(hdul["CWAVE"].data))
                detector = min(BANDS_UM, key=lambda d: abs(BANDS_UM[d][0] - low))
                found["cwave"][detector] = path
            elif "EPSF_MOSAIC" in names:
                found["epsf"].setdefault(int(hdul["EPSF"].header["DETECTOR"]), path)
            elif len(hdul) == 2 and hdul[1].header.get("BUNIT") == "arcsec2":
                found["sapm"][len(found["sapm"])] = path  # the SAPM files do not name their detector
    return found


def figure_band_layout(out_path: Path) -> None:
    apply_style()
    fig, (ax, bx) = plt.subplots(
        2, 1, figsize=(DOUBLE_COLUMN_IN, 5.0), gridspec_kw={"height_ratios": [1, 1.6], "hspace": 0.35}
    )
    for detector, (lo, hi) in BANDS_UM.items():
        ax.barh(1, hi - lo, left=lo, height=0.5, color=DETECTOR_COLOURS[detector], alpha=0.85, lw=0)
        ax.text(
            0.5 * (lo + hi),
            1,
            f"D{detector}\n$R={RESOLVING_POWER[detector]}$",
            ha="center",
            va="center",
            fontsize=7,
        )
    ax.axvspan(*DICHROIC_GAP_UM, color="k", alpha=0.6, lw=0)
    ax.annotate(
        "dichroic\n2.417-2.426",
        (2.4215, 1.3),
        xytext=(2.5, 1.75),
        fontsize=6.5,
        arrowprops={"arrowstyle": "-", "lw": 0.5},
    )
    ax.axvline(HE_I_UM, color="#D55E00", lw=1.2)
    ax.text(HE_I_UM, 1.45, "He I 1.083", color="#D55E00", fontsize=6.5, ha="center")
    for w in HE_LEAK_UM:
        ax.axvline(w, color="#D55E00", lw=0.6, ls=":")
    for w in OTHER_AIRGLOW_UM:
        ax.plot([w, w], [0.5, 0.7], color="k", lw=0.8)
    ax.text(0.78, 0.35, "other airglow lines (ticks)", fontsize=6)
    for w in SHUTTLE_GLOW_UM:
        ax.annotate("", (w, 0.72), (w, 0.5), arrowprops={"arrowstyle": "-|>", "color": "#009E73", "lw": 0.8})
    ax.text(3.0, 0.35, "shuttle glow peaks", color="#009E73", fontsize=6, ha="center")
    ax.set_xlim(0.7, 5.1)
    ax.set_ylim(0.2, 2.0)
    ax.set_yticks([])
    ax.set_xlabel(r"observed wavelength [$\mu$m]")
    panel_label(ax, "(a)")
    # (b) where rest-frame features land versus redshift
    z = np.linspace(0, 0.25, 200)
    for name, rest in REST_FEATURES_UM.items():
        if rest is None:
            continue
        label_y = {"CaT 0.86": 1.0, r"H$^-$ bump windows": 2.05, r"Pa$\alpha$ 1.875": 2.3, "H$_2$O 1.9": 2.55}
        if isinstance(rest, tuple):
            bx.fill_between(z, rest[0] * (1 + z), rest[1] * (1 + z), color="#E69F00", alpha=0.3, lw=0)
            bx.text(0.252, label_y.get(name, rest[1] * 1.25), name, fontsize=6.5, va="center")
        else:
            bx.plot(z, rest * (1 + z), color="k", lw=0.8)
            bx.text(0.252, label_y.get(name, rest * 1.25), name, fontsize=6.5, va="center")
    for detector, (lo, hi) in BANDS_UM.items():
        bx.axhspan(lo, hi, color=DETECTOR_COLOURS[detector], alpha=0.12, lw=0)
    for w in BOUNDARIES_UM:
        bx.axhline(w, color=NEUTRAL_GREY, lw=0.6, ls="--")
    bx.axhspan(*DICHROIC_GAP_UM, color="k", alpha=0.5, lw=0)
    bx.axhline(HE_I_UM, color="#D55E00", lw=1.0)
    for w in HE_LEAK_UM:
        bx.axhline(w, color="#D55E00", lw=0.5, ls=":")
    bx.axvspan(0.03, 0.06, color=NEUTRAL_GREY, alpha=0.2, lw=0)
    bx.text(0.045, 0.75, "demo\nsample", fontsize=6, ha="center", va="bottom")
    bx.set_xlim(0, 0.25)
    bx.set_ylim(0.7, 5.1)
    bx.set_yscale("log")
    bx.set_yticks([0.8, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0])
    bx.set_yticklabels(["0.8", "1.0", "1.5", "2.0", "3.0", "4.0", "5.0"])
    bx.set_xlabel("redshift")
    bx.set_ylabel(r"observed wavelength [$\mu$m]")
    panel_label(bx, "(b)")
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)


def figure_wavelength_maps(found: dict, out_path: Path) -> None:
    apply_style()
    fig, axes = plt.subplots(
        2, 3, figsize=(DOUBLE_COLUMN_IN, 4.9), gridspec_kw={"wspace": 0.25, "hspace": 0.3}
    )
    for detector, ax in zip(sorted(found["cwave"]), axes.ravel(), strict=False):
        with fits.open(found["cwave"][detector]) as hdul:
            cwave = hdul["CWAVE"].data[::8, ::8]
            cband = hdul["CBAND"].data[::8, ::8]
        extent = (0, 2040, 0, 2040)
        image = ax.imshow(cwave, origin="lower", extent=extent, cmap="viridis")
        levels = np.linspace(np.nanmin(cwave), np.nanmax(cwave), 18)
        ax.contour(
            np.linspace(0, 2040, cwave.shape[1]),
            np.linspace(0, 2040, cwave.shape[0]),
            cwave,
            levels=levels,
            colors="w",
            linewidths=0.3,
        )
        r_median = float(np.nanmedian(cwave / cband))
        ax.set_title(
            f"D{detector}: {np.nanmin(cwave):.3f}-{np.nanmax(cwave):.3f} $\\mu$m, $R$ = {r_median:.1f}",
            fontsize=7,
        )
        ax.set_xticks([0, 1000, 2000])
        ax.set_yticks([0, 1000, 2000])
        if detector in (4, 5, 6):
            ax.set_xlabel("x [pixel]")
        if detector in (1, 4):
            ax.set_ylabel("y [pixel]")
        else:
            ax.set_yticklabels([])
        cb = fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
        cb.ax.tick_params(labelsize=6)
    fig.subplots_adjust(wspace=0.45)
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)


def figure_solid_angle(found: dict, out_path: Path) -> pd.DataFrame:
    apply_style()
    fig, axes = plt.subplots(
        2, 3, figsize=(DOUBLE_COLUMN_IN, 3.6), gridspec_kw={"wspace": 0.2, "hspace": 0.35}
    )
    axes = axes.ravel()
    rows = []
    ordered = sorted(found["sapm"].values(), key=lambda p: int(fits.getheader(p, 1)["DETECTOR"]))
    for k, (ax, path) in enumerate(zip(axes, ordered, strict=True)):
        with fits.open(path) as hdul:
            sapm = hdul[1].data[::8, ::8]
            detector = int(hdul[1].header["DETECTOR"])
        image = ax.imshow(
            sapm / 6.15**2, origin="lower", extent=(0, 2040, 0, 2040), cmap="coolwarm", vmin=0.98, vmax=1.02
        )
        ax.set_xticks([0, 2000])
        ax.set_yticks([0, 2000])
        if k % 3:
            ax.set_yticklabels([])
        ax.set_title(f"D{detector}: {np.nanmin(sapm):.2f}-{np.nanmax(sapm):.2f} arcsec$^2$", fontsize=7)
        rows.append(
            {
                "detector": detector,
                "min_arcsec2": float(np.nanmin(sapm)),
                "max_arcsec2": float(np.nanmax(sapm)),
                "min_over_nominal": float(np.nanmin(sapm) / 6.15**2),
                "max_over_nominal": float(np.nanmax(sapm) / 6.15**2),
            }
        )
    cb = fig.colorbar(image, ax=axes.tolist(), fraction=0.025, pad=0.02)
    cb.set_label(r"$\Omega_{\rm pixel} / (6.15'')^2$", fontsize=7)
    cb.ax.tick_params(labelsize=6)
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    return pd.DataFrame(rows)


def figure_epsf(found: dict, out_path: Path) -> pd.DataFrame:
    apply_style()
    fig = plt.figure(figsize=(DOUBLE_COLUMN_IN, 4.6))
    grid = fig.add_gridspec(2, 6, height_ratios=[1, 1.4], hspace=0.35, wspace=0.15)
    rows = []
    neff_axis = fig.add_subplot(grid[1, :])
    for k, detector in enumerate(sorted(found["epsf"])):
        with fits.open(found["epsf"][detector]) as hdul:
            table = hdul["EPSF"].data
            oversampling = int(hdul["EPSF"].header["OVSMPX"])
        centre = np.argmin(np.hypot(table["XCENTER"] - 1020, table["YCENTER"] - 1020))
        stamp = table["EPSF"][centre]
        ax = fig.add_subplot(grid[0, k])
        half = stamp.shape[0] / 2 / oversampling
        ax.imshow(
            np.log10(np.clip(stamp / stamp.max(), 1e-4, 1)),
            origin="lower",
            extent=(-half, half, -half, half),
            cmap="magma",
            vmin=-3.5,
            vmax=0,
        )
        ax.set_title(f"D{detector}, $N_{{\\rm eff}}$ = {float(table['NEFF_MEAN'][centre]):.1f}", fontsize=7)
        ax.set_xticks([-3, 0, 3])
        ax.set_yticks([-3, 0, 3]) if k == 0 else ax.set_yticks([])
        if k == 0:
            ax.set_ylabel("native pixels")
        neff_axis.plot(
            table["CWAVE"],
            table["NEFF_MEAN"],
            ".",
            ms=2.5,
            color=DETECTOR_COLOURS[detector],
            label=f"D{detector} ({len(table)} zones)",
        )
        rows.append(
            {
                "detector": detector,
                "zones": int(len(table)),
                "neff_min": float(np.nanmin(table["NEFF_MEAN"])),
                "neff_median": float(np.nanmedian(table["NEFF_MEAN"])),
                "neff_max": float(np.nanmax(table["NEFF_MEAN"])),
                "nstar_median": float(np.nanmedian(table["NSTAR"])),
            }
        )
    neff_axis.set_xlabel(r"zone central wavelength CWAVE [$\mu$m]")
    neff_axis.set_ylabel(r"$N_{\rm eff}$ of the zone ePSF [pixels]")
    neff_axis.legend(fontsize=6.5, ncol=3, loc="lower right", frameon=False)
    neff_axis.set_xlim(0.7, 5.1)
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    return pd.DataFrame(rows)


def load_records() -> pd.DataFrame:
    frames = []
    for name in DEMO_GALAXIES:
        path = RESULTS_ROOT / name / "records_screened.parquet"
        if path.exists():
            frames.append(pd.read_parquet(path))
    return pd.concat(frames, ignore_index=True)


def figure_backgrounds(records: pd.DataFrame, out_path: Path) -> pd.DataFrame:
    apply_style()
    fig, axes = plt.subplots(1, 3, figsize=(DOUBLE_COLUMN_IN, 2.7), gridspec_kw={"wspace": 0.5})
    usable = records[(records.reject_reason == "") & (records.screen_reason == "")]
    rows = []
    for name, galaxy in DEMO_GALAXIES.items():
        sub = usable[usable.galaxy == name]
        if not len(sub):
            continue
        ecliptic = SkyCoord(galaxy.ra, galaxy.dec, unit="deg").barycentricmeanecliptic
        marker, colour = GALAXY_MARKERS[name]
        label = f"{name[3:].replace('_', ' ')} ($\\beta$ = {ecliptic.lat.deg:+.0f}$^\\circ$)"
        order = np.argsort(sub.cwave_um.to_numpy())
        axes[0].plot(
            sub.cwave_um.to_numpy()[order],
            sub.zodi_at_target_mjysr.to_numpy()[order],
            marker,
            ms=2.5,
            mec="none",
            color=colour,
            label=label,
        )
        axes[1].plot(
            sub.cwave_um,
            sub.background_const_mjysr / sub.zodi_at_target_mjysr,
            marker,
            ms=2.5,
            mec="none",
            color=colour,
            alpha=0.7,
        )
        axes[2].plot(
            sub.cwave_um,
            sub.flux_model_ujy / sub.flux_model_err_ujy,
            marker,
            ms=2.5,
            mec="none",
            color=colour,
            alpha=0.7,
        )
        rows.append(
            {
                "galaxy": name,
                "ecliptic_latitude_deg": float(ecliptic.lat.deg),
                "zodi_median_mjysr_D1": float(sub[sub.detector == 1].zodi_at_target_mjysr.median()),
                "zodi_median_mjysr_D4": float(sub[sub.detector == 4].zodi_at_target_mjysr.median()),
                "zodi_median_mjysr_D6": float(sub[sub.detector == 6].zodi_at_target_mjysr.median()),
                "residual_over_zodi_median": float(
                    (sub.background_const_mjysr / sub.zodi_at_target_mjysr).median()
                ),
                "residual_over_zodi_p16": float(
                    (sub.background_const_mjysr / sub.zodi_at_target_mjysr).quantile(0.16)
                ),
                "residual_over_zodi_p84": float(
                    (sub.background_const_mjysr / sub.zodi_at_target_mjysr).quantile(0.84)
                ),
                "snr_median_D1": float(
                    (
                        sub[sub.detector == 1].flux_model_ujy / sub[sub.detector == 1].flux_model_err_ujy
                    ).median()
                ),
                "snr_median_D6": float(
                    (
                        sub[sub.detector == 6].flux_model_ujy / sub[sub.detector == 6].flux_model_err_ujy
                    ).median()
                ),
            }
        )
    axes[0].set_ylabel("ZODI model at the target [MJy/sr]")
    axes[1].legend(fontsize=5.5, frameon=False, loc="lower left", ncol=2)
    axes[1].axhline(0, color=NEUTRAL_GREY, lw=0.6)
    axes[1].set_ylabel("fitted residual background / ZODI")
    axes[1].set_ylim(-0.3, 0.5)
    axes[2].set_ylabel("per-exposure S/N of the model flux")
    axes[2].set_yscale("log")
    for ax, label in zip(axes, ("(a)", "(b)", "(c)"), strict=True):
        ax.set_xlabel(r"CWAVE [$\mu$m]")
        ax.set_xlim(0.7, 5.1)
        panel_label(ax, label)
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    return pd.DataFrame(rows)


def figure_cadence(records: pd.DataFrame, out_path: Path) -> dict:
    apply_style()
    fig, (ax, bx) = plt.subplots(
        1, 2, figsize=(DOUBLE_COLUMN_IN, 2.6), gridspec_kw={"wspace": 0.3, "width_ratios": [1.3, 1]}
    )
    sub = records[records.galaxy == "g1_reference"]
    for detector in range(1, 7):
        pick = sub[sub.detector == detector]
        ax.plot(
            pick.mjd - 60000,
            pick.cwave_um,
            "o",
            ms=2.2,
            mec="none",
            color=DETECTOR_COLOURS[detector],
            label=f"D{detector}",
        )
    ax.set_xlabel("MJD - 60000")
    ax.set_ylabel(r"CWAVE [$\mu$m]")
    ax.set_yscale("log")
    ax.set_yticks([0.8, 1, 1.5, 2, 3, 4, 5])
    ax.set_yticklabels(["0.8", "1", "1.5", "2", "3", "4", "5"])
    ax.set_ylim(0.7, 7.5)
    ax.legend(fontsize=6, ncol=6, frameon=False, loc="upper left")
    info = {}
    for name in DEMO_GALAXIES:
        path = RESULTS_ROOT / name / "sed_model.parquet"
        if not path.exists():
            continue
        sed = pd.read_parquet(path)
        marker, colour = GALAXY_MARKERS[name]
        bx.plot(
            sed.wavelength_um, sed.n_exposures, "-", lw=0.8, color=colour, label=name[3:].replace("_", " ")
        )
        info[name] = {
            "min": int(sed.n_exposures.min()),
            "median": float(sed.n_exposures.median()),
            "max": int(sed.n_exposures.max()),
        }
    bx.set_xlabel(r"channel wavelength [$\mu$m]")
    bx.set_ylabel("used exposures per channel")
    bx.legend(fontsize=5.5, frameon=False, ncol=2)
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    # time span and passes of the reference galaxy
    mjd = np.sort(sub.mjd.unique())
    gaps = np.diff(mjd)
    passes = 1 + int((gaps > 30).sum())
    info["g1_reference_visits"] = {
        "first_mjd": float(mjd.min()),
        "last_mjd": float(mjd.max()),
        "n_unique_mjd": int(len(mjd)),
        "passes_separated_by_30d": passes,
    }
    return info


def figure_flags(out_path: Path) -> pd.DataFrame:
    apply_style()
    counts = {name: np.zeros(7, dtype=np.int64) for name in FLAG_BITS}
    pixels = np.zeros(7, dtype=np.int64)
    for path in sorted(glob.glob(str(CUTOUT_ROOT / "*" / "cutout_*.fits"))):
        with fits.open(path) as hdul:
            detector = int(hdul[0].header.get("DETECTOR") or hdul[1].header["DETECTOR"])
            flags = hdul["FLAGS"].data.astype(np.int64)
        pixels[detector] += flags.size
        for name, bit in FLAG_BITS.items():
            counts[name][detector] += int(((flags >> bit) & 1).sum())
    table = pd.DataFrame(
        {name: counts[name][1:] / pixels[1:] for name in FLAG_BITS}, index=[f"D{d}" for d in range(1, 7)]
    ).T
    table["any"] = table.mean(axis=1)
    shown = table[table["any"] > 0].sort_values("any", ascending=False)
    fig, ax = plt.subplots(figsize=(DOUBLE_COLUMN_IN, 2.8))
    width = 0.13
    for k, detector in enumerate(range(1, 7)):
        ax.bar(
            np.arange(len(shown)) + (k - 2.5) * width,
            shown[f"D{detector}"],
            width,
            color=DETECTOR_COLOURS[detector],
            label=f"D{detector}",
        )
    ax.set_yscale("log")
    ax.set_ylim(1e-6, 1)
    ax.set_xticks(range(len(shown)))
    ax.set_xticklabels(shown.index, rotation=40, ha="right", rotation_mode="anchor", fontsize=6.5)
    ax.set_ylabel("fraction of cutout pixels with the flag")
    ax.legend(fontsize=6, ncol=6, frameon=False, loc="upper right")
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    table["pixels_total"] = int(pixels.sum())
    return table


def main() -> None:
    FIGURE_ROOT.mkdir(parents=True, exist_ok=True)
    pd.set_option("display.width", 220)
    found = cache_files()
    print("cache files:", {k: {d: p.name for d, p in v.items()} for k, v in found.items()})
    figure_band_layout(FIGURE_ROOT / "band_layout.png")
    figure_wavelength_maps(found, FIGURE_ROOT / "wavelength_maps.png")
    print(figure_solid_angle(found, FIGURE_ROOT / "solid_angle_maps.png").to_string(index=False))
    print(figure_epsf(found, FIGURE_ROOT / "epsf_zones.png").round(2).to_string(index=False))
    records = load_records()
    print(figure_backgrounds(records, FIGURE_ROOT / "background_levels.png").round(3).to_string(index=False))
    print(figure_cadence(records, FIGURE_ROOT / "survey_cadence.png"))
    flags = figure_flags(FIGURE_ROOT / "flag_statistics.png")
    flags.to_csv(RESULTS_ROOT / "flag_statistics.csv")
    print((flags.drop(columns="pixels_total") * 100).round(3).to_string())
    print("pixels", int(flags.pixels_total.iloc[0]))
    print("figures written to", FIGURE_ROOT)


if __name__ == "__main__":
    main()
