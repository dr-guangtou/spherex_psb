"""Stacked SPHEREx SEDs and H-minus bump of the SDSS 48k galaxies in cells of the Dn4000-HdeltaA plane.

The SDSS indices are taken as they are (MPA-JHU DR8, emission-subtracted, as in the input catalogue).

Sample: galaxies with a measured bump index (`measure_hminus_bump.py`), outside the Magellanic Clouds, minus
the 1 % in the sparsest parts of the Dn4000-HdeltaA plane (smoothed 2-D histogram, the density at each galaxy
below the 1st percentile of all galaxies' densities).

Cells: Dn4000 cut at its quantiles into `N_DN4000_BINS`, then within each Dn4000 bin HdeltaA cut at its own
quantiles into `N_HDELTA_BINS`: equal numbers per cell, and the HdeltaA bins run from below to above the
sequence at each Dn4000 (post-starburst light is the top HdeltaA bin at intermediate Dn4000).

Exposures: aperture flux (`aper_flux_uJy`) times the Solid Angle Pixel Map factor (as for the index),
corrected for Galactic extinction (`ebv` of the run, the Schlafly & Finkbeiner 2011 scaling of SFD; Gordon
et al. 2023 curve, R_V = 3.1, at the observed wavelength), F_lambda = F_nu / lambda_rest^2.

Two stacks per cell, as asked:
1. Whole SED. Each galaxy is normalised by the median F_lambda of its exposures at rest 1.10-1.25 um (no
   strong lines; Pa-gamma 1.094 and [Fe II] 1.257 um are outside). Per galaxy the mean in each rest bin
   (ln lambda step 0.01, 0.70-4.90 um); per cell and bin the mean over galaxies after clipping galaxies more
   than 5 robust sigma from the bin median. The bump index of this stack is measured on a 0.005 um grid over
   1.44-1.84 um built the same way.
2. Bump only. Each galaxy's exposures at rest 1.44-1.84 um are screened exactly as for its own index
   (quadratic, 5 robust sigma) and divided by its own straight-line pseudo-continuum (band means of the blue
   and red windows); the ratios are stacked on the 0.005 um grid as above. The index of this stack uses the
   pseudo-continuum of the stacked profile.
For both, the index is measured on the stacked profile with every grid bin weighted equally in wavelength
(the stack is close to continuous sampling at the SPHEREx resolution). Errors: bootstrap over galaxies.

The same stacks for all galaxies and for the three redshift thirds (a feature fixed in the observed frame
would move in rest wavelength between them). Also per cell: mean and median of the galaxies' own indices;
median redshift, stellar mass, sSFR (galSpecExtra), Halpha equivalent width (galSpecLine), BPT class
fractions, and the mean SPHEREx sampling bias of a 5 Gyr TP-AGB-on template (`check_model_comparability.py`).

usage: uv run python scripts/sdss48k_review/stack_sed_and_bump.py [--max-galaxies N]
Output: <results>/sdss48k_hminus/stack_{cells,membership}.parquet, stack_profiles.npz, stack_summary.json
"""

from __future__ import annotations

import argparse
import json
import sys
import warnings
from pathlib import Path

import astropy.units as u
import numpy as np
import pandas as pd
import pyarrow.dataset as ds
from astropy.io import fits
from dust_extinction.parameter_averages import G23
from scipy.ndimage import gaussian_filter

sys.path.insert(0, str(Path(__file__).resolve().parent))
from measure_hminus_bump import (  # noqa: E402
    CONSTANT_PIXEL_ARCSEC2,
    FIT_RANGE_UM,
    MAGNITUDE,
    OUT_DIR,
    RUN_DIR,
    WINDOWS_UM,
    load_solid_angle_maps,
    screen,
)

