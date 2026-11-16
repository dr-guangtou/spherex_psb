"""Stacked SPHEREx SEDs and H-minus bump of post-starburst candidates against matched controls.

The equal-number cells of `stack_sed_and_bump.py` do not isolate post-starbursts (their top HdeltaA fifth is
the upper edge of the sequence). Here the candidates are selected directly from the MPA-JHU measurements of
all galaxies with a bump index (outside the Magellanic Clouds; the sparse parts of the plane are kept):

- weak emission: Halpha emission equivalent width below `WEAK_HALPHA_EW_A` (galSpecLine `H_ALPHA_EQW`,
  negative for emission), in the 3 arcsec SDSS fibre;
- HdeltaA excess: HdeltaA minus the median of all galaxies at the same Dn4000 (bins of 0.05), in units of the
  robust spread of that bin (which contains the HdeltaA measurement error).

Sets:
- `e_plus_a`: weak emission and HdeltaA > `E_PLUS_A_HDELTA_A`; split at Dn4000 `YOUNG_DN4000_LIMIT` into
  young and old.
- `balmer_excess`: weak emission and an HdeltaA excess above `EXCESS_LIMIT`, not in `e_plus_a`; in Dn4000
  bins.
- `balmer_deficit`: weak emission and an excess below -`EXCESS_LIMIT`: the mirror, for what the HdeltaA noise
  alone selects.
Controls: for every candidate the `CONTROLS_PER_CANDIDATE` nearest unused galaxies in (Dn4000 / 0.025,
redshift / 0.005) among the galaxies of no set with |excess| < 1: (1) weak-emission ones (`quiescent`
controls) and (2) all (`population` controls). Matching in redshift keeps the SPHEREx sampling the same.

Stacks as in `stack_sed_and_bump.py` (`stack_groups`): normalised whole SED and continuum-normalised bump
profile, bootstrap errors over galaxies.

usage: uv run python scripts/sdss48k_review/stack_post_starbursts.py
Output: <results>/sdss48k_hminus/psb_{galaxies,stacks}.parquet, psb_profiles.npz, psb_summary.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from measure_hminus_bump import OUT_DIR, robust_sigma  # noqa: E402
from stack_sed_and_bump import galaxy_matrices, load_exposures, load_galaxies, stack_groups  # noqa: E402

WEAK_HALPHA_EW_A = 3.0
E_PLUS_A_HDELTA_A = 4.0
YOUNG_DN4000_LIMIT = 1.45
EXCESS_LIMIT = 2.0
CONTROL_EXCESS_LIMIT = 1.0
CONTROLS_PER_CANDIDATE = 3
MATCH_SCALES = {"d4000_n_sub": 0.025, "redshift": 0.005}
DN4000_STEP = 0.05
EXCESS_DN4000_EDGES = [1.0, 1.65, 1.8, 1.9, 2.4]
SHAPES_FILE = "outlier_population.parquet"


def hdelta_excess(galaxies: pd.DataFrame) -> pd.Series:
    bins = np.digitize(galaxies.d4000_n_sub, np.arange(1.0, 2.45, DN4000_STEP))
    grouped = galaxies.groupby(bins).lick_hd_a_sub
    median = grouped.transform("median")
    spread = grouped.transform(lambda values: robust_sigma(values.to_numpy()))
    return (galaxies.lick_hd_a_sub - median) / spread


def match_controls(candidates: pd.DataFrame, pool: pd.DataFrame, rng: np.random.Generator) -> dict:
    """Candidate target -> list of control targets (nearest unused in scaled Dn4000 and redshift)."""
    scaled_pool = np.column_stack([pool[c] / s for c, s in MATCH_SCALES.items()])
    available = np.ones(len(pool), dtype=bool)
    matches = {}
    for position in rng.permutation(len(candidates)):
        candidate = candidates.iloc[position]
        point = np.array([candidate[c] / s for c, s in MATCH_SCALES.items()])
        distance = np.hypot(*(scaled_pool - point).T)
        distance[~available | (pool.target.to_numpy() == candidate.target)] = np.inf
        nearest = np.argsort(distance)[:CONTROLS_PER_CANDIDATE]
        nearest = nearest[np.isfinite(distance[nearest])]
        available[nearest] = False
        matches[int(candidate.target)] = pool.target.to_numpy()[nearest].tolist()
    return matches


def match_quality(candidates: pd.DataFrame, controls: pd.DataFrame) -> dict:
    return {
        f"{column}_median_difference": float(controls[column].median() - candidates[column].median())
        for column in ("d4000_n_sub", "redshift", "lick_hd_a_sub", "log_stellar_mass_msun")
    }


def main() -> None:
    rng = np.random.default_rng(4)
    galaxies = load_galaxies()
    galaxies = galaxies[~galaxies.in_magellanic.astype(bool)].reset_index(drop=True)
    shapes = pd.read_parquet(
        OUT_DIR / SHAPES_FILE, columns=["target", "axis_ratio_r", "petrosian_r50_arcsec"]
    )
    galaxies = galaxies.merge(shapes, on="target", how="left")
    galaxies["hdelta_excess"] = hdelta_excess(galaxies)
    galaxies["halpha_emission_ew"] = -galaxies.h_alpha_eqw
    weak = galaxies.halpha_emission_ew < WEAK_HALPHA_EW_A
    e_plus_a = weak & (galaxies.lick_hd_a_sub > E_PLUS_A_HDELTA_A)
    galaxies["set"] = np.select(
        [
            e_plus_a & (galaxies.d4000_n_sub < YOUNG_DN4000_LIMIT),
            e_plus_a,
            weak & (galaxies.hdelta_excess > EXCESS_LIMIT),
            weak & (galaxies.hdelta_excess < -EXCESS_LIMIT),
        ],
        ["e_plus_a_young", "e_plus_a_old", "balmer_excess", "balmer_deficit"],
        default="",
    )
    print(galaxies.set.value_counts().to_dict())

    quiet = (galaxies.hdelta_excess.abs() < CONTROL_EXCESS_LIMIT) & (galaxies.set == "")
    pools = {"quiescent": galaxies[weak & quiet], "population": galaxies[quiet]}
    membership = []
    for name in ("e_plus_a_young", "e_plus_a_old", "balmer_excess", "balmer_deficit"):
        candidates = galaxies[galaxies.set == name]
        if name.startswith("balmer"):
            dn4000_bin = pd.cut(candidates.d4000_n_sub, EXCESS_DN4000_EDGES, labels=False)
        else:
            dn4000_bin = pd.Series(0, index=candidates.index)
        for k in sorted(dn4000_bin.dropna().unique()):
            members = candidates[dn4000_bin == k]
            key = f"{name}{int(k)}" if name.startswith("balmer") else name
            membership.append(pd.DataFrame({"target": members.target, "group": key, "role": "candidate"}))
            for pool_name, pool in pools.items():
                matches = match_controls(members, pool, rng)
                targets = [t for controls in matches.values() for t in controls]
                membership.append(pd.DataFrame({"target": targets, "group": key, "role": pool_name}))
    membership = pd.concat(membership, ignore_index=True)

    stacked = (
        galaxies[galaxies.target.isin(set(membership.target))].sort_values("target").reset_index(drop=True)
    )
    position = pd.Series(stacked.index, index=stacked.target)
    rows = load_exposures(stacked)
    matrices = galaxy_matrices(rows, stacked)
    groups = {}
    for (group, role), members in membership.groupby(["group", "role"]):
        groups[f"{group}__{role}"] = position[members.target].to_numpy()
    for role in ("candidate", "quiescent", "population"):
        for prefix in ("e_plus_a", "balmer_excess", "balmer_deficit"):
            members = membership[(membership.role == role) & membership.group.str.startswith(prefix)]
            groups[f"{prefix}_all__{role}"] = position[members.target.unique()].to_numpy()
    table, profiles = stack_groups(groups, stacked, matrices, rng)
    table[["set", "role"]] = table.group.str.split("__", expand=True)

    extra = []
    for group, members in membership.groupby("group"):
        candidates = stacked.set_index("target").loc[members.target[members.role == "candidate"]]
        for role in ("quiescent", "population"):
            controls = stacked.set_index("target").loc[members.target[members.role == role]]
            extra.append({"set": group, "role": role} | match_quality(candidates, controls))
    quality = pd.DataFrame(extra)

    medians = stacked.set_index("target")[["axis_ratio_r", "petrosian_r50_arcsec", "hdelta_excess"]]
    for column in medians.columns:
        table[f"{column}_median"] = [
            float(medians.loc[stacked.target.to_numpy()[groups[g]], column].median()) for g in table.group
        ]
    table.to_parquet(OUT_DIR / "psb_stacks.parquet")
    np.savez_compressed(OUT_DIR / "psb_profiles.npz", **profiles)
    membership.merge(
        stacked[
            ["target", "d4000_n_sub", "lick_hd_a_sub", "hdelta_excess", "halpha_emission_ew", "redshift"]
        ],
        on="target",
    ).to_parquet(OUT_DIR / "psb_galaxies.parquet")

    show = [
        "group",
        "n_galaxies",
        "dn4000_median",
        "hdelta_a_median",
        "halpha_emission_ew_median",
        "log_ssfr_median",
        "individual_index_mean",
        "stack_sed_index",
        "stack_continuum_index",
        "stack_continuum_index_err",
    ]
    with pd.option_context("display.width", 250):
        print(table[show].round(4).to_string(index=False))
        print(quality.round(4).to_string(index=False))
    contrasts = {}
    wide = table.set_index(["set", "role"])
    for name in table.set.unique():
        for role in ("quiescent", "population"):
            if (name, role) in wide.index:
                a, b = wide.loc[(name, "candidate")], wide.loc[(name, role)]
                contrasts[f"{name} minus {role}"] = {
                    "stack_continuum": float(a.stack_continuum_index - b.stack_continuum_index),
                    "err": float(np.hypot(a.stack_continuum_index_err, b.stack_continuum_index_err)),
                    "stack_sed": float(a.stack_sed_index - b.stack_sed_index),
                    "individual_mean": float(a.individual_index_mean - b.individual_index_mean),
                }
    print(json.dumps(contrasts, indent=1))
    summary = {
        "set_sizes": galaxies.set.value_counts().to_dict(),
        "contrasts": contrasts,
        "match_quality": quality.to_dict(orient="records"),
    }
    with open(OUT_DIR / "psb_summary.json", "w") as handle:
        json.dump(summary, handle, indent=2, default=float)


if __name__ == "__main__":
    main()
