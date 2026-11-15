"""Compare the student's SDSS 48k photometry with our SED-demo measurements on the same exposures.

For each demo galaxy that is in the 48k catalogue, rows are matched on (observation id, detector). Ours:
DR1 + QR3, forced Sersic model flux (`flux_model_ujy`), model-corrected 2 px aperture, raw 2 px aperture
(model-corrected value times the model fraction inside the aperture) and the unclipped point-source fit on
the same pixels. Theirs: QR2 upgraded to QR3 calibration + QR3, talltable `opt_flux_uJy` (point source,
4-sigma clipping) and `aper_flux_uJy`.
usage: uv run python scripts/sdss48k_review/compare_with_demo.py
"""

import numpy as np
import pandas as pd
import pyarrow.dataset as ds

RUN_DIR = "/Users/shuang/data/spherex/spherex_sdss48k_phot"
DEMO_DIR = "/Users/shuang/data/spherex/results"
OUTPUT = "/Users/shuang/data/spherex/scratch/sdss48k_demo_match.parquet"
DEMO_GALAXIES = {
    "g1_reference": 1806085614093756416,
    "g2_compact": 1342183509195778048,
    "g3_large": 1855517184537683968,
    "g4_neighbour": 2477075517577127936,
    "g5_no_legacy": 1875860345654896640,
    "g6_post_starburst": 3340648454601861120,
}

targets = pd.read_parquet(f"{RUN_DIR}/targets.parquet")
images = pd.read_parquet(f"{RUN_DIR}/images.parquet", columns=["expid", "obsid", "detector", "release"])
photometry = ds.dataset(f"{RUN_DIR}/photometry.parquet")

matched = []
for galaxy, specobjid in DEMO_GALAXIES.items():
    row = targets[targets.specobjid == specobjid]
    if row.empty:
        print(f"{galaxy}: not in the 48k catalogue")
        continue
    target = int(row.target.iloc[0])
    theirs = photometry.to_table(filter=ds.field("target") == target).to_pandas()
    theirs = theirs.merge(images, on="expid", how="left")
    ours = pd.read_parquet(f"{DEMO_DIR}/{galaxy}/records_screened.parquet")
    ours = ours[ours.reject_reason == ""].copy()
    ours["flux_aperture_2px_raw_ujy"] = ours.flux_aperture_2px_ujy * ours.aperture_2px_model_fraction
    both = theirs.merge(
        ours,
        left_on=["obsid", "detector_id"],
        right_on=["obs_id", "detector"],
        how="inner",
        suffixes=("_theirs", "_ours"),
    )
    both["galaxy"] = galaxy
    releases = theirs.release.value_counts().to_dict()
    screened_in = int((both.screen_reason == "").sum())
    print(f"{galaxy}: target {target}, theirs {len(theirs)} rows ({releases}), ours {len(ours)} measured,")
    print(f"    matched {len(both)}, of which screened-in {screened_in}")
    matched.append(both)

matched = pd.concat(matched, ignore_index=True)
matched.to_parquet(OUTPUT)
clean = matched[matched.screen_reason == ""]
print(
    "\nwavelength agreement (theirs - ours, um): median",
    round(float((clean.wv_um - clean.cwave_um).median()), 5),
    "| p5/p95",
    np.round(np.percentile(clean.wv_um - clean.cwave_um, [5, 95]), 4),
)

ratios = {
    "their PSF / our model": ("opt_flux_uJy", "flux_model_ujy"),
    "their aperture / our model": ("aper_flux_uJy", "flux_model_ujy"),
    "their PSF / our point (unclipped)": ("opt_flux_uJy", "flux_point_ujy"),
    "their aperture / our raw 2 px aperture": ("aper_flux_uJy", "flux_aperture_2px_raw_ujy"),
    "our point / our model": ("flux_point_ujy", "flux_model_ujy"),
}
for label, (numerator, denominator) in ratios.items():
    print(f"\n{label}: median per galaxy and detector (p16-p84 across exposures)")
    clean = clean.assign(ratio=clean[numerator] / clean[denominator])
    table = clean.groupby(["galaxy", "detector_id"]).ratio.median().unstack().round(3)
    print(table.to_string())
    spread = clean.groupby("galaxy").ratio.agg(
        lambda r: f"{np.percentile(r, 16):.3f}-{np.percentile(r, 84):.3f}"
    )
    print(spread.to_string())

print("\noutlier pixels (theirs) and the PSF-flux excess over our unclipped point fit")
clean = clean.assign(excess=clean.opt_flux_uJy / clean.flux_point_ujy, any_outlier=clean.n_pix_outlier > 0)
print(
    clean.groupby(["galaxy", "any_outlier"])
    .agg(
        n=("excess", "size"), median_excess=("excess", "median"), median_outliers=("n_pix_outlier", "median")
    )
    .round(3)
    .to_string()
)
print("\nformal errors: theirs / ours (PSF error vs our model error)")
print(
    clean.assign(error_ratio=clean.opt_flux_uJy_err / clean.flux_model_err_ujy)
    .groupby("galaxy")
    .error_ratio.median()
    .round(3)
    .to_string()
)
