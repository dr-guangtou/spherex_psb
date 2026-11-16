"""Per-detector photometric scatter of every galaxy, and the exposures of the most extreme strong-bump
outlier.

Target 45124 (s = -5.6, index -0.237 +- 0.034 mag) has its blue window on D2 and its feature and red windows
on D3. For every galaxy and detector the exposure-to-exposure scatter of the aperture flux is measured without
a model: exposures sorted in observed wavelength, the median absolute difference of consecutive ln F_nu
times 1.4826 / sqrt(2) (the robust sigma of one exposure if neighbours differ by noise only; the SED slope
between neighbours of one detector is below 1 % at R ~ 40). The ratio of the D2 to the D3 scatter, and of
each detector to the median of the other three of D1-D4, flags galaxies with one failed detector; the rates
are compared between the significance tails of `investigate_bump_outliers.py`.

Bright stars beyond the 20 arcsec neighbour radius: target 45124 has a saturated star 24 arcsec away. For
every galaxy of `outlier_galaxies.parquet` (apparent and significant tails, controls) the SDSS DR17 stars
(PhotoPrimary type 6, z < `STAR_MAG_LIMIT`) within `WIDE_RADIUS_ARCSEC` are queried (SkyServer, batched,
cached); the brightest star's z magnitude (the brighter of PSF and model magnitude, as saturated stars have
unreliable photometry) relative to the galaxy's, and its separation.

usage: uv run python scripts/sdss48k_review/inspect_detector_failures.py
Output: <results>/sdss48k_hminus/detector_scatter.parquet, target_45124_exposures.parquet,
detector_scatter_summary.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.dataset as ds

sys.path.insert(0, str(Path(__file__).resolve().parent))
from measure_hminus_bump import FIT_RANGE_UM, OUT_DIR, RUN_DIR, WINDOWS_UM, screen  # noqa: E402
from stack_sed_and_bump import load_exposures, load_galaxies  # noqa: E402

from spherex_psb.extraction.catalog import _skyserver  # noqa: E402

TARGET = 45124
FAILURE_RATIO = 3.0
TAIL_LIMIT = 3.0
INNER_DETECTORS = (1, 2, 3, 4)
WIDE_RADIUS_ARCSEC = 60.0
STAR_MAG_LIMIT = 18.0
SKYSERVER_BATCH = 150
SETS = ("strong_apparent", "weak_apparent", "strong_significant", "weak_significant", "control")


def detector_scatter(targets: np.ndarray) -> pd.DataFrame:
    table = (
        ds.dataset(f"{RUN_DIR}/photometry.parquet")
        .to_table(
            columns=["target", "detector_id", "wv_um", "aper_flux_uJy"],
            filter=ds.field("target").isin(targets),
        )
        .to_pandas()
    )
    table = table[table.aper_flux_uJy > 0].sort_values(["target", "detector_id", "wv_um"])
    log_flux = np.log(table.aper_flux_uJy.to_numpy())
    target, detector = table.target.to_numpy(), table.detector_id.to_numpy()
    same = (target[1:] == target[:-1]) & (detector[1:] == detector[:-1])
    steps = pd.DataFrame(
        {"target": target[1:][same], "detector": detector[1:][same], "step": np.abs(np.diff(log_flux))[same]}
    )
    scatter = steps.groupby(["target", "detector"]).step.median().mul(1.4826 / np.sqrt(2)).unstack()
    scatter.columns = [f"scatter_d{int(c)}" for c in scatter.columns]
    scatter["d2_over_d3"] = scatter.scatter_d2 / scatter.scatter_d3
    for k in INNER_DETECTORS:
        others = [f"scatter_d{j}" for j in INNER_DETECTORS if j != k]
        scatter[f"d{k}_over_others"] = scatter[f"scatter_d{k}"] / scatter[others].median(axis=1)
    return scatter.reset_index()


def wide_stars(galaxies: pd.DataFrame) -> pd.DataFrame:
    cache = OUT_DIR / "outlier_stars_60arcsec.parquet"
    cached = pd.read_parquet(cache) if cache.exists() else pd.DataFrame(columns=["target"])
    todo = galaxies[~galaxies.target.isin(set(cached.target))].drop_duplicates("target")
    tables = [cached]
    for start in range(0, len(todo), SKYSERVER_BATCH):
        chunk = todo.iloc[start : start + SKYSERVER_BATCH]
        values = ", ".join(
            f"({int(t)}, {ra:.6f}, {dec:.6f})"
            for t, ra, dec in zip(chunk.target, chunk.ra_deg, chunk.dec_deg, strict=True)
        )
        query = f"""SELECT t.target, p.psfMag_z, p.modelMag_z, n.distance * 60 AS sep_arcsec
            FROM (VALUES {values}) AS t(target, ra, dec)
            CROSS APPLY dbo.fGetNearbyObjEq(t.ra, t.dec, {WIDE_RADIUS_ARCSEC / 60.0}) AS n
            JOIN PhotoPrimary p ON p.objID = n.objID
            WHERE p.type = 6 AND (p.psfMag_z < {STAR_MAG_LIMIT} OR p.modelMag_z < {STAR_MAG_LIMIT})"""
        table = _skyserver(query)
        missing = set(chunk.target) - set(table.target) if not table.empty else set(chunk.target)
        tables.append(pd.concat([table, pd.DataFrame({"target": sorted(missing)})], ignore_index=True))
        print(f"SkyServer batch {start // SKYSERVER_BATCH + 1}: {len(table)} stars", flush=True)
    stars = pd.concat(tables, ignore_index=True)
    stars.to_parquet(cache)
    return stars


def star_metrics(galaxies: pd.DataFrame, stars: pd.DataFrame) -> pd.DataFrame:
    stars = stars.dropna(subset=["sep_arcsec"]).copy()
    stars["mag_z"] = stars[["psfMag_z", "modelMag_z"]].where(lambda v: v > 0).min(axis=1)
    brightest = stars.sort_values("mag_z").drop_duplicates("target").set_index("target")
    out = galaxies[["target", "self_mag_z", *SETS]].copy()
    out["wide_star_relative_mag"] = out.target.map(brightest.mag_z) - out.self_mag_z
    out["wide_star_sep_arcsec"] = out.target.map(brightest.sep_arcsec)
    return out


def main() -> None:
    population = pd.read_parquet(OUT_DIR / "outlier_population.parquet")
    scatter = detector_scatter(population.target.to_numpy()).merge(population, on="target")
    scatter.to_parquet(OUT_DIR / "detector_scatter.parquet")
    strong, weak = scatter.significance < -TAIL_LIMIT, scatter.significance > TAIL_LIMIT
    ratios = ["d2_over_d3"] + [f"d{k}_over_others" for k in INNER_DETECTORS]
    summary = {
        "median_scatter": {
            c: float(scatter[c].median()) for c in scatter.columns if c.startswith("scatter_")
        },
        "ratio_percentiles_50_90_99_99.9": {
            c: np.nanpercentile(scatter[c], [50, 90, 99, 99.9]).round(3).tolist() for c in ratios
        },
        "failures": {
            c: {
                "n_above": int((scatter[c] > FAILURE_RATIO).sum()),
                "strong_tail": int(((scatter[c] > FAILURE_RATIO) & strong).sum()),
                "weak_tail": int(((scatter[c] > FAILURE_RATIO) & weak).sum()),
            }
            for c in ratios
        },
        "fraction_d2_over_d3_above_2": {
            "all": float((scatter.d2_over_d3 > 2).mean()),
            "strong_tail": float((scatter.d2_over_d3[strong] > 2).mean()),
            "weak_tail": float((scatter.d2_over_d3[weak] > 2).mean()),
        },
        "target": scatter[scatter.target == TARGET].iloc[0].to_dict(),
    }

    outliers = pd.read_parquet(OUT_DIR / "outlier_galaxies.parquet")
    stars = star_metrics(outliers, wide_stars(outliers))
    beyond = stars.wide_star_sep_arcsec > 20
    summary["wide_stars"] = {
        name: {
            "n": int(stars[name].sum()),
            "fraction_star_brighter_within_60": float((stars.wide_star_relative_mag[stars[name]] < 0).mean()),
            "fraction_star_2mag_brighter_20_to_60": float(
                ((stars.wide_star_relative_mag < -2) & beyond)[stars[name]].mean()
            ),
        }
        for name in SETS
    }
    summary["wide_stars"]["target"] = (
        stars[stars.target == TARGET][["wide_star_relative_mag", "wide_star_sep_arcsec"]].iloc[0].to_dict()
    )
    stars.to_parquet(OUT_DIR / "outlier_wide_star_metrics.parquet")

    galaxy = load_galaxies().query("target == @TARGET")
    exposures = load_exposures(
        galaxy,
        extra_columns=("expid", "aper_flux_uJy_err", "bkg_MJysr", "n_pix_flagged"),
        correct_extinction=False,
    )
    exposures["day"] = np.floor(exposures.mjd_avg).astype(int)
    window = (exposures.rest_um >= FIT_RANGE_UM[0]) & (exposures.rest_um <= FIT_RANGE_UM[1])
    keep, residual, _ = screen(exposures.rest_um[window].to_numpy(), exposures.flux_lambda[window].to_numpy())
    exposures.loc[window, "kept"] = keep
    exposures.loc[window, "fit_residual"] = residual
    exposures["window"] = ""
    for name, (low, high) in WINDOWS_UM.items():
        exposures.loc[exposures.rest_um.between(low, high), "window"] = name
    exposures.to_parquet(OUT_DIR / "target_45124_exposures.parquet")
    in_window = exposures[window & exposures.kept.astype(bool)]
    summary["target_window_means_ujy"] = (
        (
            in_window[in_window.window != ""]
            .groupby(["window", "detector_id"])
            .aper_flux_uJy.agg(["mean", "size"])
        )
        .reset_index()
        .to_dict(orient="records")
    )
    same_day = exposures[exposures.detector_id == 2].groupby("day").aper_flux_uJy.agg(["min", "max", "size"])
    summary["target_d2_same_day_max_over_min"] = float(
        (same_day["max"] / same_day["min"])[same_day["size"] > 1].max()
    )
    print(json.dumps(summary, indent=1, default=float))
    with open(OUT_DIR / "detector_scatter_summary.json", "w") as handle:
        json.dump(summary, handle, indent=2, default=float)


if __name__ == "__main__":
    main()
