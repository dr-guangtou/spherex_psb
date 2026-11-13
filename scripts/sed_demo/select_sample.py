#!/usr/bin/env python3
"""Choose demo galaxies 2-6 from the candidate pools (roles fixed before any SPHEREx pixel is seen) and make
the sample figure (figure 1).

Inputs under /Users/shuang/data/spherex/sample: parent_with_sdss_shapes.parquet (parent catalogue joined to
SDSS DR17 shapes), candidate_pool.parquet, candidate_coverage.parquet (DR1 + QR3 exposures per detector),
candidate_neighbours.parquet (SDSS neighbours), candidate_ls_footprint.parquet (Legacy Survey DR10 sources
within 72 arcsec). Output: sample_selected.parquet and docs/figures/sed_demo/fig1_sample.png.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sample_definition import DEMO_GALAXIES  # noqa: E402

from spherex_psb import SAMPLE_ROOT  # noqa: E402
from spherex_psb.figures.style import DOUBLE_COLUMN_IN, NEUTRAL_GREY, apply_style, panel_label  # noqa: E402

FIGURE_ROOT = Path(__file__).resolve().parents[2] / "docs" / "figures" / "sed_demo"
ROLE_MARKERS = {
    "g1_reference": ("*", "#D55E00"),
    "g2_compact": ("s", "#0072B2"),
    "g3_large": ("D", "#009E73"),
    "g4_neighbour": ("^", "#E69F00"),
    "g5_no_legacy": ("v", "#CC79A7"),
    "g6_post_starburst": ("P", "#56B4E9"),
}


def load_candidates() -> pd.DataFrame:
    pool = pd.read_parquet(SAMPLE_ROOT / "candidate_pool.parquet")
    pool["specobjid"] = pool.specobjid.astype(str)
    coverage = pd.read_parquet(SAMPLE_ROOT / "candidate_coverage.parquet").rename(columns={"id": "specobjid"})
    neighbours = pd.read_parquet(SAMPLE_ROOT / "candidate_neighbours.parquet")
    footprint = pd.read_parquet(SAMPLE_ROOT / "candidate_ls_footprint.parquet")
    table = pool.merge(coverage.drop(columns=["pool", "ra", "dec"]), on="specobjid", how="left")
    table = table.merge(neighbours.drop(columns=["pool"]), on="specobjid", how="left")
    table = table.merge(footprint.drop(columns=["pool"]), on="specobjid", how="left")
    wide = [c for c in table.columns if c.startswith(("dr1_D", "qr3_D"))]
    deep = [c for c in table.columns if "deep" in c]
    table[wide + deep] = table[wide + deep].fillna(0)
    table["n_wide"] = table[wide].sum(axis=1)
    table["n_deep"] = table[deep].sum(axis=1) if deep else 0
    table["n_detectors_wide"] = sum(
        (table[f"dr1_D{d}"] + table[f"qr3_D{d}"] > 0).astype(int) for d in range(1, 7)
    )
    table["min_per_detector"] = np.min([table[f"dr1_D{d}"] + table[f"qr3_D{d}"] for d in range(1, 7)], axis=0)
    table["in_legacy"] = table.n_ls_dr10_72arcsec > 0
    table["psb_score"] = table.h_delta_a_emission_subtracted_angstrom - 4 * (
        table.dn4000_emission_subtracted - 1.3
    )
    return table


def choose(table: pd.DataFrame) -> dict[str, pd.Series]:
    usable = table[(table.n_detectors_wide == 6) & (table.n_deep == 0) & (table.min_per_detector >= 10)]
    isolated = usable[(usable.n_within_15.fillna(0) == 0)]
    picks = {}
    picks["g2_compact"] = (
        isolated[(isolated.pool == "compact") & isolated.in_legacy].sort_values("r_e").iloc[0]
    )
    picks["g3_large"] = (
        isolated[(isolated.pool == "large") & isolated.in_legacy].sort_values("r_e", ascending=False).iloc[0]
    )
    # a real companion: 5-13 arcsec away (entries closer than 5 arcsec are SDSS duplicates or shreds of the
    # target), within one magnitude in z; a star is preferred because its model is exact
    close = usable[
        (usable.nearest_sep >= 5) & (usable.nearest_sep <= 13) & (usable.brightest15_dz.abs() <= 1.0)
    ].copy()
    close["score"] = close.brightest15_dz.abs() + np.where(close.nearest_type == 6, 0.0, 0.5)
    picks["g4_neighbour"] = close.sort_values("score").iloc[0]
    g5_pool = pd.read_parquet(SAMPLE_ROOT / "candidate_g5_pool.parquet")
    g5_coverage = pd.read_parquet(SAMPLE_ROOT / "candidate_g5_coverage.parquet")
    g5 = g5_pool.merge(g5_coverage, on="specobjid")
    g5["n_detectors_wide"] = sum((g5[f"dr1_D{d}"] + g5[f"qr3_D{d}"] > 0).astype(int) for d in range(1, 7))
    g5 = g5[(g5.n_dr10 == 0) & (g5.n_dr9 == 0) & (g5.n_detectors_wide == 6)].sort_values("petroMag_z")
    parent_row = table.iloc[0:0]
    if len(g5):
        full = pd.read_parquet(SAMPLE_ROOT / "parent_with_sdss_shapes.parquet")
        full["specobjid"] = full.specobjid.astype(str)
        parent_row = full[full.specobjid == g5.specobjid.iloc[0]].copy()
        for column in (
            "n_wide",
            "n_deep",
            "min_per_detector",
            "n_within_15",
            "nearest_sep",
            "brightest15_dz",
            "nearest_type",
        ):
            parent_row[column] = np.nan
        parent_row["pool"] = "sgc_high_dec"
        parent_row["in_legacy"] = False
        wide = [c for c in g5.columns if c.startswith(("dr1_D", "qr3_D"))]
        parent_row["n_wide"] = float(g5[wide].iloc[0].sum())
        parent_row["n_deep"] = 0.0
        parent_row["min_per_detector"] = float(
            min(g5[f"dr1_D{d}"].iloc[0] + g5[f"qr3_D{d}"].iloc[0] for d in range(1, 7))
        )
    picks["g5_no_legacy"] = parent_row.iloc[0] if len(parent_row) else None
    psb = isolated[(isolated.pool == "psb") & isolated.in_legacy]
    picks["g6_post_starburst"] = psb.sort_values("psb_score", ascending=False).iloc[0]
    chosen = {k: v for k, v in picks.items() if v is not None}
    ids = [v.specobjid for v in chosen.values()]
    if len(set(ids)) != len(ids):
        raise RuntimeError("a galaxy was chosen for two roles")
    return chosen


def figure_sample(parent: pd.DataFrame, picks: dict[str, pd.Series], out_path: Path) -> None:
    apply_style()
    fig, axes = plt.subplots(1, 3, figsize=(DOUBLE_COLUMN_IN, 2.5), gridspec_kw={"wspace": 0.32})
    axes[0].hist2d(
        parent.redshift,
        parent.log_stellar_mass_msun,
        bins=[60, 60],
        range=[[0.03, 0.06], [10.0, 11.8]],
        cmap="Greys",
        cmin=1,
    )
    axes[0].set_xlabel(r"$z$")
    axes[0].set_ylabel(r"$\log_{10}(M_\star/{\rm M}_\odot)$")
    axes[1].hist2d(
        parent.dn4000_emission_subtracted,
        parent.h_delta_a_emission_subtracted_angstrom,
        bins=[60, 60],
        range=[[1.0, 2.3], [-5, 8]],
        cmap="Greys",
        cmin=1,
    )
    axes[1].set_xlabel(r"${\rm D}_n4000$")
    axes[1].set_ylabel(r"${\rm H}\delta_{\rm A}\ [{\rm \AA}]$")
    r_e = parent.r_e[np.isfinite(parent.r_e)]
    axes[2].hist(r_e, bins=np.linspace(0, 16, 65), color=NEUTRAL_GREY, histtype="stepfilled", alpha=0.6)
    axes[2].set_xlabel(r"$R_{\rm e}\ ({\rm SDSS}\ r)\ [{\rm arcsec}]$")
    axes[2].set_ylabel("galaxies")
    axes[2].axvline(6.15, color="k", lw=0.6, ls=":")
    axes[2].text(6.3, 0.95, "1 px", transform=axes[2].get_xaxis_transform(), fontsize=7, va="top")
    reference = DEMO_GALAXIES["g1_reference"]
    for role, (marker, colour) in ROLE_MARKERS.items():
        if role == "g1_reference":
            row = parent[parent.specobjid.astype(str) == reference.specobjid].iloc[0]
        elif role in picks:
            row = picks[role]
        else:
            continue
        label = role[3:].replace("_", " ")
        axes[0].plot(
            row.redshift,
            row.log_stellar_mass_msun,
            marker=marker,
            color=colour,
            ms=7,
            mec="k",
            mew=0.5,
            ls="none",
            label=label,
        )
        axes[1].plot(
            row.dn4000_emission_subtracted,
            row.h_delta_a_emission_subtracted_angstrom,
            marker=marker,
            color=colour,
            ms=7,
            mec="k",
            mew=0.5,
            ls="none",
        )
        axes[2].plot(
            row.r_e,
            0.08 * axes[2].get_ylim()[1],
            marker=marker,
            color=colour,
            ms=7,
            mec="k",
            mew=0.5,
            ls="none",
        )
    axes[0].legend(fontsize=6, loc="upper right", handletextpad=0.2)
    for ax, letter in zip(axes, "abc", strict=True):
        panel_label(ax, f"({letter})", x=0.04, y=0.96)
    fig.savefig(out_path)
    plt.close(fig)


def main() -> None:
    parent = pd.read_parquet(SAMPLE_ROOT / "parent_with_sdss_shapes.parquet")
    table = load_candidates()
    picks = choose(table)
    columns = [
        "specobjid",
        "pool",
        "ra_deg",
        "dec_deg",
        "redshift",
        "log_stellar_mass_msun",
        "dn4000_emission_subtracted",
        "h_delta_a_emission_subtracted_angstrom",
        "r_e",
        "q",
        "pa",
        "fracDeV_r",
        "petroMag_z",
        "modelMag_z",
        "objID",
        "n_wide",
        "n_deep",
        "min_per_detector",
        "n_within_15",
        "nearest_sep",
        "brightest15_dz",
        "nearest_type",
        "in_legacy",
    ]
    selected = pd.DataFrame([picks[k][columns] for k in picks], index=list(picks))
    pd.set_option("display.width", 250)
    print(selected.to_string())
    selected.to_parquet(SAMPLE_ROOT / "sample_selected.parquet")
    FIGURE_ROOT.mkdir(parents=True, exist_ok=True)
    figure_sample(parent, picks, FIGURE_ROOT / "fig1_sample.png")
    print("figure:", FIGURE_ROOT / "fig1_sample.png")
    print("\ncandidate table (usable rows):")
    usable = table[(table.n_detectors_wide == 6) & (table.n_deep == 0)]
    print(
        usable[
            [
                "specobjid",
                "pool",
                "r_e",
                "petroMag_z",
                "n_wide",
                "min_per_detector",
                "n_within_15",
                "nearest_sep",
                "brightest15_dz",
                "in_legacy",
                "psb_score",
            ]
        ]
        .round(2)
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()
