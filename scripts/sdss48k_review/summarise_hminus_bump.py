"""Numbers behind the H-minus bump figures: binned medians of the index against Dn4000, HdeltaA and the broad
D4000, intrinsic scatter, the H-bump paper's model loci in the same D4000 bins, the redshift trend at fixed
Dn4000 (a check for detector and sampling systematics), and the six demo galaxies against the demo study.

Model populations (read only): the H-bump project's exponential-quench family, epochs >= 1 Gyr as in the
paper's figure 1; TP-AGB off = C3K templates with agb = 0 (`output/population`), TP-AGB on = LW02 templates
with agb = 2 (`output/population_lw02`); D4000 and HdeltaA on the sigma = 300 km/s product, the bump on the
R = 100 product.
usage: uv run python scripts/sdss48k_review/summarise_hminus_bump.py
"""

import numpy as np
import pandas as pd

from spherex_psb import RESULTS_ROOT

INDICES = RESULTS_ROOT / "sdss48k_hminus" / "hminus_bump_indices.parquet"
MODEL_ROOT = "/Users/shuang/Dropbox/work/project/luandun/stellar_pop/fsps_agb/output"
MODELS = {"TP-AGB off": ("population", "agb0"), "TP-AGB on": ("population_lw02", "agb2")}
DEMO_SPECOBJID = {
    "g1_reference": 1806085614093756416,
    "g2_compact": 1342183509195778048,
    "g3_large": 1855517184537683968,
    "g4_neighbour": 2477075517577127936,
    "g5_no_legacy": 1875860345654896640,
    "g6_post_starburst": 3340648454601861120,
}
# docs/reports/hminus_bump_feasibility.md section 3, exposure estimator on the model flux
DEMO_STUDY_INDEX = {
    "g1_reference": (-0.057, 0.017),
    "g2_compact": (-0.028, 0.020),
    "g3_large": (-0.050, 0.013),
    "g4_neighbour": (-0.055, 0.033),
    "g5_no_legacy": (-0.040, 0.011),
    "g6_post_starburst": (-0.018, 0.015),
}


def load_model(name):
    directory, key = MODELS[name]
    with np.load(f"{MODEL_ROOT}/{directory}/indices.npz") as data:
        keep = data["epoch_gyr"] >= 1.0
        return pd.DataFrame(
            {
                "d4000": data[f"d4000_{key}"][keep],
                "hdelta_a": data[f"hdelta_a_{key}"][keep],
                "bump": data[f"h_minus_bump_r100_{key}"][keep],
            }
        )


def robust_sigma(values):
    return 1.4826 * np.median(np.abs(values - np.median(values)))


def binned(table, x, edges):
    rows = []
    for low, high in zip(edges[:-1], edges[1:], strict=True):
        part = table[(table[x] >= low) & (table[x] < high)]
        if len(part) < 20:
            continue
        observed = robust_sigma(part.hminus_bump_mag)
        noise = np.median(part.hminus_bump_err_mag)
        rows.append(
            {
                "bin": f"{low:g}-{high:g}",
                "n": len(part),
                "median": part.hminus_bump_mag.median(),
                "p16": part.hminus_bump_mag.quantile(0.16),
                "p84": part.hminus_bump_mag.quantile(0.84),
                "robust_sigma": observed,
                "median_error": noise,
                "intrinsic": np.sqrt(max(observed**2 - noise**2, 0)),
            }
        )
    return pd.DataFrame(rows).round(4)


data = pd.read_parquet(INDICES)
data = data[np.isfinite(data.hminus_bump_mag)]
print(f"galaxies with an index: {len(data):,}")
print(
    "median errors: bump",
    round(data.hminus_bump_err_mag.median(), 4),
    "| Dn4000",
    round(data.d4000_n_sub_err.median(), 4),
    "| D4000",
    round(data.d4000_sub_err.median(), 4),
    "| HdeltaA",
    round(data.lick_hd_a_sub_err.median(), 3),
)
total, noise = robust_sigma(data.hminus_bump_mag), np.median(data.hminus_bump_err_mag)
print(
    f"whole sample: median {data.hminus_bump_mag.median():.4f}, robust sigma {total:.4f},"
    f" median error {noise:.4f},"
    f" implied intrinsic {np.sqrt(max(total**2 - noise**2, 0)):.4f}"
)
print(
    "Spearman rank correlation of the bump with Dn4000",
    round(data.hminus_bump_mag.corr(data.d4000_n_sub, method="spearman"), 3),
    "| with HdeltaA",
    round(data.hminus_bump_mag.corr(data.lick_hd_a_sub, method="spearman"), 3),
)
print("\nbump in Dn4000 bins (catalogue)")
print(binned(data, "d4000_n_sub", np.arange(1.0, 2.31, 0.1)).to_string(index=False))
print("\nbump in HdeltaA bins (catalogue)")
print(binned(data, "lick_hd_a_sub", np.arange(-4, 9, 1.0)).to_string(index=False))
d4000_edges = np.arange(1.1, 2.61, 0.1)
print("\nbump in broad D4000 bins: data and models (median, p16, p84)")
rows = []
models = {name: load_model(name) for name in MODELS}
for low, high in zip(d4000_edges[:-1], d4000_edges[1:], strict=True):
    row = {"D4000": f"{low:.1f}-{high:.1f}"}
    part = data[(data.d4000_sub >= low) & (data.d4000_sub < high)]
    row["data n"] = len(part)
    row["data"] = f"{part.hminus_bump_mag.median():.3f}" if len(part) >= 20 else ""
    for name, model in models.items():
        inside = model[(model.d4000 >= low) & (model.d4000 < high)].bump
        row[name] = (
            f"{inside.median():.3f} ({inside.quantile(0.16):.3f}, {inside.quantile(0.84):.3f})"
            if len(inside)
            else ""
        )
    rows.append(row)
print(pd.DataFrame(rows).to_string(index=False))
print(
    "\nbroad D4000 of the data: p5/50/95",
    np.round(np.percentile(data.d4000_sub, [5, 50, 95]), 3),
    "| Dn4000",
    np.round(np.percentile(data.d4000_n_sub, [5, 50, 95]), 3),
)

print("\nredshift trend: median bump in redshift bins, at fixed Dn4000")
data["z_bin"] = pd.cut(data.redshift, [0.03, 0.036, 0.042, 0.048, 0.054, 0.06])
data["dn_bin"] = pd.cut(data.d4000_n_sub, [1.0, 1.4, 1.7, 1.9, 2.5])
print(
    data.pivot_table(
        index="dn_bin", columns="z_bin", values="hminus_bump_mag", aggfunc="median", observed=True
    )
    .round(4)
    .to_string()
)
print(
    data.pivot_table(
        index="dn_bin", columns="z_bin", values="hminus_bump_mag", aggfunc="size", observed=True
    ).to_string()
)

print(
    "\nsix demo galaxies: this run (aperture, SAPM-corrected) against the demo study (model flux, DR1 + QR3)"
)
for name, specobjid in DEMO_SPECOBJID.items():
    row = data[data.specobjid == specobjid]
    if row.empty:
        print(name, "no index")
        continue
    row = row.iloc[0]
    study, study_error = DEMO_STUDY_INDEX[name]
    print(
        f"{name:20s} run {row.hminus_bump_mag:+.3f} +- {row.hminus_bump_err_mag:.3f}"
        f" (uncorrected {row.hminus_bump_uncorrected_mag:+.3f}) | study {study:+.3f} +- {study_error:.3f}"
        f" | n blue/feature/red {row.n_blue}/{row.n_feature}/{row.n_red}"
    )