MPA_DIR = Path("/Users/shuang/data/mpa")
N_DN4000_BINS, N_HDELTA_BINS = 8, 5
SPARSE_FRACTION = 0.01
PLANE_RANGE = {"dn4000": (1.0, 2.35), "hdelta": (-5.5, 8.5)}
NORMALISATION_WINDOW_UM = (1.10, 1.25)
SED_LN_STEP = 0.01
SED_RANGE_UM = (0.70, 4.90)
BUMP_STEP_UM = 0.005
CLIP_SIGMA = 5.0
N_BOOTSTRAP = 300
R_V = 3.1
BPT_NAMES = {
    1: "star forming",
    2: "low S/N star forming",
    3: "composite",
    4: "AGN",
    5: "low S/N LINER",
    -1: "none",
}
EXPOSURE_COLUMNS = [
    "target",
    "detector_id",
    "mjd_avg",
    "wv_um",
    "aper_flux_uJy",
    "xpix_fulldet",
    "ypix_fulldet",
]


def mpa_columns(file_name: str, columns: list[str], specobjids: pd.Series) -> pd.DataFrame:
    with fits.open(MPA_DIR / file_name, memmap=True) as hdul:
        data = hdul[1].data
        table = pd.DataFrame(
            {
                name: np.asarray(data[name]).astype(data[name].dtype.newbyteorder("="))
                for name in ["SPECOBJID", *columns]
            }
        )
    table["specobjid"] = pd.to_numeric(pd.Series(table.SPECOBJID).astype(str).str.strip(), errors="coerce")
    table = table.dropna(subset=["specobjid"]).astype({"specobjid": np.int64})
    table = table[table.specobjid.isin(set(specobjids))].drop_duplicates("specobjid")
    return table.drop(columns="SPECOBJID").rename(columns=str.lower)


def load_galaxies() -> pd.DataFrame:
    """Galaxies with a measured index, with MPA-JHU class, sSFR, Halpha, extinction and sampling bias."""
    galaxies = pd.read_parquet(OUT_DIR / "hminus_bump_indices.parquet")
    galaxies = galaxies[np.isfinite(galaxies.hminus_bump_mag)]
    for file_name, columns in [
        ("galSpecExtra-dr8.fits", ["BPTCLASS", "SPECSFR_TOT_P50"]),
        ("galSpecLine-dr8.fits", ["H_ALPHA_EQW", "H_ALPHA_EQW_ERR"]),
        ("galSpecInfo-dr8.fits", ["V_DISP"]),
    ]:
        galaxies = galaxies.merge(
            mpa_columns(file_name, columns, galaxies.specobjid), on="specobjid", how="left"
        )
    ebv = pd.read_parquet(f"{RUN_DIR}/ebv.parquet", columns=["target", "ebv"])
    galaxies = galaxies.merge(ebv, on="target", how="left")
    bias = pd.read_parquet(OUT_DIR / "model_check_sampling_bias.parquet", columns=["target", "bias_on_5gyr"])
    return galaxies.merge(bias, on="target", how="left")


def plane_density(dn4000: np.ndarray, hdelta: np.ndarray, bins: int = 80, smooth: float = 1.5) -> np.ndarray:
    """Smoothed 2-D histogram density of the Dn4000-HdeltaA plane at each galaxy."""
    counts, x_edges, y_edges = np.histogram2d(
        dn4000, hdelta, bins=bins, range=[PLANE_RANGE["dn4000"], PLANE_RANGE["hdelta"]]
    )
    counts = gaussian_filter(counts, smooth)
    i = np.clip(np.searchsorted(x_edges, dn4000) - 1, 0, bins - 1)
    j = np.clip(np.searchsorted(y_edges, hdelta) - 1, 0, bins - 1)
    return counts[i, j]


def assign_cells(galaxies: pd.DataFrame) -> pd.DataFrame:
    galaxies = galaxies.copy()
    galaxies["dn4000_bin"] = pd.qcut(galaxies.d4000_n_sub, N_DN4000_BINS, labels=False)
    galaxies["hdelta_bin"] = galaxies.groupby("dn4000_bin").lick_hd_a_sub.transform(
        lambda values: pd.qcut(values, N_HDELTA_BINS, labels=False)
    )
    galaxies["cell"] = galaxies.dn4000_bin * N_HDELTA_BINS + galaxies.hdelta_bin
    return galaxies


