"""The stacked H-minus bump of the Dn4000-HdeltaA cells and of the post-starburst sets against the H-bump
paper's model populations, on the stacks' system.

1. Resolution of the stacks. The stacks approach continuous sampling at the SPHEREx resolution (median R =
   35-41 in D1-D4). For every SSP of the H-bump project (ages `SSP_MIN_AGE_GYR`-13 Gyr, four metallicities,
   TP-AGB off: C3K agb 0; on: LW02, 2 x agb 1 - agb 0, as the paper) the index is measured as on a stack
   (F_lambda smoothed to R = 41 or 35 with `check_model_comparability.kernel_table`, averaged on the 0.005 um
   stack grid, `stack_sed_and_bump.profile_index`) and as in the population files (R = 100,
   `spectral_indices`). A straight line of (stack-system minus R = 100) against the R = 100 index, per TP-AGB
   setting, converts the populations.
2. Populations. The paper's populations (`output/population` and `population_lw02`, TP-AGB off agb 0 and on
   agb 2), restricted to epochs after `LATE_EPOCH_GYR` (what a z = 0.03-0.06 galaxy can be; section 8.4 of the
   review). Model HdeltaA is lowered by `HDELTA_A_OFFSET` (the models' sigma = 300 km/s against the SDSS
   resolution plus the galaxies' dispersion, median over SSPs; section 8.4).
3. Prediction per galaxy: the median converted model bump in the bin of broad D4000 (step `D4000_STEP`;
   `predicted1d_`, used for the comparison, because the late-epoch models lie 1.0-1.5 A below the data in
   HdeltaA at fixed D4000) and in the 2-D bin (broad D4000 step `D4000_STEP`,
   HdeltaA step `HDELTA_STEP`) holding the galaxy's MPA-JHU `D4000_SUB` and `LICK_HD_A_SUB`, if the bin holds
   at least `MIN_MODELS` model epochs; otherwise the galaxy is outside the models. Per cell: the coverage, the
   mean prediction, and the stack of the covered galaxies only (`stack_sed_and_bump.stack_groups`).
4. Post-starburst sets (`stack_post_starbursts.py`): the same prediction from the late epochs and from all
   epochs after 1 Gyr (the paper's population, which includes the recently quenched epochs a z = 0.05 galaxy
   cannot have under its prior).

usage: uv run python scripts/sdss48k_review/compare_stacks_with_models.py
Output: <results>/sdss48k_hminus/model_stack_{ssp,cells,psb}.parquet, model_stack_summary.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_model_comparability import HBUMP_PROJECT, kernel_table, spectral_indices  # noqa: E402
from measure_hminus_bump import FIT_RANGE_UM, OUT_DIR  # noqa: E402
from stack_sed_and_bump import (  # noqa: E402
    BUMP_STEP_UM,
    galaxy_matrices,
    load_exposures,
    load_galaxies,
    profile_index,
    stack_groups,
)

SSP_MIN_AGE_GYR = 0.5
STACK_RESOLVING_POWERS = (41.0, 35.0)
LATE_EPOCH_GYR = 10.0
EPOCH_CUTS_GYR = (1.0, 8.0, 10.0, 12.0)
HDELTA_A_OFFSET = -0.28
D4000_STEP, HDELTA_STEP = 0.04, 0.5
MIN_MODELS = 20
D4000_EDGES = [1.3, 1.5, 1.6, 1.7, 1.8, 1.9, 2.0, 2.1, 2.2, 2.4]
VARIANTS = {"off": ("ssp_grid", "population", "agb0"), "on": ("ssp_grid_lw02", "population_lw02", "agb2")}


def ssp_conversion() -> tuple[pd.DataFrame, dict]:
    centres = np.arange(FIT_RANGE_UM[0], FIT_RANGE_UM[1] - 1e-9, BUMP_STEP_UM) + BUMP_STEP_UM / 2
    rows = []
    for label, (folder, _, _) in VARIANTS.items():
        native = np.load(HBUMP_PROJECT / f"output/{folder}/native.npz")
        r100 = np.load(HBUMP_PROJECT / f"output/{folder}/r100.npz")
        window = (native["wave_a"] > 12500) & (native["wave_a"] < 20500)
        age_gyr = 10 ** native["log_age_yr"] / 1e9
        for i_z, log_z in enumerate(native["log_z_grid"]):
            for i_age in np.flatnonzero(age_gyr >= SSP_MIN_AGE_GYR):

                def pick(grid, i_age=i_age, i_z=i_z, label=label):
                    flux = grid["flux_nu"][i_z, :, i_age]
                    return flux[0] if label == "off" else 2.0 * flux[1] - flux[0]

                record = {
                    "tp_agb": label,
                    "log_z": float(log_z),
                    "age_gyr": float(age_gyr[i_age]),
                    "index_r100": float(spectral_indices.h_minus_bump(r100["wave_a"], pick(r100))),
                }
                log_wave, table = kernel_table(
                    native["wave_a"][window], pick(native)[window], np.array(STACK_RESOLVING_POWERS)
                )
                wave_um = log_wave / 1e4
                for power, smoothed in zip(STACK_RESOLVING_POWERS, table, strict=True):
                    edges = np.r_[centres - BUMP_STEP_UM / 2, centres[-1] + BUMP_STEP_UM / 2]
                    fine = np.linspace(edges[0], edges[-1], 20 * len(centres) + 1)
                    flux_lambda = np.interp(fine, wave_um, smoothed / wave_um**2)
                    binned = flux_lambda[:-1].reshape(len(centres), 20).mean(axis=1)
                    record[f"index_stack_r{power:g}"] = float(profile_index(centres, binned))
                rows.append(record)
    table = pd.DataFrame(rows)
    fits = {}
    for label, group in table.groupby("tp_agb"):
        shift = group.index_stack_r41 - group.index_r100
        slope, intercept = np.polyfit(group.index_r100, shift, 1)
        scatter = shift - (slope * group.index_r100 + intercept)
        fits[label] = {
            "slope": float(slope),
            "intercept": float(intercept),
            "residual_std": float(scatter.std(ddof=2)),
            "shift_r41_range": [float(shift.min()), float(shift.max())],
            "shift_r35_minus_r41_median": float((group.index_stack_r35 - group.index_stack_r41).median()),
        }
    return table, fits


def load_population(label: str, fit: dict, epoch_min: float) -> pd.DataFrame:
    _, folder, key = VARIANTS[label]
    model = np.load(HBUMP_PROJECT / f"output/{folder}/indices.npz")
    keep = model["epoch_gyr"] >= epoch_min
    r100 = model[f"h_minus_bump_r100_{key}"][keep]
    return pd.DataFrame(
        {
            "d4000": model[f"d4000_{key}"][keep],
            "hdelta_a": model[f"hdelta_a_{key}"][keep] + HDELTA_A_OFFSET,
            "bump": r100 + fit["slope"] * r100 + fit["intercept"],
        }
    )


def predict(galaxies: pd.DataFrame, models: pd.DataFrame, use_hdelta: bool = True) -> np.ndarray:
    """Median model bump in the (D4000, HdeltaA) bin, or the D4000 bin alone, of each galaxy; NaN where the
    bin has fewer than MIN_MODELS model epochs."""

    def bin_key(d4000, hdelta_a):
        hdelta_bin = np.floor(hdelta_a / HDELTA_STEP).astype(int) if use_hdelta else np.zeros(len(d4000), int)
        return pd.MultiIndex.from_arrays([np.floor(d4000 / D4000_STEP).astype(int), hdelta_bin])

    grouped = models.bump.groupby(bin_key(models.d4000.to_numpy(), models.hdelta_a.to_numpy())).agg(
        ["median", "size"]
    )
    grouped = grouped[grouped["size"] >= MIN_MODELS]["median"]
    finite = np.isfinite(galaxies.d4000_sub.to_numpy()) & np.isfinite(galaxies.lick_hd_a_sub.to_numpy())
    keys = bin_key(galaxies.d4000_sub.fillna(0).to_numpy(), galaxies.lick_hd_a_sub.fillna(0).to_numpy())
    values = grouped.reindex(keys).to_numpy()
    return np.where(finite, values, np.nan)


def main() -> None:
    rng = np.random.default_rng(5)
    ssp, fits = ssp_conversion()
    ssp.to_parquet(OUT_DIR / "model_stack_ssp.parquet")
    print(json.dumps(fits, indent=1))

    galaxies = load_galaxies()
    galaxies = galaxies[~galaxies.in_magellanic.astype(bool)].reset_index(drop=True)
    membership = pd.read_parquet(OUT_DIR / "stack_membership.parquet")
    hdelta_gap = {}
    for label in VARIANTS:
        for epoch in EPOCH_CUTS_GYR:
            models = load_population(label, fits[label], epoch)
            galaxies[f"predicted_{label}_{epoch:g}gyr"] = predict(galaxies, models)
            galaxies[f"predicted1d_{label}_{epoch:g}gyr"] = predict(galaxies, models, use_hdelta=False)
        models = load_population(label, fits[label], LATE_EPOCH_GYR)
        bins = pd.cut(models.d4000, D4000_EDGES)
        data_bins = pd.cut(galaxies.d4000_sub, D4000_EDGES)
        hdelta_gap[label] = {
            str(k): float(galaxies.lick_hd_a_sub.groupby(data_bins, observed=True).median()[k] - v)
            for k, v in models.hdelta_a.groupby(bins, observed=True).median().items()
            if k in set(data_bins.dropna())
        }

    cells = galaxies.merge(membership[["target", "cell", "dn4000_bin", "hdelta_bin"]], on="target")
    cells = cells.sort_values("target").reset_index(drop=True)
    late = f"{LATE_EPOCH_GYR:g}gyr"
    covered = cells[f"predicted1d_off_{late}"].notna() & cells[f"predicted1d_on_{late}"].notna()
    rows = load_exposures(cells)
    matrices = galaxy_matrices(rows, cells)
    groups = {
        f"covered_cell{cell:02d}": cells.index[covered & (cells.cell == cell)].to_numpy()
        for cell in range(int(cells.cell.max()) + 1)
    }
    groups = {name: index for name, index in groups.items() if len(index) >= 30}
    stacked, _ = stack_groups(groups, cells, matrices, rng)
    stacked["cell"] = stacked.group.str.extract(r"(\d+)$").astype(int)

    full = pd.read_parquet(OUT_DIR / "stack_cells.parquet").query("cell >= 0")
    records = []
    for cell, members in cells.groupby("cell"):
        record = {
            "cell": int(cell),
            "dn4000_bin": int(members.dn4000_bin.iloc[0]),
            "hdelta_bin": int(members.hdelta_bin.iloc[0]),
            "n_galaxies": len(members),
            "d4000_broad_median": float(members.d4000_sub.median()),
            "coverage_late": float(covered[members.index].mean()),
        }
        for column in [c for c in cells.columns if c.startswith("predicted")]:
            values = members[column]
            record[f"{column}_coverage"] = float(values.notna().mean())
            record[f"{column}_mean"] = float(values.mean())
        records.append(record)
    table = pd.DataFrame(records)
    table = table.merge(
        full[
            ["cell", "stack_continuum_index", "stack_continuum_index_err", "dn4000_median", "hdelta_a_median"]
        ],
        on="cell",
    )
    table = table.merge(
        stacked[["cell", "n_galaxies", "stack_continuum_index", "stack_continuum_index_err"]].rename(
            columns={
                "n_galaxies": "n_covered",
                "stack_continuum_index": "covered_stack_index",
                "stack_continuum_index_err": "covered_stack_index_err",
            }
        ),
        on="cell",
        how="left",
    )
    for label in VARIANTS:
        table[f"covered_minus_{label}"] = (
            table.covered_stack_index - table[f"predicted1d_{label}_{late}_mean"]
        )
    table.to_parquet(OUT_DIR / "model_stack_cells.parquet")
    show = [
        "cell",
        "dn4000_median",
        "d4000_broad_median",
        "hdelta_a_median",
        "coverage_late",
        "stack_continuum_index",
        "covered_stack_index",
        f"predicted_off_{late}_coverage",
        f"predicted1d_off_{late}_mean",
        f"predicted1d_on_{late}_mean",
        f"predicted_on_{late}_mean",
        "covered_minus_off",
        "covered_minus_on",
    ]
    with pd.option_context("display.width", 250):
        print(table[show].round(4).to_string(index=False))

    psb_galaxies = pd.read_parquet(OUT_DIR / "psb_galaxies.parquet")
    psb_stacks = pd.read_parquet(OUT_DIR / "psb_stacks.parquet")
    psb = psb_galaxies[psb_galaxies.role == "candidate"][["target", "group"]].merge(galaxies, on="target")
    psb["set"] = psb.group.str.replace(r"(\d|_young|_old)$", "", regex=True)
    psb_records = []
    for keys, members in [*psb.groupby("group"), *psb.groupby("set")]:
        name = keys if keys in set(psb_stacks.set) else f"{keys}_all"
        record = {"set": name, "n_galaxies": len(members), "d4000_broad_median": members.d4000_sub.median()}
        for column in [c for c in psb.columns if c.startswith("predicted")]:
            record[f"{column}_coverage"] = float(members[column].notna().mean())
            record[f"{column}_mean"] = float(members[column].mean())
        psb_records.append(record)
    psb_table = pd.DataFrame(psb_records).drop_duplicates("set")
    candidates = psb_stacks[psb_stacks.role == "candidate"][
        ["set", "stack_continuum_index", "stack_continuum_index_err", "dn4000_median", "hdelta_a_median"]
    ]
    psb_table = psb_table.merge(candidates, on="set", how="left")
    psb_table.to_parquet(OUT_DIR / "model_stack_psb.parquet")
    with pd.option_context("display.width", 250, "display.max_columns", 40):
        print(psb_table.round(4).to_string(index=False))

    in_cells = table[table.covered_stack_index.notna()]
    summary = {
        "ssp_conversion_fits": fits,
        "late_epoch_gyr": LATE_EPOCH_GYR,
        "hdelta_a_offset": HDELTA_A_OFFSET,
        "data_minus_model_hdelta_a_median_at_d4000": hdelta_gap,
        "coverage_late_all_cells": float(covered.mean()),
        "covered_cells": int(len(in_cells)),
        "covered_minus_off_range": [
            float(in_cells.covered_minus_off.min()),
            float(in_cells.covered_minus_off.max()),
        ],
        "covered_minus_on_range": [
            float(in_cells.covered_minus_on.min()),
            float(in_cells.covered_minus_on.max()),
        ],
        "covered_minus_off_median": float(in_cells.covered_minus_off.median()),
        "covered_minus_on_median": float(in_cells.covered_minus_on.median()),
    }
    print(json.dumps(summary, indent=1))
    with open(OUT_DIR / "model_stack_summary.json", "w") as handle:
        json.dump(summary, handle, indent=2, default=float)


if __name__ == "__main__":
    main()
