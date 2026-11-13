#!/usr/bin/env python3
"""Measure every selected SPHEREx exposure of one galaxy: discovery, cutouts, neighbour catalogue, forced
photometry with both estimators, per-exposure Parquet records and QA stamps.

usage: uv run python scripts/sed_demo/measure_galaxy.py <galaxy_name> [--per-detector N] [--size-deg 0.07]
       [--background constant|plane|cwave2|plane+cwave2] [--catalogue sdss|ls]
The galaxy definitions live in scripts/sed_demo/sample_definition.py (fixed before any SPHEREx data is seen).
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
from astropy.wcs import FITSFixedWarning

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sample_definition import DEMO_GALAXIES  # noqa: E402

from spherex_psb import RESULTS_ROOT  # noqa: E402
from spherex_psb.archive.cutouts import retrieve_frames  # noqa: E402
from spherex_psb.archive.discovery import (  # noqa: E402
    describe_counts,
    find_exposures,
    save_frames,
    select_per_detector,
)
from spherex_psb.extraction.catalog import (  # noqa: E402
    legacy_dr10_neighbours,
    remove_shreds,
    sdss_neighbours,
)
from spherex_psb.extraction.fit import FitSettings, Source, measure_exposure  # noqa: E402
from spherex_psb.extraction.render import SersicShape  # noqa: E402
from spherex_psb.products.bundle import list_bundles, read_bundle  # noqa: E402

NEIGHBOUR_DEPTH_MAG = 6.0  # neighbours down to target + 6 mag in z


def build_catalogue(galaxy, size_deg: float, source: str):
    radius_arcmin = size_deg * 60 / 2 * 1.1 + 0.25  # sources just outside the cutout still leak light into it
    faint = galaxy.mag_z + NEIGHBOUR_DEPTH_MAG
    if source == "ls":
        catalogue = legacy_dr10_neighbours(galaxy.ra, galaxy.dec, radius_arcmin, faint)
        if catalogue.empty:
            print("  Legacy Survey DR10: no sources (outside the footprint?); falling back to SDSS")
            source = "sdss"
    if source == "sdss":
        catalogue = sdss_neighbours(galaxy.ra, galaxy.dec, radius_arcmin, faint)
    kept, shreds = remove_shreds(catalogue, galaxy.ra, galaxy.dec, galaxy.shape, galaxy.mag_z)
    return source, kept, shreds


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("galaxy")
    parser.add_argument("--per-detector", type=int, default=None)
    parser.add_argument("--size-deg", type=float, default=None)
    parser.add_argument("--background", default="cwave2")
    parser.add_argument("--catalogue", default="auto", choices=["auto", "sdss", "ls"])
    parser.add_argument("--max-workers", type=int, default=2)
    args = parser.parse_args()
    warnings.simplefilter("ignore", FITSFixedWarning)
    galaxy = DEMO_GALAXIES[args.galaxy]
    size_deg = args.size_deg or galaxy.cutout_size_deg
    out_dir = RESULTS_ROOT / args.galaxy
    out_dir.mkdir(parents=True, exist_ok=True)
    start = time.time()

    frames = find_exposures(galaxy.ra, galaxy.dec, size_deg)
    print(f"[{args.galaxy}] discovery: {describe_counts(frames)}")
    save_frames(frames, out_dir / "exposures_all.ecsv")
    selected = select_per_detector(frames, args.per_detector)
    print(f"[{args.galaxy}] selected {len(selected)} exposures")

    cutout_dir, report = retrieve_frames(
        selected, galaxy.ra, galaxy.dec, size_deg, args.galaxy, max_workers=args.max_workers
    )
    print(f"[{args.galaxy}] cutouts: {report}")

    catalogue_source = args.catalogue if args.catalogue != "auto" else galaxy.catalogue
    catalogue_source, kept, shreds = build_catalogue(galaxy, size_deg, catalogue_source)
    kept.to_parquet(out_dir / "neighbours.parquet", index=False)
    shreds.to_parquet(out_dir / "shreds.parquet", index=False)
    print(
        f"[{args.galaxy}] catalogue {catalogue_source}: {len(kept)} neighbours kept, "
        f"{len(shreds)} shreds removed"
    )
    sources = [Source("target", galaxy.ra, galaxy.dec, galaxy.shape, galaxy.mag_z, True)]
    for i, row in kept.iterrows():
        shape = SersicShape(
            float(row.sersic_index),
            float(row.r_e_arcsec),
            float(row.axis_ratio),
            float(row.position_angle_deg),
        )
        sources.append(Source(f"n{i:03d}", float(row.ra), float(row.dec), shape, float(row.mag_z)))

    settings = FitSettings(background_model=args.background, fit_radius_px=galaxy.fit_radius_px)
    records, stamps = [], {}
    wanted = {f"cutout_{o}_D{d}.fits" for o, d in zip(selected["obs_id"], selected["detector"], strict=True)}
    for path in list_bundles(cutout_dir):
        if path.name not in wanted:
            continue
        bundle = read_bundle(path)
        result = measure_exposure(bundle, sources, settings)
        record = result.record
        record["bundle"] = path.name
        record["catalogue_source"] = catalogue_source
        records.append(record)
        if result.model is not None and bundle.detector not in stamps:
            stamps[bundle.detector] = {
                "data": result.data,
                "model": result.model,
                "good": result.good,
                "target": result.target_template,
                "neighbours": result.neighbour_light,
                "background": result.background,
                "variance": bundle.variance,
                "x0": record["x_cutout"],
                "y0": record["y_cutout"],
                "cwave": record["cwave_um"],
                "obs_id": bundle.obs_id,
            }
    table = pd.DataFrame(records)
    table["galaxy"] = args.galaxy
    table["redshift"] = galaxy.redshift
    table.to_parquet(out_dir / "records.parquet", index=False)
    np.savez_compressed(
        out_dir / "qa_stamps.npz", **{f"D{d}_{k}": v for d, s in stamps.items() for k, v in s.items()}
    )
    summary = {
        "galaxy": args.galaxy,
        "n_exposures_available": len(frames),
        "counts": frames.meta["counts"],
        "n_selected": len(selected),
        "cutouts": report,
        "catalogue_source": catalogue_source,
        "n_neighbours": len(kept),
        "n_shreds": len(shreds),
        "n_measured": int((table.reject_reason == "").sum()),
        "rejections": table.reject_reason.value_counts().to_dict(),
        "background_model": args.background,
        "seconds": round(time.time() - start, 1),
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, default=str))
    print(
        f"[{args.galaxy}] measured {summary['n_measured']} of {len(table)} exposures; "
        f"rejections {summary['rejections']}; {summary['seconds']} s"
    )
    good = table[table.reject_reason == ""]
    if len(good):
        pd.set_option("display.width", 220)
        print(
            good.groupby("detector")[
                [
                    "chi2_dof_near",
                    "flux_model_ujy",
                    "flux_aperture_2px_ujy",
                    "flux_point_ujy",
                    "model_fraction_fit",
                ]
            ]
            .median()
            .round(3)
        )


if __name__ == "__main__":
    main()