def load_exposures(
    galaxies: pd.DataFrame, extra_columns: tuple[str, ...] = (), correct_extinction: bool = True
) -> pd.DataFrame:
    """Corrected F_lambda of every exposure of the given galaxies, sorted by galaxy and rest wavelength."""
    dataset = ds.dataset(f"{RUN_DIR}/photometry.parquet")
    table = dataset.to_table(
        columns=EXPOSURE_COLUMNS + list(extra_columns),
        filter=ds.field("target").isin(galaxies.target.to_numpy()),
    )
    rows = table.to_pandas()
    rows = rows.merge(galaxies[["target", "redshift", "ebv"]], on="target", how="inner")
    rows["rest_um"] = rows.wv_um / (1 + rows.redshift)
    maps = load_solid_angle_maps()
    column = np.clip(np.round(rows.xpix_fulldet.to_numpy()).astype(int), 0, 2039)
    row = np.clip(np.round(rows.ypix_fulldet.to_numpy()).astype(int), 0, 2039)
    solid_angle = np.empty(len(rows))
    for detector, sapm in maps.items():
        on = rows.detector_id.to_numpy() == detector
        solid_angle[on] = sapm[row[on], column[on]]
    extinction_ratio = G23(Rv=R_V)(rows.wv_um.to_numpy() * u.micron)  # A_lambda / A_V
    a_lambda = extinction_ratio * R_V * rows.ebv.to_numpy() if correct_extinction else 0.0
    rows["flux_lambda"] = (
        rows.aper_flux_uJy * solid_angle / CONSTANT_PIXEL_ARCSEC2 * 10 ** (0.4 * a_lambda) / rows.rest_um**2
    )
    rows = rows[np.isfinite(rows.flux_lambda)]
    return rows.sort_values(["target", "rest_um"]).reset_index(drop=True)


def binned_means(
    galaxy_index: np.ndarray, bin_index: np.ndarray, values: np.ndarray, n_galaxies: int, n_bins: int
):
    """Per-galaxy mean in each bin, NaN where a galaxy has no exposure."""
    inside = (bin_index >= 0) & (bin_index < n_bins) & np.isfinite(values)
    flat = galaxy_index[inside] * n_bins + bin_index[inside]
    sums = np.bincount(flat, weights=values[inside], minlength=n_galaxies * n_bins)
    counts = np.bincount(flat, minlength=n_galaxies * n_bins)
    with np.errstate(invalid="ignore", divide="ignore"):
        means = sums / counts
    return means.reshape(n_galaxies, n_bins).astype(np.float32)


