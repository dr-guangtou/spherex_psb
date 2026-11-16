"""Strong H-minus bump outliers among the individual SDSS 48k measurements: scatter, systematics or real?

Selection. Each galaxy's index minus the running median at its Dn4000 (bins of 0.05) is its residual; divided
by the quadrature sum of its error and the population's intrinsic spread (robust spread of the residuals minus
the median error in quadrature) it is the significance s. Four outlier sets, each with its mirror on the
weak-bump side as the reference for what noise and symmetric systematics do:
- apparent: residual below -0.06 mag (strong) or above +0.06 mag (weak), about 1 % of galaxies on each side;
  what stands out in a plot of the individual indices;
- significant: s < -3 (strong) or s > +3 (weak).
Controls: three galaxies with |s| < 2 per strong outlier (apparent or significant), drawn in the same redshift
(0.0025) and Dn4000 (0.1) cell. A galaxy can be in more than one set (boolean columns).

Diagnostics per galaxy (all sets):
1. Visit jackknife: exposures are grouped by observing day (one visit); the index is recomputed without each
   visit; `significance_without_worst_visit` uses the drop that moves the index most towards the median.
2. Independent halves: visits sorted in time and given alternately to half A and half B; the index of each
   half (>= 1 exposure per side window, >= 3 in the feature) and the consistency (A - B) / error.
3. Detectors and calibration: fraction of window exposures per detector; the D3-D2 flux step where both
   detectors overlap (from `measure_hminus_bump.py`).
4. Data quality: per-exposure scatter, rejected exposures, aperture flux and its signal-to-noise, local
   background, flagged pixels (of the PSF fit), ecliptic and Galactic latitude, E(B-V).
5. Neighbours: SDSS DR17 PhotoPrimary objects within 20 arcsec (SkyServer, batched); the z-band flux of all
   objects other than the galaxy within the 12.3 arcsec aperture and within 12.3-20 arcsec, relative to the
   galaxy's; the brightest star. Shape, for all galaxies: r-band axis ratio (exponential or de Vaucouleurs
   fit, by fracDeV) and Petrosian radii of the spectrum's photometric object. Both cached in the results
   folder; the index residual and the outlier rates against axis ratio and size are in the summary.
6. Optical: BPT class, sSFR, Halpha equivalent width, stellar mass, velocity dispersion.
The kept exposures of these galaxies in the fit window, divided by their pseudo-continuum, are saved for
stacking in the rest and the observed frame.

usage: uv run python scripts/sdss48k_review/investigate_bump_outliers.py
Output: <results>/sdss48k_hminus/outlier_{galaxies,exposures,neighbours}.parquet, outlier_summary.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import astropy.units as u
import numpy as np
import pandas as pd
from astropy.coordinates import SkyCoord
from scipy.stats import norm

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from measure_hminus_bump import FIT_RANGE_UM, OUT_DIR, WINDOWS_UM, index_and_error, screen  # noqa: E402
from stack_sed_and_bump import load_exposures, load_galaxies  # noqa: E402

from spherex_psb.extraction.catalog import _skyserver  # noqa: E402

APPARENT_LIMIT_MAG = 0.06
SIGNIFICANCE_LIMIT = 3.0
CONTROL_LIMIT = 2.0
CONTROLS_PER_OUTLIER = 3
DN4000_STEP = 0.05
MATCH_STEPS = {"redshift": 0.0025, "d4000_n_sub": 0.1}
APERTURE_RADIUS_ARCSEC = 12.3
NEIGHBOUR_RADIUS_ARCSEC = 20.0
SELF_MATCH_ARCSEC = 3.0
SKYSERVER_BATCH = 150
EXTRA_COLUMNS = ("wv_width_um", "aper_flux_uJy_err", "bkg_MJysr", "n_pix_flagged")


def robust_sigma(values: np.ndarray) -> float:
    return float(1.4826 * np.median(np.abs(values - np.median(values))))


def significance(galaxies: pd.DataFrame) -> tuple[pd.DataFrame, float]:
    edges = np.arange(1.0, 2.4 + DN4000_STEP, DN4000_STEP)
    bins = np.digitize(galaxies.d4000_n_sub, edges)
    galaxies = galaxies.assign(
        index_median_at_dn4000=galaxies.groupby(bins).hminus_bump_mag.transform("median")
    )
    galaxies["index_residual"] = galaxies.hminus_bump_mag - galaxies.index_median_at_dn4000
    intrinsic = float(
        np.sqrt(robust_sigma(galaxies.index_residual) ** 2 - np.median(galaxies.hminus_bump_err_mag) ** 2)
    )
    galaxies["significance"] = galaxies.index_residual / np.hypot(galaxies.hminus_bump_err_mag, intrinsic)
    return galaxies, intrinsic


def choose_groups(galaxies: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    """One row per selected galaxy with a boolean column per set."""
    flags = pd.DataFrame(
        {
            "strong_apparent": galaxies.index_residual < -APPARENT_LIMIT_MAG,
            "weak_apparent": galaxies.index_residual > APPARENT_LIMIT_MAG,
            "strong_significant": galaxies.significance < -SIGNIFICANCE_LIMIT,
            "weak_significant": galaxies.significance > SIGNIFICANCE_LIMIT,
        }
    )
    strong = galaxies[flags.strong_apparent | flags.strong_significant]
    pool = galaxies[galaxies.significance.abs() < CONTROL_LIMIT]

    def cell_key(frame):
        return list(
            zip(*[np.floor(frame[c] / step).astype(int) for c, step in MATCH_STEPS.items()], strict=True)
        )

    pool_cells = pd.Series(cell_key(pool), index=pool.index)
    used = set()
    for key in cell_key(strong):
        candidates = [i for i in pool_cells.index[pool_cells == key] if i not in used]
        used.update(rng.choice(candidates, size=min(CONTROLS_PER_OUTLIER, len(candidates)), replace=False))
    flags["control"] = galaxies.index.isin(sorted(used))
    selected = flags.any(axis=1)
    return pd.concat([galaxies[selected], flags[selected]], axis=1).reset_index(drop=True)


def visit_and_half_tests(rest, flux, day, scatter, median_index, intrinsic) -> dict:
    out = {}
    visits = np.unique(day)
    out["n_visits"] = len(visits)
    feature = (rest >= WINDOWS_UM["feature"][0]) & (rest <= WINDOWS_UM["feature"][1])
    out["n_visits_feature"] = len(np.unique(day[feature]))
    full = index_and_error(rest, flux, scatter)["hminus_bump_mag"]
    best = (np.nan, np.nan)
    for visit in visits:
        keep = day != visit
        result = index_and_error(rest[keep], flux[keep], scatter)
        moved = abs(result["hminus_bump_mag"] - median_index) - abs(full - median_index)
        if np.isfinite(moved) and (not np.isfinite(best[0]) or moved < best[0]):
            best = (moved, result)
    if np.isfinite(best[0]):
        result = best[1]
        out["index_without_worst_visit"] = result["hminus_bump_mag"]
        out["significance_without_worst_visit"] = (result["hminus_bump_mag"] - median_index) / np.hypot(
            result["hminus_bump_err_mag"], intrinsic
        )
    half_of_visit = {visit: k % 2 for k, visit in enumerate(visits)}
    half = np.array([half_of_visit[d] for d in day])
    for label, value in (("a", 0), ("b", 1)):
        result = index_and_error(rest[half == value], flux[half == value], scatter, min_side=1, min_feature=3)
        out[f"index_half_{label}"] = result["hminus_bump_mag"]
        out[f"index_half_{label}_err"] = result["hminus_bump_err_mag"]
    out["halves_consistency"] = (out["index_half_a"] - out["index_half_b"]) / np.hypot(
        out["index_half_a_err"], out["index_half_b_err"]
    )
    return out


def per_galaxy_diagnostics(groups: pd.DataFrame, exposures: pd.DataFrame, intrinsic: float):
    records, kept_rows = [], []
    by_target = groups.set_index("target")
    for target, rows in exposures.groupby("target", sort=False):
        rows = rows[(rows.rest_um >= FIT_RANGE_UM[0]) & (rows.rest_um <= FIT_RANGE_UM[1])]
        rest, flux = rows.rest_um.to_numpy(), rows.flux_lambda.to_numpy()
        keep, _, scatter = screen(rest, flux)
        rows, rest, flux = rows[keep], rest[keep], flux[keep]
        galaxy = by_target.loc[target]
        record = {
            "target": target,
            "index_recomputed": index_and_error(rest, flux, scatter)["hminus_bump_mag"],
        }
        record |= visit_and_half_tests(
            rest, flux, np.floor(rows.mjd_avg.to_numpy()), scatter, galaxy.index_median_at_dn4000, intrinsic
        )
        for window, (lo, hi) in WINDOWS_UM.items():
            inside = (rest >= lo) & (rest <= hi)
            for detector in (2, 3):
                record[f"fraction_{window}_d{detector}"] = (
                    float((rows.detector_id.to_numpy()[inside] == detector).mean())
                    if inside.any()
                    else np.nan
                )
        record |= {
            "aperture_flux_median_ujy": float(rows.aper_flux_uJy.median()),
            "aperture_snr_median": float((rows.aper_flux_uJy / rows.aper_flux_uJy_err).median()),
            "background_median_mjy_sr": float(rows.bkg_MJysr.median()),
            "flagged_pixels_median": float(rows.n_pix_flagged.median()),
        }
        records.append(record)
        blue_mid, red_mid = (0.5 * sum(WINDOWS_UM[key]) for key in ("blue", "red"))
        blue = flux[(rest >= WINDOWS_UM["blue"][0]) & (rest <= WINDOWS_UM["blue"][1])].mean()
        red = flux[(rest >= WINDOWS_UM["red"][0]) & (rest <= WINDOWS_UM["red"][1])].mean()
        fraction = (rest - blue_mid) / (red_mid - blue_mid)
        kept_rows.append(
            pd.DataFrame(
                {
                    "target": target,
                    "rest_um": rest,
                    "observed_um": rows.wv_um.to_numpy(),
                    "detector_id": rows.detector_id.to_numpy(),
                    "day": np.floor(rows.mjd_avg.to_numpy()),
                    "ratio_to_continuum": flux / (blue * (1 - fraction) + red * fraction),
                }
            )
        )
    return pd.DataFrame(records), pd.concat(kept_rows, ignore_index=True)


def query_neighbours(groups: pd.DataFrame) -> pd.DataFrame:
    cache = OUT_DIR / "outlier_neighbours.parquet"
    cached = pd.read_parquet(cache) if cache.exists() else pd.DataFrame(columns=["target"])
    todo = groups[~groups.target.isin(set(cached.target))].drop_duplicates("target")
    tables = [cached]
    for start in range(0, len(todo), SKYSERVER_BATCH):
        chunk = todo.iloc[start : start + SKYSERVER_BATCH]
        values = ", ".join(
            f"({int(t)}, {ra:.6f}, {dec:.6f})"
            for t, ra, dec in zip(chunk.target, chunk.ra_deg, chunk.dec_deg, strict=True)
        )
        query = f"""SELECT t.target, p.objID, p.type, p.modelMag_z, n.distance * 60 AS sep_arcsec
            FROM (VALUES {values}) AS t(target, ra, dec)
            CROSS APPLY dbo.fGetNearbyObjEq(t.ra, t.dec, {NEIGHBOUR_RADIUS_ARCSEC / 60.0}) AS n
            JOIN PhotoPrimary p ON p.objID = n.objID"""
        table = _skyserver(query)
        missing = set(chunk.target) - set(table.target) if not table.empty else set(chunk.target)
        empty = pd.DataFrame({"target": sorted(missing)})  # no SDSS object at all: keep as queried
        tables.append(pd.concat([table, empty], ignore_index=True))
        print(f"SkyServer batch {start // SKYSERVER_BATCH + 1}: {len(table)} objects", flush=True)
    neighbours = pd.concat(tables, ignore_index=True)
    neighbours.to_parquet(cache)
    return neighbours


def neighbour_metrics(neighbours: pd.DataFrame) -> pd.DataFrame:
    records = []
    for target, objects in neighbours.groupby("target"):
        objects = objects.dropna(subset=["objID"]).sort_values("sep_arcsec")
        record = {"target": target, "self_found": False}
        if objects.empty or objects.sep_arcsec.iloc[0] > SELF_MATCH_ARCSEC:
            records.append(record)
            continue
        self_mag = objects.modelMag_z.iloc[0]
        others = objects.iloc[1:]
        others = others[(others.modelMag_z > 0) & (others.modelMag_z < 30)]
        relative = 10 ** (-0.4 * (others.modelMag_z - self_mag))
        inside = others.sep_arcsec <= APERTURE_RADIUS_ARCSEC
        stars = others[others["type"] == 6]
        record |= {
            "self_found": True,
            "self_mag_z": self_mag,
            "neighbour_flux_ratio_aperture": float(relative[inside].sum()),
            "neighbour_flux_ratio_annulus": float(relative[~inside].sum()),
            "n_neighbours_aperture_brighter_than_z21": int((inside & (others.modelMag_z < 21)).sum()),
            "brightest_star_relative_mag": float((stars.modelMag_z - self_mag).min())
            if len(stars)
            else np.nan,
            "brightest_star_sep_arcsec": float(stars.sort_values("modelMag_z").sep_arcsec.iloc[0])
            if len(stars)
            else np.nan,
        }
        records.append(record)
    return pd.DataFrame(records)


def population_shapes(galaxies: pd.DataFrame) -> pd.DataFrame:
    """SDSS r-band axis ratio and Petrosian radii of every galaxy (photometric object of its spectrum)."""
    cache = OUT_DIR / "sdss_shapes.parquet"
    cached = pd.read_parquet(cache) if cache.exists() else pd.DataFrame(columns=["target"])
    todo = galaxies[~galaxies.target.isin(set(cached.target))]
    tables = [cached]
    for start in range(0, len(todo), SKYSERVER_BATCH):
        chunk = todo.iloc[start : start + SKYSERVER_BATCH]
        values = ", ".join(
            f"({int(t)}, {int(i)})" for t, i in zip(chunk.target, chunk.specobjid, strict=True)
        )
        query = f"""SELECT t.target, p.fracDeV_r, p.expAB_r, p.deVAB_r, p.petroR50_r, p.petroR90_r
            FROM (VALUES {values}) AS t(target, specobjid)
            JOIN SpecObjAll s ON s.specObjID = t.specobjid JOIN PhotoObjAll p ON p.objID = s.bestObjID"""
        tables.append(_skyserver(query))
        if (start // SKYSERVER_BATCH) % 50 == 0:
            pd.concat(tables, ignore_index=True).to_parquet(cache)
            print(f"shapes: {start + len(chunk):,} of {len(todo):,}", flush=True)
    shapes = pd.concat(tables, ignore_index=True).drop_duplicates("target")
    shapes.to_parquet(cache)
    shapes["axis_ratio_r"] = np.where(shapes.fracDeV_r > 0.5, shapes.deVAB_r, shapes.expAB_r)
    return shapes[["target", "axis_ratio_r", "petroR50_r", "petroR90_r"]].rename(
        columns={"petroR50_r": "petrosian_r50_arcsec", "petroR90_r": "petrosian_r90_arcsec"}
    )


def shape_dependence(galaxies: pd.DataFrame) -> dict:
    """Index residual and outlier rates against axis ratio and size, all galaxies."""
    out = {}
    for column, edges in (
        ("axis_ratio_r", [0.0, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.01]),
        ("petrosian_r50_arcsec", [0.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 30.0]),
    ):
        bins = pd.cut(galaxies[column], edges)
        grouped = galaxies.groupby(bins, observed=True)
        out[column] = {
            str(interval): {
                "n": len(group),
                "residual_median": float(group.index_residual.median()),
                "residual_median_err": float(1.2533 * group.index_residual.std() / np.sqrt(len(group))),
                "fraction_strong_significant": float((group.significance < -SIGNIFICANCE_LIMIT).mean()),
                "fraction_weak_significant": float((group.significance > SIGNIFICANCE_LIMIT).mean()),
            }
            for interval, group in grouped
        }
        out[f"spearman_residual_vs_{column}"] = float(
            galaxies[["index_residual", column]].corr(method="spearman").iloc[0, 1]
        )
    return out


def tail_counts(galaxies: pd.DataFrame) -> dict:
    out = {}
    for limit in (3.0, 4.0, 5.0):
        out[f"{limit:g}"] = {
            "strong": int((galaxies.significance < -limit).sum()),
            "weak": int((galaxies.significance > limit).sum()),
            "gaussian_expectation_per_side": float(len(galaxies) * norm.sf(limit)),
        }
    return out


SETS = ("strong_apparent", "weak_apparent", "strong_significant", "weak_significant", "control")
SUMMARY_COLUMNS = [
    "hminus_bump_mag",
    "index_residual",
    "hminus_bump_err_mag",
    "significance",
    "significance_without_worst_visit",
    "halves_consistency",
    "exposure_scatter",
    "n_rejected",
    "n_feature",
    "n_visits_feature",
    "d3_minus_d2_step",
    "fraction_blue_d2",
    "fraction_feature_d3",
    "redshift",
    "aperture_flux_median_ujy",
    "aperture_snr_median",
    "background_median_mjy_sr",
    "flagged_pixels_median",
    "ecliptic_latitude_deg",
    "galactic_latitude_deg",
    "ebv",
    "neighbour_flux_ratio_aperture",
    "neighbour_flux_ratio_annulus",
    "brightest_star_relative_mag",
    "axis_ratio_r",
    "petrosian_r50_arcsec",
    "d4000_n_sub",
    "lick_hd_a_sub",
    "log_stellar_mass_msun",
    "specsfr_tot_p50",
    "h_alpha_eqw",
    "v_disp",
]


def main() -> None:
    rng = np.random.default_rng(2)
    galaxies = load_galaxies()
    galaxies = galaxies[~galaxies.in_magellanic.astype(bool)].reset_index(drop=True)
    galaxies, intrinsic = significance(galaxies)
    print(f"galaxies {len(galaxies):,}; intrinsic spread {intrinsic:.4f} mag")
    tails = tail_counts(galaxies)
    print("tail counts:", json.dumps(tails))
    population = {
        "residual_percentiles_1_99": np.percentile(galaxies.index_residual, [1, 99]).tolist(),
        "significance_robust_sigma": robust_sigma(galaxies.significance),
        "spearman_residual_vs_d3_minus_d2_step": float(
            galaxies[["index_residual", "d3_minus_d2_step"]].corr(method="spearman").iloc[0, 1]
        ),
        "spearman_residual_vs_exposure_scatter": float(
            galaxies[["index_residual", "exposure_scatter"]].corr(method="spearman").iloc[0, 1]
        ),
    }
    print(population)
    galaxies = galaxies.merge(population_shapes(galaxies), on="target", how="left")
    shapes = shape_dependence(galaxies)
    print(json.dumps(shapes, indent=1))
    galaxies[["target", "index_residual", "significance", "axis_ratio_r", "petrosian_r50_arcsec"]].to_parquet(
        OUT_DIR / "outlier_population.parquet"
    )

    groups = choose_groups(galaxies, rng)
    print({name: int(groups[name].sum()) for name in SETS}, "unique", len(groups))
    coordinates = SkyCoord(groups.ra_deg.to_numpy() * u.deg, groups.dec_deg.to_numpy() * u.deg)
    groups["ecliptic_latitude_deg"] = coordinates.barycentrictrueecliptic.lat.deg
    groups["galactic_latitude_deg"] = coordinates.galactic.b.deg

    exposures = load_exposures(groups, extra_columns=EXTRA_COLUMNS, correct_extinction=False)
    diagnostics, kept = per_galaxy_diagnostics(groups, exposures, intrinsic)
    groups = groups.merge(diagnostics, on="target", how="left")
    difference = (groups.index_recomputed - groups.hminus_bump_mag).abs()
    print(f"recomputed minus catalogue index: max |difference| {difference.max():.2e}")
    neighbours = query_neighbours(groups)
    groups = groups.merge(neighbour_metrics(neighbours), on="target", how="left")
    groups.to_parquet(OUT_DIR / "outlier_galaxies.parquet")
    kept.to_parquet(OUT_DIR / "outlier_exposures.parquet")

    table = pd.DataFrame({name: groups.loc[groups[name], SUMMARY_COLUMNS].median() for name in SETS})
    print(table.round(4).to_string())
    finite_halves = {
        name: float(groups.loc[groups[name], "halves_consistency"].notna().mean()) for name in SETS
    }
    print("fraction with both halves measured:", finite_halves)
    bpt = pd.DataFrame(
        {name: groups.loc[groups[name], "bptclass"].value_counts(normalize=True) for name in SETS}
    ).fillna(0)
    print(bpt.round(3).to_string())
    summary = {
        "n_galaxies": len(galaxies),
        "intrinsic_spread_mag": intrinsic,
        "tail_counts": tails,
        "population": population,
        "shape_dependence": shapes,
        "set_sizes": {name: int(groups[name].sum()) for name in SETS},
        "set_medians": {name: table[name].to_dict() for name in SETS},
        "fraction_with_both_halves": finite_halves,
        "bpt_fractions": {name: bpt[name].to_dict() for name in SETS},
    }
    with open(OUT_DIR / "outlier_summary.json", "w") as handle:
        json.dump(summary, handle, indent=2, default=float)


if __name__ == "__main__":
    main()
