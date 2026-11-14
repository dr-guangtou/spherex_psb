#!/usr/bin/env python3
"""Screen the per-exposure records of one galaxy, assemble its SED, and make figures 2-4.

usage: uv run python scripts/sed_demo/make_galaxy_figures.py <galaxy_name> [--aperture 2px]
Outputs: results/<galaxy>/records_screened.parquet, sed_model.parquet, sed_aperture.parquet, figures/*.png
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sample_definition import DEMO_GALAXIES  # noqa: E402

from spherex_psb import RESULTS_ROOT  # noqa: E402
from spherex_psb.figures.galaxy_figures import figure_diagnostics, figure_image_qa, figure_sed  # noqa: E402
from spherex_psb.spectra.assemble import (  # noqa: E402
    add_rest_frame,
    bin_to_channels,
    extinction_correction,
    galactic_ebv,
    screen_exposures,
)

FIGURE_ROOT = Path(__file__).resolve().parents[2] / "docs" / "figures" / "sed_demo"


MODEL_BASED_EXTERNAL = {
    ("SDSS DR17", "model"),
    ("2MASS XSC", "total (ext)"),
    ("Legacy DR10 forced", "Tractor model"),
    ("AllWISE", "elliptical (gmag)"),
}


def model_based_external_photometry(result_dir: Path) -> pd.DataFrame | None:
    """External total fluxes comparable to the forced-model flux (validation item 5), once validation has
    run: SDSS z model, 2MASS XSC total, Legacy Survey forced WISE (AllWISE elliptical where there is none)."""
    path = result_dir / "validation" / "external_photometry.parquet"
    if not path.exists():
        return None
    external = pd.read_parquet(path)
    keys = list(zip(external.origin, external.aperture, strict=True))
    external = external[[k in MODEL_BASED_EXTERNAL for k in keys]]
    if (external.origin == "Legacy DR10 forced").any():
        external = external[external.origin != "AllWISE"]
    return external


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("galaxy")
    parser.add_argument("--aperture", default="2px")
    args = parser.parse_args()
    galaxy = DEMO_GALAXIES[args.galaxy]
    result_dir = RESULTS_ROOT / args.galaxy
    FIGURE_ROOT.mkdir(parents=True, exist_ok=True)

    records = pd.read_parquet(result_dir / "records.parquet")
    records = screen_exposures(records)
    ebv = galactic_ebv(galaxy.ra, galaxy.dec)
    records["ebv_sandf"] = ebv["ebv_sandf"]
    good = records.screen_reason == ""
    correction = np.ones(len(records))
    correction[good.to_numpy()] = extinction_correction(records.cwave_um[good].to_numpy(), ebv["ebv_sandf"])
    records["extinction_factor"] = correction
    for column in [c for c in records.columns if c.startswith("flux_") and c.endswith("_ujy")]:
        records[column + "_dered"] = records[column] * correction
    records.to_parquet(result_dir / "records_screened.parquet", index=False)

    binned_model = add_rest_frame(bin_to_channels(records, "flux_model_ujy"), galaxy.redshift)
    binned_aperture = add_rest_frame(
        bin_to_channels(records, f"flux_aperture_{args.aperture}_ujy"), galaxy.redshift
    )
    binned_point = add_rest_frame(bin_to_channels(records, "flux_point_ujy"), galaxy.redshift)
    for table in (binned_model, binned_aperture, binned_point):
        factor = extinction_correction(table.wavelength_um.to_numpy(), ebv["ebv_sandf"])
        for column in [c for c in table.columns if c.startswith("flux") and c.endswith("_ujy")]:
            table[column + "_dered"] = table[column] * factor
    binned_model.to_parquet(result_dir / "sed_model.parquet", index=False)
    binned_aperture.to_parquet(result_dir / "sed_aperture.parquet", index=False)
    binned_point.to_parquet(result_dir / "sed_point.parquet", index=False)

    neighbours = pd.read_parquet(result_dir / "neighbours.parquet")
    shreds = pd.read_parquet(result_dir / "shreds.parquet")
    raw = np.load(result_dir / "qa_stamps.npz", allow_pickle=True)
    stamps: dict[int, dict] = {}
    for key in raw.files:
        detector, name = key.split("_", 1)
        stamps.setdefault(int(detector[1:]), {})[name] = raw[key].item() if raw[key].ndim == 0 else raw[key]
    prefix = FIGURE_ROOT / args.galaxy
    figure_image_qa(
        galaxy,
        records,
        neighbours,
        shreds,
        stamps,
        Path(f"{prefix}_fig2_image_qa.png"),
        fit_radius_px=galaxy.fit_radius_px,
    )
    figure_diagnostics(galaxy, records, Path(f"{prefix}_fig3_diagnostics.png"))
    figure_sed(
        galaxy,
        records,
        binned_model,
        binned_aperture,
        Path(f"{prefix}_fig4_sed.png"),
        external=model_based_external_photometry(result_dir),
        aperture_key=args.aperture,
    )

    summary = {
        "galaxy": args.galaxy,
        "ebv": ebv,
        "n_records": len(records),
        "n_used": int(good.sum()),
        "screening": records.screen_reason.value_counts().to_dict(),
        "channels_filled": int((binned_model.n_exposures > 0).sum()),
    }
    (result_dir / "sed_summary.json").write_text(json.dumps(summary, indent=2, default=str))
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