def clipped_stack(matrix: np.ndarray, rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Mean over galaxies per bin after clipping at CLIP_SIGMA robust sigma, and bootstrap stacks."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        median = np.nanmedian(matrix, axis=0)
        sigma = 1.4826 * np.nanmedian(np.abs(matrix - median), axis=0)
        clipped = np.where(np.abs(matrix - median) <= CLIP_SIGMA * sigma, matrix, np.nan)
        stack = np.nanmean(clipped, axis=0)
        n_galaxies = clipped.shape[0]
        boots = np.stack(
            [np.nanmean(clipped[rng.integers(0, n_galaxies, n_galaxies)], axis=0) for _ in range(N_BOOTSTRAP)]
        )
    return stack, boots, np.isfinite(clipped).sum(axis=0)


def profile_index(centres: np.ndarray, profile: np.ndarray) -> np.ndarray:
    """Hbump_opt on a profile sampled on a uniform grid; works on the last axis of a stack of profiles."""
    member = {key: (centres >= lo) & (centres <= hi) for key, (lo, hi) in WINDOWS_UM.items()}
    blue = profile[..., member["blue"]].mean(axis=-1, keepdims=True)
    red = profile[..., member["red"]].mean(axis=-1, keepdims=True)
    blue_mid, red_mid = (0.5 * sum(WINDOWS_UM[key]) for key in ("blue", "red"))
    fraction = (centres[member["feature"]] - blue_mid) / (red_mid - blue_mid)
    continuum = blue * (1 - fraction) + red * fraction
    return -MAGNITUDE * np.log(np.mean(profile[..., member["feature"]] / continuum, axis=-1))


def galaxy_matrices(rows: pd.DataFrame, galaxies: pd.DataFrame) -> dict:
    """Per-galaxy binned normalised SED and continuum-normalised bump profile."""
    order = {target: k for k, target in enumerate(galaxies.target)}
    galaxy_index = rows.target.map(order).to_numpy()
    n_galaxies = len(galaxies)
    rest, flux = rows.rest_um.to_numpy(), rows.flux_lambda.to_numpy()

    window = (rest >= NORMALISATION_WINDOW_UM[0]) & (rest <= NORMALISATION_WINDOW_UM[1])
    norm = (
        pd.Series(flux[window])
        .groupby(galaxy_index[window])
        .median()
        .reindex(range(n_galaxies))
        .to_numpy(copy=True)
    )
    n_norm = np.bincount(galaxy_index[window], minlength=n_galaxies)
    norm[(n_norm < 3) | ~(norm > 0)] = np.nan
    normalised = flux / norm[galaxy_index]

    sed_edges = np.arange(np.log(SED_RANGE_UM[0]), np.log(SED_RANGE_UM[1]) + 1e-9, SED_LN_STEP)
    sed_bin = np.floor((np.log(rest) - sed_edges[0]) / SED_LN_STEP).astype(int)
    sed = binned_means(galaxy_index, sed_bin, normalised, n_galaxies, len(sed_edges) - 1)

    bump_edges = np.arange(FIT_RANGE_UM[0], FIT_RANGE_UM[1] + 1e-9, BUMP_STEP_UM)
    n_bump = len(bump_edges) - 1
    in_fit = (rest >= FIT_RANGE_UM[0]) & (rest <= FIT_RANGE_UM[1])
    ratio = np.full(len(rows), np.nan)
    kept = np.zeros(len(rows), dtype=bool)
    fit_index = np.flatnonzero(in_fit)
    targets_fit = galaxy_index[fit_index]
    starts = np.flatnonzero(np.r_[True, targets_fit[1:] != targets_fit[:-1]])
    stops = np.r_[starts[1:], len(fit_index)]
    blue_mid, red_mid = (0.5 * sum(WINDOWS_UM[key]) for key in ("blue", "red"))
    for start, stop in zip(starts, stops, strict=True):
        index = fit_index[start:stop]
        keep, _, _ = screen(rest[index], flux[index])
        good = index[keep]
        kept[good] = True
        blue_member = (rest[good] >= WINDOWS_UM["blue"][0]) & (rest[good] <= WINDOWS_UM["blue"][1])
        red_member = (rest[good] >= WINDOWS_UM["red"][0]) & (rest[good] <= WINDOWS_UM["red"][1])
        if blue_member.sum() < 2 or red_member.sum() < 2:
            continue
        blue, red = flux[good][blue_member].mean(), flux[good][red_member].mean()
        fraction = (rest[good] - blue_mid) / (red_mid - blue_mid)
        ratio[good] = flux[good] / (blue * (1 - fraction) + red * fraction)
    bump_bin = np.floor((rest - bump_edges[0]) / BUMP_STEP_UM).astype(int)
    bump_bin[~kept] = -1
    return {
        "sed_centres_um": np.exp(0.5 * (sed_edges[1:] + sed_edges[:-1])),
        "sed": sed,
        "bump_centres_um": 0.5 * (bump_edges[1:] + bump_edges[:-1]),
        "bump_sed": binned_means(galaxy_index, bump_bin, normalised, n_galaxies, n_bump),
        "bump_continuum": binned_means(galaxy_index, bump_bin, ratio, n_galaxies, n_bump),
        "norm_found": np.isfinite(norm),
    }


def cell_properties(members: pd.DataFrame) -> dict:
    bpt = members.bptclass.value_counts(normalize=True)
    halpha_emission = -members.h_alpha_eqw  # MPA-JHU equivalent widths are negative for emission
    individual = members.hminus_bump_mag
    return {
        "n_galaxies": len(members),
        "dn4000_median": members.d4000_n_sub.median(),
        "hdelta_a_median": members.lick_hd_a_sub.median(),
        "dn4000_range": (members.d4000_n_sub.min(), members.d4000_n_sub.max()),
        "hdelta_a_range": (members.lick_hd_a_sub.min(), members.lick_hd_a_sub.max()),
        "redshift_median": members.redshift.median(),
        "log_stellar_mass_median": members.log_stellar_mass_msun.median(),
        "log_ssfr_median": members.specsfr_tot_p50.median(),
        "halpha_emission_ew_median": halpha_emission.median(),
        "fraction_star_forming": float(bpt.get(1, 0) + bpt.get(2, 0)),
        "fraction_composite": float(bpt.get(3, 0)),
        "fraction_agn_liner": float(bpt.get(4, 0) + bpt.get(5, 0)),
        "fraction_no_lines": float(bpt.get(-1, 0)),
        "individual_index_mean": individual.mean(),
        "individual_index_mean_err": individual.std(ddof=1) / np.sqrt(len(members)),
        "individual_index_median": individual.median(),
        "individual_index_median_err": 1.2533 * individual.std(ddof=1) / np.sqrt(len(members)),
        "sampling_bias_on_5gyr_mean": members.bias_on_5gyr.mean(),
    }


def stack_groups(
    groups: dict, galaxies: pd.DataFrame, matrices: dict, rng: np.random.Generator
) -> tuple[pd.DataFrame, dict]:
    """Both stacks, their indices and the members' properties for each group of galaxy row positions.
    Integer group names are cells (key `cellNN`); string names are used as keys."""
    bump_centres = matrices["bump_centres_um"]
    profiles = {"sed_centres_um": matrices["sed_centres_um"], "bump_centres_um": bump_centres}
    records = []
    for name, index in groups.items():
        sed, sed_boot, sed_n = clipped_stack(matrices["sed"][index], rng)
        bump_sed, bump_sed_boot, _ = clipped_stack(matrices["bump_sed"][index], rng)
        bump_cont, bump_cont_boot, bump_n = clipped_stack(matrices["bump_continuum"][index], rng)
        is_cell = isinstance(name, int)
        key = f"cell{name:02d}" if is_cell else name
        profiles |= {
            f"{key}_sed": sed,
            f"{key}_sed_err": np.nanstd(sed_boot, axis=0, ddof=1),
            f"{key}_sed_n": sed_n,
            f"{key}_bump_sed": bump_sed,
            f"{key}_bump_sed_err": np.nanstd(bump_sed_boot, axis=0, ddof=1),
            f"{key}_bump_continuum": bump_cont,
            f"{key}_bump_continuum_err": np.nanstd(bump_cont_boot, axis=0, ddof=1),
            f"{key}_bump_n": bump_n,
        }
        members = galaxies.loc[index]
        record = {"group": key, "cell": name if is_cell else -1}
        if is_cell:
            record |= {
                "dn4000_bin": int(members.dn4000_bin.iloc[0]),
                "hdelta_bin": int(members.hdelta_bin.iloc[0]),
            }
        record |= cell_properties(members)
        record |= {
            "stack_sed_index": float(profile_index(bump_centres, bump_sed)),
            "stack_sed_index_err": float(np.nanstd(profile_index(bump_centres, bump_sed_boot), ddof=1)),
            "stack_continuum_index": float(profile_index(bump_centres, bump_cont)),
            "stack_continuum_index_err": float(
                np.nanstd(profile_index(bump_centres, bump_cont_boot), ddof=1)
            ),
        }
        records.append(record)
    return pd.DataFrame(records), profiles


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-galaxies", type=int, default=None, help="random subset for a quick test")
    args = parser.parse_args()
    rng = np.random.default_rng(1)

    galaxies = load_galaxies()
    n_measured = len(galaxies)
    galaxies = galaxies[~galaxies.in_magellanic.astype(bool)]
    density = plane_density(galaxies.d4000_n_sub.to_numpy(), galaxies.lick_hd_a_sub.to_numpy())
    sparse = density < np.quantile(density, SPARSE_FRACTION)
    print(
        f"measured {n_measured:,}; outside the Magellanic Clouds {len(galaxies):,};",
        f"sparse removed {sparse.sum():,}",
    )
    galaxies = galaxies[~sparse]
    if args.max_galaxies:
        galaxies = galaxies.sample(args.max_galaxies, random_state=0)
    galaxies = assign_cells(galaxies).sort_values("target").reset_index(drop=True)
    print(
        f"stacked galaxies {len(galaxies):,}; per cell",
        galaxies.cell.value_counts().min(),
        "to",
        galaxies.cell.value_counts().max(),
    )

    rows = load_exposures(galaxies)
    print(f"exposures {len(rows):,}")
    matrices = galaxy_matrices(rows, galaxies)
    print(f"galaxies with a normalisation {matrices['norm_found'].sum():,}")

    redshift_third = pd.qcut(galaxies.redshift, 3, labels=False)
    groups = {"all": galaxies.index.to_numpy()}
    groups |= {f"redshift{k + 1}": galaxies.index[redshift_third == k].to_numpy() for k in range(3)}
    groups |= {int(cell): members.index.to_numpy() for cell, members in galaxies.groupby("cell")}
    cells, profiles = stack_groups(groups, galaxies, matrices, rng)
    suffix = "_test" if args.max_galaxies else ""
    cells.to_parquet(OUT_DIR / f"stack_cells{suffix}.parquet")
    galaxies[["target", "specobjid", "dn4000_bin", "hdelta_bin", "cell"]].to_parquet(
        OUT_DIR / f"stack_membership{suffix}.parquet"
    )
    np.savez_compressed(OUT_DIR / f"stack_profiles{suffix}.npz", **profiles)

    show = cells[
        [
            "group",
            "n_galaxies",
            "dn4000_median",
            "hdelta_a_median",
            "log_ssfr_median",
            "halpha_emission_ew_median",
            "fraction_star_forming",
            "individual_index_mean",
            "individual_index_median",
            "stack_sed_index",
            "stack_sed_index_err",
            "stack_continuum_index",
            "stack_continuum_index_err",
            "sampling_bias_on_5gyr_mean",
        ]
    ]
    print(show.round(4).to_string(index=False))
    differences = cells[cells.cell >= 0]
    summary = {
        "n_measured": n_measured,
        "n_stacked": len(galaxies),
        "n_sparse_removed": int(sparse.sum()),
        "cells": f"{N_DN4000_BINS} Dn4000 x {N_HDELTA_BINS} HdeltaA",
        "galaxies_per_cell_range": [int(differences.n_galaxies.min()), int(differences.n_galaxies.max())],
        "stack_continuum_minus_individual_mean_range": [
            float((differences.stack_continuum_index - differences.individual_index_mean).min()),
            float((differences.stack_continuum_index - differences.individual_index_mean).max()),
        ],
        "stack_sed_minus_stack_continuum_range": [
            float((differences.stack_sed_index - differences.stack_continuum_index).min()),
            float((differences.stack_sed_index - differences.stack_continuum_index).max()),
        ],
    }
    with open(OUT_DIR / f"stack_summary{suffix}.json", "w") as handle:
        json.dump(summary, handle, indent=2)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
