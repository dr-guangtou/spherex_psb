"""Controls of the H-minus bump index for the D3/D2 detector step and for inclination; face-on cell stacks.

D3/D2 step (`d3_minus_d2_step` of `measure_hminus_bump.py`: median quadratic-fit residual of the D3 minus the
D2 exposures in the observed overlap 1.616-1.668 um). At z = 0.03-0.06 the blue window falls on D2 and the
feature and red windows mostly on D3, so a real per-galaxy calibration step enters the index (a +1 % step of
D3 deepens it by about 0.005 mag). Three measured tests:
1. Noise null: for every galaxy the step is redrawn `N_NULL_DRAWS` times with its numbers of D2 and D3
   overlap exposures, from Gaussian residuals with its own exposure scatter and (empirical) from its own
   residuals outside the overlap drawn with replacement; the spread of the measured steps is compared with
   that of the null steps.
2. Correction: every galaxy's index recomputed with its D3 fluxes divided by (1 + its step), by (1 + the step
   of a random other galaxy; shuffled, the noise a correction adds), and by (1 + the median step of all
   galaxies in its redshift bin; population). The intrinsic spread (robust spread of the residual from the
   running median at Dn4000, minus the median error in quadrature) of each version.
3. Population median step against redshift and size, and the residual against redshift before and after the
   population correction.

Inclination (SDSS r-band axis ratio q, cached by `investigate_bump_outliers.py`):
4. Index residual against q in each Dn4000 bin of the stack cells; a correction is the median residual of the
   galaxy's (Dn4000 bin, q bin) minus that of the face-on (q >= `FACE_ON_LIMIT`) galaxies of its Dn4000 bin;
   the tails of the significance after the correction.
5. Stacks (`stack_sed_and_bump.stack_groups`, same cells as the full stacks): the 40 cells with face-on
   galaxies only, and every Dn4000 bin split into edge-on (q < `EDGE_ON_LIMIT`), intermediate and face-on.

usage: uv run python scripts/sdss48k_review/control_inclination_and_detectors.py [--max-galaxies N]
Output: <results>/sdss48k_hminus/control_{galaxies,stacks}.parquet, control_profiles.npz, control_summary.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from investigate_bump_outliers import significance, tail_counts  # noqa: E402
from measure_hminus_bump import (  # noqa: E402
    FIT_RANGE_UM,
    OUT_DIR,
    OVERLAP_OBSERVED_UM,
    index_and_error,
    robust_sigma,
    screen,
)
from stack_sed_and_bump import (  # noqa: E402
    N_DN4000_BINS,
    N_HDELTA_BINS,
    galaxy_matrices,
    load_exposures,
    load_galaxies,
    stack_groups,
)

N_NULL_DRAWS = 20
FACE_ON_LIMIT = 0.5
EDGE_ON_LIMIT = 0.4
Q_EDGES = [0.0, 0.3, 0.4, 0.5, 0.7, 1.01]
REDSHIFT_EDGES = np.linspace(0.03, 0.06, 7)
SIZE_EDGES = [0.0, 2.0, 2.5, 3.0, 4.0, 5.0, 100.0]


def recompute_indices(exposures: pd.DataFrame, galaxies: pd.DataFrame, rng: np.random.Generator):
    """Per galaxy: index as catalogued, with its own, a shuffled and the population D3/D2 step removed, and
    null steps."""
    steps = galaxies.set_index("target").d3_minus_d2_step
    population_steps = galaxies.set_index("target").population_step
    finite_steps = steps.dropna().to_numpy()
    rows = exposures[(exposures.rest_um >= FIT_RANGE_UM[0]) & (exposures.rest_um <= FIT_RANGE_UM[1])]
    target_ids = rows.target.to_numpy()
    starts = np.flatnonzero(np.r_[True, target_ids[1:] != target_ids[:-1]])
    stops = np.r_[starts[1:], len(target_ids)]
    rest_all, flux_all = rows.rest_um.to_numpy(), rows.flux_lambda.to_numpy()
    wave_all, detector_all = rows.wv_um.to_numpy(), rows.detector_id.to_numpy()
    records = []
    for start, stop in zip(starts, stops, strict=True):
        target = int(target_ids[start])
        rest, flux = rest_all[start:stop], flux_all[start:stop]
        keep, residual, scatter = screen(rest, flux)
        rest, flux, detector = rest[keep], flux[keep], detector_all[start:stop][keep]
        residual = residual[keep]
        wave = wave_all[start:stop][keep]
        record = {
            "target": target,
            "index_recomputed": index_and_error(rest, flux, scatter)["hminus_bump_mag"],
        }
        on_d3 = detector == 3
        step = steps.get(target, np.nan)
        for label, value in (
            ("own", step),
            ("shuffled", rng.choice(finite_steps)),
            ("population", population_steps.get(target, np.nan)),
        ):
            corrected = np.where(on_d3, flux / (1 + value), flux) if np.isfinite(value) else flux * np.nan
            record[f"index_step_{label}"] = index_and_error(rest, corrected, scatter)["hminus_bump_mag"]
        overlap = (wave >= OVERLAP_OBSERVED_UM[0]) & (wave <= OVERLAP_OBSERVED_UM[1])
        n_d2, n_d3 = int((overlap & (detector == 2)).sum()), int((overlap & on_d3).sum())
        if n_d2 and n_d3 and np.isfinite(scatter):
            draws = rng.normal(0, scatter, (N_NULL_DRAWS, n_d2 + n_d3))
            null = np.median(draws[:, n_d2:], axis=1) - np.median(draws[:, :n_d2], axis=1)
            record["null_step_draw"] = float(null[0])
            record["null_step_sigma"] = float(np.std(null, ddof=1))
            outside = residual[~overlap]
            if len(outside) >= 5:
                picks = rng.choice(outside, (N_NULL_DRAWS, n_d2 + n_d3), replace=True)
                null = np.median(picks[:, n_d2:], axis=1) - np.median(picks[:, :n_d2], axis=1)
                record["empirical_null_step_draw"] = float(null[0])
                record["empirical_null_step_sigma"] = float(np.std(null, ddof=1))
        records.append(record)
    return pd.DataFrame(records)


def intrinsic_spread(galaxies: pd.DataFrame, column: str) -> dict:
    frame = galaxies[["d4000_n_sub", "hminus_bump_err_mag", column]].dropna()
    edges = np.arange(1.0, 2.45, 0.05)
    bins = np.digitize(frame.d4000_n_sub, edges)
    residual = frame[column] - frame.groupby(bins)[column].transform("median")
    spread = robust_sigma(residual.to_numpy())
    return {
        "n": len(frame),
        "residual_robust_sigma": spread,
        "intrinsic_spread": float(np.sqrt(max(spread**2 - frame.hminus_bump_err_mag.median() ** 2, 0.0))),
    }


def inclination_correction(galaxies: pd.DataFrame) -> pd.DataFrame:
    """Median residual per (Dn4000 bin, q bin) minus that of the face-on galaxies of the Dn4000 bin."""
    frame = galaxies.dropna(subset=["axis_ratio_r"]).copy()
    frame["q_bin"] = pd.cut(frame.axis_ratio_r, Q_EDGES, labels=False)
    table = frame.groupby(["dn4000_bin", "q_bin"]).index_residual.agg(["median", "size", "std"]).reset_index()
    face_on = (
        frame[frame.axis_ratio_r >= FACE_ON_LIMIT].groupby("dn4000_bin").index_residual.median().rename("ref")
    )
    table = table.merge(face_on, on="dn4000_bin")
    table["correction"] = table["median"] - table["ref"]
    table["median_err"] = 1.2533 * table["std"] / np.sqrt(table["size"])
    return table


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-galaxies", type=int, default=None)
    args = parser.parse_args()
    rng = np.random.default_rng(3)
    suffix = "_test" if args.max_galaxies else ""

    membership = pd.read_parquet(OUT_DIR / "stack_membership.parquet")
    galaxies = load_galaxies()
    galaxies = galaxies[~galaxies.in_magellanic.astype(bool)].reset_index(drop=True)
    galaxies, intrinsic = significance(galaxies)
    shapes = pd.read_parquet(OUT_DIR / "outlier_population.parquet", columns=["target", "axis_ratio_r"])
    sizes = pd.read_parquet(OUT_DIR / "sdss_shapes.parquet", columns=["target", "petroR50_r"])
    galaxies = galaxies.merge(shapes, on="target", how="left").merge(sizes, on="target", how="left")
    galaxies = galaxies.merge(
        membership[["target", "dn4000_bin", "hdelta_bin", "cell"]], on="target", how="left"
    )
    if args.max_galaxies:
        galaxies = galaxies.sample(args.max_galaxies, random_state=0).reset_index(drop=True)
    print(f"galaxies {len(galaxies):,}; in the stack cells {galaxies.cell.notna().sum():,}")

    # 1-3: D3/D2 step
    redshift_bin = pd.cut(galaxies.redshift, REDSHIFT_EDGES)
    galaxies["population_step"] = galaxies.groupby(redshift_bin, observed=True).d3_minus_d2_step.transform(
        "median"
    )
    exposures = load_exposures(galaxies, correct_extinction=False)
    recomputed = recompute_indices(exposures, galaxies, rng)
    galaxies = galaxies.merge(recomputed, on="target", how="left")
    difference = (galaxies.index_recomputed - galaxies.hminus_bump_mag).abs().max()
    print(f"recomputed minus catalogue index: max |difference| {difference:.1e}")
    step = galaxies.d3_minus_d2_step
    summary = {
        "n_galaxies": len(galaxies),
        "step": {
            "n": int(step.notna().sum()),
            "median": float(step.median()),
            "mean_clipped_10pct": float(step[step.abs() < 0.1].mean()),
            "robust_sigma_measured": robust_sigma(step.dropna().to_numpy()),
            "robust_sigma_null_draws": robust_sigma(galaxies.null_step_draw.dropna().to_numpy()),
            "median_null_sigma_per_galaxy": float(galaxies.null_step_sigma.median()),
            "fraction_beyond_5pct_measured": float((step.abs() > 0.05).mean()),
            "fraction_beyond_5pct_null": float((galaxies.null_step_draw.abs() > 0.05).mean()),
            "robust_sigma_empirical_null_draws": robust_sigma(
                galaxies.empirical_null_step_draw.dropna().to_numpy()
            ),
            "fraction_beyond_5pct_empirical_null": float(
                (galaxies.empirical_null_step_draw.abs() > 0.05).mean()
            ),
            "ols_slope_residual_on_step": float(
                np.polyfit(step[step.abs() < 0.2], galaxies.index_residual[step.abs() < 0.2], 1)[0]
            ),
        },
        "spread": {
            label: intrinsic_spread(galaxies, column)
            for label, column in (
                ("catalogue", "hminus_bump_mag"),
                ("own_step_removed", "index_step_own"),
                ("shuffled_step_removed", "index_step_shuffled"),
                ("population_step_removed", "index_step_population"),
            )
        },
        "index_change_own_step_median": float((galaxies.index_step_own - galaxies.hminus_bump_mag).median()),
    }
    for column, edges, name in (
        ("redshift", REDSHIFT_EDGES, "step_by_redshift"),
        ("petroR50_r", SIZE_EDGES, "step_by_petrosian_r50"),
    ):
        grouped = galaxies.groupby(pd.cut(galaxies[column], edges), observed=True).d3_minus_d2_step
        summary[name] = {
            str(k): {
                "n": int(v.notna().sum()),
                "median": float(v.median()),
                "err": float(1.2533 * robust_sigma(v.dropna().to_numpy()) / np.sqrt(v.notna().sum())),
            }
            for k, v in grouped
        }
    redshift_trend = {}
    for column in ("hminus_bump_mag", "index_step_population"):
        residual = galaxies[column] - galaxies.groupby(
            np.digitize(galaxies.d4000_n_sub, np.arange(1.0, 2.45, 0.05))
        )[column].transform("median")
        redshift_trend[column] = residual.groupby(redshift_bin, observed=True).median().to_dict()
    summary["residual_by_redshift"] = {
        column: {str(k): float(v) for k, v in trend.items()} for column, trend in redshift_trend.items()
    }
    print(json.dumps(summary, indent=1))

    # 4: inclination correction of the individual indices
    in_cells = galaxies[galaxies.cell.notna()].copy()
    corrections = inclination_correction(in_cells)
    print(corrections.round(4).to_string(index=False))
    in_cells["q_bin"] = pd.cut(in_cells.axis_ratio_r, Q_EDGES, labels=False)
    in_cells = in_cells.merge(
        corrections[["dn4000_bin", "q_bin", "correction"]], on=["dn4000_bin", "q_bin"], how="left"
    )
    in_cells["index_inclination_corrected"] = in_cells.hminus_bump_mag - in_cells.correction.fillna(0.0)
    corrected = in_cells.assign(hminus_bump_mag=in_cells.index_inclination_corrected).drop(
        columns=["index_median_at_dn4000", "index_residual", "significance"]
    )
    corrected, intrinsic_corrected = significance(corrected)
    summary["inclination"] = {
        "intrinsic_before": intrinsic,
        "intrinsic_after": intrinsic_corrected,
        "tails_before": tail_counts(in_cells),
        "tails_after": tail_counts(corrected),
        "corrections": corrections.to_dict(orient="records"),
    }
    print(json.dumps({k: v for k, v in summary["inclination"].items() if k != "corrections"}, indent=1))

    # 5: stacks by inclination
    stacked = galaxies[galaxies.cell.notna() & galaxies.axis_ratio_r.notna()]
    stacked = stacked.astype({"cell": int, "dn4000_bin": int, "hdelta_bin": int}).sort_values("target")
    stacked = stacked.reset_index(drop=True)
    rows = load_exposures(stacked)
    matrices = galaxy_matrices(rows, stacked)
    face_on = stacked.axis_ratio_r >= FACE_ON_LIMIT
    edge_on = stacked.axis_ratio_r < EDGE_ON_LIMIT
    groups = {
        "faceon_all": stacked.index[face_on].to_numpy(),
        "edgeon_all": stacked.index[edge_on].to_numpy(),
    }
    for cell in range(N_DN4000_BINS * N_HDELTA_BINS):
        groups[f"faceon_cell{cell:02d}"] = stacked.index[face_on & (stacked.cell == cell)].to_numpy()
    for row in range(N_DN4000_BINS):
        in_row = stacked.dn4000_bin == row
        groups[f"edgeon_row{row}"] = stacked.index[in_row & edge_on].to_numpy()
        groups[f"middle_row{row}"] = stacked.index[in_row & ~edge_on & ~face_on].to_numpy()
        groups[f"faceon_row{row}"] = stacked.index[in_row & face_on].to_numpy()
    groups = {name: index for name, index in groups.items() if len(index) >= 10}
    table, profiles = stack_groups(groups, stacked, matrices, rng)
    table["subset"] = table.group.str.split("_").str[0]
    table["cell"] = table.group.str.extract(r"cell(\d+)").astype(float)
    table["dn4000_bin"] = table.group.str.extract(r"row(\d)").astype(float)
    table.loc[table.cell.notna(), "dn4000_bin"] = table.cell // N_HDELTA_BINS
    table.loc[table.cell.notna(), "hdelta_bin"] = table.cell % N_HDELTA_BINS
    table.to_parquet(OUT_DIR / f"control_stacks{suffix}.parquet")
    np.savez_compressed(OUT_DIR / f"control_profiles{suffix}.npz", **profiles)
    show = ["group", "n_galaxies", "dn4000_median", "stack_continuum_index", "stack_continuum_index_err"]
    print(table[show].round(4).to_string(index=False))

    galaxies = galaxies.merge(
        in_cells[["target", "correction", "index_inclination_corrected"]], on="target", how="left"
    )
    keep = [
        "target",
        "redshift",
        "d4000_n_sub",
        "dn4000_bin",
        "hdelta_bin",
        "cell",
        "axis_ratio_r",
        "petroR50_r",
        "hminus_bump_mag",
        "hminus_bump_err_mag",
        "index_residual",
        "d3_minus_d2_step",
        "null_step_draw",
        "null_step_sigma",
        "index_step_own",
        "index_step_shuffled",
        "population_step",
        "index_step_population",
        "empirical_null_step_draw",
        "correction",
        "index_inclination_corrected",
    ]
    galaxies[keep].to_parquet(OUT_DIR / f"control_galaxies{suffix}.parquet")
    with open(OUT_DIR / f"control_summary{suffix}.json", "w") as handle:
        json.dump(summary, handle, indent=2, default=float)


if __name__ == "__main__":
    main()
