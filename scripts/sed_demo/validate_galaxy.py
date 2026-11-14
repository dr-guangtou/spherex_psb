#!/usr/bin/env python3
"""Validation items for one galaxy (docs/reports/sed_demo_task.md section 7): detector-boundary ratios for
the three
estimators, estimator consistency, external photometry with synthetic SPHEREx fluxes, injection-recovery on a
subset of exposures, error calibration from repeat pairs, and the tractorjax-spherex cross-code check on a
subset. Results go to results/<galaxy>/validation/.

usage: uv run python scripts/sed_demo/validate_galaxy.py <galaxy> [--subset-per-detector 6]
       [--skip-cross-code] [--skip-injection]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from astropy.table import Table
from astropy.wcs import FITSFixedWarning

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sample_definition import DEMO_GALAXIES  # noqa: E402

from spherex_psb import CUTOUT_ROOT, RESULTS_ROOT  # noqa: E402
from spherex_psb.archive.discovery import select_per_detector  # noqa: E402
from spherex_psb.extraction.catalog import legacy_dr10_neighbours  # noqa: E402
from spherex_psb.extraction.fit import FitSettings, Source  # noqa: E402
from spherex_psb.extraction.render import SersicShape  # noqa: E402
from spherex_psb.products.bundle import read_bundle  # noqa: E402
from spherex_psb.validation.boundary import boundary_ratios, estimator_consistency  # noqa: E402
from spherex_psb.validation.cross_code import compare_with_records, run_tractorjax  # noqa: E402
from spherex_psb.validation.errors import pull_statistics, repeat_pairs  # noqa: E402
from spherex_psb.validation.external_photometry import query_external, synthetic_photometry  # noqa: E402
from spherex_psb.validation.injection import (  # noqa: E402
    inject_and_measure,
    injected_shape_like,
    injection_position,
    smooth_sed,
)


def load_sources(galaxy, result_dir: Path) -> tuple[Source, list[Source]]:
    kept = pd.read_parquet(result_dir / "neighbours.parquet")
    target = Source("target", galaxy.ra, galaxy.dec, galaxy.shape, galaxy.mag_z, True)
    sources = [target]
    for i, row in kept.iterrows():
        shape = SersicShape(
            float(row.sersic_index),
            float(row.r_e_arcsec),
            float(row.axis_ratio),
            float(row.position_angle_deg),
        )
        sources.append(Source(f"n{i:03d}", float(row.ra), float(row.dec), shape, float(row.mag_z)))
    return target, sources


def subset_records(records: pd.DataFrame, per_detector: int) -> pd.DataFrame:
    frames = Table.from_pandas(
        records[["obs_id", "detector", "mjd"]].rename(columns={"mjd": "time_bounds_lower"})
    )
    chosen = select_per_detector(frames, per_detector)
    keys = {(o, int(d)) for o, d in zip(chosen["obs_id"], chosen["detector"], strict=True)}
    return records[[(o, int(d)) in keys for o, d in zip(records.obs_id, records.detector, strict=True)]]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("galaxy")
    parser.add_argument("--subset-per-detector", type=int, default=6)
    parser.add_argument("--skip-cross-code", action="store_true")
    parser.add_argument("--skip-injection", action="store_true")
    args = parser.parse_args()
    warnings.simplefilter("ignore", FITSFixedWarning)
    galaxy = DEMO_GALAXIES[args.galaxy]
    result_dir = RESULTS_ROOT / args.galaxy
    out_dir = result_dir / "validation"
    out_dir.mkdir(exist_ok=True)
    records = pd.read_parquet(result_dir / "records_screened.parquet")
    sed_model = pd.read_parquet(result_dir / "sed_model.parquet")
    target, sources = load_sources(galaxy, result_dir)
    summary: dict = {"galaxy": args.galaxy}
    start = time.time()

    # 1-3: detector boundaries for the three estimators, estimator consistency
    boundary = pd.concat(
        [
            boundary_ratios(records, column)
            for column in ("flux_model_ujy", "flux_aperture_2px_ujy", "flux_point_ujy")
        ]
    )
    boundary["galaxy"] = args.galaxy
    boundary.to_parquet(out_dir / "boundary_ratios.parquet", index=False)
    summary["estimator_consistency"] = estimator_consistency(records)
    print(f"[{args.galaxy}] boundary ratios (B/A, mag):")
    print(boundary.pivot(index="boundary", columns="flux_column", values="ratio_mag").round(3).to_string())

    # 5: external photometry
    legacy = legacy_dr10_neighbours(galaxy.ra, galaxy.dec, 0.5, 30.0) if galaxy.catalogue == "ls" else None
    external = pd.DataFrame(
        columns=["band", "origin", "aperture", "flux_ujy", "flux_err_ujy", "wavelength_um"]
    )
    for attempt in range(4):  # IRSA catalogue services go down now and then
        try:
            external = query_external(galaxy.ra, galaxy.dec, galaxy.sdss_objid, legacy)
            break
        except Exception as error:  # noqa: BLE001
            print(f"[{args.galaxy}] external query failed (attempt {attempt + 1}): {str(error)[:120]}")
            time.sleep(90)
    external["galaxy"] = args.galaxy
    external.to_parquet(out_dir / "external_photometry.parquet", index=False)
    ok = sed_model.n_exposures > 0
    synthetic = synthetic_photometry(
        sed_model.wavelength_um[ok].to_numpy(), sed_model.flux_ujy[ok].to_numpy()
    )
    synthetic["galaxy"] = args.galaxy
    synthetic.to_parquet(out_dir / "synthetic_photometry.parquet", index=False)
    comparison = external.merge(
        synthetic[["band", "flux_ujy"]].rename(columns={"flux_ujy": "spherex_synthetic_ujy"}),
        on="band",
        how="left",
    )
    comparison["spherex_over_external"] = comparison.spherex_synthetic_ujy / comparison.flux_ujy
    comparison.to_parquet(out_dir / "external_comparison.parquet", index=False)
    print(
        comparison[
            ["band", "origin", "aperture", "flux_ujy", "spherex_synthetic_ujy", "spherex_over_external"]
        ]
        .round(3)
        .to_string(index=False)
    )

    # 7: error calibration from repeat pairs
    pairs = repeat_pairs(records)
    pairs["galaxy"] = args.galaxy
    pairs.to_parquet(out_dir / "repeat_pairs.parquet", index=False)
    pulls = pull_statistics(pairs) if len(pairs) else pd.DataFrame()
    pulls["galaxy"] = args.galaxy
    pulls.to_parquet(out_dir / "pull_statistics.parquet", index=False)
    print(f"[{args.galaxy}] repeat pairs: {len(pairs)}")
    if len(pulls):
        print(pulls.round(3).to_string(index=False))

    subset = subset_records(records[records.reject_reason == ""], args.subset_per_detector)
    paths = [CUTOUT_ROOT / args.galaxy / b for b in subset.bundle]

    # 4: injection and recovery on the subset
    if not args.skip_injection:
        sed = smooth_sed(sed_model)
        injected_shape = injected_shape_like(galaxy.shape)
        settings = FitSettings(fit_radius_px=galaxy.fit_radius_px)
        rows = []
        for path in paths:
            bundle = read_bundle(path)
            try:
                ra, dec = injection_position(
                    bundle, galaxy.ra, galaxy.dec, sources, target_mag_z=galaxy.mag_z
                )
            except RuntimeError as error:
                rows.append({"bundle": path.name, "reject_reason": str(error)})
                continue
            injected = Source("injected", ra, dec, injected_shape, galaxy.mag_z, True)
            record = inject_and_measure(bundle, sources, injected, sed, settings)
            record["bundle"] = path.name
            rows.append(record)
        injection = pd.DataFrame(rows)
        injection["galaxy"] = args.galaxy
        injection.to_parquet(out_dir / "injection_recovery.parquet", index=False)
        good = injection[injection.reject_reason == ""]
        summary["injection"] = {
            "n": int(len(good)),
            "model_ratio_median": float(good.flux_model_recovered_ratio.median()) if len(good) else np.nan,
            "model_ratio_mad": float(
                1.4826
                * (good.flux_model_recovered_ratio - good.flux_model_recovered_ratio.median()).abs().median()
            )
            if len(good)
            else np.nan,
            "aperture_ratio_median": float(good.flux_aperture_2px_recovered_ratio.median())
            if len(good)
            else np.nan,
            "point_ratio_median": float(good.flux_point_recovered_ratio.median()) if len(good) else np.nan,
        }
        print(f"[{args.galaxy}] injection: {summary['injection']}")

    # 6: cross-code check on the subset
    if not args.skip_cross_code:
        tjx = run_tractorjax(
            paths, sources, target, solver="linear", output=out_dir / "tractorjax_target.parquet"
        )
        merged = compare_with_records(records, tjx)
        merged["galaxy"] = args.galaxy
        merged.to_parquet(out_dir / "cross_code.parquet", index=False)
        used = merged[merged.screen_reason == ""]
        summary["cross_code"] = {
            "n": int(len(used)),
            "ratio_median": float(used.ratio_ours_over_tjx.median()),
            "ratio_16": float(np.percentile(used.ratio_ours_over_tjx, 16)),
            "ratio_84": float(np.percentile(used.ratio_ours_over_tjx, 84)),
            "per_detector": used.groupby("detector").ratio_ours_over_tjx.median().round(4).to_dict(),
        }
        print(f"[{args.galaxy}] cross-code: {summary['cross_code']}")

    summary["seconds"] = round(time.time() - start, 1)
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
